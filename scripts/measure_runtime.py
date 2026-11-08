#!/usr/bin/env python3
"""measure_runtime.py — words of runtime text loaded by one full-lane run of mango.

Definition (one place; docs/WRITING.md links here). A *full run* is `solve` on a backend ticket at the
default cost tier, attended. It loads:

  - the seven full-lane skills: solve, refine, analysis, design, execute, review, finalise;
  - `PRINCIPLES.md`;
  - the principles those skills READ unconditionally: refine, git-isolation, learning-loop;
  - the working-doc template `templates/ticket.md`;
  - the agents every full run dispatches: implementer, reviewer, challenger.

Not counted: frontend companions and `principles/frontend-track.md` (frontend track only),
`reviewer-max` (max tier only), `explorer`/`extractor` (optional fan-out), other templates read on a
branch, the ticket and the project's own files. Words = whitespace-separated tokens, as `wc -w`.

Usage: python3 scripts/measure_runtime.py [--json]
Exit codes: 0 measured · 1 a listed file is missing or usage.
"""
import json
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent / "plugins" / "mango"

FULL_RUN = (
    [f"skills/{s}/SKILL.md" for s in ("solve", "refine", "analysis", "design", "execute", "review", "finalise")]
    + ["PRINCIPLES.md"]
    + [f"principles/{p}.md" for p in ("refine", "git-isolation", "learning-loop")]
    + ["templates/ticket.md"]
    + [f"agents/{a}.md" for a in ("implementer", "reviewer", "challenger")]
)


def measure():
    rows = []
    for rel in FULL_RUN:
        path = PLUGIN / rel
        if not path.is_file():
            raise FileNotFoundError(rel)
        rows.append((rel, len(path.read_text(encoding="utf-8").split())))
    return rows


def main(argv):
    if any(a not in ("--json",) for a in argv[1:]):
        print(__doc__)
        return 1
    try:
        rows = measure()
    except FileNotFoundError as exc:
        print(f"measure_runtime: listed file is missing: plugins/mango/{exc}")
        return 1
    total = sum(n for _, n in rows)
    if "--json" in argv:
        print(json.dumps({"files": dict(rows), "total_words": total}, indent=2))
        return 0
    for rel, n in rows:
        print(f"{n:>7}  {rel}")
    print(f"{total:>7}  RUNTIME WORDS: full run (solve, backend, default tier)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
