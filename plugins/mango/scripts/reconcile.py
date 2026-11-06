#!/usr/bin/env python3
"""RECONCILE — the harness runs the commands; the agent reads the verdict.

Stdlib only, no network, and it MUTATES NOTHING. Reads a RUN CONTRACT, executes each condition's
`check` command, and prints the counted line. Nothing here is narrated: every count comes from an exit
status this script observed.

  RECONCILE
    conditions: <n> declared | <m> re-run | <p> holding | <q> BROKEN | <u> UNBOUND | <c> could-not-run | <w> pending-merge

`could-not-run` is a THIRD state, distinct from HOLDING and BROKEN: the check's named shell was not on
PATH, so the check did not run at all. A check that cannot run must never report holding — a false
green exactly where nothing was verified — and it is not BROKEN either, because nothing observed the
predicate fail. It is UNVERIFIED, and is counted on its own axis.

`pending-merge` is a FOURTH state of the same kind: TREE-COMPARISON (the remote's base against the
remote's branch) has meaning only once the PR is merged, and an unattended run always closes BEFORE the
merge. Run at close it is BROKEN by construction on every correct run — a routine BROKEN that trains the
reader to skip the line meant to be read first. So at close it is NOT run and is counted
`pending-merge`: never HOLDING, never BROKEN, UNVERIFIED until `--phase post-merge` runs it.

Phases
  --phase t0     before any work exists. Every BOUND condition should be in its FAILING state against
                 the real world. One that reports HOLDING here is describing something other than this
                 run's work — it is struck, and the run does not start.
  --phase close  after the last push. `q > 0` does not block a merge in this version; it means READ
                 THIS FIRST. TREE-COMPARISON is counted `pending-merge`, not run.
  --phase post-merge
                 after the human merged the PR and fetched. Runs EVERY condition, TREE-COMPARISON
                 included: a BROKEN here means a commit landed on the branch beyond what the merge
                 carried, or something is stranded on this machine.

RETIRED in v1.14.0: `--prove`, the forced-case positive control. Across three field runs EVERY
condition reported FORCE-UNPROVEN: the `force-broken` / `force-holding` cases of the shipped floor are
literal `true`/`false` that cannot mutate real state, and genuinely forcing them would require
destructive acts (closing the PR, rewriting the branch) an unattended run may never perform. It was
measured to be inert, so it is gone rather than left as ceremony — and with nothing consuming them,
`force-broken` / `force-holding` are no longer contract grammar either. NOTHING REMAINING HERE MUTATES
GIT STATE: the only commands this script runs are each condition's `check`, and the shipped floor's
checks are read-only (`git diff --quiet`, `git rev-parse --verify`, `gh pr view`).

The `t0` run is KEPT and unchanged — it is the part that earned its claim: every bound condition
observed in its FAILING state against the real world before any work exists, in about two seconds.

Subcommands
  run             <contract> --phase t0|close|post-merge [--repo DIR]
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
PENDING_MERGE = "PENDING-MERGE"
PHASES = ("t0", "close", "post-merge")
# The floor condition whose meaning begins at the merge.
POST_MERGE_ONLY = "TREE-COMPARISON"


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


def reconcile(text, phase, repo=None):
    """Run every condition and return (lines, exit_status)."""
    if phase not in PHASES:
        raise ValueError(f"unknown phase '{phase}' — one of {', '.join(PHASES)}")
    header, conditions = parse(text)
    declared = len(conditions)
    rerun = holding = broken = unbound = could_not_run = pending = 0
    strikes = []
    details = []
    for cond in conditions:
        if (phase == "close" and cond["id"] == POST_MERGE_ONLY
                and cond["fields"].get("origin") == "floor"
                and not UNBOUND_RE.search(cond["fields"].get("check", ""))):
            state, output = PENDING_MERGE, "not run before the merge — run --phase post-merge after it"
        else:
            state, output = evaluate(cond, repo=repo)
        if state == PENDING_MERGE:
            pending += 1
        elif state == UNBOUND:
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

    lines = [
        "RECONCILE",
        f"  conditions: {declared} declared | {rerun} re-run | {holding} holding | "
        f"{broken} BROKEN | {unbound} UNBOUND | {could_not_run} could-not-run | "
        f"{pending} pending-merge",
        f"  phase     : {phase} | reviewer: {header.get('reviewer')} | "
        f"challenger: {header.get('challenger')} | branch: {header.get('branch')}",
    ]
    lines.extend(details)
    lines.extend(strikes)
    if phase == "close" and broken > 0:
        lines.append(
            "  READ THIS FIRST: a BROKEN condition describes the state of the world after the last "
            "push. It does not block the merge — this version stops at the PR and the human merges."
        )
    if phase == "post-merge" and broken > 0:
        lines.append(
            "  READ THIS FIRST: a BROKEN condition after the merge — a commit landed on the branch beyond "
            "what the merge carried, or something is stranded on this machine. A detail line reading "
            "'unknown revision' / 'bad revision' means a ref did not resolve (e.g. the remote branch was "
            "deleted at merge and pruned by the fetch): the condition is unverified, not shown broken."
        )
    if phase == "close" and pending > 0:
        remote = header.get("remote", "origin")
        lines.append(
            f"  PENDING MERGE: {pending} condition(s) not verified by this run — never holding. After "
            f"merging: git fetch {remote} && reconcile.py run <contract> --phase post-merge"
        )
    if phase in ("close", "post-merge") and could_not_run > 0:
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
            if "--prove" in args:
                print("reconcile: --prove was RETIRED in v1.14.0 — the forced-case positive control "
                      "reported FORCE-UNPROVEN on every condition across three field runs and is gone. "
                      "Re-run without it; the t0 run is unchanged.")
                return 1
            phase = opt("--phase", "close")
            if phase not in PHASES:
                print(f"reconcile: unknown phase '{phase}' — one of {', '.join(PHASES)}")
                return 1
            lines, status = reconcile(text, phase, repo=opt("--repo"))
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
    # Output is UTF-8 whatever the console's code page: the grammars carry ≥ and —, which a cp1252
    # console cannot encode, and a crash there would read as a checker that never ran.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
