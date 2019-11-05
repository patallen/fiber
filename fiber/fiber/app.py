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
            await sender.event(event)
        await standard_sleep()


def main():
    log.info("Fiber is starting up...")
    app.add_task(runner(celery.Celery(broker="amqp://rabbitmq")))
    log.info("Added and running task: 'runner'.")
    app.run(host=HOST, port=PORT, debug=DEBUG, auto_reload=True)


if __name__ == "__main__":
    main()
