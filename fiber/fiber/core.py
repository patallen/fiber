import asyncio
import logging
import threading
import time
import uuid
from asyncio import Queue

from celery import Celery

log = logging.getLogger('fiber.core')


class EventPump(threading.Thread):
    def __init__(self, celery_app: Celery, queue: Queue = None, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.celery_app: Celery = celery_app
        self.state = self.celery_app.events.State()
        from celery.events.state import State
        print("WORKERS", self.state.workers)
        self.run_attempts: int = 0
        self._queue = queue or Queue()
        self._active = True
        self.start()

    def is_pumping(self) -> bool:
        return self._active

    @property
    def queue(self):
        return self._queue

    def push_event(self, event: dict):
        log.info(f"Pushing event: %s", event['type'])
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
                        log.warning(f"Run failed. %s attempts left.", 3 - self.run_attempts)
                        self.run()
                    else:
                        raise RuntimeError("Too many run attempts. ", e)

    async def iter_async(self):
        while self.is_pumping():
            if self._queue.not_empty:
                log.info("Queue not empty... getting")
                yield self._queue.get()
            await asyncio.sleep(0.05)


class Sender:
    def __init__(self, sock):
        self.sock = sock

    async def message(self, sid, message, *args, **kwargs):
        message_event = {
            'uuid': str(uuid.uuid4()),
            'body': message,
            'timestamp': time.time(),
        }
        await self.sock.emit('message', message_event, *args, to=sid, **kwargs)

    async def event(self, event, *args, **kwargs):
        await self.sock.emit('event', event, *args, **kwargs)

    async def task_update(self, *args, **kwargs):
        await self.sock.emit('task-update', *args, **kwargs)
