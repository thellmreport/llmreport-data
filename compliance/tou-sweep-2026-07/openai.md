# ToU Clearance — developers.openai.com

- **Sweep:** tou-sweep-2026-07 (design-phase legal deliverable, V-Q3 cond. 9)
- **Host-set:** `developers.openai.com` — target paths `/api/docs/models`, `/api/docs/changelog`
- **Research date:** 2026-07-07 (UTC)
- **Verdict:** **CONDITIONAL** (see §6)
- **Scope note:** `openai.com` itself is already on the exclusion list (403 WAF). This clearance covers ONLY `developers.openai.com`.

---

## 1. Governing documents

| # | Document | URL | Version date | How sourced | Fetch date |
|---|----------|-----|--------------|-------------|------------|
| 1 | developers.openai.com pages (footer legal link) | https://developers.openai.com/api/docs/models , https://developers.openai.com/api/docs/changelog | live | **Direct fetch, HTTP 200** (no bot wall; served 200 to UA `TheLLMReportBot/1.0`) | 2026-07-07 |
| 2 | OpenAI **Terms of Use** | https://openai.com/policies/terms-of-use/ | Published: January 1, 2026; Effective: January 1, 2026 | **Indirect** — direct fetch returned **HTTP 403** (WAF); sourced from Wayback Machine snapshot `20260705183726` (captured 2026-07-05), `http://web.archive.org/web/20260705183726/https://openai.com/policies/terms-of-use/` | 2026-07-07 |
| 3 | OpenAI **Services Agreement** (business-side governing document; supersedes the Business Terms as of 2026-01-01) | https://openai.com/policies/services-agreement/ | "Updated: December 1, 2025"; "Effective: January 1, 2026" | **Indirect** — openai.com is WAF-excluded for direct fetch (see scope note); sourced from Wayback snapshot `20260702193921` (captured 2026-07-02, HTTP 200) | 2026-07-07 |
| 4 | OpenAI **Business Terms** (SUPERSEDED by doc 3 effective 2026-01-01 — retained as historical context only, see §3.6) | https://openai.com/policies/business-terms/ | "Updated: November 14, 2023" | **Indirect** — direct fetch 403; latest HTTP-200 Wayback capture is `20250519024110` (2025-05-19; all newer captures are 403). Confirmed superseded (dissent D.2). | 2026-07-07 |
| 5 | OpenAI **Sharing & Publication Policy** (incorporated by ToU "What you can do" clause, §2.6; checked — not adverse to crawling) | linked from https://openai.com/policies | "Updated: November 14, 2022" | **Indirect** — Wayback snapshot `20260626093648`; governs sharing/publication of AI-generated content and model Output, not website crawling or republication of docs pages (dissent D.1) | 2026-07-07 |
| 6 | OpenAI **Usage Policies** (incorporated by ToU, §2.6; NOT yet archived) | https://openai.com/policies/usage-policies/ | — | **Not archived** — no HTTP-200 Wayback capture as of 2026-07-06; low relevance to crawling (they govern model use); locate, quote, and archive at Phase 0 (condition 7) | — |
| 7 | EU/EEA variant (noted, not analyzed) | https://openai.com/policies/eu-terms-of-use/ ; ROW variant at /policies/row-terms-of-use/ | — | Wayback snapshots exist (2026-07-02 / 2026-07-05) | 2026-07-07 |

**Which document governs the website (amended per dissent D.4):** `developers.openai.com` has no site-specific terms of its own. Its footer (verified in live HTML on 2026-07-07; re-confirmed by the verifier) contains a single legal link, text **"Terms and policies"** → `https://openai.com/policies`. The consumer Terms of Use (doc 2) defines its scope to include OpenAI websites (quoted below), but it also carves out: "Our Business Terms govern use of ChatGPT Enterprise, our APIs, and our other services for businesses and developers" — and the successor Services Agreement (doc 3) applies to "other services for customers who are businesses and developers" and defines "Services" to expressly include OpenAI's associated "documentation, and websites" (§3.3 below). A developer documentation website is therefore at least arguably a developer-facing service whose associated website falls under the Services Agreement, not (only) the consumer ToU — and the Services Agreement is the document OpenAI would actually sue under where the operating entity holds an OpenAI account (see §5.1 and condition 8). Both documents contain an anti-extraction clause, so the verdict does not turn on this classification.

