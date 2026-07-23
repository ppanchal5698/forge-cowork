"""Sprint 1 parity smoke test: same SDK calls that run in production, pointed at
MiniStack/local services. Run: docker compose exec backend python scripts/smoke_test.py
"""
import json
import os
import uuid

import boto3
import httpx
import psycopg2
import redis
from neo4j import GraphDatabase

ENDPOINT = os.environ.get("AWS_ENDPOINT_URL")
REGION = os.environ.get("AWS_REGION", "us-east-1")
TENANT = "tenant-smoke"


def aws(service):
    return boto3.client(service, region_name=REGION, endpoint_url=ENDPOINT)


# S3 round trip — tenant-prefixed key (CLAUDE.md §5)
s3 = aws("s3")
key = f"artifacts/{TENANT}/{uuid.uuid4()}.json"
s3.put_object(Bucket="artifacts", Key=key, Body=b'{"ok": true}')
assert json.loads(s3.get_object(Bucket="artifacts", Key=key)["Body"].read())["ok"] is True
print("S3: OK")

# DynamoDB round trip — TENANT# partition key (CLAUDE.md §5)
ddb = aws("dynamodb")
ddb.put_item(
    TableName="agent_state",
    Item={"PK": {"S": f"TENANT#{TENANT}"}, "SK": {"S": "SMOKE"}, "v": {"S": "1"}},
)
item = ddb.get_item(
    TableName="agent_state",
    Key={"PK": {"S": f"TENANT#{TENANT}"}, "SK": {"S": "SMOKE"}},
)["Item"]
assert item["v"]["S"] == "1"
print("DynamoDB: OK")

# Postgres — same DATABASE_URL the app uses; tenants table proves migration ran
conn = psycopg2.connect(os.environ["DATABASE_URL"])
with conn.cursor() as cur:
    cur.execute("SELECT count(*) FROM tenants")
    cur.fetchone()
conn.close()
print("Postgres: OK")

# Neo4j
driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
)
driver.verify_connectivity()
driver.close()
print("Neo4j: OK")

# Ollama
assert httpx.get(os.environ["OLLAMA_BASE_URL"] + "/api/tags", timeout=10).status_code == 200
print("Ollama: OK")

# Redis
assert redis.from_url(os.environ["REDIS_URL"]).ping()
print("Redis: OK")

print("smoke test: all services OK")
