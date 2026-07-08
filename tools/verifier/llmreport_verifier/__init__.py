"""llmreport_verifier - the verifier identity's deterministic pipeline (design.md 1.4.3).

The ONLY code in this repo that appends verdicts/<event_id>/<seq>.json.
Structurally separate from the collectors (which attach corroboration as
annotations and surface confirm-verdict DRAFTS in run reports, never writing
verdicts/**) - dual-agent separation of duties, design.md 1.2/1.7.
"""

from .pipeline import Decision, Verifier, draft_event_ids
from .storeio import VerifierStore

__all__ = ["Decision", "Verifier", "VerifierStore", "draft_event_ids"]
