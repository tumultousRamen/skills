# Consult mode — examples at each scale

## Trivial: "Where is the retry config read?"

> Retry config is read in [client.py:214](src/sdk/temporal/client.py:214), inside `_build_retry_policy` — it's the only call site; everything else receives the built policy object.

Answer first, one line of grounding, done. No pillars, no recommendation block.

## Moderate: "Why did the nightly sync job fail?"

> The sync failed because the watermark query returned zero rows — the upstream writer stopped bumping `last_updated_at` after Tuesday's deploy, so the job correctly saw "nothing to sync" and the real failure is upstream.
>
> Three things establish this:
> - **The job itself is healthy.** It ran to completion in 41s with exit 0; the "failure" is the empty-result alert, not a crash.
> - **The watermark went stale at the deploy boundary.** Last bumped `last_updated_at` is 2026-06-09 14:02 UTC, eleven minutes before the deploy that shipped the raw-Motor `update_one` change.
> - **That change bypasses the Beanie hook.** The new write path uses `get_motor_collection().update_one(...)` with no `$currentDate` bump, so every status flip since Tuesday is invisible to the sync.
>
> **Recommendation:** revert the Motor write to include `"$currentDate": {"last_updated_at": True}` and backfill watermarks for docs touched since the deploy. High confidence — would only revisit if the backfill query finds bumped docs the sync still missed.

Answer, then reasons ordered cause→effect, evidence inline, committed recommendation with a single confidence flag.

## Heavy: end of a long-running audit task

> **Ship the migration — it's safe, and the two failures you saw in staging are pre-existing flakes, not regressions.**
>
> ### The schema change is backward-compatible in both directions
> All 14 readers tolerate the new optional field (verified by grep + the contract tests in `tests/contracts/`); old writers omitting it hit the model default. Rollback needs no data repair.
>
> ### The staging failures predate the migration branch
> Both failing tests (`test_bulk_export`, `test_replay_ordering`) fail identically on `develop` at the merge-base commit — 6 of the last 20 nightly runs, always on the same two. They are timing flakes, tracked under FAI-7712.
>
> ### Load behavior is unchanged
> p95 write latency in the staging soak (4h, production-shaped traffic) moved from 38ms to 39ms; index size grew 2.1%, inside the capacity plan.
>
> ---
> **Recommendation:** merge and deploy in tomorrow's window; don't wait on the flake fix.
> **Next steps:** (1) merge the PR, (2) run the backfill script post-deploy, (3) link FAI-7712 in the deploy notes so the flakes aren't misattributed.
> **Risk:** if the backfill is skipped, queries filtering on the new field silently miss old rows — the backfill is part of the ship, not a follow-up.
>
> High confidence; would revisit only if the merge-base flake repro fails to reproduce, which would reopen the regression question.

Governing thought as the title-line, action-title sections (each heading is itself a claim — reading only the headings reconstructs the argument), evidence under each, importance-ordered, advisor close.