---

## 2. Verbatim clauses — OpenAI Terms of Use (Effective January 1, 2026)

Source: Wayback snapshot 2026-07-05 of https://openai.com/policies/terms-of-use/ (indirectly sourced; live page 403s automated fetch). The document uses named headings, not section numbers; heading names are given as section ids.

### 2.1 Scope (introduction, unnumbered)

> "These Terms of Use apply to your use of ChatGPT, DALL·E, and OpenAI’s other services for individuals, along with any associated software applications and websites (all together, “Services”). These Terms form an agreement between you and OpenAI OpCo, LLC, a Delaware company, and they include our Service Terms and important provisions for resolving disputes through arbitration. By using our Services, you agree to these Terms."

> "Our Business Terms govern use of ChatGPT Enterprise, our APIs, and our other services for businesses and developers."

### 2.2 "Using our Services" → "What you cannot do" (automated access / scraping)

> "What you cannot do. You may not use our Services for any illegal, harmful, or abusive activity. For example, you may not:
> - Use our Services in a way that infringes, misappropriates or violates anyone’s rights.
> - Modify, copy, lease, sell or distribute any of our Services.
> - Attempt to or assist anyone to reverse engineer, decompile or discover the source code or underlying components of our Services, including our models, algorithms, or systems (except to the extent this restriction is prohibited by applicable law).
> - **Automatically or programmatically extract data or Output (defined below).**
> - Represent that Output was human-generated when it was not.
> - **Interfere with or disrupt our Services, including circumvent any rate limits or restrictions or bypass any protective measures or safety mitigations we put on our Services.**
> - Use Output to develop models that compete with OpenAI."

(Emphasis added; bullet text verbatim.)

### 2.3 "Our IP rights" (reproduction / republication)

> "We and our affiliates own all rights, title, and interest in and to the Services. You may only use our name and logo in accordance with our Brand Guidelines."

### 2.4 "Copyright complaints" (takedown channel)

> "If you believe that your intellectual property rights have been infringed, please send notice to the address below or fill out this form. We may delete or disable content that we believe violates these Terms or is alleged to be infringing…"
>
> OpenAI OpCo, LLC, 1455 3rd Street, San Francisco, CA 94158, Attn: General Counsel / Copyright Agent

### 2.5 Governing law ("General Terms")

> "Governing law. California law will govern these Terms except for its conflicts of laws principles."

### 2.6 "Using our Services" → "What you can do" (incorporated policies; added per dissent D.1/D.6.5)

> "you must comply with all applicable laws as well as our Sharing & Publication Policy, Usage Policies, and any other documentation, guidelines, or policies we make available to you."

(Excerpt.) This clause is the incorporation hook for the Sharing & Publication Policy (doc 5 — checked, not adverse to crawling) and the Usage Policies (doc 6 — not yet archived; Phase 0 item under condition 7).

---

## 3. Verbatim clauses — OpenAI Services Agreement ("Updated: December 1, 2025"; "Effective: January 1, 2026"; Wayback `20260702193921`)

*Section replaced per verifier dissent D.2/D.6.1 (2026-07-08). Prior revisions of this file quoted the OpenAI Business Terms here; OpenAI replaced the Business Terms with this Services Agreement, effective the same date as the new consumer ToU. Source: Wayback snapshot `20260702193921` of https://openai.com/policies/services-agreement/ (captured 2026-07-02, HTTP 200; fetched 2026-07-07). This is the business-side document OpenAI would enforce against an account-holding entity (see §5.1 and condition 8). The superseded Business Terms are retained as historical context in §3.6.*

### 3.1 Scope

> "This OpenAI Services Agreement only applies to use of OpenAI's APIs, ChatGPT Enterprise, ChatGPT Business, ChatGPT for Clinicians, and other services for customers who are businesses and developers, and does not apply to OpenAI services used by consumers or individuals unless specified above."

### 3.2 Assent

> "By clicking "I agree," accepting the Order Form, **or using the Services**, Customer agrees to this Agreement."

