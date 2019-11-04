import logging

from dataclasses import dataclass

from sanic import Blueprint
from sanic.response import html

from fiber.engine import Engine
from fiber.server import sio

engine = Engine(sio)
sender = engine.sender

log = logging.getLogger('fiber.api')

bp = Blueprint("api", url_prefix="api")


@dataclass
class Serializable:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def serialize(cls, data):
        return cls(**data)


class PreloadRequest(Serializable):
    user_sid: str
    section_id: str

    def to_json(self):
        return {
            'user_sid': self.user_sid,
            'section_id': self.section_id,
        }


@sio.on('disconnect')
async def on_disconnect(sid):
    sio.leave_room(sid, 'global')
    await sender.message(sid, f"Good bye!")
    log.debug('disconnected: %s', sid)


@sio.on('connect')
async def on_connect(sid, environ):
    sio.leave_room(sid, 'global')
    await sender.message(sid, "Welcome Home!")
    log.debug('connected: %s', sid)


@bp.route("/", methods=["GET", "OPTIONS"])
async def index(_request):
    with open("fiber/public/index.html") as f:
        return html(f.read())


def serialize(serializable_cls):
    def outer_wrapper(f):
        def inner_wrapper(self, sid, data):
            request_object = serializable_cls.serialize(data)
            return f(self, request_object)

        return inner_wrapper

    return outer_wrapper
