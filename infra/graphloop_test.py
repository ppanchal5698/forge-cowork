"""Run the Graph Loop state machine end-to-end: a success path and a forced-failure
path (empty title → worker input missing → retries exhaust → DLQ → Fail).

Run (after skills + state machine deployed):
  docker compose cp ./infra backend:/infra && docker compose exec backend python /infra/graphloop_test.py
"""
import json
import os
import time

import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
ENDPOINT = os.environ.get("AWS_ENDPOINT_URL")
sfn = boto3.client("stepfunctions", region_name=REGION, endpoint_url=ENDPOINT)
sqs = boto3.client("sqs", region_name=REGION, endpoint_url=ENDPOINT)

SM_ARN = next(
    m["stateMachineArn"]
    for m in sfn.list_state_machines()["stateMachines"]
    if m["name"] == "graph-loop"
)


def run(payload: dict, deadline: float = 180.0) -> dict:
    ex = sfn.start_execution(stateMachineArn=SM_ARN, input=json.dumps(payload))["executionArn"]
    end = time.time() + deadline
    while time.time() < end:
        d = sfn.describe_execution(executionArn=ex)
        if d["status"] != "RUNNING":
            return d
        time.sleep(2)
    raise SystemExit("execution timed out")


# Success path
ok = run({"title": "the Neo4j graph database"})
assert ok["status"] == "SUCCEEDED", ok["status"]
print(f"success path: {ok['status']}")

# Failure path — drain DLQ first so we detect this run's message
dlq = sqs.get_queue_url(QueueName="agent-tasks-dlq")["QueueUrl"]
sqs.purge_queue(QueueUrl=dlq)
time.sleep(1)

bad = run({"title": ""})
assert bad["status"] == "FAILED", bad["status"]
print(f"failure path: {bad['status']}")

msgs = sqs.receive_message(QueueUrl=dlq, WaitTimeSeconds=3, MaxNumberOfMessages=1).get("Messages", [])
assert msgs, "expected a message in the DLQ after retries exhausted"
print(f"DLQ received failure: {msgs[0]['Body'][:80]!r}")

print("graph loop: all OK")
