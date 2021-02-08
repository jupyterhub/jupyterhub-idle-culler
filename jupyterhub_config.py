import sys

# run cull-idle as a service

c.JupyterHub.services = [  # noqa: F821
    {
        "name": "cull-idle",
        "admin": True,
        "command": [sys.executable, "cull_idle_servers.py", "--timeout=3600"],
    }
]
