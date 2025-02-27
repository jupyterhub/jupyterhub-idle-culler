#!/usr/bin/env python3
"""
Monitor & Cull idle single-user servers and users
"""

import asyncio
import json
import logging
import os
import ssl
import sys
from datetime import datetime, timezone
from functools import partial
from textwrap import dedent
from urllib.parse import quote

import dateutil.parser
from packaging.version import Version as V
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.httputil import url_concat
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.log import LogFormatter
from traitlets import Bool, Int, Unicode, default
from traitlets.config import Application

__version__ = "1.4.1.dev"

STATE_FILTER_MIN_VERSION = V("1.3.0")


def parse_date(date_string):
    """Parse a timestamp

    If it doesn't have a timezone, assume utc

    Returned datetime object will always be timezone-aware
    """
    dt = dateutil.parser.parse(date_string)
    if not dt.tzinfo:
        # assume naive timestamps are UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def format_td(td):
    """
    Nicely format a timedelta object

    as HH:MM:SS
    """
    if td is None:
        return "unknown"
    if isinstance(td, str):
        return td
    seconds = int(td.total_seconds())
    h = seconds // 3600
    seconds = seconds % 3600
    m = seconds // 60
    seconds = seconds % 60
    return f"{h:02}:{m:02}:{seconds:02}"


def make_ssl_context(keyfile, certfile, cafile=None, verify=True, check_hostname=True):
    """Setup context for starting an https server or making requests over ssl."""
    if not keyfile or not certfile:
        return None
    purpose = ssl.Purpose.SERVER_AUTH if verify else ssl.Purpose.CLIENT_AUTH
    ssl_context = ssl.create_default_context(purpose, cafile=cafile)
    ssl_context.load_default_certs(purpose)
    ssl_context.load_cert_chain(certfile, keyfile)
    ssl_context.check_hostname = check_hostname
    return ssl_context


def utcnow():
    """Return timezone-aware datetime for right now"""
    # Only a standalone function for mocking purposes
    return datetime.now(timezone.utc)