(Emphasis added.) Assent attaches by click-through, Order Form, **or use** — broader than the old Business Terms' "By signing up" mechanism. Because our company separately holds API accounts, the operating entity has plausibly already assented; see §5.1 and binding condition 8.

### 3.3 "Services" definition

> ""Services" means OpenAI's services for businesses, enterprises, or developers made available for purchase or use in Customer's Account, along with any of OpenAI's associated software, tools, developer services, **documentation, and websites**, but excluding any Third-Party Service."

(Emphasis added.) A developer documentation website is squarely within the defined term.

### 3.4 §3.3 Restrictions (excerpt)

> "Customer will not, and will not permit End Users to: […] (f) **extract data from the Services other than as permitted through the Services**; (g) buy, sell, or transfer API keys from, to, or with a third party; (h) interfere with or disrupt the Services, including circumvent any rate limits or restrictions or bypass any protective measures or safety mitigations for the Services; […]"

(Emphasis added.)

### 3.5 §14.1 Limitation on Indirect Liability (carve-out)

> "TO THE FULLEST EXTENT PERMITTED BY LAW, EXCEPT FOR: (A) A PARTY'S GROSS NEGLIGENCE OR WILLFUL MISCONDUCT; **(B) CUSTOMER'S BREACH OF SECTION 3.3 (RESTRICTIONS)**; […] NEITHER CUSTOMER NOR OPENAI OR EITHER PARTY'S AFFILIATES OR LICENSORS WILL BE LIABLE UNDER THIS AGREEMENT FOR ANY INDIRECT, PUNITIVE, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR EXEMPLARY DAMAGES […]"

(Emphasis added.) Restriction breaches — including §3.3(f) — are carved out of the indirect-damages waiver.

### 3.6 Historical context only — superseded Business Terms ("Updated: November 14, 2023"; Wayback `20250519024110`, 2025-05-19)

The old Business Terms page itself links "View upcoming services agreement" — a successor signal the original sweep missed (dissent D.2). Former §2 "Restrictions" (excerpt), retained for the record:

> "We own all right, title, and interest in and to the Services. You only receive rights to use the Services as explicitly granted in this Agreement. You will not, and will not permit End Users to: […]
> **(f) use any method to extract data from the Services other than as permitted through the APIs;** or
> (g) buy, sell, or transfer API keys from, to or with a third party."

The old Business Terms also defined Services with materially identical breadth ("along with any of our associated software, tools, developer services, documentation, and websites") — language the original §3 did not quote. **Superseded note:** this file previously reasoned that the Business Terms "bind by sign-up" and therefore "do not bind the collector's website visits." That reasoning is superseded (dissent D.2/D.3): the operative assent mechanism is now the Services Agreement's §3.2 ("or using the Services"), and contracts bind the legal entity, not the collector process — our company separately holds API accounts. See §5.1 and condition 8.

---

## 4. robots.txt findings — developers.openai.com

Fetched directly 2026-07-07 (UTC) with UA `TheLLMReportBot/1.0 (+https://thellmreport.com/bot)` → **HTTP 200**. Complete verbatim contents:

```
User-agent: *
Allow: /

Sitemap: /sitemap-index.xml
```

Relevant response headers: `Server: Vercel`, `Etag: "e7f089df4e5b960af1bf865e870dcc75"`, `Last-Modified: Mon, 06 Jul 2026 23:18:38 GMT` (file changed the day before this sweep — must be re-checked each cycle).

**Path check:**

| Path | robots.txt result | Live fetch w/ our UA (2026-07-07) |
|------|-------------------|-----------------------------------|
| `/api/docs/models` | **Allowed** (`User-agent: *` / `Allow: /`, no Disallow rules exist) | HTTP 200, 43,313 bytes |
| `/api/docs/changelog` | **Allowed** (same) | HTTP 200, 52,431 bytes |

No `<meta name="robots">` restriction found in the `/api/docs/models` HTML. A sitemap index is published — an affirmative crawl signal. No bot wall, CAPTCHA, or WAF challenge encountered on any developers.openai.com fetch (unlike openai.com, which 403s and stays excluded).

---

## 5. Analysis

