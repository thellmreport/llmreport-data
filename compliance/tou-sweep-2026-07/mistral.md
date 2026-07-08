# ToU Clearance — docs.mistral.ai

**Sweep:** tou-sweep-2026-07 (design-phase legal deliverable, V-Q3 cond. 9)
**Host in scope:** `docs.mistral.ai` (models overview page; also our changelog + model retirement-dates source)
**Planned access pattern:** hourly conditional GETs, UA `TheLLMReportBot/1.0 (+https://thellmreport.com/bot)`, backoff, robots.txt honored, no bot-wall circumvention.
**Research date (all fetches):** 2026-07-07
**Verdict: CONDITIONAL — cleared for collection subject to the conditions in §6.**

---

## 1. Governing documents (as linked from the docs.mistral.ai footer)

Footer of `https://docs.mistral.ai/getting-started/models/models_overview/` (fetched 2026-07-07) links:

| Footer label | URL | Resolves to |
|---|---|---|
| Terms of service | `https://mistral.ai/terms` | 301 → `https://legal.mistral.ai/terms` (legal hub) |
| Privacy policy | `https://mistral.ai/terms#privacy-policy` | `https://legal.mistral.ai/terms/privacy-policy` |
| Legal notice | `https://mistral.ai/legal` | Legal Notice page |

Documents examined (all fetched 2026-07-07):

1. **Legal terms hub** — `https://legal.mistral.ai/terms` (hub banner "Effective: November 28, 2025"). Lists: EU Consumer ToS, ROW Consumer ToS, Commercial ToS, Additional Product Terms, Partner-served deployment terms, Additional Terms (customer infrastructure), DPA, Connectors terms, Privacy Policy, Usage Policy, Cookie Policy, License Notice, Applicant Privacy Policy. **There is no standalone "Website Terms of Use" document.**
2. **Legal Notice** — `https://mistral.ai/legal` (and sibling `https://legal.mistral.ai/legal-notice`). Publisher-identification page only (French LCEN, law no. 2004-575 of 21 June 2004). Publisher: Mistral AI, SAS, RCS Paris 952 418 325, 15 rue des Halles, 75001 Paris; publication director Arthur Mensch; host Netlify, Inc. **Contains no IP, reproduction, scraping, crawling, automated-access, or database-rights clauses.** No dated version shown (© 2026).
3. **EU Consumer Terms of Service** — `https://legal.mistral.ai/terms/eu-consumers-terms-of-service` — "Effective: May 28, 2026".
4. **Commercial Terms of Service** — `https://legal.mistral.ai/terms/commercial-terms-of-service` — "Effective: May 28, 2026". (The consumer ToS directs business users here; this is the document that would purport to govern us, a business.)
5. **Usage Policy** — `https://legal.mistral.ai/terms/usage-policy` — "Effective: June 11, 2026". Applies to Mistral platform products (Vibe, Mistral AI Studio); excludes customer/partner-infrastructure deployments and open-source models. Only tangentially relevant clause: "You shall not try to circumvent security protections and AI safety filters." (Security Violations). No scraping/crawling/republication clauses.
6. **License Notice** — `https://legal.mistral.ai/terms/license-notice` — Effective November 28, 2025. Third-party software attributions only (e.g., continue.dev/Apache-2.0 in Mistral Code). No website/documentation content licensing terms.

### Which document governs the *website* docs.mistral.ai?

