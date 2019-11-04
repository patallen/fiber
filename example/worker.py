from datetime import date
import json

from kombu.serialization import register
from celery import Celery

from example.models import CashFlowStatement


class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, date):
            return {"__type__": "__date__", "epoch": o.isoformat()}

        if isinstance(o, CashFlowStatement):
            return {"__type__": "cfstmt", "kwargs": o.to_dict()}

        return json.JSONEncoder.default(self, o)


def decoder(o):
    if "__type__" in o:
        if o["__type__"] == "__date__":
            return date.fromisoformat(o["epoch"])
        if o["__type__"] == "cfstmt":
            return CashFlowStatement(**o["kwargs"])
    return o


def dumps(o):
    return json.dumps(o, cls=Encoder)


def loads(s):
    return json.loads(s, object_hook=decoder)


register(
    "fiberjson",
    dumps,
    loads,
    content_type="application/x-fiberjson",
    content_encoding="utf-8",
)

app = Celery(
    "tasks", backend="amqp://redis", broker="amqp://rabbitmq", include="example.tasks"
)

app.conf.update(
    accept_content=["fiberjson"],
    task_serializer="fiberjson",
    result_serializer="fiberjson",
)
