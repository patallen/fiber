import os
import threading
from queue import Queue
from signal import SIGINT, signal
from functools import partial

import socketio
from aiohttp import web
from celery import Celery
import asyncio
from celery.signals import task_failure, task_postrun, task_prerun, task_success
from sanic import Sanic
from sanic.response import html
from celery.events import EventReceiver

sio = socketio.AsyncServer(async_mode="sanic")
app = Sanic()
sio.attach(app)

HOST = os.environ["WEBSOCKET_HOST"]
PORT = int(os.environ["WEBSOCKET_PORT"])

# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def complete(task):
    return dict(event_type="complete", task=task)


class Monitor:
    def __init__(self, celery_app, loop=None):
        self.app = celery_app
        self.loop = loop or asyncio.get_event_loop()
        self.state = self.app.events.State()

    async def forward_failed_tasks(self, event):
        print("Failed tasks...")
        await sio.emit("event", dict(type=event["type"]), uuid=event["uuid"])

    async def forward_succeeded_tasks(self, event):
        self.state.event(event)
        print(f"Forwarding success for : {event['uuid']}")
        return sio.emit("event", dict(type=event["type"]), uuid=event["uuid"])

    def on_event(self, event):
        self.state.event(event)
        function = self.get_handler(event)
        return function(event)

    def noop(self, _event):
        print("noop")
        return

    def get_handler(self, event):
        handlers = {
            "task-failed": self.forward_failed_tasks,
            "task-succeeded": self.forward_succeeded_tasks,
        }
        try:
            return handlers[event["type"]]
        except KeyError:
            return self.noop

    async def run(self):
        print("Running thread.")
        with self.app.connection() as conn:
            while True:
                print("connection in thread: ", conn)


@app.route("")
async def index(_request):
    with open("fiber/public/index.html") as f:
        return html(f.read())


@sio.event
async def connect(sid, data):
    print(f"Client Connected: {sid}")
    sio.enter_room(sid, "home_page")
    await sio.send(f"Welcome, {sid}!")


@sio.event
async def disconnect(sid):
    print(f"Client Disconnected: {sid}")
    sio.leave_room(sid, "home_page")


@sio.event
async def message(sid, message):
    print(f"Socket ID: {sid} - {message}")
    await sio.emit("message", data="response!", room="home_page")


class EventHandler:
    def __init__(self, capp: Celery, q: Queue = None):
        self.capp: Celery = capp
        self.state = self.capp.events.State()
        self.queue = q or Queue()

    def callbacks(self):
        return {
            "worker-heartbeat": self.on_worker_heartbeat,
            "task-succeeded": self.on_task_succeeded,
            "task-failed": self.on_task_failed,
            "task-started": self.on_task_started,
            "task-received": self.on_task_received,
            "*": self.on_task_unmatched,
        }

    def on_task_succeeded(self, event):
        self.state.event(event)
        self.queue.put_nowait(event)
        print(f"task succeeded: {event['uuid']}")

    def on_task_failed(self, event):
        self.state.event(event)
        self.queue.put_nowait(event)
        print(f"task failed: {event['uuid']}")

    def on_task_started(self, event):
        self.state.event(event)
        self.queue.put_nowait(event)
        print(f"task started: {event['uuid']}")

    def on_task_received(self, event):
        self.state.event(event)
        self.queue.put_nowait(event)
        print(f"task received: {event['uuid']}")

    def on_task_unmatched(self, event):
        self.state.event(event)
        self.queue.put_nowait(event)
        print(f"unmatched task of type: {event['type']}")

    def on_worker_heartbeat(self, event):
        self.state.event(event)
        self.queue.put_nowait(event)
        print(f"heartbeat received")


async def watch_for_events(event_handlers, q):
    event_handlers.queue = q
    print("watching for events")
    with event_handlers.capp.connection() as conn:
        while True:
            receiver = EventReceiver(conn, handlers=event_handlers.to_dict())
            receiver.capture(limit=None, timeout=None, wakeup=True)
            await asyncio.sleep(0.5)


async def iter_queue(q: asyncio.Queue):
    while True:
        if q.empty():
            print("queue is empty... sleeping")
            yield await asyncio.sleep(0.1)
        else:
            print("queue has events... processing")
            yield await q.get()


async def process_events(q: Queue):
    async for item in iter_queue(q):
        print("FROM QUEUE: ", item)


if __name__ == "__main__":
    celery_app = Celery(broker="amqp://rabbitmq")
    events = EventHandler(celery_app)
    q = asyncio.Queue()
    app.add_task(process_events(q))
    app.add_task(watch_for_events(events, q))
    app.run(host=HOST, port=PORT, debug=True)

    # while running
    # loop loop through events
    # for each relevant event, push it into queue
    # on an interval handle all unprocessed events

# app >> queue (via amqp) >> worker
#               \
#                *--->> fiber
#                        / \
#                       /   \
#                      /     \
