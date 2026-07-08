# Build status — llmreport-data

Supersedes the former `PHASE0-STATUS.md`. Phase 0 is complete and green;
Phase 1a (no-auth collector expansion + corroboration hardening + watch jobs)
is complete and green. All open items are blocked on repo creation / bot
credentials / probe accounts — none on code.

- **Phase 0 integration review:** 2026-07-07 → GREEN
- **Phase 1a integration review:** 2026-07-07 → **GREEN**
- **Phase 1b (in progress):** verification pipeline + redaction-gate queue
  scope landed 2026-07-08 → **GREEN** (318 tests). Remaining: Managed Agents
  deployment; probe harness (blocked on owner probe accounts).

## Phase 1a component status

| Component | Location | Status | Verification |
|---|---|---|---|
| Source registry (54 records, v0.2.0) | `registry/sources.json` + `registry/schema/sources.schema.json` | GREEN | `check-jsonschema` ok; schema gained `format` enum (json/atom/rss/html/text) + `extraction_rule_id`; +2 Wayback sources, Anthropic status swapped to `history.atom` |
| Collectors (11) | `collectors/src/llmreport_collectors/` | GREEN | 4 Phase 0 + 7 Phase 1a; every `source_id` resolves in registry + fetchkit; runner registers all 11 |
| Corroboration engine | `collectors/src/llmreport_collectors/corroborate.py` | GREEN | 72h attach, independence classes, conflict→discrepancy, rollback/flap damping, api-absence carve-out; 22 unit tests |
| Independence module (shared) | `tools/linter/llmreport_linter/independence.py` | GREEN | class + effective-lineage collapse; 8 tests |
| Identity-key sidecars | `collectors/.../store.py`, linter E-KEY | GREEN | immutable `identity-keys/<event_id>.json`, hash8/provider/type verified when present, tolerated when absent |
| Docs-HTML extraction | `collectors/src/llmreport_collectors/docs_extract.py` | GREEN | per-source versioned rules for 5 changelog sources |
| fetchkit pagination + size guards | `lib/fetchkit/src/fetchkit/{client,exceptions}.py` | GREEN | `page_url` OData pagination (`PaginationViolationError` pre-I/O), `max_body_bytes` (`BodyTooLargeError`, never retried); 8 tests |
| Watch jobs (`llmreport_watch`) | `tools/watch/llmreport_watch/` | GREEN | robots_recheck, sentinel, heartbeat; 27 tests; entrypoints `python -m llmreport_watch.{robots_recheck,sentinel}` runnable |
| Heartbeat wiring | `collectors/.../runner.py::run_all` | GREEN | `HC_PING_URL` env-only, fail-ping on any collector failure; 2 runner tests |
| Schema: annotation kinds | `schemas/annotation.v2.json` | GREEN | `corroboration` kind added; metaschema ok |
| Workflows | `.github/workflows/{robots-recheck,sentinel,collect}.yml` | GREEN | robots-recheck/sentinel invoke real modules (gated `SENTINELS_ENABLED`); collect adds `HC_PING_URL` secret |

## Phase 1b component status (2026-07-08)

| Component | Location | Status | Verification |
|---|---|---|---|
| Verifier pipeline (`llmreport_verifier`) | `tools/verifier/llmreport_verifier/` | GREEN | Deterministic rules (a) two-source + (c) provider-official (design.md 1.4.3); drafts are hints only — everything re-derived from store annotations + registry pins; conservative skips (flap/rollback, open discrepancy, idempotence, reject stands, unauditable manifests); 26 pipeline + 5 store-I/O + 5 CLI tests; fixture-store integration run appends nothing and keeps the real linter GREEN |
| verify workflow | `.github/workflows/verify.yml` | TEMPLATE (gated `VERIFY_ENABLED`) | Mirrors collect.yml; cron 37 * * * * (post-collect); activation flow commits ONLY `verdicts/**` as verifier-bot via the merge queue — path scope makes any other write fail the required linter check |
| Redaction gate queue scope | `tools/guards/redaction_gate.py` | GREEN | `queue/` added to default scan dirs; `*.jsonl` scanned line-by-line with line-numbered violations (finding 2 below resolved); 4 new tests + clean/dirty JSONL fixtures |

