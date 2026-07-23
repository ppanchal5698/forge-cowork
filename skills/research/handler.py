"""Skill: small research call. Stateless, short-lived → Lambda (CLAUDE.md §6)."""
from shared.ollama_client import generate


def handler(event, context):
    query = (event or {}).get("query", "")
    if not query.strip():
        return {"error": "no query provided"}
    notes = generate(f"Give 3-5 concise factual bullet points about: {query}")
    return {"notes": notes.strip()}
