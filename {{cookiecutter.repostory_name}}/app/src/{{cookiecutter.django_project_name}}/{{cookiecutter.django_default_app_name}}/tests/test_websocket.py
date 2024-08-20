{%- if cookiecutter.use_channels == "y" -%}
import pytest

from ..schemas import Heartbeat


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test__websocket__heartbeat(communicator) -> None:
    """Check websocket consumer receiving message"""
    await communicator.send_json_to(Heartbeat().dict())
    response = await communicator.receive_json_from()
    assert response == Heartbeat().dict()
{% endif %}