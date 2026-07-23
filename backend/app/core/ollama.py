import httpx

from .config import settings


def generate(prompt: str, model: str | None = None, timeout: float = 120.0) -> str:
    """Single entry point for all LLM calls (CLAUDE.md §8).

    ponytail: per-tenant concurrency rate limiting + plan-tier model gating land
    here in Sprint 3. Keep this the only place that hits Ollama so that wrapper is
    the sole chokepoint — never call the endpoint directly from a skill/plugin.
    """
    resp = httpx.post(
        f"{settings.ollama_base_url}/api/generate",
        json={"model": model or settings.ollama_model, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["response"]
