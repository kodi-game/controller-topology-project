#!/usr/bin/env python3

# Copyright (C) 2016 Christian Fetzer
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

""" Process Kodi Game addons and unify project files """

import argparse
import collections
import datetime
import os
import multiprocessing
import re
import shlex
import shutil
import subprocess
import sys

from . import config
from . import git_access
from . import libretro_ctypes
from . import utils
from . import template_processor
from . import versions

ADDONS = config.ADDONS


def main():
    """ Process Kodi Game addons and unify project files """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-addons-dir', dest='working_directory',
                        type=str, required=True,
                        help="Directory where the game addons reside")
    parser.add_argument('--compile', action='store_true',
                        help="Compile libretro cores and read system info")
    parser.add_argument('--buildtype', default='Debug',
                        type=str, choices=['Debug', 'Release'],
                        help="Specify build type")
    parser.add_argument('--kodi-source-dir', dest='kodi_directory',
                        type=str,
                        help="Kodi's source directory")
    parser.add_argument('--git', action="store_true",
                        help="Clone / reset libretro cores from GitHub")
    parser.add_argument('--git-noclean', action="store_true",
                        help="Keep existing commits (rebase and squash)")
    parser.add_argument('--filter', type=str, default='',
                        help="Filter games (e.g. nes)")
    parser.add_argument('--push-branch', type=str,
                        help="To which branch to push to GitHub")
    parser.add_argument('--push-description', action='store_true',
                        help="Push addon descriptions")
    parser.add_argument('--clean-description', action='store_true',
                        help="Clean existing addon descriptions")

    args = parser.parse_args()

    args.working_directory = os.path.abspath(args.working_directory)
    if args.git:
        args.git = git_access.Git(auth=True)
    util = KodiGameAddons(args)
    util.process()
    util.summary()


