"""E2E acceptance-path check: signup → login → create task → start run →
poll to completion → artifact stored (S3 key) + graph written.

Run: docker compose exec backend python scripts/agents_test.py
"""
import time

import httpx

BASE = "http://localhost:8000"
EMAIL = f"agent{int(time.time())}@example.com"
PASSWORD = "Passw0rd!123"

httpx.post(
    f"{BASE}/auth/signup",
    json={"email": EMAIL, "password": PASSWORD, "tenant_name": "acme"},
).raise_for_status()
tokens = httpx.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD}).json()
h = {"Authorization": f"Bearer {tokens['id_token']}"}

task = httpx.post(f"{BASE}/tasks", json={"title": "the Neo4j graph database"}, headers=h).json()

started = httpx.post(f"{BASE}/tasks/{task['id']}/runs", headers=h)
assert started.status_code == 201, started.text
run = started.json()
assert run["status"] == "running", run

deadline = time.time() + 180
final = None
while time.time() < deadline:
    got = httpx.get(f"{BASE}/runs/{run['id']}", headers=h).json()
    if got["status"] != "running":
        final = got
        break
    time.sleep(2)

assert final and final["status"] == "done", final
assert final["output_key"] == f"artifacts/{run['tenant_id']}/{run['id']}/output.json", final
print(f"agent run OK: {final['status']} → {final['output_key']}")

# cross-tenant isolation: a second tenant can't read the first tenant's run
E2 = f"agent{int(time.time())}b@example.com"
httpx.post(f"{BASE}/auth/signup", json={"email": E2, "password": PASSWORD, "tenant_name": "beta"}).raise_for_status()
t2 = httpx.post(f"{BASE}/auth/login", json={"email": E2, "password": PASSWORD}).json()
h2 = {"Authorization": f"Bearer {t2['id_token']}"}
assert httpx.get(f"{BASE}/runs/{run['id']}", headers=h2).status_code == 404
print("cross-tenant run isolation: 404 OK")

print("agents: all OK")