There is **no dedicated website ToU**. Both ToS documents define their scope over "Mistral AI Studio, Vibe, and the other websites, products, software(s), services, and technologies we offer" (the "Mistral AI Products") — broad enough to sweep in docs.mistral.ai. **[Amended per Verifier dissent §1 — see stamp below]** These are *not* solely contracts formed by account signup/subscription acceptance as originally characterized: the Commercial ToS's own acceptance clause purports to form the contract on "(c) otherwise accessing or using any of the Mistral AI Products on behalf of Customer" (quoted in full in §2.4 below), and the EU Consumer ToS similarly forms "when you create a Mistral AI account **or use any of the Mistral AI Products**." Because "Mistral AI Products" is defined to include "the other websites… we offer," Mistral's own formation language purports to reach an accountless visitor to docs.mistral.ai the moment it fetches a page — i.e., this is a **use-based/browsewrap formation mechanism**, not a signup-gated one. docs.mistral.ai is nonetheless publicly served with no login, no interstitial, and no terms-acceptance banner; the footer merely links to the legal hub — the absence of any conspicuous notice is the actual basis for treating assent as unformed here (see §5 Analysis, item 1, as amended), not the absence of a use-based formation clause in the ToS text. The Legal Notice (the only document that unambiguously attaches to public web pages without any assent language at all) contains no use restrictions of any kind.

---

## 2. Verbatim clauses touching automated access / scraping / republication

### 2.1 Commercial Terms of Service (fetched 2026-07-07, effective 2026-05-28)

**Scope (preamble):**
> "These Terms of Service for Commercial Users (« Terms »), together with the additional terms and policies referenced herein (« Additional Terms »), govern the use of Mistral AI Studio, Vibe, and the other websites, products, softwares, services, and technologies we offer (collectively, the « Mistral AI Products ») by the organization, company, or other entity that you represent (« Customer »)."

**§2.2 Use Restrictions (lead-in and relevant items, verbatim):**
> "2.2. Use Restrictions. Customer will not, and will not permit any other person (including any End User) to: (a) use the Mistral AI Products or Outputs in a manner that violates any applicable laws (including sanctions and export control laws), these Terms, our Usage Policy, or any of our policies (including those posted at https://legal.mistral.ai/terms , which may be updated from time to time); […] (f) compromise or attempt to compromise the security or proper functionality of the Mistral AI Products, including interfering with, circumventing, or bypassing security or moderation mechanisms in the Mistral AI Products or performing any vulnerability, penetration, or similar testing of the Mistral AI Products; **(g) use any method to extract any content from the Mistral AI Products other than as permitted through the Mistral AI Products in accordance with these Terms;** or (h) buy, sell, or transfer API keys or any type of Mistral AI account from, to, or with a third party; …"

**§5.1 Reservation of Rights:**
> "5.1. Reservation of Rights. As between Customer and Mistral AI, Mistral AI owns all right, title, and interest in and to the Mistral AI Products, including all intellectual property rights therein. Customer solely receives the limited right to use the Mistral AI Products as explicitly granted in these Terms and any applicable Additional Terms. Mistral AI reserves all other rights associated with the Mistral AI Products."

**§14.4 Publicity:**
> "14.4. Publicity. Neither Party may use the other Party's name, logos, or marks without the other Party's written pre-approval in each case (email to suffice), including on websites, media, social media accounts, marketing materials, or other public statements."

### 2.2 EU Consumer Terms of Service (fetched 2026-07-07, effective 2026-05-28)

**Scope (preamble):**
> "These Terms of Service (these « Terms ») govern your personal use as an EEA consumer of Mistral AI Studio, Vibe and the other websites, products, software, services, and technologies we offer (the « Mistral AI Products »). […] If you are accessing the Mistral AI Products for business purposes such as to integrate the Mistral AI Products with your own products or services that are distributed to third-party end users, please review our Commercial Terms of Service."

**§3 Using Mistral AI Products — Restrictions (relevant items, verbatim):**
> "Restrictions. When accessing or using the Mistral AI Products, you will not, and will not permit any other person to: […] (e) Compromise the security or proper functionality of the Mistral AI Products, including interfering with, circumventing, or bypassing security or moderation mechanisms in the Mistral AI Products or performing any vulnerability, penetration, or similar testing of the Mistral AI Products; **(f) Use any method to extract any content from the Mistral AI Products other than as permitted through the Mistral AI Products;** …"

**§4 Your Data — Third-Party Content (web-search feature; noted for completeness, not applicable to docs fetching):**
> "You are not allowed to use Third-Party Content displayed using our web-search feature to (i) copy, store, archive, cache or create a database of the Third-Party Content, (ii) redistribute, resell, or sublicense the Third-Party Content, (iii) as part of any machine learning or similar algorithmic activity, or (iv) to create, train, evaluate or improve products or services that you may make available to third-parties."

