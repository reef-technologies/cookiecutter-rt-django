from collections.abc import Generator

import pytest
{%- if cookiecutter.use_channels == "y" %}
import pytest_asyncio
from channels.testing import WebsocketCommunicator
{%- endif %}
from pytest_postgresql import factories
{%- if cookiecutter.use_channels == "y" %}

from ...asgi import application
{%- endif %}

postgresql_in_docker = factories.postgresql_noproc()
postgresql = factories.postgresql("postgresql_in_docker", dbname="test")


@pytest.fixture
def some() -> Generator[int, None, None]:
    # setup code
    yield 1
    # teardown code
{% if cookiecutter.use_channels == "y" %}

@pytest_asyncio.fixture
async def communicator():
    communicator = WebsocketCommunicator(application, "/ws/v0/")
    connected, _ = await communicator.connect()
    assert connected
    yield communicator
    await communicator.disconnect(200)
{% endif %}