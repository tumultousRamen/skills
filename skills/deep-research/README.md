# Deep Research

## Why

LLMs and coding agents have a data problem. Reasoning keeps improving but the data layer has been constrained to training data plus sparse signal from flimsy web-search and web-fetch tool calls. Agents can plan research sprints, but they don't have a way to do them well — at production-research quality — without bolting on a paid service.

This skill is the in-repo answer. It uses **only Claude Code's native primitives** (WebSearch, WebFetch, the `browse` skill, subagents, Bash) and reaches the architecture pattern that Anthropic, LangChain, gpt-researcher, STORM, and Perplexity have all converged on: a multi-stage pipeline with parallel isolated workers, gap reflection, and post-hoc span-grounded citations.

No external API keys. No per-run credit cost.

## What it does

Runs five stages on a research request:

```
Scope → Plan → Research (parallel) → Reflect → Synthesize → Cite
```

Produces a written, footnoted markdown report at `.scratch/<slug>/report.md` with:
- Span-grounded citations (each footnote includes the literal supporting quote)
- An `[x]` marker on any claim the citation pass couldn't ground (honest weakly-typed feedback)
- A grounding-strength header (strong / medium / weak) when reliability matters
- A "Limitations" section if research couldn't fully cover the deliverable

## When to invoke

Use when the user explicitly asks to **research** something, **deep-dive**, **comprehensively analyze**, **produce a research report**, or invokes `/deep-research`. Also use when they want a written deliverable with citations, not just an answer.

**Don't use** for:
- Quick factual lookups
- Filling the agent's own knowledge gap mid-task (use `quick-research` instead)
- Single-source questions
- Tasks where speed matters more than thoroughness

## How it works

The skill is **orchestration over prompts** — no Python, no external services. The entry point is `SKILL.md`, which drives the five-stage pipeline by reading per-stage prompt files and spawning subagents.

```
deep-research/
  SKILL.md                 # Orchestrator — runs in main thread
  README.md                # This file
  prompts/
    planner.md             # Spawned as subagent prompt (Stage 1)
    researcher.md          # Spawned in parallel, one per research_unit (Stage 2)
    reflect.md             # Read by orchestrator's extended thinking (Stage 3)
    synthesizer.md         # Spawned as subagent prompt (Stage 4)
    citation.md            # Spawned as subagent prompt (Stage 5)
```

Per-run scratch state lives at `<cwd>/.scratch/<slug>/`:

```
.scratch/<slug>/
  brief.md                 # Scope output — the research question + great_answer line
  plan.yaml                # Plan output — flat list of disjoint research_units
  notes/<unit-id>.md       # Per-researcher checkpoint log + evidence (resume-capable)
  findings/<unit-id>.yaml  # Per-researcher compressed return
  draft.md                 # Synthesizer output with [u<id>] markers
  report.md                # Final report with footnote citations
  trace.jsonl              # Pipeline event log (debugging + resume)
```

## Plan checkpoint

After the planner runs, the orchestrator renders `plan.yaml` inline in chat and waits for an affirmative ("go", "lgtm", "looks good") before spawning researchers. You can:

- Edit `plan.yaml` directly in your editor — the orchestrator will re-read it.
- Edit it in chat ("drop u3", "tighten u2's source_guidance") — the orchestrator will edit the file and re-render.
- Ask questions about it without proceeding.

The plan is the source of truth. Whoever edits it last wins. Researchers always read the latest version on "go."

## Resume

Subsequent invocations on the same topic re-enter the existing `.scratch/<slug>/` rather than starting fresh:

- "continue with another wave on X" → spawns a new wave-2 unit on X, then reflect → synth → cite again.
- "redo synthesis with framing Y" → skips research, re-runs synthesizer + citation only.
- "dig deeper on u2" → spawns a wave-2 unit derived from u2's `gaps_identified`.

Hard cap: 2 research waves per run. Wave 3 requires explicit user opt-in.

## Failure philosophy

The report **always ships** unless one of three hard-halt conditions hits (disk unwritable, all researchers fail to find any sources, or scope can't elicit a brief). Everything else degrades gracefully:

- HTTP-aware fetch ladder per-URL (404 drop, 401/403 → browse → archive.org → drop, 429 backoff with `Retry-After`, etc.).
- Researcher subagent crash → retry once with resume-from-checkpoint, then continue without that unit.
- WebSearch empty → 3-step query reformulation fallback in the researcher.
- Reflect after wave 2 with gaps → `coverage_warnings` flow into a Limitations section. Ship.
- Citation can't ground a claim → `[x]` marker inline. Ship. >20% triggers a header warning but doesn't block.

## Design rationale

The full design doc — including which production systems we studied, what we deliberately did NOT build, and the locked answers to every design question we grilled through — lives at `<repo-root>/.research/deep-research-skill.md`. Read it before making non-trivial changes; the document captures the *why* behind decisions that look arbitrary in code.

## Status

This skill replaces the previous Firecrawl-backed `deep-research` skill. The Firecrawl version was a thin wrapper over `/agent`, requiring `FIRECRAWL_API_KEY` and per-run credits. This version uses only Claude Code primitives and costs nothing beyond the existing Claude Code subscription.
