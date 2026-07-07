# Phase 0 status — llmreport-data

Integration review date: 2026-07-07. Overall verdict: **GREEN** (with documented
open items, all blocked on repo creation / credentials, none on code).

## Component status

| Component | Location | Status | Verification |
|---|---|---|---|
| Event-store schemas (23) | `schemas/`, `schemas/data/`, `schemas/snapshots/` | GREEN | `check-jsonschema --check-metaschema`: ok (23 + registry schema) |
| Materiality / severity tables | `tables/materiality.json`, `tables/severity.json` | GREEN | consumed by collectors diff engine; tests green |
| Schema fixtures (48) | `fixtures/{events,verdicts,publications,annotations,snapshots,identity-key}/` | GREEN | 25/25 valid pass, 23/23 invalid fail on intended violation (pytest fixture-schema tests) |
| Source registry (53 records) | `registry/sources.json` + `registry/schema/sources.schema.json` | GREEN | `check-jsonschema`: ok; linter registry cross-check green |
| Model aliases | `registry/model-aliases.json` | GREEN | consumed by collectors alias resolution; tests green |
| fetchkit (fetch library) | `lib/fetchkit/` | GREEN | 43 tests pass, no live network |
| Store linter | `tools/linter/llmreport_linter/` | GREEN | GREEN vs repo root and vs `fixtures/store` (17 files, 5 events, all §1.4 paths) |
| Guards | `tools/guards/redaction_gate.py`, `tools/guards/pii_guard.py` | GREEN | both GREEN vs repo root; dirty-fixture tests pass |
| Collectors (4) | `collectors/src/llmreport_collectors/` | GREEN | 14 tests pass; live smoke run 2026-07-07 (`var/`, gitignored): 2 runs, baseline seed + clean re-diff, litellm 304 |
| CI workflows | `.github/workflows/{ci,collect,robots-recheck,sentinel}.yml` | GREEN (ci active; other three gated TEMPLATEs) | paths cross-checked against the tree this review |
| Store mini-fixture | `fixtures/store/` | GREEN | linter GREEN; derived statuses assert every §1.4 outcome |

## Test tallies (re-run in full during this review)

- `uv sync --frozen` against committed root `uv.lock`: ok
- `check-jsonschema --check-metaschema` (all schemas + registry schema): ok
- `check-jsonschema` registry vs its schema: ok
- Store linter, repo root: GREEN (emits `derived/state.json`)
- Store linter, `fixtures/store`: GREEN (17 files, 5 events)
- Redaction gate: GREEN. PII guard: GREEN.
- pytest (exact CI invocation `pytest tools lib/fetchkit/tests collectors/tests -q`): **167 passed, 0 failed**
  (110 linter/guards/fixture-schema + 43 fetchkit + 14 collectors)

## Cross-consistency checks performed

- All 6 collector `source_id`s (`openrouter-models`, `litellm-model-prices`,
  `openai-status-{summary,incidents}`, `anthropic-status-{summary,incidents}`)
  resolve in `registry/sources.json`.
- Schema `$id`s referenced by `llmreport_linter.schemas` and the collectors'
  SchemaGate resolve offline against the files under `schemas/` (linter +
  full pytest green proves resolution end to end).
- `llmreport_linter.identity.mint_event_id` matches design.md §1.4/§1.2:
  key = (provider, canonical_model_id, event_type, normalized_field_path,
  old_value → new_value), NFC-trimmed strings, normalized numbers,
  `evt_<UTC date>_<sha256[:8]>`; collectors mint exclusively through it.
- `fetchkit.redaction` matches design.md §1.5 exactly: response-header
  allowlist {content-type, etag, last-modified, date, cache-control} + status;
  send-refusal on `key=`/`token=`/`sig=`/credential-name/value patterns and
  URL userinfo; archived URLs canonicalized with credentials stripped;
  request headers never archived.
- CI workflow paths verified against the real tree (one stale path fixed, below).

## Fixes applied during integration review

