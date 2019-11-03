from dataclasses import dataclass
from sanic import Blueprint
from sanic.request import Request
from sanic.response import text, html
from fiber.server import sio


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
    await sio.send(f"Welcome, {sid}!")
    sio.logger.debug('disconnected: %s', sid)


@sio.on('connect')
async def on_connect(sid, environ):
    sio.leave_room(sid, 'global')
    await sio.send(f"Good bye!")
    sio.logger.debug('connected: %s', sid)
    sio.logger.debug('environ: %s', environ)


@bp.route("/favicon.ico")
async def favicon(_request: Request):
    return text("")


@bp.route("/", methods=["GET", "OPTIONS"])
async def index(_request):
    with open("fiber/public/index.html") as f:
        return html(f.read())


@bp.route("static/js/<filename>")
async def js(_request, filename):
    with open(f"fiber/public/js/{filename}") as f:
        return text(f.read())


@sio.on('request_preload')
async def on_request_preload(sid, request):
    sio.logger.debug('preload requested by "%s"', sid)
    await sio.emit("preload", request.to_dict())


def serialize(serializable_cls):
    def outer_wrapper(f):
        def inner_wrapper(self, sid, data):
            print("SELF: ", self)
            print("DATA: ", data)
            request_object = serializable_cls.serialize(data)
            return f(self, request_object)
        return inner_wrapper
    return outer_wrapper


