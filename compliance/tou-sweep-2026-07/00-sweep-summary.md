# ToU Sweep Summary — 2026-07

**Sweep dated 2026-07** (research 2026-07-05/06, independent verification 2026-07-07). This file and all eight host-set clearances MUST be imported verbatim into `llmreport-data/compliance/tou-sweep-2026-07/` at repo creation (Phase 0) and re-verified per the weekly policy-page job thereafter, with a full quarterly re-sweep. All eight verdicts are CONDITIONAL; verifier dissents are appended inside seven of the eight files (anthropic is a concurrence) and are binding.

> **Amendments applied 2026-07-08.** The binding required changes in all seven dissenting files (openai, google, aws, microsoft, mistral, xai, policy-pages) are folded into their bodies; each dissent is preserved verbatim as the audit record under an "Amendments applied 2026-07-08" stamp, and each was independently adversarially re-verified after amendment. All eight files are import-ready (§3 items 1–7 closed; item 8 — standing up the weekly job + quarterly schedule — is a repo-activation task). This amended set is the version imported into `llmreport-data`.

## 1. Verdict table

| Host-set | Final verdict | Basis (one line) | File |
|---|---|---|---|
| openai | CONDITIONAL | developers.openai.com robots.txt permits; browsewrap defense impaired — verifier requires Services Agreement §3.3(f) rewrite + entity-separation condition | [openai.md](./openai.md) |
| anthropic | CONDITIONAL | No website ToU exists; Commercial ToS has no anti-crawl clause; robots.txt allows both pinned docs paths (verifier concurred) | [anthropic.md](./anthropic.md) |
| google | CONDITIONAL | Google ToS permits robots.txt-compliant automation; ai.google.dev is CC BY 4.0; cloud.google.com unlicensed — minimal excerpts only | [google.md](./google.md) |
| aws | CONDITIONAL | docs.aws.amazon.com CC BY-SA 4.0 carve-out overrides Site Terms scraping ban; aws.amazon.com HTML excluded | [aws.md](./aws.md) |
| microsoft | CONDITIONAL | learn.microsoft.com content CC BY 4.0 via azure-ai-docs; Learn TOU has no anti-bot clause; GitHub raw NOT cleared as primary | [microsoft.md](./microsoft.md) |
| mistral | CONDITIONAL | Zero scrape/crawl vocabulary in any ToS; docs robots.txt absent (404); Apache-2.0 GitHub mirror is license-clean primary | [mistral.md](./mistral.md) |
| xai | CONDITIONAL | docs.x.ai robots.txt Allow-all + Content-Signals + llms.txt vs. two facial AUP anti-bot readings; residual risk accepted, stop-on-block | [xai.md](./xai.md) |
| policy-pages | CONDITIONAL | Weekly identified-UA compliance fetches of 8 legal hubs; x.ai deterministic-only and aws.amazon.com Wayback-default per verifier | [policy-pages.md](./policy-pages.md) |

## 2. REGISTRY DECISIONS

### 2.1 docs.aws.amazon.com — CLEARED (conditional); aws.amazon.com — EXCLUDED
The Bedrock changelog HTML source is **docs.aws.amazon.com only**, under the Site Terms CC BY-SA 4.0 carve-out. aws.amazon.com marketing/pricing pages stay under the unmitigated scraping ban — excluded from HTML collection; only low-frequency robots-compliant compliance fetches of `/terms/` and `/aup/` are authorized (dissent B2), defaulting to Wayback per the policy-pages verifier. **Lapse rule:** automated weekly sentinel on the carve-out sentence AND the AWS AUP (dissents B1/B3); if the carve-out disappears, verdict lapses to EXCLUDE and the collector auto-switches to the designed fallback: Bedrock `ListFoundationModels` lifecycle fields + Price List API diffs. No GitHub fallback (awsdocs Bedrock mirrors retired 2023).

### 2.2 Pinned Anthropic changelog URL
`https://platform.claude.com/docs/en/release-notes/overview` — `/docs/en/release-notes/api` is only a 307 alias. Log redirects; alert on host/canonical drift. Never fetch `/api/*` on platform.claude.com; never authenticate.

