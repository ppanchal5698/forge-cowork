"""Skill: text summarization. Stateless, short-lived → Lambda (CLAUDE.md §6)."""
from shared.ollama_client import generate


def handler(event, context):
    text = (event or {}).get("text", "")
    if not text.strip():
        return {"error": "no text provided"}
    summary = generate(f"Summarize the following in 2-3 sentences:\n\n{text}")
    return {"summary": summary.strip()}
