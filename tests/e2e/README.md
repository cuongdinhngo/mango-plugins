# Golden e2e

One unattended `/mango:autorun` on a generated sample project, judged on the **artifacts** it leaves
behind. It exists to catch what the per-skill smoke guard cannot: one skill's change breaking another
phase downstream.

**This is test data, not a demo.** The sample project is generated per run by `make_sample.sh` and
deleted afterwards; nothing here is a repo to browse, and it is not linked from any README.

| File | What it is |
|---|---|
| `make_sample.sh` | Writes the sample: a stdlib-Python word counter, a unittest suite, a 3-rule rule book, a local-mode `.harness.json`, ticket `PROJ-901` (4 ACs across 3 files), a bare repo as the remote, and a `gh` **test double** that logs PR calls and never contacts a server. |
| `run.sh` | Clones this repo's HEAD, generates the sample, dispatches `/mango:autorun PROJ-901` with the two-action handover authorisation, records cost and wall-clock, then runs the judge. |
| `assert_run.py` | The judge. Reads git state, the working doc, the PR log, and the output of `check_lines.py` and `reconcile.py` **run by the harness** — never the model's account. |
| `test_assert_run.py` | Free self-test: a scripted correct run must be green (separate or embedded working doc), and each injected defect must turn its own assertion red. Runs in CI on every push. |

## What the judge asserts

- `origin/main` did not move; exactly one feature branch was pushed and nothing is stranded locally.
- The PR host saw exactly one PR opened and no merge, close or API write.
- The working doc exists with Phase 1–5 in order — a **local** artifact by mango's contract (never
  committed), as `<KEY>.work.md` or below the separator in the ticket file — and `DISCLOSURE` was left,
  carrying the reviewer's and the challenger's state: in the PR body (the `gh` double records the body
  it was given), the working doc or the final output — never as a file.
- `.mango/` holds only its own `.gitignore` (`*`) and the run contract, and never shows in `git status`.
- `Reviewed at <sha>` names a commit on the branch, and only bookkeeping changed after it.
- `check_lines.py check --phase finalise --tree <reviewed sha> --base <base>` exits `0` (`3`, not
  checkable, is red).
- The challenger's summary: every requirement met, and at least the ticket's four.
- Every changed project file is named in the approved design and is one the ticket can need.
- The tests pass on the pushed head and **fail** against the base's source.
- The RUN CONTRACT validates at close: the generated floor checks are in their one spelling and nothing
  is left `UNBOUND`.
- `RECONCILE --phase post-merge`, re-run by the harness after a **simulated squash merge** (the work
  repo's `main` and `origin/main` refs only; `TREE-COMPARISON` has meaning only once merged): every
  condition holds, floor included, and none is `pending-merge`.

## Running it

```
python3 tests/e2e/test_assert_run.py      # free, deterministic — after editing anything here
bash tests/e2e/run.sh --local             # costs tokens; commit first (it clones HEAD)
```

CI runs the dispatch weekly and on demand (`.github/workflows/e2e.yml`), never on push, and writes each
run's cost to the job summary. Outside CI, `run.sh` refuses to start without `--local`: the dispatched
session edits files and runs git and Python inside the sandbox without asking. The session's `TMPDIR` is the
run's own temp dir. A hard-coded `/tmp` path still escapes it, so `run.sh` lists any new `/tmp` entry
in `.runs/<id>/tmp-new.txt` and warns; it does not judge them, since other processes write `/tmp` too.
The dispatch runs under `auto` mode and an allowlist, never with permissions bypassed: the allowlist passes the listed commands, and the auto-mode classifier judges each other call. `--add-dir`
gives it the run's temp tree, where the plugin clone lives. After the dispatch, `denials.py` lists
every tool call the allowlist refused in `.runs/<id>/denials.txt` and warns. It reads the main
transcript and each subagent's, because `result.json` carries only the main session's denials. A
denied challenger judges by reading only. The list is reported, not judged.

## What it does not prove

One ticket on one stack, one lane (`autorun`, which routes through the full lifecycle). A green run
says this ticket went through end to end just now. It does not cover `quick`, the epic path, the
frontend track, or a tracker, and it is not a behavioural regression suite.
