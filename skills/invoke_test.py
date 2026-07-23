"""Invoke deployed skill Lambdas and assert real output — proves MiniStack Lambda
execution + Ollama reachability from the Lambda runtime.

Run (after deploy_skills.py): docker compose exec backend python /skills/invoke_test.py
"""
import json
import os

import boto3

lam = boto3.client(
    "lambda",
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
    endpoint_url=os.environ.get("AWS_ENDPOINT_URL"),
)


def invoke(fn: str, payload: dict) -> dict:
    resp = lam.invoke(FunctionName=fn, Payload=json.dumps(payload).encode())
    return json.loads(resp["Payload"].read())


s = invoke("skill-summarize", {"text": "Ministack emulates AWS locally. It runs on port 4566. "
                               "It supports Lambda, S3, SQS and more."})
assert s.get("summary"), s
print(f"skill-summarize OK: {s['summary'][:80]!r}")

r = invoke("skill-research", {"query": "the Neo4j graph database"})
assert r.get("notes"), r
print(f"skill-research OK: {r['notes'][:80]!r}")

print("skills invoke: all OK")
