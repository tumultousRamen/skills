"""
CLI entry point for the deep-research skill.

Usage:
    python -m src.run "<research prompt>"

Exits 0 on success (prints JSON result to stdout).
Exits 1 on failure (prints error to stderr).
"""
import json
import sys

from .firecrawl.agent import start_agent
from .firecrawl.client import FirecrawlClient
from .firecrawl.poller import poll_agent


def run(prompt: str) -> dict:
    client = FirecrawlClient()

    print(f"[deep-research] Starting agent job...", flush=True)
    job_id = start_agent(prompt, client=client)
    print(f"[deep-research] Job ID: {job_id} — polling every 2s...", flush=True)

    result = poll_agent(job_id, client=client)

    if result.status == "completed":
        print(f"[deep-research] Completed. Credits used: {result.credits_used}", flush=True)
        return {
            "status": "completed",
            "job_id": job_id,
            "data": result.data,
            "credits_used": result.credits_used,
            "expires_at": result.expires_at,
        }

    raise RuntimeError(
        f"Research job {job_id} failed: {result.error or 'unknown error'}"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.run '<prompt>'", file=sys.stderr)
        sys.exit(1)

    prompt = sys.argv[1]

    if len(prompt) > 10000:
        print(
            f"Error: prompt is {len(prompt)} characters — must be under 10,000.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        output = run(prompt)
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
