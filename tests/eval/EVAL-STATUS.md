# EVAL-STATUS.md — the current eval cycle

**This file is rewritten in place, never appended to.** It describes one cycle: what is green, what is
red, and what runs next. When a cycle is superseded its per-batch rows move to
[`EVAL-ARCHIVE.md`](./EVAL-ARCHIVE.md) and this file is reset. Findings worth keeping go to
[`EVAL-FINDINGS.md`](./EVAL-FINDINGS.md) instead — never here.

| File | Job |
|---|---|
| `EVAL-STATUS.md` | this file — the current cycle |
| [`EVAL-FINDINGS.md`](./EVAL-FINDINGS.md) | permanent findings and the rules they produced |
| [`EVAL-ARCHIVE.md`](./EVAL-ARCHIVE.md) | superseded cycles, verbatim |
| `.cache/coverage.<runner-fp>.tsv` | **the authority** |

**Do not hand-type status into this file.** Read it from the ledger:

```
bash tests/eval/coverage-report.sh              # the dashboard
bash tests/eval/coverage-report.sh --remaining  # bare list of fixtures with no green row
bash tests/eval/coverage-report.sh --md         # a table to paste below
bash tests/eval/run.sh --verify-suite           # THE GATE — the only thing that proves green
```

`coverage-report.sh` is a dashboard and says so; `--verify-suite` is the gate. Only the gate's output
may be cited as evidence the suite passes.

---

## Cycle 2 — the v1.15.0 ruler

```
Runner fingerprint  : 82580ae5a8272bb39fd5d0f2fce0e17260d01ee4c85e7d4d8df9e7d33334b492
Plugin-tree fp      : 136caac19f92894859da81a6a1439332d6b1aa173474c52ad4a457b5e79aa5f0
Model / CLI         : cli-default / 2.1.258 (Claude Code)
Suite               : 126 jobs · 511 transcript assertions · 71 dispatch-free self-tests
Started             : 2026-09-02, at df45512
```

### Strategy — a discovery pass, then a proof pass

Editing `run.sh` changes `RUNNER_FP`, which wipes every `.green` and starts a fresh ledger. That is the
design working: the fingerprint **is** the ruler. But it means fixing an assertion mid-cycle throws away
every green bought so far, and the loss grows with each batch — fix at batch 2 and lose 30 fixtures, fix
at batch 8 and lose 100. So this cycle is deliberately two passes:

1. **Discovery (running now).** Every batch under runner `82580ae5a827`. Reds are **recorded, not
   fixed**; `run.sh` is not touched, so no green is invalidated and no batch is paid for twice.
2. **Proof.** Apply every fix in **one** edit — one fingerprint change, one wipe — then run the full
   suite once and prove it with `--verify-suite`.

