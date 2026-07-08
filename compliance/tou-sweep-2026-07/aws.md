# ToU Clearance — docs.aws.amazon.com (Amazon Bedrock User Guide)

**Sweep:** tou-sweep-2026-07 (design-phase legal deliverable, V-Q3 cond. 9)
**Host-set:** `docs.aws.amazon.com`
**Target paths:**
- `/bedrock/latest/userguide/doc-history.html` (Bedrock User Guide document history)
- `/bedrock/latest/userguide/model-lifecycle.html` (Bedrock model lifecycle / EOL page)
**Collector profile:** hourly conditional GETs, UA `TheLLMReportBot/1.0 (+https://thellmreport.com/bot)`, robots.txt honored, backoff, no bot-wall circumvention.
**Research date:** 2026-07-07. All quotes below were fetched live on that date unless marked otherwise.

---

## 1. Governing documents

| Document | URL | Fetch date | Version |
|---|---|---|---|
| AWS Site Terms | https://aws.amazon.com/terms/ | 2026-07-07 | "Last Updated: June 4, 2025" |
| AWS Acceptable Use Policy (dissent B1) | https://aws.amazon.com/aup/ | 2026-07-07 | "Last Updated: July 1, 2021" |
| docs.aws.amazon.com robots.txt | https://docs.aws.amazon.com/robots.txt | 2026-07-07 | live |
| CC BY-SA 4.0 legal code (incorporated by reference in Site Terms) | https://creativecommons.org/licenses/by-sa/4.0/legalcode.en | 2026-07-07 | 4.0 International |

**Does docs.aws.amazon.com display its own terms?** No separate terms document exists for the docs host. The static HTML of both target pages contains **no** terms/privacy/legal/license links or license metadata (verified by grepping the raw HTML fetched 2026-07-07; the only related element is an empty `<copyright class="copyright-print">` placeholder filled by JavaScript). The docs site chrome (JS resource bundle `https://docs.aws.amazon.com/assets/r/resources.404ba379ab61b40db88b.js`, fetched 2026-07-07) contains localized footer strings `<resource key="site-terms">Site terms</resource>` and `<resource key="terms-of-use-text">Terms of Use</resource>`, i.e. the rendered footer links to the AWS **Site Terms** — docs.aws.amazon.com is governed by the AWS Site Terms above, and by the license carve-out inside them (§3 below). Method note: WebFetch/markdown conversion strips the JS-rendered footer, so footer evidence is sourced from the raw HTML + the site's own JS resource bundle rather than a rendered screenshot (indirect but first-party).

---

## 2. AWS Site Terms — verbatim clauses

All quotes verified character-for-character against the raw HTML of https://aws.amazon.com/terms/ fetched 2026-07-07 (curl, 280,114 bytes), not from a summarizer.

### 2.1 Definition/scope of "AWS Site" (introductory paragraph; document has no numbered sections — headings are ALL-CAPS titles)

> "Welcome to the Amazon Web Services site (the "AWS Site"). Amazon Web Services, Inc. and/or its affiliates ("AWS") provides the AWS Site to you subject to the following terms of use ("Site Terms"). By visiting the AWS Site, you accept the Site Terms. Please read them carefully. In addition, when you use any current or future AWS services, content or other materials, you also will be subject to the AWS Customer Agreement or other agreement governing your use of our services (the "Agreement")."

There is no formal enumeration of which hostnames constitute the "AWS Site." However, the LICENSE AND SITE ACCESS section (§2.2) expressly names `docs.aws.amazon.com`, which confirms AWS treats the docs host as falling within the Site Terms' ambit — and simultaneously carves its materials out under an open license.

### 2.2 Section "LICENSE AND SITE ACCESS" — the scraping ban, the commercial-use ban, and the docs license carve-out (quoted in full)

