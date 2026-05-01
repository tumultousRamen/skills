---
name: deep-research
description: Conduct thorough, in-depth research on any topic by running Firecrawl's deep research agent. Use when the user explicitly asks to conduct research, run deep research, or invokes /deep-research. Requires FIRECRAWL_API_KEY set in ~/.claude/settings.json under "env".
---

You have access to a deep research tool powered by Firecrawl's /agent endpoint.

## Prerequisites

Before running, ensure the user has `FIRECRAWL_API_KEY` set. It must be in `~/.claude/settings.json` under the `env` key:

```json
{ "env": { "FIRECRAWL_API_KEY": "fc-..." } }
```

If the key is missing, tell the user and stop.

The skill uses a local virtual environment at `<SKILL_DIR>/.venv/`. If it is missing (e.g. fresh clone), create it:

```bash
cd <SKILL_DIR> && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -q
```

## Running Research

Formulate a research prompt from the user's request. The prompt **must be under 10,000 characters**.

Run from the skill's base directory using the venv's Python:

```bash
cd <SKILL_DIR> && .venv/bin/python -m src.run "<research prompt>"
```

`<SKILL_DIR>` is the base directory shown at the top of this skill file. `<research prompt>` is the prompt you construct — escape any double quotes inside it.

The script prints progress lines prefixed with `[deep-research]` to stdout, then outputs a JSON result:

```json
{
  "status": "completed",
  "job_id": "...",
  "data": { ... },
  "credits_used": 123,
  "expires_at": "..."
}
```

## Handling the Result

- **completed**: Present `data` to the user in a clear, well-structured format. Mention credits used.
- **failed**: The script exits with code 1 and prints the error to stderr. Surface the error message to the user.
- **venv missing**: If `.venv/bin/python` is not found, run the one-time setup command above, then retry.

## Prompt Crafting Guidelines

- Be specific and focused — vague prompts produce vague results.
- Include the domain, time range, and desired output format when relevant.
- Keep under 10,000 characters (the script enforces this and exits early with a clear error).
