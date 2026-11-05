#!/usr/bin/env python3
"""assert_run.py — judge one golden e2e run on its ARTIFACTS, never on the transcript's wording.

  python3 tests/e2e/assert_run.py --dir <sample dir> --base <initial main sha> --mango <plugin dir>

<sample dir> is what make_sample.sh wrote and `autorun` then worked in. Every assertion reads git
state, the working doc, the PR-host test double's log, or the output of a mango script the HARNESS
runs here — never the model's account of what it did. Prints one PASS/FAIL line per assertion and
exits 1 if any failed. Stdlib only.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KEY = "PROJ-901"
WORK_DOC = f"docs/tickets/{KEY}.work.md"
TICKET = f"docs/tickets/{KEY}.md"
SEPARATOR = "<!-- ===== MANGO WORKING DOC (below this line is NOT part of the raw ticket) ===== -->"
DISCLOSURE = f".mango/disclosure-{KEY}.*"  # autorun names no extension
CONTRACT = f".mango/run-contract-{KEY}.txt"
TEST_CMD = ["python3", "-m", "unittest", "discover", "-s", "tests", "-t", "."]
# Paths a run may touch that are bookkeeping, not the change: the working doc and ticket folder, the
# lessons file, and mango's run directory.
BOOKKEEPING = (re.compile(r"^docs/tickets/"), re.compile(r"^docs/LESSONS\.md$"), re.compile(r"^\.mango/"))
# The files the ticket can legitimately need. A change outside this set is scope creep, whatever the
# working doc's own change list says.
ALLOWED = (re.compile(r"^src/wordcount/(core|cli)\.py$"), re.compile(r"^README\.md$"),
           re.compile(r"^tests/[^/]+\.py$"))
MIN_REQUIREMENTS = 4  # the ticket carries four ACs

results = []


def check(ok, name, detail=""):
    results.append(bool(ok))
    print(f"  {'PASS' if ok else 'FAIL'}: {name}" + (f" — {detail}" if detail and not ok else ""))
    return bool(ok)


def git(repo, *args, ok_codes=(0,)):
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if p.returncode not in ok_codes:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout.strip(), p.returncode


def is_bookkeeping(path):
    return any(r.search(path) for r in BOOKKEEPING)


def changed(repo, a, b):
    out, _ = git(repo, "diff", "--name-only", f"{a}..{b}")
    return [l for l in out.splitlines() if l]


def plain(text):
    """Drop markdown emphasis so an assertion matches the decision, not the styling."""
    return re.sub(r"[*`]", "", text)  # never `_`: it is part of file paths


def section(doc, start, stop=r"^## "):
    m = re.search(start, doc, re.M)
    if not m:
        return ""
    rest = doc[m.end():]
    n = re.search(stop, rest, re.M)
    return rest[: n.start()] if n else rest


def working_doc(work):
    separate = work / WORK_DOC
    if separate.exists():
        return separate.read_text(encoding="utf-8")
    ticket = work / TICKET
    text = ticket.read_text(encoding="utf-8") if ticket.exists() else ""
    return text.split(SEPARATOR, 1)[1] if SEPARATOR in text else ""


def run_tests(tree):
    return subprocess.run(TEST_CMD, cwd=tree, capture_output=True, text=True).returncode


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--mango", required=True)
    ap.add_argument("--result", help="the dispatch's JSON result (its final output), if kept")
    a = ap.parse_args(argv)
    root = Path(a.dir).resolve()
    work, origin, mango = root / "work", root / "origin.git", Path(a.mango).resolve()

    print("== golden e2e: artifacts ==")

    # 1. The shared default branch did not move: no merge, no direct push.
    main_sha, _ = git(origin, "rev-parse", "refs/heads/main")
    check(main_sha == a.base, "origin main is unchanged (no merge, no push to the default branch)",
          f"{main_sha} != {a.base}")

    # 2. Exactly one feature branch was pushed.
    heads, _ = git(origin, "for-each-ref", "--format=%(refname:short)", "refs/heads/")
    branches = [h for h in heads.splitlines() if h and h != "main"]
    if not check(len(branches) == 1, "exactly one feature branch pushed to origin", f"found {branches}"):
        return finish()
    branch = branches[0]
    head, _ = git(origin, "rev-parse", f"refs/heads/{branch}")
    local, rc = git(work, "rev-parse", "--verify", "-q", f"refs/heads/{branch}", ok_codes=(0, 1))
    check(rc == 0 and local == head, "local branch head equals the pushed head (nothing stranded)",
          f"local {local or 'missing'} vs pushed {head}")

    # 3. The PR host saw one PR opened and no merge, close or other write.
    log = root / "pr-log.jsonl"
    events = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    creates = [e for e in events if e["kind"] == "create"]
    forbidden = [e for e in events if e["kind"] == "forbidden"]
    check(len(creates) == 1, "exactly one PR opened through pr_host", f"{len(creates)} create call(s)")
    check(not forbidden, "no merge / close / API write attempted on the PR host",
          "; ".join(" ".join(e["args"]) for e in forbidden))

    # 4. The working doc exists with every phase in order. It is a LOCAL artifact by mango's contract
    #    (never committed; DISCLOSURE says so), placed per work_doc_mode: a separate <KEY>.work.md, or
    #    embedded in the local ticket file below the raw-ticket separator.
    doc = working_doc(work)
    if not check(doc, f"working doc exists ({WORK_DOC}, or {TICKET} below the separator)"):
        return finish()
    # autorun names no file for DISCLOSURE: it is in the run's output, a file, or both. Either way it
    # must carry the seed's first line — reviewer and challenger state, recorded separately.
    places = []
    for disclosure in sorted(work.glob(DISCLOSURE)):
        places.append(disclosure.read_text(encoding="utf-8"))
    if a.result and Path(a.result).exists():
        try:
            places.append(str(json.loads(Path(a.result).read_text(encoding="utf-8")).get("result", "")))
        except ValueError:
            pass
    check(any("DISCLOSURE" in t.upper() and re.search(r"REVIEWER\s*:", t) and re.search(r"CHALLENGER\s*:", t)
              for t in places),
          "the run left a DISCLOSURE carrying the reviewer and challenger state (file or final output)")
    positions = [doc.find(f"## Phase {n}") for n in range(1, 6)]
    check(all(p >= 0 for p in positions) and positions == sorted(positions),
          "working doc carries Phase 1-5 in order", f"positions {positions}")

    # 5. The stale-review guard: Reviewed at <sha> names a commit on the branch, and anything after it
    #    is bookkeeping only.
    m = re.findall(r"Reviewed at\s+([0-9a-f]{7,40})", plain(doc))
    reviewed = None
    if check(m, "working doc records `Reviewed at <sha>`"):
        reviewed, rc = git(work, "rev-parse", "--verify", "-q", f"{m[-1]}^{{commit}}", ok_codes=(0, 1))
        _, anc = git(work, "merge-base", "--is-ancestor", reviewed or "0" * 40, head, ok_codes=(0, 1, 128))
        if check(rc == 0 and anc == 0, "the reviewed commit is on the pushed branch", f"{m[-1]}"):
            late = [p for p in changed(work, reviewed, head) if not is_bookkeeping(p)]
            check(not late, "nothing but bookkeeping changed after the review", f"{late}")

    # 6. The checker, run HERE by the harness, passes the doc through finalise with the base the branch
    #    was cut from (the only SHA a `(pre-change)` record may name) and the tree under review. That
    #    tree is the reviewed commit or the pushed head: finalise passes `git rev-parse HEAD`, and the
    #    stale-review guard exempts bookkeeping commits after review, so a run may stamp either. Step 5
    #    asserted only bookkeeping lies between them; the doc must pass in full against ONE of them.
    trees = [t for t in dict.fromkeys([reviewed, head]) if t]
    with tempfile.TemporaryDirectory() as t:
        doc_file = Path(t) / "doc.md"
        doc_file.write_text(doc, encoding="utf-8")
        for tree in trees:
            p = subprocess.run([sys.executable, str(mango / "scripts" / "check_lines.py"), "check",
                                str(doc_file), "--phase", "finalise", "--base", a.base, "--tree", tree],
                               capture_output=True, text=True)
            if p.returncode == 0:
                break
    check(p.returncode == 0, "check_lines.py exits 0 on the final working doc",
          f"exit {p.returncode}: " + " | ".join(l.strip() for l in p.stdout.splitlines() if "FAIL" in l or "MISSING" in l or "BROKEN" in l)[:400])

    # 7. The challenger met every requirement it rebuilt, and rebuilt at least the four ACs.
    # The challenger's brief fixes the four numbers, not the words around them.
    # The challenger's brief names three counts and no grammar, so only the counts are matched: the
    # total is optional and any short non-digit separator (`,` `|` `/` `;` `·`) is accepted.
    s = re.findall(r"(?:(\d+)\s+requirements?\b[^\n\d]{0,40}?)?(\d+)\s+met\b[^\n\d]{0,6}?(\d+)\s+not met\b"
                   r"[^\n\d]{0,6}?(\d+)\s+can'?t tell", plain(section(doc, r"^## Phase 4")), re.I)
    if check(s, "Phase 4 carries the challenger's summary line"):
        total, met, not_met, cant = s[-1]
        met, not_met, cant = int(met), int(not_met), int(cant)
        total = int(total) if total else met + not_met + cant
        check(not_met == 0 and cant == 0 and met == total and total >= MIN_REQUIREMENTS,
              f"challenger: every requirement met (>= {MIN_REQUIREMENTS})",
              f"{total} requirements: {met} met, {not_met} not met, {cant} can't tell")

    # 8. Scope: every non-bookkeeping file changed is in the approved change list AND in the set the
    #    ticket can need.
    files = [p for p in changed(work, a.base, head) if not is_bookkeeping(p)]
    check(files, "the branch changes at least one project file", "empty diff")
    approved = set(re.findall(r"[\w./-]+\.(?:py|md|cfg|toml|txt|json)", section(plain(doc), r"^## Phase 2")))
    outside = [f for f in files if f not in approved and not any(f.endswith("/" + x) or x.endswith("/" + f) for x in approved)]
    check(approved and not outside, "diff is a subset of the approved change list",
          f"approved {sorted(approved)}; outside {outside}")
    creep = [f for f in files if not any(r.search(f) for r in ALLOWED)]
    check(not creep, "diff stays inside the files the ticket can need", f"{creep}")

    # 9. The proving tests: green on the branch, and red against the base's source.
    with tempfile.TemporaryDirectory() as t:
        tree = Path(t) / "tree"
        git(work, "worktree", "add", "-q", "--detach", str(tree), head)
        try:
            check(run_tests(tree) == 0, "the test suite passes on the pushed head")
            git(tree, "checkout", a.base, "--", "src", "README.md")
            check(run_tests(tree) != 0, "the branch's tests fail against the base's source (they prove the change)")
        finally:
            git(work, "worktree", "remove", "--force", str(tree))

    # 10. RECONCILE, re-run by the harness at close, after a SIMULATED squash merge: every condition
    #     holds. TREE-COMPARISON (`git diff --quiet <base> <branch>`) can only hold once the PR is
    #     merged, so the harness moves `main` and `origin/main` IN THE WORK REPO to a squash of the branch — refs only, the
    #     checkout and origin are untouched, and origin main was asserted unchanged above.
    contract = work / CONTRACT
    if check(contract.exists(), f"the RUN CONTRACT exists at {CONTRACT}"):
        tree_sha, _ = git(work, "rev-parse", f"{head}^{{tree}}")
        squash, _ = git(work, "commit-tree", tree_sha, "-p", "refs/heads/main", "-m", "e2e: simulated squash merge")
        git(work, "update-ref", "refs/heads/main", squash)
        git(work, "update-ref", "refs/remotes/origin/main", squash)  # a contract may compare either ref
        p = subprocess.run([sys.executable, str(mango / "scripts" / "reconcile.py"), "run", str(contract),
                            "--phase", "close", "--repo", str(work)], capture_output=True, text=True,
                           # the same PR-host test double the dispatched session had
                           env=dict(os.environ, PATH=f"{root / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}",
                                    MANGO_E2E_DIR=str(root)))
        c = re.search(r"conditions:\s*(\d+) declared \| (\d+) re-run \| (\d+) holding \| (\d+) BROKEN \| "
                      r"(\d+) UNBOUND \| (\d+) could-not-run", p.stdout)
        if check(c, "RECONCILE prints its conditions line", p.stdout[-300:] + p.stderr[-300:]):
            d, _, h, q, u, cnr = map(int, c.groups())
            check(q == 0 and u == 0 and cnr == 0 and h == d and d >= 3,
                  "RECONCILE at close, after a simulated merge: every condition holds (floor included)",
                  f"{d} declared, {h} holding, {q} BROKEN, {u} UNBOUND, {cnr} could-not-run")

    return finish()


def finish():
    n, ok = len(results), sum(results)
    print(f"E2E: {ok}/{n} assertions pass")
    return 0 if n and ok == n else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
