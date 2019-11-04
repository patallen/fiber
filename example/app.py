from flask import Flask, jsonify
from celery import chain

from example import tasks

app = Flask(__name__)
app.config["DEBUG"] = True


@app.route("/")
def index():
    return jsonify({"body": "Welcome!", "meta": {}})


@app.route("/cf/summary/<abbrev>")
def cash_flow_statement_summary(abbrev):
    result = chain(
        tasks.fetch_cashflow_statements.s(),
        tasks.serialize_cashflow_statements.s(),
        tasks.average_cashflow_statements.s(),
    ).delay(abbrev.upper())
    return jsonify(result.get())
