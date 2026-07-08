# ToU Clearance: learn.microsoft.com (Azure AI Foundry / Azure OpenAI "What's new" page)

- **Sweep:** tou-sweep-2026-07 (design-phase legal deliverable, V-Q3 cond. 9)
- **Host:** `learn.microsoft.com`
- **Target path:** `/en-us/azure/ai-foundry/openai/whats-new`
- **Fetch date for all sources below:** 2026-07-07
- **Collector profile assumed:** hourly conditional GET, UA `TheLLMReportBot/1.0 (+https://thellmreport.com/bot)`, backoff, robots.txt honored, no bot-wall circumvention.

---

## 1. Governing documents

| Document | URL | Fetched | Notes |
|---|---|---|---|
| Terms of Use \| Microsoft Learn ("TOU") | https://learn.microsoft.com/en-us/legal/termsofuse | 2026-07-07 | Page metadata: `ms.date: 2025-05-12`, `updated_at: 2025-05-12T21:58:00Z`. Source: `github.com/MicrosoftDocs/DocsLegal-pr/blob/live/DocsLegal/termsofuse.md` (commit `9fd90ed8`). Directly sourced (no bot wall). |
| robots.txt | https://learn.microsoft.com/robots.txt | 2026-07-07 | File header comment dated `08/19/2022`. Directly sourced. |
| CC BY 4.0 LICENSE of public docs mirror | https://raw.githubusercontent.com/MicrosoftDocs/azure-ai-docs/main/LICENSE | 2026-07-07 | Creative Commons Attribution 4.0 International. Directly sourced. |
| GitHub source of target page (public mirror) | https://raw.githubusercontent.com/MicrosoftDocs/azure-ai-docs/main/articles/foundry-classic/openai/whats-new.md | 2026-07-07 | Confirmed live and in sync with the website (May 2026 entries present; frontmatter `ms.date: 12/30/2025`). |
| Target page (rendered) | https://learn.microsoft.com/en-us/azure/ai-foundry/openai/whats-new | 2026-07-07 | Loaded normally, no bot wall. Page metadata: `updated_at: 2026-06-05T22:11:00Z`. |

**Scope confirmation.** The TOU states which site it governs (Acceptance of Terms, quoted verbatim):

