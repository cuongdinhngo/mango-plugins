#!/usr/bin/env python3
"""BUDGET — the call-count proxy, and the degradation ladder.

Stdlib only, no network. A call-count ceiling is a PROXY, not a measurement: mango's ledger measures
subagent dispatch only, so the largest term (main-loop spend) is invisible to the harness at runtime on
at least one host. This script does arithmetic on numbers the agent read out of the ledger; it invents
nothing, and with no history it says `unknown` and does not block.

Subcommands
  ceiling --rows "<fresh>/<calls>,..." [--budget <tokens>]
          per-call estimate = sum(fresh) / sum(calls); ceiling = budget / estimate.
          No rows, or no budget → `unknown`. Nothing is invented, nothing is blocked.
  check   --ceiling <n|unknown> --calls <n> [--projected <n>] [--at t0|mid-run]
          reports OK | APPROACHING | EXCEEDED | UNKNOWN and names the next ladder step.
  ladder  prints the degradation ladder in order.

Exit code is always 0: a budget proxy reports, it never kills a run mid-phase.
"""

import sys

# Ordered by measured cost against measured value. Step 1 is the ~90% term and the only lever that
# matters at scale; step 2 saves little and is a disclosure event more than a budget one; step 3
# degrades the review SEAT in three sub-steps and never to zero.
LADDER = [
    (
        "1-narrow-main-loop",
        "Reduce main-loop work first: narrow the scope, drop optional exploration fan-out, stop at "
        "the smallest complete change list. This is roughly 90% of run cost.",
    ),
    (
        "2-drop-challenger",
        "Drop the challenger (~58k per run). It saves little — record it in DISCLOSURE line one; "
        "this is a disclosure event more than a budget one.",
    ),
    (
        "3a-reviewer-max-to-reviewer",
        "Downgrade `reviewer-max` (Opus) to `reviewer` (Sonnet, ~108k per round). Findings are still "
        "grounded in the project rule book.",
    ),
    (
        "3b-reviewer-to-native-code-review",
        "Downgrade `reviewer` to the host's native `/code-review` on the PR (~62k). This is NOT a "
        "smaller reviewer: it does not read `.harness.json`, so it checks general standards rather "
        "than this project's codified rules. Record which step ran in DISCLOSURE.",
    ),
]

# Never on the ladder, at any budget. Named here so a future edit has to delete a line rather than
# forget one.
NEVER = [
    "the review seat (a degraded run without a review is not a cheaper run — it is a run whose "
    "defects are found later by the operator)",
    "the envelope (RUN CONTRACT / RECONCILE / DISCLOSURE — a small fraction of run cost and the only "
    "thing watching outside the diff)",
]

APPROACHING_AT = 0.8


def parse_rows(spec):
    """`"689200/164,638300/167"` → [(fresh, calls), ...]. A malformed row is dropped, never guessed."""
    rows = []
    for chunk in (spec or "").split(","):
        chunk = chunk.strip()
        if not chunk or "/" not in chunk:
            continue
        fresh, _, calls = chunk.partition("/")
        try:
            f, c = int(fresh.strip()), int(calls.strip())
        except ValueError:
            continue
        if c > 0:
            rows.append((f, c))
    return rows


def ceiling(rows, budget=None):
    """Return (ceiling, per_call_estimate, source) — ('unknown', 'unknown', reason) with no history."""
    if not rows:
        return "unknown", "unknown", "no ledger history for this tier — nothing invented, nothing blocked"
    per_call = round(sum(f for f, _ in rows) / sum(c for _, c in rows))
    source = f"{len(rows)} ledger row(s), {sum(c for _, c in rows)} call(s) total"
    if not budget or per_call <= 0:
        return "unknown", per_call, source + " — no token budget supplied, so no ceiling is derivable"
    return int(budget) // per_call, per_call, source


def check(ceiling_value, calls, projected=None, at="mid-run"):
    """Report status + the next ladder step. Never blocks, never dies mid-phase."""
    if str(ceiling_value) == "unknown":
        return (
            "UNKNOWN",
            "call-count ceiling unknown — no ledger history for this tier. The run proceeds; "
            "nothing is invented and nothing is blocked.",
            None,
        )
    ceil_n = int(ceiling_value)
    total = int(calls) + int(projected or 0)
    if total > ceil_n:
        step = LADDER[0] if at == "t0" else LADDER[0]
        return (
            "EXCEEDED",
            f"projected {total} call(s) against a ceiling of {ceil_n}"
            + (
                " — reported AT T0, before any work exists, not discovered mid-run."
                if at == "t0"
                else " — degrade per the ladder and complete the run."
            ),
            step,
        )
    if ceil_n and total >= ceil_n * APPROACHING_AT:
        return (
            "APPROACHING",
            f"{total} call(s) against a ceiling of {ceil_n} — degrade per the ladder, record it in "
            "DISCLOSURE, and complete the run. Never a mid-phase death.",
            LADDER[0],
        )
    return "OK", f"{total} call(s) against a ceiling of {ceil_n}", None


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 0
    cmd = argv[1]
    args = argv[2:]

    def opt(name, default=None):
        return args[args.index(name) + 1] if name in args else default

    if cmd == "ceiling":
        ceil_v, per_call, source = ceiling(parse_rows(opt("--rows")), opt("--budget"))
        print(f"BUDGET: call-ceiling {ceil_v} | per-call estimate {per_call} | source: {source}")
        print("BUDGET: a call-count ceiling is a PROXY, not a measurement — mango measures subagent "
              "dispatch only, and main-loop spend is the larger term.")
        return 0
    if cmd == "check":
        status, message, step = check(
            opt("--ceiling", "unknown"), opt("--calls", 0), opt("--projected"), opt("--at", "mid-run")
        )
        print(f"BUDGET: {status} — {message}")
        if step:
            print(f"BUDGET: next ladder step → {step[0]}: {step[1]}")
        return 0
    if cmd == "ladder":
        print("DEGRADATION LADDER (ordered by measured cost against measured value):")
        for name, text in LADDER:
            print(f"  {name}: {text}")
        print("NEVER degraded, at any budget:")
        for text in NEVER:
            print(f"  - {text}")
        return 0
    print(f"budget: unknown subcommand '{cmd}'")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
