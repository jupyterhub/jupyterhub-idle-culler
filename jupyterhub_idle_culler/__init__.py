#!/usr/bin/env python3
"""
Monitor & Cull idle single-user servers and users
"""

import asyncio
import ssl
import json
import os
from datetime import datetime
from datetime import timezone
from distutils.version import LooseVersion as V
from functools import partial
from textwrap import dedent

from urllib.parse import quote

import dateutil.parser

from tornado.log import app_log
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.httputil import url_concat
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.options import define, options, parse_command_line

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
    return "{h:02}:{m:02}:{seconds:02}".format(h=h, m=m, seconds=seconds)


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


async def cull_idle(
    url,
    api_token,
    inactive_limit,
    cull_users=False,
    remove_named_servers=False,
    max_age=0,
    concurrency=10,
    ssl_enabled=False,
    internal_certs_location="",
    cull_admin_users=True,
    api_page_size=0,
):
    """Shutdown idle single-user servers

    If cull_users, inactive *users* will be deleted as well.
    """
    defaults = {
        # GET /users may be slow if there are thousands of users and we
        # don't do any server side filtering so default request timeouts
        # to 60 seconds rather than tornado's 20 second default.
        "request_timeout": os.environ.get("JUPYTERHUB_REQUEST_TIMEOUT", 60)
    }
    if ssl_enabled:
        ssl_context = make_ssl_context(
            f"{internal_certs_location}/hub-internal/hub-internal.key",
            f"{internal_certs_location}/hub-internal/hub-internal.crt",
            f"{internal_certs_location}/hub-ca/hub-ca.crt",
        )

        app_log.debug("ssl_enabled is Enabled: %s", ssl_enabled)
        app_log.debug("internal_certs_location is %s", internal_certs_location)
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
                    app_log.info(f"Fetching page {page_no} {next_info['url']}")
                    # submit next request
                    req.url = next_info["url"]
                    resp_future = asyncio.ensure_future(fetch(req))

            for item in items:
                item_count += 1
                yield item

        app_log.debug(f"Fetched {item_count} items from {url} in {page_no} pages")

    # Starting with jupyterhub 1.3.0 the users can be filtered in the server
    # using the `state` filter parameter. "ready" means all users who have any
    # ready servers (running, not pending).
    auth_header = {"Authorization": "token %s" % api_token}
    resp = await fetch(HTTPRequest(url=url + "/", headers=auth_header))

    resp_model = json.loads(resp.body.decode("utf8", "replace"))
    state_filter = V(resp_model["version"]) >= STATE_FILTER_MIN_VERSION

    now = datetime.now(timezone.utc)

    async def handle_server(user, server_name, server, max_age, inactive_limit):
        """Handle (maybe) culling a single server

        "server" is the entire server model from the API.

        Returns True if server is now stopped (user removable),
        False otherwise.
        """
        log_name = user["name"]
        if server_name:
            log_name = "%s/%s" % (user["name"], server_name)
        if server.get("pending"):
            app_log.warning(
                "Not culling server %s with pending %s", log_name, server["pending"]
            )
            return False

        # jupyterhub < 0.9 defined 'server.url' once the server was ready
        # as an *implicit* signal that the server was ready.
        # 0.9 adds a dedicated, explicit 'ready' field.
        # By current (0.9) definitions, servers that have no pending
        # events and are not ready shouldn't be in the model,
        # but let's check just to be safe.

        if not server.get("ready", bool(server["url"])):
            app_log.warning(
                "Not culling not-ready not-pending server %s: %s", log_name, server
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

        should_cull = (
            inactive is not None and inactive.total_seconds() >= inactive_limit
        )
        if should_cull:
            app_log.info(
                "Culling server %s (inactive for %s)", log_name, format_td(inactive)
            )

        if max_age and not should_cull:
            # only check started if max_age is specified
            # so that we can still be compatible with jupyterhub 0.8
            # which doesn't define the 'started' field
            if age is not None and age.total_seconds() >= max_age:
                app_log.info(
                    "Culling server %s (age: %s, inactive for %s)",
                    log_name,
                    format_td(age),
                    format_td(inactive),
                )
                should_cull = True

        if not should_cull:
            app_log.debug(
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
            delete_url = url + "/users/%s/servers/%s" % (
                quote(user["name"]),
                quote(server["name"]),
            )
            if remove_named_servers:
                body = json.dumps({"remove": True})
        else:
            delete_url = url + "/users/%s/server" % quote(user["name"])

        req = HTTPRequest(
            url=delete_url,
            method="DELETE",
            headers=auth_header,
            body=body,
            allow_nonstandard_methods=True,
        )
        resp = await fetch(req)
        if resp.code == 202:
            app_log.warning("Server %s is slow to stop", log_name)
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
            app_log.debug(
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
            app_log.info("Culling user %s (inactive for %s)", user["name"], inactive)

        if max_age and not should_cull:
            # only check created if max_age is specified
            # so that we can still be compatible with jupyterhub 0.8
            # which doesn't define the 'started' field
            if age is not None and age.total_seconds() >= max_age:
                app_log.info(
                    "Culling user %s (age: %s, inactive for %s)",
                    user["name"],
                    format_td(age),
                    format_td(inactive),
                )
                should_cull = True

        if not should_cull:
            app_log.debug(
                "Not culling user %s (created: %s, last active: %s)",
                user["name"],
                format_td(age),
                format_td(inactive),
            )
            return False

        req = HTTPRequest(
            url=url + "/users/%s" % user["name"], method="DELETE", headers=auth_header
        )
        await fetch(req)
        return True

    futures = []

    params = {}
    if api_page_size:
        params["limit"] = str(api_page_size)

    users_url = url + "/users"

    # If we filter users by state=ready then we do not get back any which
    # are inactive, so if we're also culling users get the set of users which
    # are inactive and see if they should be culled as well.
    if state_filter and cull_users:
        inactive_params = {"state": "inactive"}
        inactive_params.update(params)
        req = HTTPRequest(url_concat(users_url, inactive_params), headers=auth_header)
        n_idle = 0
        async for user in fetch_paginated(req):
            n_idle += 1
            futures.append((user["name"], handle_user(user)))
        app_log.debug(f"Got {n_idle} users with inactive servers")

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

    app_log.debug(
        "Got %d users%s", n_users, (" with ready servers" if state_filter else "")
    )

    for (name, f) in futures:
        try:
            result = await f
        except Exception:
            app_log.exception("Error processing %s", name)
        else:
            if result:
                app_log.debug("Finished culling %s", name)


def main():
    define(
        "url",
        default=os.environ.get("JUPYTERHUB_API_URL"),
        help=dedent(
            """
            The JupyterHub API URL.
            """
        ).strip(),
    )
    define(
        "timeout",
        type=int,
        default=600,
        help=dedent(
            """
            The idle timeout (in seconds).
            """
        ).strip(),
    )
    define(
        "cull_every",
        type=int,
        default=0,
        help=dedent(
            """
            The interval (in seconds) for checking for idle servers to cull.
            """
        ).strip(),
    )
    define(
        "max_age",
        type=int,
        default=0,
        help=dedent(
            """
            The maximum age (in seconds) of servers that should be culled even if they are active.
            """
        ).strip(),
    )
    define(
        "cull_users",
        type=bool,
        default=False,
        help=dedent(
            """
            Cull users in addition to servers.

            This is for use in temporary-user cases such as tmpnb.
            """
        ).strip(),
    )
    define(
        "remove_named_servers",
        default=False,
        type=bool,
        help=dedent(
            """
            Remove named servers in addition to stopping them.

            This is useful for a BinderHub that uses authentication and named servers.
            """
        ).strip(),
    )
    define(
        "concurrency",
        type=int,
        default=10,
        help=dedent(
            """
            Limit the number of concurrent requests made to the Hub.

            Deleting a lot of users at the same time can slow down the Hub,
            so limit the number of API requests we have outstanding at any given time.
            """
        ).strip(),
    )
    define(
        "ssl_enabled",
        type=bool,
        default=False,
        help=dedent(
            """
            Whether the Jupyter API endpoint has TLS enabled.
            """
        ).strip(),
    )
    define(
        "internal_certs_location",
        type=str,
        default="internal-ssl",
        help=dedent(
            """
            The location of generated internal-ssl certificates (only needed with --ssl-enabled=true).
            """
        ).strip(),
    )
    define(
        "cull_admin_users",
        type=bool,
        default=True,
        help=dedent(
            """
            Whether admin users should be culled (only if --cull-users=true).
            """
        ).strip(),
    )
    define(
        "api_page_size",
        type=int,
        default=0,
        help=dedent(
            """
            Number of users to request per page,
            when using JupyterHub 2.0's paginated user list API.
            Default: user the server-side default configured page size.
            """
        ).strip(),
    )

    parse_command_line()
    if not options.cull_every:
        options.cull_every = options.timeout // 2
    api_token = os.environ["JUPYTERHUB_API_TOKEN"]

    try:
        AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    except ImportError as e:
        app_log.warning(
            "Could not load pycurl: %s\n"
            "pycurl is recommended if you have a large number of users.",
            e,
        )

    loop = IOLoop.current()
    cull = partial(
        cull_idle,
        url=options.url,
        api_token=api_token,
        inactive_limit=options.timeout,
        cull_users=options.cull_users,
        remove_named_servers=options.remove_named_servers,
        max_age=options.max_age,
        concurrency=options.concurrency,
        ssl_enabled=options.ssl_enabled,
        internal_certs_location=options.internal_certs_location,
        cull_admin_users=options.cull_admin_users,
        api_page_size=options.api_page_size,
    )
    # schedule first cull immediately
    # because PeriodicCallback doesn't start until the end of the first interval
    loop.add_callback(cull)
    # schedule periodic cull
    pc = PeriodicCallback(cull, 1e3 * options.cull_every)
    pc.start()
    try:
        loop.start()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
