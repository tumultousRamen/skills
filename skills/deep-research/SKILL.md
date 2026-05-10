---
name: deep-research
description: >
  Conduct thorough, multi-stage research on a topic with parallel investigation,
  gap analysis, and span-grounded citations. Produces a written markdown report
  at .scratch/<slug>/report.md with a plan checkpoint where the user reviews
  before research fans out. The pipeline runs scope → plan → parallel research
  → reflect → synthesize → cite.

  USE when the user explicitly asks to: conduct/run research, perform deep
  research, do a deep dive, comprehensively analyze, produce a research report,
  or invokes /deep-research. Also use when the user wants a written deliverable
  with citations, not just an answer.

  DO NOT use for: quick factual lookups, filling the agent's own knowledge gap
  mid-task (the quick-research skill handles those — use it instead), single-source
  questions, or tasks where speed matters more than thoroughness. Do not use when
  the user just wants to know "what's X" — that's quick-research territory.

  Resumable: subsequent invocations on the same topic re-enter the existing
  .scratch/<slug>/ run rather than starting fresh.
---

# Deep Research

You are the orchestrator of a multi-stage research pipeline. The pipeline runs five stages: **Scope → Plan → Research → Reflect → Synthesize → Cite**. Some stages run in your main thread; some run in subagents you spawn.

This skill produces a written, span-grounded markdown report at `.scratch/<slug>/report.md`. Its design rationale is documented in `.research/deep-research-skill.md` (read that file if you need to understand *why* a stage works the way it does).

## Pipeline overview

| Stage | Where it runs | Output |
|---|---|---|
| 0. Scope | Main thread, free-form Q&A | `<SCRATCH_DIR>/brief.md` |
| 1. Plan | `general-purpose` subagent | `<SCRATCH_DIR>/plan.yaml` |
| — | Plan checkpoint with user (main thread) | go / edit / proceed |
| 2. Research | N `general-purpose` subagents in parallel | `<SCRATCH_DIR>/notes/<u>.md` + `<SCRATCH_DIR>/findings/<u>.yaml` |
| 3. Reflect | Main thread, extended thinking | decision: proceed / another wave |
| 4. Synthesize | `general-purpose` subagent | `<SCRATCH_DIR>/draft.md` |
| 5. Cite | `general-purpose` subagent | `<SCRATCH_DIR>/report.md` |

## Setup (do this first, every run)

1. Determine `<SKILL_DIR>` — the absolute path to this skill's directory (the directory containing this `SKILL.md`). You'll need it to read prompts/.
2. Determine the working directory's scratch root: `<CWD>/.scratch/`. Create it via `mkdir -p` if missing.
3. Run `date -u +%Y-%m-%dT%H:%M:%SZ` via Bash; remember as `<NOW>` for trace timestamps.

## Resume detection (BEFORE Stage 0)

If the user's request looks like a continuation, do NOT start a fresh run. Heuristics for "continuation":

- They say "continue", "another wave", "redo synth", "redo synthesis with framing X", "dig deeper on uN", or similar.
- Their request mentions a topic for which a `.scratch/<slug>/` already exists.

When you detect continuation:

1. Identify the matching slug (ask the user if ambiguous between multiple existing scratch dirs).
2. Read `<SCRATCH_DIR>/trace.jsonl` to determine the last completed stage.
3. Re-enter at the appropriate stage with the user's new instruction:
   - "another wave on X" → re-enter Reflect (forcing `another_research_round` with a new unit on X), then proceed through Research → Reflect → Synthesize → Cite.
   - "redo synthesis with framing Y" → skip Stages 0–3, re-enter at Synthesize with framing Y as a manual `framing_update`.
   - "dig deeper on u2" → spawn a wave-2 unit derived from u2's `gaps_identified`, then Reflect → Synthesize → Cite.
4. Append a `{"stage":"resume","event":"reentered","at_stage":"<stage>"}` event to `trace.jsonl`.
5. The 2-wave hard cap can be extended to wave 3 only when the user *explicitly* asks for "another wave" beyond wave 2 — never silently.

## Stage 0 — Scope (main thread)

**Goal:** produce `<SCRATCH_DIR>/brief.md`.

You do NOT use `AskUserQuestion`. You ask clarifying questions in plain prose, in chat, and the user answers in plain prose. This is a deliberate design choice — keep it natural.

### When to ask vs. when to write the brief directly

Ask 1–3 free-form clarifying questions if any of these are unclear from the user's initial request:

- The deliverable shape (comparison-table / annotated-bibliography / report-with-sections / direct-answer)
- The audience (technical depth, prior knowledge)
- The time horizon (post-2024 only? historical? current as of this week?)
- What a "great answer" would look like (forces commitment to a vision)

If the user's request already specifies these, write the brief directly without asking.

### Brief schema

After scope settles, write `<SCRATCH_DIR>/brief.md` with this YAML body (no other content):

```yaml
question: <restated and scoped, one or two sentences>
deliverable_shape: comparison-table | annotated-bibliography | report-with-sections | direct-answer
depth_class: shallow | medium | deep      # advisory; planner re-decides
time_horizon: <e.g. "post-2024 sources preferred", "current as of this week", "historical context welcome">
audience: <one phrase, e.g. "technical, familiar with LLM internals">
today: <YYYY-MM-DD UTC>                   # from Bash date
great_answer: |
  <One sentence describing what an outstanding answer to this question
  looks like. The reflect stage uses this as its done-ness check.>
counter_positions: []                     # only filled when deliverable is opinionated/comparative
```

Append to `trace.jsonl`:
```jsonl
{"t":"<NOW>","stage":"scope","event":"brief_written","question":"<question>"}
```

You don't yet know the slug — that's the planner's job. Until the planner picks one, write the brief to a temporary path you'll move once the slug exists. Or simpler: ask the planner to pick the slug first as a pre-pass and only then create `<SCRATCH_DIR>` and write the brief. Either is fine; both work.

**Suggested order**: ask the planner to pick the slug from the brief content (pass the brief inline in the spawn message), then create `<SCRATCH_DIR>` based on what the planner returns, write `brief.md` to it, and proceed to Stage 1 properly. This avoids the temp-path dance.

## Stage 1 — Plan (subagent)

**Goal:** produce `<SCRATCH_DIR>/plan.yaml`.

### Spawn the planner

Read `<SKILL_DIR>/prompts/planner.md`. Spawn a `general-purpose` subagent with:

- The full contents of `prompts/planner.md` as its prompt
- Plus appended sections containing:
  - The full contents of `brief.md`
  - The absolute path to `<SCRATCH_DIR>` (or instructions to create one based on a slug it picks)
  - Today's date in UTC

The planner subagent will:
- Run a WebSearch landscape scan (≤5 calls)
- Decide effort_class
- Cleave research_units thematically per `deliverable_shape`
- Write `plan.yaml` to `<SCRATCH_DIR>/plan.yaml`
- Return a brief confirmation

### After the planner returns

Append to `trace.jsonl`:
```jsonl
{"t":"<NOW>","stage":"plan","event":"plan_written","slug":"<slug>","units":<N>,"effort":"<class>","budget_total":<sum of budget_fetches>}
```

## Plan checkpoint — render inline, await semantic affirmative (main thread)

`plan.yaml` is the source of truth. Either you (in response to the user) or the user (directly) can edit it. Researchers always read the latest version on "go."

### Render the plan inline

Read `<SCRATCH_DIR>/plan.yaml` and display its content in chat. Plans are typically 50–150 lines / ~600–2500 tokens — render the file directly, not a summary.

Append the path and an explicit "say go to proceed" line:

```
Full plan: <SCRATCH_DIR>/plan.yaml — edit there or tell me what to change. Say "go" to proceed.
```

### User responses

- **Affirmative (no improvement):** "go", "proceed", "yes", "lgtm", "looks good", "ship it" → proceed to Stage 2.
- **Affirmative + edit suggestion:** "looks good but tighten u2's source_guidance" → edit `plan.yaml` accordingly (use `Read`/`Edit`), re-render the updated plan inline, await another affirmative.
- **Edits in chat:** "drop u3", "expand u1 to also cover X" → same as above, edit `plan.yaml`, re-render, await affirmative.
- **Edits in editor:** if the user says they edited the file, `Read` `plan.yaml` again and proceed.
- **Question:** answer the question, await affirmative.
- **Ambiguous ("hmm", "interesting", silent):** ask explicitly "ready to proceed?". Do NOT proceed on ambiguity.

Append on approval:
```jsonl
{"t":"<NOW>","stage":"checkpoint","event":"plan_approved","edits":[<list of human-readable edits, may be empty>]}
```

## Stage 2 — Research (parallel subagents)

**Goal:** produce `<SCRATCH_DIR>/notes/<unit-id>.md` and `<SCRATCH_DIR>/findings/<unit-id>.yaml` for every research_unit.