class KodiGameAddons:
    """ Process Kodi Game addons and unify project files """
    def __init__(self, args):
        """ Initialize instance """
        self._args = args
        self._prepare_environment()

    def _prepare_environment(self):
        """ Prepare and check the environment (directories and config) """
        # Check if given filter matches with config.py
        config.ADDONS = {k: v for k, v in config.ADDONS.items()
                         if re.search(self._args.filter, k)}
        if not config.ADDONS:
            raise ValueError("Filter doesn't match any items in config.py")

        # Check GitHub repos
        repos = {}
        if self._args.git:
            print("Fetching libretro-super repo")
            self._args.git.clone_repo(
                git_access.GitRepo(
                    'libretro-super',
                    'https://github.com/libretro/libretro-super.git', ''),
                self._args.working_directory)

            regex = (self._args.filter if self._args.filter
                     else config.GITHUB_ADDON_PREFIX)
            print("Querying repos matching '{}'".format(regex))
            repos = self._args.git.get_repos(config.GITHUB_ORGANIZATION, regex)

        # Create Addon objects
        self._addons = collections.OrderedDict()
        for game_name in sorted(config.ADDONS):
            addon_name = '{}{}'.format(config.GITHUB_ADDON_PREFIX, game_name)
            repo = repos.get(addon_name, None)
            if self._args.git and not repo:
                print("Creating GitHub repository {}".format(addon_name))
                repo = self._args.git.create_repo(
                    config.GITHUB_ORGANIZATION, addon_name)
            self._addons[game_name] = Addon(addon_name, game_name,
                                            repo, self._args)

        print("Processing the following addons: {}".format(
            ', '.join(self._addons)))

        # Clone/Fetch repos
        if self._args.git:
            for addon in self._addons.values():
                addon.clone()

        # Clean addon descriptions
        if self._args.clean_description:
            desc_dir = os.path.join(self._args.kodi_directory,
                                    'cmake', 'addons', 'addons')
            for path in next(os.walk(desc_dir))[1]:
                if path.startswith(config.GITHUB_ADDON_PREFIX):
                    shutil.rmtree(os.path.join(desc_dir, path))

    def process(self):
        """ Process list of addons from config """

        # First iteration: Makefiles
        print("First iteration: Generate Makefiles")
        for addon in self._addons.values():
            print(" Processing addon: {}".format(addon.name))
            addon.process_addon_files()
            print(" Processing addon description: {}".format(addon.name))
            addon.process_description_files()

        # Compile addons to read info from built library
        # Instead of compiling individual addons we compile all at once to save
        # time (tinyxml and others would be compiled multiple times).
        if self._args.compile:
            if not self._compile_addons():
                return

            # Second iteration: Metadata files
            print("Second iteration: Generate Metadata files")
            for addon in self._addons.values():
                print(" Processing addon: {}".format(addon.name))
                addon.process_addon_files()

        # Create commit
        if self._args.git:
            for addon in self._addons.values():
                addon.commit()

            # Push in reversed order so that the repository list on GitHub
            # stays sorted alphabetically
            if self._args.push_branch:
                for addon in reversed(self._addons.values()):
                    addon.push()

                # Push addon descriptions to kodi repo
                # Don't specify urls as we use the existing remote origin
                if self._args.push_description:
                    path, name = os.path.split(self._args.kodi_directory)
                    repo = git_access.GitRepo(name, url='', ssh_url='')
                    print("Commiting descriptions to GitHub repo")
                    self._args.git.commit_repo(
                        repo, path, "Updated by kodi-game-scripting",
                        directory=os.path.join(
                            'cmake', 'addons', 'addons'),
                        force=True)
                    print("Pushing descriptions to GitHub repo")
                    self._args.git.push_repo(repo, path,
                                             self._args.push_branch)

    def summary(self):
        """ Print summary """
        print("Generating summary")
        template_vars = {'addons': []}
        for addon in self._addons.values():
            template_vars['addons'].append(addon.info)
        template_processor.TemplateProcessor.process(
            'summary', self._args.working_directory, template_vars)

    def _compile_addons(self):
        """ Compiles the addons in order to read system info from the libs """
        print("Compiling addons")
        build_dir = os.path.join(self._args.working_directory, 'build')
        install_dir = os.path.join(self._args.working_directory, 'install')
        cmake_dir = os.path.join(self._args.kodi_directory,
                                 'cmake', 'addons')

        utils.ensure_directory_exists(build_dir, clean=True)
        addons = '|'.join(['{}{}$'.format(config.GITHUB_ADDON_PREFIX, a)
                           for a in config.ADDONS])
        try:
            subprocess.run([os.environ.get('CMAKE', 'cmake'),
                            '-DADDONS_TO_BUILD={}'.format(addons),
                            '-DADDON_SRC_PREFIX={}'
                            .format(self._args.working_directory),
                            '-DCMAKE_BUILD_TYPE={}'
                            .format(self._args.buildtype),
                            '-DPACKAGE_ZIP=1',
                            '-DCMAKE_INSTALL_PREFIX={}'.format(install_dir),
                            cmake_dir], cwd=build_dir)
            subprocess.run([os.environ.get('CMAKE', 'cmake'), '--build', '.',
                            '--', '-j{}'.format(multiprocessing.cpu_count())],
                           cwd=build_dir)
        except subprocess.CalledProcessError:
            print("Compilation failed!")
            return False
        return True


