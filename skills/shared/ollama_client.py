"""Shared Ollama entry point for skills running as Lambdas.

Mirrors backend `app.core.ollama.generate`, but stdlib-only (urllib, no httpx) so a
skill's deployment zip needs no pip dependencies. Skills run in a separate deployment
unit and can't import the backend package — this is their shared wrapper (CLAUDE.md §8).

ponytail: per-tenant concurrency rate limiting + plan-tier model gating (Sprint 3)
wrap here too — keep this the only place a skill touches Ollama.
"""
import json
import os
import urllib.request


def generate(prompt: str, model: str | None = None, timeout: float = 180.0) -> str:
    base = os.environ["OLLAMA_BASE_URL"]
    model = model or os.environ.get("OLLAMA_MODEL", "llama3.2:1b")
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        f"{base}/api/generate", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["response"]