1. **Formation analysis (amended per dissent D.3 — the browsewrap shield holds only under entity separation).** For a fetcher whose operating entity has no OpenAI contractual relationship, the Terms of Use attach only by "By using our Services, you agree" — classic browsewrap. Under prevailing US case law, browsewrap terms are weakly enforceable against visitors who never manifested assent, particularly for publicly available pages (cf. hiQ v. LinkedIn line on public data; contrast Register.com v. Verio where continued use with actual knowledge mattered — we now have actual knowledge, which is why this is CONDITIONAL, not CLEAR). **However, contracts bind legal persons, not processes.** Our company separately holds API accounts (§3.6), so the operating entity has plausibly already assented — by click-through or by "using the Services" (§3.2) — to the Services Agreement, whose defined "Services" expressly include OpenAI's developer "documentation, and websites" (§3.3) and whose §3.3(f) prohibits extracting data from them other than as permitted through the Services (§3.4). The collector is that entity's instrumentality; condition 2 ("no account in the collector path") is process hygiene and does not sever contract privity. On these facts the applicable adverse clause is plausibly a **clickwrap-bound §3.3(f)**, not a weak browsewrap — the hiQ-style framing above survives only if collection is placed under an entity with no OpenAI contractual relationship (binding condition 8). Counterarguments preserved for the record (dissent D.3): the Services definition ties to what is "made available for purchase or use in Customer's Account"; OpenAI would still need to show damages; robots.txt allow-all and public availability cut against materiality of breach. These reduce, but do not eliminate, the exposure.
2. **The adverse clauses are real.** "Automatically or programmatically extract data or Output" (§2.2 above), read literally, covers hourly programmatic polling of docs pages. "Modify, copy … or distribute any of our Services" touches republication. For a bound Customer, the Services Agreement carries parallel restrictions: §3.3(f) (extract data other than as permitted through the Services) and §3.3(h) (interfere/circumvent) — see §3.4.
3. **The technical signals cut the other way.** robots.txt affirmatively allows all user-agents on all paths and publishes a sitemap; the server returned 200 to our *identified* bot UA. A maximalist reading of the ToU clause (no automated fetches ever) is contradicted by OpenAI's own machine-readable access policy for this host.
4. **Our conduct minimizes the residual risk.** No login, no assent-clicks, no rate-limit or bot-wall circumvention (none exists here to circumvent), conditional GETs (server supplies ETags), single identified UA with contact URL. Republication is limited to uncopyrightable facts (model names, prices, dates, deprecations) plus minimal quoted excerpts under fair-use quotation; verbatim archives stay private as evidence.
5. **Worst realistic outcome (amended per dissent D.2/D.6.3).** For an unbound visitor, the worst realistic outcome is a UA/IP block or a cease-and-desist; cease-on-demand posture caps that exposure. For a bound Customer (see §5.1 and condition 8), realistic outcomes additionally include **termination of the company's own OpenAI account/API access** and a **contract claim for breach of §3.3 (Restrictions) that falls outside the indirect-damages waiver** via the §14.1(B) carve-out (§3.5). The earlier framing — that the ToU's enforcement mechanisms presuppose "an account relationship we don't have on this host" — is superseded: the entity-level account relationship exists regardless of which host the collector visits (dissent D.3).
6. **Sourcing caveat (amended).** The ToU text is quoted from a Wayback snapshot two days old at research time (2026-07-05; independently re-verified verbatim by the verifier, dissent D.1); the Services Agreement is quoted from a 2026-07-02 snapshot (`20260702193921`); the Sharing & Publication Policy from `20260626093648`; the Usage Policies are not archived at all (no HTTP-200 Wayback capture as of 2026-07-06). A human should eyeball the live policies pages — ToU, Services Agreement, and Usage Policies — in a normal browser at Phase 0 to confirm the quoted text (manual viewing is not bot-wall circumvention); see condition 7. The superseded Business Terms (§3.6) require no further monitoring.
7. **Incorporated policies (added per dissent D.1/D.5).** The ToU's "What you can do" clause (§2.6) incorporates the Sharing & Publication Policy and the Usage Policies. The Sharing & Publication Policy ("Updated: November 14, 2022"; Wayback `20260626093648`) governs sharing/publication of AI-generated content and model Output, not website crawling or republication of docs pages — not adverse to the collector. The Usage Policies remain to be located, quoted, and archived at Phase 0 (condition 7); low relevance to crawling (they govern model use).

