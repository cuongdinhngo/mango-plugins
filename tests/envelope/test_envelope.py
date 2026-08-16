#!/usr/bin/env python3
"""Test suite for the three envelope scripts — RUN CONTRACT, RECONCILE, BUDGET.

Stdlib `unittest` only, no network, no `claude -p` dispatch: free and deterministic, so it runs on
every edit rather than once a month. Every git test builds its own throwaway repo under `tempfile` and
destroys it; the live checkout is never touched.

Run:  python3 tests/envelope/test_envelope.py
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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
            "merge-strategy": "squash", "challenger": "on", "call-ceiling": "140",
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
