==============================
JupyterHub Idle Culler Service
==============================

``jupyterhub-idle-culler`` provides a JupyterHub service to cull and
shut down idle notebook servers and users on a JupyterHub deployment.


Setup
=====

As a hub managed service
------------------------

In ``jupyterhub_config.py``, add the following dictionary for the idle-culler
Service to the `c.JupyterHub.services` list:

.. code:: python

    c.JupyterHub.services = [
        {
            'name': 'idle-culler',
            'admin': True,
            'command': [
                sys.executable,
                '-m', 'jupyterhub-idle-culler,
                '--timeout=3600'
            ],
        }
    ]

where:

- ``'admin': True`` indicates that the Service requires admin permissions so
  it can shut down arbitrary user notebooks, and
- ``'command'`` indicates that the Service will be managed by the Hub.

As a standalone script
----------------------

``jupyterhub-idle-culler`` can also be run as a standalone script. It can
access the hub's api with a service token. The service token must have
admin privileges.

Generate an API token and store it in a ``JUPYTERHUB_API_TOKEN`` environment
variable. Then start ``jupyterhub-idle-culler`` manually

.. code:: bash

    export JUPYTERHUB_API_TOKEN=$(jupyterhub token)
    python3 -m jupyterhub-idle-culler[--timeout=900] [--url=http://localhost:8081/hub/api]
