# PROJ-820 — Add a `--verbose` flag to the export command

**Requirement:** The export command accepts a `--verbose` flag that prints per-row progress.

**Acceptance Criteria:**
- Running the export with `--verbose` prints one progress line per exported row.

## Context — the run has completed all five phases (for the finalise cost-ledger step)

This full-tier ticket has been through analysis → design → execute → review, dispatching the usual
subagents. The recorded per-dispatch token usage (one row transcribed from each dispatch return's
usage block — the harness surfaces a single figure per return, not an in/out split) was:

| Phase | Subagent / dispatch | Round | Tokens |
|-------|---------------------|-------|--------|
| analysis | Explore fan-out | 1 | 22k |
| review | reviewer | 1 | 68k |
| review | challenger (ticket-blind) | 1 | 64k |
| execute | extractor | 1 | 14k |

This fixture exercises the **Cost ledger**: mango records token usage **per phase and per subagent
dispatch** into the working doc as a **facts-only** counted artifact, and `finalise` surfaces a
one-line summary (total + top cost driver). The ledger is **descriptive, never normative** — it makes
the cost visible so a human can decide where to trim; it must **not** itself decide to cut a check, a
gate, a critic, or evidence detail.
