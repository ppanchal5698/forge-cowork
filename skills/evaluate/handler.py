"""Skill: evaluation agent. Judges whether the worker's answer addresses the task.
Stateless, short-lived → Lambda (CLAUDE.md §6)."""
from shared.ollama_client import generate


def handler(event, context):
    answer = (event or {}).get("answer", "")
    task = (event or {}).get("task", "")
    if not answer.strip():
        return {"error": "no answer provided"}
    verdict = generate(
        f"Task: {task}\nAnswer: {answer}\n\n"
        "Does the answer address the task? Reply with one word: APPROVE or REVISE."
    )
    return {"approved": "APPROVE" in verdict.upper(), "verdict": verdict.strip()[:200]}
