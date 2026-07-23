"""E2E task CRUD check against the running stack.

Run: docker compose exec backend python scripts/tasks_test.py
"""
import time

import httpx

BASE = "http://localhost:8000"
EMAIL = f"tasks{int(time.time())}@example.com"
PASSWORD = "Passw0rd!123"

httpx.post(
    f"{BASE}/auth/signup",
    json={"email": EMAIL, "password": PASSWORD, "tenant_name": "acme"},
).raise_for_status()
tokens = httpx.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD}).json()
h = {"Authorization": f"Bearer {tokens['id_token']}"}

created = httpx.post(f"{BASE}/tasks", json={"title": "summarize deck"}, headers=h)
assert created.status_code == 201, created.text
task = created.json()
assert task["title"] == "summarize deck"
assert task["status"] == "pending"

listed = httpx.get(f"{BASE}/tasks", headers=h)
assert listed.status_code == 200, listed.text
assert any(t["id"] == task["id"] for t in listed.json())

one = httpx.get(f"{BASE}/tasks/{task['id']}", headers=h)
assert one.status_code == 200 and one.json()["id"] == task["id"], one.text

missing = httpx.get(f"{BASE}/tasks/{'0' * 8}-0000-0000-0000-000000000000", headers=h)
assert missing.status_code == 404, missing.text

no_auth = httpx.get(f"{BASE}/tasks")
assert no_auth.status_code == 401, no_auth.text

print(f"tasks OK: created+listed+fetched {task['id']}")
