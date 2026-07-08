# ToU Clearance — Google hosts (ai.google.dev, cloud.google.com)

**Sweep:** tou-sweep-2026-07 (design-phase legal deliverable, V-Q3 cond. 9)
**Fetch date for all sources:** 2026-07-07 (UTC; server `date` headers confirmed Tue, 07 Jul 2026)
**Agent:** compliance research agent, TheLLMReport
**Sourcing note:** All documents fetched live on 2026-07-07 (no bot walls encountered; no indirect sourcing needed). Quotes below are verbatim as extracted from the fetched pages via automated retrieval.

---

## 1. Host: ai.google.dev

**Planned collector paths:**
- `/gemini-api/docs/pricing` (HTTP 200, `last-modified: Tue, 30 Jun 2026 15:41:12 GMT`)
- `/gemini-api/docs/changelog` (serves Gemini API "Release notes"; most recent entry 2026-06-30)

### 1.1 Governing documents

| Document | URL | Fetched | Applies? |
|---|---|---|---|
| Google Terms of Service (effective May 22, 2024) | https://policies.google.com/terms | 2026-07-07 | **YES — governs the website.** Both target pages' footers link "Terms" → `//policies.google.com/terms`. |
| Google Developers Site Policies | https://developers.google.com/terms/site-policies | 2026-07-07 | **YES — content licensing.** Referenced by the on-page license notice on both target pages. |
| Google APIs Terms of Service (last modified Nov 9, 2021) | https://developers.google.com/terms | 2026-07-07 | **NO for this activity.** Governs programmatic API use only: "By accessing or using our APIs, you are agreeing to the terms below." We fetch documentation web pages; we do not call the Gemini API. |
| Gemini API Additional Terms of Service (effective Mar 23, 2026) | https://ai.google.dev/gemini-api/terms | 2026-07-07 | **NO for this activity.** Scope statement: "To use Gemini API, Google AI Studio, and the other Google developer services that reference these terms (collectively, the 'APIs' or 'Services'), you must accept (1) the Google APIs Terms of Service (the 'API Terms'), and (2) these Gemini API Additional Terms of Service (the 'Additional Terms')." Governs the API/services, not browsing ai.google.dev. |

### 1.2 Verbatim clauses — Google Terms of Service (fetched 2026-07-07, https://policies.google.com/terms, effective May 22, 2024)

Under heading **"Don't abuse our services"** (section "Respect others" / conduct rules):

> "You must not abuse, harm, interfere with, or disrupt our services or systems — for example, by:"
>
> - "introducing malware"
> - "spamming, hacking, or bypassing our systems or protective measures"
> - "jailbreaking, adversarial prompting, or prompt injection, except as part of our safety and bug testing programs"
> - "accessing or using our services or content in fraudulent or deceptive ways"
> - "reverse engineering our services or underlying technology, such as our machine learning models, to extract trade secrets or other proprietary information"
> - **"using automated means to access content from any of our services in violation of the machine-readable instructions on our web pages (for example, robots.txt files that disallow crawling, training, or other activities)"**
> - "using AI-generated content from our services to develop machine learning models or related AI technology"

Under heading **"Google content"** (section "Content in Google services"):

> "Some of our services include content that belongs to Google... You may use Google's content as allowed by these terms and any service-specific additional terms, but we retain any intellectual property rights that we have in our content. Don't remove, obscure, or alter any of our branding, logos, or legal notices."

Under heading **"Software in Google services"**, immediately following the personal, non-assignable license grant (recorded per verifier dissent item 1, same document, same fetch):

> "You may not copy, modify, distribute, sell, or lease any part of our services or software."

**Ruling on this clause (dissent item 1):** Read in context, the sentence is a limitation on the *software* license grant, but its literal text reaches "any part of our services" — it is the single most restrictive content-related sentence in the governing document and the clause opposing counsel would cite against (a) full-page verbatim archives and (b) republication of excerpts. For ai.google.dev it is answered by the express CC BY 4.0 license on the doc pages (§1.3): a specific affirmative grant controls over this general restriction, so archives and attributed excerpts from ai.google.dev doc pages are covered. For cloud.google.com, where no license exists, see the ruling at §2.3–§2.4.

