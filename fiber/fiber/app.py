from typing import Optional
import asyncio
import os
from queue import Queue
import datetime

from celery import Celery
import logging
import uvloop
import uuid

from fiber.core import EventPump

from fiber.server import app
from fiber.api import sender

HOST = os.environ.get("WEBSOCKET_HOST", "0.0.0.0")
PORT = int(os.environ.get("WEBSOCKET_PORT", 8080))
DEBUG = False

logging.getLogger('sanic').setLevel(logging.CRITICAL)
logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
log = logging.getLogger('fiber')

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
        log.info("In filter_async")
        i = 0
        async for event in event_pump.iter_async():
            i += 1
            if event and self.filter_one(event):
                yield event
            else:
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

from dataclasses import dataclass
import enum

class WorkerEventType(enum.Enum):
    ONLINE = "worker-online"
    OFFLINE = "worker-offline"
    HEARTBEAT = "worker-heartbeat"


class TaskState(enum.Enum):
    FAILURE = "FAILURE"
    PENDING = "PENDING"
    REVOKED = "REVOKED"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    RETRY   = "RETRY"


@dataclass
class TaskEvent:
    class Type(enum.Enum):
        SUCCEEDED = "task-succeeded"
        RECEIVED = "task-received"
        REJECTED = "task-rejected"
        RETRIED = "task-retried"
        REVOKED = "task-revoked"
        STARTED = "task-started"
        FAILED = "task-failed"
        SENT = "task-sent"

    type: Type
    args: Optional[str]
    clock: int
    eta: datetime.datetime
    expires: Optional[datetime.datetime]
    hostname: str
    kwargs: dict
    local_received: datetime.datetime
    name: str
    parent_id: uuid.UUID
    pid: int
    retries: int
    root_id: uuid.UUID
    state: TaskState
    timestamp: datetime.datetime
    utcoffset: int
    uuid: uuid.UUID


@dataclass
class Worker:
    hostname: str


@dataclass
class Task:
    received_at: datetime.datetime
    parent_id: Optional[uuid.UUID]
    expires: datetime.datetime
    root_id: uuid.UUID
    state: TaskState
    uuid: uuid.UUID
    runtime: float
    retries: int
    kwargs: dict
    args: tuple
    name: str

    @classmethod
    def from_event(cls, event):
        parent_id = None
        if event.get('parent_id'):
            parent_id = uuid.UUID(event['parent_id'])

        root_id = None
        if event.get('root_id'):
            root_id = uuid.UUID(event['root_id'])

        expires = None
        if event.get('expires'):
            expires = datetime.datetime.fromordinal(event['expires'])


        return cls(
            received_at=datetime.datetime.fromordinal(event['timestamp']),
            state=TaskState.from_text(event['state']),
            runtime=int(event.get('runtime', 0)),
            uuid=uuid.UUID(event['uuid']),
            retries=event['retries'],
            kwargs=event['kwargs'],
            name=event.get('name'),
            parent_id=parent_id,
            args=event['args'],
            root_id=root_id,
            expires=expires,
        )

class Store:
    def __init__(self):
        self.tasks = {}
        self.workers = {}


class EventHandler:
    def __init__(self, store, sio):
        self.store = store
        self.sio = sio

    def handle(self, event):
        self.store.events.append(event)
        if event['type'].startswith('worker-'):
            self.handle_worker_event(event)
        elif event['type'].startswith('task-'):
            self.handle_task_event(event)
        else:
            raise ValueError("%s is not a known event type", event['type'])

    def handle_task_event(self, event):
        if event['type'] == 'task-received':
            self.store.tasks.receive(event)
        elif event['type'] == 'task-started':
            task = Task.from_event(event)
            task = self.store.tasks.add(task)
        elif event['type'] == 'task-succeeded':
            self.store.tasks[event['uuid']].handle_success(event)

    def handle_worker_event(self, event):
        hostname = event['hostname']
        event_type = event['type']

        if event['type'] == 'worker-heartbeat':
            self.store.workers[hostname].record_heartbeat(event)
        elif event['type'] in {'worker-online', 'worker-offline'}:
            self.store.workers[hostname].update_status(event)
        else:
            raise RuntimeError("%s is not a valid worker event type.", event_type)


async def runner(celery_app: Celery, event_filter: EventFilter = None):
    event_filter = event_filter or NoFilter()
    event_pump = EventPump(celery_app, queue=Queue())

    async for event in event_filter.filter_async(event_pump):
        if event:
            await sender.event(event)
        await asyncio.sleep(0.26)


def main():
    log.info("Starting up...")
    app.add_task(runner(Celery("tasks", broker="amqp://rabbitmq")))
    log.info("Added and running task: 'runner'.")
    app.run(host=HOST, port=PORT, debug=DEBUG, auto_reload=True)


if __name__ == "__main__":
    main()