async def cull_idle(
    url,
    api_token,
    inactive_limit,
    logger,
    cull_users=False,
    remove_named_servers=False,
    max_age=0,
    concurrency=10,
    ssl_enabled=False,
    internal_certs_location="",
    cull_admin_users=True,
    api_page_size=0,
    cull_default_servers=True,
    cull_named_servers=True,
):
    """Shutdown idle single-user servers

    If cull_users, inactive *users* will be deleted as well.
    """
    defaults = {
        # GET /users may be slow if there are thousands of users and we
        # don't do any server side filtering so default request timeouts
        # to 60 seconds rather than tornado's 20 second default.
        "request_timeout": int(os.environ.get("JUPYTERHUB_REQUEST_TIMEOUT") or 60)
    }
    if ssl_enabled:
        ssl_context = make_ssl_context(
            f"{internal_certs_location}/hub-internal/hub-internal.key",
            f"{internal_certs_location}/hub-internal/hub-internal.crt",
            f"{internal_certs_location}/hub-ca/hub-ca.crt",
        )

        logger.debug("ssl_enabled is Enabled: %s", ssl_enabled)
        logger.debug("internal_certs_location is %s", internal_certs_location)
        defaults["ssl_options"] = ssl_context

    AsyncHTTPClient.configure(None, defaults=defaults)
    client = AsyncHTTPClient()

    if concurrency:
        semaphore = asyncio.Semaphore(concurrency)

        async def fetch(req):
            """client.fetch wrapped in a semaphore to limit concurrency"""
            await semaphore.acquire()
            try:
                return await client.fetch(req)
            finally:
                semaphore.release()

    else:
        fetch = client.fetch

    async def fetch_paginated(req):
        """Make a paginated API request

        async generator, yields all items from a list endpoint
        """
        req.headers["Accept"] = "application/jupyterhub-pagination+json"
        url = req.url
        resp_future = asyncio.ensure_future(fetch(req))
        page_no = 1
        item_count = 0
        while resp_future is not None:
            response = await resp_future
            resp_future = None
            resp_model = json.loads(response.body.decode("utf8", "replace"))

            if isinstance(resp_model, list):
                # handle pre-2.0 response, no pagination
                items = resp_model
            else:
                # paginated response
                items = resp_model["items"]

                next_info = resp_model["_pagination"]["next"]
                if next_info:
                    page_no += 1
                    logger.info(f"Fetching page {page_no} {next_info['url']}")
                    # submit next request
                    req.url = next_info["url"]
                    resp_future = asyncio.ensure_future(fetch(req))

            for item in items:
                item_count += 1
                yield item

        logger.debug(f"Fetched {item_count} items from {url} in {page_no} pages")

    # Starting with jupyterhub 1.3.0 the users can be filtered in the server
    # using the `state` filter parameter. "ready" means all users who have any
    # ready servers (running, not pending).
    auth_header = {"Authorization": f"token {api_token}"}
    resp = await fetch(HTTPRequest(url=f"{url}/", headers=auth_header))

    resp_model = json.loads(resp.body.decode("utf8", "replace"))
    state_filter = V(resp_model["version"]) >= STATE_FILTER_MIN_VERSION

    now = utcnow()

    async def handle_server(user, server_name, server, max_age, inactive_limit):
        """Handle (maybe) culling a single server

        "server" is the entire server model from the API.

        Returns True if server is now stopped (user removable),
        False otherwise.
        """
        log_name = user["name"]
        if server_name:
            log_name = f"{user['name']}/{server_name}"
        if server.get("pending"):
            logger.warning(
                f"Not culling server {log_name} with pending {server['pending']}"
            )
            return False

        # jupyterhub < 0.9 defined 'server.url' once the server was ready
        # as an *implicit* signal that the server was ready.
        # 0.9 adds a dedicated, explicit 'ready' field.
        # By current (0.9) definitions, servers that have no pending
        # events and are not ready shouldn't be in the model,
        # but let's check just to be safe.

        if not server.get("ready", bool(server["url"])):
            logger.warning(
                f"Not culling not-ready not-pending server {log_name}: {server}"
            )
            return False

        if server.get("started"):
            age = now - parse_date(server["started"])
        else:
            # started may be undefined on jupyterhub < 0.9
            age = None

        # check last activity
        # last_activity can be None in 0.9
        if server["last_activity"]:
            inactive = now - parse_date(server["last_activity"])
        else:
            # no activity yet, use start date
            # last_activity may be None with jupyterhub 0.9,
            # which introduces the 'started' field which is never None
            # for running servers
            inactive = age

        # CUSTOM CULLING TEST CODE HERE
        # Add in additional server tests here.  Return False to mean "don't
        # cull", True means "cull immediately", or, for example, update some
        # other variables like inactive_limit.
        #
        # Here, server['state'] is the result of the get_state method
        # on the spawner.  This does *not* contain the below by
        # default, you may have to modify your spawner to make this
        # work.  The `user` variable is the user model from the API.
        #
        # if server['state']['profile_name'] == 'unlimited'
        #     return False
        # inactive_limit = server['state']['culltime']

        is_default_server = server_name == ""
        is_named_server = server_name != ""

        should_cull = (
            inactive is not None
            and inactive.total_seconds() >= inactive_limit
            and (
                (cull_default_servers and is_default_server)
                or (cull_named_servers and is_named_server)
            )
        )
        if should_cull:
            logger.info(
                f"Culling server {log_name} (inactive for {format_td(inactive)})"
            )

        if max_age and not should_cull:
            # only check started if max_age is specified
            # so that we can still be compatible with jupyterhub 0.8
            # which doesn't define the 'started' field
            if age is not None and age.total_seconds() >= max_age:
                logger.info(
                    "Culling server %s (age: %s, inactive for %s)",
                    log_name,
                    format_td(age),
                    format_td(inactive),
                )
                should_cull = True

        if not should_cull:
            logger.debug(
                "Not culling server %s (age: %s, inactive for %s)",
                log_name,
                format_td(age),
                format_td(inactive),
            )
            return False

        body = None
        if server_name:
            # culling a named server
            # A named server can be stopped and kept available to the user
            # for starting again or stopped and removed. To remove the named
            # server we have to pass an additional option in the body of our
            # DELETE request.
            delete_url = "{}/users/{}/servers/{}".format(
                url,
                quote(user["name"]),
                quote(server["name"]),
            )
            if remove_named_servers:
                body = json.dumps({"remove": True})
        else:
            delete_url = "{}/users/{}/server".format(
                url,
                quote(user["name"]),
            )

        req = HTTPRequest(
            url=delete_url,
            method="DELETE",
            headers=auth_header,
            body=body,
            allow_nonstandard_methods=True,
        )
        resp = await fetch(req)
        if resp.code == 202:
            logger.warning(f"Server {log_name} is slow to stop")
            # return False to prevent culling user with pending shutdowns
            return False
        return True

    async def handle_user(user):
        """Handle one user.

        Create a list of their servers, and async exec them.  Wait for
        that to be done, and if all servers are stopped, possibly cull
        the user.
        """
        # shutdown servers first.
        # Hub doesn't allow deleting users with running servers.
        # jupyterhub 0.9 always provides a 'servers' model.
        # 0.8 only does this when named servers are enabled.
        if "servers" in user:
            servers = user["servers"]
        else:
            # jupyterhub < 0.9 without named servers enabled.
            # create servers dict with one entry for the default server
            # from the user model.
            # only if the server is running.
            servers = {}
            if user["server"]:
                servers[""] = {
                    "last_activity": user["last_activity"],
                    "pending": user["pending"],
                    "url": user["server"],
                }
        server_futures = [
            handle_server(user, server_name, server, max_age, inactive_limit)
            for server_name, server in servers.items()
        ]
        if server_futures:
            results = await asyncio.gather(*server_futures)
        else:
            results = []

        if not cull_users:
            return
        # some servers are still running, cannot cull users
        still_alive = len(results) - sum(results)
        if still_alive:
            logger.debug(
                "Not culling user %s with %i servers still alive",
                user["name"],
                still_alive,
            )
            return False

        should_cull = False
        if user.get("created"):
            age = now - parse_date(user["created"])
        else:
            # created may be undefined on jupyterhub < 0.9
            age = None

        # check last activity
        # last_activity can be None in 0.9
        if user["last_activity"]:
            inactive = now - parse_date(user["last_activity"])
        else:
            # no activity yet, use start date
            # last_activity may be None with jupyterhub 0.9,
            # which introduces the 'created' field which is never None
            inactive = age

        user_is_admin = user["admin"]

        should_cull = (
            inactive is not None and inactive.total_seconds() >= inactive_limit
        ) and (cull_admin_users or not user_is_admin)

        if should_cull:
            logger.info(f"Culling user {user['name']} " f"(inactive for {inactive})")

        if max_age and not should_cull:
            # only check created if max_age is specified
            # so that we can still be compatible with jupyterhub 0.8
            # which doesn't define the 'started' field
            if age is not None and age.total_seconds() >= max_age:
                logger.info(
                    f"Culling user {user['name']} "
                    f"(age: {format_td(age)}, inactive for {format_td(inactive)})"
                )
                should_cull = True

        if not should_cull:
            logger.debug(
                f"Not culling user {user['name']} "
                f"(created: {format_td(age)}, last active: {format_td(inactive)})"
            )
            return False

        req = HTTPRequest(
            url=f"{url}/users/{user['name']}", method="DELETE", headers=auth_header
        )
        await fetch(req)
        return True

    futures = []

    params = {}
    if api_page_size:
        params["limit"] = str(api_page_size)

    # If we filter users by state=ready then we do not get back any which
    # are inactive, so if we're also culling users get the set of users which
    # are inactive and see if they should be culled as well.
    users_url = f"{url}/users"
    if state_filter and cull_users:
        inactive_params = {"state": "inactive"}
        inactive_params.update(params)
        req = HTTPRequest(url_concat(users_url, inactive_params), headers=auth_header)
        n_idle = 0
        async for user in fetch_paginated(req):
            n_idle += 1
            futures.append((user["name"], handle_user(user)))
        logger.debug(f"Got {n_idle} users with inactive servers")

    if state_filter:
        params["state"] = "ready"

    req = HTTPRequest(
        url=url_concat(users_url, params),
        headers=auth_header,
    )

    n_users = 0
    async for user in fetch_paginated(req):
        n_users += 1
        futures.append((user["name"], handle_user(user)))

    if state_filter:
        logger.debug(f"Got {n_users} users with ready servers")
    else:
        logger.debug(f"Got {n_users} users")

    for name, f in futures:
        try:
            result = await f
        except Exception:
            logger.exception(f"Error processing {name}")
        else:
            if result:
                logger.debug("Finished culling %s", name)


