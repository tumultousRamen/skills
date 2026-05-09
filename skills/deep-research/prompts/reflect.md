# Reflect — coverage + adversarial + compellingness

This stage runs in the **main orchestrator thread** with extended thinking. It is NOT a subagent. The instructions below are what the orchestrator follows when reaching the reflect stage.

The output is a single decision payload that the orchestrator either passes to the synthesizer (proceed) or feeds back to a second wave of researchers (another_research_round).

## Inputs

Read these into the main thread before reflecting:

- `<SCRATCH_DIR>/brief.md` — verbatim, especially `great_answer`
- `<SCRATCH_DIR>/plan.yaml` — original units (and `landscape_notes`)
- All `<SCRATCH_DIR>/findings/<unit-id>.yaml` files — compressed researcher returns
- All `<SCRATCH_DIR>/notes/<unit-id>.md` `## Checkpoint` blocks — to know which units came back partial / errored / no_sources_found
- The current wave counter (1 or 2)

You do NOT need to read the full notes files for reflect. The compressed `findings/<unit-id>.yaml` is enough — the whole point of the compression is that it's the right level of detail for cross-unit reasoning.

## The three passes

Run these in order, in extended thinking. Treat them as one continuous reasoning pass with three distinct sections in your output.

### Pass 1 — Coverage

Walk the brief's `great_answer` line. For each claim or section it implies, ask:
- Is there at least one finding (across all units) that supports it?
- If yes, with what `confidence`?
- If no, which unit *should* have covered it? Was the unit run, and what was its `status`?

Identify **structural gaps**: parts of the deliverable shape that aren't supported by the current corpus.

### Pass 2 — Adversarial

Examine the **combined corpus** (across all units), not unit-by-unit. Ask:

1. **Source authority.** Are top-cited findings backed by first-party / canonical sources, or are we leaning on blog summaries that derive from a small number of underlying sources? If derivative chains dominate, do we have the underlying source directly? (If not, is it worth pursuing?)

2. **Source concentration.** Hostname / author / ideological-cluster diversity across the *whole* corpus. If one hostname dominates >40% of cited findings, that's a concentration risk worth flagging.

3. **Framing audit.** Has anything in the findings or in `gaps_identified` shifted what `great_answer` *should* be? E.g., the research surfaced that "everyone thinks X but the actual data is Y" — that's a framing update. Or "the right axis of comparison is not A/B/C but X/Y" — that's a framing update. Output goes into `framing_updates`.

4. **Critical-source gap.** Concatenate all `gaps_identified` from all units, dedupe. For each, judge: "if pursued, would this *meaningfully shift* the answer (acceptable → compelling), or would it just add detail?" Only the *meaningful shift* gaps matter.

### Pass 3 — Compellingness threshold

The honest question, with explicit soft tolerance:

> Given everything, is this enough to write a *compelling* answer, accepting that perfect is impossible?

Three possible verdicts:

- **Proceed.** Material is sufficient. Move to synthesis.
- **Proceed with framing update.** Material is sufficient but the original `great_answer` should be reframed (writer will use `framing_updates` to override).
- **Another wave.** A specific, named gap would shift the answer from acceptable to compelling. Spawn one or more new research_units targeting it.

## Output — exactly one of these payloads

The orchestrator emits one of two YAML blocks based on your verdict. Append it to `trace.jsonl` as the reflect event payload.

### Verdict A: Proceed

```yaml
decision: proceed_to_synthesis
wave: <1 or 2>
contradictions_to_flag:
  - claim_a: "<short summary of one position>"
    claim_b: "<short summary of the conflicting position>"
    sources: [<urls or unit ids>]
    note: "<why this is unresolved — usually a real-world disagreement, not a research gap>"
framing_updates:
  - <one-sentence reframing the writer should adopt over the original great_answer>
coverage_warnings: []   # nonempty only when wave 2 still has gaps and we're shipping anyway
```

### Verdict B: Another wave

```yaml
decision: another_research_round
wave: <2 — only valid coming from wave 1>
rationale: |
  <One paragraph: what specifically would shift the answer from acceptable to
  compelling. This is what justifies another ~15× token wave.>
new_units:
  - id: u<next>
    objective: <scoped question>
    output_format: findings-with-spans
    source_guidance: <prose>
    boundaries: <one sentence>
    budget_fetches: <int>
    seed_search_terms: [<list>]
  # ... usually 1-3 new units, never more
framing_updates:
  - <reframings to carry into wave 2>
```

## Termination rules

- **Hard cap: 2 waves.** If wave 2 still leaves gaps, override to `proceed_to_synthesis` with non-empty `coverage_warnings`. The synthesizer will fold these into a "Limitations" section. Failure-as-honest-output, not failure-as-error.
- **Wave 2 with 0 new units → done.** Reflect calling for "another wave" but unable to specify a useful new_unit means the brief is fully fishable; just proceed.
- **Contradictions never trigger more research.** They go in `contradictions_to_flag`. The writer presents them as named tensions ("Source A says X; Source B says Y; this is unresolved in the field"). More research won't resolve real-world disagreements; honest writing handles them better.

## What this pass does NOT do

- It does NOT critique writing quality. (The synthesizer hasn't written anything yet.)
- It does NOT re-grade individual findings' quality. (Researcher protocol enforced quality at fetch time.)
- It does NOT pursue every gap. Only meaningful-shift gaps. Detail-gaps go into `coverage_warnings` if at all.
- It does NOT spawn a critic agent. The adversarial pass IS the critic — folded into the same extended-thinking call.