### 2.3 Notable absences (checked across all documents above, 2026-07-07)

- **No occurrence anywhere of:** "scrape/scraping", "crawl/crawler", "robot", "spider", "harvest", "data mining", "text and data mining", "bulk download". Confirmed by keyword search over the full extracted text of the Commercial ToS, EU Consumer ToS, Usage Policy, Legal Notice, and License Notice.
- No TDM-reservation (EU DSM Directive art. 4 opt-out) signal on docs.mistral.ai: no `robots.txt`, no `<meta name="robots">`, no `noai`/`tdm-reservation` meta tags, no `X-Robots-Tag` header (checked on the models overview page, 2026-07-07).

### 2.4 Contract-formation clauses (added per Verifier dissent §1 — bears on browsewrap analysis, §1 and §5 item 1)

**Commercial ToS acceptance clause (verbatim, verified 2026-07-07):**
> "By (a) clicking on 'I agree' (or any similar button or checkbox) at the time you sign up for a Mistral AI Product, (b) executing an Order Form referencing these Terms, or (c) otherwise accessing or using any of the Mistral AI Products on behalf of Customer, you represent that you have the legal authority to bind Customer and are agreeing to these Terms"

**EU Consumer ToS formation language (verbatim, verified 2026-07-07):**
> "…when you create a Mistral AI account or use any of the Mistral AI Products."

Both clauses reach beyond signup: limb (c) of the Commercial ToS and the "or use" limb of the EU Consumer ToS purport to form the contract on mere use of any "Mistral AI Product," a defined term that includes "the other websites… we offer" — i.e., docs.mistral.ai. This is a use-based/browsewrap formation mechanism, not a signup-only one. See §5 Analysis, item 1 (amended), for why this does not change the bottom-line verdict.

---

## 3. robots.txt findings