class IdleCuller(Application):

    api_page_size = Int(
        0,
        help=dedent(
            """
            Number of users to request per page,
            when using JupyterHub 2.0's paginated user list API.
            Default: user the server-side default configured page size.
            """
        ).strip(),
    ).tag(
        config=True,
    )

    concurrency = Int(
        10,
        help=dedent(
            """
            Limit the number of concurrent requests made to the Hub.

            Deleting a lot of users at the same time can slow down the Hub,
            so limit the number of API requests we have outstanding at any given time.
            """
        ).strip(),
    ).tag(
        config=True,
    )

    config_file = Unicode(
        "idle_culler_config.py",
        help=dedent(
            """
            Config file to load.
            """
        ).strip(),
    ).tag(
        config=True,
    )

    cull_admin_users = Bool(
        True,
        help=dedent(
            """
            Whether admin users should be culled (only if --cull-users=true).
            """
        ).strip(),
    ).tag(
        config=True,
    )

    cull_default_servers = Bool(
        True,
        help=dedent(
            """
            Whether default servers should be culled (only if --cull-default-servers=true).
            """
        ).strip(),
    ).tag(
        config=True,
    )

    cull_every = Int(
        0,
        help=dedent(
            """
            The interval (in seconds) for checking for idle servers to cull.
            """
        ).strip(),
    ).tag(
        config=True,
    )

    @default("cull_every")
    def _default_cull_every(self):
        return self.timeout // 2

    cull_named_servers = Bool(
        True,
        help=dedent(
            """
            Whether named servers should be culled (only if --cull-named-servers=true).
            """
        ).strip(),
    ).tag(
        config=True,
    )

    cull_users = Bool(
        False,
        help=dedent(
            """
            Cull users in addition to servers.

            This is for use in temporary-user cases such as tmpnb.
            """
        ).strip(),
    ).tag(
        config=True,
    )

    generate_config = Bool(
        False,
        help=dedent(
            """
            Generate default config file.
            """
        ).strip(),
    ).tag(
        config=True,
    )

    internal_certs_location = Unicode(
        "internal-ssl",
        help=dedent(
            """
            The location of generated internal-ssl certificates (only needed with --ssl-enabled=true).
            """
        ).strip(),
    ).tag(
        config=True,
    )

    _log_formatter_cls = LogFormatter

    @default("log_level")
    def _log_level_default(self):
        return logging.INFO

    @default("log_datefmt")
    def _log_datefmt_default(self):
        """Exclude date from default date format"""
        return "%Y-%m-%d %H:%M:%S"

    @default("log_format")
    def _log_format_default(self):
        """override default log format to include time"""
        return "%(color)s[%(levelname)1.1s %(asctime)s.%(msecs).03d %(name)s %(module)s:%(lineno)d]%(end_color)s %(message)s"

    max_age = Int(
        0,
        help=dedent(
            """
            The maximum age (in seconds) of servers that should be culled even if they are active.",
            """
        ).strip(),
    ).tag(
        config=True,
    )

    remove_named_servers = Bool(
        False,
        help=dedent(
            """
            Remove named servers in addition to stopping them.

            This is useful for a BinderHub that uses authentication and named servers.
            """
        ).strip(),
    ).tag(
        config=True,
    )

    ssl_enabled = Bool(
        False,
        help=dedent(
            """
            Whether the Jupyter API endpoint has TLS enabled.
            """
        ).strip(),
    ).tag(
        config=True,
    )

    timeout = Int(
        600,
        help=dedent(
            """
            The idle timeout (in seconds).
            """
        ).strip(),
    ).tag(
        config=True,
    )

    url = Unicode(
        os.environ.get("JUPYTERHUB_API_URL"),
        allow_none=True,
        help=dedent(
            """
            The JupyterHub API URL.
            """
        ).strip(),
    ).tag(
        config=True,
    )

    aliases = {
        "api-page-size": "IdleCuller.api_page_size",
        "concurrency": "IdleCuller.concurrency",
        "config": "IdleCuller.config_file",
        "cull-admin-users": "IdleCuller.cull_admin_users",
        "cull-default-servers": "IdleCuller.cull_default_servers",
        "cull-every": "IdleCuller.cull_every",
        "cull-named-servers": "IdleCuller.cull_named_servers",
        "cull-users": "IdleCuller.cull_users",
        "internal-certs-location": "IdleCuller.internal_certs_location",
        "max-age": "IdleCuller.max_age",
        "remove-named-servers": "IdleCuller.remove_named_servers",
        "ssl-enabled": "IdleCuller.ssl_enabled",
        "timeout": "IdleCuller.timeout",
        "url": "IdleCuller.url",
    }

    flags = {
        "generate-config": (
            {"IdleCuller": {"generate_config": True}},
            generate_config.help,
        )
    }

    def start(self):

        if self.generate_config:
            print(self.generate_config_file())
            sys.exit(0)

        if self.config_file:
            self.load_config_file(self.config_file)

        api_token = os.environ["JUPYTERHUB_API_TOKEN"]

        try:
            AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        except ImportError as e:
            self.log.warning(
                f"Could not load pycurl: {e}\n"
                "pycurl is recommended if you have a large number of users."
            )

        loop = IOLoop.current()
        cull = partial(
            cull_idle,
            url=self.url,
            api_token=api_token,
            inactive_limit=self.timeout,
            logger=self.log,
            cull_users=self.cull_users,
            remove_named_servers=self.remove_named_servers,
            max_age=self.max_age,
            concurrency=self.concurrency,
            ssl_enabled=self.ssl_enabled,
            internal_certs_location=self.internal_certs_location,
            cull_admin_users=self.cull_admin_users,
            api_page_size=self.api_page_size,
            cull_default_servers=self.cull_default_servers,
            cull_named_servers=self.cull_named_servers,
        )
        # schedule first cull immediately
        # because PeriodicCallback doesn't start until the end of the first interval
        loop.add_callback(cull)
        # schedule periodic cull
        pc = PeriodicCallback(cull, 1e3 * self.cull_every)
        pc.start()
        try:
            loop.start()
        except KeyboardInterrupt:
            pass


def main():
    IdleCuller.launch_instance()


if __name__ == "__main__":
    main()
