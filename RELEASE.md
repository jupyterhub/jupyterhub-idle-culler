# How to make a release

`jupyterhub-idle-culler` is a package [available on
PyPI](https://pypi.org/project/jupyterhub-idle-culler/). These are instructions
on how to make a release on PyPI. The PyPI release is done automatically by a
GitHub workflow when a tag is pushed.

For you to follow along according to these instructions, you need:

- To have push rights to the [jupyterhub-idle-culler GitHub
  repository](https://github.com/jupyterhub/jupyterhub-idle-culler).

## Steps to make a release

1. Checkout main and make sure it is up to date.

   ```shell
   ORIGIN=${ORIGIN:-origin} # set to the canonical remote, e.g. 'upstream' if 'origin' is not the official repo
   git checkout main
   git fetch $ORIGIN main
   git reset --hard $ORIGIN/main
   # WARNING! This next command deletes any untracked files in the repo
   git clean -xfd
   ```

1. Update [CHANGELOG.md](CHANGELOG.md). Doing this can be made easier with the
   help of the
   [choldgraf/github-activity](https://github.com/choldgraf/github-activity)
   utility.

1. Set the `version` variable in [setup.py](setup.py) appropriately and make a
   commit.

   ```
   git add setup.py
   VERSION=...  # e.g. 1.2.3
   git commit -m "release $VERSION"
   ```

1. Reset the `version` variable in [setup.py](setup.py) appropriately with an
   incremented patch version and a `dev` element, then make a commit.

   ```
   git add setup.py
   git commit -m "back to dev"
   ```

1. Push your two commits to main.

   ```shell
   # first push commits without a tags to ensure the
   # commits comes through, because a tag can otherwise
   # be pushed all alone without company of rejected
   # commits, and we want have our tagged release coupled
   # with a specific commit in main
   git push $ORIGIN main
   ```

1. Create a git tag for the pushed release commit and push it.

   ```shell
   git tag -a $VERSION -m $VERSION HEAD~1

   # then verify you tagged the right commit
   git log

   # then push it
   git push $ORIGIN refs/tags/$VERSION
   ```
