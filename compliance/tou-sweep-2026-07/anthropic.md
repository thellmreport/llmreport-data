# ToU Clearance: Anthropic — platform.claude.com

- **Sweep:** tou-sweep-2026-07 (design-phase legal deliverable, V-Q3 cond. 9)
- **Host-set:** `platform.claude.com` (docs models overview; platform/API release notes)
- **Fetch date for all sources below:** 2026-07-07 (all directly sourced; no bot wall encountered — plain HTTPS GETs returned 200 with full HTML via Cloudflare, no challenge)
- **Planned collector behavior:** hourly conditional GETs, UA `TheLLMReportBot/1.0 (+https://thellmreport.com/bot)`, robots.txt honored, backoff, no bot-wall circumvention
- **Verdict:** **CONDITIONAL** (see §7)

---

## 1. Target URLs for collectors

| Purpose | URL | Status (2026-07-07) |
|---|---|---|
| Models overview (registry) | `https://platform.claude.com/docs/en/about-claude/models/overview` | HTTP 200, live; current models table (Fable 5 / Opus 4.8 / Sonnet 5 / Haiku 4.5) with IDs, pricing, context windows |
| Platform/API release notes (changelog) | `https://platform.claude.com/docs/en/release-notes/overview` | HTTP 200, live; entries dated July 1 2026, June 30 2026 |

## 2. Registry task: release-notes URL pin [design.md §1.3]

Verified 2026-07-07:

- `https://platform.claude.com/docs/en/release-notes/api` **exists but is NOT the stable URL** — it returns **HTTP 307** with `location: /docs/en/release-notes/overview`.
- The served page's canonical tag is `<link rel="canonical" href="https://platform.claude.com/docs/en/release-notes/overview"/>`.
- Legacy hosts both land on the same page (200 after redirect chain): `https://docs.anthropic.com/en/release-notes/api` and `https://docs.claude.com/en/release-notes/api` → `https://platform.claude.com/docs/en/release-notes/overview`.
- Page identity: title "Claude Platform"; subtitle "Updates to the Claude Platform, including the Claude API, client SDKs, and the Claude Console."

**PIN:** register `https://platform.claude.com/docs/en/release-notes/overview` as the Anthropic changelog source. Treat `/docs/en/release-notes/api` as a redirect alias only. The docs models-overview page is registered as the secondary/corroborating source, not the changelog. **Note:** this docs property has moved host twice (docs.anthropic.com → docs.claude.com → platform.claude.com); the collector must follow and log 3xx responses and alert on canonical drift.

## 3. Governing documents

No standalone "website terms of use" exists for platform.claude.com / claude.com / anthropic.com. Confirmed by (a) the legal index at `https://www.anthropic.com/legal` (fetched 2026-07-07 — lists Usage Policy/AUP, Privacy Policy, Commercial ToS, Consumer ToS, Supported Regions, Consumer Health Data Privacy, Responsible Disclosure; no website ToU) and (b) web search. The site's own footer identifies the governing documents:

**Footer of `https://platform.claude.com/docs/en/about-claude/models/overview` (fetched 2026-07-07) links:**
- "Terms of service: Commercial" → `https://www.anthropic.com/legal/commercial-terms`
- "Terms of service: Consumer" → `https://www.anthropic.com/legal/consumer-terms`
- "Usage policy" → `https://www.anthropic.com/legal/aup`
- "Privacy policy" → `https://www.anthropic.com/legal/privacy`

| Document | URL | Effective date | Fetched |
|---|---|---|---|
| Commercial Terms of Service | https://www.anthropic.com/legal/commercial-terms | June 17, 2025 | 2026-07-07 |
| Consumer Terms of Service | https://www.anthropic.com/legal/consumer-terms | October 8, 2025 | 2026-07-07 |

platform.claude.com is the Claude developer platform (Claude Console + platform documentation). The Commercial ToS is the primary governing document for this surface (its "Services" definition expressly includes documentation, §4 quotes below), and the Consumer ToS itself carves the Console out of its own scope. The Consumer ToS is analyzed anyway because the footer links it and its restrictions are the only anti-scraping language Anthropic publishes.

## 4. Verbatim clauses — Commercial Terms of Service (eff. 2025-06-17, fetched 2026-07-07)

**Preamble (scope / "Services" definition):**

> "They govern Customer's use of Anthropic API keys and any other Anthropic offerings that references these Terms, as well as all related Anthropic tools, documentation and services (the "Services")."

**Section D.4 (Use Restrictions) — complete text:**

> "D.4. Use Restrictions. Customer may not and must not attempt to (a) access the Services to build a competing product or service, including to train competing AI models or resell the Services except as expressly approved by Anthropic; (b) reverse engineer or duplicate the Services; or (c) support any third party's attempt at any of the conduct restricted in this sentence."

**Section F (Intellectual Property):**

> "Except as expressly stated in these Terms, these Terms do not grant either party any rights to the other's content or intellectual property, by implication or otherwise."

