#!/usr/bin/env python3
"""PROOF — the harness runs the proving test twice; the agent reads the verdict.

Stdlib only, no network. It MUTATES NOTHING in the checkout: both runs happen in throwaway worktrees
that are removed on every path out, a failure included. Nothing here is narrated: every count comes
from a test result this script observed.

  PROOF: <n> proving test(s) | <p> proven | <r> regression-guard | <z> green@base |
         <e> env-fault@base | <g> not green@head | <f> flaky | <c> could-not-run

The input is the design's **Proving test** command (the first backticked command after the
`**Proving test**` label in the working doc's `## Phase 2` section) and, optionally, the tests the
design declared as regression guards (`**Regression guards:**` followed by backticked test ids, or
`none`). A test not declared a regression guard is declared as proof.

  Run 1 — base source + head tests: a worktree at <base>, with every test file the branch added or
          changed checked out from <head> (`verification.proof.test_paths`). This is the setup execute
          already uses for its `(pre-change)` block.
  Run 2 — head: a worktree at <head>. A test that does not pass is run once more there; passing on
          that re-run makes it `flaky`.

CLASSIFIED BY THE KIND OF FAILURE, NEVER BY HOW MANY TESTS FAIL. At base every new proving test is
expected to fail:

  base fails or errors, or cannot import a module or symbol THE DIFF ADDS; head passes -> proven
  base cannot import something present in BOTH trees, or a connection error            -> env-fault@base
  base passes, the design declared a regression guard                                  -> regression-guard
  base passes, the design declared proof                                               -> green@base
  head does not pass (failed, errored, skipped, expected failure)                      -> not green@head
  head fails, then passes on one re-run                                                -> flaky
  the test cannot be run or its result cannot be read                                  -> could-not-run

PRESETS. `unittest` only: FAIL and ERROR are both red; results are read from `-v` output, which this
script adds. Any other runner is `could-not-run` until a recorded sample proves how to read it. A
command that cannot run at all counts as ONE test, could-not-run — a PROOF line with no test is never
written, because `0 proving test(s)` would read clean.

CONFIG (`.harness.json` → `verification.proof`, every key optional):
  enabled     default true. false prints `PROOF waived (verification.proof.enabled: false)` and no
              PROOF line; the waiver is disclosed, never a pass.
  timeout_s   default 300, per run. A run that times out leaves its tests could-not-run.
  test_paths  globs naming test files (default: tests/*, test/*, */tests/*, test_*.py, */test_*.py,
              *_test.py).

Usage
  proof.py run <workdoc> --base <sha> [--head <sha>] [--repo <dir>] [--config <.harness.json>]
               [--command <proving-test command>]

Exit codes: 0 clean (every test proven or a regression guard) · 2 `z > 0` or `g > 0` · 3 nothing
blocks but something was not verified (`e`, `f`, `c` > 0, or waived) · 1 usage.
"""

import fnmatch
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

DEFAULT_TEST_PATHS = ("tests/*", "test/*", "*/tests/*", "test_*.py", "*/test_*.py", "*_test.py")
DEFAULT_TIMEOUT = 300
WAIVED = "PROOF waived (verification.proof.enabled: false)"
SEPARATOR = "MANGO WORKING DOC (below this line is NOT part of the raw ticket)"
FIELDS = ("proven", "regression-guard", "green@base", "env-fault@base", "not green@head", "flaky",
          "could-not-run")

# A test's verbose header. What follows it — a docstring, the test's own printed output, then
# `... <status>` — may span lines, so a status is read from the test's own segment, not the header line.
HEADER_RE = re.compile(r"^(?P<name>\w+) \((?P<where>[\w.]+)\)(?=[^\n]*(?:\.\.\.|$))", re.M)
PASS_STATUS_RE = re.compile(r"(?:^|\.\.\. |\s)(ok|skipped|expected failure|unexpected success)\b[^\n]*$",
                            re.M)
SUMMARY_RE = re.compile(r"^={20,}$|^-{20,}\nRan ", re.M)
BLOCK_RE = re.compile(r"^(?P<kind>ERROR|FAIL): (?P<name>\S+) \((?P<where>[\w.]+)\)[^\n]*\n(?P<body>.*?)"
                      r"(?=^={20,}|^-{20,}\nRan |\Z)", re.M | re.S)
EXC_RE = re.compile(r"^(?P<exc>[A-Za-z_][\w.]*(?:Error|Exception|Failure|Exit))\b:?[ \t]?(?P<msg>.*)$",
                    re.M)