### Spawn researchers in parallel

Read `<SKILL_DIR>/prompts/researcher.md`. For each `research_unit` in `plan.yaml`:

- Construct a researcher prompt = `researcher.md` content + appended sections containing:
  - Full contents of `brief.md`
  - The full YAML of THIS unit (one entry from `research_units`)
  - The `landscape_notes` block from `plan.yaml`
  - Absolute path to `<SCRATCH_DIR>`
  - Today's date in UTC

**Spawn ALL researchers in a single tool message** (all `Agent` calls in one assistant turn). This is what makes them run in parallel. Do NOT spawn sequentially — that defeats the architectural purpose of multi-agent context shedding.

`mkdir -p <SCRATCH_DIR>/notes <SCRATCH_DIR>/findings` before spawning so the researchers can write into them.

Append before spawning:
```jsonl
{"t":"<NOW>","stage":"research","event":"wave_started","wave":<1 or 2>,"unit_ids":[<list>]}
```

### As each researcher returns

Each returns a YAML `Findings` block per the schema in `prompts/researcher.md`. Save it to `<SCRATCH_DIR>/findings/<unit-id>.yaml` (Write the YAML body to the file).

Append per-unit:
```jsonl
{"t":"<NOW>","stage":"research","event":"unit_done","unit_id":"<id>","status":"<status>","fetches":<n>,"resumed":<bool>}
```

### Failure handling for researchers

- **Errored or crashed subagent**: retry the spawn ONCE with the same prompt. The researcher's resume protocol (in its prompt) will pick up the partial notes file from the previous attempt. If retry also fails: mark the unit `errored` and continue with the rest. Append a trace event with `"status":"errored","retry":2,"action":"continue_without"`.
- **Returned `no_sources_found`**: not an error. Reflect will decide whether to broaden seeds in wave 2 or accept the gap.
- **Returned `partial`**: not an error. The notes file will have whatever was gathered.

After all researchers return (or fail terminally):
```jsonl
{"t":"<NOW>","stage":"research","event":"wave_complete","wave":<n>,"complete":<n>,"partial":<n>,"no_sources":<n>,"errored":<n>}
```

## Stage 3 — Reflect (main thread, extended thinking)

Read `<SKILL_DIR>/prompts/reflect.md` for the protocol. Apply it in your own main-thread extended thinking. (The instructions in `reflect.md` are written for *you*, the orchestrator, not a subagent.)

Inputs (read into context):
- `<SCRATCH_DIR>/brief.md`
- `<SCRATCH_DIR>/plan.yaml`
- All `<SCRATCH_DIR>/findings/<unit-id>.yaml` files
- All `<SCRATCH_DIR>/notes/<unit-id>.md` `## Checkpoint` blocks (read just the bottom of each file to get status without bloating context)
- The current wave counter

Run the three passes (coverage / adversarial / compellingness) and emit one of two decisions:

- `proceed_to_synthesis` (with optional `contradictions_to_flag`, `framing_updates`, `coverage_warnings`)
- `another_research_round` (with `rationale`, `new_units`, optional `framing_updates`)

### Termination rules

- Hard cap: 2 waves. If you'd want a wave 3, override to `proceed_to_synthesis` with `coverage_warnings` populated.
- Wave 2 with 0 new units → done.
- Contradictions never trigger more research; they go into `contradictions_to_flag`.

### Append to trace

```jsonl
{"t":"<NOW>","stage":"reflect","event":"<another_wave|proceed>","wave":<n>,"rationale":"<short>","framing_updates":<n>,"contradictions":<n>}
```

If `another_research_round`, append the new units to `plan.yaml`'s `research_units` list (don't lose the original ones — append) and loop back to Stage 2 with just the new unit IDs.

## Stage 4 — Synthesize (subagent)

**Goal:** produce `<SCRATCH_DIR>/draft.md`.

### Spawn the synthesizer

Read `<SKILL_DIR>/prompts/synthesizer.md`. Spawn a `general-purpose` subagent with:

- The full contents of `prompts/synthesizer.md` as its prompt
- Plus appended sections containing:
  - Path to `<SCRATCH_DIR>/brief.md`
  - Path to `<SCRATCH_DIR>/plan.yaml`
  - Paths to all `<SCRATCH_DIR>/findings/<unit-id>.yaml` files
  - The reflect decision payload (`contradictions_to_flag`, `framing_updates`, `coverage_warnings`)
  - Path to `<SCRATCH_DIR>/notes/` directory (for lazy verbatim quotes)
  - Today's date in UTC