> "AWS grants you a limited license to access and make personal use of the AWS Site and not to download (other than page caching) or modify it, or any portion of it, except with express written consent of AWS. This license does not include any resale or commercial use of the AWS Site or its contents; any derivative use of the AWS Site or its contents; any downloading or copying of any other users' account information; or any use of data mining, robots, or similar data gathering and extraction tools. Unless otherwise specified by AWS in a separate license, your right to use any software, data, documentation or other materials that you access or download through the AWS Site is subject to these Site Terms or, if you have an AWS account, the Agreement. **The materials hosted on docs.aws.amazon.com are licensed as follows: documentation (e.g., user guides, developer guides, other publications) is licensed under CC-BY-SA-4.0, while any code therein is licensed under MIT-0.** The AWS Site or any portion of the AWS Site may not be reproduced, duplicated, copied, sold, resold, visited, or otherwise exploited for any commercial purpose without express written consent or license of AWS. You may not frame or utilize framing techniques to enclose any trademark, logo, or other proprietary information (including images, text, page layout, or form) of AWS without express written consent. You may not use any meta tags or any other "hidden text" utilizing AWS's name or trademarks without the express written consent of AWS. Any unauthorized use terminates the permission or license granted by AWS. You are granted a limited, revocable, and nonexclusive right to create a hyperlink to the home page of the AWS Site, so long as the link does not portray AWS, or its products or services in a false, misleading, derogatory, or otherwise offensive matter. You may not use any AWS logo or other proprietary graphic or trademark as part of the link without express written permission."

(Bold added for emphasis; not in original. The bolded sentence was independently re-verified in the raw HTML: it appears verbatim, immediately after the "separate license" sentence and before the commercial-use sentence.)

### 2.3 The operative open license — CC BY-SA 4.0 (incorporated by the carve-out above)

CC BY-SA 4.0 legal code, fetched 2026-07-07 from https://creativecommons.org/licenses/by-sa/4.0/legalcode.en:

> §2(a)(1): "the Licensor hereby grants You a worldwide, royalty-free, non-sublicensable, non-exclusive, irrevocable license to exercise the Licensed Rights in the Licensed Material to: (A) reproduce and Share the Licensed Material, in whole or in part; and (B) produce, reproduce, and Share Adapted Material."

Conditions: §3(a) Attribution — if you Share the Licensed Material (including in modified form) you must retain creator identification, copyright notice, a reference to the license, the disclaimer notice, and a URI/hyperlink to the material, and indicate modifications. §3(b)(1) ShareAlike — "The Adapter's License You apply must be a Creative Commons license with the same License Elements, this version or later, or a BY-SA Compatible License." Note CC BY-SA 4.0 permits **commercial** use (no NC element).

### 2.4 AWS Acceptable Use Policy — scope and automated-access findings (dissent B1)