---

## 6. Verdict: **CONDITIONAL**

Cleared to collect from `developers.openai.com/api/docs/models` and `/api/docs/changelog` subject to ALL of the following binding conditions:

1. **Re-check robots.txt every crawl cycle** (it was modified 2026-07-06); stop immediately if any rule disallows our paths or UA.
2. **Never authenticate or assent** on this host: no OpenAI account, no login cookies, no click-through acceptance in the collector path (keeps the ToU clause a browsewrap as to the collector).
3. **Cease-on-block:** any 403/429/challenge from developers.openai.com halts collection for the host — no retry-with-different-UA, no circumvention — and escalates for human review.
4. **Rate discipline:** ≤ 1 poll/hour/page, conditional GETs honoring ETag/Last-Modified, exponential backoff, single identified UA `TheLLMReportBot/1.0 (+https://thellmreport.com/bot)`.
5. **Publication limits:** publish facts (model names, prices, dates, deprecation status) and minimal quoted excerpts only, with attribution and link-back; verbatim page archives remain private (sha256 manifests public only).
6. **Honor takedowns immediately** via the ToU copyright-complaints channel (OpenAI OpCo, LLC, Attn: General Counsel / Copyright Agent); any C&D → immediate halt + counsel review.
7. **Re-verify quoted terms at Phase 0** by human browser view of the live pages — the Terms of Use (quoted from 2026-07-05 Wayback snapshot), the **Services Agreement** (quoted from 2026-07-02 Wayback snapshot `20260702193921`), and the **Usage Policies** (incorporated by the ToU, §2.6; no HTTP-200 Wayback capture as of 2026-07-06 — locate, quote, and archive them at Phase 0) — and re-run this sweep quarterly or on any change to the policies index, with the Services Agreement and Usage Policies included in every re-verification and quarterly re-sweep (the superseded Business Terms need no further monitoring). *(Amended per dissent D.6.4/D.5.)*
8. **Entity separation or counsel sign-off (pre-collection gate; added per dissent D.6.2):** before any collection from developers.openai.com, inventory whether the operating entity or its principal holds any OpenAI account (API, ChatGPT Business/Enterprise, or otherwise). If yes, the browsewrap analysis in §5.1 is inoperative for this host, and collection may proceed only after either (a) the collector is placed under a legal entity with no OpenAI contractual relationship, or (b) counsel sign-off is obtained accepting clickwrap-bound §3.3(f) risk, acknowledging that enforcement could include termination of the company's own OpenAI API access and a contract claim outside the indirect-damages waiver under the §14.1(B) carve-out.

---

*Prepared by compliance research agent, 2026-07-07. Evidence files (raw HTML of ToU snapshot, Business Terms snapshot, robots.txt with headers, live page fetches) were collected during this session; re-collect at Phase 0 import for the production evidence manifest.*

---

## Verifier dissent (2026-07-07)

**Amendments applied 2026-07-08** - every required change below is folded into the body above; import-ready.

Adversarial re-verification performed 2026-07-07 (UTC) by independent legal-review agent. I re-fetched the load-bearing documents myself. **I concur with the CONDITIONAL verdict letter but dissent from the analysis: §§1, 3, and 5 rest on a superseded business document and an entity-assent gap that materially understates contract risk. The file must be amended as set out below before Phase 0 import.**

### D.1 What re-verification confirmed (no dispute)

