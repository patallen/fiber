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

HOST = os.environ.get("WEBSOCKET_HOST", "0.0.0.0")
PORT = int(os.environ.get("WEBSOCKET_PORT", 8080))
DEBUG = False

logging.getLogger("sanic").setLevel(logging.CRITICAL)
logging.basicConfig(
    level=logging.WARN, format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
)
log = logging.getLogger("fiber")

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def runner(celery_app: celery.Celery, event_filter: EventFilter = None):
    event_filter = event_filter or NoFilter()
    event_pump = EventPump(celery_app, queue=queue.Queue())

    async for event in event_filter.filter_async(event_pump):
        if event:
            await sender.event(translate_event(event))
        await standard_sleep()


def create_task(event):
    import pprint
    pprint.pprint(event)
    return dict(
        action="LOAD_TASK",
        payload=dict(
            args=event["args"],
            kwargs=event["kwargs"],
            eta=event["eta"],
            name=event["name"],
            state=event["state"],
            uuid=event["uuid"],
            parent_id=event["parent_id"],
            expires=event["expires"],
            created_at=event['timestamp']
        ),
        worker=dict(id=make_worker_id(event), hostname=event["hostname"], pid=event["pid"]),
        timestamp=event["timestamp"],
        clock=event["clock"],
    )


def update_task(event):
    print(event)
    return dict(
        action="UPDATE_TASK",
        type=event['type'],
        payload=dict(
            uuid=event["uuid"],
            state=event["state"],
            result=event.get('result'),
            runtime=event.get('runtime'),
        ),
        worker=dict(id=make_worker_id(event), hostname=event["hostname"], pid=event["pid"]),
        timetamp=event["timestamp"],
        clock=event["clock"],
    )


def make_worker_id(event):
    return f"{event['hostname']}.{event['pid']}"


def create_worker(event):
    return dict(
        action="LOAD_WORKER",
        type=event['type'],
        payload=dict(
            id=make_worker_id(event),
            hostname=event['hostname'],
            pid=event['pid'],
            active=event.get('active'),
            processed=event.get('processed'),
            loadavg=event.get('loadavg'),
            clock=event.get('clock'),
            state=event.get('state'),
        ),
        timestamp=event['timestamp']
    )


def update_worker(event):
    return dict(
        action="UPDATE_WORKER",
        type=event['type'],
        payload=dict(
            id=make_worker_id(event),
            hostname=event["hostname"],
            pid=event["pid"],
            active=event.get("active", 0),
            processed=event.get("processed", 0),
            loadavg=event.get("loadavg"),
            clock=event['clock'],
            state=event.get('state')
        ),
        timestamp=event["timestamp"],
    )


def translate_event(event):
    domain, event_type = event["type"].split("-")
    if domain == "task":
        if event_type == "received":
            return create_task(event)
        if event_type in ("started", "succeeded", "failed"):
            return update_task(event)
    elif domain == "worker":
        if event_type == "online":
            return create_worker(event)
        if event_type in ("online", "heartbeat"):
            return update_worker(event)
    raise RuntimeError


def main():
    log.info("Fiber is starting up...")
    app.add_task(runner(celery.Celery(broker="amqp://rabbitmq")))
    log.info("Added and running task: 'runner'.")
    app.run(host=HOST, port=PORT, debug=DEBUG, auto_reload=True)


if __name__ == "__main__":
    main()
