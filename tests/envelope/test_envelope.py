#!/usr/bin/env python3
"""Test suite for the plugin's harness scripts — RUN CONTRACT, RECONCILE, BUDGET, CHECK-LINES.

The first three are the autorun envelope; CHECK-LINES (v1.13.0) verdicts the counted lines in a
working doc. All four live in `plugins/mango/scripts/` and are gated by this one command.

Stdlib `unittest` only, no network, no `claude -p` dispatch: free and deterministic, so it runs on
every edit rather than once a month. Every git test builds its own throwaway repo under `tempfile` and
destroys it; the live checkout is never touched.

Run:  python3 tests/envelope/test_envelope.py
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "plugins" / "mango" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import budget  # noqa: E402
import reconcile  # noqa: E402
import run_contract as rc  # noqa: E402


# --------------------------------------------------------------------------- helpers

FLOOR_BLOCK = """  CONDITION PR-EXISTS
    statement: the PR exists and its state is readable
    origin: floor
    derived-by: {pr_derive}
    value: {pr_value}
    check: {pr_check}
    force-broken: {pr_broken}
    force-holding: {pr_holding}
  END CONDITION
  CONDITION TREE-COMPARISON
    statement: no commit landed on the branch beyond what the PR carries (tree comparison)
    origin: floor
    derived-by: {tree_derive}
    value: {tree_value}
    check: {tree_check}
    force-broken: {tree_broken}
    force-holding: {tree_holding}
  END CONDITION
  CONDITION LOCAL-HEAD-PUSHED
    statement: nothing is stranded on this machine: local branch head == the remote's
    origin: floor
    derived-by: git rev-parse HEAD
    value: abc123 (exit 0)
    check: {head_check}
    force-broken: git commit --allow-empty -m stranded
    force-holding: git push origin feat/PROJ-1-x
  END CONDITION
