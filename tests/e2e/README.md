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
| `test_assert_run.py` | Free self-test: a scripted correct run must be green, and each of 13 injected defects must turn its own assertion red. Runs in CI on every push. |

## What the judge asserts

- `origin/main` did not move; exactly one feature branch was pushed and nothing is stranded locally.
- The PR host saw exactly one PR opened and no merge, close or API write.
- The working doc is on the pushed branch with Phase 1–5 in order.
- `Reviewed at <sha>` names a commit on the branch, and only bookkeeping changed after it.
- `check_lines.py check --phase finalise --tree <reviewed sha>` exits `0` (`3`, not checkable, is red).
- The challenger's summary: every requirement met, and at least the ticket's four.
- Every changed project file is named in the approved design and is one the ticket can need.
- The tests pass on the pushed head and **fail** against the base's source.
- `RECONCILE --phase close`, re-run by the harness: every condition holds, floor included.

## Running it

```
python3 tests/e2e/test_assert_run.py      # free, deterministic — after editing anything here
bash tests/e2e/run.sh --local             # costs tokens; commit first (it clones HEAD)
```

CI runs the dispatch weekly and on demand (`.github/workflows/e2e.yml`), never on push, and writes each
run's cost to the job summary. Outside CI, `run.sh` refuses to start without `--local`: the dispatched
session edits files and runs git and Python inside the sandbox without asking.

## What it does not prove

One ticket on one stack, one lane (`autorun`, which routes through the full lifecycle). A green run
says this ticket went through end to end just now. It does not cover `quick`, the epic path, the
frontend track, or a tracker, and it is not a behavioural regression suite.
