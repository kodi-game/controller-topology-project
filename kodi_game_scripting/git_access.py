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

""" Access GitHub API and Git Repos """

import collections
import functools
import os
import re

import git
import github

from . import credentials
from . import utils

GitRepo = collections.namedtuple('GitRepo', 'name url ssh_url')


class Git:
    """
    Access GitHub API and Git repos
    """
    def __init__(self, auth=False):
        """
        Initialize Git instance
        """
        try:
            if auth:
                cred = credentials.Credentials('github')
                username, password = cred.load()
            else:
                username, password = None, None

            self._github = github.Github(username, password)

            rate = self._github.get_rate_limit().rate
            print("GitHub API rate: limit: {}, remaining: {}, reset: {}"
                  .format(rate.limit, rate.remaining, rate.reset.isoformat()))

            if auth:
                cred.save(username, password)
        except github.BadCredentialsException:
            if auth:
                cred.clean()
            raise ValueError("Authentication to GitHub failed")

    @functools.lru_cache()
    def get_repos(self, organization, repo_filter):
        """ Query all GitHub repos of the given organization that matches
            the given filter. Since API calls are limited, cache results. """
        repos = {
            repo.name: GitRepo(repo.name, repo.clone_url, repo.ssh_url)
            for repo in self._github.get_organization(organization).get_repos()
            if re.search(repo_filter, repo.name)
        }
        return repos

    def create_repo(self, organization, name):
        """ Create a new repo on GitHub """
        repo = self._github.get_organization(organization).create_repo(
            name, auto_init=True)
        self.get_repos.cache_clear()  # pylint: disable=no-member
        return GitRepo(repo.name, repo.clone_url, repo.ssh_url)

    def clone_repos(self, repos, directory):
        """ Clone list of repos into directory

            If the repos exist all changes will be discarded. """
        for repo in repos:
            self.clone_repo(repo, directory)

    @classmethod
    def is_git_repo(cls, path):
        """ Determine if a path is a Git repository """
        try:
            _ = git.Repo(path).git_dir  # flake8: noqa
            return True
        except git.exc.InvalidGitRepositoryError:  # pylint: disable=no-member
            return False

    @classmethod
    def has_remote_branch(cls, path, branch):
        """ Determines if a branch exists on the remote origin """
        gitrepo = git.Repo(path)
        return gitrepo.git.ls_remote('origin', branch, heads=True)

    @classmethod
    def clone_repo(cls, repo, path, reset=True):
        """ Clone repo into directory

            If the repo exists all changes will be discarded. """
        git_dir = os.path.join(path, repo.name)
        utils.ensure_directory_exists(git_dir)
        if not cls.is_git_repo(git_dir):
            print("New repo, creating {}".format(repo.name))
            gitrepo = git.Repo.init(git_dir)
            origin = gitrepo.create_remote('origin', repo.url)
        else:
            print("Existing repo {}".format(repo.name))
            gitrepo = git.Repo(git_dir)
            origin = gitrepo.remotes.origin
        origin.set_url(repo.ssh_url, push=True)
        print("Fetching {}".format(repo.name))
        origin.fetch('master')
        if reset:
            print("Resetting {}".format(repo.name))
            gitrepo.git.reset('--hard', 'origin/master')
        else:
            print("Rebasing {}".format(repo.name))
            gitrepo.git.rebase('origin/master')
        print("Cleaning local changes {}".format(repo.name))
        gitrepo.git.reset()
        gitrepo.git.clean('-xffd')

    @classmethod
    def commit_repo(cls, repo, path,  # pylint: disable=too-many-arguments
                    message, directory=None, force=False, squash=False):
        """ Create commit in repo """
        git_dir = os.path.join(path, repo.name)
        gitrepo = git.Repo(git_dir)
        if directory:
            gitrepo.git.add(directory, force=force)
        else:
            gitrepo.git.add(all=True, force=force)
        if squash:
            gitrepo.git.reset('origin/master', soft=True)
        if gitrepo.is_dirty():
            gitrepo.index.commit(message)

    @classmethod
    def diff_repo(cls, repo, path):
        """ Diff commits in repo """
        git_dir = os.path.join(path, repo.name)
        gitrepo = git.Repo(git_dir)
        return gitrepo.git.diff("origin/master", gitrepo.head.commit)

    @classmethod
    def push_repo(cls, repo, path, branch):
        """ Create commit in repo """
        git_dir = os.path.join(path, repo.name)
        gitrepo = git.Repo(git_dir)
        if gitrepo.is_dirty():
            raise ValueError("Skipping, repository is dirty")
        origin = gitrepo.remotes.origin
        origin.push('HEAD:{}'.format(branch),
                    force=False if branch == 'master' else True)

def test_clone_single_repo():
    """ Tests cloning a single repo """
    test_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        'tests', os.path.splitext(os.path.basename(__file__))[0])
    utils.ensure_directory_exists(test_dir, clean=True)

    gitaccess = Git()
    gitaccess.clone_repo(
        GitRepo('kodi-game-scripting',
                'https://github.com/fetzerch/kodi-game-scripting', ''),
        test_dir)
    gitaccess.clone_repos(
        [GitRepo('kodi-game-scripting',
                 'https://github.com/fetzerch/kodi-game-scripting', '')],
        test_dir)


def test_github_repos():
    """ Tests getting a repo list """
    gitaccess = Git()
    repos = gitaccess.get_repos('kodi-game', r'game\.libretro\.')
    print(repos)
    assert repos