FAILED_LOAD = ("unittest.loader._FailedTest", "unittest.loader.ModuleImportFailure")
CONNECTION = ("ConnectionError", "ConnectionRefusedError", "ConnectionResetError",
              "ConnectionAbortedError", "gaierror")


# --------------------------------------------------------------------------- the working doc


def doc_body(text):
    idx = text.find(SEPARATOR)
    return text if idx == -1 else text[idx:]


def phase2(text):
    m = re.search(r"^## Phase 2\b.*?(?=^## |\Z)", doc_body(text), re.M | re.S)
    return m.group(0) if m else ""


def proving_command(text):
    """The first backticked span after the `**Proving test**` label in Phase 2, or None."""
    m = re.search(r"\*\*Proving test\*\*[^`]*`([^`]+)`", phase2(text))
    return m.group(1).strip() if m else None


def regression_guards(text):
    m = re.search(r"\*\*Regression guards?:?\*\*:?([^\n]*(?:\n(?![ \t]*[-*]|\n)[^\n]*)*)", phase2(text))
    return re.findall(r"`([^`]+)`", m.group(1)) if m else []


# --------------------------------------------------------------------------- config and git


def read_config(path):
    out = {"enabled": True, "timeout_s": DEFAULT_TIMEOUT, "test_paths": list(DEFAULT_TEST_PATHS)}
    if not path or not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        proof = ((json.load(fh).get("verification") or {}).get("proof") or {})
    if proof.get("enabled") is False:
        out["enabled"] = False
    if isinstance(proof.get("timeout_s"), (int, float)) and proof["timeout_s"] > 0:
        out["timeout_s"] = proof["timeout_s"]
    if isinstance(proof.get("test_paths"), list) and proof["test_paths"]:
        out["test_paths"] = [str(p) for p in proof["test_paths"]]
    return out


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout


def git_ok(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True).returncode == 0


def is_test_path(path, globs):
    return any(fnmatch.fnmatch(path, g) for g in globs)


# --------------------------------------------------------------------------- the runner preset


def plan_command(command):
    """(argv, None) for a command the unittest preset can run, or (None, reason)."""
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return None, f"the command does not parse ({exc})"
    if any(t in ("&&", "||", ";", "|", ">", "<") for t in argv):
        return None, "a compound shell command; name one test command"
    if "pytest" in argv or any(t.endswith("pytest") for t in argv):
        return None, "no verified preset for pytest yet (unittest only)"
    if "unittest" not in argv:
        return None, "no preset for this runner (unittest only)"
    i = argv.index("unittest")
    # `discover` must be unittest's first argument, so `-v` goes after it, never before it.
    if i + 1 < len(argv) and argv[i + 1] == "discover":
        i += 1
    if "-v" not in argv[i + 1:] and "--verbose" not in argv[i + 1:]:
        argv = argv[: i + 1] + ["-v"] + argv[i + 1:]
    return argv, None