- **ToU quotes are real and current.** Independently fetched Wayback snapshot `20260705183726` of `openai.com/policies/terms-of-use/` (fetch date 2026-07-07; live URL re-confirmed HTTP 403). All §2 quotations verified verbatim, including "Automatically or programmatically extract data or Output (defined below)," the scope sentence, the IP clause, the copyright-complaints address, and both dates (Published/Effective: January 1, 2026).
- **robots.txt is accurately reported.** Live fetch 2026-07-07: HTTP 200, body byte-identical (`User-agent: *` / `Allow: /` / `Sitemap: /sitemap-index.xml`), `Etag: "e7f089df4e5b960af1bf865e870dcc75"`, `Last-Modified: Mon, 06 Jul 2026 23:18:38 GMT` — all match §4.
- **Footer check confirmed.** Live fetch of `/api/docs/models` (2026-07-07, HTTP 200): sole legal link is "Terms and policies" → `https://openai.com/policies`; no meta-robots restriction observed.
- **Sharing & Publication Policy checked (a §2 gap, but benign).** The ToU's "What you can do" clause incorporates it: "you must comply with all applicable laws as well as our Sharing & Publication Policy, Usage Policies, and any other documentation, guidelines, or policies we make available to you." Fetched via Wayback `20260626093648` (fetch 2026-07-07; "Updated: November 14, 2022"): it governs sharing/publication of AI-generated content and model Output, not website crawling or republication of docs pages. Not adverse to the collector. It should nonetheless be added to §1 as an incorporated document.

### D.2 Material defect 1 — the Business Terms quoted in §3 are superseded

The file quotes Business Terms "Updated: November 14, 2023" from a 2025-05-19 snapshot and flags them "may be outdated." They **are** outdated: OpenAI replaced the Business Terms with the **OpenAI Services Agreement, "Updated: December 1, 2025," "Effective: January 1, 2026"** — the same effective date as the new consumer ToU. Verified via Wayback snapshot `20260702193921` of `https://openai.com/policies/services-agreement/` (captured 2026-07-02, HTTP 200; fetch date 2026-07-07). The old Business Terms page itself links "View upcoming services agreement" — a successor signal the sweep missed. Key clauses, quoted verbatim from the 2026-07-02 snapshot:

> "This OpenAI Services Agreement only applies to use of OpenAI's APIs, ChatGPT Enterprise, ChatGPT Business, ChatGPT for Clinicians, and other services for customers who are businesses and developers, and does not apply to OpenAI services used by consumers or individuals unless specified above."

> "By clicking "I agree," accepting the Order Form, **or using the Services**, Customer agrees to this Agreement."

> ""Services" means OpenAI's services for businesses, enterprises, or developers made available for purchase or use in Customer's Account, along with any of OpenAI's associated software, tools, developer services, **documentation, and websites**, but excluding any Third-Party Service."

> §3.3 Restrictions: "Customer will not, and will not permit End Users to: […] (f) **extract data from the Services other than as permitted through the Services**; (g) buy, sell, or transfer API keys from, to, or with a third party; (h) interfere with or disrupt the Services, including circumvent any rate limits or restrictions or bypass any protective measures or safety mitigations for the Services; […]"

> §14.1 Limitation on Indirect Liability: "TO THE FULLEST EXTENT PERMITTED BY LAW, EXCEPT FOR: (A) A PARTY'S GROSS NEGLIGENCE OR WILLFUL MISCONDUCT; **(B) CUSTOMER'S BREACH OF SECTION 3.3 (RESTRICTIONS)**; […] NEITHER CUSTOMER NOR OPENAI OR EITHER PARTY'S AFFILIATES OR LICENSORS WILL BE LIABLE UNDER THIS AGREEMENT FOR ANY INDIRECT, PUNITIVE, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR EXEMPLARY DAMAGES […]"

Three consequences the file does not capture:

1. **Assent is broader than "sign-up."** The old Business Terms attached "By signing up"; the Services Agreement attaches by "clicking 'I agree,' accepting the Order Form, **or using the Services**." The file's §3 note ("bind by sign-up") is no longer the operative assent mechanism.
2. **The Services definition expressly includes "documentation, and websites."** A developer documentation website is squarely within the defined term (the old Business Terms had materially identical language — "along with any of our associated software, tools, developer services, documentation, and websites" — which §3 did not quote either).
3. **Restriction breaches are carved out of the liability cap** (§14.1(B)). "Worst realistic outcome" in §5.5 (block or C&D) understates the downside for a bound Customer: account termination plus a contract claim outside the indirect-damages waiver.

### D.3 Material defect 2 — entity-level assent defeats the browsewrap shield

