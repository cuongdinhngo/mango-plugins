#!/usr/bin/env python3
"""Test suite for the plugin's harness scripts — RUN CONTRACT, RECONCILE, BUDGET, CHECK-LINES, PROOF,
TICKET-STATS.

The first three are the autorun envelope; CHECK-LINES (v1.13.0) verdicts the counted lines in a
working doc. All four live in `plugins/mango/scripts/` and are gated by this one command.

Stdlib `unittest` only, no network, no `claude -p` dispatch: free and deterministic, so it runs on
every edit rather than once a month. Every git test builds its own throwaway repo under `tempfile` and
destroys it; the live checkout is never touched.

Run:  python3 tests/envelope/test_envelope.py
"""

import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "plugins" / "mango" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import budget  # noqa: E402
import reconcile  # noqa: E402
import run_contract as rc  # noqa: E402
import ticket_stats  # noqa: E402


# --------------------------------------------------------------------------- helpers

FLOOR_BLOCK = """  CONDITION PR-EXISTS
    statement: the PR exists and its state is readable
    origin: floor
    derived-by: {pr_derive}
    value: {pr_value}
    check: {pr_check}
  END CONDITION
  CONDITION TREE-COMPARISON
    statement: no commit landed on the branch beyond what the PR carries (tree comparison)
    origin: floor
    derived-by: {tree_derive}
    value: {tree_value}
    check: {tree_check}
  END CONDITION
  CONDITION LOCAL-HEAD-PUSHED
    statement: nothing is stranded on this machine: local branch head == the remote's
    origin: floor
    derived-by: git rev-parse HEAD
    value: abc123 (exit 0)
    check: {head_check}
  END CONDITION
"""

DEFAULTS = dict(
    pr_derive="gh pr view 1 --json state",
    pr_value="OPEN (exit 0)",
    pr_check="gh pr view 1 --json state",
    tree_derive="git rev-parse main",
    tree_value="deadbee (exit 0)",
    # v1.21.0 — the two generated floor checks, exactly as `run_contract.py write` renders them
    # (TREE-COMPARISON bound at Gate 2 to the approved change list).
    tree_check=rc.tree_check("main", "feat/PROJ-1-x", "origin", "a.txt"),
    head_check=rc.head_check("feat/PROJ-1-x", "origin"),
    base="main@deadbee",
    branch="feat/PROJ-1-x",
)


# The same shape against `main`, for tests that build a repo rather than a branch.
HEAD_MAIN_CHECK = (
    "git rev-parse --verify main >/dev/null 2>&1 && "
    "git rev-parse --verify origin/main >/dev/null 2>&1 && "
    'test "$(git rev-parse main)" = "$(git rev-parse origin/main)"'
)


def contract(extra_conditions="", floor=True, **overrides):
    """A well-formed contract, plus whatever the test wants to break."""
    fields = dict(DEFAULTS)
    fields.update(overrides)
    header = (
        "RUN CONTRACT v1\n"
        "  key: PROJ-1\n"
        "  started: 2026-08-16T23:00:00Z\n"
        "  plugin-version: 1.11.0\n"
        "  plugin-path: /plugins/mango\n"
        "  repo: /repo\n"
        f"  base: {fields['base']}\n"
        f"  branch: {fields['branch']}\n"
        "  remote: origin\n"
        "  merge-strategy: squash-or-rebase (recent first-parent topology)\n"
        f"  reviewer: {overrides.get('reviewer', 'on')}\n"
        f"  challenger: {overrides.get('challenger', 'on')}\n"
        f"  handover-authorisation: {overrides.get('handover_authorisation', 'approved 22:58 — push feat/PROJ-1-x, open the PR; nothing else')}\n"
        f"  call-ceiling: {overrides.get('call_ceiling', '140')}\n"
        "  per-call-estimate: 3100\n"
        "  ceiling-source: 4 ledger row(s), 567 call(s) total\n"
        "  token-budget: unmeasured (host surfaces no usage)\n"
    )
    body = FLOOR_BLOCK.format(**fields) if floor else ""
    return header + body + extra_conditions + "END RUN CONTRACT\n"


def simple_condition(cid, check, origin="agent"):
    return (
        f"  CONDITION {cid}\n"
        f"    statement: {cid} holds\n"
        f"    origin: {origin}\n"
        f"    derived-by: {rc.AGENT_CLAIM}\n"
        f"    value: stated by the agent\n"
        f"    check: {check}\n"
        "  END CONDITION\n"
    )


def git(repo, *args):
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
        cwd=repo, capture_output=True, text=True,
    )


def new_repo(path):
    os.makedirs(path, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    Path(path, "a.txt").write_text("one\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "init")
    return path


# --------------------------------------------------------------------------- T1/T2 grammar


class TestGrammar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_valid_contract_parses(self):
        rc.validate(contract(), "t0")

    def test_T7_a_contract_carrying_force_broken_is_REJECTED_not_ignored(self):
        """v1.14.0 B / T7 — the forced-case fields are retired. A contract still carrying one is
        rejected with a named reason: tolerating and silently ignoring it would leave a field nothing
        consumes looking like a live requirement."""
        text = contract().replace(
            "    check: gh pr view 1 --json state\n",
            "    check: gh pr view 1 --json state\n    force-broken: gh pr close 1\n", 1)
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("force-broken" in r and "RETIRED" in r for r in ctx.exception.reasons))

    def test_T7_force_holding_is_rejected_the_same_way(self):
        text = contract().replace(
            "    check: gh pr view 1 --json state\n",
            "    check: gh pr view 1 --json state\n    force-holding: gh pr reopen 1\n", 1)
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("force-holding" in r and "RETIRED" in r for r in ctx.exception.reasons))

    def test_the_forced_case_fields_are_not_condition_grammar(self):
        self.assertNotIn("force-broken", rc.CONDITION_KEYS)
        self.assertNotIn("force-holding", rc.CONDITION_KEYS)
        self.assertEqual(rc.RETIRED_CONDITION_KEYS, ("force-broken", "force-holding"))

    def test_F_reviewer_must_be_on_or_off(self):
        """v1.14.0 F — the reviewer is a seat the contract records, exactly as the challenger is."""
        rc.validate(contract(reviewer="off"), "t0")
        with self.assertRaises(rc.ContractError):
            rc.validate(contract(reviewer="sometimes"), "t0")

    def test_F_a_contract_missing_the_reviewer_seat_does_not_parse(self):
        text = contract().replace("  reviewer: on\n", "")
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("reviewer" in r for r in ctx.exception.reasons))

    def test_T2_unbound_survives_past_gate2_is_refused(self):
        """T2 — an UNBOUND placeholder surviving past Gate 2: re-validation refuses."""
        text = contract(
            extra_conditions=simple_condition(
                "PROVING-TEST", "UNBOUND ${TEST_CMD}")
        )
        rc.validate(text, "t0")  # allowed at t0 — the value cannot exist before the change
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "gate2")
        self.assertTrue(any("UNBOUND" in r for r in ctx.exception.reasons))

    def test_T2_bind_resolves_then_parses(self):
        text = contract(
            extra_conditions=simple_condition("PROVING-TEST", "UNBOUND ${TEST_CMD}")
        )
        bound = rc.bind(text, {"TEST_CMD": "pytest -k proving"}, "gate2")
        self.assertIn("check: pytest -k proving", bound)

    def test_T2_bind_refuses_a_partial_binding(self):
        text = contract(
            extra_conditions=simple_condition("PROVING-TEST", "UNBOUND ${TEST_CMD}")
            + simple_condition("SECOND", "UNBOUND ${OTHER}")
        )
        with self.assertRaises(rc.ContractError):
            rc.bind(text, {"TEST_CMD": "pytest"}, "gate2")

    def test_unbound_without_a_placeholder_does_not_parse(self):
        text = contract(extra_conditions=simple_condition("X", "UNBOUND"))
        with self.assertRaises(rc.ContractError):
            rc.validate(text, "t0")

    def test_unknown_field_does_not_parse(self):
        text = contract().replace("    origin: floor\n", "    origin: floor\n    severity: high\n", 1)
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("severity" in r for r in ctx.exception.reasons))

    def test_challenger_must_be_on_or_off(self):
        text = contract().replace("  challenger: on\n", "  challenger: maybe\n")
        with self.assertRaises(rc.ContractError):
            rc.validate(text, "t0")

    def test_ceiling_is_an_integer_or_the_literal_unknown(self):
        rc.validate(contract(call_ceiling="unknown"), "t0")
        with self.assertRaises(rc.ContractError):
            rc.validate(contract(call_ceiling="about 140"), "t0")


# --------------------------------------------------------------------------- the fixed floor


class TestFloor(unittest.TestCase):
    def test_a_dropped_floor_condition_does_not_parse(self):
        text = contract(floor=False, extra_conditions=simple_condition("X", "true"))
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("PR-EXISTS" in r for r in ctx.exception.reasons))

    def test_a_floor_condition_re_authored_as_agent_origin_does_not_parse(self):
        text = contract().replace(
            "    statement: the PR exists and its state is readable\n    origin: floor\n",
            "    statement: the PR exists and its state is readable\n    origin: agent\n",
        )
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("origin: floor" in r for r in ctx.exception.reasons))

    def test_T4_ancestry_predicate_is_refused_at_contract_time(self):
        """T4 — an ancestry predicate is a false-red under squash; it never reaches RECONCILE."""
        text = contract(tree_check="git merge-base --is-ancestor feat/PROJ-1-x main")
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("ancestry" in r for r in ctx.exception.reasons))

    def test_T4_content_grep_is_refused_at_contract_time(self):
        """T4 — a grep looks for content named at t0; a post-merge correction is unnamed then."""
        text = contract(tree_check="git show main:a.txt | grep -q 'the fix'")
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("grep" in r for r in ctx.exception.reasons))

    def test_local_head_condition_must_name_the_remote(self):
        text = contract(head_check="test \"$(git rev-parse HEAD)\" = \"$(git rev-parse main)\"")
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("remote" in r for r in ctx.exception.reasons))

    def test_an_unverified_rev_parse_comparison_is_refused(self):
        """Caught by this suite while writing it: when BOTH `git rev-parse` lookups fail (a branch
        that does not exist, a repo with no remote), `test "$(...)" = "$(...)"` compares empty to
        empty and reports HOLDING. A false green precisely where nothing was pushed."""
        text = contract(
            head_check='test "$(git rev-parse x)" = "$(git rev-parse origin/x)"'
        )
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("--verify" in r for r in ctx.exception.reasons))

    def test_the_unverified_comparison_really_does_report_a_false_holding(self):
        """The teeth of the rule above: the refused shape is refused because it is WRONG, and this
        proves the wrongness rather than asserting it. The trigger is git failing on BOTH sides —
        the run started outside a repo, or the checkout is not where the contract said it was."""
        tmp = tempfile.mkdtemp()
        try:
            bad = {"id": "H", "fields": {
                "check": 'test "$(git rev-parse main)" = "$(git rev-parse origin/main)"'}}
            good = {"id": "H", "fields": {"check": HEAD_MAIN_CHECK}}
            self.assertEqual(reconcile.evaluate(bad, repo=tmp)[0], reconcile.HOLDING)
            self.assertEqual(reconcile.evaluate(good, repo=tmp)[0], reconcile.BROKEN)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_pr_exists_must_carry_a_real_command(self):
        text = contract(pr_check=rc.AGENT_CLAIM)
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("PR-EXISTS" in r for r in ctx.exception.reasons))


# --------------------------------------------------------------------------- T3 t0 reconcile


class TestReconcileT0(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _contract(self, check):
        return contract(
            pr_check="false", tree_check="git diff --quiet main nope -- .",
            head_check=HEAD_MAIN_CHECK,
            extra_conditions=simple_condition("SUBJECT", check),
        )

    def test_T3_a_condition_holding_on_an_empty_run_is_struck(self):
        """T3 — before any work exists every bound condition should be in its FAILING state."""
        lines, status = reconcile.reconcile(self._contract("true"), "t0", repo=self.tmp)
        joined = "\n".join(lines)
        self.assertEqual(status, 2)
        self.assertIn("STRIKE SUBJECT", joined)
        self.assertIn("describes something other than this run's work", joined)

    def test_T3_all_broken_at_t0_starts_the_run(self):
        marker = os.path.join(self.tmp, "flag")
        lines, status = reconcile.reconcile(
            self._contract(f"test -f {marker}"), "t0", repo=self.tmp
        )
        self.assertEqual(status, 0)
        self.assertIn("0 holding", "\n".join(lines))

    def test_unbound_conditions_are_counted_not_run(self):
        text = contract(
            extra_conditions=simple_condition("LATER", "UNBOUND ${X}")
        )
        lines, _ = reconcile.reconcile(text, "close", repo=self.tmp)
        self.assertIn("1 UNBOUND", "\n".join(lines))


# --------------------------------------------------- B — the handover-authorisation header slot


class TestHandoverAuthorisation(unittest.TestCase):
    """Part B — the contract must have a slot for the handover authorisation the skill demands, and the
    run must not start without it. Its absence fails the parse; an empty value fails validation; and the
    two-phase re-validation (`bind`) refuses a contract that lost it."""

    def test_the_key_is_a_mandatory_header(self):
        self.assertIn("handover-authorisation", rc.HEADER_KEYS)

    def test_T6_a_contract_missing_the_handover_line_does_not_parse(self):
        text = contract().replace(
            "  handover-authorisation: approved 22:58 — push feat/PROJ-1-x, open the PR; nothing else\n",
            "",
        )
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("handover-authorisation" in r for r in ctx.exception.reasons))

    def test_T6_an_empty_handover_authorisation_is_refused(self):
        text = contract(handover_authorisation="")
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "t0")
        self.assertTrue(any("handover-authorisation" in r and "empty" in r
                            for r in ctx.exception.reasons))

    def test_a_recorded_authorisation_parses(self):
        rc.validate(contract(handover_authorisation="approved — push branch + open PR only"), "t0")

    def test_two_phase_rebind_still_refuses_a_lost_authorisation(self):
        """The bind pass re-validates; a contract whose authorisation was blanked between phases is
        refused at gate2, not silently carried."""
        text = contract(
            handover_authorisation="",
            extra_conditions=simple_condition("PROVING-TEST", "UNBOUND ${TEST_CMD}"),
        )
        with self.assertRaises(rc.ContractError) as ctx:
            rc.bind(text, {"TEST_CMD": "pytest -k proving"}, "gate2")
        self.assertTrue(any("handover-authorisation" in r for r in ctx.exception.reasons))


# ------------------------------------------- D — explicit shell + the could-not-run third state


