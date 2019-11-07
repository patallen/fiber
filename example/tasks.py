from example.models import CashFlowStatement
import requests

from example.worker import app
import time

BASE_URL = "https://financialmodelingprep.com/api/v3/financials/cash-flow-statement"


@app.task
def fetch_cashflow_statements(abbrev):
    time.sleep(1)
    return requests.get(f"{BASE_URL}/{abbrev}").json()["financials"]


@app.task
def serialize_cashflow_statements(statements):
    return [CashFlowStatement.from_dict(stmt) for stmt in statements]


@app.task
def average_cashflow_statements(statements):
    return {
            'opFlow': {
                'mean': sum(s.op_flow for s in statements)
                }
            }
