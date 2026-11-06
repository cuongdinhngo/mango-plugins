#!/usr/bin/env bash
# make_sample.sh <dir> — generate the golden e2e sample project in <dir> (must not exist).
#
# TEST DATA, NOT A DEMO. Nothing here is committed as a repo: this script is the only source, and
# the project it writes lives in a temp directory for one run. It is never linked from a README.
#
# What it writes:
#   <dir>/origin.git   a bare repo standing in for the shared remote (file://, no network)
#   <dir>/work         the project: a small stdlib-Python word counter, a unittest suite, a 3-rule
#                      rule book, a local-mode .harness.json, and ticket PROJ-901 (4 ACs, 3 files)
#   <dir>/bin/gh       a PR-host TEST DOUBLE. It records `gh pr create` / `gh pr view` / any merge
#                      attempt to <dir>/pr-log.jsonl and never contacts any server.
set -euo pipefail

DIR="${1:?usage: make_sample.sh <dir>}"
[ ! -e "$DIR" ] || { echo "make_sample: $DIR already exists" >&2; exit 1; }
mkdir -p "$DIR/bin"
DIR="$(cd "$DIR" && pwd)"
W="$DIR/work"
mkdir -p "$W/src/wordcount" "$W/tests" "$W/docs/tickets"

cat >"$W/src/wordcount/__init__.py" <<'EOF'
"""Count words in text."""
EOF

cat >"$W/src/wordcount/core.py" <<'EOF'
"""Word counting."""
import re

_WORD = re.compile(r"[a-z0-9']+")


def count_words(text):
    """Return a dict mapping each lower-cased word in ``text`` to how often it occurs."""
    counts = {}
    for word in _WORD.findall(text.lower()):
        counts[word] = counts.get(word, 0) + 1
    return counts
EOF

cat >"$W/src/wordcount/cli.py" <<'EOF'
"""Command line: wordcount FILE — print `<word> <count>` lines, most frequent first."""
import argparse
import sys

from wordcount.core import count_words


def main(argv=None):
    """Run the command line and return its exit code."""
    parser = argparse.ArgumentParser(prog="wordcount")
    parser.add_argument("file")
    args = parser.parse_args(argv)
    with open(args.file, encoding="utf-8") as handle:
        counts = count_words(handle.read())
    for word, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{word} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
EOF

cat >"$W/tests/__init__.py" <<'EOF'
EOF

cat >"$W/tests/test_core.py" <<'EOF'
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wordcount.core import count_words  # noqa: E402


class CountWordsTest(unittest.TestCase):
    def test_counts_case_insensitively(self):
        self.assertEqual(count_words("The cat and the hat"), {"the": 2, "cat": 1, "and": 1, "hat": 1})

    def test_empty_text(self):
        self.assertEqual(count_words(""), {})


if __name__ == "__main__":
    unittest.main()
EOF

cat >"$W/tests/test_cli.py" <<'EOF'
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wordcount.cli import main  # noqa: E402


class CliTest(unittest.TestCase):
    def test_prints_most_frequent_first(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("b a b")
        out = io.StringIO()
        with redirect_stdout(out):
            code = main([f.name])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().splitlines(), ["b 2", "a 1"])


if __name__ == "__main__":
    unittest.main()
EOF

cat >"$W/README.md" <<'EOF'
# wordcount

Count the words in a text file.

## Usage

```
PYTHONPATH=src python3 -m wordcount.cli FILE
```

Prints one `<word> <count>` line per distinct word, most frequent first.

## Options

None yet.
EOF

cat >"$W/docs/ENGINEERING_RULES.md" <<'EOF'
# Engineering rules

## R1 — Docstrings
Every public function and module has a docstring.

## R2 — Tests ship with behaviour
Every behaviour change ships a unittest under `tests/` that fails without the change.

## R3 — Documented options
Every command-line option is documented in `README.md` under *Options*.
EOF

cat >"$W/docs/LESSONS.md" <<'EOF'
# Lessons
EOF

cat >"$W/docs/tickets/PROJ-901.md" <<'EOF'
# PROJ-901 — Ignore short words in the word count

