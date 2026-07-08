# compliance

Imported compliance record for the source registry. The fetch library and
`registry/sources.json` are governed by these clearances (each source's
`tou_ref` points here); collection may only proceed within the binding
conditions each file states.

## tou-sweep-2026-07

One-time website-ToU sweep of every HTML host in the registry (design.md
§1.3, V-Q3 cond. 9), authored during the design phase and imported here
verbatim at repo creation. Each host-set clearance was independently
adversarially re-verified; seven of the eight carry a binding **verifier
dissent** (anthropic is a concurrence). The **required amendments from every
dissent were applied 2026-07-08** and each amended file re-verified — the
dissent sections are preserved verbatim as the audit record under an
"Amendments applied 2026-07-08" stamp. `00-sweep-summary.md` is the index:
the verdict table, the binding registry decisions (§2), and the Phase-0 open
items (§3).

**All eight verdicts are CONDITIONAL** — every clearance carries binding
conditions (host-scope locks, cadence caps, attribution/ShareAlike duties,
sentinels, counsel-sign-off gates). Notable postures to preserve:

- `docs.aws.amazon.com` cleared under the Site-Terms CC BY-SA 4.0 carve-out
  with an automated weekly lapse-sentinel (carve-out sentence **and** the AWS
  AUP); lapse → EXCLUDE → `ListFoundationModels` + Price List API fallback.
- `aws.amazon.com` legal pages: **Wayback-snapshot diffing is the plan of
  record**; direct fetch only on affirmative counsel sign-off.
- `x.ai`: Content-Signal `ai-input=no` applies **end-to-end** — no agent may
  receive x.ai page text at any pipeline stage; if a fully deterministic path
  is not architected by Phase 0 the host degrades to EXCLUDE pending written
  consent.
- Mistral: the Apache-2.0 GitHub mirror is the **primary** archive/diff
  source; `docs.mistral.ai` is liveness/parity only.
- Microsoft: `learn.microsoft.com` is primary; any GitHub route needs its own
  host-set clearance first (REST API, not `raw.githubusercontent.com`).

**Re-verification cadence:** the weekly robots/policy-page job and the
registry sentinels watch these hosts continuously; a full quarterly re-sweep
of every file is required. Any sentinel trip or dissent-flagged lapse routes
to the exceptions queue — collection never silently adapts to a changed term.

Do not edit these files as living documents: a changed verdict is a new dated
sweep, not an in-place rewrite.
