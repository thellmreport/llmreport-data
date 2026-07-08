# ToU Sweep — Source Class: `policy-page`

**Sweep:** tou-sweep-2026-07 · design-phase legal deliverable [V-Q3 cond. 9]
**Fetch date (all fetches):** 2026-07-07
**Prepared by:** compliance research agent (automated sweep, human review pending)
**Poll cadence for this class:** WEEKLY (feeds `policy.changed` events)
**Production User-Agent:** `TheLLMReportBot/1.0 (+https://thellmreport.com/bot)` — all "resolves" checks below were verified with this exact UA via HTTPS GET; secondary verification via a generic fetch client where noted. No bot wall was ever bypassed: where a host returned 403 to the generic client, we recorded the fact and re-tried only with our identified production UA, which is the honest production configuration.

---

## 1. Registry seed (class: `policy-page`)

All URLs verified resolving HTTP 200 on 2026-07-07 with the production UA unless noted.

| # | id | Provider / document | Exact URL | Status 2026-07-07 | Doc's own date |
|---|----|---------------------|-----------|--------------------|----------------|
| 1 | `openai-usage-policies` | OpenAI Usage Policies | https://openai.com/policies/usage-policies/ | 200 (403 to generic client) | Effective Oct 29, 2025 |
| 2 | `openai-services-agreement` | OpenAI Services Agreement (formerly "Business Terms") | https://openai.com/policies/business-terms/ → **307** → https://openai.com/policies/services-agreement/ | 200 at canonical | Updated Dec 1, 2025; Effective Jan 1, 2026 |
| 3 | `anthropic-usage-policy` | Anthropic Usage Policy (AUP) | https://www.anthropic.com/legal/aup | 200 | Effective Sep 15, 2025 |
| 4 | `anthropic-commercial-terms` | Anthropic Commercial Terms of Service | https://www.anthropic.com/legal/commercial-terms | 200 | Effective Jun 17, 2025 |
| 5 | `google-genai-prohibited-use` | Google Generative AI Prohibited Use Policy | https://policies.google.com/terms/generative-ai/use-policy | 200 | Last updated Dec 17, 2024 |
| 6 | `google-apis-tos` | Google APIs Terms of Service | https://developers.google.com/terms | 200 | Last modified Nov 9, 2021 |
| 7 | `aws-service-terms` | AWS Service Terms | https://aws.amazon.com/service-terms/ | 200 | Last updated Jun 30, 2026 |
| 8 | `aws-aup` | AWS Acceptable Use Policy | https://aws.amazon.com/aup/ | 200 | Last updated Jul 1, 2021 |
| 9 | `ms-product-terms-online-services` | Microsoft Product Terms — For Online Services | https://www.microsoft.com/licensing/terms/product/ForOnlineServices/all | 200 | Monthly editions; "Effective Date" field client-populated |
| 10 | `mistral-commercial-tos` | Mistral Commercial Terms of Service | https://legal.mistral.ai/terms/commercial-terms-of-service | 200 | Effective May 28, 2026 |
| 11 | `mistral-usage-policy` | Mistral Usage Policy | https://legal.mistral.ai/terms/usage-policy | 200 | Effective Jun 11, 2026 |
| 12 | `xai-tos` | xAI Terms of Service (consumer) | https://x.ai/legal/terms-of-service | 200 (403 to generic client) | Effective Jun 26, 2026 |
| 13 | `xai-aup` | xAI Acceptable Use Policy | https://x.ai/legal/acceptable-use-policy | 200 (403 to generic client) | Effective Jun 26, 2026 |

