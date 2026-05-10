# Quick Research

## Why

Coding agents fail in two predictable ways when their training data runs out:

1. **Unknown entity.** The user mentions a tool, library, or service the agent has zero confident model of. Without a way to fill the gap, the agent either fabricates plausibly-wrong content or stops to ask the user for references — *before trying to find them itself*.
2. **Stale knowledge.** The agent confidently recalls a setup pattern, API surface, or recommended approach from training data, not realizing that pattern has been deprecated, renamed, or replaced. The user gets confidently delivered legacy advice.

Sibling to `deep-research`, but optimized for the opposite end of the spectrum. Where deep-research is a multi-stage research project that produces a written report, quick-research is a 30-second context fill the agent invokes liberally mid-task.

## What it does

Spawns one `general-purpose` subagent that runs a tight WebSearch + WebFetch loop and returns a question-shaped answer. The subagent's context absorbs the raw fetched content (5–15k tokens per page); the calling agent only sees the final compressed answer (~300–2000 tokens depending on the question).

```
caller has a knowledge gap mid-task
        ↓
subagent: ≤3 searches → ≤4 fetches (early-exit) → compose
        ↓
returned message: question-shaped answer + ## Caveats + ## Sources
        ↓
caller incorporates into reply, surfaces sources
```

## When to invoke

**USE when:**

- The user mentions a tool, library, product, person, or event you have no confident model of.
- The user asks for "latest" / "current" / "recent" / "this week's" anything.
- You're advising on documentation, APIs, SDK usage, config, deployment recipes, or pricing for an actively-evolving service AND your confident knowledge of it predates ~4 months from `date -u`.

**Don't use** for:

- Stable concepts (algorithms, language semantics, established CS).
- Facts visible in the local codebase or already provided by the user.
- Cases where you have an exact URL and just need to fetch it (call `WebFetch` directly, no subagent).
- Deliverables that need a written report with citations — use `deep-research`.

## Invocation contract

The caller passes:

```
question:    the specific user-facing question this lookup will help answer
prior_model: (optional) what you currently believe, if anything — the
             subagent will verify or refute that specifically
today:       date -u +%Y-%m-%d
```

`question` should be the *specific user-facing question*, not a vague topic. "How do I reinstall openclaw from scratch?" beats "look up openclaw."

`prior_model` is the high-leverage optional field for staleness checks: "I believe Supabase auth uses `signIn({ email, password })` — verify or correct." The subagent targets that specific claim instead of re-deriving the whole setup.

## How it works

The skill is **orchestration over a single prompt** — no Python, no external services, no plan checkpoint, no persistence.

```
quick-research/
  SKILL.md              # Orchestrator — read by the calling agent
  README.md             # This file
  prompts/
    researcher.md       # Spawned as the subagent's prompt
```

There is no `.scratch/` directory, no notes file, no trace log. Quick-research is *context*, not a deliverable. The result lives in the conversation; the caller uses it and moves on.

## Internal protocol (subagent)

- ≤3 WebSearch calls (with refinement strategies: drop-most-specific → synonymize → site-target).
- ≤4 WebFetch calls with early-exit (stop on first authoritative answer; fetch more only for verification, contradiction-checking, or staleness checks).
- HTTP fallback ladder: 2xx-tiny → `browse` once → drop. 4xx/5xx → drop, no retry. Per-URL attempt cap: 1.
- Source priority: official docs > recent credible blog/release notes > Stack Overflow / GitHub issues > everything else.
- Verbatim quoting of code, commands, config — no paraphrase.
- Mandatory `## Caveats` and `## Sources` sections in the returned answer.
- `no_useful_sources` is a first-class return shape — never fabricate.

## Returning to the user

When the calling agent incorporates the subagent's answer into its reply:

- Answer naturally — don't preface with "I looked this up."
- Quote code/commands/config verbatim from the subagent's response.
- Surface the sources at the end so the user can see what was web-verified.
- If the subagent returned `no_useful_sources`, say so honestly and ask the user for a reference.

## Cost trade

The skill optimizes for **caller-context-window**, not total tokens billed. Subagent invocation costs slightly more total tokens than running the loop in main thread (spawn overhead, duplicated prompt) — but it keeps the raw fetched content out of the caller's window, which is what makes liberal invocation across a long session viable.

For Claude Code, where context-window pressure is the dominant constraint, this is the correct trade.
