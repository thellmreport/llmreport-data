# llmreport-data

Public, typed change-event store for [The LLM Report](https://thellmreport.com)
— the change log of the LLM industry: model releases, price changes,
deprecations, outages. Operated by always-on agents; every event carries
evidence manifests and an append-only verification chain. Humans and agents
alike can audit every claim back to hashed source bytes.

Authoritative spec: `design.md` in the parent project (§1.2 store, §1.4
verification, §1.5 evidence/redaction, §1.7 write discipline). Current build
state: see `STATUS.md`.

## Layout

| Path | What it is |
|---|---|
| `schemas/` | JSON Schema 2020-12 for every record type: change-event envelope + 13 per-type `data/` schemas (plus the shared `price-structure` def), verdicts, publications, annotations, identity-key, 4 `snapshots/` schemas |
| `tables/` | `materiality.json` (what counts as a material delta) and `severity.json` (sev1–3 dispatch) |
| `registry/` | `sources.json` — the fetch allowlist: 54 source records with class/lineage, cadence, robots/attribution conditions, exclusions and compliance sentinels; `model-aliases.json`; the registry's own schema |
| `lib/fetchkit/` | The only code allowed to touch the network. Registry-enforced allowlist, robots gate, credential send-refusal (§1.5), conditional GET, pagination + body-size guards, evidence bytes + manifests, JSONL request audit |
| `collectors/` | 11 no-auth collectors (Phase 0: OpenRouter models, LiteLLM prices, OpenAI + Anthropic status; Phase 1a: AWS Bedrock + Azure pricing, AWS Health + Azure + Mistral status, Mistral models, generic docs changelogs) — normalize → snapshot → materiality diff → deterministic event minting → corroboration engine |
| `tools/linter/` | Store linter: schema validation, id minting rules, identity-key sidecar + independence/corroboration checks, verdict-chain status fold, publish legality, cross-file integrity; emits `derived/state.json` |
| `tools/guards/` | Redaction gate (§1.5) and PII guard — required CI checks |
| `tools/watch/` | Scheduled watch jobs (`llmreport_watch`): weekly robots.txt re-check, registry-driven compliance sentinels, healthchecks.io dead-man heartbeat (wired into the collector runner) |
| `fixtures/` | Valid/invalid fixtures per schema + `fixtures/store/` mini-store exercising every §1.4 verification path |
| `queue/` | Exceptions-queue drop directory (`queue/<emitter>/<run-ts>.jsonl`); CI turns each line into a GitHub issue. Only `README.md` is tracked |
| `.github/workflows/` | `ci.yml` (active); `robots-recheck.yml` + `sentinel.yml` invoke the real `llmreport_watch` modules (gated by `SENTINELS_ENABLED`); `collect.yml` gated until repo + bot credentials exist |
| `derived/` | Linter-computed event state (never hand-edited) |

Events are immutable once merged; verdicts/publications/annotations are
append-only chains. An event file never stores status — the linter derives it
from the verdict chain.

## Run CI locally

Python 3.12 + [uv](https://docs.astral.sh/uv/). If the checkout is on a slow
or network mount, put the venv on local disk first:

```
# PowerShell                                   # bash
$env:UV_PROJECT_ENVIRONMENT="$env:TEMP\llmreport-venv"   export UV_PROJECT_ENVIRONMENT=/tmp/llmreport-venv
```

Then, from the repo root (these are the exact `ci.yml` steps):

```
uv sync --frozen
uv run check-jsonschema --check-metaschema schemas/*.json schemas/data/*.json schemas/snapshots/*.json registry/schema/sources.schema.json
uv run check-jsonschema --schemafile registry/schema/sources.schema.json registry/sources.json
uv run python -m llmreport_linter --store . --schemas schemas --registry registry/sources.json --emit-derived derived/state.json
uv run python tools/guards/redaction_gate.py --root .
uv run python tools/guards/pii_guard.py --root .
uv run pytest tools lib/fetchkit/tests collectors/tests -q
```

One-shot collector smoke run (writes to gitignored `var/`, never the store):

```
uv run python -m llmreport_collectors --repo-root . --out var/smoke
```

## Conventions

LF line endings, UTF-8 without BOM, JSON pretty-printed with 2-space indent.
All network fetches go through fetchkit against `registry/sources.json` —
collector code never contains a URL. No credentials in query strings, ever;
request headers are never archived; response headers persist from the §1.5
allowlist only.
