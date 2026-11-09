import os

c = get_config()  # noqa

c.JupyterHub.spawner_class = "simple"
c.JupyterHub.last_activity_interval = 3

c.Authenticator.allowed_users = {f"test-{i}" for i in range(5)}

c.JupyterHub.authenticator_class = "null"

c.JupyterHub.services = [
    {
        "name": "pytest",
        "api_token": os.environ["TEST_ADMIN_TOKEN"],
    },
    {
        "name": "idle-culler",
        "api_token": os.environ["TEST_CULL_TOKEN"],
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
