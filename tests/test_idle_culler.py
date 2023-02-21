import sys
from datetime import timedelta
from subprocess import check_output
from unittest import mock

from jupyterhub_idle_culler import utcnow


async def test_alive(hub_url, hub, admin_request):
    # just test that the hub itself is alive
    info = await admin_request("/info")
    print(info)


async def start_users(admin_request, n):
    for i in range(n):
        # start server
        await admin_request("/users/test-{n}/server", method="POST")
        await admin_request("/users/test-{n}/server/progress", method="GET")


async def count_active_users(admin_request):
    users = await admin_request("/users")
    active_users = 0
    for user in users:
        if any(s["ready"] for s in user["servers"].values()):
            active_users += 1
    return active_users


async def test_cull_idle(cull_idle, start_users, admin_request):
    assert await count_active_users(admin_request) == 0
    await start_users(3)
    assert await count_active_users(admin_request) == 3
    await cull_idle(inactive_limit=300)
    # no change
    assert await count_active_users(admin_request) == 3

    # time travel into the future, everyone should be culled
    with mock.patch(
        "jupyterhub_idle_culler.utcnow", lambda: utcnow() + timedelta(seconds=600)
    ):
        await cull_idle(inactive_limit=300)
    assert await count_active_users(admin_request) == 0


def test_help():
    check_output([sys.executable, "-m", "jupyterhub_idle_culler", "--help"])