1. `.github/workflows/ci.yml` — pytest step omitted `collectors/tests`
   (collectors landed after the workflow was written); added.
2. `.github/workflows/collect.yml` — stale TODO referenced the pre-build
   module layout (`tools/collectors`, `python -m collectors.run`); updated to
   the real `collectors/src/llmreport_collectors` /
   `python -m llmreport_collectors --repo-root . --out .`.
3. Deleted stale `lib/fetchkit/uv.lock` (+ stray `.pytest_cache`) — the root
   workspace `uv.lock` is authoritative (flagged for reconciliation by the
   linter-CI builder).

## Consolidated spec deviations / Phase 0 pins

Schemas (details in the schema `$comment`s):
- `$id`s use `.../schemas/<name>/v2.json` (slash) vs the spec example's dot
  form; disk filenames keep the dot form.
- Tables emitted to `tables/` (spec text says `schemas/materiality.json` etc.).
- `capability.changed` data shape, annotation shape, publication `surface`
  enum (`tracker|changelog|weekly-email|x|bluesky|pro-alert`) pinned — spec
  leaves them open.
- Nullability pin: `|null`-marked §1.2.2 fields are nullable-but-required.
- Identity-key serialization pinned: compact sorted-key UTF-8 JSON → sha256 →
  hash8 (golden-tested; mirrored in `schemas/identity-key.v2.json`).
- Rule-(c) disappearance carve-out carried by `source_kind: "api-absence"`;
  enforcement is verifier/linter-side per §1.4c.
- `models-api` snapshot `created` accepts integer|string|null (OpenAI epoch vs
  Anthropic RFC3339).

Registry:
- `attribution` enum extended with `apache-2.0` (Mistral mirror license).
- OpenAI policy pages `wayback_only=true` (openai.com is 403-WAF-excluded;
  V-Q3 cond. 1 forbids circumvention).
- `litellm-model-prices` URL is the raw.githubusercontent.com JSON (owner-
  directed Phase 0 override of the sweep's blob-URL pin; revisit at GitHub
  host-set clearance — sweep open item 4).
- `anthropic-status-incidents` added beyond the design matrix (mirrors
  openai-status-incidents; needed by the status collector; registry 0.1.1).
- 3 OpenAI regional ToU URLs + MS Learn TOU URL resolved from known paths;
  verify at sweep import.
- Bedrock ListFoundationModels pinned to the concrete us-east-1 control-plane
  endpoint. Mistral Checkly status pinned to `status.mistral.ai/_payload.json`.

fetchkit:
- Added `UnclearedRedirectError` (registry `global-uncleared-redirect`
  sentinel) and `AuthPolicyViolationError` (`never_authenticate`).
- Bot-challenge 503 = revocation; plain 503 = bounded backoff; 404/410 fail
  immediately. Robots unreachable = conservative disallow; 404 = allow.
- "3 consecutive failures" enforced within one fetch(); cross-cycle counting
  is collector-level.
- Audit lines carry 2 additive fields (source_id, purpose) beyond the spec's 5.

Linter / CI:
- Status pins: reject → `retracted`; precedence retracted > corrected >
  confirmed > unconfirmed; publication filename timestamp = `published_at`
  with `:` → `-`.
- hash8 not recomputable per stored event (identity key not persisted;
  schemas are additionalProperties:false) — minting enforced structurally +
  by golden test; collectors MUST mint via `llmreport_linter.identity`.
- `fetch-depth: 0` in the immutability/path-scope job only (documented
  exception to §1.1 shallow-clone mandate; diff attribution needs history).
- Actions pinned by exact version tag + `uv==0.7.13` + lockfile; full
  SHA-pinning deferred to repo creation.
- One root pyproject/uv workspace for all Python tooling (one venv, one lock).

Collectors:
- Phase 0 diff pins (documented in `collectors/README.md`): statuspage
  incident-id removals / `updated_at` churn = window artifacts, not material;
  price rows added/removed → `diff.unclassified` per model; `pct_change` 0.0
  on zero baseline; `producer.code_sha` from `LLMREPORT_CODE_SHA` env or
  `"uncommitted"` (git forbidden in the build session).

