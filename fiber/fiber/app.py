import asyncio
import logging
import os
import queue

import celery
import uvloop

from fiber.api import sender
from fiber.events import EventFilter, EventPump, NoFilter
from fiber.server import app
from fiber.utils import standard_sleep
from fiber.store import EventStore


HOST = os.environ.get("WEBSOCKET_HOST", "0.0.0.0")
PORT = int(os.environ.get("WEBSOCKET_PORT", 8080))
DEBUG = False

logging.getLogger("sanic").setLevel(logging.CRITICAL)
logging.basicConfig(
    level=logging.WARN, format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
)
log = logging.getLogger("fiber")

store = EventStore()

# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def save_event(event: dict):
    store.add_event(event)


async def runner(celery_app: celery.Celery, event_filter: EventFilter = None):
    event_filter = event_filter or NoFilter()
    event_pump = EventPump(celery_app, queue=queue.Queue())

    async for event in event_filter.filter_async(event_pump):
        if event:
            event = translate_event(event)
            await save_event(event)
            await sender.event(event)
        await standard_sleep()


def create_task(event):
    return dict(
        action="LOAD_TASK",
        timestamp=event["timestamp"],
        payload=dict(
            args=event["args"],
            kwargs=event["kwargs"],
            eta=event["eta"],
            name=event["name"],
            state=event["state"],
            uuid=event["uuid"],
            parent_id=event["parent_id"],
            expires=event["expires"],
            created_at=event["timestamp"],
            worker_id=make_worker_id(event),
        ),
    )


def update_task(event):
    return dict(
        action="UPDATE_TASK",
        type=event["type"],
        timetamp=event["timestamp"],
        payload=dict(
            uuid=event["uuid"],
            state=event["state"],
            result=event.get("result"),
            runtime=event.get("runtime"),
        ),
    )


def complete_task(event):
    return dict(
        action="COMPLETE_TASK",
        type=event["type"],
        timetamp=event["timestamp"],
        payload=dict(
            uuid=event["uuid"],
            state=event["state"],
            runtime=event["runtime"],
            result=event["result"],
        ),
    )


def make_worker_id(event):
    return f"{event['hostname']}.{event['pid']}"


def bring_worker_online(event):
    return dict(
        action="BRING_WORKER_ONLINE",
        type=event["type"],
        timestamp=event["timestamp"],
        payload=dict(
            id=make_worker_id(event),
            hostname=event["hostname"],
            pid=event["pid"],
            active=event.get("active"),
            processed=event.get("processed"),
            loadavg=event.get("loadavg"),
            clock=event.get("clock"),
            state=event.get("state"),
            online_at=event["timestamp"],
            status="ONLINE",
        ),
    )


def update_worker(event):
    return dict(
        action="UPDATE_WORKER",
        type=event["type"],
        payload=dict(
            id=make_worker_id(event),
            hostname=event["hostname"],
            pid=event["pid"],
            active=event.get("active", 0),
            processed=event.get("processed", 0),
            loadavg=event.get("loadavg"),
            clock=event["clock"],
            status="ONLINE",
        ),
        timestamp=event["timestamp"],
    )


def take_worker_offline(event):
    return dict(
        action="TAKE_WORKER_OFFLINE",
        type=event["type"],
        payload=dict(
            id=make_worker_id(event),
            active=False,
            offline_at=event["timestamp"],
            status="OFFLINE",
        ),
        timestamp=event["timestamp"],
    )


def translate_event(event):
    domain, event_type = event["type"].split("-")
    if domain == "task":
        if event_type == "received":
            return create_task(event)
        if event_type == "started":
            return update_task(event)
        if event_type in ("succeeded", "failed"):
            return complete_task(event)
    elif domain == "worker":
        if event_type == "online":
            return bring_worker_online(event)
        if event_type == "heartbeat":
            return update_worker(event)
        if event_type == "offline":
            return take_worker_offline(event)
    raise RuntimeError


def main():
    store = EventStore()
    event_queue = asyncio.Queue()
    log.info("Fiber is starting up...")
    runner_task = runner(celery.Celery(broker="amqp://rabbitmq"))
    app.add_task(runner_task)
    log.info("Added and running task: 'runner'.")
    app.run(host=HOST, port=PORT, debug=DEBUG, auto_reload=True)


if __name__ == "__main__":
    main()
