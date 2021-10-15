import asyncio
import inspect
import json
import os
import secrets
import shutil
import time
from functools import partial
from pathlib import Path
from subprocess import Popen
from tempfile import TemporaryDirectory
from unittest import mock

import psutil
import pytest
from tornado.httpclient import AsyncHTTPClient, HTTPClient

import jupyterhub_idle_culler

here = Path(__file__).parent


def pytest_collection_modifyitems(items):
    """This function is automatically run by pytest passing all collected test
    functions.

    We use it to add asyncio marker to all async tests and assert we don't use
    test functions that are async generators which wouldn't make sense.
    """
    for item in items:
        if inspect.iscoroutinefunction(item.obj):
            item.add_marker("asyncio")
        assert not inspect.isasyncgenfunction(item.obj)


@pytest.fixture(scope="session")
def admin_token():
    """Generate a token to use for admin requests"""
    token = secrets.token_hex(16)
    # jupyterhub subprocess loads this from the environment
    with mock.patch.dict(os.environ, {"TEST_ADMIN_TOKEN": token}):
        yield token


@pytest.fixture(scope="session")
def cull_token():
    """Generate a token to use for the cull service"""
    token = secrets.token_hex(16)
    # jupyterhub subprocess loads this from the environment
    with mock.patch.dict(os.environ, {"TEST_CULL_TOKEN": token}):
        yield token


@pytest.fixture(scope="session")
def hub_url():
    # hardcoded for now, but might want to override
    return "http://127.0.0.1:8000"


@pytest.fixture(scope="session")
def hub(hub_url, request, admin_token, cull_token):
    """Start JupyterHub, set up to use our tokens"""
    jupyterhub_config = here.joinpath("jupyterhub_config.py")
    with TemporaryDirectory() as td:
        shutil.copy(jupyterhub_config, Path(td).joinpath("jupyterhub_config.py"))
        hub = Popen(["jupyterhub", "--debug"], cwd=td)

        def cleanup():
            if hub.poll() is None:
                try:
                    for p in psutil.Process(hub.pid).children():
                        print(f"terminating {p}")
                        p.terminate()
                except psutil.ProcessLookupError:
                    pass
            print("terminating hub")
            hub.terminate()

        request.addfinalizer(cleanup)

        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                HTTPClient().fetch(hub_url + "/hub/api")
            except Exception as e:
                print(e)
                if hub.poll() is not None:
                    raise RuntimeError("hub failed to start")
                time.sleep(1)
                continue
            else:
                break

        yield hub


async def api_request(hub_url, path, token=None, parse_json=True, **kwargs):
    """Make an API request to the Hub, parsing JSON responses"""
    hub_url = hub_url.rstrip("/")
    headers = kwargs.setdefault("headers", {})
    headers["Authorization"] = f"token {token}"

    path = path.lstrip("/")
    url = f"{hub_url}/hub/api/{path}"
    print(url, kwargs)
    resp = await AsyncHTTPClient().fetch(url, **kwargs)
    if not parse_json:
        return resp
    if resp.body:
        return json.loads(resp.body.decode("utf8"))
    else:
        return None


@pytest.fixture
def admin_request(hub, hub_url, admin_token):
    """make an API request to a path with an admin token"""
    return partial(api_request, hub_url, token=admin_token)


@pytest.fixture
def start_users(admin_request, request):
    """Returns a function to start a number of users"""

    def stop_user(i):
        asyncio.get_event_loop().run_until_complete(
            admin_request(f"/users/test-{i}/server", method="DELETE")
        )

    async def start_users(n):
        for i in range(n):
            # start servers
            await admin_request(f"/users/test-{i}/server", body="", method="POST")
            request.addfinalizer(partial(stop_user, i))
        for i in range(n):
            # wait for servers to be ready via progress API
            await admin_request(
                f"/users/test-{i}/server/progress", parse_json=False, method="GET"
            )

    return start_users


@pytest.fixture
def cull_idle(hub_url, cull_token):
    """Returns `cull_idle` configured to talk to our Hub"""
    return partial(
        jupyterhub_idle_culler.cull_idle, hub_url + "/hub/api", api_token=cull_token
    )