Dual-agent separation preserved end-to-end: collectors surface drafts and
never write `verdicts/**` (Phase 1a pin); the verifier writes ONLY
`verdicts/**` (`VerifierStore` has no other write path) and never edits a
candidate. Rule (b) direct-probe is structurally accommodated, not
implemented — blocked on probe accounts.

## Test tallies (re-run in full during this review, 2026-07-07)

- `uv sync --frozen`: ok (36 packages)
- `check-jsonschema --check-metaschema` (all schemas + registry schema): ok
- `check-jsonschema` registry vs its schema: ok
- Store linter, repo root: GREEN (1 file, 0 events; emits `derived/state.json`)
- Store linter, `fixtures/store`: GREEN (17 files, 5 events)
- Redaction gate: GREEN. PII guard: GREEN.
- pytest (exact CI invocation `pytest tools lib/fetchkit/tests collectors/tests -q`):
  **278 passed, 0 failed** (was 167 at Phase 0; +111 across Phase 1a and the
  parallel corroboration/watch work).

Phase 1b re-run (2026-07-08, full CI battery): `uv sync --frozen` ok;
check-jsonschema (metaschema + registry) ok; store linter GREEN; redaction
gate GREEN (now incl. queue scope); PII guard GREEN; pytest **318 passed,
0 failed** (+36 verifier: 26 pipeline / 5 store-I/O / 5 CLI; +4
redaction-gate JSONL).

## Cross-consistency checks performed (Phase 1a review)

- All 11 collectors' `source_id`s (incl. parity `parity_of`) resolve in
  `registry/sources.json` and via `fetchkit.Registry.get`.
- No collector fetches an excluded host: `excluded_hosts =
  {aws.amazon.com, azure.microsoft.com, openai.com, status.x.ai, x.ai}`; every
  collector source sits on a distinct non-excluded host
  (`health.aws.amazon.com`, `docs.x.ai`, `raw.githubusercontent.com`, etc.).
- Workflows reference real installed modules: `llmreport_watch.robots_recheck`,
  `llmreport_watch.sentinel`, `llmreport_collectors`, `llmreport_linter` — all
  `--help`-runnable.
- `robots_recheck` host set excludes `source.excluded`, `excluded_hosts`
  members, and `wayback_only` sources (x.ai never contacted even for
  robots.txt; its Content-Signals honored via the docs.x.ai pin).

## Hard-rule audit (by reading the new code)

- **No LLM calls anywhere**: no `openai`/`anthropic`/`cohere`/`mistralai`/
  `google.generativeai` client imports or `*.messages.create` /
  `*.chat.completions` calls in `collectors/` or `tools/`.
- **fetchkit-only network in collectors**: no `requests`/`urllib`/`httpx`/
  `socket` in `collectors/src` (the only `requests` hit is the `requests.jsonl`
  audit-log filename). Watch `robots_recheck`/`sentinel` fetch through fetchkit
  (`FetchClient` / fetchkit `Transport`); `urllib` there is only
  `robotparser` (parse) and `urllib.parse` (urljoin/urlsplit).
- **Heartbeat is the one deliberate fetchkit bypass** (documented): `urllib`
  POST to the secret ping URL, resolved from `HC_PING_URL` env only, never
  hardcoded, never logged, never raises.
- **xAI publish-block honored**: `xai-changelog` carries a registry
  `entitlement_caveat` containing "BLOCKED"; `events.publish_block_note`
  gates every minted event → append-only `note` annotation "PUBLISH BLOCKED
  per registry entitlement_caveat: …" + `events_publish_blocked` in the run
  report. Status enum never flipped by the collector.
