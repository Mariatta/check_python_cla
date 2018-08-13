import os

import aiohttp
import aiohttp_jinja2
import jinja2
from aiohttp import web
from gidgethub.aiohttp import GitHubAPI

from check_python_cla.bpo import Status, check_cla
from check_python_cla.exceptions import CheckCLAException
from check_python_cla.github import get_and_update_pending_prs


@web.middleware
async def error_middleware(request, handler):
    """Middlware to render error message using the template renderer."""
    try:
        response = await handler(request)
    except web.HTTPException as ex:
        if ex.text:
            message = ex.text
        else:
            message = ex.reason
        context = {"error_message": message, "status": ex.status}
        response = aiohttp_jinja2.render_template(
            "error.html", request, context=context
        )
    return response


async def handle_get(request):
    """Render a page with a textbox and submit button."""
    response = aiohttp_jinja2.render_template("index.html", request, context={})
    return response


async def handle_post(request):
    """Check if the user has signed the CLA.

    If the user has signed the CLA, and there are still open PRs with `CLA not signed` label,
    remove the `CLA not signed` label.
    Otherwise, just display a page saying whether user has signed the CLA or not.
    """
    data = await request.post()
    gh_username = data.get("gh_username", "")
    context = {}
    template = "index.html"
    if len(gh_username) > 0:
        async with aiohttp.ClientSession() as session:
            try:
                cla_result = await check_cla(session, gh_username)
            except CheckCLAException as e:
                context = {"error_message": e}
            else:
                context = {"gh_username": gh_username, "cla_result": cla_result}
                if cla_result == Status.signed.value:
                    gh = GitHubAPI(
                        session, "python/cpython", oauth_token=os.environ.get("GH_AUTH")
                    )
                    pending_prs = await get_and_update_pending_prs(gh, gh_username)
                    if len(pending_prs) > 0:
                        template = "pull_requests.html"
                        context["pull_requests"] = pending_prs

    response = aiohttp_jinja2.render_template(template, request, context=context)
    return response


if __name__ == "__main__":  # pragma: no cover
    app = web.Application(middlewares=[error_middleware])
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
