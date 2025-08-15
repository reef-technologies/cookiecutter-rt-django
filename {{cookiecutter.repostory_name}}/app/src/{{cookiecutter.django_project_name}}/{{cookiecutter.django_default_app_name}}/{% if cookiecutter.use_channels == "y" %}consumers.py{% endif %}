from collections.abc import Callable
from typing import Annotated, ClassVar, Union

import structlog
from channels.generic.websocket import AsyncWebsocketConsumer
from pydantic import BaseModel, Field, TypeAdapter, ValidationError
from structlog.contextvars import bound_contextvars

from .schemas import Heartbeat

log = structlog.get_logger(__name__)


class DefaultConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        await super().connect()
        log.info("connected", scope=self.scope)

    async def disconnect(self, code: int | str) -> None:
        log.info("disconnected", scope=self.scope, code=code)

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        with bound_contextvars(text_data=text_data, bytes_data=bytes_data):
            log.debug("message received")
            try:
                message: BaseModel = self.MESSAGE_MODEL.validate_json(text_data)
            except ValidationError as exc:
                errors = exc.errors()
                log.debug("message parsing failed", errors=errors)
                return

            handler = self.MESSAGE_HANDLERS[type(message)]
            log.debug("selected message handler", handler=handler)
            await handler(self, message)

    async def handle_heartbeat(self, message: Heartbeat) -> None:
        await self.send(text_data=message.json())

    MESSAGE_HANDLERS: ClassVar[dict[BaseModel, Callable]] = {
        Heartbeat: handle_heartbeat,
    }
    MESSAGE_MODEL = TypeAdapter(Annotated[Union[*MESSAGE_HANDLERS.keys()], Field(discriminator="type")])
