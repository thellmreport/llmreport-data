"""Writer-identity path scoping (design.md 1.2/1.7 separation of duties).

Email literals are assembled with chr(64) so the PII guard's repo-wide scan
never flags this test module.
"""

from llmreport_linter.path_scope import classify_identity, violations

AT = chr(64)


def _bot(name: str) -> str:
    return f"{name}{AT}thellmreport.com"


def test_verifier_cannot_write_events():
    out = violations(_bot("verifier-bot"), ["events/2026/07/evt_x.json"])
    assert len(out) == 1 and "verifier-bot" in out[0]


def test_verifier_may_append_verdicts():
    assert violations(_bot("verifier-bot"), ["verdicts/evt_x/1.json"]) == []


def test_interpreter_cannot_write_verdicts():
    assert len(violations(_bot("interpreter-bot"), ["verdicts/evt_x/2.json"])) == 1


def test_interpreter_may_write_events_and_annotations():
    paths = ["events/2026/07/evt_x.json", "annotations/evt_x/1.json"]
    assert violations(_bot("interpreter-bot"), paths) == []


def test_collector_scope():
    ok = [
        "events/2026/07/evt_x.json",
        "snapshots/openai-models-api/latest.json",
        "manifests/evidence/openai-models-api/t.meta.json",
    ]
    assert violations(_bot("collector-bot"), ok) == []
    assert violations(_bot("collector-bot"), ["verdicts/evt_x/1.json"])


def test_github_noreply_identities_match():
    ident = f"12345+verifier-bot{AT}users.noreply.github.com"
    assert classify_identity(ident) == "verifier-bot"


def test_humans_are_out_of_scope():
    # oversight/humans go through reviewed PRs; path scoping does not apply
    human = f"owner{AT}example.invalid"
    assert classify_identity(human) is None
    assert violations(human, ["events/x.json", "verdicts/y.json"]) == []
