# JupyterHub Idle Culler Service

[![GitHub Workflow Status - Test](https://img.shields.io/github/workflow/status/jupyterhub/jupyterhub-idle-culler/Test?logo=github&label=tests)](https://github.com/jupyterhub/jupyterhub-idle-culler/actions)
[![Latest PyPI version](https://img.shields.io/pypi/v/jupyterhub-idle-culler?logo=pypi&logoColor=white)](https://pypi.python.org/pypi/jupyterhub-idle-culler)
[![GitHub](https://img.shields.io/badge/issue_tracking-github-blue?logo=github)](https://github.com/jupyterhub/jupyterhub-idle-culler/issues)
[![Discourse](https://img.shields.io/badge/help_forum-discourse-blue?logo=discourse)](https://discourse.jupyter.org/c/jupyterhub)
[![Gitter](https://img.shields.io/badge/social_chat-gitter-blue?logo=gitter)](https://gitter.im/jupyterhub/jupyterhub)

`jupyterhub-idle-culler` provides a JupyterHub service to identify and shut down idle or long-running Jupyter Notebook servers.
The exact actions performed are dependent on the used spawner for the Jupyter Notebook server (e.g. the default [LocalProcessSpawner](https://jupyterhub.readthedocs.io/en/stable/api/spawner.html#localprocessspawner>), [kubespawner](https://github.com/jupyterhub/kubespawner), or [dockerspawner](https://github.com/jupyterhub/dockerspawner)).
In addition, if explicitly requested, all users whose Jupyter Notebook servers have been shut down this way are deleted as JupyterHub users from the internal database. This neither affects the authentication method which continues to allow those users to log in nor does it delete persisted user data (e.g. stored in docker volumes for dockerspawner or in persisted volumes for kubespawner).

## Setup

### Installation

```bash
pip install jupyterhub-idle-culler
```

### As a hub managed service

In `jupyterhub_config.py`, add the following dictionary for the idle-culler
Service to the `c.JupyterHub.services` list:

```python
c.JupyterHub.services = [
    {
        'name': 'idle-culler',
        'admin': True,
        'command': [
            sys.executable,
            '-m', 'jupyterhub_idle_culler',
            '--timeout=3600'
        ],
    }
]
```

where:

- `'admin': True` indicates that the Service requires admin permissions so
  it can shut down arbitrary user notebooks, and
- `'command'` indicates that the Service will be managed by the Hub.

### As a standalone script

`jupyterhub-idle-culler` can also be run as a standalone script. It can
access the hub's api with a service token. The service token must have
admin privileges.

Generate an API token and store it in a `JUPYTERHUB_API_TOKEN` environment
variable. Then start `jupyterhub-idle-culler` manually

```bash
export JUPYTERHUB_API_TOKEN=$(jupyterhub token)
python3 -m jupyterhub-idle-culler [--timeout=900] [--url=http://localhost:8081/hub/api]
```

The command line interface also gives a quick overview of the different options for configuration.

```
  --concurrency                    Limit the number of concurrent requests made
                                   to the Hub.                  Deleting a lot
                                   of users at the same time can slow down the
                                   Hub,                 so limit the number of
                                   API requests we have outstanding at any
                                   given time.                  (default 10)
  --cull-every                     The interval (in seconds) for checking for
                                   idle servers to cull (default 0)
  --cull-users                     Cull users in addition to servers.
                                   This is for use in temporary-user cases such
                                   as tmpnb. (default False)
  --max-age                        The maximum age (in seconds) of servers that
                                   should be culled even if they are active
                                   (default 0)
  --remove-named-servers           Remove named servers in addition to stopping
                                   them.             This is useful for a
                                   BinderHub that uses authentication and named
                                   servers. (default False)
  --timeout                        The idle timeout (in seconds) (default 600)
  --url                            The JupyterHub API URL
```

## Caveats

1. last_activity is not updated with high frequency, so cull timeout should be
   greater than the sum of:

   - single-user websocket ping interval (default: 30 seconds)
   - `JupyterHub.last_activity_interval` (default: 5 minutes)

2. The same `--timeout` and `--max-age` values are used to cull
   users and users' servers. If you want a different value for users and servers,
   you should add this script to the services list twice, just with different
   `name`s, different values, and one with the `--cull-users` option.
