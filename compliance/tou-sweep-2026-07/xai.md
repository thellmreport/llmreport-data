# TOU Clearance: xAI — docs.x.ai

**Sweep:** tou-sweep-2026-07 (design-phase legal deliverable, V-Q3 cond. 9)
**Host in scope:** `docs.x.ai` (models page — our only xAI HTML source)
**Hosts already excluded:** `x.ai`, `status.x.ai` (both 403 to fetchers — bot-walled; we do not circumvent)
**Fetch/research date:** 2026-07-07
**Verdict:** **CONDITIONAL** (see conditions at end)

> Scope note: this clearance covers **fetching docs.x.ai only**. Publishing xAI probe
> numbers is separately blocked pending manual review of the xAI Enterprise/API terms at
> account signup (tracked outside this sweep).

---

## 1. Target accessibility

| Check | Result | Method / date |
|---|---|---|
| `https://docs.x.ai/docs/models` | **308 →** `https://docs.x.ai/developers/models` | direct curl, UA `TheLLMReportBot/1.0 (+https://thellmreport.com/bot)`, 2026-07-07 |
| `https://docs.x.ai/developers/models` | **200 OK** (no bot-wall for our UA) | direct curl, same UA, 2026-07-07 |
| docs.x.ai legal links | **Corrected per verifier dissent 1:** no persistent footer legal links, but the navigation dropdown menu (`data-dropdown-link`, alongside "llms.txt", "Discord", "Email support") contains a link labeled **"Terms and Policies" → `https://x.ai/legal`** | initial WebFetch render of `https://docs.x.ai/` and `/docs/models` missed it; verified in raw HTML of `https://docs.x.ai/`, 2026-07-07 |

**Action item:** collector config must target `https://docs.x.ai/developers/models` (the
canonical post-redirect URL) or follow the 308.

## 2. Governing documents

