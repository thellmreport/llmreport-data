"""llmreport_watch — scheduled watch jobs for llmreport-data (Phase 1a).

Modules (each is a standalone ``python -m llmreport_watch.<name>`` CLI):

    robots_recheck  weekly robots.txt stance sweep across every directly
                    fetched registry host (sentinel global-robots-stance-diff,
                    design.md §1.3 [V-Q3 cond. 7]), incl. Content Signals
    sentinel        weekly compliance sentinels driven by the registry
                    ``sentinels`` records (aws-carveout verdict-lapse watch,
                    mistral-legal-hub-watch)
    heartbeat       healthchecks.io dead-man pings (design.md §5.3); wired
                    into the collector runner
    queue           the exceptions-queue JSONL file convention (design.md
                    §5.3 Tier 1) shared by the watch jobs

All source fetching goes through fetchkit against registry/sources.json —
never a caller-supplied URL, never an excluded host. Kept import-light on
purpose: consumers import the submodule they need.
"""

__version__ = "0.1.0"
