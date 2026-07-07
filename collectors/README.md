# collectors

Phase 0 + Phase 1a collectors for The LLM Report. All network I/O goes through
`fetchkit.FetchClient.fetch(source_id)` — URLs always come from
`registry/sources.json`, never from collector code (design.md §1.3).

| collector | source_ids | snapshot schema |
|---|---|---|
| `openrouter_models` | `openrouter-models` | `snapshots/models-api.v2.json` |
| `litellm_prices` | `litellm-model-prices` | `snapshots/pricing-api.v2.json` |
| `status_openai` | `openai-status-summary`, `openai-status-incidents` | `snapshots/statuspage.v2.json` |
| `status_anthropic` | `anthropic-status-history` (Atom feed) | `snapshots/statuspage.v2.json` |
| `aws_bedrock_pricing` | `aws-bedrock-pricelist-api` (size-guarded; evidence archived via truncation rule `aws-bedrock-offers-slim-v1`) | `snapshots/pricing-api.v2.json` |
| `azure_openai_pricing` | `azure-retail-prices-api` (OData `NextPageLink` pagination, same-endpoint-guarded) | `snapshots/pricing-api.v2.json` |
| `aws_health` | `aws-health-status` (UTF-16 JSON; Bedrock-scoped filter) | `snapshots/statuspage.v2.json` |
| `azure_status` | `azure-status-feed` (RSS; Azure-OpenAI-relevance filter) | `snapshots/statuspage.v2.json` |
| `mistral_models` | `mistral-docs-mirror` (mirror-primary models index) + `mistral-models-docs` (liveness/parity fetch ONLY — no snapshot) | `snapshots/docs-html.v2.json` |
| `mistral_status` | `mistral-status-payload` (Checkly/Nuxt devalue payload) | `snapshots/statuspage.v2.json` |
| `docs_changelog` | `openai-changelog`, `anthropic-changelog`, `google-gemini-changelog`, `azure-openai-whats-new`, `xai-changelog` (per-source extraction rules) | `snapshots/docs-html.v2.json` |

Pipeline per source: **fetch** (evidence bytes + `.meta.json` manifest built
and persisted via fetchkit) → **normalize** to the canonical snapshot →
**validate** against the snapshot schema → **diff** against the prior
snapshot per `tables/materiality.json` → **mint candidate events** with the
deterministic identity key via `llmreport_linter.identity.mint_event_id`
(the single sanctioned mint function) → **corroborate** against the store's
open candidates (`llmreport_collectors.corroborate`, design.md §1.4).
Lineage and class come from the registry record and ride along in the run
report and exceptions items.

## Corroboration hardening (design.md §1.4)