**Registry notes**
- (#2) `https://mistral.ai/terms` now **301-redirects to `https://legal.mistral.ai/terms`** — Mistral moved its legal center to a dedicated host (Netlify-hosted per its own Legal Notice). Register documents at the `legal.mistral.ai` canonical URLs; keep `mistral.ai/terms` as a redirect-watch alias.
- (#2) OpenAI renamed "Business Terms" to "OpenAI Services Agreement". Register the canonical `/policies/services-agreement/`; keep `/policies/business-terms/` as a redirect-watch alias (redirect churn is itself a `policy.changed` signal).
- Both OpenAI and xAI legal pages link a "previous version" archive — useful for diff validation.
- (verifier dissent item 5) OpenAI's Terms of Use registry entry covers only `/policies/terms-of-use/`; OpenAI also maintains regional variants (`/policies/row-terms-of-use/`, `/policies/eu-terms-of-use/`) not independently examined by this sweep. Record which variant serves the operator (see §2.1 condition 7) and watch all three for divergence in the extract-data clause; log the serving variant in each raw-HTML evidence capture, since `/policies/terms-of-use/` may itself be geo-routed.

### Hosts in this class vs. the rest of the sweep

| Host | Covered by another sweep file? | Action |
|------|-------------------------------|--------|
| openai.com | expected (docs/pricing sweeps) | cross-check; clearance also recorded here |
| www.anthropic.com | expected | cross-check; clearance also recorded here |
| **policies.google.com** | **NEW — flag** | full clearance in §2.3 |
| **developers.google.com** | **NEW — flag** | full clearance in §2.4 |
| aws.amazon.com | expected | cross-check; clearance also recorded here |
| www.microsoft.com | verify (product-terms path may be unique to this file) | clearance in §2.6 |
| **legal.mistral.ai** | **NEW — discovered via 301 from mistral.ai/terms — flag** | full clearance in §2.7 |
| x.ai | expected | cross-check; clearance also recorded here |

---

## 2. Host-by-host clearance

### 2.1 openai.com

**Governing document:** OpenAI **Terms of Use** — https://openai.com/policies/terms-of-use/ — Published Jan 1, 2026; Effective Jan 1, 2026 — fetched 2026-07-07 (200 with production UA; 403 to generic client).

Scope clause (verbatim, preamble):
> "These Terms of Use apply to your use of ChatGPT, DALL·E, and OpenAI's other services for individuals, along with any associated software applications and websites (all together, 'Services'). … By using our Services, you agree to these Terms."

Automated-access clauses (verbatim, section **"Using our Services → What you cannot do"**):
> "You may not use our Services for any illegal, harmful, or abusive activity. For example, you may not: …
> Automatically or programmatically extract data or Output (defined below). …
> Interfere with or disrupt our Services, including circumvent any rate limits or restrictions or bypass any protective measures or safety mitigations we put on our Services."

**robots.txt** (https://openai.com/robots.txt, fetched 2026-07-07): `User-agent: *` / `Allow: /` / `Disallow: /microsoft-for-startups/` / `Sitemap: https://openai.com/sitemap.xml`. Our paths `/policies/usage-policies/`, `/policies/services-agreement/`, `/policies/business-terms/` are **allowed**.

**Bot-wall observation (amended per verifier dissent item 3):** openai.com returned **403 to a generic fetch client** but **200 to `TheLLMReportBot/1.0`** on 2026-07-07. This is not circumvention — the identified UA is our declared production identity, and any 403/429 to it is treated as revocation regardless of cause. But no permission inference runs the other way: a 200 to an unrecognized UA means the wall has not classified it, not that the operator admitted or authorized it. That the wall specifically 403s a generic client on the ToU pages themselves is affirmative evidence of intent to restrict automated access to exactly these pages — this cuts against, rather than reinforces, the robots.txt counterweight discussed below.

**Analysis (revised per verifier dissent item 3):** The ToU's "automatically or programmatically extract data" clause facially covers scripted fetching of the policy pages, and the Services definition reaches OpenAI's websites. Counterweights: robots.txt affirmatively allows crawling of these paths (a machine-readable permission signal) — though, per the bot-wall observation above, this counterweight is weakened, not reinforced, by a bot wall that specifically 403s a generic client on exactly these ToU pages; our access is low-volume conditional GETs of public, non-authenticated pages; we quote minimal excerpts (fair-use quotation for commentary/reporting) and keep verbatim archives private; browsewrap assent by a bot reading public pages is legally weak. The circumvention clause is fully complied with: we never bypass rate limits or protective measures, and a 403 to our UA is treated as revocation — this halt-on-403 behavior is correct and unaffected by the above.

**Verdict: CONDITIONAL.**
Conditions: (1) re-check robots.txt each run; (2) always send the identified UA; (3) conditional GETs (ETag/If-Modified-Since), weekly cadence for this class; (4) any 403/429 to our UA = permission revoked → stop, mark source degraded, fall back to Internet Archive snapshots; (5) published output limited to minimal quoted excerpts + diff metadata; verbatim archives stay private; (6) no login, no paywalled or gated content ever; (7) record which OpenAI ToU regional variant (ROW/EU/US) serves the operator at `/policies/terms-of-use/` and monitor `/policies/row-terms-of-use/` and `/policies/eu-terms-of-use/` for divergence in the extract-data clause; evidence capture must log the serving variant per fetch (verifier dissent item 5).

---

### 2.2 www.anthropic.com

**Governing document:** No dedicated website terms exist. The Anthropic legal center (https://www.anthropic.com/legal, fetched 2026-07-07) lists: Consumer Terms (`/legal/consumer-terms`), Commercial Terms (`/legal/commercial-terms`), Privacy Policy (`/legal/privacy`), Consumer Health Data Privacy Policy, Acceptable Use Policy (`/legal/aup`), Responsible Disclosure Policy. The closest document is the **Consumer Terms of Service** — https://www.anthropic.com/legal/consumer-terms — Effective Oct 8, 2025 — fetched 2026-07-07.

Scope clause (verbatim, preamble):
> "These Terms of Service ('Terms') govern your use of Claude.ai, Claude Pro, and other products and services that we may offer for individuals, along with any associated apps, software, and websites (together, our 'Services')."

Automated-access clauses (verbatim, section "Use of our Services" prohibited-uses list):
> "To crawl, scrape, or otherwise harvest data or information from our Services other than as permitted under these Terms."
> "Except when you are accessing our Services via an Anthropic API Key or where we otherwise explicitly permit it, to access the Services through automated or non-human means, whether through a bot, script, or otherwise."

Tracked-document scope note: the Usage Policy states (verbatim, preamble): "Our Usage Policy (also referred to as our 'Acceptable Use Policy' or 'AUP') applies to anyone who can submit inputs to Anthropic's products and/or services, including via any authorized resellers or passthrough access, all of whom we refer to as 'users.'" — i.e., it governs product usage, not website browsing.

**robots.txt** (https://www.anthropic.com/robots.txt, fetched 2026-07-07): `User-Agent: *` / `Allow: /` / `Sitemap: https://www.anthropic.com/sitemap.xml`. Our paths `/legal/aup`, `/legal/commercial-terms` are **allowed** — no restrictions at all.

**Analysis (revised per verifier dissent item 4):** Whether the marketing/legal site anthropic.com is an "associated website" of the consumer products is ambiguous; if it is, the crawl/scrape clause applies "other than as permitted under these Terms," and the bot clause carves out access "where we otherwise explicitly permit it." A fully permissive `Allow: /` robots.txt default is generic, not the "explicit" permission the carve-out contemplates, and a reviewing court would not equate the two — this file no longer relies on robots.txt as a source of explicit permission here. The CONDITIONAL verdict instead rests on grounds already present and independently sufficient: browsewrap assent is legally weak where the "acceptor" is a bot reading public, non-authenticated pages; our access is non-disruptive and honors revocation (403/429 halts the host); and published output is minimal quotation for reporting, with verbatim archives kept private. That Anthropic publishes these legal URLs for public reference remains a fact in the record, but is not treated as a source of permission.

**Verdict: CONDITIONAL.**
Conditions: same standing conditions as §2.1 (robots re-check, identified UA, conditional GETs, 403/429 = revocation, minimal excerpts public / verbatim archive private).

---

### 2.3 policies.google.com — NEW HOST (flag)

**Governing document:** **Google Terms of Service** — https://policies.google.com/terms — Effective May 22, 2024 — fetched 2026-07-07.

Coverage (verbatim, "Definitions" via service-specific reference):
> "The Google services that are subject to these terms are the products and services listed at https://policies.google.com/terms/service-specific, including: apps and sites (like Search and Maps), platforms (like Google Shopping), integrated services (like Maps embedded in other companies' apps or sites), devices and other goods (like Google Nest)."

Automated-access clause (verbatim, section **"Don't abuse our services"**):
> "You must not abuse, harm, interfere with, or disrupt our services or systems — for example, by: introducing malware, spamming, hacking, or bypassing our systems or protective measures … using automated means to access content from any of our services in violation of the machine-readable instructions on our web pages (for example, robots.txt files that disallow crawling, training, or other activities)"

**robots.txt** (https://policies.google.com/robots.txt, fetched 2026-07-07): **HTTP 404 — no robots.txt exists for this host.** Under RFC 9309 §2.3.1.2, absence of robots.txt means crawling is unrestricted. The target path `/terms/generative-ai/use-policy` is therefore unrestricted (confirmed 200 with production UA).

**Analysis:** Google's own ToS defines the abuse line as automated access *"in violation of the machine-readable instructions on our web pages"* — i.e., Google contractually keys permission to robots.txt. With no robots.txt on this host and no disallow anywhere, compliant automated access is affirmatively consistent with Google's terms. Cleanest host in the set.

**Verdict: CLEAR.**
(Standing program conditions still apply: identified UA, conditional GETs, re-check robots.txt each run in case one appears, minimal excerpts.)

---

### 2.4 developers.google.com — NEW HOST (flag)

**Governing documents:**
1. **Google Terms of Service** (same as §2.3 — May 22, 2024) — same robots.txt-keyed abuse clause, quoted above.
2. **Google Developers Site Policies** — https://developers.google.com/terms/site-policies — Last updated 2025-08-06 UTC — fetched 2026-07-07. Content licensing (verbatim):
> "Except as otherwise noted, the content of this page is licensed under the Creative Commons Attribution 4.0 License, and code samples are licensed under the Apache 2.0 License."

Tracked-document note: the Google APIs ToS itself (https://developers.google.com/terms, Last modified Nov 9, 2021) contains a scraping clause at **Section 5.e** — "Scrape, build databases, or otherwise create permanent copies of such content, or keep cached copies longer than permitted by the cache header" — but by its terms this governs content **returned by Google APIs**, not fetching of the ToS web page itself.

**robots.txt** (https://developers.google.com/robots.txt, fetched 2026-07-07): `User-agent: *` / `Disallow: /youtube/partner/` / `Sitemap: https://developers.google.com/sitemap.xml`. Our path `/terms` is **allowed**.

**Analysis:** Same robots.txt-keyed permission as §2.3; additionally the site's text content is CC BY 4.0 (except as otherwise noted), which independently licenses quotation/republication with attribution — stronger than fair use alone. Legal terms pages may be an "otherwise noted" carve-out in spirit, so we still keep excerpts minimal.

**Verdict: CLEAR.**
Conditions: attribute Google when quoting (CC BY 4.0 hygiene); standing program conditions.

---

### 2.5 aws.amazon.com

**Governing documents:**
1. **AWS Site Terms** — https://aws.amazon.com/terms/ — Last updated Jun 4, 2025 — fetched 2026-07-07.
2. **AWS Acceptable Use Policy** — https://aws.amazon.com/aup/ — Last updated Jul 1, 2021 — fetched 2026-07-07.

Site Terms scope (verbatim):
> "By visiting the AWS Site, you accept the Site Terms. Please read them carefully."

Site Terms license + robots clause (verbatim, "License and Site Access"):
> "AWS grants you a limited license to access and make personal use of the AWS Site and not to download (other than page caching) or modify it, or any portion of it, except with express written consent of AWS. This license does not include any resale or commercial use of the AWS Site or its contents; any derivative use of the AWS Site or its contents; … use of data mining, robots, or similar data gathering and extraction tools."

Site Terms republication clause (verbatim, same section):
> "The AWS Site or any portion of the AWS Site may not be reproduced, duplicated, copied, sold, resold, visited, or otherwise exploited for any commercial purpose without express written consent or license of AWS. You may not frame or utilize framing techniques to enclose any trademark, logo, or other proprietary information (including images, text, page layout, or form) of AWS without express written consent."

AUP scope (verbatim, preamble):
> "This Acceptable Use Policy ('Policy') governs your use of the services offered by Amazon Web Services, Inc. and its affiliates ('Services') and our website(s) including http://aws.amazon.com ('AWS Site'). We may modify this Policy by posting a revised version on the AWS Site. By using the Services or accessing the AWS Site, you agree to the latest version of this Policy."

The current (Jul 1, 2021) AUP prohibited-use list covers illegal/fraudulent activity, rights violations, violence/terrorism, CSAE, security/integrity violations, and spam — it contains **no anti-crawling clause** (the pre-2021 "Monitoring or Crawling" network-abuse bullet no longer exists).

**robots.txt** (https://aws.amazon.com/robots.txt, fetched 2026-07-07): rule groups for `AdsBot-Google`/`AdsBot-Google-Mobile` and `User-agent: *`; many path disallows (`/blogs/`, `/search`, `/pm/`, `/community/*`, etc.) but **no rule matching `/service-terms/` or `/aup/`** — both paths are **allowed** (verified by direct inspection, not just summary).

**Analysis (revised per verifier dissent item 2):** This is the highest-risk host in the class. The Site Terms browsewrap expressly excludes "data mining, robots, or similar data gathering and extraction tools" from the site license and forbids commercial reproduction without written consent — the only host in this set with a flat robots prohibition in prose, and this is unambiguously a commercial product. Robots.txt affirmatively permits these exact paths, but a permissive robots.txt is crawl etiquette, not a license grant: it mitigates CFAA-style unauthorized-access theories, not the contract/license theory that is the operative risk here, and it cannot enlarge the scope of a license whose text expressly excludes robots. The AUP (which also governs the AWS Site and is the more recent, conduct-focused document) prohibits nothing we do; the pages are public and non-authenticated; published output would be diff metadata plus minimal quoted excerpts (quotation for reporting, not reproduction of "the AWS Site or any portion" in a substitutive sense); verbatim copies would stay private as evidence — but given the express exclusion and the commercial-use posture, the presumption runs against direct fetching, not for it. Browsewrap robots-prohibitions of this vintage are of doubtful enforceability against robots.txt-compliant, non-disruptive access to public pages, but the textual conflict is real; direct fetching is gated behind counsel sign-off, and Wayback-snapshot diffing is the default plan of record (see conditions below).

**Verdict: CONDITIONAL.**
Conditions (default flipped per verifier dissent item 2 — Wayback is the plan of record; direct fetch is the gated exception): (1) **default plan of record is diffing Internet Archive (Wayback) snapshots of the two registry-tracked aws.amazon.com content pages — `https://aws.amazon.com/service-terms/` (`aws-service-terms`, §1 row 7) and `https://aws.amazon.com/aup/` (`aws-aup`, §1 row 8)** — no direct fetching of aws.amazon.com at Phase 0. (The Site Terms at `https://aws.amazon.com/terms/`, quoted above for the crawl-permission analysis, is *not* a registry-tracked content row and is not diffed for `policy.changed`; its clause-stability is covered by the `aws.md` carve-out sentinel and the quarterly re-sweep, not by this condition.) (2) direct fetching may be enabled ONLY on affirmative counsel sign-off (silence, non-response, or ambiguity does not authorize direct fetch) — highest-priority review item in this file; (3) send a written notice/consent request to AWS (abuse/legal contact) describing TheLLMReportBot, cadence, and purpose — non-response does not equal consent but documents good faith, and does not by itself unlock direct fetching; (4) if and only if counsel authorizes direct fetching: weekly conditional GETs only, never hourly, for aws.amazon.com paths; (5) published excerpts strictly minimal (headline + changed sentence fragments), never section-scale reproduction, no framing — applies to both Wayback-sourced and (if authorized) direct-sourced content; (6) standing conditions (robots re-check, identified UA, 403/429 = stop) apply if and when direct fetching is ever authorized.

---

### 2.6 www.microsoft.com

**Governing document:** **Microsoft Terms of Use** — https://www.microsoft.com/en-us/legal/terms-of-use — Last updated Feb 7, 2022 — fetched 2026-07-07.

Scope (verbatim, preamble):
> "Through its network of Web properties, Microsoft provides you with access to a variety of resources, including developer tools, download areas, communication forums and product information (collectively 'Services')."

Access/automation clauses (verbatim, "No Unlawful or Prohibited Use" / membership-services conduct list):
> "You may not attempt to gain unauthorized access to any Services, other accounts, computer systems or networks connected to any Microsoft server or to any of the Services, through hacking, password mining or any other means."
> "Harvest or otherwise collect information about others, including e-mail addresses."

AI-services clause (verbatim, AI Services section — governs Microsoft's AI services, not ordinary web pages):
> "You may not use web scraping, web harvesting, or web data extraction methods to extract data from the AI services."

Republication clause (verbatim, "Notice Specific to Software/Documents Available on this Web Site" family):
> "You may not modify, copy, distribute, transmit, display, perform, reproduce, publish, license, create derivative works from, transfer, or sell any information, software, products or services obtained from the Services."

Tracked-document note: the Product Terms content itself contains (verbatim, Universal License Terms for Online Services → Microsoft Generative AI Services, heading **"Extracting Data"**): "Customer may not use web scraping, web harvesting, or other data extraction methods to extract data from a Microsoft Generative AI Service." — a clause about the licensed services, not about fetching the Product Terms page; recorded here because it is exactly the kind of clause our diffs will report on.

**robots.txt** (https://www.microsoft.com/robots.txt, fetched 2026-07-07): `User-agent: *` with numerous disallows; the only licensing-related rule is `Disallow: /rus/licensing/Unilateral.aspx/*`. Our path `/licensing/terms/product/ForOnlineServices/all` is **allowed** (verified by direct inspection).

**Analysis:** Microsoft's ToU contains no general anti-bot/anti-crawl clause; the harvesting clause targets personal information, the unauthorized-access clause targets hacking, and the scraping clause is expressly limited to "the AI services." The operative friction is the broad no-reproduce/no-publish clause, addressed by our minimal-excerpt + private-archive design (quotation for change reporting, not republication of the document). The Product Terms page is public, unauthenticated, and robots-allowed. Note Microsoft publishes the Product Terms specifically so customers can track licensing changes; monthly archived editions exist on the same site, which supports the legitimacy of change tracking.

**Verdict: CONDITIONAL.**
Conditions: (1) minimal excerpts only; never republish section-scale Product Terms text; (2) standing conditions (robots re-check, identified UA, conditional GETs, 403/429 = stop); (3) verify whether www.microsoft.com is already cleared in another sweep file and reconcile verdicts (this path may be unique to this file).

---

### 2.7 legal.mistral.ai — NEW HOST (flag; discovered via redirect)

**Discovery:** `https://mistral.ai/terms` → **301** → `https://legal.mistral.ai/terms` (observed 2026-07-07). The legal center hub page is "Effective: November 28, 2025". Document URLs on this host: `/terms/commercial-terms-of-service` (Effective May 28, 2026), `/terms/usage-policy` (Effective Jun 11, 2026), `/terms/eu-consumers-terms-of-service`, `/terms/row-consumer-terms`, `/terms/additional-terms`, `/terms/data-processing-addendum`, `/terms/privacy-policy`, `/terms/cookie-policy`, `/terms/license-notice`, `/legal-notice`, and others.

**Governing document:** There is **no website terms-of-use** for this host. The only site-governing document is the French-law **Legal Notice** — https://legal.mistral.ai/legal-notice — fetched 2026-07-07 (verbatim, "Editor"):
> "In accordance with the provisions of article 6(I) (1) of law no. 2004-575 of 21 June 2004 on confidence in the digital economy, the publisher of the website https://legal.mistral.ai/ is: Mistral AI, a simplified joint stock company with capital of EUR 15,000 … The company tasked with hosting the https://legal.mistral.ai/ website is Netlify, Inc."

It contains publisher identification only — no usage restrictions, no scraping clause.

Product-terms scope check (ROW Consumer Terms of Service, fetched 2026-07-07, verbatim preamble): "These Terms of Service (these 'Terms') govern your personal use as a consumer outside of the EEA of Mistral AI Studio, Vibe and the other websites, products, software, services, and technologies we offer (the 'Mistral AI Products')." — governs consumers using Mistral products; no anti-crawl clause found in the document relevant to reading public legal pages.

**robots.txt** (https://legal.mistral.ai/robots.txt, fetched 2026-07-07): `User-agent: *` / `Allow: /` — fully permissive. Origin host mistral.ai robots.txt (fetched 2026-07-07): `User-agent: *` / `Allow: /` / `Sitemap: https://mistral.ai/sitemap-index.xml` — also fully permissive.

**Analysis:** No contractual restriction on automated access to this host exists at all; robots.txt is fully permissive on both the legal host and the redirect origin; French Legal Notice imposes no conduct terms. The hub page exposes an "Effective:" date and a "Versions" archive per document — ideal for change intelligence. EU database-right/copyright still counsels minimal excerpts, which is already our design.

**Verdict: CLEAR.**
Conditions: standing program conditions only; watch for a future ToU appearing on this host (the legal center is new and actively versioned).

---

### 2.8 x.ai

**Governing documents:**
1. **xAI Terms of Service (consumer)** — https://x.ai/legal/terms-of-service — Effective Jun 26, 2026 — fetched 2026-07-07 (200 with production UA; 403 to generic client).
2. **xAI Acceptable Use Policy** — https://x.ai/legal/acceptable-use-policy — Effective Jun 26, 2026 — fetched 2026-07-07.

ToS scope (verbatim, preamble):
> "These Terms of Service ('Terms') apply to your or others' access, interactions and/or use of Grok, Grokipedia, and xAI's other services for individuals, including associated applications, features, tools, software and websites (collectively, the 'Service'). … By accessing and using our Service, you acknowledge and agree to these Terms and any other applicable terms and policies, including our Acceptable Use Policy."

AUP scope (verbatim, preamble): "xAI's Acceptable Use Policy ('AUP') applies to anyone using our Service, including consumers, developers and businesses."

AUP automated-access / scraping / circumvention clauses (verbatim, under "Comply with the law … Detrimentally impacting the Service, including by:"):
> "Modifying, copying, translating, leasing, selling, reselling, distributing, distilling, manipulating, using bots to access, reverse engineer, decompile, disassemble or otherwise seek to obtain the source code of our Service …"
> "Scraping, harvesting or reselling any Input or Output, or distilling model data or Outputs"
> "Disrupting, interfering with, or unauthorized access to the Service or its safety systems, including circumventing any rate limits or restrictions or protective measures and safety mitigations"

and (under the misleading-use bullet list):
> "Accessing the Services through automated or non-human means, whether through a bot, script, or otherwise"

**robots.txt** (https://x.ai/robots.txt, fetched 2026-07-07, verbatim):
```
User-agent: *
Allow: /
Disallow: /tools/

User-agent: GPTBot
User-agent: ChatGPT-User
User-agent: PerplexityBot
User-agent: ClaudeBot
User-agent: Google-Extended
User-agent: Applebot-Extended
Allow: /
Disallow: /tools/

Sitemap: https://x.ai/sitemap.xml

# Content Signals (draft) — declare AI/search usage preferences
# See: https://contentsignals.org/
Content-Signal: ai-train=no, search=yes, ai-input=no
```
Our paths under `/legal/` are **allowed** for all agents, including named AI crawlers.

**Bot-wall observation (amended per verifier dissent item 3):** 403 to a generic fetch client; 200 to `TheLLMReportBot/1.0` (2026-07-07). As at §2.1: 403/429 to our identified UA is treated as revocation regardless of cause, but a 200 to our UA is not evidence of admission or authorization — the wall has simply not classified/blocked it. A wall that specifically 403s a generic client on these legal pages is affirmative evidence of intent to restrict automated access to exactly these pages, which cuts against, rather than reinforces, the robots.txt counterweight discussed below.

**Analysis (revised per verifier dissent items 1 and 3):** The AUP prose ("using bots to access", "accessing the Services through automated or non-human means") facially conflicts with a robots.txt that affirmatively allows all crawlers — including, by name, AI bots — on these paths; per the bot-wall observation above, that robots.txt counterweight is itself weakened by the targeted 403-to-generic-client behavior, not simply reinforced by the Allow-all rule. The AUP bullets read as product-conduct rules (they sit in lists about jailbreaking, distillation, scraping Inputs/Outputs), but the text is broad enough to cover us. **Content-Signal compliance:** `search=yes` covers fetch-index-monitor uses like ours; `ai-train=no` is irrelevant (we never train on collected content); `ai-input=no` matters — x.ai page content must NOT be fed to LLMs in our pipeline. This business is agent-operated end-to-end — LLM agents curate the tracker, draft the weekly diff email, and write paid alerts; the owner is a legal/financial principal only, not an operational reviewer — so there is no human in the loop who could safely absorb an x.ai excerpt, and this file no longer relies on "human review where judgment is needed" as a safety valve. Diffs for this host must instead be produced and published by a fully deterministic code path end-to-end — collection through drafting and QA — with no agent ever receiving x.ai page text (including headings or excerpts) as input at any stage, unless and until xAI grants written consent.

**Verdict: CONDITIONAL** (degrades to **EXCLUDE pending xAI's written consent** if condition (1) below cannot be architected by Phase 0 — verifier dissent item 1).
Conditions: (1) the `ai-input=no` boundary applies end-to-end, not just at collection: excerpt selection is by deterministic diff algorithm (changed-sentence extraction, fixed truncation) and rendering into site/email/alerts is templated; no agent (LLM) may receive x.ai page text — including headings or excerpts — as input at any pipeline stage, including QA; agents may handle only self-generated metadata (URL, timestamp, hash, section anchor, change-type enum); flag this constraint in the collector config for this host; (2) 403/429 to our UA = revocation → stop, fall back to Internet Archive; (3) minimal excerpts public, verbatim archive private; (4) standing conditions (robots re-check each run, identified UA, conditional GETs); (5) counsel review of the AUP bot clauses alongside the AWS review; (6) counsel sign-off AND a documented good-faith notice to xAI's legal/abuse contact (describing TheLLMReportBot, cadence, and purpose) are required before any direct Phase 0 activation of x.ai fetching — independent of condition (1)'s deterministic ai-input=no pipeline requirement (synced with §4 class-wide condition 10).

---

## 3. Extraction hints (registry `extract` field per source)

| Source | Hint |
|--------|------|
| `openai-usage-policies` | Next.js, content server-rendered in initial HTML. Anchor: `h1` title + literal line `Effective: <Month D, YYYY>` near top (with "(Previous version)" link). Strip global nav/footer; diff main article only. |
| `openai-services-agreement` | Same template. Follow the 307 from `/policies/business-terms/`; alert if redirect target changes. `Updated:` and `Effective:` lines both present; numbered sections `1.`, `1.1.`, `a.` |
| `anthropic-usage-policy` | Next.js server-rendered. `h1` "Usage Policy"; effective-date line near top; three main parts (Universal Usage Standards / High-Risk Use Case Requirements / Additional Use Case Guidelines). |
| `anthropic-commercial-terms` | Same template; lettered sections A–M with decimal subsections (A.1, A.2 …); effective-date line near top. |
| `google-genai-prohibited-use` | Plain, stable static HTML (policies.google.com template). `h1` + "Last updated" line; four numbered prohibition categories with lettered sub-items. Smallest, most stable page in the class. No robots.txt on host. |
| `google-apis-tos` | Google DevSite template, server-rendered `<article>`; "Last modified" line at top; stable `Section N:` headings 1–10. Ignore DevSite chrome/sidebars. |
| `aws-service-terms` | Very large single HTML page (hundreds of KB), 26 numbered sections, `h2` per section, decimal subsections; "Last updated: <date>" near top. Conditional GET essential; diff by section anchor to keep `policy.changed` events granular. |
| `aws-aup` | Short static page; "Last Updated: July 1, 2021" line; flat bullet list + "Investigation and Enforcement" / "Reporting of Violations" headings. |
| `ms-product-terms-online-services` | Despite SPA chrome, the Universal License Terms content IS present in the raw HTML (verified: "Extracting Data" `h4` and body text server-rendered). Strip UHF header/footer (`uhf.microsoft.com` includes) and analytics; the visible "Effective Date:" field is client-populated — do not diff it; diff the main terms container. URL params select program/edition; monthly archived editions exist for validation. |
| `mistral-commercial-tos` / `mistral-usage-policy` | Netlify-hosted, server-rendered. Anchor: literal `Effective:<Month D, YYYY>` line + `h1`; per-document "Versions" archive link on page — poll it for validation. Sidebar nav lists all legal docs; diff main content only. |
| `xai-tos` / `xai-aup` | Next.js server-rendered; `h1` + `Effective: <Month D, YYYY> (previous version)` line. REQUIRES identified UA (403 to generic clients). Marketing nav noise at top; diff main legal body. Deterministic pipeline only (Content-Signal `ai-input=no`). |

---

## 4. Overall verdict for source class `policy-page`

**CONDITIONAL.** No host is excluded, subject to the x.ai contingency below. Three hosts are CLEAR (policies.google.com, developers.google.com — Google contractually keys permission to robots.txt, which permits us; legal.mistral.ai also CLEAR with no restrictive terms at all). Five hosts are CONDITIONAL: openai.com (broad anti-automation prose; per verifier dissent item 3, a bot wall that specifically 403s generic clients on these ToU pages weakens rather than reinforces the robots.txt counterweight — see §2.1; standard mitigations suffice), www.anthropic.com (broad anti-automation prose; per verifier dissent item 4 the verdict rests on weak browsewrap assent, non-disruptive revocation-honoring access, and minimal quotation — NOT on robots.txt as "explicit permission" — see §2.2), www.microsoft.com (republication clause; minimal excerpts), and two hosts where direct fetching is gated: **aws.amazon.com** (Site Terms expressly exclude "data mining, robots, or similar data gathering and extraction tools" and commercial reproduction; per verifier dissent item 2, Wayback-snapshot diffing is now the default plan of record, with direct fetching enabled only by affirmative counsel sign-off) and **x.ai** (AUP anti-bot prose + Content-Signal `ai-input=no`; per verifier dissent item 1, `ai-input=no` compliance must extend end-to-end through every pipeline stage — no agent may ever receive x.ai page text as input — and this host degrades to EXCLUDE, not CONDITIONAL, if that fully deterministic pipeline cannot be architected by Phase 0).

Class-wide binding conditions (import into collector config):
1. Identified UA `TheLLMReportBot/1.0 (+https://thellmreport.com/bot)` on every request; never rotate or disguise.
2. robots.txt fetched and re-evaluated every run, per host; treat new disallows or Content-Signals as immediately binding.
3. Conditional GETs (ETag / If-Modified-Since), weekly cadence for this class, exponential backoff, single concurrent connection per host.
4. HTTP 403/429 addressed to our UA = permission revoked → halt host, alert, fall back to Internet Archive snapshots; never retry around a block.
5. Published output: diff metadata + minimal verbatim excerpts with attribution; full verbatim page archives remain private (sha256 manifests public).
6. x.ai only (amended per verifier dissent item 1): `ai-input=no` applies end-to-end — collection, excerpt selection (deterministic changed-sentence extraction, fixed truncation), templated rendering into site/email/alerts, and QA; no agent (LLM) may ever receive x.ai page text, including headings or excerpts, as input at any stage; agents may handle only self-generated metadata (URL, timestamp, hash, section anchor, change-type enum). If this fully deterministic pipeline cannot be architected by Phase 0, x.ai degrades from CONDITIONAL to **EXCLUDE pending xAI's written consent**.
7. aws.amazon.com (amended per verifier dissent item 2): Wayback-snapshot diffing of the registry-tracked pages `https://aws.amazon.com/service-terms/` (`aws-service-terms`, §1 row 7) and `https://aws.amazon.com/aup/` (`aws-aup`, §1 row 8) is the default plan of record; direct fetching of aws.amazon.com is suspended until counsel affirmatively signs off (silence/non-response does not authorize it), plus a documented good-faith notice to AWS's abuse/legal contact. (The Site Terms `https://aws.amazon.com/terms/` is the crawl-permission legal basis, not a tracked content row — see §2.5.)
8. developers.google.com: CC BY 4.0 attribution on quoted content.
9. New-host watch: any future redirect of a registry URL to an uncleared host suspends that source until a clearance addendum is filed (this sweep caught mistral.ai → legal.mistral.ai).
10. x.ai (synced with §2.8 condition (6)): counsel sign-off + a documented good-faith notice to xAI's legal/abuse contact required before any direct Phase 0 activation of x.ai fetching, independent of condition 6 above (the `ai-input=no` deterministic-pipeline requirement).

*All fetches 2026-07-07. Verification methods: HTTPS GET with production UA (curl) + secondary generic fetch client; OpenAI and xAI hosts returned 403 to the generic client and 200 to the production UA — recorded, not bypassed. Raw HTML evidence captured during sweep; import verbatim archives at Phase 0.*

---

## Verifier dissent (2026-07-07)

**Amendments applied 2026-07-08** - every required change below is folded into the body above; import-ready.

Independent adversarial re-verification, generic-client UA only (no production-UA use by the verifier), 2026-07-07.

**What was re-verified and confirmed accurate:**
- **AWS Site Terms** (https://aws.amazon.com/terms/) re-fetched: "Last updated June 4, 2025" confirmed; both load-bearing quotes — "use of data mining, robots, or similar data gathering and extraction tools" and "may not be reproduced, duplicated, copied, sold, resold, visited, or otherwise exploited for any commercial purpose without express written consent" — verbatim and current. §2.5's quotes are real, not stale.
- **Anthropic Consumer Terms** re-fetched: Effective October 8, 2025 confirmed; the crawl/scrape clause and the automated-access clause (with API-key / "where we otherwise explicitly permit it" carve-outs) verbatim.
- **robots.txt re-fetched raw** on openai.com, x.ai (Content-Signal line `ai-train=no, search=yes, ai-input=no` verbatim), www.anthropic.com, developers.google.com, www.microsoft.com, legal.mistral.ai — all match §2 transcriptions. policies.google.com/robots.txt HTTP 404 confirmed. aws.amazon.com/robots.txt pulled in full (309 lines): `Disallow: /s/*` exists but under RFC 9309 prefix matching does not match `/service-terms/`; no rule matches `/service-terms/`, `/aup/`, or `/terms/`. §2.5's path-allowed claim holds.
- **openai.com** returned 403 to the verifier's generic client, consistent with §2.1. The "Automatically or programmatically extract data or Output" clause was verified as current OpenAI ToU language via secondary corroboration (OpenAI ROW/EU ToU variants and third-party quotations); the canonical `/policies/services-agreement/` URL confirmed live. **The Jan 1, 2026 effective date of the ToU was NOT independently verifiable** (403 wall; archive service unavailable to verifier) — the sweep's private raw-HTML capture is the sole evidence for that date and must be in the sha256 manifest at Phase 0 import.

**Dissent — the following must change. The class verdict remains CONDITIONAL only if amendments 1–4 are adopted; otherwise x.ai must be EXCLUDE.**

1. **x.ai condition 6 is not satisfiable as written by this business, and the file does not confront that.** The condition confines `ai-input=no` compliance to "the collector config" and a "deterministic diff pipeline," and §2.8 leans on "human review where judgment is needed." But The LLM Report is agent-operated end-to-end: LLM agents curate the tracker, draft the weekly diff email, and write paid alerts. Any agent that reads an x.ai excerpt — even a "minimal quoted excerpt" — to draft copy has fed x.ai page content to an LLM, breaching the compliance posture this file itself declares binding (class condition 2 treats Content-Signals as immediately binding). There is no human in the operational loop; the owner is a legal/financial principal only. **Required amendment:** extend the `ai-input=no` boundary to every pipeline stage, not just collection — x.ai items must follow a fully deterministic path end-to-end: excerpt selection by the diff algorithm (changed-sentence extraction, fixed truncation), templated rendering into site/email/alerts, and no agent ever receiving x.ai page text (including headings and excerpts) as input at any stage including QA. Agents may handle only self-generated metadata (URL, timestamp, hash, section anchor, change-type enum). If this cannot be architected by Phase 0, **x.ai is EXCLUDE pending xAI's written consent**, not CONDITIONAL.
2. **aws.amazon.com: flip the default.** §2.5 conditions read as "direct fetch at Phase 0, provided counsel signs off." Given the only verified-current flat robots prohibition in the class plus an express ban on *any* commercial use without written consent — and this is unambiguously a commercial product — the presumption must run the other way: **Wayback-snapshot diffing is the default plan of record for aws.amazon.com; direct fetching is enabled only by affirmative counsel sign-off** (and ideally AWS's response to the good-faith notice). Note also the analysis overweights robots.txt: a permissive robots.txt is crawl etiquette and cannot enlarge the scope of a license grant whose text excludes robots; it mitigates CFAA-style access theories, not the contract/license theory, which is the operative risk here.
3. **Strike or reword the bot-wall framing in §2.1/§2.8** ("active bot management … currently admits our identified UA"). A 200 to an unrecognized UA means the wall has not classified it, not that the operator admitted it; no permission inference may be drawn from it at Phase 0. Worse, a bot wall that 403s generic clients on the ToU pages themselves is affirmative evidence of intent to restrict automated access to exactly these pages, which *cuts against* the robots.txt counterweight for openai.com and x.ai. Verdicts stand (revocation semantics are correct), but the record must not read as if passage = permission.
4. **Anthropic (§2.2): drop the "robots.txt as explicit permission" argument.** An `Allow: /` default is generic, not the "explicit" permission the Consumer Terms carve-out contemplates; a reviewing court would not equate them. The CONDITIONAL verdict survives on the defensible grounds already present (weak browsewrap assent for non-authenticated public pages, non-disruptive revocation-honoring access, minimal quotation) — rely on those, not on a strained carve-out reading.
5. **Recorded gaps (no verdict change):** (a) OpenAI maintains regional ToU variants (`/policies/row-terms-of-use/`, `/policies/eu-terms-of-use/`) not examined by this sweep; the extract-data clause appears in all variants, but the registry should record which variant governs the operator and watch all three for divergence. (b) `/policies/terms-of-use/` may itself be geo-routed — the private evidence capture should record the serving variant.

**Verifier verdict: CONDITIONAL, with the four amendments above incorporated as binding class conditions. x.ai degrades to EXCLUDE if amendment 1 is not implemented before Phase 0.**
