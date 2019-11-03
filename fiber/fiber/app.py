import asyncio
import os
from queue import Queue

from celery import Celery
from sanic import Sanic
import logging
import uvloop

from fiber.core import EventPump

from fiber.server import app


HOST = os.environ.get("WEBSOCKET_HOST", "0.0.0.0")
PORT = int(os.environ.get("WEBSOCKET_PORT", 8080))
DEBUG = os.environ.get("DEBUG", True)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def aenumerate(async_iterable, start=0):

    pos = start
    async for item in async_iterable:
        yield pos, item
        pos += 1


class EventFilter:

    def filter_one(self, event):
        raise NotImplementedError

    async def filter_async(self, event_pump: EventPump):
        log.debug("In filter_async")
        async for (i, event) in aenumerate(event_pump.iter_async()):
            log.debug("filter_async loop ", i + 1)
            if event and self.filter_one(event):
                log.debug("yielding")
                yield event
            else:
                log.debug("sleeping")
                await asyncio.sleep(0.20)


class MultiFilter(EventFilter):

    def __init__(self, filters):
        super().__init__()
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


async def runner(celery_app: Celery, event_filter: EventFilter = None):
    event_filter = event_filter or NoFilter()
    log.debug("entered runner")
    event_pump = EventPump(celery_app, queue=Queue())
    log.debug("created event pump")
    async for event in event_filter.filter_async(event_pump):
        log.debug("entered loop")
        await asyncio.sleep(0.26)


def main():
    log.debug("Starting up...")
    app.add_task(
        runner(
            Celery(
                "tasks",
                broker="amqp://rabbitmq",
                event_filter=NoHeartbeat()
            )
        )
    )
    log.debug("Added and running task: 'runner'.")
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
