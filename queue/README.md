# queue/ — exceptions-queue item files (design.md §5.3 Tier 1)

The production exceptions queue is GitHub issues (owner reviews them in the
weekly window). The deterministic watch jobs also write every item to a
durable file here so the record exists even where no token does:

    queue/<emitter>/<run-ts>.jsonl      one JSON object per line

- `<emitter>` is the writing job (`robots_recheck`, `sentinel`, ...).
- `<run-ts>` is the run's UTC RFC3339 timestamp with `:` → `-`.
- Files are per-run; a run never edits another run's file. No file = clean run.
- The invoking workflow (`robots-recheck.yml`, `sentinel.yml`) turns each
  line into one GitHub issue labeled `exceptions-queue`.

Item shape and the kind taxonomy are pinned in
`tools/watch/llmreport_watch/queue.py` (the module docstring is normative):
`queue`, `emitter`, `kind`, `severity` (notice|warning|critical), `subject`,
`title`, `source_ids`, `details`, `action_required`, `queued_at`,
`auto_publish` (always `false` — queue items never publish anywhere).
