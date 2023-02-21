import os

import jupyterhub
from packaging.version import Version as V

c = get_config()  # noqa

c.JupyterHub.spawner_class = "simple"
c.JupyterHub.last_activity_interval = 3

c.Authenticator.allowed_users = {f"test-{i}" for i in range(5)}

use_roles = V(jupyterhub.__version__) >= V("2")

if use_roles:
    c.JupyterHub.authenticator_class = "null"
else:
    c.JupyterHub.authenticator_class = "nullauthenticator.NullAuthenticator"

c.JupyterHub.services = [
    {
        "name": "pytest",
        "api_token": os.environ["TEST_ADMIN_TOKEN"],
        "admin": not use_roles,
    },
    {
        "name": "idle-culler",
        "api_token": os.environ["TEST_CULL_TOKEN"],
        "admin": not use_roles,
    },
]

# load_roles config is ignored if not recognized
c.JupyterHub.load_roles = [
    {
        "name": "pytest",
        "scopes": [
            "servers",
            "admin:users",
            "read:hub",
        ],
        "services": ["pytest"],
    },
    {
        "name": "idle-culler",
        "scopes": [
            "list:users",
            "read:users:activity",
            "read:servers",
            "delete:servers",
            # "admin:users", # if using --cull-users
        ],
        "services": ["idle-culler"],
    },
]