The Commercial ToS contains **no clause restricting automated access, crawling, scraping, bots, or republication**. D.4 is limited to competing products, reverse engineering/duplication, and assisting either.

## 5. Verbatim clauses — Consumer Terms of Service (eff. 2025-10-08, fetched 2026-07-07)

**Preamble (scope):**

> "These Terms of Service ("Terms") govern your use of Claude.ai, Claude Pro, and other products and services that we may offer for individuals, along with any associated apps, software, and websites (together, our "Services")."

**Preamble (carve-out pointing platform surfaces to Commercial ToS):**

> "Please note: Our Commercial Terms of Service govern your use of any Anthropic API key, the Anthropic Console, or any other Anthropic offerings that reference the Commercial Terms of Service. For clarity, this does not include Claude.ai or Claude Pro use for individuals or entities."

**Section 3 (Use of our Services) — prohibited-uses list intro:**

> "You may not access or use, or help another person to access or use, our Services in the following ways:"

**Section 3 — anti-crawl/scrape item:**

> "To crawl, scrape, or otherwise harvest data or information from our Services other than as permitted under these Terms."

**Section 3 — automated-access item (note the express permission carve-out):**

> "Except when you are accessing our Services via an Anthropic API Key or where we otherwise explicitly permit it, to access the Services through automated or non-human means, whether through a bot, script, or otherwise."

**Section 3 — interference item:**

> "You also must not abuse, harm, interfere with, or disrupt our Services, including, for example, introducing viruses or malware, spamming or DDoSing Services, or bypassing any of our systems or protective measures."

**Section 10 (Ownership of the Services) — relevant to republication:**

> "We and our Providers retain all of our respective rights, title, and interest, including intellectual property rights, in and to the Services. Other than the rights of access and use expressly granted in our Terms, our Terms do not grant you any right, title, or interest in or to our Services."

