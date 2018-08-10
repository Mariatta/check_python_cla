import enum
import json
import os

import aiohttp
import aiohttp_jinja2
import jinja2
from aiohttp import web

BPO_URL = "https://bugs.python.org/user?@template=clacheck&github_names="


class Status(enum.Enum):
    """The CLA status of the contribution."""

    signed = 1
    not_signed = 2
    username_not_found = 3


async def handle_get(request):
    response = aiohttp_jinja2.render_template("index.html", request, context={})
    return response


async def handle_post(request):
    data = await request.post()
    gh_username = data.get("gh_username", "")
    context = {}
    if len(gh_username) > 0:
        cla_result = await check_cla(gh_username)
        context = {"gh_username": gh_username, "cla_result": cla_result}
    response = aiohttp_jinja2.render_template("index.html", request, context=context)
    return response


async def check_cla(gh_username):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BPO_URL}{gh_username}") as response:
            if response.status >= 300:
                msg = f"unexpected response for {response.url!r}: {response.status}"
                raise aiohttp.web.HTTPInternalServerError(text=msg)
                # Explicitly decode JSON as b.p.o doesn't set the content-type as
                # `application/json`.
            results = json.loads(await response.text())
            if results[gh_username] == True:
                return Status.signed.value
            elif results[gh_username] == False:
                return Status.not_signed.value
            else:
                return Status.username_not_found.value

if __name__ == "__main__":  # pragma: no cover
    app = web.Application()
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(os.path.join(os.getcwd(), "templates"))
    )
    app["static_root_url"] = os.path.join(os.getcwd(), "static")
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)
    app.add_routes(
        [
            web.get("/", handle_get),
            web.post("/", handle_post),
            web.static("/static", os.path.join(os.getcwd(), "static")),
        ]
    )
    web.run_app(app, port=port)