### 2.3 Policy-page registry seed list (weekly job)
- `https://openai.com/policies/services-agreement/` (business-terms 307s here) + ToU incl. all three regional variants (ROW/EU/US)
- `https://www.anthropic.com/legal` — Commercial ToS (eff. 2025-06-17), Consumer ToS (eff. 2025-10-08), Usage Policy
- `https://aws.amazon.com/terms/` + `https://aws.amazon.com/aup/` (Wayback-default; direct only on counsel sign-off)
- `https://x.ai/legal/*` (Wayback-only; ai-input=no — deterministic pipeline, no LLM ingestion at any stage)
- `https://developers.google.com/terms/site-policies` + `https://policies.google.com/terms` (CC BY 4.0 attribution on quotes)
- learn.microsoft.com Terms of Use (rev. 2025-05-12)
- `https://legal.mistral.ai/terms` (mistral.ai/terms 301s here; monitor the hub itself — new policies can appear without robots change)

### 2.4 Conditions to encode in sources.json / fetch library
**Global:** single UA `TheLLMReportBot/1.0 (+https://thellmreport.com/bot)`, never rotated; conditional GETs (ETag/Last-Modified); exponential backoff; max 1 poll/hour/page; robots.txt re-fetch every cycle (≤24h Anthropic; weekly policy job); any 403/429/bot-challenge = revocation → auto-halt host, escalate, never circumvent; redirect to uncleared host = suspend source + fresh clearance; verbatim archives private, sha256 manifests public; fetched content flagged no-ML-training; manifests capture title + canonical + redirect chain per fetch.
**Per-host:** AWS Crawl-delay ≥5s, auto-halt if any `/bedrock/` path disallowed, weekly carve-out sentinel; xAI Content-Signal flags (docs.x.ai ai-train=no/ai-input=yes; x.ai ai-input=no), pin `https://docs.x.ai/developers/models`; attribution templates — CC BY 4.0 (ai.google.dev, learn.microsoft.com, with modification notices) and CC BY-SA 4.0 (docs.aws.amazon.com: attribute, license-link, ShareAlike or short unmodified quotes; note §6(a) auto-termination); text-only excerpting, no logos/trade dress (AWS, Microsoft, Google branding untouched); Mistral: mirror-primary `github.com/mistralai/platform-docs-public` (Apache-2.0), docs.mistral.ai fetches liveness/parity only, pin `/models/overview`; Microsoft: primary = learn.microsoft.com (raw.githubusercontent.com NOT cleared), skip `/*/opbuildpdf/`, `/api/nextsteps/*`, `/api/attachments/*`; Google: cross-host redirects (docs.cloud.google.com migration) = new-host events; never authenticate on any host (OpenAI, Anthropic, Mistral explicit).

## 3. Open items for Phase 0

**Status 2026-07-08:** items 1–7 (dissent amendments) are APPLIED and re-verified — see the header stamp; each is now folded into its file's body. The strikethrough-marked detail below is retained as the original open-item record. Item 8 remains open (repo-activation task).

1. ~~Apply verifier dissent amendments in openai, google, aws, microsoft, mistral, xai, policy-pages before import; anthropic imports as-is (concurrence).~~ **DONE 2026-07-08.**
2. OpenAI: replace Business Terms analysis with Services Agreement (eff. 2026-01-01) §3.3(f)/§14.1(B); entity-separation + counsel sign-off condition; human-browser re-verification of ToU (currently Wayback-sourced).
3. Counsel sign-off + good-faith provider notice before direct aws.amazon.com and x.ai policy fetching; implement x.ai deterministic-only pipeline or EXCLUDE.
4. Microsoft: separate GitHub host-set clearance (REST API mechanism, not raw polling) before any GitHub-based collection.
5. xAI probe-number publication blocked pending manual Enterprise/API terms review.
6. Google: rule on the "may not copy... our services or software" ToS clause; add condition 8 (cloud.google.com archives never published).
7. Mistral: formation-analysis rewrite (browsewrap, not signup-only); add legal.mistral.ai monitoring condition.
8. Stand up the weekly policy-page job and quarterly re-sweep schedule at repo creation.
