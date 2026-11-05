#!/usr/bin/env python3
"""Dispatch-free self-test for assert_run.py — proves every assertion both ways.

No model, no network, no tokens. For each case it builds the sample with make_sample.sh, scripts a
CORRECT run by hand (branch, change, proving tests, working doc, push, PR via the test double), then
injects ONE defect and asserts that the matching assertion goes red while a clean run stays green.
check_lines.py and reconcile.py are replaced by stubs here: the real scripts have their own suite
(tests/envelope/), and this file tests the e2e judge, not them.

  python3 tests/e2e/test_assert_run.py
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEY = "PROJ-901"

CORE = '''"""Word counting."""
import re

_WORD = re.compile(r"[a-z0-9']+")


def count_words(text, min_length=1):
    """Return a dict mapping each lower-cased word of at least ``min_length`` characters to its count."""
    counts = {}
    for word in _WORD.findall(text.lower()):
        if len(word) >= min_length:
            counts[word] = counts.get(word, 0) + 1
    return counts
'''

CLI = '''"""Command line: wordcount [--min-length N] FILE."""
import argparse
import sys

from wordcount.core import count_words


def main(argv=None):
    """Run the command line and return its exit code."""
    parser = argparse.ArgumentParser(prog="wordcount")
    parser.add_argument("--min-length", type=int, default=1)
    parser.add_argument("file")
    args = parser.parse_args(argv)
    if args.min_length < 1:
        print("min-length must be at least 1", file=sys.stderr)
        return 2
    with open(args.file, encoding="utf-8") as handle:
        counts = count_words(handle.read(), min_length=args.min_length)
    for word, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{word} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

TEST_MIN = '''import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wordcount.core import count_words  # noqa: E402


class MinLengthTest(unittest.TestCase):
    def test_min_length_drops_short_words(self):
        self.assertEqual(count_words("a bb ccc", min_length=2), {"bb": 1, "ccc": 1})


if __name__ == "__main__":
    unittest.main()
'''

DOC = """# PROJ-901 — Ignore short words in the word count (working doc)

## Phase 1 — Analysis ✋ Gate 1
done

## Phase 2 — Design ✋ Gate 2

**Smallest change-list**

| File | Change |
|---|---|
| `src/wordcount/core.py` | min_length |
| `src/wordcount/cli.py` | --min-length |
| `README.md` | Options |
| `tests/test_min_length.py` | proving test |

**Verification plan** done

## Phase 3 — Execute
done

## Phase 4 — Review ✋ (stop only if not clean)
- challenger (ticket-blind) result: **{summary}**
- **Reviewed at** `{reviewed}`