- **No credentials or ping URLs hardcoded**: `grep -rE
  'hcw_|sk-ant|github_pat|cfut_'` over the tree → the only hit is the
  `github_pat_` *detection regex* in `fetchkit/redaction.py`; `hc-ping.com`
  appears only in `tools/watch/tests/`. Clean.

## Phase 1a deviations / pins (authoritative detail in `collectors/README.md`)

- Anthropic status swapped to `status.claude.com/history.atom` (robots-
  compliant); JSON `/api/v2/*` endpoints removed. Same canonical statuspage
  snapshot/sidecar shape → diff/events unchanged (thinner detail).
- Mistral models mirror re-pinned to raw `…/schema/models/models/index.ts` on
  raw.githubusercontent.com (owner-directed raw-file override, litellm
  precedent; revisit at GitHub host-set clearance).
- Corroboration attach is realized as append-only annotations (events
  immutable); auto-confirmation surfaced as a verdict DRAFT + `two_source_
  satisfied` derived state — the collector never writes `verdicts/**`
  (dual-agent separation).
- Identity keys now persisted as immutable `identity-keys/` sidecars (reverses
  the Phase 0 "hash8 not recomputable" pin; linter verifies when present).
- Changelog deltas mint no events (no rule-declared type → `diff.unclassified`);
  only model-list rules (mistral index, xai models) mint
  `model.released`/`model.deprecated` with `source_kind:"docs"`.
- Window-bounded resolution: AWS/Checkly resolved-item disappearance is a
  window artifact; `outage.resolved` mints only while the resolved state is
  still listed.
- Azure meter + Bedrock inferenceType vocabularies are deterministic
  skip-lists (ambiguous tokens skipped, never guessed).

## Open items — blocked on repo / credentials / accounts (not code)

Carried from Phase 0 (still open):
- Create GitHub repos, branch protection + merge queue + required checks,
  secret scanning + push protection.
- Bot identities + fine-grained PATs; signed commits; SHA-pin all Actions.
- Import the ToU sweep archive into `compliance/tou-sweep-2026-07/`.
- Set `LLMREPORT_CODE_SHA` from real commit SHAs once history exists.

New in Phase 1a:
- `robots-state/`, `sentinel-state/`, and seeded sentinel references cannot be
  pushed by the workflows until bot PATs exist — state is artifact-uploaded and
  the queue issue instructs the commit; weekly alerts repeat until accepted.
- `HC_PING_URL` secret must be provisioned before `collect.yml` heartbeats.
- Flip `SENTINELS_ENABLED=true` once bot PATs land, then `COLLECT_ENABLED`.

## Structural findings (this review) — filed, not code-blocking

1. **Queue runtime files not gitignored** — RESOLVED (`.gitignore` carries
   `queue/*/`, parallel to `var/`).
2. **Redaction gate does not scan `queue/*.jsonl`** — RESOLVED 2026-07-08:
   `queue/` joined the default scan dirs and `*.jsonl` files are scanned
   line-by-line (violations carry line numbers); clean/dirty fixtures + tests
   added (builder deviation 7 closed).
3. **design.md §1.3 source-matrix back-annotation** for the Anthropic atom swap,
   the Mistral raw-file override, and the Phase 1a sources remains a follow-up
   (git/narrative is the main session's responsibility).

## Phase 1b — what remains

- **Managed Agents deployment**: promote the collector/watch/verifier runners
  to the always-on agent surface (design §5); wire the exceptions-queue →
  GitHub-issue path end-to-end once repos exist.
- **Verification pipeline**: DONE 2026-07-08 — `tools/verifier/`
  (`llmreport_verifier`), the verifier identity consuming run-report verdict
  DRAFTs as hints and sweeping the store; writes ONLY `verdicts/**`
  (dual-agent separation preserved). See "Phase 1b component status" above.
- **Probe harness**: own-probe collectors (xAI availability probe, others) —
  **blocked on probe accounts / API credentials**; publishing xAI numbers stays
  BLOCKED until the manual API-terms review at signup (registry
  `entitlement_caveat`, V-Q3 cond. 5).