> The following Terms of Use ("TOU") apply to your use of the Microsoft Learn website ([https://learn.microsoft.com](/en-us/)), Microsoft Learn Profile and any associated services. Microsoft reserves the right to update the TOU at any time without notice to you.

This is the website terms document, not the Azure/API service terms — correct instrument for this sweep.

---

## 2. Verbatim clauses touching automated access / scraping / republication

The TOU uses **named section headings, not section numbers**. Section identifiers below are the exact headings.

### 2.1 "Personal and Non-Commercial Use Limitation" (operative clause; final sentence elided per verifier dissent, Minor)

> Unless otherwise specified, the Services are for your personal and non-commercial use. You may not modify, copy, distribute, transmit, publicly display, perform, reproduce, publish, license, create derivative works from, transfer or sell any information, software, products or services obtained from the Services (except for your own, personal, non-commercial use) without prior written consent from Microsoft. […]

*Elision note (added per verifier dissent, Minor):* the clause's final sentence — "For your own safety, do not post any sensitive information..." — is omitted above; the omission is analytically harmless (it addresses posting, not collection), but a verbatim-evidence deliverable must mark elisions with an ellipsis rather than label the excerpt "entire."

**Relevance:** On its face this bars commercial republication of anything "obtained from the Services," **and** — per verifier dissent point 2 — imposes a separate contractual restriction on *commercial use of the Services themselves* (independent of any copyright license in the content). §2.2's CC BY 4.0 override resolves the republication/copyright half of this clause; it does not fully resolve the access-restriction half. See §4.2 (amended) for the reconciled analysis and Verdict condition 6 for the mitigating operational discipline.

### 2.2 "Notice Specific to Documents Available on this Website" (operative excerpts)

> Certain documentation may be subject to explicit license terms separate from the terms contained here. To the extent the terms conflict, the explicit license terms control.

> Permission to use Documents (such as white papers, press releases, datasheets and FAQs) from the Services is granted, provided that (1) the below copyright notice appears in all copies and that both the copyright notice and this permission notice appear, (2) use of such Documents from the Services is for informational and non-commercial or personal use only and will not be copied or posted on any network computer or broadcast in any media, and (3) no modifications of any Documents are made. […] Use for any other purpose is expressly prohibited by law, and may result in severe civil and criminal penalties.

> Documents specified above do not include the design or layout of the Microsoft.com website or any other Microsoft owned, operated, licensed or controlled site. Elements of Microsoft websites are protected by trade dress, trademark, unfair competition, and other laws and may not be copied or imitated in whole or in part. No logo, graphic, sound or image from any Microsoft website may be copied or retransmitted unless expressly permitted by Microsoft.

**Relevance:** The first sentence is the key: **explicit license terms control over the TOU on conflict.** The target page's documentation content carries an explicit license — CC BY 4.0 — via its public GitHub source (see §4). The design/layout/logo exclusion survives regardless.

### 2.3 "No Unlawful or Prohibited Use" (entire clause)

> As a condition of your use of the Services, you will not use the Services for any purpose that is unlawful or prohibited by these terms, conditions, and notices. You may not use the Services in any manner that could damage, disable, overburden, or impair any Microsoft server, or the network(s) connected to any Microsoft server, or interfere with any other party's use and enjoyment of any Services. You may not attempt to gain unauthorized access to any Services, other accounts, computer systems or networks connected to any Microsoft server or to any of the Services, through hacking, password mining or any other means. You may not obtain or attempt to obtain any materials or information through any means not intentionally made available through the Services.

**Relevance:** This is the closest thing to an automated-access clause. **The TOU contains no express bot/crawler/scraper prohibition.** Hourly conditional GETs of one public article page cannot plausibly "overburden," and public pages listed in Microsoft's own sitemap are "intentionally made available."

### 2.4 "Use of Services" (bullets touching harvesting/copying)

> - Harvest or otherwise collect information about others, including e-mail addresses.
> - Use, download or otherwise copy, or provide (whether or not for a fee) to a person or entity any directory of users of the Services or other user or usage information or any portion thereof.
> - Use any material or information, including images or photographs, which are made available through the Services in any manner that infringes any copyright, trademark, patent, trade secret, or other proprietary right of any party.

**Relevance:** The harvesting/directory prohibitions target **user personal information**, not documentation content. Not implicated by our collector. The IP bullet is satisfied by operating under the CC BY 4.0 license.

### 2.5 Explicit-license override applied to the target page — CC BY 4.0 attribution condition

Public docs mirror LICENSE (`MicrosoftDocs/azure-ai-docs`, fetched 2026-07-07) is Creative Commons Attribution 4.0 International. Opening acceptance line:

> By exercising the Licensed Rights (defined below), You accept and agree to be bound by the terms and conditions of this Creative Commons Attribution 4.0 International Public License.

Attribution condition, **CC BY 4.0 §3(a)(1)** (verbatim):

> If You Share the Licensed Material (including in modified form), You must:
>
> a. retain the following if it is supplied by the Licensor with the Licensed Material:
>
> i. identification of the creator(s) of the Licensed Material and any others designated to receive attribution, in any reasonable manner requested by the Licensor (including by pseudonym if designated);
>
> ii. a copyright notice;
>
> iii. a notice that refers to this Public License;
>
> iv. a notice that refers to the disclaimer of warranties;
>
> v. a URI or hyperlink to the Licensed Material to the extent reasonably practicable;
>
> b. indicate if You modified the Licensed Material and retain an indication of any previous modifications; and
>
> c. indicate the Licensed Material is licensed under this Public License, and include the text of, or the URI or hyperlink to, this Public License.

---

## 3. robots.txt findings

Fetched https://learn.microsoft.com/robots.txt on 2026-07-07. Full verbatim contents:

```
# learn.microsoft.com
# 08/19/2022

User-agent: *

Sitemap: https://learn.microsoft.com/_sitemaps/sitemapindex.xml
Sitemap: https://learn.microsoft.com/answers/sitemaps/sitemap.xml

Disallow: /*/answers/accounts/
Disallow: /*/answers/users/
Disallow: /*/answers/revisions/
Disallow: /*/answers/search
Disallow: /*/answers/*sort=newest
Disallow: /*/answers/*sort=hottest
Disallow: /*/answers/*sort=votes
Disallow: /*/answers/commands/
Disallow: /*/answers/badges/
Disallow: /*/answers/comments
Disallow: /*/answers/*?*sort=
Disallow: /*/answers/*?*topics=
Disallow: /*/answers/*?*pagesize=
Disallow: /*/answers/*?*orderby=
Disallow: /*/answers/*?*filterby=
Disallow: /*/opbuildpdf/
Disallow: /*/search/?*terms
Disallow: /api/nextsteps/*
Disallow: /api/attachments/*
```

**Analysis for our paths:**
- Single `User-agent: *` group — applies to `TheLLMReportBot/1.0`. No bot-specific blocks, no `Crawl-delay`.
- `/en-us/azure/ai-foundry/openai/whats-new` — **not matched by any Disallow. ALLOWED.**
- Canonical `/en-us/azure/foundry-classic/openai/whats-new` (see §4 migration note) — **ALLOWED.**
- Disallows we must respect if scope ever expands: `/*/opbuildpdf/` (PDF renderings of docs — do not fetch), `/api/nextsteps/*`, `/api/attachments/*`, all `/answers/` sub-paths listed.

---

## 4. Analysis

**4.1 No express anti-bot clause.** The Microsoft Learn TOU (2025-05-12 revision) contains no clause prohibiting automated access, crawling, or scraping as such. The operative constraints are (a) don't overburden servers, (b) don't access things not intentionally made available, (c) don't republish commercially without consent or license. Our collector profile (hourly conditional GET, identified UA, backoff, robots honored) comfortably satisfies (a) and (b); the docs sitemap even invites crawling of article pages.

**4.2 Republication is the real issue — and it is licensed.** The "Personal and Non-Commercial Use Limitation" and the Documents notice would, standing alone, bar a commercial diff-publication service. But the Documents notice expressly provides that *"Certain documentation may be subject to explicit license terms separate from the terms contained here. To the extent the terms conflict, the explicit license terms control."* The target page's documentation content is published by Microsoft under **CC BY 4.0** in the public GitHub mirror:

- Live page metadata declares its source: `original_content_git_url: https://github.com/MicrosoftDocs/azure-ai-docs-pr/blob/live/articles/foundry-classic/openai/whats-new.md` (the `-pr` repo is Microsoft's private authoring repo; not publicly accessible).
- The **public mirror** is `MicrosoftDocs/azure-ai-docs`, same path `articles/foundry-classic/openai/whats-new.md`. Verified live on 2026-07-07 with identical content and freshness (May 2026 changelog entries present in both; live page `updated_at: 2026-06-05`).
- Repo `LICENSE` = CC BY 4.0 (covers docs content; code samples are separately MIT under `LICENSE-CODE`, not relevant here).

Therefore: minimal quoted excerpts, diffs, and even full-text private archives of the *documentation content* are licensed under CC BY 4.0 subject to §3(a)(1) attribution. Additionally, the facts we extract (model names, release dates, region availability, deprecations) are uncopyrightable facts.

**Amended per Verifier dissent point 2 (2026-07-08):** The heading above ("Republication is the real issue — and it is licensed") and the CC BY 4.0 override analyzed here resolve the **copyright/republication** half of the "Personal and Non-Commercial Use Limitation" clause only — CC BY 4.0 expressly permits commercial use, and where it conflicts with the TOU, the explicit-license-controls sentence in §2.2 makes CC BY control. This is **not** a complete answer to the clause's first sentence, *"Unless otherwise specified, the Services are for your personal and non-commercial use,"* which reads as a separate contractual restriction on **commercial use of the Services** (the act of a commercial operator fetching the site), independent of any copyright license in the content collected. A breach-of-contract theory on that first sentence survives the CC BY analysis on paper. Residual risk is assessed as low — the TOU is browsewrap of contested enforceability against a non-assenting crawler, Microsoft's own sitemap and robots.txt affirmatively invite crawling of article paths, and damages from one conditional GET per hour are illusory — but the risk is mitigated, not eliminated, by CC BY 4.0. This is an additional reason (beyond the "overburden" clause) to keep learn.microsoft.com fetch volume minimal per condition 6.

**4.3 What CC BY 4.0 does NOT cover:** the Learn site chrome, design/layout, Microsoft logos, and embedded media served from the site ("No logo, graphic, sound or image from any Microsoft website may be copied or retransmitted unless expressly permitted"). The page embeds media (e.g., `media/computer-use-preview.gif`, icon SVGs). Note: images that live *inside the CC BY repo* are technically under the repo license, but the conservative line — and our product's need — is text-only excerpts. Verbatim HTML snapshots (including chrome) stay in the PRIVATE archive only, which is defensible as non-distributed archival/evidence use and never "posted on any network computer."

**4.4 Collection route — SUPERSEDED 2026-07-08 per Verifier dissent point 1; do not rely on the struck text below.**

> ~~The cleanest architecture is to poll the raw GitHub source (`raw.githubusercontent.com/MicrosoftDocs/azure-ai-docs/main/articles/foundry-classic/openai/whats-new.md`) as the primary feed: the content there is directly CC BY 4.0, GitHub's ToS permit API/raw access, ETag-based conditional GETs work well, and commit history gives free, precise diffs (`git log` on the file). Poll the learn.microsoft.com rendered page as a secondary consistency check. This makes the Learn TOU's non-commercial clause nearly moot for the republication path.~~

The struck paragraph designated an **uncleared host** (`raw.githubusercontent.com`) as the primary collection route and asserted "GitHub's ToS permit API/raw access" without quoting any GitHub clause — an unevidenced legal conclusion. The Verifier's direct re-fetch of GitHub's Acceptable Use Policies (2026-07-07) shows this does not hold: hourly polling of a raw file meets GitHub's own definition of "scraping" ("extracting information from our Service via an automated process, such as a bot or webcrawler"), and the AUP's information-use whitelist (open-access research; archival use) does not obviously cover a commercial diff-alert product.

**Corrected route (per amended condition 2 and new condition 8):** `learn.microsoft.com` — the host actually cleared by this file — is the primary collection source. The public GitHub mirror is usable for *verification and diff context only* and is not itself a cleared collection route. A separate `github` host-set clearance, quoting GitHub Terms of Service §H (API Terms) and GitHub Acceptable Use Policies §§4, 6, 7, must be completed and issue its own verdict before any GitHub route is used for collection. If/when that clearance CLEARs a GitHub route, the mechanism must be the **GitHub REST API** (Contents/Commits endpoints, authenticated, within documented rate limits) — expressly excluded from the AUP's "scraping" definition — not `raw.githubusercontent.com` polling.

**4.5 URL migration warning.** The requested URL `/en-us/azure/ai-foundry/openai/whats-new` currently serves a page whose `canonicalUrl` is `https://learn.microsoft.com/en-us/azure/foundry-classic/openai/whats-new` and which is flagged *"Applies only to: Foundry (classic) portal"*. Microsoft is mid-migration from "Azure AI Foundry" to "Microsoft Foundry"; a successor what's-new page for the new portal likely exists/will exist under `/azure/foundry/` or in the `articles/foundry/` tree of the same repo. The collector must follow redirects/canonicals and this clearance must be re-checked if the content moves outside `MicrosoftDocs/*` CC BY repos (unlikely).

**4.6 Sourcing integrity.** All documents were fetched directly on 2026-07-07; no bot walls were encountered; nothing in this file is indirectly sourced.

---

## 5. Verdict

### CONDITIONAL — CLEAR to collect and publish, subject to the following binding conditions:

1. **Attribution (CC BY 4.0 §3(a)(1)):** Every published excerpt/diff of this page's content must carry: creator ("Microsoft Corporation / Microsoft Learn documentation"), a hyperlink to the source (the learn.microsoft.com page and/or the GitHub source file), the notice "Licensed under CC BY 4.0" with a link to https://creativecommons.org/licenses/by/4.0/, and an indication that the material is modified/excerpted (our diffs are modifications).
2. **Primary source = learn.microsoft.com (AMENDED 2026-07-08 per Verifier dissent point 1, required change 1):** `learn.microsoft.com` — the host actually cleared by this file — remains the primary collection source until a `github` host-set clearance is completed and CLEARs a GitHub route (see condition 8). The public GitHub mirror (`https://raw.githubusercontent.com/MicrosoftDocs/azure-ai-docs/main/articles/foundry-classic/openai/whats-new.md`) may be used for **verification and diff context only** in the interim — it is not a cleared collection route. *[Original condition, superseded: "Primary source = public GitHub mirror: Collect from raw.githubusercontent.com/... as primary; treat learn.microsoft.com as secondary verification." Struck per dissent — retained here for audit history only.]*
3. **Text only in public output:** No Microsoft logos, icons, images, GIFs, or site design/layout in anything published. Embedded media excluded from public excerpts.
4. **Private archive stays private:** Verbatim HTML snapshots (which include non-CC site chrome) are evidence-only, never published or shared — consistent with existing product design (sha256 manifests public, archives private).
5. **robots.txt compliance:** Fetch only article paths. Never fetch `/*/opbuildpdf/`, `/api/nextsteps/*`, `/api/attachments/*`, or the disallowed `/answers/` paths. Re-check robots.txt periodically (current file dated 2022-08-19; no crawl-delay).
6. **Rate discipline:** Hourly conditional GET (If-None-Match/If-Modified-Since), single identified UA, exponential backoff on 4xx/5xx — required by the "damage, disable, overburden, or impair" clause.
7. **Migration watch:** Alert on redirect/canonical change of the target URL or removal of the GitHub source path (`articles/foundry-classic/openai/whats-new.md`); locate the successor "Microsoft Foundry (new portal)" changelog and re-run clearance for it before adding it as a target.
8. **GitHub host-set clearance required before any GitHub-based collection (ADDED 2026-07-08 per Verifier dissent point 1, required change 2):** No collection may be routed through any `github.com` or `raw.githubusercontent.com` path until a separate `github` host-set clearance is completed — quoting GitHub Terms of Service §H (API Terms) and GitHub Acceptable Use Policies §§4, 6, 7 — and that clearance issues its own verdict. If/when it CLEARs a GitHub route, the mechanism must be the **GitHub REST API** (Contents/Commits endpoints, authenticated, within documented rate limits), not `raw.githubusercontent.com` polling. Until this clearance exists, condition 2 (learn.microsoft.com as primary) governs. Tracked as an open Phase-0 item in `00-sweep-summary.md` §3 (item 4).

*Prepared 2026-07-07 by compliance research agent (tou-sweep-2026-07). Import verbatim at Phase 0.* *Conditions 2 and 8, and §4.2/§4.4 analysis, amended 2026-07-08 per Verifier dissent — see stamp below.*

---

## Verifier dissent (2026-07-07)

**Amendments applied 2026-07-08** - every required change below is folded into the body above; import-ready.

Adversarial re-verification performed 2026-07-07 by independent legal-review agent. All primary sources re-fetched directly (no bot walls).

### What was verified and CONFIRMED

- **Learn TOU quotes are verbatim and current.** Re-fetched https://learn.microsoft.com/en-us/legal/termsofuse (2026-07-07; `ms.date: 2025-05-12`, `git_commit_id: 9fd90ed8...` — same revision cited above). The quoted "Acceptance of Terms," "Personal and Non-Commercial Use Limitation," "No Unlawful or Prohibited Use," and "Notice Specific to Documents Available on this Website" clauses match the live text word-for-word, including the load-bearing sentence *"To the extent the terms conflict, the explicit license terms control."*
- **No missed anti-bot clause.** The full TOU was checked section-by-section for bots, crawlers, scraping, spiders, automated access, data mining, TDM, AI/ML training, and harvesting. None exists. The "Use of Services" bullets and "Policies" (content-conduct) section add nothing applicable to a read-only collector. The Learn TOU is the correct, most-specific instrument for this host; the Microsoft Services Agreement attaches to signed-in Microsoft accounts only (our collector is anonymous) and the generic microsoft.com ToU is displaced by the Learn-specific TOU per its own Acceptance-of-Terms scope line.
- **robots.txt verified identical** (re-fetched 2026-07-07): single `User-agent: *` group, target path and its `foundry-classic` canonical not disallowed.
- **CC BY 4.0 basis verified**: `MicrosoftDocs/azure-ai-docs` LICENSE re-fetched 2026-07-07 — Creative Commons Attribution 4.0 International, title and acceptance line match §2.5. Note also CC BY 4.0 §2(a)(5)(A): every *recipient* of the Licensed Material automatically receives the license offer, which is what lets content collected from the rendered Learn page (not just the repo) ride on the CC basis.

### Dissent point 1 (MUST CHANGE): Condition 2 routes primary collection through an UNCLEARED host

Condition 2 designates `raw.githubusercontent.com` as the **primary** collection source, and §4.4 asserts "GitHub's ToS permit API/raw access" with no quoted clause and no clearance file for that host. That assertion does not survive contact with GitHub's Acceptable Use Policies (re-fetched 2026-07-07, https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies):

> "Scraping refers to extracting information from our Service via an automated process, such as a bot or webcrawler. Scraping does not refer to the collection of information through our API."

> "You may use information from our Service for the following reasons, regardless of whether the information was scraped, collected through our API, or obtained otherwise: Researchers may use public, non-personal information from the Service for research purposes, only if any publications resulting from that research are open access. Archivists may use public information from the Service for archival purposes."

An hourly bot polling a raw file IS "scraping" under that definition, and the information-usage whitelist (open-access researchers; archivists) does not obviously cover a commercial diff-alert product. GitHub AUP §4 separately prohibits "excessive automated bulk activity" (one file hourly is likely fine, but that is a judgment GitHub's clearance file must make, not this one). The underlying content being Microsoft's CC BY 4.0 material helps on copyright but does not neutralize GitHub's contractual access/usage terms.

**Required changes:**
1. **Amend condition 2**: `learn.microsoft.com` — the host actually cleared by this file — remains the primary collection source until a `github` host-set clearance is completed and CLEARs a GitHub route. The GitHub mirror may be used for *verification and diff context* only in the interim.
2. If/when GitHub is cleared, the preferred mechanism is the **GitHub REST API** (Contents/Commits endpoints, authenticated, within documented rate limits) — expressly excluded from the AUP's "scraping" definition — not `raw.githubusercontent.com` polling. That clearance must quote GitHub ToS §H (API Terms) and AUP §§4, 6, 7 and issue its own verdict.
3. Strike or caveat the §4.4 sentence "GitHub's ToS permit API/raw access" — as written it is an unevidenced legal conclusion inside a deliverable that will be imported verbatim.

### Dissent point 2 (must be acknowledged): the CC BY override resolves republication, not the access restriction

§4.2 frames the "Personal and Non-Commercial Use Limitation" as fully "resolved" by the explicit-license-controls sentence. That is correct for the *copyright/republication* half of the clause (CC BY 4.0 expressly permits commercial use; direct conflict; explicit license controls). It is **not** a complete answer to the clause's first sentence — *"Unless otherwise specified, the Services are for your personal and non-commercial use"* — which reads as a contractual restriction on commercial **use of the Services** (i.e., the act of a commercial operator fetching the site), independent of any copyright license in the content. Residual risk is low: the TOU is browsewrap of contested enforceability against a non-assenting crawler; Microsoft's sitemap and robots.txt affirmatively invite crawling of article paths; and damages from one conditional GET per hour are illusory. But a breach-of-contract theory survives the CC BY analysis on paper, and this file should say so rather than declare the clause resolved. This is an additional reason to keep Learn-page fetches minimal once a cleared GitHub route exists.

### Minor

- §2.1 is labeled "(entire operative clause)" but omits the section's final sentence ("For your own safety, do not post any sensitive information..."). The omission is analytically harmless (the sentence addresses posting, not collection), but a verbatim-evidence deliverable should mark elisions with an ellipsis. Add one.

### Verifier verdict

**CONDITIONAL — verdict class AFFIRMED, conditions as originally written NOT affirmed.** Clearance for `learn.microsoft.com` collection and CC BY-attributed republication stands on the evidence. Conditions must be amended per dissent point 1 (Learn primary until a `github` host-set clearance exists; GitHub API, not raw polling, as the future GitHub mechanism; strike the unevidenced GitHub ToS assertion) and the residual contractual-access risk in dissent point 2 must be recorded. Do not import at Phase 0 until conditions 2 and §4.4 are revised.

*Verified 2026-07-07 by adversarial legal-review agent. Sources re-fetched: Learn TOU, learn.microsoft.com/robots.txt, azure-ai-docs LICENSE, GitHub Acceptable Use Policies.*
