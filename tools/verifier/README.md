# llmreport_verifier — the verifier identity's deterministic pipeline

The only code in this repo that appends `verdicts/<event_id>/<seq>.json`
(design.md §1.4.3). Structurally separate from the collectors: they attach
corroboration as annotations and surface confirm-verdict **drafts** in run
reports (`corroborate.py`) but never write `verdicts/**`; this package never
writes anything else (writer path scoping, design.md §1.2/§1.7 — enforced in
CI by `llmreport_linter.path_scope` on the `verifier-bot` identity).

## What it confirms, deterministically

| Rule | Condition (all re-derived from store + registry; drafts are hints only) |
|---|---|
| (a) two-source | unconfirmed candidate with a `corroboration` annotation whose cited sources are recomputed as independent (different class **and** effective lineage) of the event's evidence; api-absence candidates additionally need an independent positive-statement class (§1.4.3c) |
| (c) provider-official | unconfirmed candidate whose own evidence is the provider's official machine-readable statement (`official-api` / `statuspage`, lineage `provider-primary`, not corroboration-only, not excluded); never for api-absence negative inferences |
| (b) direct-probe | **not implemented** — blocked on probe accounts (probe harness); schema + structure already accommodate it |

Conservative skips, by design: rolled-back / flap-damped candidates, open
discrepancies, already-confirmed (idempotent) and rejected candidates, and any
confirm whose cited evidence manifest is missing from the store (a verdict
must cite auditable evidence). Discrepancy resolution and reject verdicts are
the agent/owner review path, never this pipeline.

## Usage

```
uv run python -m llmreport_verifier --store . \
    --verified-by "actions:verify:$GITHUB_RUN_ID" \
    [--report reports/run-<ts>.json ...]   # drafts as review hints
    [--no-sweep] [--dry-run]
```

Default mode sweeps every event in the store (the corroboration annotations
carry all the state rule (a) needs, so the pipeline does not depend on run
reports existing). The verification report lands in `reports/verify-<ts>.json`
— a CI artifact, never committed. Workflow: `.github/workflows/verify.yml`
(TEMPLATE, gated on `VERIFY_ENABLED`, commits only `verdicts/**` via the
`verifier-bot` identity through the merge queue).