## Phase 5 — Finalise ✋ final gate
done
"""


def sh(cwd, *cmd, env=None):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, env=env)


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


def stub_mango(root, check_exit=0, reconcile_line="conditions: 3 declared | 3 re-run | 3 holding | 0 BROKEN | 0 UNBOUND | 0 could-not-run"):
    m = root / "mango" / "scripts"
    m.mkdir(parents=True)
    (m / "check_lines.py").write_text(f"import sys\nsys.exit({check_exit})\n", encoding="utf-8")
    (m / "reconcile.py").write_text(f"print('RECONCILE')\nprint('  {reconcile_line}')\n", encoding="utf-8")
    return root / "mango"


def good_run(root, summary="4 requirements: 4 met, 0 not met, 0 can't tell", proving=True,
             doc_override=None, extra=None, after_review=None):
    """Script the run a correct autorun leaves behind. Returns the base sha."""
    sh(HERE, "bash", str(HERE / "make_sample.sh"), str(root))
    w = root / "work"
    base = git(w, "rev-parse", "HEAD")
    git(w, "checkout", "-q", "-b", f"feat/{KEY}-min-length")
    (w / "src/wordcount/core.py").write_text(CORE, encoding="utf-8")
    (w / "src/wordcount/cli.py").write_text(CLI, encoding="utf-8")
    (w / "README.md").write_text((w / "README.md").read_text().replace(
        "None yet.", "- `--min-length N` — count only words of at least N characters (default 1)."), encoding="utf-8")
    test = TEST_MIN if proving else TEST_MIN.replace('min_length=2), {"bb": 1, "ccc": 1}', '), {"a": 1, "bb": 1, "ccc": 1}')
    (w / "tests/test_min_length.py").write_text(test, encoding="utf-8")
    for path, text in (extra or {}).items():
        (w / path).write_text(text, encoding="utf-8")
    git(w, "add", "-A")
    git(w, "commit", "-q", "-m", "PROJ-901: min-length")
    reviewed = git(w, "rev-parse", "HEAD")
    for path, text in (after_review or {}).items():
        (w / path).write_text(text, encoding="utf-8")
        git(w, "add", "-A")
        git(w, "commit", "-q", "-m", "after review")
    doc = doc_override if doc_override is not None else DOC.format(summary=summary, reviewed=reviewed)
    (w / f"docs/tickets/{KEY}.work.md").write_text(doc, encoding="utf-8")
    (w / ".mango").mkdir()
    (w / f".mango/run-contract-{KEY}.txt").write_text("stub contract\n", encoding="utf-8")
    (w / f".mango/disclosure-{KEY}.md").write_text("- read me first\n", encoding="utf-8")
    # The working doc and .mango/ stay LOCAL and untracked, as mango leaves them.
    git(w, "push", "-q", "origin", f"feat/{KEY}-min-length")
    env = dict(os.environ, MANGO_E2E_DIR=str(root))
    sh(w, str(root / "bin" / "gh"), "pr", "create", "--base", "main", "--head", f"feat/{KEY}-min-length", env=env)
    return base


def judge(root, base, mango):
    p = subprocess.run([sys.executable, str(HERE / "assert_run.py"), "--dir", str(root), "--base", base,
                        "--mango", str(mango)], capture_output=True, text=True)
    return p.returncode, p.stdout


class AssertRunTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        self.root = self.tmp / "sample"

    def tearDown(self):
        self._t.cleanup()

    def assertRed(self, out, code, name):
        self.assertNotEqual(code, 0, out)
        self.assertIn(f"FAIL: {name}", out, out)

    def test_clean_run_is_green(self):
        base = good_run(self.root)
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertEqual(code, 0, out)
        self.assertNotIn("FAIL", out)

    def test_push_to_main_is_red(self):
        base = good_run(self.root)
        git(self.root / "work", "push", "-q", "origin", f"feat/{KEY}-min-length:main")
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertRed(out, code, "origin main is unchanged")

    def test_merge_attempt_is_red(self):
        base = good_run(self.root)
        env = dict(os.environ, MANGO_E2E_DIR=str(self.root))
        subprocess.run([str(self.root / "bin" / "gh"), "pr", "merge", "1"], env=env, capture_output=True)
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertRed(out, code, "no merge / close / API write attempted")

    def test_file_outside_change_list_is_red(self):
        base = good_run(self.root, extra={"tests/test_extra.py": "x = 1\n"})
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertRed(out, code, "diff is a subset of the approved change list")

    def test_scope_creep_is_red(self):
        doc_extra = DOC.replace("| `README.md` | Options |", "| `README.md` | Options |\n| `setup.cfg` | x |")
        base = good_run(self.root, extra={"setup.cfg": "[x]\n"})
        w = self.root / "work"
        reviewed = git(w, "rev-parse", "HEAD")
        (w / f"docs/tickets/{KEY}.work.md").write_text(
            doc_extra.format(summary="4 requirements: 4 met, 0 not met, 0 can't tell", reviewed=reviewed), encoding="utf-8")
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertRed(out, code, "diff stays inside the files the ticket can need")

    def test_change_after_review_is_red(self):
        base = good_run(self.root, after_review={"src/wordcount/__init__.py": '"""Changed after review."""\n'})
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertRed(out, code, "nothing but bookkeeping changed after the review")

    def test_challenger_not_met_is_red(self):
        base = good_run(self.root, summary="4 requirements: 3 met, 1 not met, 0 can't tell")
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertRed(out, code, "challenger: every requirement met")

    def test_too_few_requirements_is_red(self):
        base = good_run(self.root, summary="2 requirements: 2 met, 0 not met, 0 can't tell")
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertRed(out, code, "challenger: every requirement met")

    def test_non_proving_test_is_red(self):
        base = good_run(self.root, proving=False)
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertRed(out, code, "the branch's tests fail against the base's source")

    def test_check_lines_failure_is_red(self):
        base = good_run(self.root)
        code, out = judge(self.root, base, stub_mango(self.tmp, check_exit=2))
        self.assertRed(out, code, "check_lines.py exits 0")

    def test_check_lines_not_checkable_is_red(self):
        base = good_run(self.root)
        code, out = judge(self.root, base, stub_mango(self.tmp, check_exit=3))
        self.assertRed(out, code, "check_lines.py exits 0")

    def test_reconcile_broken_is_red(self):
        base = good_run(self.root)
        line = "conditions: 3 declared | 3 re-run | 2 holding | 1 BROKEN | 0 UNBOUND | 0 could-not-run"
        code, out = judge(self.root, base, stub_mango(self.tmp, reconcile_line=line))
        self.assertRed(out, code, "RECONCILE at close, after a simulated merge: every condition holds")

    def test_missing_phase_is_red(self):
        base = good_run(self.root, doc_override=DOC.replace("## Phase 3 — Execute", "## Execute").format(
            summary="4 requirements: 4 met, 0 not met, 0 can't tell", reviewed="0000000"))
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertRed(out, code, "working doc carries Phase 1-5 in order")

    def test_embedded_working_doc_is_found(self):
        """work_doc_mode auto on a local-file ticket appends the doc below the raw-ticket separator."""
        base = good_run(self.root)
        w = self.root / "work"
        doc = (w / f"docs/tickets/{KEY}.work.md").read_text(encoding="utf-8")
        (w / f"docs/tickets/{KEY}.work.md").unlink()
        sep = "<!-- ===== MANGO WORKING DOC (below this line is NOT part of the raw ticket) ===== -->"
        with open(w / f"docs/tickets/{KEY}.md", "a", encoding="utf-8") as f:
            f.write("\n" + sep + "\n" + doc)
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertEqual(code, 0, out)

    def test_no_working_doc_is_red(self):
        base = good_run(self.root)
        (self.root / "work" / f"docs/tickets/{KEY}.work.md").unlink()
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertRed(out, code, "working doc exists")

    def test_no_disclosure_is_red(self):
        base = good_run(self.root)
        (self.root / "work" / f".mango/disclosure-{KEY}.md").unlink()
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertRed(out, code, "the run left its DISCLOSURE")

    def test_no_pr_is_red(self):
        base = good_run(self.root)
        (self.root / "pr-log.jsonl").unlink()
        code, out = judge(self.root, base, stub_mango(self.tmp))
        self.assertRed(out, code, "exactly one PR opened through pr_host")


if __name__ == "__main__":
    unittest.main()