- `https://docs.mistral.ai/robots.txt` → **HTTP 404 Not Found** (fetched 2026-07-07, twice: once via generic fetch, once via `curl -A "TheLLMReportBot/1.0 (+https://thellmreport.com/bot)"`; body is the site's Next.js 404 page, not a robots file).
- **No robots.txt exists ⇒ no crawl restrictions are declared for any path.** Under REP (RFC 9309), absence of robots.txt means all paths are crawlable, including our targets.
- Target path check: `https://docs.mistral.ai/getting-started/models/models_overview/` → **308 Permanent Redirect** → canonical **`https://docs.mistral.ai/models/overview`** → HTTP 200 to our declared bot UA (no bot-wall, no UA discrimination observed). Response carries an **`ETag`** header (`"ed3ece6669638b5d02d93ca1a38df703"` at fetch time) — conditional GETs (`If-None-Match`) are supported, matching our design. **Action: pin the post-redirect URL `https://docs.mistral.ai/models/overview` in the collector config.**
- **Corroborating fact (added per Verifier dissent verification note):** `https://mistral.ai/robots.txt` (the parent marketing site, not our target host) returns HTTP 200 with `User-agent: * / Allow: /` — an affirmative allow-all. Not dispositive for docs.mistral.ai specifically, but consistent with an open-crawl posture across Mistral web properties.

---

## 4. Favorable fact: docs source is open-source (Apache-2.0)

The documentation site's source is public at **`https://github.com/mistralai/platform-docs-public`** (deployed via Vercel, `platform-docs-public-mistral-ai.vercel.app`). Its `LICENSE` file (verified verbatim at `https://raw.githubusercontent.com/mistralai/platform-docs-public/main/LICENSE`, 2026-07-07) is **Apache License, Version 2.0, January 2004**. The same content we would excerpt from docs.mistral.ai is therefore available under an express license permitting reproduction and redistribution with attribution/notice. This provides both (a) an affirmative license basis for minimal quoted excerpts and (b) an alternative/corroborating collection source (git history also gives us diffs for free).

**Role, strengthened per Verifier dissent §3 / Verdict condition 4:** this Apache-2.0 mirror is the **primary** source for verbatim archives and diff derivation — not merely a secondary corroborating source. docs.mistral.ai fetches serve as liveness/parity checks and evidence timestamps only. This moves the riskiest act (building a private verbatim archive, potentially implicating Commercial ToS §2.2(g) and French database/IP law) entirely onto expressly licensed material.

---

## 5. Analysis

1. **Contract formation — corrected per Verifier dissent §1.** docs.mistral.ai does *not* lack a use-based formation mechanism: the Commercial ToS's own acceptance clause purports to form the contract via "(c) otherwise accessing or using any of the Mistral AI Products on behalf of Customer," and the EU Consumer ToS forms "when you create a Mistral AI account or use any of the Mistral AI Products" (both quoted in full at §2.4). Because "Mistral AI Products" is defined to include "the other websites… we offer," this formation language purports to bind an accountless visitor to docs.mistral.ai the moment it fetches a page. The §2.2(g)/§3(f) extraction restriction therefore cannot be dismissed as unformed. The defensible position instead is that **use-based/browsewrap assent without conspicuous notice is generally unenforceable**: docs.mistral.ai has no login, no interstitial, and no terms-acceptance banner — no mechanism brings the ToS to a visitor's attention before or during access (US: *Nguyen v. Barnes & Noble*, 763 F.3d 1171 (9th Cir. 2014); EU/France: assent requires the terms be brought to the user's attention and accepted, cf. CJEU C-30/14 *Ryanair v PR Aviation*, which bound the scraper only because the terms had in fact been accepted — the inverse of our facts, where no acceptance step exists). Practical consequence: §2.2(g)/§3(f) is *arguably applicable but likely unenforceable for want of conspicuous notice*, and in the alternative *not breached* (item 2, reframed as fallback below), and in the further alternative *licensed* (Apache-2.0 mirror, item 3, reframed as primary below). Prudence: keep the collector operationally separate from any Mistral account the business may later hold.
2. **Even if bound — secondary/fallback argument, reframed per Verifier dissent §3.** The claim that hourly automated fetching is "access through the product's ordinary, permitted channel" is optimistic: §2.2(g)/§3(f) target extraction *methods*, and a systematic hourly collector building a private verbatim archive is plausibly "a method to extract content… other than as permitted." This argument survives as a fallback but is **not** the primary basis for collection or republication — that role now belongs to the Apache-2.0 license (item 3). No security/moderation mechanism is interfered with regardless (§2.2(f)/§3(e) not implicated).
3. **Republication — primary basis is the Apache-2.0 license, reframed per Verifier dissent §3.** Mistral reserves all IP in the Mistral AI Products under the Commercial ToS (§5.1), but the identical documentation content is independently Apache-2.0-licensed via the public GitHub repo (`github.com/mistralai/platform-docs-public`), which affirmatively permits reproduction and redistribution with attribution — this is now the **primary** legal basis for both verbatim archiving and excerpt republication (Verdict condition 4, strengthened). Publishing only minimal quoted excerpts + sha256 manifests while keeping verbatim archives private additionally fits within EU/French quotation rights as a secondary fallback if the license basis were ever contested.
4. **robots.txt / TDM signals — plus legal-hub monitoring, expanded per Verifier dissent §2.** No robots.txt restrictions exist today; nothing to honor yet. Because absence ≠ permanent permission, the collector must re-check robots.txt each cycle (our baseline behavior) and treat any future appearance, meta-robots/`noai`, or `X-Robots-Tag` as immediately binding. Separately, Commercial ToS §2.2(a) incorporates "our Usage Policy, or any of our policies (including those posted at https://legal.mistral.ai/terms , which may be updated from time to time)," and §13 allows Mistral to update terms on 30 days' notice — so the restriction set can grow without any robots.txt change at all (e.g., a new website ToU or anti-scraping policy could be added directly to the legal hub). See Verdict condition 7 (new).
5. **Publicity clause (§14.4)** binds only contract "Parties"; nominative use of the "Mistral" name to identify the subject of factual reporting is standard trademark fair use. Avoid logo use.
6. **Bonus — status feed.** `status.mistral.ai` is a **Checkly-hosted status page** (Checkly's hosted product, `checkly-status-page.com`; Nuxt app, Checkly build assets, `api.checklyhq.com` audience). Status-page ID: **`89510173-714f-4ba6-9ad3-b4598370f903`**, slug `mistral-ai`. Machine-readable feed to pin for Phase 0: **`https://status.mistral.ai/_payload.json`** (HTTP 200, `application/json`; contains `statusPage`, `unresolved-incidents-89510173-…`, `uptime-89510173-…`, and `maintenance-windows-mistral-ai` blocks; verified 2026-07-07). No RSS/Atom endpoint exists (`/rss`, `/feed.rss`, `/history.rss` return the SPA HTML fallback).

---

## 6. Verdict

**CONDITIONAL — CLEARED for hourly collection of docs.mistral.ai, subject to:**

1. **Public paths only, no account linkage.** Fetch only unauthenticated docs.mistral.ai pages; never fetch console.mistral.ai or any logged-in surface; keep the collector unassociated with any Mistral account (avoids forming/breaching Commercial ToS §2.2(g)).
2. **Re-check robots.txt every cycle.** It is currently 404 (no restrictions); if one appears — or a meta-robots/`noai`/TDM-reservation tag or `X-Robots-Tag` header is introduced — honor it immediately (baseline behavior; restated here because the current permission rests on absence).
3. **Excerpt discipline + attribution.** Published diffs carry only minimal quotations attributed to Mistral's documentation; verbatim archives remain private. Where excerpts are republished, note the Apache-2.0 source (`github.com/mistralai/platform-docs-public`) in the evidence manifest to invoke the express license.
4. **GitHub mirror is primary for verbatim archives (strengthened per Verifier dissent §3, from "prefer/pair").** The GitHub mirror (`mistralai/platform-docs-public`, Apache-2.0) is the primary source for verbatim archives and diff derivation; docs.mistral.ai fetches serve as liveness/parity checks and evidence timestamps only.
5. **Trademark hygiene.** Nominative use of "Mistral"/"Mistral AI" only; no logo use without a brand-permission check.
6. **Pin canonical URL.** Use `https://docs.mistral.ai/models/overview` (the old `/getting-started/models/models_overview/` path 308-redirects); use conditional GETs against the served `ETag`.
7. **Monitor the legal hub (new, per Verifier dissent §2).** Re-check `https://legal.mistral.ai/terms` (document list + effective-date banners) on a recurring cadence — at least monthly, and at every sweep refresh. A new "Terms of Use"/AUP-type document appearing on the hub, or a revised Commercial ToS, triggers re-clearance of this host.

---

*Prepared by compliance research agent, 2026-07-07. All quotes fetched verbatim from live pages on that date; no bot-walls encountered; no indirect sourcing required.*

---

## Verifier dissent (2026-07-07)

**Amendments applied 2026-07-08** - every required change below is folded into the body above; import-ready.

Adversarial re-verification (independent re-fetch of the Commercial ToS, EU Consumer ToS, legal hub, robots.txt/headers, and the GitHub LICENSE, all 2026-07-07). **Verdict letter sustained: CONDITIONAL.** The quoted clauses are real, current, and complete; the notable-absences claim (no scrape/crawl/robot/spider/harvest/data-mining/TDM language anywhere) reproduces; robots.txt is 404 with our bot UA and `/models/overview` serves HTTP 200 with the same ETag (`"ed3ece6669638b5d02d93ca1a38df703"`), no `X-Robots-Tag`, no meta-robots/`noai`/`tdm` tags; the Apache-2.0 LICENSE at `mistralai/platform-docs-public` is the full license text on an active repo whose MDX content is the docs site. However, the analysis contains one material mischaracterization and two soft spots that must be corrected before Phase 0 import:

### 1. MUST FIX — Formation analysis misstates the Commercial ToS (§1 and §5.1 of this file)

The file claims both ToS are "contracts formed by account signup/subscription acceptance, not browsewrap." **That is wrong on the document's own text.** The Commercial ToS acceptance clause reads (verified verbatim 2026-07-07):

> "By (a) clicking on 'I agree' (or any similar button or checkbox) at the time you sign up for a Mistral AI Product, (b) executing an Order Form referencing these Terms, or **(c) otherwise accessing or using any of the Mistral AI Products on behalf of Customer**, you represent that you have the legal authority to bind Customer and are agreeing to these Terms"

The EU Consumer ToS similarly forms "when you create a Mistral AI account **or use any of the Mistral AI Products**." Because "Mistral AI Products" is defined to include "the other websites… we offer," Mistral's own formation language purports to bind an accountless visitor to docs.mistral.ai the moment it fetches a page. The defensible position is therefore NOT "no formation mechanism reaches us" — it is that **use-based/browsewrap assent without conspicuous notice is generally unenforceable** (US: *Nguyen v. Barnes & Noble*, 763 F.3d 1171 (9th Cir. 2014); EU/France: assent requires the terms be brought to the user's attention and accepted, cf. CJEU C-30/14 *Ryanair* binding only because the terms had been accepted). That is a weaker, contestable position and the clearance memo must say so honestly. Practical consequence: the §2.2(g) "extract any content" clause cannot be dismissed as unformed; it must be treated as *arguably applicable but likely unenforceable, and in the alternative not breached* (ordinary public HTTP channel, no circumvention) *and in the further alternative licensed* (Apache-2.0 mirror).

### 2. MUST FIX — Add a condition: monitor the legal hub, not just robots.txt

Commercial ToS §2.2(a) incorporates "our Usage Policy, or any of our policies (including those posted at https://legal.mistral.ai/terms , **which may be updated from time to time**)." The restriction set can grow without any robots.txt change — e.g., Mistral could add a website ToU or an anti-scraping policy to the hub at any time, and §13 lets Mistral update terms on 30 days' notice. **New condition 7: re-check https://legal.mistral.ai/terms (document list + effective-date banners) on a recurring cadence (at least monthly, and at every sweep refresh); a new "Terms of Use"/AUP-type document or a revised Commercial ToS triggers re-clearance of this host.**

### 3. SHOULD FIX — Weight the even-if-bound argument correctly (§5.2)

The claim that hourly automated fetching is "access through the product's ordinary, permitted channel" is optimistic: §2.2(g) targets extraction *methods*, and a systematic hourly collector building a private verbatim archive is plausibly "a method to extract content… other than as permitted." The argument survives, but it should be positioned as a secondary fallback. The primary legal basis for both collection and excerpt republication should be the **Apache-2.0 license** on the identical content. Accordingly, strengthen condition 4 from "prefer/pair" to: **the GitHub mirror (`mistralai/platform-docs-public`) is the primary source for verbatim archives and diff derivation; docs.mistral.ai fetches serve as liveness/parity checks and evidence timestamps.** This moves the verbatim-archive activity (the riskiest act under §2.2(g) and French database/IP law) entirely onto expressly licensed material.

### Corroborating fact found during verification (favorable, add to §3)

`https://mistral.ai/robots.txt` (the parent marketing site, not our target host) returns HTTP 200 with `User-agent: * / Allow: /` — an affirmative allow-all. Not dispositive for docs.mistral.ai, but consistent with an open-crawl posture across Mistral web properties.

**Disposition: CONDITIONAL sustained, with conditions amended — add condition 7 (legal-hub monitoring) and strengthen condition 4 (mirror-primary for verbatim archives). §1/§5.1 formation language must be rewritten per point 1 before this file is imported verbatim into the production repo.**

*Verifier: adversarial legal review agent, 2026-07-07. Independent fetches: Commercial ToS, EU Consumer ToS, legal hub (WebFetch); robots.txt/headers/meta checks via curl with declared bot UA; GitHub LICENSE + repo status.*