The synthesizer reads inputs, writes outline-then-draft in one thread, and outputs `draft.md` with `[u<id>]` markers (no inline URLs).

Append:
```jsonl
{"t":"<NOW>","stage":"synth","event":"draft_written","words":<int>,"sections":<int>,"markers_placed":<int>}
```

## Stage 5 — Cite (subagent)

**Goal:** produce `<SCRATCH_DIR>/report.md`.

### Spawn the citation pass

Read `<SKILL_DIR>/prompts/citation.md`. Spawn a `general-purpose` subagent with:

- The full contents of `prompts/citation.md` as its prompt
- Plus appended sections containing:
  - Path to `<SCRATCH_DIR>/draft.md`
  - Path to `<SCRATCH_DIR>/notes/` directory
  - Path where to write `report.md` (`<SCRATCH_DIR>/report.md`)
  - Today's date in UTC

The citation pass walks every `[u<id>]` marker, grounds it against the notes corpus, replaces with `[^N]` footnotes (or `[x]` if unverifiable), builds a Sources section, and writes `report.md`.

Append:
```jsonl
{"t":"<NOW>","stage":"cite","event":"resolved","markers_total":<n>,"markers_unverified":<n>,"unique_sources":<n>,"grounding":"strong|medium|weak"}
```

## Final user message (JtBD-shaped)

After `report.md` exists, present the user with exactly three lines:

1. The TL;DR sentence — `Read` the first line of `report.md` (the synthesizer's TL;DR is the first line by contract).
2. A pointer to the report file with grounding stats: `→ <SCRATCH_DIR>/report.md (<words>w · <sources> sources · <unverified> [x] · grounding: <strong|medium|weak>)`
3. Concrete continue commands: `→ Continue: "another wave on <suggested topic>" · "redo synth with framing on <suggested>"` — derive the suggestions from the report's `gaps_identified` (across all units' findings) and from the `framing_updates` reflect surfaced. If neither is meaningful, omit this line.

Example:

```
Prompt caching is most cost-effective for prompts >2KB with 5+ reads per
cache window; below that the 25% write premium dominates.

→ .scratch/prompt-caching-strategies/report.md  (1,450w · 12 sources · 2 [x] · grounding: strong)
→ Continue: "another wave on cache poisoning" · "redo synth with framing on cost-per-1k-tokens"
```

Do NOT inline the report. Do NOT summarize it further. The user opens it in their editor.

Append:
```jsonl
{"t":"<NOW>","stage":"final","event":"report_presented"}
```

## File layout

```
<CWD>/.scratch/<slug>/
  brief.md                  # Stage 0 — brief carried verbatim into all stages
  plan.yaml                 # Stage 1 — source of truth for what to research
  notes/<unit-id>.md        # Stage 2 — per-researcher checkpoint log + evidence
  findings/<unit-id>.yaml   # Stage 2 — compressed per-researcher returns
  draft.md                  # Stage 4 — synthesizer output with [u<id>] markers
  report.md                 # Stage 5 — final, span-grounded, footnoted
  trace.jsonl               # All stages — append-only event log
```

## Failure philosophy

The report **always ships** unless one of three hard-halt conditions hits:

1. **Disk write failure** (`.scratch/` unwritable) — surface a clear error, halt.
2. **All researchers in wave 2 returned `no_sources_found`** — surface "research failed: no usable sources for any unit," halt.
3. **Scope produced an empty brief** — re-enter Stage 0 with explicit clarification request.

Everything else degrades gracefully:
- Researcher errors → retry once, then mark errored, continue.
- WebSearch empty → researcher's 3-step reformulation fallback (in its prompt).
- `[x]` rate >20% → citation pass adds a header warning. Ship.
- Wave-2 still has gaps → coverage_warnings → Limitations section. Ship.

## Hard rules (orchestrator)

- Do NOT spawn researchers sequentially in Stage 2. They must go in a single tool message.
- Do NOT skip the plan checkpoint. The user MUST approve before research fans out.
- Do NOT use `AskUserQuestion`. Stage 0 is plain-prose Q&A.
- Do NOT exceed 2 research waves silently. Wave 3 requires explicit user opt-in.
- Do NOT inline the full report in the final message. Path + TL;DR + continue commands only.
- Do NOT proceed past plan checkpoint on ambiguous user responses. Ask for explicit go.
- Do NOT modify the contents of `prompts/*.md` between runs (those are stable subagent contracts).