"""

DEFAULTS = dict(
    pr_derive="gh pr view 1 --json state",
    pr_value="OPEN (exit 0)",
    pr_check="gh pr view 1 --json state",
    pr_broken="gh pr close 1",
    pr_holding="gh pr reopen 1",
    tree_derive="git rev-parse main",
    tree_value="deadbee (exit 0)",
    tree_check="git diff --quiet main feat/PROJ-1-x -- .",
    tree_broken="git commit --allow-empty -m drift",
    tree_holding="git checkout main -- .",
    head_check=(
        "git rev-parse --verify feat/PROJ-1-x >/dev/null 2>&1 && "
        "git rev-parse --verify origin/feat/PROJ-1-x >/dev/null 2>&1 && "
        'test "$(git rev-parse feat/PROJ-1-x)" = "$(git rev-parse origin/feat/PROJ-1-x)"'
    ),
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
        "  base: main\n"
        "  branch: feat/PROJ-1-x\n"
        "  remote: origin\n"
        "  merge-strategy: squash-or-rebase (recent first-parent topology)\n"
        f"  challenger: {overrides.get('challenger', 'on')}\n"
        f"  handover-authorisation: {overrides.get('handover_authorisation', 'approved 22:58 — push feat/PROJ-1-x, open the PR; nothing else')}\n"
        f"  call-ceiling: {overrides.get('call_ceiling', '140')}\n"
        "  per-call-estimate: 3100\n"
        "  ceiling-source: 4 ledger row(s), 567 call(s) total\n"
        "  token-budget: unmeasured (host surfaces no usage)\n"
    )
    body = FLOOR_BLOCK.format(**fields) if floor else ""
    return header + body + extra_conditions + "END RUN CONTRACT\n"


def simple_condition(cid, check, broken, holding, origin="agent"):
    return (
        f"  CONDITION {cid}\n"
        f"    statement: {cid} holds\n"
        f"    origin: {origin}\n"
        f"    derived-by: {rc.AGENT_CLAIM}\n"
        f"    value: stated by the agent\n"
        f"    check: {check}\n"
        f"    force-broken: {broken}\n"
        f"    force-holding: {holding}\n"
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

    def test_T1_missing_force_broken_does_not_parse(self):
        """T1 — a condition missing `force-broken` does not parse, so the run does not start."""
        broken = contract().replace("    force-broken: gh pr close 1\n", "")
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(broken, "t0")
        self.assertTrue(any("force-broken" in r for r in ctx.exception.reasons))

    def test_T1_missing_force_holding_does_not_parse(self):
        """T1 — the other half: a predicate never shown to HOLD on a clean run is a false-red waiting."""
        broken = contract().replace("    force-holding: gh pr reopen 1\n", "")
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(broken, "t0")
        self.assertTrue(any("force-holding" in r for r in ctx.exception.reasons))

    def test_T2_unbound_survives_past_gate2_is_refused(self):
        """T2 — an UNBOUND placeholder surviving past Gate 2: re-validation refuses."""
        text = contract(
            extra_conditions=simple_condition(
                "PROVING-TEST", "UNBOUND ${TEST_CMD}", "true", "true"
            )
        )
        rc.validate(text, "t0")  # allowed at t0 — the value cannot exist before the change
        with self.assertRaises(rc.ContractError) as ctx:
            rc.validate(text, "gate2")
        self.assertTrue(any("UNBOUND" in r for r in ctx.exception.reasons))

    def test_T2_bind_resolves_then_parses(self):
        text = contract(
            extra_conditions=simple_condition("PROVING-TEST", "UNBOUND ${TEST_CMD}", "true", "true")
        )
        bound = rc.bind(text, {"TEST_CMD": "pytest -k proving"}, "gate2")
        self.assertIn("check: pytest -k proving", bound)

    def test_T2_bind_refuses_a_partial_binding(self):
        text = contract(
            extra_conditions=simple_condition("PROVING-TEST", "UNBOUND ${TEST_CMD}", "true", "true")
            + simple_condition("SECOND", "UNBOUND ${OTHER}", "true", "true")
        )
        with self.assertRaises(rc.ContractError):
            rc.bind(text, {"TEST_CMD": "pytest"}, "gate2")

    def test_unbound_without_a_placeholder_does_not_parse(self):
        text = contract(extra_conditions=simple_condition("X", "UNBOUND", "true", "true"))
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
        text = contract(floor=False, extra_conditions=simple_condition("X", "true", "false", "true"))
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
            extra_conditions=simple_condition("SUBJECT", check, "true", "true"),
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
            extra_conditions=simple_condition("LATER", "UNBOUND ${X}", "true", "true")
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
            extra_conditions=simple_condition("PROVING-TEST", "UNBOUND ${TEST_CMD}", "true", "true"),
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
        self.assertIn("3 could-not-run", joined)
        self.assertIn("COULD NOT RUN", joined)

    def test_T9_could_not_run_at_t0_strikes_the_run(self):
        """A precondition that cannot be verified is not a green light: at t0 a COULD-NOT-RUN strikes
        the run exactly as a false HOLDING does."""
        text = contract(pr_check="true", tree_check="true", head_check="true")
        with mock.patch.object(rc.shutil, "which", return_value=None):
            lines, status = reconcile.reconcile(text, "t0", repo=self.tmp)
        self.assertEqual(status, 2)
        self.assertIn("COULD-NOT-RUN at t0", "\n".join(lines))

    def test_the_forced_case_control_cannot_run_without_the_shell(self):
        cond = {"id": "FLAG", "fields": {
            "check": "true", "force-holding": "true", "force-broken": "false"}}
        with mock.patch.object(rc.shutil, "which", return_value=None):
            shown_broken, shown_holding, notes = reconcile.prove_one(cond, repo=self.tmp)
        self.assertFalse(shown_broken)
        self.assertFalse(shown_holding)
        self.assertTrue(any("COULD-NOT-RUN" in n for n in notes))


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
        self.assertIn("3 BROKEN", joined)
        self.assertIn("READ THIS FIRST", joined)


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


# --------------------------------------------------------------- forced-case positive control


class TestForcedCasePositiveControl(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.flag = os.path.join(self.tmp, "flag")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_a_forceable_condition_counts_on_both_axes(self):
        cond = {
            "id": "FLAG",
            "fields": {
                "check": f"test -f {self.flag}",
                "force-holding": f"touch {self.flag}",
                "force-broken": f"rm -f {self.flag}",
            },
        }
        shown_broken, shown_holding, notes = reconcile.prove_one(cond, repo=self.tmp)
        self.assertTrue(shown_broken)
        self.assertTrue(shown_holding)
        self.assertEqual(notes, [])

    def test_a_mutation_that_silently_did_not_apply_is_NOT_counted(self):
        """The positive control: one forced-BROKEN mutation once passed because it never applied."""
        cond = {
            "id": "FLAG",
            "fields": {
                "check": f"test -f {self.flag}",
                "force-holding": f"touch {self.flag}",
                "force-broken": "true",  # a no-op standing in for a mutation that did not land
            },
        }
        shown_broken, shown_holding, notes = reconcile.prove_one(cond, repo=self.tmp)
        self.assertFalse(shown_broken)
        self.assertTrue(shown_holding)
        self.assertTrue(any("FORCE-UNPROVEN" in n for n in notes))

    def test_a_condition_that_never_holds_cannot_prove_its_broken_case(self):
        cond = {
            "id": "FLAG",
            "fields": {"check": "false", "force-holding": "true", "force-broken": "true"},
        }
        shown_broken, shown_holding, notes = reconcile.prove_one(cond, repo=self.tmp)
        self.assertFalse(shown_broken)
        self.assertFalse(shown_holding)
        self.assertTrue(any("FORCE-UNPROVEN" in n for n in notes))

    def test_proven_counts_reach_the_counted_line(self):
        text = contract(
            pr_check="false",
            tree_check="git diff --quiet main nope -- .",
            head_check=HEAD_MAIN_CHECK,
            extra_conditions=simple_condition(
                "FLAG", f"test -f {self.flag}", f"rm -f {self.flag}", f"touch {self.flag}"
            ),
        )
        lines, _ = reconcile.reconcile(text, "close", repo=self.tmp, prove=True)
        self.assertIn("1 shown BROKEN when forced | 1 shown HOLDING on a clean run", "\n".join(lines))


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
        first = seed.splitlines()[1]
        self.assertIn("CHALLENGER: OFF", first)
        self.assertIn("not evidence of independence", first + seed)

    def test_T11_the_default_records_the_challenger_as_having_run(self):
        header, conditions = rc.parse(contract())
        self.assertIn("CHALLENGER: ON", rc.disclosure_seed(header, conditions).splitlines()[1])

    def test_unchecked_agent_claims_are_carried_into_the_disclosure(self):
        text = contract(extra_conditions=simple_condition("CLAIMED", "true", "false", "true"))
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
        spec = {
            "key": "PROJ-1", "started": "t", "plugin-version": "1.11.0", "plugin-path": "/p",
            "repo": self.tmp, "base": "main", "branch": "feat/PROJ-1-x", "remote": "origin",
            "merge-strategy": "squash", "challenger": "on",
            "handover-authorisation": "approved 22:58 — push feat/PROJ-1-x, open the PR; nothing else",
            "call-ceiling": "140",
            "per-call-estimate": "3100", "ceiling-source": "ledger", "token-budget": "unmeasured",
            "conditions": [
                {"id": "PR-EXISTS", "statement": "the PR exists and its state is readable",
                 "origin": "floor", "derived-by": "echo OPEN", "value": "", "check": "gh pr view 1",
                 "force-broken": "gh pr close 1", "force-holding": "gh pr reopen 1"},
                {"id": "TREE-COMPARISON",
                 "statement": "no commit landed on the branch beyond what the PR carries",
                 "origin": "floor", "derived-by": "echo deadbee", "value": "",
                 "check": "git diff --quiet main feat/PROJ-1-x -- .",
                 "force-broken": "git commit --allow-empty -m x", "force-holding": "true"},
                {"id": "LOCAL-HEAD-PUSHED",
                 "statement": "nothing is stranded on this machine: local head == the remote's",
                 "origin": "floor", "derived-by": rc.AGENT_CLAIM, "value": "the agent says so",
                 "check": HEAD_MAIN_CHECK,
                 "force-broken": "git commit --allow-empty -m y", "force-holding": "git push"},
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
    "EXCLUSIONS": "EXCLUSIONS: 0 recorded | 0 with a checkable expiry | 0 recurring | "
                  "0 with an overdue predecessor",
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
            capture_output=True, text=True)
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
                              capture_output=True, text=True)
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
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        for token in cl.GRAMMARS:
            self.assertIn(token, proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
