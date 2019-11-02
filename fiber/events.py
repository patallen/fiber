from celery import Celery
import threading
from celery.events import EventReceiver

from asyncio import Queue


class EventPump(threading.Thread):
    def __init__(self, capp: Celery, queue: Queue = None, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.capp: Celery = capp
        self.state = capp.events.State()
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
        self.state.event(event)
        self.queue.put(event)

    def run(self):
        self.run_attempts += 1
        with self.capp.connection() as conn:
            while True:
                try:
                    recvr = self.capp.events.Receiver(
                        conn, handlers={"*": self.push_event}
                    )
                    recvr.capture(limit=None, timeout=None, wakeup=True)
                    self.run_attempts = 0
                except Exception as e:
                    self.run_attempts += 1
                    if self.run_attempts <= 3:
                        print(f"Run failed. {3 - self.run_attempts} attempts left.")
                        self.run()
                    else:
                        raise RuntimeError("Too many run attempts.")

    async def iter_async(self):
        while self.is_pumping():
            if self._queue.not_empty:
                yield self._queue.get()
            yield
