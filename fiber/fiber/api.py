import logging
from dataclasses import dataclass

from sanic import Blueprint
from sanic.response import html

from fiber.events import Sender
from fiber.server import sio

log = logging.getLogger("fiber.api")

sender = Sender(sio)


@sio.on("disconnect")
async def on_disconnect(sid):
    sio.leave_room(sid, "global")
    await sender.message(sid, f"Good bye!")
    log.debug("disconnected: %s", sid)


@sio.on("connect")
async def on_connect(sid, environ):
    sio.leave_room(sid, "global")
    await sender.message(sid, "Welcome Home!")
    log.debug("connected: %s", sid)


def serialize(serializable_cls):
    def outer_wrapper(f):
        def inner_wrapper(self, sid, data):
            request_object = serializable_cls.serialize(data)
            return f(self, request_object)

        return inner_wrapper

    return outer_wrapper