The docs site publishes no site-specific terms of its own. **Corrected per verifier
dissent 1:** it does link to xAI's legal documents — the docs.x.ai navigation dropdown
contains a link labeled "Terms and Policies" → `https://x.ai/legal` (verified in raw HTML
of `https://docs.x.ai/`, 2026-07-07). The applicable governing documents are xAI's
site-wide legal set, published on `x.ai` (footer "Legal: Terms · Enterprise Terms ·
Privacy · Cookies · AUP · Brand"):

| Document | URL | Effective date | How sourced |
|---|---|---|---|
| Terms of Service – Consumer | `https://x.ai/legal/terms-of-service` | **June 26, 2026** | **INDIRECT** — direct fetch 403 (bot-wall, not circumvented). Retrieved 2026-07-07 from Wayback snapshot 2026-07-03: `https://web.archive.org/web/20260703115056/https://x.ai/legal/terms-of-service` |
| xAI Acceptable Use Policy (AUP) | `https://x.ai/legal/acceptable-use-policy` | **June 26, 2026** | **INDIRECT** — direct fetch 403. Retrieved 2026-07-07 from Wayback snapshot 2026-07-03: `https://web.archive.org/web/20260703180025/https://x.ai/legal/acceptable-use-policy` |
| Enterprise Terms of Service | `https://x.ai/legal/terms-of-service-enterprise` | page shows "October 29, 2024" / "September 5, 2024" | **INDIRECT** — Wayback snapshot 2026-06-28: `https://web.archive.org/web/20260628170058/https://x.ai/legal/terms-of-service-enterprise`. **Not the governing doc for anonymous website fetches** (see §4); flagged for the separate API-terms review. |

Both the Consumer ToS and the AUP were re-issued effective **2026-06-26 — eleven days
before this sweep**. xAI revises these documents actively; see condition 6.

### Which document governs the website?

The Consumer ToS is the general website terms. Scope clause (intro, unnumbered):

> "These Terms of Service ("Terms") apply to your or others' access, interactions and/or
> use of Grok, Grokipedia, and xAI's other services for individuals, including associated
> applications, features, tools, software and **websites** (collectively, the "Service")."

It expressly carves out the enterprise side (intro, "Please note"):

> "Our Enterprise Terms of Service govern the use of our Services for developers and
> businesses, including xAI APIs and PromptIDE."

The Enterprise ToS, in turn, is a purchase-triggered subscription contract, not website
terms (intro):

> "This Agreement and is effective as of the date Customer makes the applicable purchase
> memorialized by an xAI online purchase confirmation (the "Effective Date")." [sic]

We hold no xAI account and make no purchase, so the Enterprise ToS does not bind our
anonymous fetches of docs.x.ai. The Consumer ToS (a browsewrap as applied to logged-out
website visitors, with imperfect dropdown-link notice on docs.x.ai — see §5.3) plus the
AUP it incorporates are the operative website terms.

## 3. Verbatim clauses touching automated access / scraping / republication

Neither document uses numbered sections; citations are by heading and bullet path.

### 3.1 Terms of Service – Consumer (eff. 2026-06-26)

**"Using our Service" → "What you cannot do":**

> "You may not access or use our Services to engage in, or help another person engage in,
> or promote any illegal, harmful, or abusive activities, or any other behavior that
> violates our Acceptable Use Policy."

**"xAI's Intellectual Property Rights" → "We own our Service":**

> "We and our affiliates own all rights, title, and interest in and to the Service."

**"Using our Service" → "When you use our Service, you understand and agree that:" (final bullet):**

> "At our sole discretion, we may implement rate limitations to accommodate system
> resources or usage needs."

**"Who Is Prohibited" (section ending; noted per verifier dissent, minor item):**

> "If you do not have a valid contract with us, you are prohibited from using our Service."

Circular as applied to anonymous visitors — it presupposes the contract whose formation is
at issue — but adversarially quotable.

Notable: the Consumer ToS itself contains **no clause on scraping, crawling, bots, or
automated access** (grep of the full captured text for scrap/crawl/automat/bot/spider/
harvest/data-mining: no prohibitory hits). All conduct restrictions are delegated to the
AUP.

### 3.2 xAI Acceptable Use Policy (eff. 2026-06-26)

Applicability (intro):

> "xAI's Acceptable Use Policy ("AUP") applies to anyone using our Service, including
> consumers, developers and businesses."

**"Comply with the law" → "Detrimentally impacting the Service, including by:" (bullets 1, 6, 7):**

> "Modifying, copying, translating, leasing, selling, reselling, distributing, distilling,
> manipulating, **using bots to access**, reverse engineer, decompile, disassemble or
> otherwise seek to obtain the source code of our Service, including our systems, models,
> or algorithms (except to the extent this restriction is prohibited by applicable law)"

> "**Scraping, harvesting or reselling any Input or Output**, or distilling model data or
> Outputs"

> "Disrupting, interfering with, or unauthorized access to the Service or its safety
> systems, including circumventing any rate limits or restrictions or protective measures
> and safety mitigations"

**"Comply with the law" → "Not complying with laws or regulations, including by:" (final bullet):**

> "**Accessing the Services through automated or non-human means, whether through a bot,
> script, or otherwise**"

(Emphasis added. Nesting verified against the raw archived HTML: the "automated or
non-human means" bullet sits under "Not complying with laws or regulations", a sibling of
the "Detrimentally impacting the Service" list.)

### 3.3 Enterprise ToS (for the record only — binds paying Customers, not this sweep)

Section 2 (use restrictions), relevant fragments:

> "Customer shall not, and shall not allow any third party … to: … (d) copy, modify or
> create derivative works from any Service or any Documentation; (e) scrape any User
> Content, distill model behavior, or remove or obscure any copyright or proprietary or
> other notice contained in any Service or Documentation; … (g) access or use any Services
> in a manner intended to circumvent or exceed service account limitations or requirements"

Clause (d)/(e) reach "Documentation" — material for the **API signup review**, since on
account creation we become a "Customer" and these restrictions attach.

## 4. robots.txt and Content Signals

### 4.1 `https://docs.x.ai/robots.txt` — fetched directly 2026-07-07, HTTP 200, verbatim:

```
User-agent: *
Allow: /

# Content Signals (draft) — declare AI/search usage preferences
# See: https://contentsignals.org/
Content-Signal: ai-train=no, search=yes, ai-input=yes

Sitemap: https://docs.x.ai/sitemap.xml
```

- **Our paths:** `/developers/models` (and everything else) — **allowed** (`Allow: /`, no
  Disallow, no Crawl-delay).
- **Content Signals (docs.x.ai):** `search=yes` (indexing/monitoring OK),
  `ai-input=yes` (feeding content to AI for real-time answers OK), **`ai-train=no`**
  (no model training on this content).
- Fetch anomaly for the record: one WebFetch attempt earlier on 2026-07-07 returned 404
  for this URL; three direct curl retrievals (our production UA, default curl UA, browser
  UA) all returned 200 with identical content. Treated as a transient/edge anomaly;
  collectors should re-fetch robots.txt each cycle and fail safe (assume most recent 200
  copy; if persistently 404, REP default = crawl permitted).

### 4.2 `https://x.ai/robots.txt` (apex — context only; host excluded) — fetched directly 2026-07-07, HTTP 200, verbatim:

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

Note the apex signals are stricter: **`ai-input=no`** on x.ai vs `ai-input=yes` on
docs.x.ai. Per-host signals govern per host. x.ai HTML remains excluded (403 bot-wall)
regardless.

### 4.3 `https://docs.x.ai/llms.txt` (added per verifier dissent — missed favorable fact)

docs.x.ai publishes `https://docs.x.ai/llms.txt` (HTTP 200, verified 2026-07-07), serving
the documentation in LLM-consumable form. It is linked in the same navigation dropdown
menu as "Terms and Policies". xAI thereby expressly invites automated/LLM consumption of
the exact content we monitor — this materially strengthens the implied-license argument
relied on in §5 and condition 4.

## 5. Analysis

1. **The robots layer expressly invites crawling.** docs.x.ai publishes `User-agent: *
   Allow: /` plus a sitemap, and declares Content Signals — directives that are only
   meaningful as instructions to automated agents. x.ai apex goes further and by name
   allows GPTBot, ClaudeBot, PerplexityBot et al. xAI's operative, machine-readable policy
   toward well-behaved bots on its public sites is permissive. docs.x.ai additionally
   publishes `llms.txt` (§4.3), expressly inviting automated/LLM consumption of the exact
   content we monitor — materially strengthening the implied-license argument (verifier
   dissent, missed favorable fact).

2. **The AUP contains two facial anti-bot clauses, not one** (rewritten per verifier
   dissent 2 — the original reading of the "using bots to access" bullet as limited to
   model/source exfiltration resolved a grammatical ambiguity in our own favor and is
   superseded). **(a)** "Accessing the Services through automated or non-human means,
   whether through a bot, script, or otherwise" (under "Not complying with laws or
   regulations"). **(b)** "using bots to access … our Service": the bullet's gerund series
   ("Modifying, copying, translating, …, manipulating, **using bots to access**") switches
   to bare infinitives at "reverse engineer, decompile, disassemble or otherwise seek to
   obtain the source code" — the natural parse attaches the gerunds directly to "**our
   Service**" (defined in the ToS to include "websites"), with the source-code phrase as a
   separate second series. Under that parse the AUP contains a second facial anti-bot
   clause, and it sits under "Detrimentally impacting the Service," a heading a court
   could read as aimed precisely at automated load. Read literally against the ToS
   definition of "Service", either clause would forbid all crawling of any xAI web
   property — a reading directly contradicted by xAI's own robots.txt/Content
   Signals/llms.txt and one that would also condemn every search engine xAI explicitly
   allows. Countervailing facts: one conditional GET per hour of one page is de minimis
   load, and xAI's own robots.txt invites crawlers. The Input/Output-scoped wording of
   the scraping bullet ("Scraping, harvesting or reselling any **Input or Output**" —
   defined terms meaning user prompts and model outputs; documentation pages are neither)
   remains a valid limiting argument for that bullet, but it does not neutralize either
   anti-bot clause.

3. **Assent posture: imperfect dropdown-link notice** (corrected per verifier dissent 1 —
   the prior "browsewrap at its weakest" characterization overstated our position and is
   superseded). The ToS/AUP bind on acceptance or on "access, interactions and/or use of"
   the consumer platform; we fetch anonymously, with no account and no click-through. But
   the docs.x.ai navigation dropdown carries a link labeled "Terms and Policies" →
   `https://x.ai/legal` — a labeled terms link on the very host we fetch gives xAI a
   colorable constructive-notice argument. It is not a persistent footer link, so notice
   is still imperfect under *Nguyen v. Barnes & Noble* standards. Combined with (1),
   enforcement risk for polite, identified, robots-compliant fetching of docs pages
   remains low — but the clauses exist and notice is arguable, so this cannot be a CLEAR.

4. **Our concrete conduct:** hourly conditional GETs of one docs page, single identified
   UA, backoff, robots.txt honored each cycle, no login, no Grok interaction, no rate-limit
   or bot-wall circumvention (x.ai and status.x.ai already excluded for exactly that
   reason). Published output is factual change data (model names, prices, dates — facts,
   not copyrightable expression) plus minimal quoted excerpts with attribution and sha256
   manifests; verbatim archives stay private. This aligns with `search=yes` monitoring
   use. Per verifier dissent 3: the publication limits cure *distribution* risk under the
   AUP "copying/distributing" bullet only; the hourly verbatim private archive is itself
   "copying" under the adverse parse of that bullet, regardless of what we publish —
   archival copying rests on the reliance stated in condition 4 (implied license,
   fair-use posture, de minimis scope). Risk accepted, not cured.

5. **Content Signals compliance:** our fetch library honors Content Signals. docs.x.ai
   requires `ai-train=no` — fetched xAI content must be flagged non-trainable in the
   archive pipeline. `ai-input=yes` permits LLM-assisted processing of docs.x.ai content
   (e.g., agent summarization of diffs). If any x.ai-apex content ever entered the pipeline
   (it should not), the stricter `ai-input=no` would additionally bar LLM processing of it.

6. **Risk profile — dispute terms (noted per verifier dissent, minor item):** the Consumer
   ToS specifies Texas law, N.D. Tex./Wichita/Tarrant venue, a class-action waiver, and a
   1-year federal limitations period. Any dispute would be litigated on those terms.

## 6. Verdict

**CONDITIONAL — cleared to fetch docs.x.ai subject to:**

1. **Fetch scope:** docs.x.ai only. `x.ai` and `status.x.ai` remain excluded (403
   bot-wall; we never circumvent). Target the canonical URL
   `https://docs.x.ai/developers/models` (or follow the 308 from `/docs/models`).
2. **robots.txt re-checked every crawl cycle** and obeyed; currently `Allow: /`. If
   docs.x.ai later blocks `*` or our UA, or starts 403ing our fetches, treat as revocation
   of permission and stop — no UA rotation, no circumvention.
3. **Content-Signal `ai-train=no` enforced:** all content fetched from docs.x.ai is tagged
   non-trainable in the archive/pipeline; never used for model training. `ai-input=yes`
   permits LLM processing of docs.x.ai content; x.ai-apex content (excluded anyway) would
   carry `ai-input=no`.
4. **Publication limits and archival-copying reliance** (rationale rewritten per verifier
   dissent 3): diffs restricted to facts (model ids, prices, dates, deprecations) plus
   minimal attributed excerpts; verbatim page archives remain private (evidence manifests
   public as sha256 only). No republication of substantial portions. These publication
   limits cure *distribution* risk under the AUP "copying/distributing" bullet and keep
   publication clear of the ToS IP clause; they do not cover the private archives. The
   hourly verbatim private archive is itself "copying" under the adverse parse of the
   same bullet, regardless of what we publish. Archival copying relies on: (a) implied
   license from `Allow: /` robots.txt + Content-Signal `ai-input=yes`, reinforced by
   llms.txt (§4.3); (b) fair-use posture (factual monitoring, non-substitutive, private,
   minimal scope); (c) de minimis single-page scope. Risk accepted, not cured.
5. **AUP anti-bot clause risk accepted, not cleared** (broadened per verifier dissents
   1–2): the AUP (eff. 2026-06-26) contains **two** facial anti-bot clauses — (a)
   "[a]ccessing the Services through automated or non-human means, whether through a bot,
   script, or otherwise" (under "Not complying with laws or regulations") and (b) "using
   bots to access … our Service" under the natural parse of the "Detrimentally impacting
   the Service" bullet (§5.2). We rely on the robots.txt/Content Signals/llms.txt
   permission, the Input/Output-scoped wording of the scraping clause, the de minimis
   load of one conditional GET per hour, and **imperfect dropdown-link notice** (not
   "weak browsewrap assent" — docs.x.ai's nav dropdown links "Terms and Policies" →
   `https://x.ai/legal`; §5.3). Any contact from xAI (legal notice, UA block, robots
   change) escalates to counsel and suspends the collector.
6. **Legal-page watch:** ToS and AUP were re-issued 2026-06-26 (11 days before this
   sweep). Re-run this clearance if either document's effective date changes; recommend
   adding `x.ai/legal/*` effective-date checks (via Wayback, not direct fetch) to the
   quarterly compliance review.
7. **Separate block stands:** publishing xAI probe numbers stays blocked pending the
   manual Enterprise/API terms review at account signup (Enterprise ToS §2(d)–(e) reach
   "Documentation" and "User Content" once we become a Customer).

---

## Appendix: sourcing log

| Item | Method | Date | Result |
|---|---|---|---|
| `https://docs.x.ai/robots.txt` | direct curl ×3 (bot UA / curl UA / browser UA) | 2026-07-07 | 200; verbatim above (one earlier WebFetch 404, treated as transient) |
| `https://x.ai/robots.txt` | direct curl (bot UA) | 2026-07-07 | 200; verbatim above |
| `https://docs.x.ai/docs/models` | direct curl (bot UA) | 2026-07-07 | 308 → `/developers/models` → 200 |
| `https://x.ai/legal/terms-of-service` | direct WebFetch | 2026-07-07 | **403** (bot-wall; not circumvented) |
| same, Wayback `20260703115056` | curl via web.archive.org (`id_` raw) | 2026-07-07 | 200; full text captured; "Effective: June 26, 2026" |
| `https://x.ai/legal/acceptable-use-policy`, Wayback `20260703180025` | curl via web.archive.org (`id_` raw) | 2026-07-07 | 200; full text captured; "Effective: June 26, 2026"; bullet nesting verified in raw HTML |
| `https://x.ai/legal/terms-of-service-enterprise`, Wayback `20260628170058` | curl via web.archive.org (`id_` raw) | 2026-07-07 | 200; §2 restrictions captured |
| docs.x.ai legal-link check | WebFetch (`/` and `/docs/models`); corrected by verifier raw-HTML review of `https://docs.x.ai/` | 2026-07-07 | **Corrected per dissent 1:** no persistent footer links, but nav dropdown contains "Terms and Policies" → `https://x.ai/legal` |
| `https://docs.x.ai/llms.txt` | live fetch (verifier re-verification) | 2026-07-07 | 200; documentation in LLM-consumable form; linked in same nav menu as "Terms and Policies" |

---

## Verifier dissent (2026-07-07)

**Amendments applied 2026-07-08** - every required change below is folded into the body above; import-ready.

Independent adversarial re-verification (second reviewer). Re-fetched: the same Wayback
`id_` raw snapshots of the Consumer ToS (`20260703115056`) and AUP (`20260703180025`);
live `https://docs.x.ai/robots.txt`; live `https://docs.x.ai/` (308 → `/overview`);
live `https://docs.x.ai/llms.txt`; Wayback CDX history for both legal URLs (2026-06-01
→ 2026-07-07). All on 2026-07-07.

**What checks out.** Every clause quoted in §3 is verbatim-accurate against the raw
archived HTML. Effective dates (both 2026-06-26) confirmed. The anti-bot bullet's nesting
under "Not complying with laws or regulations" confirmed. The Consumer ToS's lack of any
scraping/bot/crawl prohibition confirmed by independent full-text review. robots.txt
matches §4.1 byte-for-byte (fetched 2026-07-07, HTTP 200). CDX confirms the snapshots
used are the **newest that exist** for both documents — the quotes are current as of the
last Wayback capture (2026-07-03), post-dating the 2026-06-26 re-issue.

**Dissent 1 — factual error: docs.x.ai DOES link to xAI's legal documents.** §1 (table)
and §2 state the docs site "links to no ToS/ToU/AUP/privacy page" / "publishes no
site-specific terms and links to none." False. The docs.x.ai navigation (dropdown menu,
`data-dropdown-link`, alongside "llms.txt", "Discord", "Email support") contains a link
labeled **"Terms and Policies" → `https://x.ai/legal`** (verified in raw HTML of
`https://docs.x.ai/` on 2026-07-07). This is not a persistent footer link — notice is
still imperfect under *Nguyen v. Barnes & Noble* standards — but "browsewrap at its
weakest" (§5.3) overstates our position. A labeled terms link on the very host we fetch
gives xAI a colorable constructive-notice argument. §1, §2, §5.3, and the sourcing-log
row above must be corrected; the assent pillar of condition 5 must be downgraded from
"weak browsewrap assent" to "imperfect dropdown-link notice."

