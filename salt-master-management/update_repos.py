#!/usr/bin/env python
#
# update_repos.py
#
# Description: Updates and creates State and Pillar repos for Everbridge Salt
#              Masters. Run `update_pillar.py -h` for syntax.

import argparse
import git

# Adding our required arguments
parser = argparse.ArgumentParser()

# Location of the state directory on filesystem
parser.add_argument(
    "state_location", help="Location of state files on the filesystem (eg. /srv/salt)"
)

# Location of root pillar directory on filesystem
parser.add_argument(
    "pillar_location", help="Location of Pillar on the filesystem (eg. /srv/pillar)"
)

# The Salt environment we're using (qa1/qa2/stg1/prd1)
parser.add_argument("saltenv", help="Salt environment (dev3/qa1/qa2/stg1/prd1/prdeu1)")

args = parser.parse_args()

# Making local variables based on our args
state_location = args.state_location
pillar_location = args.pillar_location
saltenv = args.saltenv

# Create a list of all currently supported environments
supported_envs = [
    'qa1',
    'qa2',
    'stg1',
    'prd1',
    'prdeu1'
]

# Determine correct git repo location until we are finally moved over to GHE
#git_source_states = 'eb-github.com:eb-forks/fork-cep-salt-state.git'
git_source_states = 'https://cep-platform:evbg-gitlab--c-uzUz_7NYQHs_fB4k7@gitlab.eb-tools.com/engineering/platform/sre/cep-sre/cep-salt-state.git'

# note 'qa2' being in this list is intended only for the NEW atlas provisioned qa2 environment
#git_source_pillar = "eb-github.com:Development/cep-salt-pillar-%s.git" % saltenv
git_source_pillar = "https://cep-platform:evbg-gitlab--c-uzUz_7NYQHs_fB4k7@gitlab.eb-tools.com/engineering/platform/sre/cep-sre/cep-salt-pillar-%s.git" % saltenv

branch = "master"


def _update_repo(remote_repo, local_repo, salt_env, source_type):
    """
    Checks if specific filesystem path is a Git repo. If so, clears local
    changes and updates repo. If not, the repo is cloned to that location.
    """

    # Using a try/except to see if the specific path is a Git repo
    try:
        # Repo check
        local = git.Repo(local_repo)
        assert local.__class__ is git.Repo

        # Clear all local changes
        local.git.reset("--hard")
        local.git.clean("-fdx")

        # Fetch from remote
        local.git.fetch("--all", "--tags", "--prune")

        # Check out branch or tag
        if source_type == "branch":
            local.git.checkout(salt_env)
        elif source_type == "tag":
            local.git.checkout("tags/" + salt_env)

        # If this is a branch, `git pull`
        if source_type == "branch":
            local.remotes.origin.pull()

        return "Updated '%s' branch from '%s' repo in '%s'..." % (
            salt_env,
            remote_repo,
            local_repo,
        )

    # If folder doesn't exist or isn't a Git repo, we clone the Repo
    except (git.exc.NoSuchPathError, git.exc.InvalidGitRepositoryError):
        if source_type == "branch":
            branch = salt_env
        elif source_type == "tag":
            branch = "master"

        git.Repo.clone_from(remote_repo, local_repo, branch=branch)

        if source_type == "tag":
            # Fetch from remote
            local = git.Repo(local_repo)
            local.git.fetch("--all", "--tags", "--prune")

            # Check out tag
            local.git.checkout("tags/" + salt_env)

        return "Cloned '%s' repo in '%s'..." % (remote_repo, local_repo)


# Clone salt state repo
if saltenv in supported_envs:
    state_tree = _update_repo(
        "%s" % git_source_states, state_location, saltenv, "tag"
    )
else:
    state_tree = _update_repo(
        "%s" % git_source_states,
        state_location,
        'master',
        'branch'
    )
print(state_tree)

# Clone standard pillar repo
standard_pillar = _update_repo(
    "%s" % git_source_pillar, pillar_location, branch, "branch"
)
print(standard_pillar)
