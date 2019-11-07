import datetime
import enum
import logging
import queue
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from celery import Celery

from fiber.utils import standard_sleep

log = logging.getLogger("fabric.events")


class Domain(enum.Enum):
    WORKERS = "WORKERS"
    TASKS = "TASKS"


class EventId(int):
    pass


class WorkerAction(enum.Enum):
    HEARTBEAT = "HEARTBEAT"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class Action(enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"


class Serializer:
    @staticmethod
    def to_dict(event: "Event") -> dict:
        raise NotImplementedError

    @staticmethod
    def from_dict(adict: dict) -> "Event":
        raise NotImplementedError


class Event:
    serializer: Serializer = None

    def encode(self, adict: dict) -> "Event":
        return self.serializer.from_dict(adict)

    def decode(self) -> dict:
        return self.serializer.to_dict(self)


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
    RETRY = "RETRY"


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
        if event.get("parent_id"):
            parent_id = uuid.UUID(event["parent_id"])

        root_id = None
        if event.get("root_id"):
            root_id = uuid.UUID(event["root_id"])

        expires = None
        if event.get("expires"):
            expires = datetime.datetime.fromordinal(event["expires"])

        return cls(
            received_at=datetime.datetime.fromordinal(event["timestamp"]),
            runtime=int(event.get("runtime", 0)),
            state=TaskState[event["state"]],
            uuid=uuid.UUID(event["uuid"]),
            retries=event["retries"],
            kwargs=event["kwargs"],
            name=event.get("name"),
            parent_id=parent_id,
            args=event["args"],
            root_id=root_id,
            expires=expires,
        )


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


class EventHandler:
    def __init__(self, store, sio):
        self.store = store
        self.sio = sio

    def handle(self, event):
        self.store.events.append(event)
        if event["type"].startswith("worker-"):
            self.handle_worker_event(event)
        elif event["type"].startswith("task-"):
            self.handle_task_event(event)
        else:
            raise ValueError("%s is not a known event type", event["type"])

    def handle_task_event(self, event):
        if event["type"] == "task-received":
            self.store.tasks.receive(event)
        elif event["type"] == "task-started":
            task = Task.from_event(event)
            task = self.store.tasks.add(task)
        elif event["type"] == "task-succeeded":
            self.store.tasks[event["uuid"]].handle_success(event)

    def handle_worker_event(self, event):
        hostname = event["hostname"]
        event_type = event["type"]

        if event["type"] == "worker-heartbeat":
            self.store.workers[hostname].record_heartbeat(event)
        elif event["type"] in {"worker-online", "worker-offline"}:
            self.store.workers[hostname].update_status(event)
        else:
            raise RuntimeError("%s is not a valid worker event type.", event_type)


class EventPump(threading.Thread):
    def __init__(self, celery_app: Celery, queue: queue.Queue = None, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.celery_app: Celery = celery_app
        self.state = self.celery_app.events.State()
        self.run_attempts: int = 0
        self._queue = queue or queue.Queue()
        self._active = True
        self.start()

    def is_pumping(self) -> bool:
        return self._active

    @property
    def queue(self):
        return self._queue

    def push_event(self, event: dict):
        log.info(f"Pushing event: %s", event["type"])
        self.state.event(event)
        log.info(tuple(self.state.workers.values()))
        self.queue.put(event)

    def run(self):
        self.run_attempts += 1
        with self.celery_app.connection() as conn:
            log.info("Celery connection obtained.")
            while True:
                try:
                    receiver = self.celery_app.events.Receiver(
                        conn, handlers={"*": self.push_event}
                    )
                    receiver.capture(limit=None, timeout=None, wakeup=True)
                    self.run_attempts = 0
                except Exception as e:
                    self.run_attempts += 1
                    if self.run_attempts <= 3:
                        log.warning(
                            f"Run failed. %s attempts left.", 3 - self.run_attempts
                        )
                        self.run()
                    else:
                        raise RuntimeError("Too many run attempts. ", e)

    async def iter_async(self):
        while self.is_pumping():
            if self._queue.not_empty:
                log.info("Queue not empty... getting")
                yield self._queue.get()
            await standard_sleep()


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
                await standard_sleep()


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


class Sender:
    def __init__(self, sock):
        self.sock = sock

    async def message(self, sid, message, *args, **kwargs):
        message_event = {
            "uuid": str(uuid.uuid4()),
            "body": message,
            "timestamp": time.time(),
        }
        await self.sock.emit("message", message_event, *args, to=sid, **kwargs)

    async def event(self, event, *args, **kwargs):
        await self.sock.emit("event", event, *args, **kwargs)

    async def task_update(self, *args, **kwargs):
        await self.sock.emit("task-update", *args, **kwargs)
