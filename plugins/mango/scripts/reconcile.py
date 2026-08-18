#!/usr/bin/env python3
"""RECONCILE — the harness runs the commands; the agent reads the verdict.

Stdlib only, no network. Reads a RUN CONTRACT, executes each condition's `check` command, and prints
the two counted lines. Nothing here is narrated: every count comes from an exit status this script
observed.

  RECONCILE
    conditions: <n> declared | <m> re-run | <p> holding | <q> BROKEN | <u> UNBOUND | <c> could-not-run
    proven    : <b> shown BROKEN when forced | <h> shown HOLDING on a clean run

`could-not-run` is a THIRD state, distinct from HOLDING and BROKEN: the check's named shell was not on
PATH, so the check did not run at all. A check that cannot run must never report holding — a false
green exactly where nothing was verified — and it is not BROKEN either, because nothing observed the
predicate fail. It is UNVERIFIED, and is counted on its own axis.

Phases
  --phase t0     before any work exists. Every BOUND condition should be in its FAILING state against
                 the real world. One that reports HOLDING here is describing something other than this
                 run's work — it is struck, and the run does not start.
  --phase close  after the last push. `q > 0` does not block a merge in this version; it means READ
                 THIS FIRST.

  --prove        the forced-case positive control. For each condition: observe the pre-state, run
                 `force-holding` and require the check to report HOLDING, then run `force-broken` and
                 require it to FLIP to BROKEN. A case that does not flip is reported
                 FORCE-UNPROVEN and is NOT counted — a mutation that silently did not apply would
                 otherwise report a green that means nothing.

Subcommands
  run             <contract> --phase t0|close [--repo DIR] [--prove]
  merge-strategy  --repo DIR [--base main]

Exit codes: 0 ok · 2 the contract does not parse, or a t0 condition reports HOLDING · 1 usage/IO.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from run_contract import NO_SHELL, UNBOUND_RE, ContractError, parse, sh  # noqa: E402

HOLDING = "HOLDING"
BROKEN = "BROKEN"
UNBOUND = "UNBOUND"
COULD_NOT_RUN = "COULD-NOT-RUN"


def evaluate(cond, repo=None):
    """Run one condition's check. Exit 0 == HOLDING, anything else == BROKEN.

    A check whose named shell is not on PATH did not run at all: it is COULD-NOT-RUN, never HOLDING
    (a false green) and never BROKEN (nothing observed the predicate fail)."""
    check = cond["fields"].get("check", "")
    if UNBOUND_RE.search(check):
        return UNBOUND, "not bound — never run"
    status, output = sh(check, repo=repo)
    if status == NO_SHELL:
        return COULD_NOT_RUN, output
    return (HOLDING if status == 0 else BROKEN), output


def prove_one(cond, repo=None):
    """The forced-case positive control for one condition.

    Returns (shown_broken, shown_holding, notes). A case only counts when the check FLIPS: a
    force-holding that does not produce HOLDING, or a force-broken that does not produce BROKEN,
    proves nothing about the predicate and is reported instead of counted.
    """
    notes = []
    shown_broken = shown_holding = False
    fields = cond["fields"]
    if UNBOUND_RE.search(fields.get("check", "")):
        return False, False, [f"{cond['id']}: UNBOUND — not forceable yet"]
    if evaluate(cond, repo=repo)[0] == COULD_NOT_RUN:
        return False, False, [
            f"{cond['id']}: COULD-NOT-RUN — the named shell is unavailable, so the forced-case "
            "positive control cannot run and counts for nothing on either axis"
        ]

    sh(fields.get("force-holding", ""), repo=repo)
    state, _ = evaluate(cond, repo=repo)
    if state == HOLDING:
        shown_holding = True
    else:
        notes.append(
            f"{cond['id']}: FORCE-UNPROVEN — `force-holding` ran but the check still reports {state}; "
            "the mutation did not land, so a HOLDING elsewhere is not evidence"
        )

    sh(fields.get("force-broken", ""), repo=repo)
    state, _ = evaluate(cond, repo=repo)
    if state == BROKEN and shown_holding:
        shown_broken = True
    elif state != BROKEN:
        notes.append(
            f"{cond['id']}: FORCE-UNPROVEN — `force-broken` ran but the check still reports {state}; "
            "the mutation did not land and this forced case counts for nothing"
        )
    else:
        notes.append(
            f"{cond['id']}: FORCE-UNPROVEN — the check never reported HOLDING first, so the flip to "
            "BROKEN is unproven"
        )
    return shown_broken, shown_holding, notes


def reconcile(text, phase, repo=None, prove=False):
    """Run every condition and return (lines, exit_status)."""
    header, conditions = parse(text)
    declared = len(conditions)
    rerun = holding = broken = unbound = could_not_run = 0
    strikes = []
    details = []
    for cond in conditions:
        state, output = evaluate(cond, repo=repo)
        if state == UNBOUND:
            unbound += 1
        elif state == COULD_NOT_RUN:
            could_not_run += 1
        else:
            rerun += 1
            if state == HOLDING:
                holding += 1
            else:
                broken += 1
        details.append(f"    {cond['id']}: {state} — {output.splitlines()[0] if output else ''}"[:200])
        if phase == "t0" and state == HOLDING:
            strikes.append(
                f"    STRIKE {cond['id']}: reports HOLDING on an empty run — it describes something "
                "other than this run's work. Strike it before starting."
            )
        if phase == "t0" and state == COULD_NOT_RUN:
            strikes.append(
                f"    STRIKE {cond['id']}: COULD-NOT-RUN at t0 — the named shell is unavailable, so "
                "this run's preconditions cannot be verified. The run does not start."
            )

    shown_broken = shown_holding = 0
    notes = []
    if prove:
        for cond in conditions:
            b, h, n = prove_one(cond, repo=repo)
            shown_broken += int(b)
            shown_holding += int(h)
            notes.extend(n)

    lines = [
        "RECONCILE",
        f"  conditions: {declared} declared | {rerun} re-run | {holding} holding | "
        f"{broken} BROKEN | {unbound} UNBOUND | {could_not_run} could-not-run",
        f"  proven    : {shown_broken} shown BROKEN when forced | "
        f"{shown_holding} shown HOLDING on a clean run",
        f"  phase     : {phase} | challenger: {header.get('challenger')} | "
        f"branch: {header.get('branch')}",
    ]
    lines.extend(details)
    lines.extend(f"    {n}" for n in notes)
    lines.extend(strikes)
    if phase == "close" and broken > 0:
        lines.append(
            "  READ THIS FIRST: a BROKEN condition describes the state of the world after the last "
            "push. It does not block the merge — this version stops at the PR and the human merges."
        )
    if phase == "close" and could_not_run > 0:
        lines.append(
            f"  COULD NOT RUN: {could_not_run} condition(s) — the named shell was unavailable, so "
            "these are UNVERIFIED, not holding. A check that cannot run never reports holding; treat "
            "each as unknown and re-run it where the shell exists."
        )
    return lines, (2 if strikes else 0)


# --------------------------------------------------------------------------- merge strategy


def merge_strategy(repo, base="main"):
    """Read the merge strategy from RECENT FIRST-PARENT TOPOLOGY, and say what that does not settle.

    Never the host's allowed-strategy flags (they say what is PERMITTED, never what is USED) and never
    a whole-history merge count (which returns the pre-change answer when a repo switched strategy
    mid-history — in the dangerous direction). The window is: commits between the newest merge commit
    on the default branch and its tip.
    """
    status, newest = sh(f"git rev-list --first-parent --merges -n 1 {base}", repo=repo)
    if status != 0:
        return "unknown (cannot read first-parent topology)", -1
    newest = newest.strip().splitlines()[0] if newest.strip() else ""
    if not newest:
        return "squash-or-rebase (no merge commit anywhere in the first-parent history)", -1
    status, count = sh(f"git rev-list --count --first-parent {newest}..{base}", repo=repo)
    if status != 0:
        return "unknown (cannot count the first-parent window)", -1
    n = int(count.strip().splitlines()[0] or 0)
    if n == 0:
        return "merge-commits (the tip of the default branch IS a merge commit)", n
    return (
        f"squash-or-rebase ({n} first-parent commit(s) since the newest merge commit) — this "
        "narrows the judgement rather than removing it: a direct commit to the default branch "
        "looks the same",
        n,
    )


# --------------------------------------------------------------------------- cli


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    args = argv[2:]

    def opt(name, default=None):
        return args[args.index(name) + 1] if name in args else default

    try:
        if cmd == "run":
            text = open(args[0], encoding="utf-8").read()
            lines, status = reconcile(
                text, opt("--phase", "close"), repo=opt("--repo"), prove="--prove" in args
            )
            print("\n".join(lines))
            return status
        if cmd == "merge-strategy":
            verdict, _ = merge_strategy(opt("--repo", "."), opt("--base", "main"))
            print(f"MERGE STRATEGY: {verdict}")
            return 0
    except ContractError as exc:
        print("RECONCILE: the RUN CONTRACT does not parse — nothing was run.")
        for reason in exc.reasons:
            print(f"  - {reason}")
        return 2
    except OSError as exc:
        print(f"reconcile: {exc}")
        return 1
    print(f"reconcile: unknown subcommand '{cmd}'")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