## Structural findings (not fixed — need owner / next phase)

1. **status.claude.com robots-disallowed** (live finding): `Disallow: /api/`
   blocks both registered Anthropic status endpoints; fetchkit correctly
   refuses pre-I/O. The design-pinned Anthropic status source has no
   compliant fetch path today → exceptions-queue / compliance follow-up at
   repo creation (alternatives: page-scrape endpoint stance check, RSS, or
   own-probe).
2. **ToU sweep not yet imported**: `compliance/tou-sweep-2026-07/` must be
   copied from `docs/compliance/tou-sweep-2026-07/` at repo creation
   (design.md §1.3); §10.1 Phase 0 verification requires it archived+current.
3. **Registry review items**: litellm raw-URL override and the added
   anthropic-status-incidents record are annotated for the next registry
   review; the spec's source matrix should be back-annotated or the records
   confirmed.
4. **Spec back-port**: the pinned-but-unspecified shapes (capability.changed,
   annotation, publication surface enum, identity-key serialization, status
   fold pins) should be written back into design.md so spec and store can't
   drift.

## Open TODOs blocked on credentials / repo creation

- Create public GitHub repo `llmreport-data` (+ private `llmreport-evidence`);
  push this tree as initial commit.
- Branch protection + merge queue + required checks (ci.yml jobs) per §1.7;
  org-wide secret scanning + push protection (§1.1/§1.5).
- Bot identities + fine-grained PATs (collector-bot: contents:write on
  `ingest/*` only, no workflow scope); signed commits.
- Activate `collect.yml`: remove TODO(activation) guards, set repo var
  `COLLECT_ENABLED=true`.
- `robots-recheck.yml` / `sentinel.yml`: Phase 1 fetchkit robots-recheck +
  sentinels modules, then `SENTINELS_ENABLED=true`.
- Import the ToU sweep archive into `compliance/tou-sweep-2026-07/`.
- SHA-pin all GitHub Actions (currently version-tag-pinned).
- Set `LLMREPORT_CODE_SHA` from real commit SHAs once git history exists.

## Repo-push day — exact next actions

1. `git init` (LF enforced via `.gitattributes` — add one: `* text=auto eol=lf`),
   initial commit of this tree; verify `var/` stays untracked.
2. Create the GitHub repo, push, enable branch protection / merge queue /
   secret scanning + push protection; add required checks from `ci.yml`.
3. Confirm first CI run green (it runs the exact commands under
   "How to run CI locally" in README.md).
4. Import `compliance/tou-sweep-2026-07/`; verify the 4 URL-resolution notes
   in the registry against the sweep files.
5. File the exceptions-queue issues: status.claude.com robots stance;
   litellm URL override; anthropic-status-incidents registry addition.
6. Provision bot identities/PATs; SHA-pin actions; then flip
   `COLLECT_ENABLED` when ready for the first live hourly tick.

---

## Addendum 2026-07-07 — structural finding 1 RESOLVED (pending code change)

Live verification (2026-07-07, main session): `status.claude.com/robots.txt` = `User-agent: *`,
`Disallow: /api/`, `Disallow: /embed/` — the registered `/api/v2/summary.json` and
`/api/v2/incidents.json` endpoints are indeed non-compliant for a robots-honoring bot.
**Compliant replacement verified live:** `https://status.claude.com/history.atom` — valid Atom
feed ("Claude Status - Incident History", 30 entries, status progression labels
Investigating/Identified/Monitoring/Resolved; thinner component detail than the JSON API).
Phase 1 action: replace the two `anthropic-status-*` registry records with one
`anthropic-status-history` record (format: atom, class: statuspage), adapt the status_anthropic
collector + fixtures, and back-annotate design.md §1.3 source matrix. Until then the collector
must stay disabled for Anthropic status (fetchkit robots enforcement would refuse the fetch
anyway - by design).