The considered alternative was to split `DISPATCH_FP` (what determines a transcript) from `RUNNER_FP`
(the ledger's ruler), so an assertion-only edit would keep the transcripts and the proof pass would be a
free re-judge. It is ~$50 cheaper and was **rejected on risk**: it means new cache-invalidation
machinery, and the cache is exactly where a false-green would hide. Paying twice for a blunt, obviously
correct ruler is the cheaper mistake.

> **A discovery-pass green is not a green.** Every row in this pass is measured under a ruler the proof
> pass will replace. Nothing here may be cited as evidence the suite passes.

### Coverage

| Metric | Value |
|---|---|
| Runner fingerprint | `82580ae5a827` |
| Plugin-tree fingerprint | `136caac19f92` |
| Fixtures green | 64 of 119 on disk (+0 scenario rows) |
| Rows not green | 1 |
| Stale greens | 0 |
| Distinct rulers among rows | 1 (must be 1) |
| Fixtures with no green row | 55 |

Regenerate with `bash tests/eval/coverage-report.sh --md`.

### Batches run

| Batch | Group | Parts | Jobs | Assertions | Dispatch | Result |
|---|---|---|---|---|---|---|
| 1 ↻ | the unknowns (stop-gate) | 1 | 10 | 127 / 127 | 457s | ✅ green |
| 2 ↻ | `refine` (phase 0) | 3 | 21 | 302 / 303 | 1047s | 🟡 **20/21** — R1 |
| 3 ↻ | `analysis` (Gate 1) | 2 | 13 | 189 / 189 | 693s | ✅ green |
| 4 ↻ | `design` (Gate 2) | 2 | 17 | 205 / 205 | 645s | ✅ green |
| 5 ↻ | `execute` (phase 3) | 1 | 4 | 82 / 82 | 218s | ✅ green |

Assertion counts include the 71 dispatch-free self-tests once per part, so they do not sum to 511.

Notes worth carrying:

- **Batch 4 is the one that mattered.** Its cycle-1 predecessor went red on `API Error: 529` with seven
  fixtures never running and three assertions passing anyway on the harness header. All 17 are now
  proven on real output, no `API Error` in any transcript. See [`EVAL-FINDINGS.md`](./EVAL-FINDINGS.md).
- **Batch 2's fixture assertion count did not move** — 56 before Fix 3, 56 after. Stripping the header
  removed no assertion and broke none, so the checks that could have matched the header were matching
  real output too. Not an outcome to assume; the strip is the kind of change that turns a silent pass
  red.
- **Batch 5's isolation guards were read, not assumed** — it is the batch that branches and commits.
  All three fired their non-vacuity controls, then passed.
- **Selector rebuilt for batch 4** from `FIXTURE_SKILLS` rather than copied: it is the one batch with no
  recorded selector. 18 map to `design`, 1 already green, 17 run — exactly the original's count.
- **Timing:** this cycle runs ≈**1.55×** slower than cycle 1, so any batch whose predecessor took over
  ~380s must be split to stay under the 600s tool ceiling. Splitting is free.

### Register — reds to fix in the single edit

| # | Job | Assertion | Class | Evidence |
|---|-----|-----------|-------|----------|
| R1 | `refine-consistency-is-how` | `refine-consistency: NOT asked as a want-decision` | wording / emphasis window | Behaviour **correct**: H1 filed, resolved "apply to ALL consumers sharing the recipe", cited, flagged for ratification. Transcript says *"It was **not** put to the user as an open want"*. Regex is `not .{0,20}(ask\|want-decision\|open want)`; `open want` lands at offset **25** because the `**` emphasis eats 2. |

Each fix ships with its paired `selftest_assertion` — a `good` transcript carrying the observed wording
and a `bad` one that actually asked the question, so the widened token still misses wrong behaviour.

### Next

**Paused by request after batch 5.** Batches 6–10 remain, under this same fingerprint. What is left,
derived from `FIXTURE_SKILLS` minus the green rows — **55 fixtures + 7 scenarios = 62 jobs**:

| Group | Left | Note |
|---|---|---|
| `finalise` (+`codify`) | 17 | largest remaining; needs 2–3 parts |
| `review` | 11 | has a recorded selector |
| `autorun` | 7 | has a recorded selector |
| `breakdown` | 4 | |
| `budget` | 3 | includes `budget-rtk-wire-guidance`, whose green was wiped by the v1.15.0 FP change |
| `promote` | 3 | |
| `solve` / `solve finalise` | 4 | |
| `quick`, `init doctor`, `codify` | 5 | |
| `refine` | 1 | R1 — stays red by design this pass |
| scenarios | 7 | **foreground, split** — the background attempt was stopped host-side |

Then: one edit fixing the register, then a full pass, then `bash tests/eval/run.sh --verify-suite`.

### Closing entry — fill after the proof pass

```
Suite proven green at SHA :
Date                      :
--verify-suite output     :        ← paste it; it is the only admissible evidence
Total jobs                : 126
Batches needed            :
Reds fixed from register  :
New findings              :        ← and move them to EVAL-FINDINGS.md
```