def run_once(argv, cwd, timeout):
    """(exit status, combined output), or (None, reason) when the run itself failed."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return None, f"timed out after {timeout}s"
    except OSError as exc:
        return None, f"could not start: {exc}"
    return p.returncode, p.stdout + p.stderr


def parse_unittest(output):
    """{test id: (status, exception, message)} and {failed-to-load module name: (exception, message)}."""
    errors, failures = {}, {}
    for b in BLOCK_RE.finditer(output):
        excs = EXC_RE.findall(b.group("body"))
        key = (b.group("name"), b.group("where"))
        errors[key] = excs[-1] if excs else ("", "")
        failures[key] = b.group("kind")
    cut = SUMMARY_RE.search(output)
    progress = output[: cut.start()] if cut else output
    heads = list(HEADER_RE.finditer(progress))
    results, failed_modules = {}, {}
    for i, m in enumerate(heads):
        name, where = m.group("name"), m.group("where")
        segment = progress[m.end(): heads[i + 1].start() if i + 1 < len(heads) else len(progress)]
        if (name, where) in failures:
            st = failures[(name, where)]
        else:
            found = PASS_STATUS_RE.findall(segment)
            if not found:
                continue                     # no readable status: the test stays unread, never a pass
            st = found[-1]
        exc, msg = errors.get((name, where), ("", ""))
        if where.startswith(FAILED_LOAD):
            failed_modules[name] = (exc, msg)
            continue
        tid = where if where.endswith("." + name) else f"{where}.{name}"
        results[tid] = (st, exc, msg)
    return results, failed_modules


def lookup(tid, results, failed_modules):
    if tid in results:
        return results[tid]
    parts = tid.split(".")
    for mod, (exc, msg) in failed_modules.items():
        if mod in parts[:-1]:
            return ("ERROR", exc, msg)
    return None


# --------------------------------------------------------------------------- import failures


def import_target(exc, msg):
    """('symbol', name, module) or ('module', dotted, None) for an import failure, else None."""
    if exc.split(".")[-1] not in ("ImportError", "ModuleNotFoundError"):
        return None
    m = re.search(r"cannot import name '([\w.]+)' from '([\w.]+)'", msg)
    if m:
        return ("symbol", m.group(1), m.group(2))
    m = re.search(r"No module named '([\w.]+)'", msg)
    if m:
        return ("module", m.group(1), None)
    return None


def module_paths(dotted):
    base = dotted.replace(".", "/")
    return [f"{pre}{base}{suf}" for pre in ("", "src/") for suf in (".py", "/__init__.py")]


def exists_at(repo, sha, path):
    return git_ok(repo, "cat-file", "-e", f"{sha}:{path}")


def defines(repo, sha, path, name):
    try:
        text = git(repo, "show", f"{sha}:{path}")
    except RuntimeError:
        return False
    return re.search(rf"^\s*(?:async\s+)?(?:def|class)\s+{re.escape(name)}\b|^{re.escape(name)}\s*(?::[^=\n]*)?=",
                     text, re.M) is not None


def import_verdict(repo, base, head, target):
    """'diff-adds' when the diff adds what failed to import, else 'both-trees' or 'unknown'."""
    kind, name, module = target
    if kind == "module":
        paths = module_paths(name)
        at_base = any(exists_at(repo, base, p) for p in paths)
        at_head = any(exists_at(repo, head, p) for p in paths)
        if at_head and not at_base:
            return "diff-adds"
        return "both-trees" if at_base and at_head else "unknown"
    paths = module_paths(module)
    at_base = any(defines(repo, base, p, name) for p in paths)
    at_head = any(defines(repo, head, p, name) for p in paths)
    if at_head and not at_base:
        return "diff-adds"
    return "both-trees" if at_base and at_head else "unknown"


# --------------------------------------------------------------------------- the two runs


def worktree(repo, sha, root, label):
    path = os.path.join(root, label)
    git(repo, "worktree", "add", "--quiet", "--detach", path, sha)
    return path


def matches_guard(tid, guards):
    return any(tid == g or tid.endswith("." + g) for g in guards)


def classify(tid, base_r, head_r, rerun_r, guards, repo, base, head):
    """(field, reason) for one test."""
    if head_r is None:
        return "could-not-run", "no result at head"
    if head_r[0] != "ok":
        if rerun_r and rerun_r[0] == "ok":
            return "flaky", f"head {head_r[0]}, then ok on one re-run"
        return "not green@head", f"head {head_r[0]} {head_r[1]}: {head_r[2]}".rstrip(": ")
    if base_r is None:
        return "could-not-run", "no result at base"
    status, exc, msg = base_r
    if status == "ok":
        if matches_guard(tid, guards):
            return "regression-guard", "passes at base, declared a regression guard"
        return "green@base", "passes at base, declared proof — it proves nothing"
    if status in ("FAIL", "unexpected success", "expected failure"):
        return "proven", f"base {status} {exc}: {msg}".rstrip(": ")
    if status == "skipped":
        return "could-not-run", "skipped at base"
    target = import_target(exc, msg)
    if target:
        verdict = import_verdict(repo, base, head, target)
        if verdict == "diff-adds":
            return "proven", f"base cannot import {target[1]}, which the diff adds"
        return "env-fault@base", f"base cannot import {target[1]} ({verdict})"
    if exc.split(".")[-1] in CONNECTION:
        return "env-fault@base", f"base {exc}: {msg}"
    return "proven", f"base ERROR {exc}: {msg}".rstrip(": ")


def prove(repo, base, head, command, guards, cfg):
    """(counts, details, notes). Worktrees are removed on every path out."""
    argv, reason = plan_command(command) if command else (None, "no proving-test command in Phase 2")
    if argv is None:
        return {"could-not-run": 1}, [f"    (the command): could-not-run — {reason}"], []
    root = tempfile.mkdtemp(prefix="mango-proof-")
    notes = []
    try:
        changed = [p for p in git(repo, "diff", "--name-only", "--diff-filter=AMR", base, head).splitlines()
                   if p and is_test_path(p, cfg["test_paths"])]
        base_tree = worktree(repo, base, root, "base")
        if changed:
            git(base_tree, "checkout", head, "--", *changed)
        head_tree = worktree(repo, head, root, "head")
        notes.append(f"  base     : {base[:12]} + {len(changed)} test file(s) from head")
        base_rc, base_out = run_once(argv, base_tree, cfg["timeout_s"])
        head_rc, head_out = run_once(argv, head_tree, cfg["timeout_s"])
        notes.append(f"  runs     : base exit {base_rc if base_rc is not None else base_out} · "
                     f"head {head[:12]} exit {head_rc if head_rc is not None else head_out}")
        if head_rc is None:
            return {"could-not-run": 1}, [f"    (the command): could-not-run — head run {head_out}"], notes
        head_res, head_failed = parse_unittest(head_out)
        base_res, base_failed = parse_unittest(base_out) if base_rc is not None else ({}, {})
        tests = list(head_res) + [f"{m} (module import)" for m in head_failed]
        if not tests:
            return {"could-not-run": 1}, ["    (the command): could-not-run — no test result could be "
                                          "read at head"], notes
        rerun_res = {}
        if any(head_res.get(t, ("ERROR",))[0] != "ok" for t in tests):
            rerun_rc, rerun_out = run_once(argv, head_tree, cfg["timeout_s"])
            if rerun_rc is not None:
                rerun_res, _ = parse_unittest(rerun_out)
        counts, details = {}, []
        for tid in tests:
            if tid.endswith(" (module import)"):
                exc, msg = head_failed[tid.split(" ")[0]]
                field, why = "not green@head", f"the test module does not import at head: {exc}: {msg}"
            else:
                field, why = classify(tid, lookup(tid, base_res, base_failed), head_res.get(tid),
                                      rerun_res.get(tid), guards, repo, base, head)
            if field == "proven" and matches_guard(tid, guards):
                why += " (declared a regression guard, yet it fails at base)"
            counts[field] = counts.get(field, 0) + 1
            details.append(f"    {tid}: {field} — {why[:200]}")
        return counts, details, notes
    except RuntimeError as exc:
        return {"could-not-run": 1}, [f"    (the command): could-not-run — {exc}"], notes
    finally:
        for label in ("head", "base"):
            path = os.path.join(root, label)
            if os.path.exists(path):
                subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", path],
                               capture_output=True)
        subprocess.run(["git", "-C", repo, "worktree", "prune"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)


def proof_line(counts):
    n = sum(counts.get(f, 0) for f in FIELDS)
    return (f"PROOF: {n} proving test(s) | {counts.get('proven', 0)} proven | "
            f"{counts.get('regression-guard', 0)} regression-guard | {counts.get('green@base', 0)} green@base | "
            f"{counts.get('env-fault@base', 0)} env-fault@base | {counts.get('not green@head', 0)} not green@head | "
            f"{counts.get('flaky', 0)} flaky | {counts.get('could-not-run', 0)} could-not-run")


def status_of(counts):
    if counts.get("green@base") or counts.get("not green@head"):
        return 2
    if counts.get("env-fault@base") or counts.get("flaky") or counts.get("could-not-run"):
        return 3
    return 0


# --------------------------------------------------------------------------- cli


def main(argv):
    if len(argv) < 3 or argv[1] != "run":
        print(__doc__)
        return 1
    doc, args = argv[2], argv[3:]

    def opt(name, default=None):
        i = args.index(name) if name in args else -1
        return args[i + 1] if 0 <= i < len(args) - 1 else default

    base = opt("--base")
    if not base:
        print("proof: run <workdoc> --base <sha> [--head <sha>] [--repo <dir>] [--config <file>] "
              "[--command <cmd>]")
        return 1
    repo = opt("--repo", ".")
    try:
        cfg = read_config(opt("--config", os.path.join(repo, ".harness.json")))
    except (OSError, ValueError) as exc:
        print(f"proof: cannot read the config ({exc})")
        return 1
    if not cfg["enabled"]:
        print(WAIVED)
        return 3
    try:
        with open(doc, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"proof: cannot read the working doc ({exc})")
        return 1
    try:
        base = git(repo, "rev-parse", "--verify", f"{base}^{{commit}}").strip()
        head = git(repo, "rev-parse", "--verify", f"{opt('--head', 'HEAD')}^{{commit}}").strip()
    except RuntimeError as exc:
        print(f"proof: {exc}")
        return 1
    command = opt("--command") or proving_command(text)
    counts, details, notes = prove(repo, base, head, command, regression_guards(text), cfg)
    print(proof_line(counts))
    print(f"  command  : {command or '(none found)'}")
    print("\n".join(notes + details))
    return status_of(counts)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