class TestExplicitShellAndCouldNotRun(unittest.TestCase):
    """Part D — a condition check names its own shell (`bash`), never the host's default, and a check
    whose named shell is unavailable reports COULD-NOT-RUN — a third state, never HOLDING."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_check_runs_in_bash_not_the_host_default(self):
        """A bash-only construct (`[[ … ]]`) that cmd.exe / dash would choke on runs correctly — proof
        the named shell is invoked, not whatever the host would pick."""
        cond = {"id": "BASHONLY", "fields": {"check": "[[ -n nonempty ]]"}}
        self.assertEqual(reconcile.evaluate(cond, repo=self.tmp)[0], reconcile.HOLDING)
        cond_broken = {"id": "BASHONLY", "fields": {"check": "[[ -z nonempty ]]"}}
        self.assertEqual(reconcile.evaluate(cond_broken, repo=self.tmp)[0], reconcile.BROKEN)

    def test_sh_invokes_an_explicit_named_shell_never_shell_true(self):
        """The source guards the invocation shape: `subprocess.run([shell, "-c", …])`, and the
        `subprocess.run(command, shell=True, …)` form that lets the host pick the shell is gone."""
        src = (SCRIPTS / "run_contract.py").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"subprocess\.run\(\s*command\s*,\s*shell=True", src))
        self.assertIsNotNone(re.search(r'subprocess\.run\(\s*\n?\s*\[shell,\s*"-c",\s*command\]', src))
        self.assertIn('SHELL = "bash"', src)

    def test_T9_named_shell_unavailable_is_could_not_run_never_holding(self):
        """T9 — when the named shell is not on PATH, a check that would exit 0 (and so read HOLDING)
        must instead report COULD-NOT-RUN. A check that cannot run never reports holding."""
        cond = {"id": "ANY", "fields": {"check": "true"}}
        with mock.patch.object(rc.shutil, "which", return_value=None):
            state, output = reconcile.evaluate(cond, repo=self.tmp)
        self.assertEqual(state, reconcile.COULD_NOT_RUN)
        self.assertNotEqual(state, reconcile.HOLDING)
        self.assertIn("could-not-run", output)

    def test_could_not_run_is_counted_on_its_own_axis_not_as_holding(self):
        text = contract(
            pr_check="true", tree_check="true", head_check="true",
        )
        with mock.patch.object(rc.shutil, "which", return_value=None):
            lines, status = reconcile.reconcile(text, "close", repo=self.tmp)
        joined = "\n".join(lines)
        self.assertIn("0 holding", joined)
        # v1.21.0 — at close TREE-COMPARISON is pending-merge (not run), so two could not run.
        self.assertIn("2 could-not-run | 1 pending-merge", joined)
        self.assertIn("COULD NOT RUN", joined)
        with mock.patch.object(rc.shutil, "which", return_value=None):
            lines, _ = reconcile.reconcile(text, "post-merge", repo=self.tmp)
        self.assertIn("3 could-not-run | 0 pending-merge", "\n".join(lines))

    def test_T9_could_not_run_at_t0_strikes_the_run(self):
        """A precondition that cannot be verified is not a green light: at t0 a COULD-NOT-RUN strikes
        the run exactly as a false HOLDING does."""
        text = contract(pr_check="true", tree_check="true", head_check="true")
        with mock.patch.object(rc.shutil, "which", return_value=None):
            lines, status = reconcile.reconcile(text, "t0", repo=self.tmp)
        self.assertEqual(status, 2)
        self.assertIn("COULD-NOT-RUN at t0", "\n".join(lines))

    def test_a_close_run_without_the_shell_is_could_not_run_on_every_condition(self):
        text = contract(pr_check="true", tree_check="true", head_check="true")
        with mock.patch.object(rc.shutil, "which", return_value=None):
            lines, status = reconcile.reconcile(text, "close", repo=self.tmp)
        joined = "\n".join(lines)
        self.assertIn("2 could-not-run | 1 pending-merge", joined)
        self.assertIn("0 holding", joined)
        self.assertEqual(status, 0)


# --------------------------------------------------------------------------- T5/T6 tree + head


class TestGitFloorConditions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _squash_merged_repo(self):
        """A branch whose content was squash-merged into main — the clean case."""
        repo = new_repo(os.path.join(self.tmp, "repo"))
        git(repo, "checkout", "-q", "-b", "feat/PROJ-1-x")
        Path(repo, "a.txt").write_text("one\ntwo\n", encoding="utf-8")
        git(repo, "commit", "-qam", "work")
        git(repo, "checkout", "-q", "main")
        git(repo, "merge", "-q", "--squash", "feat/PROJ-1-x")
        git(repo, "commit", "-qm", "squash: work (#1)")
        return repo

    def test_T4_clean_squash_merge_reports_holding(self):
        """T4 — the tree comparison HOLDS under a squash merge, where ancestry would be a false-red."""
        repo = self._squash_merged_repo()
        cond = {"id": "TREE", "fields": {"check": "git diff --quiet main feat/PROJ-1-x -- ."}}
        state, _ = reconcile.evaluate(cond, repo=repo)
        self.assertEqual(state, reconcile.HOLDING)
        anc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", "feat/PROJ-1-x", "main"],
            cwd=repo, capture_output=True,
        )
        self.assertNotEqual(anc.returncode, 0, "the ancestry predicate is the false-red this avoids")

    def test_T5_correction_committed_on_the_branch_after_merge_is_BROKEN(self):
        """T5 — the incident this floor condition exists to catch."""
        repo = self._squash_merged_repo()
        git(repo, "checkout", "-q", "feat/PROJ-1-x")
        Path(repo, "a.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
        git(repo, "commit", "-qam", "correction after merge")
        cond = {"id": "TREE", "fields": {"check": "git diff --quiet main feat/PROJ-1-x -- ."}}
        state, _ = reconcile.evaluate(cond, repo=repo)
        self.assertEqual(state, reconcile.BROKEN)

    def test_T6_local_commit_never_pushed_is_BROKEN(self):
        """T6 — the twin failure: the correction never left the laptop."""
        origin = new_repo(os.path.join(self.tmp, "origin"))
        clone = os.path.join(self.tmp, "clone")
        subprocess.run(["git", "clone", "-q", origin, clone], capture_output=True)
        git(clone, "checkout", "-q", "-b", "feat/PROJ-1-x")
        git(clone, "push", "-q", "origin", "feat/PROJ-1-x")
        check = 'test "$(git rev-parse feat/PROJ-1-x)" = "$(git rev-parse origin/feat/PROJ-1-x)"'
        cond = {"id": "HEAD", "fields": {"check": check}}
        self.assertEqual(reconcile.evaluate(cond, repo=clone)[0], reconcile.HOLDING)
        Path(clone, "a.txt").write_text("stranded\n", encoding="utf-8")
        git(clone, "commit", "-qam", "never pushed")
        self.assertEqual(reconcile.evaluate(cond, repo=clone)[0], reconcile.BROKEN)

    def test_G3_no_origin_remote_reports_honestly_and_does_not_crash(self):
        """G3 — a repo with no `origin`: the floor conditions report BROKEN, nothing explodes."""
        repo = new_repo(os.path.join(self.tmp, "lonely"))
        text = contract(
            pr_check="false",
            tree_check="git diff --quiet main origin/main -- .",
            head_check=HEAD_MAIN_CHECK,
        )
        lines, status = reconcile.reconcile(text, "close", repo=repo)
        joined = "\n".join(lines)
        self.assertEqual(status, 0)
        self.assertIn("2 BROKEN", joined)
        self.assertIn("1 pending-merge", joined)
        self.assertIn("READ THIS FIRST", joined)
        lines, status = reconcile.reconcile(text, "post-merge", repo=repo)
        self.assertIn("3 BROKEN", "\n".join(lines))


# ------------------------------------------- v1.21.0 — the generated floor and the post-merge phase


class TestGeneratedFloor(unittest.TestCase):
    """v1.21.0 — TREE-COMPARISON and LOCAL-HEAD-PUSHED are rendered by `run_contract.py write` from the
    header; any other spelling is refused. Twelve golden-e2e contracts carried two meanings under the
    one TREE-COMPARISON id: 4 compared the base to the branch (BROKEN at every pre-merge close), 8
    compared the remote branch to the local one (a false HOLDING on a correction pushed after merge)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def spec(self, **floor):
        conds = [{"id": "PR-EXISTS", "statement": "the PR exists and its state is readable",
                  "origin": "floor", "derived-by": rc.AGENT_CLAIM, "value": "x", "check": "gh pr view 1"},
                 {"id": "TREE-COMPARISON", **floor.get("tree", {})},
                 {"id": "LOCAL-HEAD-PUSHED", **floor.get("head", {})}]
        return {"key": "PROJ-1", "started": "t", "plugin-version": "1.21.0", "plugin-path": "/p",
                "repo": self.tmp, "base": floor.get("base", "main"), "branch": "feat/PROJ-1-x",
                "remote": "origin", "merge-strategy": "squash", "reviewer": "on", "challenger": "on",
                "handover-authorisation": "push feat/PROJ-1-x, open the PR; nothing else",
                "call-ceiling": "unknown", "per-call-estimate": "unknown", "ceiling-source": "none",
                "token-budget": "unmeasured", "conditions": conds}

    def test_write_renders_both_checks_and_derives_base(self):
        new_repo(self.tmp)
        sha = git(self.tmp, "rev-parse", "main").stdout.strip()
        text = rc.write(self.spec(), repo=self.tmp)
        self.assertIn(f"base: main@{sha}", text)
        self.assertIn("check: " + rc.tree_check("main", "feat/PROJ-1-x", "origin"), text)
        self.assertIn("check: " + rc.head_check("feat/PROJ-1-x", "origin"), text)
        self.assertIn("statement: " + rc.FLOOR["TREE-COMPARISON"], text)
        rc.validate(text, "t0")
        bound = rc.bind(text, {"CHANGED_PATHS": "a.txt src/b.py"}, "gate2")
        self.assertIn("-- a.txt src/b.py", bound)

    def test_write_refuses_an_authored_tree_check(self):
        """The observed false-green form, remote branch against local branch, is refused at write."""
        new_repo(self.tmp)
        authored = "git diff --quiet origin/feat/PROJ-1-x feat/PROJ-1-x -- UNBOUND ${CHANGED_PATHS}"
        with self.assertRaises(rc.ContractError) as ctx:
            rc.write(self.spec(tree={"check": authored}), repo=self.tmp)
        self.assertTrue(any("GENERATED" in r for r in ctx.exception.reasons))

    def test_write_refuses_an_authored_head_check(self):
        new_repo(self.tmp)
        with self.assertRaises(rc.ContractError) as ctx:
            rc.write(self.spec(head={"check": HEAD_MAIN_CHECK}), repo=self.tmp)
        self.assertTrue(any("GENERATED" in r for r in ctx.exception.reasons))

    def test_write_refuses_a_base_sha_the_repo_contradicts(self):
        new_repo(self.tmp)
        with self.assertRaises(rc.ContractError) as ctx:
            rc.write(self.spec(base="main@0000000"), repo=self.tmp)
        self.assertTrue(any("the repo says" in r for r in ctx.exception.reasons))

    def test_write_refuses_a_base_that_does_not_resolve(self):
        new_repo(self.tmp)
        with self.assertRaises(rc.ContractError):
            rc.write(self.spec(base="trunk"), repo=self.tmp)

    def test_validate_refuses_each_observed_free_form_base(self):
        for base in ("main", "f9272be", "main @ f9272be", "main@not-a-sha"):
            with self.assertRaises(rc.ContractError, msg=base) as ctx:
                rc.validate(contract(base=base), "t0")
            self.assertTrue(any("<branch>@<sha>" in r for r in ctx.exception.reasons), base)

    def test_validate_refuses_both_observed_authored_tree_forms(self):
        for chk in ("git diff --quiet main feat/PROJ-1-x -- a.txt",
                    "git diff --quiet origin/feat/PROJ-1-x feat/PROJ-1-x -- a.txt",
                    "git diff --quiet origin/main origin/feat/PROJ-1-x -- src tests; true"):
            with self.assertRaises(rc.ContractError, msg=chk) as ctx:
                rc.validate(contract(tree_check=chk), "t0")
            self.assertTrue(any("TREE-COMPARISON" in r and "GENERATED" in r
                                for r in ctx.exception.reasons), chk)

    def test_validate_refuses_a_head_check_in_another_spelling(self):
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(contract(head_check=DEFAULTS_HEAD_OLD), "t0")
        self.assertTrue(any("LOCAL-HEAD-PUSHED" in r and "GENERATED" in r
                            for r in ctx.exception.reasons))

    def test_validate_refuses_a_branch_that_is_not_a_plain_ref(self):
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(contract(branch="feat/x;rm"), "t0")
        self.assertTrue(any("plain ref name" in r for r in ctx.exception.reasons))

    def test_the_unbound_path_list_is_refused_past_gate2(self):
        text = contract(tree_check=rc.tree_check("main", "feat/PROJ-1-x", "origin"))
        rc.validate(text, "t0")
        with self.assertRaises(rc.ContractError):
            rc.validate(text, "gate2")


DEFAULTS_HEAD_OLD = (
    "git rev-parse --verify feat/PROJ-1-x >/dev/null 2>&1 && "
    "git rev-parse --verify origin/feat/PROJ-1-x >/dev/null 2>&1 && "
    'test "$(git rev-parse feat/PROJ-1-x)" = "$(git rev-parse origin/feat/PROJ-1-x)"'
)