**Type:** enhancement

## Goal
Let a user leave very short words (such as "a" or "of") out of the counts.

## Constraint
- Standard library only; no new dependency.
- With no new option given, output is exactly what it is today.

## Requirement
- `count_words` takes an optional `min_length` (an integer, default `1`) and counts only words at
  least that many characters long.

## Acceptance Criteria
- **AC-1:** `count_words("a bb ccc", min_length=2)` returns `{"bb": 1, "ccc": 1}`; with no
  `min_length` it returns `{"a": 1, "bb": 1, "ccc": 1}`.
- **AC-2:** `wordcount --min-length N FILE` passes `N` through to `count_words`, so
  `--min-length 3` on a file containing `a bb ccc ccc` prints exactly one line, `ccc 2`.
- **AC-3:** `--min-length` below `1` (for example `0`) exits with code `2` and prints
  `min-length must be at least 1` to stderr, printing nothing to stdout.
- **AC-4:** `README.md` documents `--min-length` under *Options*.
EOF

cat >"$W/.harness.json" <<'EOF'
{
  "rulebook_path": "docs/ENGINEERING_RULES.md",
  "repos": [{ "name": "wordcount", "root": "." }],
  "test_command": "python3 -m unittest discover -s tests -t .",
  "tickets_dir": "docs/tickets",
  "work_dir": "docs/tickets",
  "tracker": { "mode": "local" },
  "ticket_header_schema": {
    "Constraint": "C",
    "Requirement": "R",
    "Goal": "G",
    "Acceptance Criteria": "AC"
  },
  "pr_host": "gh",
  "lessons_path": "docs/LESSONS.md",
  "high_stakes_paths": [],
  "explore_fanout": false,
  "cost_tier": "standard"
}
EOF

cat >"$W/.gitignore" <<'EOF'
__pycache__/
*.pyc
EOF

# The PR-host test double. Reads/writes only $MANGO_E2E_DIR/pr-log.jsonl; no network, ever.
cat >"$DIR/bin/gh" <<'EOF'
#!/usr/bin/env python3
import json, os, sys
log = os.path.join(os.environ["MANGO_E2E_DIR"], "pr-log.jsonl")
args = sys.argv[1:]
def record(kind):
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": kind, "args": args, "cwd": os.getcwd()}) + "\n")
def created():
    try:
        return [json.loads(l) for l in open(log, encoding="utf-8") if '"kind": "create"' in l]
    except OSError:
        return []
if args[:2] == ["pr", "create"]:
    record("create")
    print("https://pr-host.invalid/sample/wordcount/pull/1")
    sys.exit(0)
if args[:2] == ["pr", "view"]:
    record("view")
    if not created():
        print("no pull requests found", file=sys.stderr); sys.exit(1)
    if "--json" in args:
        print(json.dumps({"number": 1, "state": "OPEN", "url": "https://pr-host.invalid/sample/wordcount/pull/1"}))
    else:
        print("state:\tOPEN\nnumber:\t1")
    sys.exit(0)
if args[:2] in (["pr", "merge"], ["pr", "close"]) or args[:1] == ["api"] or args[:1] == ["release"]:
    record("forbidden")
    print("gh test double: refused", file=sys.stderr); sys.exit(1)
if args[:2] == ["auth", "status"] or args[:1] == ["--version"]:
    record("info"); print("gh test double (no network)"); sys.exit(0)
record("other")
print("gh test double: unsupported command", file=sys.stderr); sys.exit(1)
EOF
chmod +x "$DIR/bin/gh"

git init -q --bare "$DIR/origin.git"
git -C "$DIR/origin.git" symbolic-ref HEAD refs/heads/main
(
  cd "$W"
  git init -q -b main
  git config user.name "mango e2e"
  git config user.email "e2e@example.invalid"
  git add -A
  git commit -q -m "wordcount: initial"
  git remote add origin "$DIR/origin.git"
  git push -q -u origin main
  git remote set-head origin main >/dev/null
)
echo "$DIR"