**Dissent 2 — the "using bots to access" clause is mischaracterized.** §5.2 reads the
AUP bullet as "'using bots to access … source code of our Service' targets model/source
exfiltration." That resolves a grammatical ambiguity in our own favor without flagging
it. The bullet's gerund series ("Modifying, copying, translating, …, manipulating,
**using bots to access**") switches to bare infinitives at "reverse engineer, decompile,
disassemble or otherwise seek to obtain the source code" — the natural parse attaches the
gerunds directly to "**our Service**" (defined in the ToS to include "websites"), with
the source-code phrase as a separate second series. Under that parse the AUP contains a
**second facial anti-bot clause** — "using bots to access … our Service" — and it sits
under "Detrimentally impacting the Service," a heading a court could read as aimed
precisely at automated load. (Countervailing fact worth stating: one conditional GET per
hour of one page is de minimis load, and xAI's own robots.txt invites crawlers.)
Condition 5's accepted-risk framing cites only the "automated or non-human means" clause;
it must be broadened to name both clauses.

**Dissent 3 — condition 4 does not cover the private archives.** Condition 4 claims the
publication limits keep us "clear of the AUP 'copying/distributing' bullet." Publication
limits cure *distribution* risk only. The hourly **verbatim private archive is itself
"copying"** under the adverse parse of the same bullet ("copying … our Service"),
regardless of what we publish. The file must state the actual reliance for archival
copying explicitly: (a) implied license from `Allow: /` robots.txt + Content-Signal
`ai-input=yes`; (b) fair-use posture (factual monitoring, non-substitutive, private,
minimal scope); (c) de minimis single-page scope. Risk accepted, not cured by condition 4
as written.

**Missed favorable fact — llms.txt.** docs.x.ai publishes `https://docs.x.ai/llms.txt`
(HTTP 200, verified 2026-07-07), serving the documentation in LLM-consumable form and
linked in the same nav menu as "Terms and Policies." xAI thereby expressly invites
automated/LLM consumption of the exact content we monitor. This materially strengthens
the implied-license argument and belongs in §4/§5 and the sourcing log.

**Minor:** the Consumer ToS "Who Is Prohibited" section ends "If you do not have a valid
contract with us, you are prohibited from using our Service" — circular as applied to
anonymous visitors but adversarially quotable; note it. Dispute terms (Texas law, N.D.
Tex./Wichita/Tarrant venue, class-action waiver, 1-year federal limitations) are worth a
line in the risk profile.

**Verdict position: CONDITIONAL affirmed — but only as amended above.** CLEAR is
impossible (two facial anti-bot readings, not one). EXCLUDE is not warranted: robots.txt
expressly allows all crawlers, Content-Signals and llms.txt contemplate automated and AI
consumption of this exact content, notice remains imperfect, and the conduct is
one identified conditional GET per hour with stop-on-block. Required changes before this
clearance is relied on at Phase 0: correct the docs.x.ai legal-link claim (§1, §2, §5.3,
sourcing log); broaden condition 5 to name both anti-bot clauses and the corrected assent
posture; rewrite condition 4's rationale to state the archival-copying reliance; add
llms.txt as evidence. — Verifier, 2026-07-07