Before anything is written, every candidate is dispatched against the open
candidates already in the store (72h window, anchored to the open
candidate's `observed_at`):

- **Same identity key** → attach instead of mint. A **new source of a
  different independence class AND lineage** (registry pins, evaluated by
  `llmreport_linter.independence`) appends a `corroboration` annotation —
  two-source is satisfied automatically and a ready-to-append confirm-verdict
  draft lands in the run report for the verifier session (the collector never
  writes `verdicts/**` — separation of duties). Mirror-lineage sources
  (OpenRouter / LiteLLM / docs pages all share provider-docs lineage) append
  `mirror-corroborated`; the candidate stays unconfirmed.
- **Equal-and-opposite reversal** within 48h (docs/pricing) / 24h (status)
  appends a `rollback` annotation to the original — no second event, the
  pair is surfaced once. Hysteresis: once rolled back, every further
  oscillation inside the window appends `flap` and never counts toward
  confirmation. Reversals outside the damping window are ordinary events.
  `model.released` ↔ `model.deprecated` pair up as reversals of each other.
- **Conflicting new value** on the same partial key (provider, model, type,
  field path) appends a `discrepancy` annotation and opens a `value-conflict`
  exceptions-queue item — the store linter blocks every publication while
  the hold is open. A delta chaining from the candidate's new value is an
  ordinary sequential change; one reaching the same new value from a stale
  baseline corroborates the end state.
- **Rule-(c) disappearance carve-out**: `model.deprecated` from list absence
  (`data.source_kind = "api-absence"`, registry `entitlement_caveat`) is only
  corroborated-to-confirm by a positive-statement class (provider-docs /
  own-probe); absence corroborating absence stays `mirror-corroborated`.

Minted events get an immutable identity-key sidecar
(`identity-keys/<event_id>.json`) so the linter can verify hash8 and the
engine can detect conflicting values on later ticks. Event files stay
immutable — every attach is an append-only annotation on the open candidate.

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
  rewritten; a corroborating observation attaches as an append-only
  annotation on the open candidate (same-source re-observations are pure
  idempotence and recorded in the run report only).
- **Corroboration pins** (deterministic resolutions of §1.4 edges): the
  attach/damping windows compare `observed_at` with strict `<` (exactly 72h
  later mints fresh — matches the linter's E-DUP window); with several open
  candidates the latest one wins; a rolled-back candidate never regains
  corroboration momentum inside its window (`flap`, hysteresis); two-source
  auto-confirmation is surfaced as a verdict DRAFT in the run report — the
  verifier identity appends the actual verdict file (dual-agent rule).

## Phase 1a pins (documented interpretations)

- **docs-HTML extraction rules are versioned code**
  (`llmreport_collectors.docs_extract`, rule ids pinned in the registry
  records). Extraction is structure-hash based, never brittle selectors
  alone: content-root fallback chains (rule marker → `<article>` → `<main>` →
  `<body>`, ALL matching regions captured), sections keyed by heading slugs
  (or date-marker lines for the heading-less OpenAI changelog), values carry
  an NFC-normalized visible-text hash, and a page that yields no sections
  degrades to ONE `page[text-hash]` item so change detection never goes
  blind. Markup/styling churn never surfaces (materiality ignore: cosmetic).
- **Changelog deltas are exceptions, not events**: no extraction rule for the
  four changelog pages declares a target event type, so every section delta
  routes to `diff.unclassified` (materiality by-extraction-rule fall-through)
  for human classification. Only the model-list rules
  (`mistral-models-index-v1`, `xai-changelog-v1`) declare types:
  models[] added → `model.released`, removed → `model.deprecated` with
  `data.source_kind = "docs"` (a provider-docs stance, not the api-absence
  carve-out); modified model sections stay unclassified.
- **xAI publish gate [V-Q3 cond. 5]**: events minted from a source whose
  registry `entitlement_caveat` declares publishing BLOCKED are minted
  normally (facts are facts) and immediately marked with an append-only
  `note` annotation carrying the caveat (the change-event schema is
  additionalProperties:false, so the mark cannot live on the event file);
  the run report lists them under `events_publish_blocked` and the publisher
  MUST consult the annotation before any surface routing.
- **Pagination** (Azure Retail Prices): `NextPageLink` continuations are the
  ONLY sanctioned deviation from the registered URL and must stay on the
  registered scheme+host+path (fetchkit `PaginationViolationError` pre-I/O
  otherwise); pages merge into ONE snapshot — an over-long chain (> 40 pages)
  fails the source rather than writing a partial snapshot that would diff as
  a mass removal; page fetches skip the conditional-GET validator cache both
  ways; every page's bytes+manifest are archived (`<ts>.p<n>.bin`), the
  change-event evidence entry cites page 1.
- **Size guard + slim evidence** (AWS Price List, ~15 MB live): the fetch
  carries `max_body_bytes` (128 MB — `BodyTooLargeError`, never retried) and
  the archived evidence is the deterministic `aws-bedrock-offers-slim-v1`
  truncation (token-inference products/terms only, compact sorted JSON);
  `sha256_full` of the raw body is in the manifest per design.md §1.5.
- **Pricing vocabularies are rule-pinned skip-lists, never guesses**: Bedrock
  `inferenceType`s that don't map into the price-structure dimension enum
  (flex tiers, image/audio/video token counts, cache+priority combos) are
  skipped; Azure meters without an unambiguous direction token (e.g. the
  `opt` abbreviation) are skipped; Azure `model_ref` = meter base tokens +
  deployment scope (`-global`/`-datazone`/`-regional`), Bedrock `model_ref` =
  `<provider-slug>/<model-slug>` from Price-List display names — both resolve
  to canonical ids via `registry/model-aliases.json` (unmapped → the
  alias-unmapped exceptions queue, alias maintenance rule 2).
- **Status feeds with only-current windows** (AWS health `currentevents`,
  Checkly unresolved-incidents): incident disappearance is a window artifact
  (dropped, same as the statuspage pin), so `outage.resolved` mints only
  while a resolved/closed state is still listed. AWS status codes map
  `{'0': resolved, '1': open}` (unknown codes pass through prefixed, never
  into the resolved set); Azure RSS maps `Mitigated`→`resolved` (Azure's
  customer-impact-over marker) under rule `azure-status-rss-v1`; both feeds
  are platform-wide and filter to Bedrock / Azure-OpenAI surface area by
  documented keyword lists.
- **Mistral mirror-primary**: content extraction runs ONLY against the
  Apache-2.0 GitHub mirror's `src/schema/models/models/index.ts` (the repo
  restructured away the models-overview markdown; the raw-file conditional
  GET mirrors the litellm owner-directed override). `docs.mistral.ai` is
  fetched as a liveness/parity check only: the run report records how many
  mirror model ids appear on the live page (`parity.ok` at ≥ 0.5), no
  snapshot, no events.

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
