import os
from unittest import mock

import aiohttp_jinja2
import jinja2
import pytest
from aiohttp import web

from check_python_cla import __main__ as main
from check_python_cla.__main__ import error_middleware
from check_python_cla.bpo import Status


@pytest.fixture
def cli(loop, aiohttp_client):
    app = web.Application(middlewares=[error_middleware])
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(os.path.join(os.getcwd(), "templates"))
    )
    app.router.add_get("/", main.handle_get)
    app.router.add_post("/", main.handle_post)
    return loop.run_until_complete(aiohttp_client(app))


async def test_get(cli):
    response = await cli.get("/")
    assert response.status == 200
    text = await response.text()
    assert "Check if you have signed Python's" in text


async def test_post_no_postdata(cli):
    response = await cli.post("/")
    assert response.status == 200
    text = await response.text()
    assert "Check if you have signed Python's" in text


async def test_post_no_username(cli):
    response = await cli.post("/", data={"gh_username": ""})
    assert response.status == 200
    text = await response.text()
    assert "Check if you have signed Python's" in text


async def test_post_with_username_has_signed(cli):
    response = await cli.post("/", data={"gh_username": "mariatta"})
    assert response.status == 200
    text = await response.text()
    assert "mariatta" in text
    assert "has signed the CLA" in text
    assert "Check another?" in text


async def test_post_with_username_has_not_signed(cli):
    response = await cli.post("/", data={"gh_username": "miss-islington"})

    assert response.status == 200
    text = await response.text()
    assert "miss-islington" in text
    assert "has not signed CLA" in text
