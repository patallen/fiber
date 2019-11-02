import os
from queue import Queue

import socketio
from celery import Celery
import asyncio
from sanic import Sanic
from sanic.response import html, text
from events import EventPump

sio = socketio.AsyncServer(async_mode="sanic")
app = Sanic()
sio.attach(app)

HOST = os.environ["WEBSOCKET_HOST"]
PORT = int(os.environ["WEBSOCKET_PORT"])

# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def complete(task):
    return dict(event_type="complete", task=task)


@app.route("/favicon.ico")
async def favicon(_request):
    return text("")


@app.route("")
async def index(_request):
    with open("fiber/public/index.html") as f:
        return html(f.read())


@app.route("static/js/<filename>")
async def js(_request, filename):
    with open(f"fiber/public/js/{filename}") as f:
        return text(f.read())


@sio.event
async def connect(sid, data):
    print(f"Client Connected: {sid}")
    sio.enter_room(sid, "home_page")
    await sio.send(f"Welcome, {sid}!")


@sio.event
async def disconnect(sid):
    print(f"Client Disconnected: {sid}")
    sio.leave_room(sid, "home_page")
    await sio.send(f"Cya, fucker.")


class EventFilter:
    def filter_one(self, event):
        raise NotImplementedError

    async def filter_async(self, event_pump: EventPump):
        async for event in event_pump.iter_async():
            if event and self.filter_one(event):
                yield event
            else:
                await asyncio.sleep(0.05)


class MultiFilter(EventFilter):
    def __init__(self, filters):
        self.filters = filters or []

    def filter_one(self, event):
        return all(f.filter_one(event) for f in self.filters) and event


class NoHeartbeat(EventFilter):
    def filter_one(self, event):
        if event["type"] == "worker-heartbeat":
            return None
        return event


class NoFilter(EventFilter):
    def filter_one(self, event):
        return event


async def runner(capp: Celery, event_filter: EventFilter = None):
    event_pump = EventPump(capp, queue=Queue())
    async for event in event_filter.filter_async(event_pump):
        await sio.emit("event", event)
        await asyncio.sleep(0.05)


if __name__ == "__main__":
    # while running
    # loop loop through events
    # for each relevant event, push it into queue
    # on an interval handle all unprocessed events

    app.add_task(runner(Celery(broker="amqp://rabbitmq"), event_filter=NoHeartbeat()))
    app.run(host=HOST, port=PORT)