class Addon():
    """ Process a single Kodi Game addon """
    def __init__(self, addon_name, game_name, repo, args):
        self.name = addon_name
        self.game_name = game_name
        self._config = config.ADDONS[game_name]
        self._repo = repo
        self._args = args
        self.path = os.path.join(self._args.working_directory, addon_name)
        self.library_file = os.path.join(
            'install', self.name, '{}.{}'.format(
                self.name, libretro_ctypes.LibretroWrapper.EXT))
        self.libretro_soname = '{}_libretro'.format(game_name)

        if not os.path.isdir(self.path):
            print("Initializing empty addon directory: {}".format(
                addon_name))
            utils.ensure_directory_exists(self.path)

        self.info = {
            'game': {'name': self.game_name, 'addon': self.name},
            'datetime': '{0:%Y-%m-%d %H:%Mi%z}'.format(
                datetime.datetime.now()),
            'system_info': {}, 'settings': [],
            'repo': self._config[0],
            'repo_branch': 'master',
            'makefile': {'file': self._config[1], 'dir': self._config[2],
                         'jni': self._config[3], 'jnisoname': 'libretro'},
            'library': {'file': self.library_file, 'loaded': False},
            'assets': {}, 'git': {}}

        if self._args.push_branch:
            self.info['branch'] = self._args.push_branch
        if len(self._config) > 4:
            self.info['config'] = self._config[4]
            if 'branch' in self._config[4]:
                self.info['repo_branch'] = self._config[4]['branch']
            if 'soname' in self._config[4]:
                self.libretro_soname = '{}_libretro'.format(
                    self._config[4]['soname'])
            if 'jnisoname' in self._config[4]:
                self.info['makefile']['jnisoname'] = \
                    self._config[4]['jnisoname']

        self.info['makefile']['soname'] = self.libretro_soname
        self.load_info_file()

    def process_description_files(self):
        """ Generate addon description files """
        template_processor.TemplateProcessor.process(
            'description',
            os.path.join(self._args.kodi_directory, 'cmake',
                         'addons', 'addons', self.name),
            self.info)

    def load_library_file(self):
        """ Load the compiled library file """
        library = None
        library_path = os.path.join(self._args.working_directory,
                                    self.library_file)
        if os.path.isfile(os.path.join(library_path)):
            try:
                library = libretro_ctypes.LibretroWrapper(library_path)
                self.info['library']['loaded'] = True
                self.info['system_info'] = library.system_info
                self.info['settings'] = sorted(library.variables,
                                               key=lambda x: x.id)
                self.info['game']['version'] = versions.AddonVersion.get(
                    library.system_info.version)

                if sys.platform != 'darwin':
                    ldd_command = ['ldd', library_path]
                else:
                    ldd_command = ['otool', '-L', library_path]
                ldd_output = subprocess.run(ldd_command,
                                            stdout=subprocess.PIPE)
                if (re.search(r'(?:libgl|opengl)',
                              str(ldd_output.stdout, 'utf-8'), re.IGNORECASE)):
                    self.info['library']['opengl'] = True
            except OSError as err:
                self.info['library']['error'] = err
                print("Failed to read output library.")
        return library

    def load_info_file(self):
        """ Load libretro-info file """
        path = os.path.join(self._args.working_directory, 'libretro-super',
                            'dist', 'info',
                            '{}.info'.format(self.libretro_soname))
        if os.path.isfile(path):
            with open(path, 'r') as info_ctx:
                self.info['libretro_info'] = {}
                for line in info_ctx:
                    name, var = line.partition('=')[::2]
                    self.info['libretro_info'][name.strip()] = \
                        shlex.split(var)[0]

    def load_assets(self):
        """ Process assets """
        # Loop over all images files in the repo
        self.info['assets'] = {}
        for asset in sorted(utils.list_all_files(self.path)):
            if os.path.splitext(asset)[1] not in ['.png', '.jpg', '.svg']:
                continue

            if asset == os.path.join(self.name, 'resources', 'icon.png'):
                self.info['assets']['icon'] = 'resources/icon.png'
            elif asset == os.path.join(self.name, 'resources', 'fanart.jpg'):
                self.info['assets']['fanart'] = 'resources/fanart.jpg'
            elif asset.startswith(os.path.join(self.name, 'resources',
                                               'screenshot')):
                self.info['assets'].setdefault('screenshots', []).append(
                    os.path.join('resources', os.path.basename(asset)))
            else:
                print("Unrecognized image detected: {}".format(asset))

    def process_addon_files(self):
        """ Generate addon files """
        self.load_assets()
        self.load_library_file()
        template_processor.TemplateProcessor.process(
            'addon', self.path, self.info)

    def clone(self):
        """ Clone / reset Git repository """
        print("  Fetching & resetting Git repo {}".format(self.name))
        if self._repo:
            self._args.git.clone_repo(
                self._repo, self._args.working_directory,
                reset=False if self._args.git_noclean else True)

    def commit(self):
        """ Commit changes to Git repository """
        print("  Commiting changes to Git repo {}".format(self.name))
        if self._repo:
            self._args.git.commit_repo(
                self._repo, self._args.working_directory,
                "Updated by kodi-game-scripting",
                squash=self._args.git_noclean)
            self.info['git']['diff'] = self._args.git.diff_repo(
                self._repo, self._args.working_directory)

    def push(self):
        """ Push addon changes to GitHub repository """
        print("  Pushing changes to GitHub repo {}".format(self.name))
        if self._repo and self._args.push_branch:
            self._args.git.push_repo(self._repo,
                                     self._args.working_directory,
                                     self._args.push_branch)


if __name__ == '__main__':
    main()
