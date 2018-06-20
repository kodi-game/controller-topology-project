#
# Copyright (C) 2018 The Magnificent Mr. B
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
# with this program; if not, see <http://www.gnu.org/licenses/>.
#

"""
Process Kodi Game add-ons and generate button maps
"""

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
    addons = GameAddons(args)
    addons.process()
    addons.summary()


class GameAddons:
    """
    Process Kodi game add-ons
    """
    def __init__(self, args):
        """ Initialize instance """
        self._args = args
        self._prepareenvironment()

    def _prepareenvironment(self):
        """
        Prepare and check the environment (directories and config)
        """
        # Create Add-on objects
        for gamename in sorted(config.ADDONS):
            addonname = '{}{}'.format(config.GITHUB_ADDON_PREFIX, gamename)

            repo = repos.get(addonname, None)

            if self._args.git and not repo:
                print("Creating GitHub repository {}".format(addonname))
                repo = self._args.git.createrepo(
                    config.GITHUB_ORGANIZATION, addonname)

            self._addons[gamename] = Addon(addonname,
                                           gamename,
                                           repo,
                                           self._args
            )

        print("Processing the following addons: {}".format(
            ', '.join(self._addons)))

        # Clone/Fetch repos
        if self._args.git:
            for addon in self._addons.values():
                addon.clone()

    def process(self):
        """
        Process list of add-ons from config
        """

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
        """
        Print summary
        """
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
    """
    Process a single Kodi controller add-on
    """
    def __init__(self, addonname, repo, args):
        self.name = addonname
        self._repo = repo
        self._args = args
        self.path = os.path.join(self._args.workingdirectory, addonname)

        if not os.path.isdir(self.path):
            print("Initializing empty add-on directory: {}".format(
                addonname
            ))
            utils.ensuredirectoryexists(self.path)

        self.info = {
            'addon': self.name,
            'repo': self._repo,
            'repobranch': 'master'
        }

    def processbuttonmap(self):
        """
        Generate button map
        """
        # TODO
        pass

    def clone(self):
        """
        Clone / reset Git repository
        """
        print("  Fetching & resetting Git repo {}".format(self.name))

        self._args.git.clonerepo(
            self._repo,
            self._args.workingdirectory,
            reset=False if self._args.gitnoclean else True)

    def commit(self):
        """
        Commit changes to Git repository
        """
        print("  Committing changes to Git repo {}".format(self.name))

        self._args.git.commitrepo(
            self._repo,
            self._args.workingdirectory,
            "Updated by controller-topology-project",
            squash=self._args.gitnoclean
        )

    def push(self):
        """
        Push add-on changes to GitHub repository
        """
        print("  Pushing changes to GitHub repo {}".format(self.name))

        if self._repo and self._args.push_branch:
            self._args.git.pushrepo(self._repo,
                                    self._args.workingdirectory,
                                    self._args.pushbranch)
