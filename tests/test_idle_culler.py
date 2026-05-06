import sys
from datetime import timedelta
from subprocess import check_output
from unittest import mock

from tornado.log import app_log

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


def cull_arbiter_function(inactive, inactive_limit, server):
    return True


async def async_cull_arbiter_function(inactive, inactive_limit, server):
    return True


async def test_cull_idle(cull_idle, start_users, admin_request):
    assert await count_active_users(admin_request) == 0
    await start_users(3)
    assert await count_active_users(admin_request) == 3
    await cull_idle(inactive_limit=300, logger=app_log)
    # no change
    assert await count_active_users(admin_request) == 3

    # time travel into the future, everyone should be culled
    with mock.patch(
        "jupyterhub_idle_culler.utcnow", lambda: utcnow() + timedelta(seconds=600)
    ):
        await cull_idle(inactive_limit=300, logger=app_log)
    assert await count_active_users(admin_request) == 0


async def test_custom_cull_arbiter(cull_idle, start_users, admin_request):
    assert await count_active_users(admin_request) == 0
    await start_users(3)
    assert await count_active_users(admin_request) == 3
    await cull_idle(inactive_limit=300, logger=app_log, cull_arbiter=cull_arbiter_function)
    # time has not passed but the cull arbiter function returns true
    # so, everyone culled
    assert await count_active_users(admin_request) == 0


async def test_async_custom_cull_arbiter(cull_idle, start_users, admin_request):
    assert await count_active_users(admin_request) == 0
    await start_users(3)
    assert await count_active_users(admin_request) == 3
    await cull_idle(inactive_limit=300, logger=app_log, cull_arbiter=async_cull_arbiter_function)
    assert await count_active_users(admin_request) == 0


def test_help():
    check_output([sys.executable, "-m", "jupyterhub_idle_culler", "--help"])