class TestPendingMergeAndPostMerge(unittest.TestCase):
    """v1.21.0 — TREE-COMPARISON has meaning only once merged. At close it is counted `pending-merge`
    (never holding, never run); `--phase post-merge` runs it."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _pushed_branch(self):
        """origin (bare) + a clone whose feature branch is pushed, not yet merged."""
        bare = os.path.join(self.tmp, "origin.git")
        seed = new_repo(os.path.join(self.tmp, "seed"))
        subprocess.run(["git", "clone", "-q", "--bare", seed, bare], capture_output=True)
        work = os.path.join(self.tmp, "work")
        subprocess.run(["git", "clone", "-q", bare, work], capture_output=True)
        git(work, "checkout", "-q", "-b", "feat/PROJ-1-x")
        Path(work, "a.txt").write_text("one\ntwo\n", encoding="utf-8")
        git(work, "commit", "-qam", "work")
        git(work, "push", "-q", "origin", "feat/PROJ-1-x")
        return bare, work

    def _squash_merge_on_origin(self, bare):
        """The human's squash merge, done in a separate clone and pushed to main."""
        other = os.path.join(self.tmp, "merger")
        subprocess.run(["git", "clone", "-q", bare, other], capture_output=True)
        git(other, "merge", "-q", "--squash", "origin/feat/PROJ-1-x")
        git(other, "commit", "-qm", "squash: work (#1)")
        git(other, "push", "-q", "origin", "main")

    def _text(self):
        return contract(pr_check="true")

    def test_close_counts_tree_comparison_pending_never_holding(self):
        bare, work = self._pushed_branch()
        lines, status = reconcile.reconcile(self._text(), "close", repo=work)
        joined = "\n".join(lines)
        self.assertEqual(status, 0)
        self.assertIn("2 holding | 0 BROKEN | 0 UNBOUND | 0 could-not-run | 1 pending-merge", joined)
        self.assertIn("TREE-COMPARISON: PENDING-MERGE", joined)
        self.assertIn("--phase post-merge", joined)
        self.assertNotIn("READ THIS FIRST", joined)

    def test_the_correct_form_run_before_the_merge_is_broken_by_construction(self):
        """Why it is not run at close: before the merge the base cannot carry the PR."""
        bare, work = self._pushed_branch()
        lines, _ = reconcile.reconcile(self._text(), "post-merge", repo=work)
        self.assertIn("TREE-COMPARISON: BROKEN", "\n".join(lines))

    def test_post_merge_after_a_clean_squash_holds(self):
        bare, work = self._pushed_branch()
        self._squash_merge_on_origin(bare)
        git(work, "fetch", "-q", "origin")
        lines, status = reconcile.reconcile(self._text(), "post-merge", repo=work)
        joined = "\n".join(lines)
        self.assertIn("3 holding | 0 BROKEN | 0 UNBOUND | 0 could-not-run | 0 pending-merge", joined)
        self.assertIn("DONE: every condition holds after the merge", joined)

    def test_post_merge_done_prints_the_removal_command_and_deletes_nothing(self):
        """1.21.1 — the contract's end of life: the script says it may go, the human removes it."""
        bare, work = self._pushed_branch()
        self._squash_merge_on_origin(bare)
        git(work, "fetch", "-q", "origin")
        path = os.path.join(self.tmp, "run-contract-PROJ-1.txt")
        Path(path).write_text(self._text(), encoding="utf-8")
        out = subprocess.run([sys.executable, str(SCRIPTS / "reconcile.py"), "run", path,
                              "--phase", "post-merge", "--repo", work], capture_output=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertIn(f"    rm {path}", out.stdout)
        self.assertTrue(os.path.exists(path), "reconcile must never delete the contract itself")

    def test_no_done_line_unless_every_condition_holds(self):
        bare, work = self._pushed_branch()
        lines, _ = reconcile.reconcile(self._text(), "post-merge", repo=work)   # not merged: BROKEN
        self.assertNotIn("DONE:", "\n".join(lines))
        lines, _ = reconcile.reconcile(self._text(), "close", repo=work)
        self.assertNotIn("DONE:", "\n".join(lines))

    def test_post_merge_a_correction_pushed_after_the_merge_is_BROKEN(self):
        """The incident TREE-COMPARISON exists for — and the refused remote-vs-local form HOLDS on it."""
        bare, work = self._pushed_branch()
        self._squash_merge_on_origin(bare)
        Path(work, "a.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
        git(work, "commit", "-qam", "correction after merge")
        git(work, "push", "-q", "origin", "feat/PROJ-1-x")
        git(work, "fetch", "-q", "origin")
        lines, _ = reconcile.reconcile(self._text(), "post-merge", repo=work)
        joined = "\n".join(lines)
        self.assertIn("TREE-COMPARISON: BROKEN", joined)
        self.assertIn("READ THIS FIRST", joined)
        false_green = {"id": "T", "fields": {
            "check": "git diff --quiet refs/remotes/origin/feat/PROJ-1-x refs/heads/feat/PROJ-1-x -- a.txt"}}
        self.assertEqual(reconcile.evaluate(false_green, repo=work)[0], reconcile.HOLDING)

    def test_an_unbound_tree_comparison_at_close_is_unbound_not_pending(self):
        text = contract(tree_check=rc.tree_check("main", "feat/PROJ-1-x", "origin"), pr_check="false")
        lines, _ = reconcile.reconcile(text, "close", repo=self.tmp)
        self.assertIn("1 UNBOUND | 0 could-not-run | 0 pending-merge", "\n".join(lines))

    def test_t0_is_unchanged_the_generated_floor_starts_the_run(self):
        repo = new_repo(os.path.join(self.tmp, "r"))
        text = contract(tree_check=rc.tree_check("main", "feat/PROJ-1-x", "origin"), pr_check="false")
        lines, status = reconcile.reconcile(text, "t0", repo=repo)
        self.assertEqual(status, 0, "\n".join(lines))
        self.assertIn("0 holding", "\n".join(lines))

    def test_an_unknown_phase_is_refused(self):
        with self.assertRaises(ValueError):
            reconcile.reconcile(self._text(), "after", repo=self.tmp)
        path = os.path.join(self.tmp, "c.txt")
        Path(path).write_text(self._text(), encoding="utf-8")
        out = subprocess.run([sys.executable, str(SCRIPTS / "reconcile.py"), "run", path,
                              "--phase", "after"], capture_output=True, encoding="utf-8")
        self.assertEqual(out.returncode, 1)
        self.assertIn("unknown phase", out.stdout)

    def test_the_disclosure_names_the_post_merge_command(self):
        seed = rc.disclosure_seed(*rc.parse(self._text()), contract_path=".mango/c.txt")
        self.assertIn("POST-MERGE: TREE-COMPARISON is NOT verified by this run", seed)
        self.assertIn("reconcile.py run .mango/c.txt --phase post-merge", seed)
        self.assertIn("git fetch origin", seed)


# --------------------------------------------------------------------------- T7 merge strategy


class TestMergeStrategy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_T7_repo_that_switched_strategy_mid_history(self):
        """T7 — old history full of merge commits, recent tip window squashed.

        The first-parent tip window reports squash. A whole-history merge count returns the
        pre-change answer — in the dangerous direction — so it is asserted here as the wrong tool.
        """
        repo = new_repo(os.path.join(self.tmp, "switched"))
        for i in range(3):
            git(repo, "checkout", "-q", "-b", f"old{i}")
            Path(repo, f"o{i}.txt").write_text("x\n", encoding="utf-8")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", f"old {i}")
            git(repo, "checkout", "-q", "main")
            git(repo, "merge", "-q", "--no-ff", "-m", f"Merge old{i}", f"old{i}")
        for i in range(4):
            Path(repo, f"s{i}.txt").write_text("y\n", encoding="utf-8")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", f"squash: change {i} (#{i})")
        verdict, window = reconcile.merge_strategy(repo, "main")
        self.assertIn("squash-or-rebase", verdict)
        self.assertEqual(window, 4)
        whole = subprocess.run(
            ["git", "rev-list", "--count", "--merges", "main"], cwd=repo,
            capture_output=True, text=True,
        )
        self.assertEqual(int(whole.stdout.strip()), 3,
                         "a whole-history count still sees the old merges — the wrong answer")

    def test_merge_commit_tip_reports_merge_commits(self):
        repo = new_repo(os.path.join(self.tmp, "merging"))
        git(repo, "checkout", "-q", "-b", "side")
        Path(repo, "b.txt").write_text("b\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "side")
        git(repo, "checkout", "-q", "main")
        git(repo, "merge", "-q", "--no-ff", "-m", "Merge side", "side")
        verdict, window = reconcile.merge_strategy(repo, "main")
        self.assertIn("merge-commits", verdict)
        self.assertEqual(window, 0)

    def test_no_merge_commit_at_all_says_so(self):
        repo = new_repo(os.path.join(self.tmp, "linear"))
        verdict, _ = reconcile.merge_strategy(repo, "main")
        self.assertIn("no merge commit anywhere", verdict)

    def test_the_verdict_states_that_it_narrows_rather_than_settles(self):
        repo = new_repo(os.path.join(self.tmp, "narrow"))
        git(repo, "checkout", "-q", "-b", "s")
        Path(repo, "c.txt").write_text("c\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "s")
        git(repo, "checkout", "-q", "main")
        git(repo, "merge", "-q", "--no-ff", "-m", "Merge s", "s")
        Path(repo, "d.txt").write_text("d\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "after")
        verdict, _ = reconcile.merge_strategy(repo, "main")
        self.assertIn("narrows the judgement", verdict)


# ------------------------------------------------- B — the forced-case control is RETIRED and gone


class TestForcedCaseRetirement(unittest.TestCase):
    """v1.14.0 (B). Across three field runs EVERY condition reported FORCE-UNPROVEN: the floor's
    force cases are literal true/false that cannot mutate real state, and genuinely forcing them would
    need destructive acts an unattended run may never perform. It was measured inert, so it is gone —
    and these tests are the removal's teeth."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        new_repo(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_prove_machinery_is_gone_from_the_module(self):
        self.assertFalse(hasattr(reconcile, "prove_one"))

    def test_reconcile_takes_no_prove_argument(self):
        with self.assertRaises(TypeError):
            reconcile.reconcile(contract(), "close", repo=self.tmp, prove=True)

    def test_the_proven_counted_line_went_with_the_control_that_fed_it(self):
        lines, _ = reconcile.reconcile(
            contract(pr_check="false", tree_check="false", head_check="false"), "close", repo=self.tmp)
        joined = "\n".join(lines)
        self.assertNotIn("shown BROKEN when forced", joined)
        self.assertIn("conditions:", joined)

    def test_T7_the_flag_is_refused_at_the_cli_never_silently_ignored(self):
        path = os.path.join(self.tmp, "c.txt")
        Path(path).write_text(contract(), encoding="utf-8")
        out = subprocess.run(
            [sys.executable, str(SCRIPTS / "reconcile.py"), "run", path, "--phase", "close",
             "--repo", self.tmp, "--prove"], capture_output=True, encoding="utf-8")
        self.assertEqual(out.returncode, 1)
        self.assertIn("RETIRED", out.stdout)

    def test_T8_the_t0_run_is_unchanged_and_still_strikes_a_holding_condition(self):
        """T8 — the part that earned its claim is KEPT: every bound condition observed in its failing
        state before any work exists, and one that holds on an empty run is struck."""
        text = contract(pr_check="false", tree_check="false", head_check="false",
                        extra_conditions=simple_condition("SUBJECT", "true"))
        lines, status = reconcile.reconcile(text, "t0", repo=self.tmp)
        self.assertEqual(status, 2)
        self.assertIn("STRIKE SUBJECT", "\n".join(lines))

    def test_T8_all_broken_at_t0_still_starts_the_run(self):
        text = contract(pr_check="false", tree_check="false", head_check="false",
                        extra_conditions=simple_condition("SUBJECT", "false"))
        lines, status = reconcile.reconcile(text, "t0", repo=self.tmp)
        self.assertEqual(status, 0)
        self.assertIn("4 BROKEN", "\n".join(lines))

    def test_NOTHING_IN_THE_REMAINING_PATH_MUTATES_GIT_STATE(self):
        """One earlier forced case left `refs/remotes/origin/<branch>` repointed at main, exiting 0
        silently. With the control gone the only commands run are each condition's read-only check —
        asserted by observing the repo before and after a full close run."""
        git(self.tmp, "branch", "feat/x")
        git(self.tmp, "update-ref", "refs/remotes/origin/feat/x", "refs/heads/feat/x")

        def snapshot():
            refs = git(self.tmp, "show-ref").stdout
            head = git(self.tmp, "rev-parse", "HEAD").stdout
            log = git(self.tmp, "log", "--all", "--oneline").stdout
            status = git(self.tmp, "status", "--porcelain", "-uall").stdout
            return refs, head, log, status

        before = snapshot()
        text = contract(
            base="main", branch="feat/x",
            pr_check="false",
            tree_check="git diff --quiet main feat/x -- .",
            head_check=('git rev-parse --verify feat/x >/dev/null 2>&1 && '
                        'git rev-parse --verify origin/feat/x >/dev/null 2>&1 && '
                        'test "$(git rev-parse feat/x)" = "$(git rev-parse origin/feat/x)"'),
            extra_conditions=simple_condition("SUBJECT", "git status --porcelain"))
        reconcile.reconcile(text, "close", repo=self.tmp)
        self.assertEqual(before, snapshot())


# --------------------------------------------------------------------------- D — budget


class TestBudget(unittest.TestCase):
    def test_per_call_estimate_and_ceiling_come_from_the_supplied_rows(self):
        rows = budget.parse_rows("689200/164,638300/167,217700/114,426600/122")
        ceil_v, per_call, source = budget.ceiling(rows, 500000)
        self.assertEqual(len(rows), 4)
        self.assertTrue(1500 <= per_call <= 4200, f"per-call estimate {per_call} off the ledger range")
        self.assertEqual(ceil_v, 500000 // per_call)
        self.assertIn("ledger row", source)

    def test_T14_no_ledger_history_is_unknown_and_does_not_block(self):
        """T14 / G2 — a fresh project: record `unknown`, do not block, do not invent a number."""
        ceil_v, per_call, source = budget.ceiling(budget.parse_rows(""), 500000)
        self.assertEqual(ceil_v, "unknown")
        self.assertEqual(per_call, "unknown")
        self.assertIn("nothing invented", source)
        status, message, step = budget.check("unknown", 40)
        self.assertEqual(status, "UNKNOWN")
        self.assertIn("does not block", message.replace("nothing is blocked", "does not block"))
        self.assertIsNone(step)

    def test_no_token_budget_also_yields_unknown(self):
        ceil_v, per_call, _ = budget.ceiling(budget.parse_rows("100000/50"), None)
        self.assertEqual(ceil_v, "unknown")
        self.assertEqual(per_call, 2000)

    def test_T12_estimate_exceeding_the_ceiling_is_reported_at_t0(self):
        status, message, step = budget.check(100, 0, projected=180, at="t0")
        self.assertEqual(status, "EXCEEDED")
        self.assertIn("AT T0", message)
        self.assertEqual(step[0], "1-narrow-main-loop")

    def test_T13_approaching_the_ceiling_degrades_rather_than_dying(self):
        status, message, step = budget.check(100, 85, at="mid-run")
        self.assertEqual(status, "APPROACHING")
        self.assertIn("Never a mid-phase death", message)
        self.assertEqual(step[0], "1-narrow-main-loop")

    def test_well_inside_the_ceiling_is_OK(self):
        status, _, step = budget.check(200, 20)
        self.assertEqual(status, "OK")
        self.assertIsNone(step)

    def test_the_ladder_starts_at_the_main_loop_not_at_a_subagent(self):
        self.assertEqual(budget.LADDER[0][0], "1-narrow-main-loop")
        self.assertIn("90%", budget.LADDER[0][1])

    def test_the_review_seat_is_degraded_in_steps_and_never_to_zero(self):
        names = [name for name, _ in budget.LADDER]
        self.assertIn("3a-reviewer-max-to-reviewer", names)
        self.assertIn("3b-reviewer-to-native-code-review", names)
        self.assertFalse(any("no-review" in n or "skip-review" in n for n in names))

    def test_the_native_step_is_not_sold_as_a_smaller_reviewer(self):
        text = dict(budget.LADDER)["3b-reviewer-to-native-code-review"]
        self.assertIn("does not read `.harness.json`", text)
        self.assertIn("DISCLOSURE", text)

    def test_the_review_seat_and_the_envelope_are_named_as_never_degraded(self):
        joined = " ".join(budget.NEVER)
        self.assertIn("review seat", joined)
        self.assertIn("envelope", joined)


# --------------------------------------------------------------------------- DISCLOSURE seed


class TestDisclosureSeed(unittest.TestCase):
    def test_T10_a_disabled_challenger_is_line_one(self):
        header, conditions = rc.parse(contract(challenger="off"))
        seed = rc.disclosure_seed(header, conditions)
        challenger_line = seed.splitlines()[2]
        self.assertIn("CHALLENGER: OFF", challenger_line)
        self.assertIn("not evidence of independence", challenger_line + seed)

    def test_T11_the_default_records_both_seats_as_enabled_never_as_having_run(self):
        """1.23.1 — the seed is written before any phase runs. An e2e run that stopped at Gate 1 carried
        `the reviewer ran` in its DISCLOSURE although no review happened: the seed may state the
        configuration only, never an outcome."""
        seed = rc.disclosure_seed(*rc.parse(contract())).splitlines()
        self.assertIn("REVIEWER: ON", seed[1])
        self.assertIn("CHALLENGER: ON", seed[2])
        for line in seed[1:3]:
            self.assertIn("enabled for this run", line)
            self.assertNotRegex(line, r"(reviewer|challenger) ran\.")

    def test_T15_no_reviewer_alone_leaves_the_challenger_recorded_as_ON(self):
        """v1.14.0 F / T15 — the two seats are separate decisions. A morning reader must be able to
        tell 'clean, nobody looked' from 'clean, the blind reviewer looked'."""
        seed = rc.disclosure_seed(*rc.parse(contract(reviewer="off"))).splitlines()
        self.assertIn("REVIEWER: OFF", seed[1])
        self.assertIn("--no-reviewer", seed[1])
        self.assertIn("CHALLENGER: ON", seed[2])
        self.assertNotIn("BOTH SEATS OFF", "\n".join(seed))

    def test_T15_no_challenger_alone_leaves_the_reviewer_recorded_as_ON(self):
        seed = rc.disclosure_seed(*rc.parse(contract(challenger="off"))).splitlines()
        self.assertIn("REVIEWER: ON", seed[1])
        self.assertIn("CHALLENGER: OFF", seed[2])

    def test_both_seats_waived_is_recorded_not_refused(self):
        text = contract(reviewer="off", challenger="off")
        rc.validate(text, "t0")                       # no policy refuses to run
        self.assertIn("BOTH SEATS OFF", rc.disclosure_seed(*rc.parse(text)))

    def test_unchecked_agent_claims_are_carried_into_the_disclosure(self):
        text = contract(extra_conditions=simple_condition("CLAIMED", "true"))
        header, conditions = rc.parse(text)
        seed = rc.disclosure_seed(header, conditions)
        self.assertIn("UNCHECKED AGENT CLAIMS: 1", seed)
        self.assertIn("CLAIMED", seed)

    def test_the_disclosure_says_it_is_the_one_artifact_nothing_can_check(self):
        header, conditions = rc.parse(contract())
        seed = rc.disclosure_seed(header, conditions)
        self.assertIn("ONE artifact nothing can check", seed)
        self.assertIn("near-empty list", seed)

    def test_an_unknown_ceiling_is_disclosed_as_unknown(self):
        header, conditions = rc.parse(contract(call_ceiling="unknown"))
        self.assertIn("ceiling unknown", rc.disclosure_seed(header, conditions))


# --------------------------------------------------------------------------- write / derive


class TestWriteDerivesValues(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_every_derivable_value_is_derived_by_running_its_command(self):
        new_repo(self.tmp)
        spec = {
            "key": "PROJ-1", "started": "t", "plugin-version": "1.11.0", "plugin-path": "/p",
            "repo": self.tmp, "base": "main", "branch": "feat/PROJ-1-x", "remote": "origin",
            "merge-strategy": "squash", "reviewer": "on", "challenger": "on",
            "handover-authorisation": "approved 22:58 — push feat/PROJ-1-x, open the PR; nothing else",
            "call-ceiling": "140",
            "per-call-estimate": "3100", "ceiling-source": "ledger", "token-budget": "unmeasured",
            "conditions": [
                {"id": "PR-EXISTS", "statement": "the PR exists and its state is readable",
                 "origin": "floor", "derived-by": "echo OPEN", "value": "",
                 "check": "gh pr view 1"},
                {"id": "TREE-COMPARISON",
                 "statement": "no commit landed on the branch beyond what the PR carries",
                 "origin": "floor", "derived-by": "echo deadbee", "value": ""},
                {"id": "LOCAL-HEAD-PUSHED",
                 "statement": "nothing is stranded on this machine: local head == the remote's",
                 "origin": "floor", "derived-by": rc.AGENT_CLAIM, "value": "the agent says so"},
            ],
        }
        text = rc.write(spec, repo=self.tmp)
        self.assertIn("value: OPEN (exit 0)", text)
        self.assertIn("value: deadbee (exit 0)", text)
        self.assertIn("value: the agent says so", text)   # unchecked claim, left as claimed
        rc.validate(text, "t0")

    def test_write_refuses_a_spec_that_omits_a_floor_condition(self):
        with self.assertRaises(rc.ContractError):
            rc.write({"conditions": [{"id": "PR-EXISTS"}]}, repo=self.tmp)




# ===========================================================================================
# CHECK-LINES — the counted-line checker (v1.13.0)
# ===========================================================================================
#
# The teeth tests are numbered T1-T9 and G1-G3 to match the build spec, so a later reader can map an
# assertion to the field case it came from. Every fixture below is a synthetic working doc built in
# memory: no real project, no dispatch, no network.

import check_lines as cl  # noqa: E402

CLEAN_LINES = {
    "PREMISE": "PREMISE: 0 reference(s) checked | 0 missing | 0 ambiguous (surfaced, not blocking)",
    "RECALL": "RECALL: 0 claim(s) surfaced | 0 by symbol | 0 by handle | 0 by area | 0 by finding | "
              "0 retired skipped — advisory (blocks nothing)",
    "REFINE": "REFINE: 0 unresolved surfaced | 0 want-decision asked | 0 how-decision resolved+cited | "
              "0 ASSUMED | skip: yes",
    "SECTIONS": "SECTIONS: 2 found (Goal · Acceptance criteria) | 2 decomposed | "
                "ROWS: C=0 R=1 G=1 AC=1",
    "CLARIFICATION": "CLARIFICATION: 0 raised | 0 self-resolved (cited) | 0 for human decision",
    "RULE SECTIONS": "RULE SECTIONS: 0 applicable — 0 by change-type | 0 by recalled handle — none",
    "HANDLES": "HANDLES: 0 recalled | 0 traced | 0 does not apply | 0 unanswered",
    "CHALLENGER VERDICT": "CHALLENGER VERDICT: 4 requirement(s) rebuilt | 4 met | 0 not met | 0 can't tell | "
                 "0 not-met covered by a recorded exclusion",
    "EXCLUSIONS": "EXCLUSIONS: 0 recorded | 0 with a checkable expiry | 0 recurring | "
                  "0 with an overdue predecessor | 0 input-shape-dependent AC(s) | "
                  "0 proven on a real corpus",
    "CLAIMS": "CLAIMS: 0 claim(s) from 0 lesson entr(ies) | T1=0 T2=0 T3=0 T4=0 T5=0 T6=0 | "
              "0 unclassified",
    "RECURRENCE": "RECURRENCE: 0 recurring | 0 superseded (0 retired) | 0 promotion candidate(s)",
    "FALSIFY": "FALSIFY: 0 candidate(s) checked | 0 still-true (proceed) | 0 falsified (BLOCKED) | "
               "0 not cheaply checkable (BLOCKED)",
    "RECURRING-T2": "RECURRING-T2: 0 type-2 claim(s) with seen >= 2 | 0 routed to a destination | "
                    "0 cannot promote | 0 left in lessons_path",
    "PROMOTION": "PROMOTION: 0 proposed | 0 human-ratified | destinations: none | "
                 "mango files written: 0",
    "LEDGER TOTAL": "LEDGER TOTAL: 0 · top cost driver: none (no dispatch)",
}


def workdoc(phase="finalise", tier="full", track="backend", drop=(), replace=None, extra=""):
    """A synthetic working doc carrying the counted lines, each in the canonical form by default."""
    lines = dict(CLEAN_LINES)
    for token in drop:
        lines.pop(token, None)
    for token, text in (replace or {}).items():
        lines[token] = text
    body = "\n".join(f"`{text}`" for text in lines.values())
    return (
        f"# PROJ-1 — a ticket (working doc)\n\n"
        f"- **SCOPE:** S\n- **TRACK:** {track}\n- **TIER:** {tier}\n- **BASELINE:** green\n\n"
        f"{body}\n\n{extra}\n\n## Session status\n\n- **Current phase:** {phase}\n"
    )


def run(text, **kw):
    lines, status = cl.check_doc(text, **kw)
    return "\n".join(lines), status


class TestCheckLinesTeeth(unittest.TestCase):
    # v1.23.2 — the RULE SECTIONS shape shows `, ` between entries; ` / ` (the 1.23.0 e2e's red run,
    # copying the old `✅ / N/A` shape) is not a separator and still fails the count.
    RS = ("RULE SECTIONS: 3 applicable — 3 by change-type | 0 by recalled handle — "
          "§R1 (change-type) ✅ docstring names the option{sep}§R2 (change-type) ✅ new tests fail "
          "without it{sep}§R3 (change-type) N/A because no CLI option changes")

    def test_RULE_SECTIONS_entries_split_by_comma_pass(self):
        out, status = run(f"`{self.RS.format(sep=', ')}`\n")
        self.assertIn("RULE SECTIONS: PASS", out)

    def test_RULE_SECTIONS_entries_split_by_slash_fail_the_count(self):
        out, status = run(f"`{self.RS.format(sep=' / ')}`\n")
        self.assertIn("RULE SECTIONS: FAIL", out)
        self.assertIn("does not match `<n> applicable`", out)

    # v1.20.0 — the challenger's verdict as a counted line.
    def test_CHALLENGE_a_clean_challenger_line_passes(self):
        out, status = run(workdoc(phase="review"))
        self.assertEqual(status, 0, out)
        self.assertIn("CHALLENGER VERDICT: PASS", out)

    def test_CHALLENGE_counts_that_do_not_sum_fail(self):
        out, status = run(workdoc(phase="review", replace={"CHALLENGER VERDICT":
            "CHALLENGER VERDICT: 5 requirement(s) rebuilt | 4 met | 0 not met | 0 can't tell | "
            "0 not-met covered by a recorded exclusion"}))
        self.assertEqual(status, 2, out)
        self.assertIn("n != m + x + u", out)

    def test_CHALLENGE_an_unmet_requirement_blocks_clean(self):
        out, status = run(workdoc(phase="review", replace={"CHALLENGER VERDICT":
            "CHALLENGER VERDICT: 4 requirement(s) rebuilt | 3 met | 1 not met | 0 can't tell | "
            "0 not-met covered by a recorded exclusion"}))
        self.assertEqual(status, 2, out)
        self.assertIn("BLOCKS clean", out)

    def test_CHALLENGE_cant_tell_blocks_clean(self):
        out, status = run(workdoc(phase="review", replace={"CHALLENGER VERDICT":
            "CHALLENGER VERDICT: 4 requirement(s) rebuilt | 3 met | 0 not met | 1 can't tell | "
            "0 not-met covered by a recorded exclusion"}))
        self.assertEqual(status, 2, out)

    def test_CHALLENGE_a_not_met_inside_a_recorded_exclusion_does_not_block(self):
        out, status = run(workdoc(phase="review", replace={"CHALLENGER VERDICT":
            "CHALLENGER VERDICT: 4 requirement(s) rebuilt | 3 met | 1 not met | 0 can't tell | "
            "1 not-met covered by a recorded exclusion"}))
        self.assertNotIn("BLOCKS clean", out)

    def test_CHALLENGE_zero_requirements_is_not_a_pass(self):
        out, status = run(workdoc(phase="review", replace={"CHALLENGER VERDICT":
            "CHALLENGER VERDICT: 0 requirement(s) rebuilt | 0 met | 0 not met | 0 can't tell | "
            "0 not-met covered by a recorded exclusion"}))
        self.assertEqual(status, 2, out)

    def test_CHALLENGE_missing_at_review_is_MISSING(self):
        out, status = run(workdoc(phase="review", drop=("CHALLENGER VERDICT",)))
        self.assertEqual(status, 2, out)
        self.assertIn("CHALLENGER VERDICT", out.split("MISSING")[-1])

    def test_CHALLENGE_is_not_required_when_the_seat_was_waived_by_its_flag(self):
        out, status = run(workdoc(phase="review", drop=("CHALLENGER VERDICT",),
                                  extra="- CHALLENGER: OFF (--no-challenger)"))
        self.assertEqual(status, 0, out)

    def test_CHALLENGE_is_not_required_before_review_or_in_the_lite_lane(self):
        self.assertEqual(run(workdoc(phase="execute", drop=("CHALLENGER VERDICT",)))[1], 0)
        self.assertNotIn("CHALLENGER VERDICT", cl.required_tokens("finalise", "lite", "backend", False))

    def test_CL_T1_a_claims_line_whose_type_counts_do_not_sum_to_c_fails(self):
        """The decisive cheap check: the line disagrees with itself. No grammar debate needed."""
        out, status = run(workdoc(replace={
            "CLAIMS": "CLAIMS: 3 claim(s) from 1 lesson entr(ies) | T1=0 T2=2 T3=1 T4=0 T5=1 T6=0 | "
                      "0 unclassified"}))
        self.assertEqual(status, 2)
        self.assertIn("CLAIMS: FAIL", out)
        self.assertIn("contradiction: c != T1..T6 + u", out)
        # It is a CONTRADICTION, not an off-grammar finding: every field matched the canonical form.
        self.assertNotIn("field omitted", out)
        self.assertNotIn("field invented", out)

    def test_CL_T2_a_handles_line_where_h_does_not_equal_t_plus_x_plus_u_fails(self):
        out, status = run(workdoc(replace={
            "HANDLES": "HANDLES: 4 recalled | 2 traced | 1 does not apply | 0 unanswered"}))
        self.assertEqual(status, 2)
        self.assertIn("HANDLES: FAIL", out)
        self.assertIn("h != t + x + u", out)

    def test_CL_T3_an_exclusion_in_the_matrix_with_no_EXCLUSIONS_line_fails(self):
        """Case 4: the exclusion was recorded as prose and the counted line was never written."""
        out, status = run(workdoc(drop=("EXCLUSIONS",), extra=(
            "**Coverage-gap exclusions**\n\n"
            "| Item | Risk tier | Why deferred | Follow-up | Expiry | Seen |\n"
            "|---|---|---|---|---|---|\n"
            "| AC1(b) sensible-on-the-anchor-repo | medium | no runner | PROJ-9 | PROJ-9 | none |\n")))
        self.assertEqual(status, 2)
        self.assertIn("MISSING EXCLUSIONS", out)
        self.assertIn("emitted by design", out)

    def test_CL_T4_a_recall_line_with_an_invented_field_and_by_handle_omitted_fails(self):
        """Case 3: a field invented, `<h> by handle` omitted, the whole thing committed."""
        out, status = run(workdoc(replace={
            "RECALL": "RECALL: 8 claim(s) surfaced | 0 by symbol | 3 by area | 5 does-not-apply | "
                      "0 retired skipped — advisory"}))
        self.assertEqual(status, 2)
        self.assertIn("RECALL: FAIL", out)
        self.assertIn("field omitted: `<h> by handle`", out)
        self.assertIn("field invented: `5 does-not-apply`", out)

    def test_CL_T5_every_line_correct_and_consistent_passes_with_no_noise(self):
        out, status = run(workdoc())
        self.assertEqual(status, 0, out)
        self.assertIn("0 FAIL", out)
        self.assertNotIn(": FAIL", out)
        self.assertNotIn("NOT-CHECKABLE", out)
        self.assertIn("0 MISSING", out)
        self.assertIn("0 BROKEN", out)

    def test_CL_T6_an_all_zero_recall_on_an_empty_corpus_passes(self):
        """A zero line is a valid line: no lessons file must not read as a defect."""
        out, status = run(workdoc(phase="refine", drop=tuple(
            t for t in CLEAN_LINES if t not in ("PREMISE", "RECALL", "REFINE"))))
        self.assertEqual(status, 0, out)
        self.assertIn("RECALL: PASS", out)

    def test_CL_T7_a_counted_line_with_no_grammar_is_not_checkable_and_counted_separately(self):
        out, status = run(workdoc(extra="`AC VALIDATION: 5 AC | 5 falsifiable | 0 unfalsifiable`"))
        self.assertIn("AC VALIDATION: NOT-CHECKABLE", out)
        self.assertIn("1 not-checkable", out)
        self.assertNotEqual(status, 0, "a not-checkable line must never be a silent pass")
        self.assertEqual(status, 3, "not-checkable has its own exit status, distinct from a FAIL")
        self.assertNotIn("AC VALIDATION: PASS", out)

    def test_CL_T8_an_unreadable_working_doc_reports_plainly_and_never_passes(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "check_lines.py"), "check", "/nonexistent/PROJ-1.work.md"],
            capture_output=True, encoding="utf-8")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("CANNOT READ", proc.stdout)
        self.assertIn("NOTHING was checked", proc.stdout)
        self.assertNotIn("PASS", proc.stdout)

    def test_CL_T9_the_verdict_is_tied_to_one_doc_state_and_the_limit_is_stated(self):
        """No script can stop an agent quoting a verdict it never ran. The cheap half IS available: the
        verdict names the doc's length and digest, so a verdict quoted against a changed doc is
        detectable — and the docstring says plainly that the rest is a disclosure obligation."""
        out_a, _ = run(workdoc())
        out_b, _ = run(workdoc(extra="one more sentence"))
        fp_a = [ln for ln in out_a.splitlines() if ln.startswith("  doc")][0]
        fp_b = [ln for ln in out_b.splitlines() if ln.startswith("  doc")][0]
        self.assertNotEqual(fp_a, fp_b, "the fingerprint must move when the doc moves")
        self.assertIn("WHAT THIS CANNOT PREVENT", cl.__doc__)
        self.assertIn("disclosure\nobligation", cl.__doc__)


class TestCheckLinesGreenfield(unittest.TestCase):
    """A failure here blocks the version: the check must not become a tax on an ordinary ticket."""

    def test_CL_G1_a_fresh_first_ticket_with_every_line_at_zero_passes_with_no_extra_step(self):
        out, status = run(workdoc(phase="finalise"))
        self.assertEqual(status, 0, out)
        self.assertNotIn(": FAIL", out)
        self.assertNotIn("MISSING ", out)
        self.assertNotIn("GATE BROKEN", out)
        self.assertIn("0 pending", out)
        self.assertNotIn("pending (not yet required", out)

    def test_CL_G2_a_lite_lane_doc_is_held_only_to_the_lines_its_lane_emits(self):
        """`quick` runs exactly two reads pre-code; it emits no SECTIONS, CLARIFICATION or HANDLES."""
        lite = workdoc(phase="finalise", tier="lite", drop=(
            "PREMISE", "REFINE", "SECTIONS", "CLARIFICATION", "HANDLES", "EXCLUSIONS"))
        out, status = run(lite)
        self.assertEqual(status, 0, out)
        self.assertIn("0 MISSING", out)
        for absent in ("MISSING SECTIONS", "MISSING HANDLES", "MISSING EXCLUSIONS"):
            self.assertNotIn(absent, out)

    def test_CL_G2b_the_same_doc_on_the_full_lane_IS_held_to_them(self):
        """The negative control: the lite carve-out must come from TIER, not from leniency."""
        full = workdoc(phase="finalise", tier="full", drop=(
            "PREMISE", "REFINE", "SECTIONS", "CLARIFICATION", "HANDLES", "EXCLUSIONS"))
        out, status = run(full)
        self.assertEqual(status, 2)
        for token in ("SECTIONS", "HANDLES", "EXCLUSIONS"):
            self.assertIn(f"MISSING {token}", out)

    def test_CL_G3_a_host_where_the_script_cannot_run_is_the_callers_documented_fallback(self):
        """The script cannot report on its own absence. Every skill that invokes it must carry the
        could-not-run fallback in text: report not-checkable, do not block, do not claim to have
        checked."""
        for name in ("autorun", "solve", "finalise"):
            body = (ROOT / "plugins" / "mango" / "skills" / name / "SKILL.md").read_text(
                encoding="utf-8")
            self.assertTrue("check_lines.py" in body, f"{name} must invoke the checker")
            self.assertTrue(
                re.search(r"(?s)check_lines.{0,1200}(cannot run|not-checkable|could-not-run)", body),
                f"{name} must carry the could-not-run fallback beside the invocation")

    def test_CL_G3b_a_backend_doc_is_never_held_to_a_frontend_only_line(self):
        out, status = run(workdoc(track="backend"))
        self.assertEqual(status, 0, out)
        self.assertNotIn("SURFACES", out)


class TestCheckLinesDiscipline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_report_never_rewrite_the_doc_is_byte_identical_after_a_run(self):
        path = Path(self.tmp) / "PROJ-1.work.md"
        before = workdoc(replace={"CLAIMS": "CLAIMS: 3 claim(s) from 1 lesson entr(ies) | "
                                            "T1=0 T2=2 T3=1 T4=0 T5=1 T6=0 | 0 unclassified"})
        path.write_text(before, encoding="utf-8")
        proc = subprocess.run([sys.executable, str(SCRIPTS / "check_lines.py"), "check", str(path)],
                              capture_output=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(path.read_text(encoding="utf-8"), before, "the checker must never rewrite")

    def test_the_source_opens_the_doc_read_only_and_carries_no_write_path(self):
        src = (SCRIPTS / "check_lines.py").read_text(encoding="utf-8")
        self.assertNotIn("write_text", src)
        self.assertNotIn('"w"', src)
        self.assertNotIn("'w'", src)
        self.assertNotIn("os.replace", src)
        self.assertIn("REPORT, NEVER REWRITE", src)

    def test_the_checker_ships_no_counted_line_of_its_own(self):
        """It reports through the mechanism that already exists. A new counted line nothing parses is
        the joke this version exists to end."""
        src = (SCRIPTS / "check_lines.py").read_text(encoding="utf-8")
        for token in cl.GRAMMARS:
            self.assertNotIn(f"CHECK-LINES: {token}", src)
        self.assertNotIn("CHECK-LINES:", src.replace("CHECK-LINES: the", ""))

    def test_an_unfilled_template_placeholder_is_a_fail_not_a_pass(self):
        out, status = run(workdoc(replace={
            "HANDLES": "HANDLES: <h> recalled | <t> traced (command + result) | "
                       "<x> does not apply (reason) | <u> unanswered"}))
        self.assertEqual(status, 2)
        self.assertIn("unfilled template placeholder", out)

    def test_a_narrated_count_is_not_an_emission(self):
        """`a narrated count is an addition, never a substitute` — so prose mentioning the token does
        not satisfy the requirement."""
        out, status = run(workdoc(drop=("EXCLUSIONS",), extra=(
            "We recorded one coverage-gap exclusion, so EXCLUSIONS: 1 recorded with a checkable "
            "expiry and nothing recurring.")))
        self.assertEqual(status, 2)
        self.assertIn("MISSING EXCLUSIONS", out)

    def test_a_carried_forward_restatement_is_counted_not_double_penalised(self):
        """analysis carries refine's PREMISE/RECALL lines forward; that is one emission, not two."""
        doc = workdoc(phase="finalise")
        doc += f"\n`{CLEAN_LINES['PREMISE']}` *(carried forward)*\n`{CLEAN_LINES['RECALL']}`\n"
        out, status = run(doc)
        self.assertEqual(status, 0, out)
        self.assertIn("restated : 2", out)

    def test_a_contradiction_in_a_restatement_still_fails(self):
        """Off-grammar is judged on the best occurrence; a CONTRADICTION is judged on every one."""
        doc = workdoc(phase="finalise")
        doc += "\n`HANDLES: 4 recalled | 2 traced | 1 does not apply | 0 unanswered`\n"
        out, status = run(doc)
        self.assertEqual(status, 2)
        self.assertIn("h != t + x + u", out)

    def test_an_undeclared_phase_makes_the_required_axis_not_checkable_never_clean(self):
        doc = workdoc().replace("- **Current phase:** finalise", "- **Current phase:**")
        out, status = run(doc)
        self.assertEqual(status, 3)
        self.assertIn("does not declare its phase", out)
        self.assertIn("UNVERIFIED, not clean", out)

    def test_an_explicit_phase_flag_overrides_a_doc_that_does_not_declare_one(self):
        doc = workdoc().replace("- **Current phase:** finalise", "")
        out, status = run(doc, phase="finalise")
        self.assertEqual(status, 0, out)

    def test_the_embed_mode_separator_scopes_the_scan_to_the_working_doc(self):
        raw = ("# 101 — a raw ticket\n\n`RECALL: 9 claim(s) surfaced | 1 by symbol`\n\n"
               f"<!-- ===== {cl.MANGO_SEPARATOR} ===== -->\n" + workdoc())
        out, status = run(raw)
        self.assertEqual(status, 0, out)
        self.assertIn("RECALL: PASS", out)

    def test_header_field_labels_are_never_reported_as_counted_lines(self):
        out, _ = run(workdoc(extra="`STRUCTURE: native` · `TRACK: backend` · `TIER: full`"))
        self.assertNotIn("STRUCTURE:", out)
        self.assertNotIn("0 not-checkable | 0 pending\n    TIER", out)

    def test_a_near_miss_token_is_named_off_grammar_not_shrugged_off(self):
        out, status = run(workdoc(replace={"CLARIFICATION": "CLARIFICATIONS: j = 0 blocking"}))
        self.assertEqual(status, 2)
        self.assertIn("the canonical token is `CLARIFICATION:`", out)

    def test_natural_pluralisation_is_tolerated_but_a_truncated_label_is_not(self):
        ok, status_ok = run(workdoc(replace={
            "CLAIMS": "CLAIMS: 1 claim from 1 lesson entry | T1=0 T2=0 T3=0 T4=1 T5=0 T6=0 | "
                      "0 unclassified"}))
        self.assertEqual(status_ok, 0, ok)
        bad, status_bad = run(workdoc(replace={
            "RECURRING-T2": "RECURRING-T2: 0 type-2 with seen >= 2 | 0 routed | 0 cannot promote | "
                            "0 left in lessons_path"}))
        self.assertEqual(status_bad, 2)
        self.assertIn("RECURRING-T2: FAIL", bad)

    def test_a_gate_condition_the_shipped_text_calls_blocking_is_counted_broken(self):
        out, status = run(workdoc(replace={
            "EXCLUSIONS": "EXCLUSIONS: 2 recorded | 1 with a checkable expiry | 0 recurring | "
                          "0 with an overdue predecessor"}))
        self.assertEqual(status, 2)
        self.assertIn("GATE BROKEN EXCLUSIONS", out)
        self.assertIn("BLOCKS Gate 2", out)

    def test_a_clarification_for_a_human_is_a_fact_not_a_broken_gate(self):
        """`j > 0` is a legitimate STOP. Reporting it as a gate failure would conflate a correct stop
        with a defect."""
        out, status = run(workdoc(replace={
            "CLARIFICATION": "CLARIFICATION: 2 raised | 1 self-resolved (cited) | "
                             "1 for human decision"}))
        self.assertEqual(status, 0, out)
        self.assertIn("CLARIFICATION: PASS", out)
        self.assertNotIn("GATE BROKEN CLARIFICATION", out)

    def test_every_grammar_carries_a_canonical_form_and_an_emitter(self):
        for token, spec in cl.GRAMMARS.items():
            self.assertTrue(spec["canonical"].startswith(f"{token}:"), token)
            self.assertTrue(spec["emitter"], token)
            self.assertTrue(spec["segments"], token)

    def test_the_canonical_form_of_every_grammar_parses_against_itself(self):
        """A registry entry whose own canonical form does not parse would silently never match."""
        for token, spec in cl.GRAMMARS.items():
            body = spec["canonical"].split(":", 1)[1].strip()
            _, _, problems = cl.parse_line(token, body)
            self.assertEqual(
                problems, ["unfilled template placeholder — the line was copied, not emitted"],
                f"{token}: the canonical form must be recognised as the template it is, nothing else")

    def test_the_grammars_subcommand_prints_every_shipped_line(self):
        proc = subprocess.run([sys.executable, str(SCRIPTS / "check_lines.py"), "grammars"],
                              capture_output=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0)
        for token in cl.GRAMMARS:
            self.assertIn(token, proc.stdout)


# ===========================================================================================
# v1.14.0 — fixture provenance (A), evidence provenance (E), the size margin (G)
# ===========================================================================================
#
# Numbered to match the build spec's teeth table so a later reader can map an assertion to the field
# case it came from. Every fixture is a synthetic working doc built in memory: no project, no dispatch.


def excl(n=0, e=0, r=0, o=0, s=0, c=0):
    return (f"EXCLUSIONS: {n} recorded | {e} with a checkable expiry | {r} recurring "
            f"(class seen >= 3) | {o} with an overdue predecessor | "
            f"{s} input-shape-dependent AC(s) | {c} proven on a real corpus")


class TestSpecLines(unittest.TestCase):
    """Track S — the spec track's lines. A spec phase holds a document only to its own lines, never to a
    lifecycle line; a lens `not run` is never a clean round."""

    @staticmethod
    def review(line):
        return f"# A spec\n\n## Review record\n\n| id | lens |\n|---|---|\n\n`{line}`\n"

    CLEAN = ("SPEC REVIEW: round 2 | 3 lenses | 0 not run | 0 blockers open | 0 majors open | "
             "4 settled | 0 escalated open")

    def test_a_clean_round_passes_and_is_held_to_no_lifecycle_line(self):
        out, status = run(self.review(self.CLEAN), phase="spec-review")
        self.assertEqual(status, 0, out)
        self.assertIn("1 required through spec-review | 0 MISSING", out)
        self.assertIn("| 0 pending", out)
        self.assertNotIn("pending (not yet required", out)

    def test_a_lens_not_run_is_never_a_clean_round(self):
        line = self.CLEAN.replace("0 not run", "1 not run")
        out, status = run(self.review(line), phase="spec-review")
        self.assertEqual(status, 2, out)
        self.assertIn("GATE BROKEN SPEC REVIEW", out)

    def test_open_blocker_major_or_escalate_breaks_the_round(self):
        for old, new in (("0 blockers open", "1 blocker open"), ("0 majors open", "2 majors open"),
                         ("0 escalated open", "1 escalated open")):
            out, status = run(self.review(self.CLEAN.replace(old, new)), phase="spec-review")
            self.assertEqual(status, 2, out)

    def test_more_lenses_not_run_than_dispatched_is_a_contradiction(self):
        line = self.CLEAN.replace("3 lenses", "1 lens").replace("0 not run", "2 not run")
        out, status = run(self.review(line), phase="spec-review")
        self.assertEqual(status, 2, out)
        self.assertIn("x > l", out)

    def test_a_missing_line_at_its_phase_is_missing(self):
        out, status = run("# A spec\n\nNo review yet.\n", phase="spec-review")
        self.assertEqual(status, 2, out)
        self.assertIn("MISSING SPEC REVIEW", out)

    def test_the_cli_accepts_the_spec_phases(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "x.spec.md"
            path.write_text(self.review(self.CLEAN), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                status = cl.main(["check_lines.py", "check", str(path), "--phase", "spec-review"])
            self.assertEqual(status, 0, buf.getvalue())


class TestProtocolHeader(unittest.TestCase):
    """`PROTOCOL:` opts a doc into a protocol version. A doc without it is legacy and its report does not
    change; an unknown version is never read as legacy and never passed."""

    @staticmethod
    def declare(field):
        return workdoc().replace("- **SCOPE:** S\n", f"- **SCOPE:** S\n{field}\n")

    @staticmethod
    def without_doc_line(out):
        """The report minus its `doc` line, line numbers dropped (the field adds a header line)."""
        return [re.sub(r"\(line \d+\)", "(line N)", line)
                for line in out.splitlines() if not line.startswith("  doc      :")]

    def test_a_doc_without_the_field_is_legacy_and_reports_no_protocol(self):
        out, status = run(workdoc())
        self.assertEqual(status, 0, out)
        self.assertNotIn("protocol", out.lower())
        self.assertIsNone(cl.read_header(workdoc())["protocol"])

    def test_a_declared_version_is_named_on_the_doc_line_and_v0_1_changes_nothing_else(self):
        legacy, _ = run(workdoc())
        for field in ("- **PROTOCOL:** v0.1", "`PROTOCOL: v0.1` · `TIER: full`"):
            out, status = run(self.declare(field))
            self.assertEqual(status, 0, out)
            doc_line = next(line for line in out.splitlines() if line.startswith("  doc      :"))
            self.assertTrue(doc_line.endswith("| protocol: v0.1"), doc_line)
            self.assertEqual(self.without_doc_line(out), self.without_doc_line(legacy))

    def test_a_v0_2_doc_must_carry_proof_from_review_and_a_legacy_doc_never_sees_it(self):
        out, status = run(self.declare("- **PROTOCOL:** v0.2"))
        self.assertEqual(status, 2, out)
        self.assertIn("MISSING PROOF: required through finalise", out)
        early, _ = run(self.declare("- **PROTOCOL:** v0.2").replace("finalise", "design"))
        self.assertIn("pending (not yet required at design): ", early)
        self.assertIn("PROOF", early.split("pending (not yet required at design): ")[1])
        for phase in ("design", "review", "finalise"):
            legacy, _ = run(workdoc(phase=phase))
            self.assertNotIn("PROOF", legacy, phase)

    def test_a_v0_2_doc_is_clean_with_a_clean_proof_or_a_recorded_waiver(self):
        line = ("`PROOF: 3 proving test(s) | 3 proven | 0 regression-guard | 0 green@base | "
                "0 env-fault@base | 0 not green@head | 0 flaky | 0 could-not-run`")
        for extra in (line, "PROOF waived (verification.proof.enabled: false)"):
            out, status = run(self.declare("- **PROTOCOL:** v0.2").replace("## Session status",
                                                                            extra + "\n\n## Session status"))
            self.assertEqual(status, 0, out)

    def test_proof_gates_block_on_a_green_base_a_red_head_or_no_test(self):
        for line, gate in (
                ("PROOF: 2 proving test(s) | 1 proven | 0 regression-guard | 1 green@base | "
                 "0 env-fault@base | 0 not green@head | 0 flaky | 0 could-not-run", "z > 0"),
                ("PROOF: 1 proving test(s) | 0 proven | 0 regression-guard | 0 green@base | "
                 "0 env-fault@base | 1 not green@head | 0 flaky | 0 could-not-run", "g > 0"),
                ("PROOF: 0 proving test(s) | 0 proven | 0 regression-guard | 0 green@base | "
                 "0 env-fault@base | 0 not green@head | 0 flaky | 0 could-not-run", "n = 0")):
            out, status = run(workdoc(extra=f"`{line}`"))
            self.assertEqual(status, 2, out)
            self.assertIn(f"GATE BROKEN PROOF", out)
            self.assertIn(gate, out)
        out, status = run(workdoc(extra="`PROOF: 3 proving test(s) | 3 proven | 0 regression-guard | "
                                        "0 green@base | 0 env-fault@base | 0 not green@head | 0 flaky | "
                                        "1 could-not-run`"))
        self.assertEqual(status, 2, out)
        self.assertIn("n != p + r + z + e + g + f + c", out)

    def test_an_unknown_version_is_not_checkable_never_legacy_or_a_pass(self):
        out, status = run(self.declare("- **PROTOCOL:** v9"))
        self.assertEqual(status, 3, out)
        self.assertIn("| protocol: v9", out)
        self.assertIn("NOT-CHECKABLE: the doc declares `PROTOCOL: v9`", out)

    def test_an_unknown_version_does_not_hide_a_failure(self):
        out, status = run(self.declare("- **PROTOCOL:** v9").replace("`PREMISE:", "`PREMISES:"))
        self.assertEqual(status, 2, out)

    def test_a_template_placeholder_is_not_a_declaration(self):
        self.assertIsNone(cl.read_header(self.declare("- **PROTOCOL:** <v0.2 | omit>"))["protocol"])

    def test_the_field_in_the_raw_ticket_above_the_embed_separator_is_ignored(self):
        raw = ("# 101 — a raw ticket\n\n- **PROTOCOL:** v0.2\n\n"
               f"<!-- ===== {cl.MANGO_SEPARATOR} ===== -->\n" + workdoc())
        out, status = run(raw)
        self.assertEqual(status, 0, out)
        self.assertNotIn("protocol", out.lower())

    def test_the_field_quoted_below_the_header_declares_nothing(self):
        doc = workdoc().replace("## Session status", "## Phase 1\n\nA lesson says to write "
                                "`PROTOCOL: v0.2` in new docs.\n\n## Session status")
        self.assertIsNone(cl.read_header(doc)["protocol"])

    def test_the_field_is_never_reported_as_a_counted_line(self):
        out, _ = run(self.declare("`PROTOCOL: v0.2` · `TIER: full`"))
        self.assertIn("0 not-checkable", out)
        self.assertNotIn("PROTOCOL:", out)


class TestFixtureProvenance(unittest.TestCase):
    """A — an AC whose correctness depends on the SHAPE OF REAL INPUT may not close on authored
    fixtures alone. Four field cases, four real-data defects, four green fixture suites: the fixture is
    part of the diff, so a diff and the fixture shaped to it agree with each other and nothing else."""

    def test_T1_an_input_shape_AC_on_authored_fixtures_alone_blocks_gate_2(self):
        out, status = run(workdoc(phase="design", replace={"EXCLUSIONS": excl(s=1, c=0)}))
        self.assertEqual(status, 2, out)
        self.assertIn("GATE BROKEN EXCLUSIONS", out)
        self.assertIn("s - c > n", out)

    def test_T2_the_same_AC_proven_on_the_real_corpus_passes(self):
        out, status = run(workdoc(phase="design", replace={"EXCLUSIONS": excl(s=1, c=1)}))
        self.assertEqual(status, 0, out)
        self.assertIn("EXCLUSIONS: PASS", out)

    def test_T3_authored_plus_an_exclusion_with_a_checkable_expiry_passes(self):
        """The honest escape, and it is the EXISTING one — 1.12.0's exclusion, not a second hatch."""
        out, status = run(workdoc(phase="design", replace={"EXCLUSIONS": excl(n=1, e=1, s=1, c=0)}))
        self.assertEqual(status, 0, out)

    def test_T4_authored_plus_an_exclusion_with_NO_expiry_is_still_blocked(self):
        """1.12.0's rule still bites: an exclusion with no checkable expiry does not count as recorded."""
        out, status = run(workdoc(phase="design", replace={"EXCLUSIONS": excl(n=1, e=0, s=1, c=0)}))
        self.assertEqual(status, 2, out)
        self.assertIn("e != n", out)

    def test_T5_an_AC_comparing_two_literal_values_costs_nothing(self):
        """THE ANTI-TAX CONTROL. Most ACs are `n/a`; an all-zero line passes and adds no work at all."""
        out, status = run(workdoc(phase="design", replace={"EXCLUSIONS": excl()}))
        self.assertEqual(status, 0, out)
        self.assertNotIn("GATE BROKEN", out)
        self.assertNotIn("input-shape-dependent AC(s) | 0 proven", out.split("EXCLUSIONS: PASS")[-1])

    def test_more_corpus_proofs_than_input_shape_ACs_is_a_contradiction(self):
        out, status = run(workdoc(phase="design", replace={"EXCLUSIONS": excl(s=1, c=2)}))
        self.assertEqual(status, 2, out)
        self.assertIn("c > s", out)

    def test_G1_a_greenfield_design_phase_with_no_corpus_is_clean(self):
        """GREENFIELD — a fresh project has no corpus and must run with ZERO extra steps."""
        out, status = run(workdoc(phase="design", replace={"EXCLUSIONS": excl()},
                                  drop=("CLAIMS", "RECURRENCE", "FALSIFY", "RECURRING-T2",
                                        "PROMOTION", "LEDGER TOTAL")))
        self.assertEqual(status, 0, out)
        self.assertIn("0 MISSING", out)

    def test_G3_a_backend_project_is_unaffected_by_anything_in_A(self):
        out, status = run(workdoc(track="backend", replace={"EXCLUSIONS": excl()}))
        self.assertEqual(status, 0, out)
        self.assertNotIn("SURFACES", out)

    def test_the_canonical_form_still_parses_against_itself(self):
        counts, _, problems = cl.parse_line("EXCLUSIONS", cl.GRAMMARS["EXCLUSIONS"]["canonical"]
                                            .split(": ", 1)[1].replace("<n>", "0").replace("<e>", "0")
                                            .replace("<r>", "0").replace("<o>", "0")
                                            .replace("<s>", "0").replace("<c>", "0"))
        self.assertEqual(problems, [])
        self.assertEqual(counts["s"], 0)
        self.assertEqual(counts["c"], 0)


class TestEvidenceProvenance(unittest.TestCase):
    """E — test evidence carries the SHA of the tree it ran on, and a gate refuses evidence from a
    different tree. This sits UNDERNEATH every other gate: a green suite from a stale tree satisfies
    all of them, because nothing else asks which tree produced it."""

    TREE = "b7d5e29aa11"

    def _doc(self, block):
        return workdoc(phase="review", extra=block)

    def test_T14_evidence_matching_the_tree_passes_with_no_extra_work(self):
        out, status = run(self._doc("Ran at `b7d5e29`\n\n```\n$ pytest -q\n84 passed\n```"),
                          tree=self.TREE)
        self.assertEqual(status, 0, out)
        self.assertIn("1 on the tree under review", out)
        self.assertIn("0 from ANOTHER tree", out)

    def test_T11_evidence_from_another_tree_is_refused(self):
        out, status = run(self._doc("Ran at `c40b7e1`\n\n```\n$ pytest -q\n84 passed\n```"),
                          tree=self.TREE)
        self.assertEqual(status, 2, out)
        self.assertIn("1 from ANOTHER tree", out)
        self.assertIn("REFUSED", out)

    def test_T12_a_container_built_before_the_last_commit_is_refused(self):
        """This is ticket 150: `docker build` ran before the last edits landed, so COPY captured the
        previous tree and the delta-green run was green against code that was no longer the code."""
        block = ("Ran at `c40b7e1`  <!-- the tree the image was BUILT FROM -->\n\n"
                 "```\n$ docker run --rm atlas-ci pytest -q\n84 passed\n```")
        out, status = run(self._doc(block), tree=self.TREE)
        self.assertEqual(status, 2, out)
        self.assertIn("is NOT the tree under review", out)

    def test_T13_evidence_whose_tree_cannot_be_established_is_never_a_pass(self):
        out, status = run(self._doc("```\n$ ./scripts/migrate --check\n0 rows changed\n```"),
                          tree=self.TREE)
        self.assertEqual(status, 3, out)
        self.assertIn("provenance-unknown", out)
        self.assertNotIn("PASS (line", out.split("EVIDENCE")[-1])

    def test_T13_the_explicit_marker_is_also_provenance_unknown(self):
        out, status = run(self._doc("Ran at `provenance-unknown`\n\n```\n$ pytest -q\nok\n```"),
                          tree=self.TREE)
        self.assertEqual(status, 3, out)
        self.assertIn("1 provenance-unknown", out)

    def test_a_stale_record_outranks_an_unknown_one_on_the_exit_status(self):
        block = ("Ran at `c40b7e1`\n\n```\n$ pytest -q\nok\n```\n\n"
                 "```\n$ npm test\nok\n```")
        out, status = run(self._doc(block), tree=self.TREE)
        self.assertEqual(status, 2, out)          # a FAIL is a stronger answer than not-checkable

    def test_without_the_tree_the_axis_is_ABSENT_not_silently_clean(self):
        """An axis that was not asked is a different answer from an axis that was verified."""
        out, status = run(self._doc("```\n$ pytest -q\nok\n```"))
        self.assertEqual(status, 0, out)
        self.assertNotIn("evidence :", out)

    def test_a_fence_that_is_not_empirical_output_is_not_an_evidence_record(self):
        """Only the shipped `$ <command>` shape is a record — a code sample is not test evidence."""
        out, status = run(self._doc("```\ndef f(x):\n    return x\n```"), tree=self.TREE)
        self.assertEqual(status, 0, out)
        self.assertIn("0 empirical-output record(s)", out)

    def test_the_shipped_marker_shape_binds_to_its_block(self):
        """The template puts `Ran at <sha>` directly above the fence; that shape must bind."""
        block = "Ran at `b7d5e29`\n\n```\n$ pytest -q -k proving\n1 passed\n```"
        out, status = run(self._doc(block), tree=self.TREE)
        self.assertEqual(status, 0, out)
        self.assertIn("1 on the tree under review", out)

    def test_a_marker_too_far_from_its_block_fails_SAFE_to_unknown_not_to_a_pass(self):
        """The lookback is deliberately narrow. A marker a paragraph away is not claimed as this
        block's provenance — the axis reports provenance-unknown rather than GUESSING a pass, which is
        the direction a provenance check must fail in."""
        block = ("Ran at `b7d5e29`\n\nsome prose\n\nand more prose\n\n"
                 "```\n$ pytest -q -k proving\n1 passed\n```")
        out, status = run(self._doc(block), tree=self.TREE)
        self.assertEqual(status, 3, out)
        self.assertIn("1 provenance-unknown", out)

    def test_the_marker_binds_inside_the_block_too(self):
        block = "```\n$ pytest -q\n1 passed\nRan at b7d5e29\n```"
        out, status = run(self._doc(block), tree=self.TREE)
        self.assertEqual(status, 0, out)
        self.assertIn("1 on the tree under review", out)

    # v1.19.2 — pre-change evidence. Found by the golden e2e: analysis's BASELINE, design's
    # blast-radius trace and execute's fails-without run all run BEFORE the change, so under `--tree
    # HEAD` every honest doc was refused at Gate 4. The role binds to exactly one caller-supplied SHA.

    BASE = "f338bb6b75b"

    def test_E2_pre_change_evidence_on_the_base_is_accepted_on_its_own_field(self):
        block = ("Ran at `f338bb6` (pre-change)\n\n```\n$ pytest -q\n3 passed\n```\n\n"
                 "Ran at `b7d5e29`\n\n```\n$ pytest -q\n7 passed\n```")
        out, status = run(self._doc(block), tree=self.TREE, base=self.BASE)
        self.assertEqual(status, 0, out)
        self.assertIn("1 on the tree under review", out)
        self.assertIn("1 pre-change on the base", out)
        self.assertIn("0 from ANOTHER tree", out)

    def test_E2_pre_change_evidence_is_never_counted_as_on_the_tree_under_review(self):
        out, status = run(self._doc("Ran at `f338bb6` (pre-change)\n\n```\n$ pytest -q\nok\n```"),
                          tree=self.TREE, base=self.BASE)
        self.assertIn("0 on the tree under review", out)
        self.assertIn("1 pre-change on the base", out)

    def test_E2_pre_change_naming_another_tree_is_refused(self):
        out, status = run(self._doc("Ran at `c40b7e1` (pre-change)\n\n```\n$ pytest -q\nok\n```"),
                          tree=self.TREE, base=self.BASE)
        self.assertEqual(status, 2, out)
        self.assertIn("NOT the base the branch was cut from", out)
        self.assertIn("0 pre-change on the base", out)

    def test_E2_pre_change_without_a_base_is_refused_not_trusted(self):
        out, status = run(self._doc("Ran at `f338bb6` (pre-change)\n\n```\n$ pytest -q\nok\n```"),
                          tree=self.TREE)
        self.assertEqual(status, 2, out)
        self.assertIn("no --base was given", out)

    def test_E2_an_undeclared_record_on_the_base_is_still_stale(self):
        """The base is accepted only for a record that DECLARES the pre-change role."""
        out, status = run(self._doc("Ran at `f338bb6`\n\n```\n$ pytest -q\nok\n```"),
                          tree=self.TREE, base=self.BASE)
        self.assertEqual(status, 2, out)
        self.assertIn("1 from ANOTHER tree", out)

    def test_E2_a_pre_change_role_does_not_rescue_an_unknown_tree(self):
        out, status = run(self._doc("Ran at `provenance-unknown` (pre-change)\n\n```\n$ pytest -q\nok\n```"),
                          tree=self.TREE, base=self.BASE)
        self.assertEqual(status, 3, out)
        self.assertIn("1 provenance-unknown", out)


class TestSizeMargin(unittest.TestCase):
    """G — the size budget is surfaced BEFORE it bites. mango measures no ceiling of its own; the
    project supplies it, this reuses the byte length already computed, adds no counted line, and never
    blocks."""

    def test_T17_a_doc_just_under_the_ceiling_surfaces_its_margin_and_blocks_nothing(self):
        doc = workdoc()
        budget = int(len(doc.encode("utf-8")) / 0.9)
        out, status = run(doc, size_budget=budget)
        self.assertEqual(status, 0, out)
        self.assertIn("SIZE:", out)
        self.assertIn("margin left", out)
        self.assertIn("nothing is blocked", out)

    def test_a_doc_over_the_ceiling_is_reported_and_still_does_not_block(self):
        doc = workdoc()
        out, status = run(doc, size_budget=10)
        self.assertEqual(status, 0, out)
        self.assertIn("over budget", out)

    def test_a_doc_well_inside_the_ceiling_warns_about_nothing(self):
        doc = workdoc()
        out, status = run(doc, size_budget=len(doc.encode("utf-8")) * 10)
        self.assertEqual(status, 0, out)
        self.assertIn("size:", out)
        self.assertNotIn("SIZE:", out)

    def test_with_no_budget_configured_nothing_is_reported(self):
        out, _ = run(workdoc())
        self.assertNotIn("size:", out)

    def test_a_nonsense_budget_is_ignored_rather_than_crashing(self):
        for bad in ("", "lots", "0", "-5", None):
            self.assertEqual(cl.size_margin("x" * 10, bad), ("", []), bad)

    def test_the_margin_rides_the_doc_line_and_adds_no_counted_line(self):
        doc = workdoc()
        out, _ = run(doc, size_budget=len(doc.encode("utf-8")) * 2)
        doc_line = next(ln for ln in out.splitlines() if ln.strip().startswith("doc "))
        self.assertIn("size:", doc_line)


class TestConsoleEncoding(unittest.TestCase):
    """v1.17.2 — every harness script writes UTF-8 whatever the console's code page. A cp1252 console
    (Windows' default) cannot encode the ≥ and — the grammars carry; before 1.17.2 the script crashed
    there, and a checker that crashes reads as one that never ran."""

    CP1252 = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}

    def run_script(self, name, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / name), *args],
                              capture_output=True, encoding="utf-8", env=self.CP1252)

    def test_check_lines_grammars_survives_a_cp1252_console(self):
        proc = self.run_script("check_lines.py", "grammars")
        self.assertNotIn("UnicodeEncodeError", proc.stderr)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("≥", proc.stdout)

    def test_every_script_usage_survives_a_cp1252_console(self):
        for name in ("check_lines.py", "run_contract.py", "reconcile.py", "budget.py"):
            with self.subTest(script=name):
                proc = self.run_script(name)
                self.assertNotIn("UnicodeEncodeError", proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)
                self.assertTrue(any(ord(c) > 127 for c in proc.stdout),
                                f"{name}'s usage text carries no non-ASCII, so this test proves nothing")


# --------------------------------------------------------------------------- PROOF

import proof  # noqa: E402

PROOF_DOC = (
    "# PROJ-1 — a ticket (working doc)\n\n## Phase 2 — Design\n\n"
    "- **Proving test** (fails pre-change, passes post-change):\n  `{command}`\n"
    "- **Regression guards:** {guards}\n\n## Phase 3 — Execute\n"
)

# The interpreter running this suite: on Windows `python3` may be the Store stub.
PY = shlex.quote(sys.executable)
BASE_PKG = "def old():\n    return 1\n"
FLAKY_TEST = (
    "import os, unittest, hashlib\n"
    "class F(unittest.TestCase):\n"
    "    def test_flaky(self):\n"
    "        mark = os.path.join(os.environ['PROOF_MARKS'], hashlib.sha1(os.getcwd().encode()).hexdigest())\n"
    "        if not os.path.exists(mark):\n"
    "            open(mark, 'w').close()\n"
    "            self.fail('first run in this tree')\n"
)


class TestProof(unittest.TestCase):
    """The proving test runs at base (with head's tests) and at head; each test is classified by the
    kind of failure. A green-at-base proof or a red head blocks; worktrees never outlive the run."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        (self.repo / "pkg").mkdir(parents=True)
        (self.repo / "tests").mkdir()
        (self.repo / "pkg" / "__init__.py").write_text(BASE_PKG)
        (self.repo / "tests" / "__init__.py").write_text("")
        (self.repo / "tests" / "test_old.py").write_text(
            "import unittest\nfrom pkg import old\n"
            "class Old(unittest.TestCase):\n    def test_old(self):\n        self.assertEqual(old(), 1)\n")
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
        self.base = self.git("rev-parse", "HEAD").strip()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, text=True,
                              check=True).stdout

    def commit_head(self, files):
        for rel, text in files.items():
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "head")

    def run_proof(self, command, guards="none", config=None):
        doc = self.tmp / "PROJ-1.work.md"
        doc.write_text(PROOF_DOC.format(command=command, guards=guards))
        args = ["proof.py", "run", str(doc), "--base", self.base, "--repo", str(self.repo)]
        if config is not None:
            cfg = self.tmp / "harness.json"
            cfg.write_text(json.dumps(config))
            args += ["--config", str(cfg)]
        buf = io.StringIO()
        with redirect_stdout(buf):
            status = proof.main(args)
        out = buf.getvalue()
        worktrees = self.git("worktree", "list").strip().splitlines()
        self.assertEqual(len(worktrees), 1, f"a worktree outlived the run: {worktrees}")
        self.assertEqual(self.git("status", "--porcelain"), "", "the checkout was modified")
        return out, status

    def counts(self, out):
        m = re.search(r"^PROOF: .*$", out, re.M)
        self.assertIsNotNone(m, out)
        lines, _ = cl.check_doc(f"`{m.group(0)}`\n")
        self.assertIn("PROOF: PASS", "\n".join(lines), "proof.py wrote a PROOF line its grammar refuses")
        return {k: int(v) for v, k in re.findall(
            r"(\d+) (proving test\(s\)|proven|regression-guard|green@base|env-fault@base|"
            r"not green@head|flaky|could-not-run)", m.group(0))}

    def test_a_test_red_at_base_and_green_at_head_is_proven(self):
        self.commit_head({
            "pkg/__init__.py": "def old(scale=1):\n    return scale\n",
            "tests/test_new.py": "import sys, unittest\nfrom pkg import old\n"
                                 "class New(unittest.TestCase):\n    def test_scale(self):\n"
                                 "        print('noise', file=sys.stderr)\n        self.assertEqual(old(3), 3)\n",
        })
        out, status = self.run_proof(PY + " -m unittest tests.test_new.New.test_scale")
        self.assertEqual(status, 0, out)
        self.assertEqual(self.counts(out), {"proving test(s)": 1, "proven": 1, "regression-guard": 0,
                                            "green@base": 0, "env-fault@base": 0, "not green@head": 0,
                                            "flaky": 0, "could-not-run": 0})
        self.assertIn("base ERROR TypeError", out)

    def test_a_proof_green_at_base_proves_nothing_and_blocks(self):
        self.commit_head({"pkg/__init__.py": BASE_PKG + "\ndef more():\n    return 2\n"})
        out, status = self.run_proof(PY + " -m unittest tests.test_old")
        self.assertEqual(status, 2, out)
        self.assertEqual(self.counts(out)["green@base"], 1)

    def test_a_declared_regression_guard_green_at_base_is_expected_and_never_blocks(self):
        self.commit_head({"pkg/__init__.py": "def old():\n    return 0 + 1\n"})
        out, status = self.run_proof(PY + " -m unittest tests.test_old", guards="`Old.test_old`")
        self.assertEqual(status, 0, out)
        self.assertEqual(self.counts(out)["regression-guard"], 1)

    def test_an_import_of_a_symbol_or_module_the_diff_adds_is_proven(self):
        self.commit_head({
            "pkg/__init__.py": BASE_PKG + "\ndef newsym():\n    return 2\n",
            "pkg/extra.py": "VALUE = 3\n",
            "tests/test_sym.py": "import unittest\nfrom pkg import newsym\n"
                                 "class S(unittest.TestCase):\n    def test_sym(self):\n"
                                 "        self.assertEqual(newsym(), 2)\n",
            "tests/test_mod.py": "import unittest\nfrom pkg.extra import VALUE\n"
                                 "class M(unittest.TestCase):\n    def test_mod(self):\n"
                                 "        self.assertEqual(VALUE, 3)\n",
        })
        out, status = self.run_proof(PY + " -m unittest tests.test_sym tests.test_mod")
        self.assertEqual(status, 0, out)
        self.assertEqual(self.counts(out)["proven"], 2, out)
        self.assertIn("which the diff adds", out)

    def test_an_import_of_something_the_diff_does_not_add_is_an_env_fault(self):
        self.assertEqual(proof.import_verdict(str(self.repo), self.base, self.base,
                                              ("symbol", "old", "pkg")), "both-trees")
        self.assertEqual(proof.import_verdict(str(self.repo), self.base, self.base,
                                              ("module", "not_installed_anywhere", None)), "unknown")
        for exc, msg in (("ModuleNotFoundError", "No module named 'not_installed_anywhere'"),
                         ("ImportError", "cannot import name 'old' from 'pkg' (/x/pkg/__init__.py)"),
                         ("ConnectionRefusedError", "[Errno 111] Connection refused")):
            field, _ = proof.classify("t.T.x", ("ERROR", exc, msg), ("ok", "", ""), None, [],
                                      str(self.repo), self.base, self.base)
            self.assertEqual(field, "env-fault@base", exc)

    def test_a_head_that_is_not_green_blocks(self):
        self.commit_head({"tests/test_new.py": "import unittest\nclass N(unittest.TestCase):\n"
                                               "    def test_n(self):\n        self.assertEqual(1, 2)\n"})
        out, status = self.run_proof(PY + " -m unittest tests.test_new")
        self.assertEqual(status, 2, out)
        self.assertEqual(self.counts(out)["not green@head"], 1)

    def test_a_test_module_that_does_not_import_at_head_is_not_green(self):
        self.commit_head({"tests/test_new.py": "import unittest\nfrom pkg import missing\n"})
        out, status = self.run_proof(PY + " -m unittest tests.test_new")
        self.assertEqual(status, 2, out)
        self.assertEqual(self.counts(out)["not green@head"], 1)

    def test_a_skipped_proof_at_head_is_not_green(self):
        self.commit_head({"tests/test_new.py": "import unittest\nclass N(unittest.TestCase):\n"
                                               "    @unittest.skip('later')\n"
                                               "    def test_n(self):\n        pass\n"})
        out, status = self.run_proof(PY + " -m unittest tests.test_new")
        self.assertEqual(status, 2, out)
        self.assertEqual(self.counts(out)["not green@head"], 1)

    def test_a_test_that_passes_on_one_rerun_at_head_is_flaky(self):
        marks = self.tmp / "marks"
        marks.mkdir()
        self.commit_head({"tests/test_flaky.py": FLAKY_TEST})
        with mock.patch.dict(os.environ, {"PROOF_MARKS": str(marks)}):
            out, status = self.run_proof(PY + " -m unittest tests.test_flaky")
        self.assertEqual(status, 3, out)
        self.assertEqual(self.counts(out)["flaky"], 1)

    def test_an_unsupported_runner_or_no_command_is_one_could_not_run_never_zero_tests(self):
        self.commit_head({"pkg/__init__.py": "def old():\n    return 1  # head\n"})
        for command in ("pytest tests", PY + " -m unittest tests && echo done"):
            out, status = self.run_proof(command)
            self.assertEqual(status, 3, out)
            self.assertEqual(self.counts(out)["proving test(s)"], 1)
            self.assertEqual(self.counts(out)["could-not-run"], 1)
        doc = self.tmp / "empty.work.md"
        doc.write_text("# PROJ-1\n\n## Phase 2 — Design\n\nno command here\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            status = proof.main(["proof.py", "run", str(doc), "--base", self.base, "--repo", str(self.repo)])
        self.assertEqual(status, 3, buf.getvalue())
        self.assertIn("no proving-test command in Phase 2", buf.getvalue())

    def test_a_timeout_leaves_the_tests_could_not_run_and_cleans_up(self):
        before = set(Path(tempfile.gettempdir()).glob("mango-proof-*"))
        self.commit_head({"tests/test_slow.py": "import time, unittest\nclass S(unittest.TestCase):\n"
                                                "    def test_s(self):\n        time.sleep(5)\n"})
        out, status = self.run_proof(PY + " -m unittest tests.test_slow",
                                     config={"verification": {"proof": {"timeout_s": 1}}})
        self.assertEqual(status, 3, out)
        self.assertEqual(self.counts(out)["could-not-run"], 1)
        self.assertEqual(set(Path(tempfile.gettempdir()).glob("mango-proof-*")), before)

    def test_enabled_false_is_waived_and_writes_no_proof_line(self):
        self.commit_head({"pkg/__init__.py": "def old():\n    return 1  # head\n"})
        out, status = self.run_proof(PY + " -m unittest tests.test_old",
                                     config={"verification": {"proof": {"enabled": False}}})
        self.assertEqual(status, 3)
        self.assertEqual(out.strip(), proof.WAIVED)

    def test_the_unittest_reader_handles_both_header_shapes_and_interleaved_output(self):
        output = ("test_a (tests.test_x.X) ... ok\n"
                  "test_b (tests.test_x.X.test_b) ... some printed text\nERROR\n"
                  "test_c (tests.test_x.X.test_c)\nA docstring ... skipped 'why'\n"
                  "test_d (tests.test_x.X.test_d) ... printed\n\n"
                  "======================================================================\n"
                  "ERROR: test_b (tests.test_x.X.test_b)\n------\nTraceback\nValueError: bad\n\n"
                  "----------------------------------------------------------------------\nRan 4 tests\n")
        results, failed = proof.parse_unittest(output)
        self.assertEqual(results["tests.test_x.X.test_a"][0], "ok")
        self.assertEqual(results["tests.test_x.X.test_b"], ("ERROR", "ValueError", "bad"))
        self.assertEqual(results["tests.test_x.X.test_c"][0], "skipped")
        self.assertNotIn("tests.test_x.X.test_d", results, "a test with no readable status is never a pass")
        self.assertEqual(failed, {})

    def test_verbose_goes_after_discover_never_before_it(self):
        """1.23.1 — an e2e run's design named `unittest discover -s tests -t .`; `-v` inserted before
        `discover` made unittest reject `-s` and the proof `could-not-run`."""
        argv, why = proof.plan_command("python3 -m unittest discover -s tests -t .")
        self.assertIsNone(why)
        self.assertEqual(argv[argv.index("unittest") + 1:argv.index("unittest") + 3], ["discover", "-v"])
        argv, _ = proof.plan_command("python3 -m unittest tests.test_x")
        self.assertEqual(argv[argv.index("unittest") + 1], "-v")
        argv, _ = proof.plan_command("python3 -m unittest discover -v -s tests")
        self.assertEqual(argv.count("-v"), 1)

    def test_the_proving_command_and_guards_are_read_from_phase_2_only(self):
        doc = ("- **Proving test**: `python3 -m unittest wrong`\n\n## Phase 2 — Design\n\n"
               "- **Proving test** (fails pre-change):\n  `python3 -m unittest right`\n"
               "- **Regression guards:** `A.test_a` · `B.test_b`\n\n## Phase 3\n")
        self.assertEqual(proof.proving_command(doc), "python3 -m unittest right")
        self.assertEqual(proof.regression_guards(doc), ["A.test_a", "B.test_b"])


STATS_DOC = """# {key} — {title} (working doc)

- **Ticket:** {key} · `{path}`
- **SCOPE:** {scope}
- **TIER:** {tier}
- **PROTOCOL:** v0.2

## Phase 1 — Analysis ✋ Gate 1

- **Gate 1 status:** cleared

## Phase 2 — Design ✋ Gate 2

- **Gate 2 status:** {gate2}

## Phase 4 — Review ✋ (stop only if not clean)

{verdict}
- **Reviewed at** `abc123` · reviewed files: `{path}`, `src/{name}/b.py`, `tests/test_{name}.py`

## Phase 5 — Finalise ✋ final gate

{phase5}

## Cost ledger

| Phase | Subagent / dispatch | Round | Tokens | Optimizer applied · est./measured saving |
|-------|---------------------|-------|--------|------------------------------------------|
| review | reviewer ({name}) | 1 | 31,516 | none |
| review | challenger ({name}) | 1 | {tokens} | none |

LEDGER TOTAL: 62021 · top cost driver: review/reviewer

## Session status

- **Last updated:** 2026-11-06 by {name}
"""
SENTINELS = ("ACME-4471", "Initech Payroll", "secret/billing/ledger.py", "jdoe")


def stats_doc(**kw):
    fields = dict(key="ACME-4471", title="Initech Payroll export", path="secret/billing/ledger.py",
                  name="jdoe", scope="M", tier="full", gate2="cleared", tokens="30505",
                  verdict="CHALLENGER VERDICT: 7 requirement(s) rebuilt | 5 met | 2 not met | 0 can't tell "
                          "| 0 not-met covered by a recorded exclusion",
                  phase5="- PR draft: `/tmp/pr-ACME-4471.md`")
    fields.update(kw)
    return STATS_DOC.format(**fields)


class TestTicketStats(unittest.TestCase):
    """One aggregate row from a working doc: every field has a fixed shape, so no key, path, name or
    text from the doc can reach the output; a field the doc does not carry is `unknown`, never guessed."""

    def cli(self, text, *args):
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text(text, encoding="utf-8")
            before = doc.read_bytes()
            out = subprocess.run([sys.executable, str(SCRIPTS / "ticket_stats.py"), str(doc), *args],
                                 capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(doc.read_bytes(), before, "the script never writes the doc")
        return out.stdout + out.stderr, out.returncode

    def test_the_fields_are_exactly_the_approved_aggregate_list(self):
        self.assertEqual([k for k, _, _ in ticket_stats.FIELDS],
                         ["lane", "scope", "dispatches", "dispatch_tokens", "unmeasured", "session_tokens",
                          "minutes", "gates", "not_met", "mango", "date"])

    def test_a_full_doc_gives_one_row_read_from_its_records(self):
        out, status = self.cli(stats_doc(), "--real", "1")
        self.assertEqual(out.strip(), "COST: lane=full scope=M/3 dispatches=2 dispatch_tokens=62021 unmeasured=0 "
                                      "session_tokens=unknown minutes=unknown gates=2 not_met=1/2 mango=unknown "
                                      "date=2026-11-06")
        self.assertEqual(status, 0)

    def test_no_key_path_name_or_text_reaches_the_output(self):
        poisoned = stats_doc(scope="ACME-4471", tier="jdoe", gate2="cleared by jdoe",
                             tokens="secret/billing/ledger.py",
                             verdict="CHALLENGER VERDICT: Initech Payroll | 2 not met",
                             phase5="DISCLOSURE\n- ACME-4471 in secret/billing/ledger.py")
        for args in ((), ("--row",)):
            out, status = self.cli(poisoned, *args)
            for word in SENTINELS:
                self.assertNotIn(word, out)
            self.assertEqual(status, 3)
        row, _ = ticket_stats.stats(poisoned)
        for key, _, _ in ticket_stats.FIELDS:
            self.assertRegex(row[key], ticket_stats.PATTERNS[key])

    def test_an_option_value_outside_its_shape_is_refused_and_not_echoed(self):
        for opt in ("--mango", "--minutes", "--lane", "--session-tokens", "--real"):
            out, status = self.cli(stats_doc(), opt, "ACME-4471")
            self.assertEqual(status, 1)
            self.assertNotIn("ACME-4471", out)

    def test_real_not_met_is_a_human_judgement_never_inferred(self):
        out, status = self.cli(stats_doc())
        self.assertIn("not_met=unknown/2", out)
        self.assertEqual(status, 3, "real/raised unread is not a fully read row")
        self.assertEqual(self.cli(stats_doc(), "--real", "3")[1], 1, "real cannot exceed raised")
        zero = stats_doc(verdict="CHALLENGER VERDICT: 7 requirement(s) rebuilt | 7 met | 0 not met | 0 can't tell "
                                 "| 0 not-met covered by a recorded exclusion")
        self.assertIn("not_met=0/0", self.cli(zero)[0])

    def test_lane_comes_from_tier_and_the_phase_5_disclosure(self):
        auto = stats_doc(phase5="DISCLOSURE\n- reviewer: ran · challenger: ran")
        self.assertIn("lane=autorun", self.cli(auto, "--real", "1")[0])
        lite = stats_doc(tier="lite", verdict="")
        out, status = self.cli(lite)
        self.assertIn("lane=quick", out)
        self.assertIn("not_met=n/a", out)
        self.assertEqual(status, 0)
        self.assertIn("lane=autorun", self.cli(stats_doc(), "--lane", "autorun", "--real", "1")[0])

    def test_unmeasured_cells_are_counted_and_an_unreadable_cell_is_not_summed(self):
        out, status = self.cli(stats_doc(tokens="unmeasured (blocking retrieval)"), "--real", "1")
        self.assertIn("dispatches=2 dispatch_tokens=31516 unmeasured=1", out)
        self.assertEqual(status, 0)
        out, status = self.cli(stats_doc(tokens=""), "--real", "1")
        self.assertIn("dispatch_tokens=unknown", out)
        self.assertEqual(status, 3)

    def test_the_template_placeholder_is_not_a_scope(self):
        out, status = self.cli(stats_doc(scope="S | M | L"), "--real", "1")
        self.assertIn("scope=unknown/3", out)
        self.assertEqual(status, 3)

    def test_an_embedded_doc_is_read_below_the_separator_only(self):
        """1.23.1 — under `work_doc_mode: embed` the ticket's own `## ` sections come first; the header
        is below the separator. Both green e2e docs of 1.23.0 printed `lane=unknown scope=unknown`."""
        ticket = ("# PROJ-1 — a ticket\n\n## Description\n\n- **SCOPE:** L\n- **TIER:** lite\n\n"
                  "## Acceptance criteria\n\n- AC-1\n\n---\n\n"
                  f"{ticket_stats.MANGO_SEPARATOR}\n\n")
        out, status = self.cli(ticket + stats_doc(), "--real", "1")
        self.assertIn("lane=full scope=M/3", out)
        self.assertEqual(status, 0)

    def test_the_backticked_header_shape_is_read(self):
        doc = stats_doc().replace("- **SCOPE:** M\n- **TIER:** full\n", "`SCOPE: M` · `TIER: full`\n")
        out, status = self.cli(doc, "--real", "1")
        self.assertIn("lane=full scope=M/3", out)
        self.assertEqual(status, 0)

    def test_the_row_form_matches_the_docs_cost_columns(self):
        out, _ = self.cli(stats_doc(), "--row", "--real", "1", "--mango", "1.23.0", "--minutes", "41")
        cells = [c.strip() for c in out.strip().strip("|").split("|")]
        self.assertEqual(len(cells), len(ticket_stats.FIELDS))
        self.assertEqual(cells[-2:], ["1.23.0", "2026-11-06"])
        self.assertIn("| Lane |", ticket_stats.header_row())

if __name__ == "__main__":
    unittest.main(verbosity=2)
