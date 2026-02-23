from collections.abc import Generator

import pytest
{% if cookiecutter.use_channels %}
import pytest_asyncio
from channels.testing import WebsocketCommunicator

from ...asgi import application
{% endif %}


@pytest.fixture
def some() -> Generator[int]:
    # setup code
    yield 1
    # teardown code
{% if cookiecutter.use_channels %}


@pytest_asyncio.fixture
async def communicator():
    communicator = WebsocketCommunicator(application, "/ws/v0/")
    connected, _ = await communicator.connect()
    assert connected
    yield communicator
    await communicator.disconnect(200)
{% endif %}