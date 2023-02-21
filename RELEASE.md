# How to make a release

`jupyterhub-idle-culler` is a package available on [PyPI] and [conda-forge].
These are instructions on how to make a release.

## Pre-requisites

- Push rights to [jupyterhub/jupyterhub-idle-culler]

## Steps to make a release

1. Create a PR updating `CHANGELOG.md` with [github-activity] and continue only
   when its merged.

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

   Following this, the [CI system] will build and publish a release.

1. Reset the version back to dev, e.g. `2.1.0.dev` after releasing `2.0.0`

   ```shell
   tbump --no-tag ${NEXT_VERSION}.dev
   ```

1. Following the release to PyPI, an automated PR should arrive within 24 hours
   to [conda-forge/jupyterhub-idle-culler-feedstock] with instructions on
   releasing to conda-forge. You are welcome to volunteer doing this, but aren't
   required as part of making this release to PyPI.

[pypi]: https://pypi.org/project/jupyterhub-idle-culler/
[conda-forge]: https://anaconda.org/conda-forge/jupyterhub-idle-culler
[jupyterhub/jupyterhub-idle-culler]: https://github.com/jupyterhub/jupyterhub-idle-culler
[conda-forge/jupyterhub-idle-culler-feedstock]: https://github.com/conda-forge/jupyterhub-idle-culler-feedstock
[github-activity]: https://github.com/executablebooks/github-activity
[ci system]: https://github.com/jupyterhub/jupyterhub-idle-culler/actions/workflows/release.yaml