The entire §5 analysis rests on "no assent → weak browsewrap." But the file's own §3 note concedes: *"our company separately holds API accounts."* Contracts bind legal persons, not processes. If the entity operating TheLLMReportBot (or the owner as principal) is an OpenAI API Customer, that entity **has already assented** — by click-through or by use — to the Services Agreement, whose defined "Services" include OpenAI's developer "documentation, and websites," and whose §3.3(f) prohibits extracting data from them other than as permitted through the Services. The collector is that entity's instrumentality; condition 2 ("no account in the collector path") is process hygiene and does not sever contract privity. On these facts the applicable adverse clause is plausibly a **clickwrap-bound** §3.3(f), not a weak browsewrap — the hiQ-style framing in §5.1 does not survive that.

Counterarguments preserved for the record: the definition ties Services to what is "made available for purchase or use in Customer's Account," and OpenAI would still need to show damages; robots.txt allow-all and public availability cut against materiality of breach. These reduce, but do not eliminate, the exposure — and none of them appear in the file.

### D.4 Secondary defect — governing-document classification is inverted for this host

§1 treats the consumer ToU as primary and the business document as "secondary." The ToU itself carves out: "Our Business Terms govern use of ChatGPT Enterprise, our APIs, and our other services for businesses and developers," and the Services Agreement's scope covers "other services for customers who are businesses and developers." A developer docs site is at least arguably a developer-facing service whose associated website falls under the Services Agreement, not (only) the consumer ToU. Both documents contain an anti-extraction clause, so the verdict does not flip on this — but the evidence archive must quote the document OpenAI would actually sue under, and today that is the Services Agreement.

### D.5 Open item

- **Usage Policies** are incorporated by the ToU but were not archived by the sweep and have no HTTP-200 Wayback capture at `openai.com/policies/usage-policies/` as of 2026-07-06. Low relevance to crawling (they govern model use), but locate, quote, and archive them at Phase 0 for completeness.

### D.6 Required changes (verdict stays CONDITIONAL only if all are made)

1. **Replace §3** with the OpenAI Services Agreement (Updated 2025-12-01, Effective 2026-01-01; Wayback `20260702193921`, fetched 2026-07-07), quoting the scope sentence, the assent clause, the "Services" definition, §3.3(f)/(h), and the §14.1(B) carve-out. Retain the old Business Terms only as historical context.
2. **Add a condition 8 (entity separation):** before any collection from developers.openai.com, inventory whether the operating entity or its principal holds any OpenAI account (API, ChatGPT Business/Enterprise, or otherwise). If yes, the browsewrap analysis in §5.1 is inoperative for this host; either (a) place the collector under a legal entity with no OpenAI contractual relationship, or (b) obtain counsel sign-off accepting clickwrap-bound §3.3(f) risk, acknowledging that enforcement could include termination of the company's own OpenAI API access and an uncapped-indirect-damages contract claim.
3. **Amend §5.5** to list account termination and a §14.1(B)-carved-out contract claim as realistic outcomes for a bound Customer, alongside block/C&D.
4. **Amend condition 7** to include the Services Agreement and the Usage Policies in the Phase 0 human re-verification and the quarterly re-sweep (not just ToU and the defunct Business Terms).
5. **Add the Sharing & Publication Policy and Usage Policies to §1** as ToU-incorporated documents (checked; not adverse to crawling as of the snapshots cited above).

**Dissent verdict: CONDITIONAL — affirmed in letter, not in reasoning.** The conduct posture (identified UA, robots-allow-all host, ≤1 poll/hour, cease-on-block, facts-plus-minimal-excerpts, private archives) remains defensible; the paper record as filed is not. Do not import this file into the production repo until D.6 items 1–5 are applied.

*Verifier evidence: live `openai.com/policies/terms-of-use/` HTTP 403 (2026-07-07); Wayback `20260705183726` ToU (verified verbatim); Wayback `20260702193921` Services Agreement; Wayback `20250519024110` Business Terms (confirmed latest 200 capture); Wayback `20260626093648` Sharing & Publication Policy; live `developers.openai.com/robots.txt` HTTP 200 with matching ETag/Last-Modified (2026-07-07); live `/api/docs/models` footer check (2026-07-07).*
