"""E2E auth check against the running stack: signup → login → /auth/me → refresh.

Run: docker compose exec backend python scripts/auth_test.py
"""
import time

import httpx

BASE = "http://localhost:8000"
EMAIL = f"user{int(time.time())}@example.com"
PASSWORD = "Passw0rd!123"

signup = httpx.post(
    f"{BASE}/auth/signup",
    json={"email": EMAIL, "password": PASSWORD, "tenant_name": "acme"},
)
assert signup.status_code == 201, signup.text
tenant_id = signup.json()["tenant_id"]

dup = httpx.post(
    f"{BASE}/auth/signup",
    json={"email": EMAIL, "password": PASSWORD, "tenant_name": "acme"},
)
assert dup.status_code == 409, dup.text

login = httpx.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
assert login.status_code == 200, login.text
tokens = login.json()

me = httpx.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {tokens['id_token']}"})
assert me.status_code == 200, me.text
assert me.json()["tenant_id"] == tenant_id, me.json()

refreshed = httpx.post(f"{BASE}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
assert refreshed.status_code == 200, refreshed.text
assert refreshed.json()["id_token"]

bad = httpx.get(f"{BASE}/auth/me", headers={"Authorization": "Bearer garbage"})
assert bad.status_code == 401, bad.text

wrong_pw = httpx.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": "nope"})
assert wrong_pw.status_code == 401, wrong_pw.text

print(f"auth OK: {EMAIL} tenant={tenant_id}")
