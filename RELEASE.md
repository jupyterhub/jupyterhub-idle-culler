# How to make a release

`jupyterhub-idle-culler` is a package available on [PyPI][] and [conda-forge][].
These are instructions on how to make a release.

## Pre-requisites

- Push rights to [jupyterhub/jupyterhub-idle-culler][]
- Push rights to [conda-forge/jupyterhub-idle-culler-feedstock][]

## Steps to make a release

1. Create a PR updating `docs/source/changelog.md` with [github-activity][] and
   continue only when its merged.

   ```shell
   pip install github-activity

   github-activity --heading-level=3 jupyterhub/jupyterhub-idle-culler
   ```

1. Checkout main and make sure it is up to date.

   ```shell
   git checkout main
   git fetch origin main
   git reset --hard origin/main
   ```

1. Update the version, make commits, and push a git tag with `tbump`.

   ```shell
   pip install tbump
   tbump --dry-run ${VERSION}

   tbump ${VERSION}
   ```
