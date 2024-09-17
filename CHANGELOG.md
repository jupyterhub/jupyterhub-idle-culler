# Changelog

This changelog is maintained manually with assistance of
[`github-activity`](https://github.com/executablebooks/github-activity).

## 1.4

### 1.4.0 - 2024-09-17

([full changelog](https://github.com/jupyterhub/jupyterhub-idle-culler/compare/1.3.1...1.4.0))

#### New features added

- add options to cull named servers and default servers separately [#74](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/74) ([@HCharlie](https://github.com/HCharlie), [@yuvipanda](https://github.com/yuvipanda))

#### Continuous integration improvements

- ci: test against jupyterhub 5 [#80](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/80) ([@consideRatio](https://github.com/consideRatio))

#### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/en/latest/#how-does-this-tool-define-contributions-in-the-reports).

([GitHub contributors page for this release](https://github.com/jupyterhub/jupyterhub-idle-culler/graphs/contributors?from=2024-02-28&to=2024-09-17&type=c))

@consideRatio ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3AconsideRatio+updated%3A2024-02-28..2024-09-17&type=Issues)) | @HCharlie ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3AHCharlie+updated%3A2024-02-28..2024-09-17&type=Issues)) | @yuvipanda ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Ayuvipanda+updated%3A2024-02-28..2024-09-17&type=Issues))

## 1.3

### 1.3.1 - 2024-02-26

Fixes missing dependency on `packaging` in 1.3.0.

([full changelog](https://github.com/jupyterhub/jupyterhub-idle-culler/compare/1.3.0...1.3.1))

#### Bugs fixed

- missing dependency on packaging [#70](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/70) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))

#### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/en/latest/#how-does-this-tool-define-contributions-in-the-reports).

([GitHub contributors page for this release](https://github.com/jupyterhub/jupyterhub-idle-culler/graphs/contributors?from=2024-02-26&to=2024-02-26&type=c))

@consideRatio ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3AconsideRatio+updated%3A2024-02-26..2024-02-26&type=Issues)) | @minrk ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Aminrk+updated%3A2024-02-26..2024-02-26&type=Issues))

### 1.3.0 - 2024-02-26

`jupyterhub-idle-culler` now functions with Python 3.12.

#### Bugs fixed

- fix type of request_timeout when $JUPYTERHUB_REQUEST_TIMEOUT is set [#49](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/49) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))

#### Maintenance and upkeep improvements

- Add dependabot to bump github actions and misc ci updates [#65](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/65) ([@consideRatio](https://github.com/consideRatio))
- maint: require py37, fix tests, use pyupgrade/isort/autoflake, use pyproject.toml, more f-strings [#58](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/58) ([@consideRatio](https://github.com/consideRatio), [@yuvipanda](https://github.com/yuvipanda), [@minrk](https://github.com/minrk), [@manics](https://github.com/manics))
- Add a test [#39](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/39) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))

#### Documentation improvements

- Refresh README.md [#57](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/57) ([@consideRatio](https://github.com/consideRatio), [@minrk](https://github.com/minrk))
- docs: fix typo in README.md [#54](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/54) ([@jincheng9](https://github.com/jincheng9), [@consideRatio](https://github.com/consideRatio))
- docs: fix omission of required read:servers scope [#41](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/41) ([@consideRatio](https://github.com/consideRatio), [@minrk](https://github.com/minrk))

#### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/en/latest/#how-does-this-tool-define-contributions-in-the-reports).

([GitHub contributors page for this release](https://github.com/jupyterhub/jupyterhub-idle-culler/graphs/contributors?from=2021-10-15&to=2024-02-26&type=c))

@consideRatio ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3AconsideRatio+updated%3A2021-10-15..2024-02-26&type=Issues)) | @jincheng9 ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Ajincheng9+updated%3A2021-10-15..2024-02-26&type=Issues)) | @manics ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Amanics+updated%3A2021-10-15..2024-02-26&type=Issues)) | @minrk ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Aminrk+updated%3A2021-10-15..2024-02-26&type=Issues)) | @yuvipanda ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Ayuvipanda+updated%3A2021-10-15..2024-02-26&type=Issues))

## 1.2

### 1.2.1 - 2021-10-15

#### Enhancements made

- Avoid the need for read:hub scope [#35](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/35) ([@consideRatio](https://github.com/consideRatio))

#### Documentation improvements

- docs: change from master branch to main [#37](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/37) ([@consideRatio](https://github.com/consideRatio))
- Minor tweaks to the readme [#34](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/34) ([@consideRatio](https://github.com/consideRatio))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/jupyterhub-idle-culler/graphs/contributors?from=2021-09-20&to=2021-10-15&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3AconsideRatio+updated%3A2021-09-20..2021-10-15&type=Issues)

### 1.2.0 - 2021-09-20

#### New features added

- Flag --cull-admin-users added (default: true) for when --cull-users=true [#24](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/24) ([@anderoonies](https://github.com/anderoonies))

#### Enhancements made

- support JupyterHub 2.0 API pagination [#30](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/30) ([@minrk](https://github.com/minrk))
- Change default request_timeout and allow override [#27](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/27) ([@mriedem](https://github.com/mriedem))
- Filter users on the server if possible [#22](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/22) ([@mriedem](https://github.com/mriedem))

#### Documentation improvements

- document required scopes for non-admin permissions with hub 2.0 [#32](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/32) ([@minrk](https://github.com/minrk))
- Add documentation about how it works in README.md [#28](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/28) ([@consideRatio](https://github.com/consideRatio))
- Update README CLI's options list and fix indentation issues for --help [#23](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/23) ([@consideRatio](https://github.com/consideRatio))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/jupyterhub-idle-culler/graphs/contributors?from=2021-03-05&to=2021-09-20&type=c))

[@anderoonies](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Aanderoonies+updated%3A2021-03-05..2021-09-20&type=Issues) | [@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3AconsideRatio+updated%3A2021-03-05..2021-09-20&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Aminrk+updated%3A2021-03-05..2021-09-20&type=Issues) | [@mriedem](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Amriedem+updated%3A2021-03-05..2021-09-20&type=Issues) | [@yuvipanda](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Ayuvipanda+updated%3A2021-03-05..2021-09-20&type=Issues)

## 1.1

### 1.1.0 - 2021-03-05

#### Enhancements made

- jupyterhub_idle_culler: Support SSL when internal_ssl is enabled on jupyterhub [#11](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/11) ([@chancez](https://github.com/chancez))

#### Maintenance and upkeep improvements

- General maintenance: readme badges, autoformatting, flake8 test, .gitignore, changelog [#20](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/20) ([@consideRatio](https://github.com/consideRatio))

#### Documentation improvements

- Add pypi installation instructions [#17](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/17) ([@manics](https://github.com/manics))
- Consolidate docs in README [#15](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/15) ([@yuvipanda](https://github.com/yuvipanda))
- Docs: Add closing bracket [#12](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/12) ([@1kastner](https://github.com/1kastner))
- Add more explanation regarding the project purpose [#7](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/7) ([@1kastner](https://github.com/1kastner))
- Simple documentation of service capabilities [#6](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/6) ([@1kastner](https://github.com/1kastner))
- Package license [#3](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/3) ([@ericdill](https://github.com/ericdill))
- Fixed typo in readme [#2](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/2) ([@riyasyash](https://github.com/riyasyash))

#### Continuous integration

- Add publish to PyPI GitHub workflow. [#19](https://github.com/jupyterhub/jupyterhub-idle-culler/pull/19) ([@manics](https://github.com/manics))

#### Contributors to this release

[@1kastner](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3A1kastner+updated%3A2020-04-28..2021-01-28&type=Issues) | [@betatim](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Abetatim+updated%3A2020-04-28..2021-01-28&type=Issues) | [@chancez](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Achancez+updated%3A2020-04-28..2021-01-28&type=Issues) | [@ericdill](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Aericdill+updated%3A2020-04-28..2021-01-28&type=Issues) | [@manics](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Amanics+updated%3A2020-04-28..2021-01-28&type=Issues) | [@meeseeksmachine](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Ameeseeksmachine+updated%3A2020-04-28..2021-01-28&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Aminrk+updated%3A2020-04-28..2021-01-28&type=Issues) | [@riyasyash](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Ariyasyash+updated%3A2020-04-28..2021-01-28&type=Issues) | [@rkdarst](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Arkdarst+updated%3A2020-04-28..2021-01-28&type=Issues) | [@yuvipanda](https://github.com/search?q=repo%3Ajupyterhub%2Fjupyterhub-idle-culler+involves%3Ayuvipanda+updated%3A2020-04-28..2021-01-28&type=Issues)

## 1.0

### 1.0.0 - 2020-04-27

Initial release as a standalone Python package.
