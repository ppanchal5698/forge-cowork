"""Checks the shared core clients against the running stack.

Run: docker compose exec backend python scripts/core_clients_test.py
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import ollama, storage

# Ollama wrapper — real generation, non-empty text back
out = ollama.generate("Reply with the single word: OK")
assert isinstance(out, str) and out.strip(), out
print(f"Ollama wrapper: OK ({out.strip()[:40]!r})")

# S3 artifact helper — tenant-prefixed key + round trip
tenant, run = f"tenant-{uuid.uuid4()}", str(uuid.uuid4())
key = storage.put_artifact(tenant, run, "output.txt", b"hello", content_type="text/plain")
assert key == f"artifacts/{tenant}/{run}/output.txt", key
assert storage.get_artifact(key) == b"hello"
print(f"S3 artifact helper: OK ({key})")

# Isolation guard — no un-tenanted paths
for bad in [("", run), (tenant, "")]:
    try:
        storage.artifact_key(*bad, "x")
        raise SystemExit(f"expected ValueError for {bad}")
    except ValueError:
        pass
print("artifact key guard: OK")

print("core clients: all OK")
