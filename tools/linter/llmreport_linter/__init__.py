"""llmreport-data store linter (design.md 1.2 / 1.4 / 1.7).

Deterministic, non-LLM. Required CI check on every merge:
- validates every store file against its JSON Schema (2020-12),
- enforces the immutable-event / append-only-verdict lifecycle invariants,
- enforces deterministic event-id minting rules and 72h duplicate-candidate windows,
- folds verdict/annotation chains into the computed effective status and
  emits derived/state.json for the site generator.
"""

from .identity import canonical_key_json, hash8, mint_event_id
from .status import derive_state, fold_verdicts, status_at

__all__ = [
    "canonical_key_json",
    "hash8",
    "mint_event_id",
    "derive_state",
    "fold_verdicts",
    "status_at",
]
