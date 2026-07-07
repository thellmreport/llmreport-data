# fetchkit

Shared fetch library for The LLM Report collectors. Every collector network request
goes through `fetchkit.FetchClient.fetch(source_id)` — the URL always comes from
`registry/sources.json`, never from the caller.

Enforced in one place (design.md):

- **§1.3 allowlist + etiquette** — only registered `source_id`s; hard refusal of
  excluded hosts; single identified User-Agent (`TheLLMReportBot/1.0
  (+https://thellmreport.com/bot)`, never rotated); conditional GETs
  (ETag / If-Modified-Since); exponential backoff with jitter; per-host
  crawl-delay from registry `conditions.crawl_delay_s`; cached robots.txt check
  with TTL from registry `robots_recheck`; never circumvent a bot wall.
- **§1.5 redaction** — credentials in headers only, never query strings (requests
  whose URL contains key/token/sig-like params or credential patterns are refused
  before any I/O); request headers are never archived; response headers are
  persisted from an allowlist only (`content-type`, `etag`, `last-modified`,
  `date`, `cache-control`, plus HTTP status); archived URLs are canonicalized with
  query credentials stripped.
- **§1.6 alert-and-failover** — 403/429/bot-challenge raises `SourceRevokedError`
  (a revocation signal carrying the registry `failover` source_id); other failures
  raise `SourceFailedError` with a `source.failed` alert payload after a bounded
  backoff schedule. Never silent retry beyond backoff.

Also writes the request-level audit log (JSONL: host, timestamp, status, UA,
conditional-GET result) required by V-Q3 cond. 7, and evidence outputs
(raw bytes + `sha256_full`/`sha256_stored` + truncation rule id + `.meta.json`
manifest) to caller-supplied paths.

## Usage

```python
from fetchkit import FetchClient, Registry, TruncationRule

registry = Registry.load("registry/sources.json")
client = FetchClient(registry, cache_dir=".cache/conditional",
                     audit_log_path="ledger/audit/requests.jsonl")

result = client.fetch(
    "openai-status-summary",
    evidence_path="evidence/openai-status-summary/2026-07-06T1700Z.json",
)
```

## Tests

No live network — a fake transport is injected. From this directory:

```
uv run pytest
```

(On this workstation set `UV_PROJECT_ENVIRONMENT` to a local-disk path first —
the repo lives on a slow SMB mount.)