The AWS Acceptable Use Policy (https://aws.amazon.com/aup/, "Last Updated: July 1, 2021") is a governing document for docs.aws.amazon.com in its own right, not merely a services agreement — it expressly names the website:

> "governs your use of the services offered by Amazon Web Services, Inc. and its affiliates ("Services") and our website(s) including http://aws.amazon.com ("AWS Site")"

Verified content (re-checked 2026-07-07): the current revision contains **no** clause on crawling, robots, scraping, monitoring, or automated access — the pre-2021 AUP's "Monitoring or Crawling … that impairs or disrupts" network-abuse clause has been removed (search terms "crawling", "robot", "scraping", "Monitoring or Crawling" — zero hits).

Net effect: **supportive**. The only automated-access prohibition anywhere in AWS's website-governing documents remains the single Site Terms sentence analyzed in §2.2 and §5. Because a future AUP amendment could reintroduce a crawling ban and would today bypass a sentinel that watches only the Site Terms carve-out sentence, the sentinel (C5) is extended to also diff the AUP for any newly added automated-access clause.

---

## 3. robots.txt findings — docs.aws.amazon.com

Fetched 2026-07-07 via curl from https://docs.aws.amazon.com/robots.txt (3,567 bytes) and cross-checked with a second independent fetch. Structure:

- Single block: `User-agent: *` (applies to all crawlers including TheLLMReportBot)
- `Sitemap: https://docs.aws.amazon.com/sitemap_index.xml` (site invites indexing)
- 98 `Disallow` rules — all target deprecated API-version directories (e.g. `/AWSEC2/2006-06-26/`, `/AmazonCloudFront/2008-06-30/`) and utility paths (`/forms/`, `/en_pv/`, `/help-panel/`, `/search/`, `/freertos/archive/`, `/iot-expresslink/archive/`, `/cloudhsm/classic/`, `/awsaccountbilling/latest/about/`)
- `Crawl-delay: 5`
- **No rule mentions `/bedrock/` or any parent of our target paths.** Both `/bedrock/latest/userguide/doc-history.html` and `/bedrock/latest/userguide/model-lifecycle.html` are **permitted** for all user-agents.
- No bot-wall encountered: both target pages returned full static HTML to a plain curl fetch on 2026-07-07 (doc-history.html 103,891 bytes, "Latest documentation update: November 26th, 2025", history table current through June 30, 2026; model-lifecycle.html 30,353 bytes, `<title>Model lifecycle - Amazon Bedrock`).

Collector impact: 2 URLs/hour with conditional GETs is far inside `Crawl-delay: 5`; ensure inter-request spacing ≥ 5 s anyway (condition C2).

### 3.1 aws.amazon.com robots.txt (compliance-fetch scope only, dissent B2)

Checked by direct curl 2026-07-07: single `User-agent: *` block, 269 `Disallow` lines, none covering `/terms/` or `/aup/` — both compliance pages are robots-permitted on the marketing host. This finding is the basis for the C1 compliance-fetch carve-out (§6): low-frequency, identified-UA, robots-compliant fetches of these two legal pages for compliance verification (not HTML collection) are consistent with aws.amazon.com's own crawl policy, resolving the C1/C5 contradiction identified in dissent B2.

---

## 4. GitHub mirror investigation (awsdocs)

- GitHub repository search `org:awsdocs bedrock` via the GitHub API (https://api.github.com/search/repositories?q=org%3Aawsdocs+bedrock, fetched 2026-07-07): **total_count = 0**. No Bedrock docs repo exists in the awsdocs org.
- Cause: AWS retired the open-source GitHub documentation mirrors in June 2023 ("Retiring the AWS Documentation on GitHub," Jeff Barr, AWS News Blog, https://aws.amazon.com/blogs/aws/retiring-the-aws-documentation-on-github/ — repos archived starting week of June 5, 2023 because syncing 262 repos with internal sources was unsustainable; only code-sample repos were kept). Amazon Bedrock reached GA in September 2023, **after** the retirement, so a GitHub mirror of the Bedrock User Guide never existed.
- **Conclusion: the "ToU-clean GitHub alternative source" does NOT exist for Bedrock.** However, the same open license that made the GitHub mirrors clean (CC-BY-SA-4.0) now attaches to docs.aws.amazon.com itself, directly in the Site Terms (§2.2) — the licensing posture survived the mirror retirement and moved to the live host.

---

## 5. Analysis

**The tension.** The LICENSE AND SITE ACCESS section bans "any use of data mining, robots, or similar data gathering and extraction tools" and any "commercial use of the AWS Site or its contents." Read in isolation, that clause would exclude any scraper, ours included.

**Why the ban does not end the analysis for this host:**

1. **Express open license for exactly these materials.** The same section states the ban is subject to "a separate license" AWS may specify, then immediately specifies one: documentation on docs.aws.amazon.com is CC-BY-SA-4.0. CC BY-SA 4.0 §2(a)(1) is a worldwide, royalty-free, **irrevocable** grant to "reproduce and Share the Licensed Material, in whole or in part," including commercially. Our entire downstream use — private verbatim archives, public minimal excerpts, published diffs — is squarely within the grant, subject to attribution and ShareAlike.
2. **Express machine-readable crawl permission.** docs.aws.amazon.com publishes a robots.txt that allows all user-agents on our paths, sets a crawl-rate expectation (5 s), and advertises a sitemap index. This is an affirmative, host-specific signal that automated retrieval of these pages is expected and tolerated — more specific to the docs host than the generic Site Terms sentence, and it is the industry-standard mechanism AWS chose for expressing per-path crawl policy.
3. **Proportionality.** Two documentation pages, once per hour, with conditional GETs (mostly 304s), an identified UA, and backoff, is indistinguishable in load terms from a single human reader and is the precise conduct class robots.txt invites.
4. **The Acceptable Use Policy does not add a stricter restriction (dissent B1).** The AUP also governs the AWS Site (§2.4) but its current revision contains no crawling/scraping/monitoring/automated-access clause; it neither reinforces nor undercuts points 1–3, and the only operative automated-access prohibition in AWS's website-governing documents remains the single Site Terms sentence already analyzed.

**Residual risk (why not unconditionally CLEAR):** a literalist could argue CC-BY-SA-4.0 licenses the *use of the materials* while the robots clause separately governs the *method of access*, and that the Site Terms' scraping sentence therefore still reaches scripted collection. That reading is strained against robots.txt's express permission and would equally condemn every search engine indexing docs.aws.amazon.com, but the clause has never (to our knowledge) been construed by a court in this configuration, and the Site Terms are unilateral browsewrap AWS can amend at any time. The carve-out sentence itself could be removed in a future revision, and the AUP could be amended to add a crawling ban it currently lacks. These risks are managed by conditions, not exclusion — the sentinel (C5) now watches both documents on an automated weekly cadence (dissents B1/B3) — and a fully designed non-HTML fallback exists (Bedrock `ListFoundationModels` lifecycle fields + AWS Price List API), governed by the AWS Customer Agreement / API terms rather than the Site Terms, which caps worst-case downside at an engineering swap.

**Trademark/framing hygiene:** the CC license covers the *documentation content*, not AWS logos, page chrome, or trademarks. Excerpts must be text-only quotations; never reproduce AWS logos, page layout, or screenshots of the docs site; never frame docs pages.

---

## 6. VERDICT: **CONDITIONAL**

docs.aws.amazon.com (Bedrock User Guide `doc-history.html` and `model-lifecycle.html`) is cleared for the designed collector, subject to the following binding conditions:

- **C1 — Host scope lock.** Fetch only URLs under `docs.aws.amazon.com` for the HTML-collection pipeline. The CC-BY-SA-4.0 carve-out is host-specific; `aws.amazon.com` marketing/pricing pages have no such license and remain under the unmitigated scraping ban — they are OUT of scope for HTML collection (pricing changes come from the Price List API instead). **Compliance-fetch carve-out (dissent B2):** this scope lock governs the HTML-collection pipeline only. Low-frequency, robots-compliant, identified-UA fetches of AWS legal documents on `aws.amazon.com` (https://aws.amazon.com/terms/ and https://aws.amazon.com/aup/ — both robots-permitted, §3.1) for compliance verification are permitted and do **not** constitute "HTML collection" under this condition: results are evidence-manifest only, never published, never diffed publicly. Cadence for these compliance fetches is set by C5.
- **C2 — robots.txt compliance, live.** Re-fetch robots.txt each run (already designed); keep inter-request spacing ≥ 5 s per `Crawl-delay: 5`; halt collection automatically if any `/bedrock/` path becomes disallowed.
- **C3 — CC-BY-SA-4.0 compliance on the public layer.** Every public excerpt/diff derived from these pages must carry: attribution to "Amazon Web Services, Inc." with a hyperlink to the source page, a link to CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/), an indication that the excerpt is modified/excerpted, and — where the published diff constitutes Adapted Material — the diff content itself must be offered under CC BY-SA 4.0 or a compatible license (ShareAlike, §3(b)(1)). Confirm this is compatible with The LLM Report's publication licensing before Phase 0; if the product cannot ShareAlike its diff layer, restrict public output for this host to unmodified short verbatim quotations with attribution. **Termination mechanics (dissent B4):** CC BY-SA 4.0 §6(a) terminates the license automatically upon any failure to comply with §3(a)/(b) (attribution, ShareAlike); §6(b) permits reinstatement only via cure within 30 days of discovery of the violation, or express reinstatement by the licensor. A malformed attribution block on a published diff therefore momentarily strips the legal basis for that public output. Accordingly, the attribution/ShareAlike block MUST be a templated, tested component of the publishing pipeline (not hand-assembled per diff) before Phase 0 — this is a precondition of C3, not a stylistic preference.
- **C4 — Content-only excerpting.** Text quotations only; no AWS logos, trademarks-as-branding, page layout reproduction, framing, or screenshots of the docs site (Site Terms framing/trademark sentences remain fully applicable).
- **C5 — Carve-out sentinel.** **Automated, weekly (minimum monthly)** machine check that the sentence "The materials hosted on docs.aws.amazon.com are licensed as follows: documentation … is licensed under CC-BY-SA-4.0 …" remains present in the Site Terms (https://aws.amazon.com/terms/), with **auto-halt of the docs collector plus operator alert on any miss** (dissent B3 — tightened from quarterly-only, which left up to ~13 weeks of unlicensed hourly fetching exposed if the sentence were removed). **Scope extended to the AUP (dissent B1):** the same automated job must also diff https://aws.amazon.com/aup/ for any newly added automated-access/crawling/scraping/monitoring clause (none exists in the July 1, 2021 revision verified in §2.4); a newly added such clause triggers the same auto-halt + alert. A full quarterly human ToU re-sweep of both documents continues unchanged, at Phase 0 and thereafter. If the CC-BY-SA-4.0 carve-out sentence is removed, this verdict lapses to EXCLUDE and the collector must switch to the fallback: **Bedrock `ListFoundationModels` lifecycle fields + AWS Price List API diffs (already designed)**. Note CC BY-SA 4.0 is irrevocable for material already obtained (§2(a)(1)) — existing archives remain licensed — but future fetching would lose its basis.
- **C6 — No GitHub fallback.** Do not cite or rely on an awsdocs GitHub mirror for Bedrock; it does not exist (verified 2026-07-07, `org:awsdocs bedrock` → 0 repos; mirrors retired June 2023).
- **C7 — Verbatim archives stay private** (as designed). CC-BY-SA-4.0 would arguably permit publishing them with attribution, but keeping them private moots any argument about reproducing non-licensed page chrome and matches the sweep-wide evidence-manifest posture (public sha256 manifests only).

**Basis in one line:** AWS's own Site Terms (June 4, 2025 revision) expressly license all docs.aws.amazon.com documentation under CC-BY-SA-4.0, and the host's robots.txt expressly permits crawling our two target paths at ≥5 s spacing; the generic anti-robot sentence in the same Site Terms section is mitigated, not erased, hence CONDITIONAL rather than CLEAR.

---

*Prepared by compliance research agent, 2026-07-07. Evidence fetched live; raw-HTML verification performed for all load-bearing quotes (Site Terms clause, robots.txt, both target pages). Wayback Machine cross-check was attempted for the Site Terms but web.archive.org is unreachable from this environment; verification instead used direct raw-HTML fetch plus an independent search-engine corroboration of the CC-BY-SA-4.0 sentence.*

---

## Verifier dissent (2026-07-07)

**Amendments applied 2026-07-08** - every required change below is folded into the body above; import-ready.

Independent adversarial re-verification performed 2026-07-07 (separate agent, separate fetches). **Verdict class CONDITIONAL is affirmed — but the clearance is incomplete as issued and must be amended as stated below before Phase 0 import.** This section records both what verified and what must change.

### A. Independently re-verified (all load-bearing claims held)

| Claim | Re-verification result |
|---|---|
| Site Terms version | Confirmed: https://aws.amazon.com/terms/ "Last Updated: June 4, 2025" (re-fetched 2026-07-07). |
| Anti-robot sentence | Confirmed verbatim: "This license does not include any resale or commercial use of the AWS Site or its contents; any derivative use of the AWS Site or its contents; any downloading or copying of any other users' account information; or any use of data mining, robots, or similar data gathering and extraction tools." |
| CC-BY-SA-4.0 carve-out | Confirmed verbatim, character-for-character, in the live LICENSE AND SITE ACCESS section: "The materials hosted on docs.aws.amazon.com are licensed as follows: documentation (e.g., user guides, developer guides, other publications) is licensed under CC-BY-SA-4.0, while any code therein is licensed under MIT-0." |
| docs robots.txt | Confirmed by direct curl 2026-07-07: single `User-agent: *` block, exactly **98** `Disallow` lines (researcher's count correct), none matching `/bedrock/` or any parent, `Crawl-delay: 5`, `Sitemap: https://docs.aws.amazon.com/sitemap_index.xml`. |
| GitHub mirror absence (C6) | Confirmed live via GitHub API 2026-07-07: `org:awsdocs bedrock` → `total_count: 0`. |
| Governing law | Confirmed: Washington law; disputes > $7,500 to King County, WA courts; AWS reserves unilateral modification rights. Consistent with §5's browsewrap-amendment risk framing. |

No stricter clause was found in the Site Terms beyond those already quoted. The §5 analysis and the C1–C7 structure are sound as far as they go.

### B. Dissent items — what must change

**B1. The AWS Acceptable Use Policy was omitted and must be added to §1 (governing documents) and to the C5 sentinel scope.** The sweep spec requires ruling website-governing documents in or out; the AUP was never examined. Fetched 2026-07-07: https://aws.amazon.com/aup/ ("Last Updated: July 1, 2021") states it "governs your use of the services offered by Amazon Web Services, Inc. and its affiliates (\"Services\") and our website(s) including http://aws.amazon.com (\"AWS Site\")" — i.e., it expressly reaches the website, not just services. Verified content: the current revision contains **no** clause on crawling, robots, scraping, monitoring, or automated access (the pre-2021 AUP's "Monitoring or Crawling … that impairs or disrupts" network-abuse clause is gone; searched terms "crawling", "robot", "scraping", "Monitoring or Crawling" — zero hits). Net effect: **supportive** — the only automated-access prohibition anywhere in AWS's website-governing documents remains the single Site Terms sentence already analyzed. But because a future AUP amendment could reintroduce a crawling ban and would today bypass the C5 sentinel (which watches only the Site Terms carve-out sentence), the quarterly sentinel MUST also diff the AUP for any newly added automated-access clause. Required edits: add AUP row to §1 table; extend C5 accordingly.

**B2. C1/C5 internal contradiction must be resolved.** C5 (and B1's extension) requires periodically re-fetching https://aws.amazon.com/terms/ and https://aws.amazon.com/aup/ — both on `aws.amazon.com`, the host C1 declares under the "unmitigated scraping ban" and excluded from HTML collection. As drafted, executing C5 violates C1. Verified mitigation, 2026-07-07: aws.amazon.com robots.txt (`User-agent: *` block, 269 Disallow lines checked by direct curl) contains **no** rule covering `/terms/` or `/aup/` — both compliance pages are robots-permitted. Required edit: amend C1 to read that low-frequency (quarterly), robots-compliant, identified-UA fetches of AWS legal documents for compliance verification are permitted and are not "HTML collection" (never published, never diffed publicly, evidence-manifest only). Without this carve-out the conditions are not internally executable.

**B3. Sentinel cadence is too loose for an hourly collector.** A quarterly-only C5 check leaves up to ~13 weeks of continued hourly fetching after a hypothetical removal of the carve-out sentence — thousands of fetches with no license basis (robots.txt permission alone would then be the only cover, which §5 itself concedes is the weak reading). The collector already re-fetches robots.txt every run; the marginal cost of a sentence-level sentinel is trivial. Required edit: strengthen C5 to an **automated weekly** (at minimum monthly) check that the CC-BY-SA-4.0 carve-out sentence remains present in https://aws.amazon.com/terms/, with auto-halt of the docs collector plus operator alert on any miss, quarterly human re-sweep unchanged.

**B4. Record CC BY-SA 4.0 termination mechanics (one-line gap in C3).** The clearance rests entirely on the license; the file cites §2(a)(1) irrevocability but not §6(a): the license **terminates automatically** upon any failure to comply (attribution, ShareAlike), with reinstatement only via §6(b) (cure within 30 days of discovery, or express reinstatement). A malformed attribution block on published diffs would therefore momentarily strip the legal basis for the public layer. Required edit: note §6(a)/(b) in C3 and make the attribution/ShareAlike block a templated, tested component (not hand-assembled per diff) before Phase 0.

### C. Disposition

Verdict remains **CONDITIONAL** with conditions amended per B1–B4 (AUP added to governing documents and sentinel; C1 compliance-fetch carve-out; weekly automated carve-out sentinel; CC termination mechanics in C3). The original researcher's factual record is accurate — every load-bearing quote re-verified live — and no stricter clause exists in the Site Terms, AUP, or robots.txt. The dissent is to completeness and condition drafting, not to the outcome.

*Adversarial verifier, 2026-07-07. Independent fetches: aws.amazon.com/terms/ (WebFetch), aws.amazon.com/aup/ (WebFetch, twice — scope + full clause search), docs.aws.amazon.com/robots.txt (direct curl, 98 Disallows counted), aws.amazon.com/robots.txt (direct curl, grep for /terms/, /aup/, legal paths), api.github.com repo search (direct curl).*
