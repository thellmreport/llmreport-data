"""Phase 0 collectors for The LLM Report (design.md 1.3/1.4).

Four collectors, all network I/O through ``fetchkit.FetchClient`` ONLY:

- ``openrouter_models``  — openrouter.ai/api/v1/models        -> models-api snapshot
- ``litellm_prices``     — LiteLLM model_prices JSON           -> pricing-api snapshot
- ``status_openai``      — status.openai.com summary+incidents -> statuspage snapshots
- ``status_anthropic``   — status.claude.com history.atom feed  -> statuspage snapshots

Pipeline per source: fetch (evidence sidecar written by fetchkit) -> normalize
to the canonical snapshot (schemas/snapshots/*.v2.json) -> diff vs the prior
snapshot per tables/materiality.json -> mint candidate events with the
deterministic identity key (llmreport_linter.identity.mint_event_id — the
single sanctioned mint function). Lineage/class come from registry/sources.json.
Deltas that the materiality table does not classify, and aggregator model ids
with no entry in registry/model-aliases.json, go to the exceptions queue —
never auto-published (design.md 1.2.3).

The shared runner isolates every source: one failure never blocks the others.
"""

from .runner import COLLECTORS, CollectorSpec, SourceTask, run_all

__version__ = "0.1.0"

__all__ = ["COLLECTORS", "CollectorSpec", "SourceTask", "run_all"]