The Usage Policy (https://www.anthropic.com/legal/aup) governs use of Claude model capabilities, not website fetching; not further analyzed here.

## 6. robots.txt — `https://platform.claude.com/robots.txt` (fetched 2026-07-07)

Complete verbatim contents:

```
User-Agent: *
Disallow: /api/

Sitemap: https://platform.claude.com/sitemap.xml
```

Findings:

- No rules specific to `TheLLMReportBot`; we fall under `User-Agent: *`.
- Only `/api/` is disallowed. Both target paths (`/docs/en/about-claude/models/overview`, `/docs/en/release-notes/overview`) are **permitted**. The disallow is the path prefix `/api/` and does not match `/docs/en/api/...` reference pages (which we do not fetch anyway).
- Sitemap fetched 2026-07-07: 3,386 `<loc>` entries, dominated by API-reference doc pages; it does **not** list `/docs/en/about-claude/*` or `/docs/en/release-notes/*`. Sitemap omission has no bearing on crawl permission (robots.txt governs); noted for completeness.

## 7. Analysis

1. **Governing regime.** The pages we fetch are platform documentation. The Commercial ToS "Services" definition expressly includes "all related Anthropic tools, documentation and services," and the Consumer ToS expressly hands "the Anthropic Console, or any other Anthropic offerings that reference the Commercial Terms of Service" to the Commercial ToS. The platform.claude.com footer references both. Best reading: **Commercial ToS governs**, and it contains **no restriction on automated access, crawling, scraping, or republication**. Our activity does not implicate D.4: a change-intelligence digest about Anthropic's public documentation is not "access[ing] the Services to build a competing product or service," not reverse engineering, and not duplication of the Services (verbatim archives stay private; public output is diffs + minimal excerpts).
2. **Residual Consumer-ToS risk.** Consumer ToS §3 prohibits crawling/scraping and automated access, and its scope phrase "along with any associated apps, software, and websites" could be stretched to cover Anthropic web properties generally. Three mitigations: (a) the automated-means clause carves out "where we otherwise explicitly permit it" — robots.txt affirmatively permitting all non-`/api/` paths for all user agents, on a public unauthenticated docs site built to be crawled, is the strongest available form of technical permission; (b) the Consumer ToS's own preamble routes platform offerings to the Commercial ToS; (c) we never create or use a consumer account, never authenticate, and never touch claude.ai. This is browsewrap as to anonymous visitors, but our policy is to comply regardless — hence a CONDITIONAL rather than CLEAR verdict.
3. **Enforcement posture.** Anthropic demonstrated willingness to enforce automated-access restrictions in early 2026 (third-party OAuth/subscription harness bans). That episode concerned consumer-subscription credential abuse, not docs crawling, but it supports keeping our footprint identified, trivial in volume, and instantly stoppable.
4. **Republication.** No license is granted (Consumer §10; Commercial §F). Public output must stay within facts (model IDs, prices, dates, deprecations — not copyrightable) plus minimal quoted excerpts with attribution and links (fair-use posture). Verbatim page archives remain private evidence with sha256 manifests only.
5. **No bot wall.** All documents and target pages were fetched directly on 2026-07-07 with ordinary HTTPS GETs (Cloudflare in path, no challenge served). Nothing in this file is indirectly sourced.

## 8. Verdict

**CONDITIONAL — cleared to collect, subject to all of the following binding conditions:**

1. Fetch only public, unauthenticated docs paths permitted by robots.txt (currently everything outside `/api/`); never fetch `/api/*` on platform.claude.com; never authenticate to or fetch Console-session surfaces; never touch claude.ai.
2. Re-fetch and honor robots.txt at least every 24h; comply immediately if a `TheLLMReportBot` or `*` rule tightens.
3. If Cloudflare or any bot wall challenges the collector, stop fetching this host and escalate for re-review — the "explicitly permit" rationale (§7.2) collapses once access is technically refused. No circumvention, ever.
4. Volume stays trivial: the two pinned pages, hourly, conditional GETs (ETag/If-Modified-Since), exponential backoff on 4xx/5xx, identified UA with live bot info page.
5. Public output limited to factual change data and minimal quoted excerpts with attribution and a link to the source page; verbatim archives remain private (evidence manifests public, content private).
6. Changelog registry pin per §2: `https://platform.claude.com/docs/en/release-notes/overview` (the `/release-notes/api` path is a 307 alias). Log all redirects; alert on host or canonical drift.
7. Re-run this review if either governing document's effective date changes (Commercial ToS currently 2025-06-17; Consumer ToS currently 2025-10-08), if a dedicated website ToU appears, or if the docs migrate hosts again.

---
*Prepared by compliance research agent, 2026-07-07. Source snapshots (HTML) retained in session scratchpad; quotes transcribed verbatim from fetched documents.*

## Verifier concurrence (2026-07-07)

Independent adversarial re-verification by a second agent. All load-bearing sources re-fetched directly 2026-07-07; no dissent — verdict **CONDITIONAL** stands with the conditions as written. Findings:

1. **Quotes verified verbatim and current.** Commercial ToS (https://www.anthropic.com/legal/commercial-terms, eff. June 17, 2025): Services definition ("as well as all related Anthropic tools, documentation and services"), full §D.4, and §F match §4 above word-for-word; independently confirmed the document contains **no** clause on automated access, crawling, scraping, bots, harvesting, republication, or copying. Consumer ToS (https://www.anthropic.com/legal/consumer-terms, eff. October 8, 2025): scope preamble, Commercial-routing carve-out ("Our Commercial Terms of Service govern your use of any Anthropic API key, the Anthropic Console, or any other Anthropic offerings that reference the Commercial Terms of Service."), all three §3 items quoted in §5 above (including the carve-out "or where we otherwise explicitly permit it"), and §10 match word-for-word.
2. **Gap closed — Usage Policy verified, not just assumed, out of scope.** §5 above dismissed the AUP without analysis. Re-fetched https://www.anthropic.com/legal/aup 2026-07-07: its stated scope is anyone who "submit[s] inputs to Anthropic's products and/or services, including via any authorized resellers or passthrough access" — i.e., model users. Its only automation clause is "Utilize automation in account creation or to engage in spammy behavior" (under "Do Not Abuse our Platform"). It contains no clause on crawling, scraping, harvesting, rate limits, or accessing/copying Anthropic websites or documentation. The collector submits no inputs and never authenticates; the AUP does not reach this activity.
3. **No missed website ToU.** Re-fetched https://www.anthropic.com/legal index 2026-07-07: lists Privacy Policy, Acceptable Use Policy, Commercial ToS, Consumer ToS (with archive link), Supported Regions, and support pages — no "Terms of Use"/"Website Terms"/"Site Terms" document exists. §3's conclusion confirmed.
4. **robots.txt re-verified 2026-07-07:** exactly `User-Agent: *` / `Disallow: /api/` / sitemap line, as transcribed in §6. Both pinned paths permitted.
5. **Caveat on §7.2(a) — do not overstate the robots.txt argument.** Characterizing a robots.txt allowance as satisfying the Consumer ToS "where we otherwise explicitly permit it" carve-out is doctrinally generous: robots.txt is an exclusion protocol; the absence of a Disallow is a default, not an affirmative grant of explicit permission, and the crawl/scrape item ("other than as permitted under these Terms") has no such carve-out at all. The clearance does not fall with this argument — the primary defense is scope (Commercial ToS governs the platform docs surface, verified in point 1) plus never authenticating — but no future memo should cite §7.2(a) as a standalone basis. Condition 3 (stop on any bot-wall challenge) is the operative safeguard and is retained unchanged.
6. **Minor date discrepancy, immaterial:** the sweep records fetches dated 2026-07-07; verification fetches returned identical content. All effective dates unchanged (Commercial 2025-06-17; Consumer 2025-10-08), so re-review trigger condition 7 is not tripped.

*Adversarial verifier agent, 2026-07-07. All URLs above re-fetched directly; no bot wall or challenge encountered.*
