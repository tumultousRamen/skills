# Consult

## Why

Agent responses to long-running or analysis-shaped tasks default to chronology: context, method, findings, and — eventually — the answer. That's the discovery order, not the reading order. When you return to a finished task as the decision-maker, you want the verdict first and the option to drill into the support, or skip it entirely.

This skill ports Barbara Minto's Pyramid Principle (the McKinsey communication standard) into an output mode: **think bottom-up, present top-down**.

## What it does

Once invoked, every final response for the rest of the session is structured as a pyramid:

```
Governing thought (the answer, sentence one)
        ↓
2–4 MECE supporting arguments, each an action-title assertion
        ↓
Evidence under each argument (paths, data, repro output)
        ↓
Recommendation → next steps → risks, one confidence flag
```

Three design choices keep it usable rather than ceremonial:

- **Scales to stakes.** Trivial questions get one sentence + one line of why; only heavy tasks get the full pyramid. No fixed template — ordering rules are fixed, the visual skeleton adapts.
- **Final answers only.** Interim progress notes during long tasks stay short and plain; the pyramid lands in the end-of-turn message.
- **Committed voice, one caveat.** Takes a position without hedging, then states confidence and what evidence would change the answer — exactly once.

See [SKILL.md](SKILL.md) for the rules and [EXAMPLES.md](EXAMPLES.md) for the structure rendered at three scales.

## Off switch

Say "drop consult mode" (or any clear stop) — persistence and exit are stated in the skill itself.