Scope/coverage statements:

> "Google services are provided by, and you're contracting with: Google LLC organized under the laws of the State of Delaware, USA" — services include "apps and sites (like Search and Maps), platforms (like Google Shopping), integrated services, devices (like Google Nest and Pixel)."
>
> "Follow these terms and service-specific additional terms, which could, for example, include things like additional age requirements"

**Key reading:** Google's website ToS does NOT categorically prohibit automated access. The prohibition is expressly conditioned on violating "machine-readable instructions" (robots.txt). Automated access that honors robots.txt — which is a design invariant of our collector — is not within the prohibited conduct as drafted. "Bypassing our systems or protective measures" is also inapplicable: our policy forbids bot-wall circumvention.

### 1.3 Content license (republication basis)

On-page notice at the bottom of both `/gemini-api/docs/pricing` and `/gemini-api/docs/changelog` (fetched 2026-07-07):

> "Except as otherwise noted, the content of this page is licensed under the Creative Commons Attribution 4.0 License, and code samples are licensed under the Apache 2.0 License. For details, see the Google Developers Site Policies."

Google Developers Site Policies (https://developers.google.com/terms/site-policies, fetched 2026-07-07) — attribution requirements:

> For exact reproductions: "Portions of this page are reproduced from work created and shared by Google and used according to terms described in the Creative Commons 4.0 Attribution License."
>
> For modified versions: "Portions of this page are modifications based on work created and shared by Google and used according to terms described in the Creative Commons 4.0 Attribution License."

Exceptions noted: Google trademarks/brand features excluded; images/audio/video and externally linked material may carry separate licenses. Link back to original source pages required. The Site Policies page contains **no clause restricting crawling, scraping, or automated access**.

**Republication of diff excerpts from ai.google.dev doc pages is affirmatively licensed (CC BY 4.0) provided attribution + source link are given.**

### 1.4 robots.txt — https://ai.google.dev/robots.txt (fetched 2026-07-07)

Complete file, verbatim:

```
User-agent: *
Disallow:
Sitemap: https://ai.google.dev/sitemap.xml
```

**Path check:** empty `Disallow` under `User-agent: *` = everything allowed. `/gemini-api/docs/pricing` — ALLOWED. `/gemini-api/docs/changelog` — ALLOWED. No agent-specific blocks that would catch `TheLLMReportBot`.

---

## 2. Host: cloud.google.com

**Planned collector path:** `/vertex-ai/generative-ai/pricing`

### 2.1 REDIRECT FINDING (operationally significant)

Verified 2026-07-07 with our production User-Agent (`TheLLMReportBot/1.0 (+https://thellmreport.com/bot)`):

```
GET https://cloud.google.com/vertex-ai/generative-ai/pricing
→ 301 Moved Permanently
→ Location: https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing
→ 200 OK (1 redirect, same host)
```

Final page title at the research fetch: "Cost of building and deploying AI models in Agent Platform" — Google has rebranded the Vertex AI generative-AI pricing page under "Gemini Enterprise Agent Platform." **Title churn (dissent item 3):** the verifier's same-day re-fetch (2026-07-07) observed the page's `<title>` rendering as "Agent Platform Pricing | Google Cloud" — the page is actively churning, so neither title snapshot in this file may be relied on. Same host, so no new-host clearance is triggered, but the collector must record canonical-URL changes in evidence manifests, and manifests must capture page title + canonical URL per fetch rather than relying on this file's snapshot (condition 9).

**Separate migration signal:** Google Cloud *documentation* pages (e.g. `/vertex-ai/generative-ai/docs/learn/models`) now 301 cross-host to **docs.cloud.google.com**. Its robots.txt (fetched 2026-07-07) mirrors cloud.google.com's: no rules affecting `/vertex-ai/generative-ai/*`; `Sitemap: https://docs.cloud.google.com/sitemap.xml`. If our target ever migrates cross-host, docs.cloud.google.com is pre-checked as of this date but must be re-verified at cutover.

### 2.2 Governing documents

| Document | URL | Fetched | Applies? |
|---|---|---|---|
| Google Terms of Service (effective May 22, 2024) | https://policies.google.com/terms | 2026-07-07 | **YES — governs the website.** The final pricing page links to `policies.google.com/terms?hl=en` (confirmed in fetched HTML). cloud.google.com is a Google site within the ToS's stated coverage ("apps and sites"). |
| Google Cloud Platform Terms of Service | https://cloud.google.com/terms | 2026-07-07 | **NO for this activity.** Opening clause: "These Google Cloud Terms of Service (together, the 'Agreement') are entered into by Google and the entity or person agreeing to these terms ('Customer') and govern Customer's access to and use of the Services." It binds account-holding Customers using GCP Services; it does not govern unauthenticated browsing of public marketing/pricing pages. The fetched text contains **no clause about scraping/crawling the cloud.google.com website** (Section 3.3 restrictions target service usage: High Risk Activities, AUP, etc.). |
| Google APIs Terms of Service | https://developers.google.com/terms | 2026-07-07 | **NO** — API use only (see §1.1). Recorded for completeness: Section 5(e) prohibits, for content returned from APIs: "Scrape, build databases, or otherwise create permanent copies of such content, or keep cached copies longer than permitted by the cache header". We do not consume any Google API. |

### 2.3 Verbatim clauses

The applicable website terms are the same Google Terms of Service quoted in full in §1.2 above (same document, same effective date, same fetch). The operative clauses for this host are identical:

> "using automated means to access content from any of our services in violation of the machine-readable instructions on our web pages (for example, robots.txt files that disallow crawling, training, or other activities)" — *Google ToS, "Don't abuse our services", effective May 22, 2024, fetched 2026-07-07*

> "You may use Google's content as allowed by these terms and any service-specific additional terms, but we retain any intellectual property rights that we have in our content. Don't remove, obscure, or alter any of our branding, logos, or legal notices." — *Google ToS, "Google content", fetched 2026-07-07*

> "You may not copy, modify, distribute, sell, or lease any part of our services or software." — *Google ToS, "Software in Google services", effective May 22, 2024, fetched 2026-07-07 (recorded per verifier dissent item 1)*

**Ruling on this clause for this host (dissent item 1):** Contextual reading = software-license limitation, but its literal reach ("any part of our services") matters most here because the pricing page carries **no affirmative license** (§2.4). Our private verbatim archives of this page are therefore full-page copies made with no affirmative permission, resting solely on fair-use / uncopyrightable-facts grounds: non-published, evidence-preservation purpose, fact-dominant page, no market substitution. That position is defensible only while the archives remain private and non-distributed — see binding condition 8.

### 2.4 Content license

Unlike ai.google.dev doc pages, the final pricing page (`/gemini-enterprise-agent-platform/generative-ai/pricing`) contains **no Creative Commons license notice** (raw HTML grepped 2026-07-07: no "Creative Commons" / "licensed under" strings). Republication from this page therefore rests on minimal-quotation (fact-heavy pricing data: prices per token are uncopyrightable facts; short excerpts quoted for reporting/commentary), not on an affirmative license. Verbatim page archives remain PRIVATE per our design. Per the "Software in Google services" clause ruled on in §2.3 (dissent item 1), those full-page archives are justified only as private, non-distributed, evidence-preservation copies under fair use — they must never be published, distributed, or shared outside the evidence pipeline (condition 8), and published diffs must prefer factual data points over expressive prose.

### 2.5 robots.txt — https://cloud.google.com/robots.txt (fetched 2026-07-07)

Rules under `User-agent: *`, verbatim (complete):

```
User-agent: *
Disallow: /console?*getstarted=*
Disallow: /landing/
Disallow: /walkthroughs/
Disallow: /terms/looker/legal/sccs/
Disallow: /terms/looker/legal/customers/mobile-governing-agreement
Disallow: /terms/looker/legal/customers/aup
Disallow: /terms/looker/dpst
Disallow: /terms/looker/legal/eu-modelclauses-nov16
Disallow: /terms/looker/legal/suppliers/supplier-code-of-conduct
Disallow: /terms/looker/legal/suppliers/partner-assignment-faq
Disallow: /terms/looker/legal/rapid-deployment-terms
Disallow: /terms/looker/legal/partner-success-services-agreement
Disallow: /terms/looker/additional-product-terms
Disallow: /log?*
Disallow: /partners/resources/gartner-dbms-mq-report
Disallow: /partners/resources/forrester-dsp-wave-report
Disallow: /cpp/docs/reference/*
Allow: /cpp/docs/reference/
Allow: /cpp/docs/reference/*/latest/
Allow: /cpp/docs/reference/*/latest$
Allow: /cpp/docs/reference/help/
Disallow: /dotnet/docs/reference/*
Allow: /dotnet/docs/reference/
Allow: /dotnet/docs/reference/*/latest/
Allow: /dotnet/docs/reference/*/latest$
Allow: /dotnet/docs/reference/help/
Disallow: /go/docs/reference/*
Allow: /go/docs/reference/
Allow: /go/docs/reference/*/latest/
Allow: /go/docs/reference/*/latest$
Allow: /go/docs/reference/help/
Disallow: /java/docs/reference/*
Allow: /java/docs/reference/
Allow: /java/docs/reference/*/latest/
Allow: /java/docs/reference/*/latest$
Allow: /java/docs/reference/help/
Disallow: /nodejs/docs/reference/*
Allow: /nodejs/docs/reference/
Allow: /nodejs/docs/reference/*/latest/
Allow: /nodejs/docs/reference/*/latest$
Allow: /nodejs/docs/reference/help/
Disallow: /php/docs/reference/*
Allow: /php/docs/reference/
Allow: /php/docs/reference/*/latest/
Allow: /php/docs/reference/*/latest$
Allow: /php/docs/reference/help/
Disallow: /python/docs/reference/*
Allow: /python/docs/reference/
Allow: /python/docs/reference/*/latest/
Allow: /python/docs/reference/*/latest$
Allow: /python/docs/reference/help/
Disallow: /ruby/docs/reference/*
Allow: /ruby/docs/reference/
Allow: /ruby/docs/reference/*/latest/
Allow: /ruby/docs/reference/*/latest$
Allow: /ruby/docs/reference/help/
User-agent: Google-DevRel
Allow: /

Sitemap: https://cloud.google.com/sitemap.xml
Sitemap: https://cloud.google.com/sitemapindex.xml
Sitemap: https://cloud.google.com/cgc/sitemapindex.xml
Sitemap: https://cloud.google.com/transform/sitemapsummarylanding/cloudblog
Sitemap: https://cloud.google.com/transform/sitemapsummary/cloudblog
Sitemap: https://cloud.google.com/transform/sitemapsummary/transform
```

**Path check:** No Disallow matches `/vertex-ai/generative-ai/pricing` (original) or `/gemini-enterprise-agent-platform/generative-ai/pricing` (301 target) — both ALLOWED. Disallows target console, Looker legal pages, gated reports, and non-latest SDK reference docs only. No agent-specific block catches `TheLLMReportBot`.

---

## 3. Analysis

1. **Which terms govern:** Both hosts are public Google websites whose footers/pages link to the **Google Terms of Service (policies.google.com/terms, eff. 2024-05-22)** as the governing terms. The Google APIs ToS, Gemini API Additional Terms, and GCP ToS are service/contract terms triggered by API use or a Customer account — none of which our HTML collector engages in.
2. **Automated access:** The Google ToS prohibits automated access only "in violation of the machine-readable instructions on our web pages (for example, robots.txt files...)". Both robots.txt files, fetched 2026-07-07, allow every path we plan to fetch. Honoring robots.txt therefore keeps the collector on the permitted side of the only automated-access clause in the governing document. Our no-bot-wall-circumvention rule also satisfies "bypassing our systems or protective measures."
3. **Republication:** ai.google.dev doc pages are CC BY 4.0 (attribution + source link required, exact Site Policies attribution strings quoted in §1.3; trademarks/media excluded). The cloud.google.com pricing page carries no CC license — excerpts there must stay minimal (pricing facts + short quotes), attributed, with verbatim archives private. Per the ToS "Google content" clause, quoted material must not have branding/logos/legal notices removed, obscured, or altered.
4. **Change risk:** the Vertex pricing URL already 301s to an Agent Platform URL, the final page's `<title>` changed between same-day fetches on 2026-07-07 (§2.1, dissent item 3), and Google Cloud docs are migrating cross-host to docs.cloud.google.com. Collector must log redirect chains plus page title and canonical URL per fetch in manifests, and re-run robots/ToU checks if the target moves to a new host.
5. **"May not copy... any part of our services" clause (recorded per dissent item 1):** the ToS "Software in Google services" restriction — "You may not copy, modify, distribute, sell, or lease any part of our services or software" — is the most restrictive content-related sentence in the governing document. Contextually it limits the software license grant, but its literal text reaches "any part of our services." Resolution: for ai.google.dev, the express CC BY 4.0 grant (§1.3) controls as the specific affirmative license; for cloud.google.com, no license exists, so verbatim archives stand only as private, non-distributed, evidence-preservation copies under fair use (non-published purpose, fact-dominant page, no market substitution) — enforced by condition 8.

## 4. Verdict

**CONDITIONAL — cleared to collect, subject to the conditions below.**

1. Re-check `robots.txt` on each host at least daily and before each crawl cycle where practical; halt fetching any path that becomes disallowed for `*` or for our agent (the ToS ties permission for automated access directly to robots.txt).
2. Never bypass bot walls, rate limits, or other protective measures (ToS "bypassing our systems or protective measures"); keep conditional GETs + backoff.
3. When republishing excerpts from ai.google.dev doc pages, include CC BY 4.0 attribution using the Site Policies wording and a link to the source page; do not reproduce Google trademarks/brand features or embedded media under this license.
4. Keep cloud.google.com excerpts minimal (pricing facts and short quotes for reporting); no affirmative license exists for that page — verbatim archives stay PRIVATE.
5. Do not remove, obscure, or alter Google branding, logos, or legal notices within any quoted excerpt.
6. Treat a cross-host redirect (e.g., migration to docs.cloud.google.com) as a new-host event: re-verify robots.txt and governing terms before fetching the new host; record all redirect chains (the current 301 to `/gemini-enterprise-agent-platform/generative-ai/pricing`) in evidence manifests.
7. Do not use fetched content to train/develop ML models beyond change-detection processing (robots.txt "training" language and ToS AI-content clause both signal Google's sensitivity here; our diff pipeline is fine, model training is not cleared).
8. Verbatim archives of cloud.google.com pages must never be published, distributed, or shared outside the evidence pipeline (including in Pro alerts or API responses); retention is for verification/dispute purposes only. Published diffs from cloud.google.com must prefer factual data points (prices, model names, dates) over expressive prose; any prose quote stays at minimal-quotation length. (Added per verifier dissent item 2.)
9. Evidence manifests must capture page title + canonical URL per fetch (alongside the redirect chains required by condition 6) and must not rely on this file's snapshots: the Agent Platform pricing page's `<title>` changed between same-day fetches on 2026-07-07 ("Cost of building and deploying AI models in Agent Platform" → "Agent Platform Pricing | Google Cloud"). (Added per verifier dissent item 3.)

*Prepared 2026-07-07 by the compliance research agent. Amended 2026-07-08 per the verifier dissent below (clause recorded in §1.2/§2.3/§3; conditions 8–9 added). Import verbatim at Phase 0.*

---

## Verifier dissent (2026-07-07)

**Amendments applied 2026-07-08** - every required change below is folded into the body above; import-ready.

**Reviewer:** adversarial legal verifier (independent re-fetch, 2026-07-07). **Re-fetched:** policies.google.com/terms, developers.google.com/terms/site-policies, both robots.txt files, both target pages, and the 301 chain.

### What verified

- Google ToS quotes in §1.2/§2.3 are **real and current**: effective date still "Effective May 22, 2024" on live fetch; the "automated means ... machine-readable instructions ... robots.txt" clause and the "Google content" branding clause are verbatim accurate.
- Site Policies CC BY 4.0 attribution strings verified verbatim; that page contains no crawl/scrape restriction, as stated.
- robots.txt for both hosts re-fetched: matches §1.4 and §2.5 in all material respects; both planned paths ALLOWED under `User-agent: *`.
- ai.google.dev pricing page carries the CC BY 4.0 / Apache 2.0 footer notice and links Terms → `//policies.google.com/terms`; the cloud.google.com Agent Platform pricing page carries **no** CC notice — both as claimed.
- `GET /vertex-ai/generative-ai/pricing` → 301 → same-host `/gemini-enterprise-agent-platform/generative-ai/pricing` → 200, independently reproduced.
- The ruling-out of the Google APIs ToS, Gemini API Additional Terms, and GCP ToS (customer/service contracts, not website terms) is sound. The GCP AUP binds Customers via the GCP ToS and does not reach unauthenticated browsing.

### Material omission — the file is incomplete as filed

The Google ToS (same document, same fetch) also contains, in the **"Software in Google services"** section, immediately following the personal, non-assignable license grant:

> "You may not copy, modify, distribute, sell, or lease any part of our services or software."

The sweep file never records or rules on this sentence. Read in context it is a limitation on the *software* license grant, but its literal text reaches **"any part of our services"** — and it is the single most restrictive content-related sentence in the governing document. It is precisely the clause opposing counsel would cite against (a) full-page verbatim archives and (b) republication of excerpts. For ai.google.dev this is answered by the express CC BY 4.0 license (which, as a specific affirmative grant, controls). For the **cloud.google.com pricing page there is no license at all**, so our private verbatim archives are full-page copies made with no affirmative permission, resting solely on fair-use / uncopyrightable-facts grounds — a defensible position (non-published, evidence-preservation purpose, fact-dominant page, no market substitution), but one the clearance record must actually take, not omit.

### Required changes

1. **Record the clause.** §1.2 and §2.3 must quote the "You may not copy, modify, distribute, sell, or lease any part of our services or software" sentence (ToS, "Software in Google services", eff. 2024-05-22, fetched 2026-07-07) and rule on it explicitly: contextual reading = software-license limitation; ai.google.dev archives/excerpts covered by CC BY 4.0; cloud.google.com verbatim archives justified only as private, non-distributed, evidence-preservation copies under fair use.
2. **Add condition 8:** Verbatim archives of cloud.google.com pages must never be published, distributed, or shared outside the evidence pipeline (including in Pro alerts or API responses); retention is for verification/dispute purposes only. Published diffs from cloud.google.com must prefer factual data points (prices, model names, dates) over expressive prose; any prose quote stays at minimal-quotation length.
3. **Minor evidence-hygiene note:** the Agent Platform pricing page's `<title>` now renders as "Agent Platform Pricing | Google Cloud" (vs the title recorded in §2.1) — the page is actively churning; manifests should capture page title + canonical URL per fetch, not rely on this file's snapshot.

### Revised verdict

**CONDITIONAL — verdict class unchanged, but the clearance is not import-ready until the omitted ToS clause is recorded and condition 8 above is added.** With those amendments, the clearance is defensible for an hourly, robots.txt-honoring, identified-UA fetcher publishing minimal-excerpt diffs: Google's ToS expressly conditions its automated-access prohibition on robots.txt compliance, both robots.txt files allow the target paths, and the republication posture (CC BY 4.0 with attribution on ai.google.dev; minimal factual excerpts on cloud.google.com) is sound.

*Dissent appended 2026-07-07 by the adversarial verifier. All verification fetches performed live on 2026-07-07.*
