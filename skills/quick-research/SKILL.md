---
name: quick-research
description: >
  Fast web lookup to fill the agent's own knowledge gap mid-task. A subagent
  runs a tight WebSearch + WebFetch loop (≤3 searches, ≤4 fetches) and returns
  a question-shaped answer with caveats and sources. Designed to be invoked
  liberally — context isolation keeps the caller's window clean.

  DO NOT use for: stable concepts (algorithms, language semantics, math,
  established CS); facts visible in the local codebase or already provided
  by the user; cases where you have an exact URL and just need to fetch it
  (do that directly with WebFetch); deliverables that need a written report
  with citations (use deep-research instead); or when speed matters more
  than current accuracy.

  USE when:
  - The user mentions a tool, library, product, person, or event you have
    no confident model of.
  - The user asks for "latest" / "current" / "recent" / "this week's" anything.
  - You're advising on documentation, APIs, SDK usage, config, deployment
    recipes, or pricing for an actively-evolving service AND your confident
    knowledge of it predates ~4 months from `date -u`.

  When invoking, pass:
    question:    the specific user-facing question this lookup will help answer
    prior_model: (optional) what you currently believe, if anything — the
                 subagent will verify or refute that specifically

  When using the returned answer in your reply, surface the sources. The
  user should be able to see what was web-verified vs. recalled.
---

# Quick Research

A single-subagent web lookup that fills the calling agent's knowledge gap mid-task. Sibling to `deep-research`: where deep-research produces a written, span-grounded report at `.scratch/<slug>/report.md`, quick-research produces a returned message you use immediately and discard. No persistence, no plan checkpoint, no synthesis stage — just search → fetch → compress → return.

The architectural premise: the calling agent's context window is the scarce resource. Doing the search/fetch loop in a subagent means raw fetch content (5–15k tokens per page) lives in the subagent's context, not yours. You only see the final compressed answer. That's what makes "called liberally" viable across a long session.

## Setup (do this first, every run)

1. Determine `<SKILL_DIR>` — the absolute path to this skill's directory (the directory containing this `SKILL.md`). You'll need it to read `prompts/researcher.md`.
2. Run `date -u +%Y-%m-%d` via Bash; remember as `<TODAY>`.

## How to invoke

1. Read `<SKILL_DIR>/prompts/researcher.md`.
2. Spawn a `general-purpose` subagent in a single tool message with:
   - The full contents of `prompts/researcher.md` as the prompt
   - An appended `## Invocation payload` section containing:
     - `question:` the specific user-facing question you're trying to answer
     - `prior_model:` (optional) what you currently believe, if anything
     - `today:` `<TODAY>`
3. The subagent returns a markdown answer. Use it in your reply to the user and surface the sources (see "Returning to the user" below).

The subagent is a one-shot. Spawn it with everything it needs in a single message; do not chat with it across turns.

### Forming the `question` field

The output quality is bounded by how the caller phrases the question. Bad invocation: "look up openclaw." Good invocation: "I need to tell the user how to reinstall openclaw from scratch — find the official reinstall procedure." The question should be the *specific user-facing question this lookup will help answer*, not a vague "tell me about X."

### When to populate `prior_model`

Use it when your confident-but-possibly-stale knowledge is the thing you want verified. Example:

> question: "What's the current way to set up Supabase auth?"
> prior_model: "I believe it's `supabase.auth.signIn({ email, password })` with the
>               supabase-js v1 SDK; the user's repo is on supabase-js v2."

The subagent will target that claim specifically (verify-or-refute) instead of re-deriving the whole setup. Big speedup for the staleness case.

## When NOT to invoke (anti-triggers)

Duplicated from the frontmatter for the orchestrator's eyes:

- The user already gave you the answer in this session.
- The fact you need is in the local codebase — read it instead.
- You have the exact URL — call WebFetch directly, no subagent.
- It's a stable concept (algorithms, language semantics, established CS).
- The user asked for a deep-dive deliverable with citations — use deep-research.

## Returning to the user

When you incorporate the subagent's answer into your reply:

- Answer the user's question naturally — don't preface with "I looked this up." The lookup is a means, not the message.
- Quote code samples, exact commands, and config snippets verbatim from the subagent's response. Paraphrasing reintroduces the staleness problem we were solving.
- **Surface the sources at the end of your reply** — same as you'd cite anything fetched mid-conversation. The user should be able to see what was web-verified vs. recalled.
- If the subagent returned the `no_useful_sources` shape (see researcher prompt), say so honestly: "I tried to look this up and couldn't find authoritative info — do you have a reference URL or alternative name for the topic?"

## Hard rules (orchestrator)

- Do NOT skip the subagent and run WebSearch/WebFetch yourself. The whole point is context isolation; running it in main thread defeats the skill.
- Do NOT invoke this skill recursively from inside another research skill (e.g. from a deep-research researcher subagent). Those agents already have web tools and their own protocol.
- Do NOT silently swallow the answer. Sources must surface to the user.
- Do NOT extend the budget. If 3 searches + 4 fetches doesn't find it, the subagent returns `no_useful_sources`; tell the user honestly.
- Do NOT write to disk. This skill is ephemeral — no `.scratch/`, no notes file, no trace.
