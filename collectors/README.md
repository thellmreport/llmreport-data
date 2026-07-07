# collectors

Phase 0 collectors for The LLM Report. All network I/O goes through
`fetchkit.FetchClient.fetch(source_id)` — URLs always come from
`registry/sources.json`, never from collector code (design.md §1.3).

| collector | source_ids | snapshot schema |
|---|---|---|
| `openrouter_models` | `openrouter-models` | `snapshots/models-api.v2.json` |
| `litellm_prices` | `litellm-model-prices` | `snapshots/pricing-api.v2.json` |
| `status_openai` | `openai-status-summary`, `openai-status-incidents` | `snapshots/statuspage.v2.json` |
| `status_anthropic` | `anthropic-status-summary`, `anthropic-status-incidents` | `snapshots/statuspage.v2.json` |

Pipeline per source: **fetch** (evidence bytes + `.meta.json` manifest built
and persisted via fetchkit) → **normalize** to the canonical snapshot →
**validate** against the snapshot schema → **diff** against the prior
snapshot per `tables/materiality.json` → **mint candidate events** with the
deterministic identity key via `llmreport_linter.identity.mint_event_id`
(the single sanctioned mint function). Lineage and class come from the
registry record and ride along in the run report and exceptions items.

The shared runner (`llmreport_collectors.runner`) isolates every source and
every collector: a revocation, backoff exhaustion, robots refusal, parse or
validation failure lands in the run report (with fetchkit's alert payload)
and never blocks the other sources.

Unclassified deltas (`diff.unclassified`, per the materiality table's
unlisted-field-path rule) and aggregator model ids missing from
`registry/model-aliases.json` go to `exceptions/<collector>/<run>.json` —
never auto-published.

## Phase 0 pins (documented interpretations)

- **Identity-key values are canonical**: `model.released`/`model.deprecated`
  keys carry the canonical model id (not the provider-native mirror id), so
  the same change observed via different sources mints the same event id.
- **`outage.resolved` key path** is `incidents[id=<incident_id>].status`
  (parallel to the `prices[direction=…].value` fixture convention) so two
  incidents resolving the same day cannot collide.
- **Statuspage window artifacts**: `incidents[].id` *removals* (leaving the
  unresolved window of `summary.json` / aging out of the recent window of
  `incidents.json`) and `incidents[].updated_at` churn are dropped, not
  material; resolution is captured by the `incidents[].status` rule.
- **First run seeds the baseline**: no prior snapshot → no deltas, no events.
- **Immutable events**: an event id that already exists on disk is never
  rewritten; the corroborating observation is recorded in the run report
  (evidence attach is the verifier's append-only job, design.md §1.4).

## Run

This package is part of the repo-root `llmreport-tools` project (one venv,
one `uv sync`). From the repo root:

```
# venv on local disk first (SMB): $env:UV_PROJECT_ENVIRONMENT='C:\...\llmreport-venv'
uv sync
uv run python -m llmreport_collectors --out var/smoke-2026-07-07
# validate the produced store with the real linter:
uv run python -m llmreport_linter --store var/smoke-2026-07-07 --schemas schemas --registry registry/sources.json
```

## Tests

No live network — a route-table fake transport with recorded fixture
responses (`tests/fixtures/`). From the repo root: `uv run pytest collectors/tests`.
