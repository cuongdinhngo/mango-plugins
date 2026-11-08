# mango roadmap — phases 0 to 4

> **In 30 seconds.** mango is Level 2 for the full lane today. Five phases take it to honest
> machine-readable gates, measured proof, a status card a human reads first, and a PR check that
> verifies consistency and binding — with docs that stop growing. A phase ends when its exit criteria
> hold, not on a date; the next starts right away. Each phase ships as a release.

## Positioning

*mango is the verification layer for AI-assisted delivery.* Your agent and your host's native
commands (`/plan`, `/code-review`, `/security-review`, `/verify`, `/run`) do the work. mango
independently checks the work against the ticket, holds the gates a human approved, binds every piece
of evidence to a commit, and says plainly what it could not verify. It records native commands as
evidence; it never replaces them.

## Where we are (1.21.0)

- First-run path fixed: minimal config, tracker local mode, one-screen README, `/mango:challenge`.
- `CHALLENGER VERDICT` is a counted line; evidence is bound to the reviewed commit; `(pre-change)`
  proof blocks are bound to the base and measured in the e2e run.
- Weekly e2e `autorun` judged on artifacts: $3–5.5 and ≤ 10 minutes per run; findings #1 and #5 of
  its first runs fixed in 1.21.0.
- Frontend track: falsifiable rubric, universal-surface coverage, proof tier ladder.

Gaps the phases close:

1. Gate decisions are prose; G3/G4 appear only in prose, and only under autorun.
2. "Fails without the change" is measured in e2e but not in real projects.
3. No one-glance view of a ticket; what was *not* verified lives outside the working doc.
4. Nothing outside the session checks the verdict's consistency and binding.
5. Text keeps growing: plugin README 654 lines, working-doc template 4,278 words, skills 37,158 words.

## Phases

| Phase | Goal | Starts when | Done when |
|---|---|---|---|
| **0** | Publish; stop doc growth; split the plugin README | now | budget ledger in CI; plugin README ≤ 120 lines with no `validate.py` scan narrowed |
| **1** | Honest gate records; status card | Phase 0 done | e2e doc's gate history rebuilt by script, with no `by human` line; card printed into the PR body |
| **2** | Measured proof; profiles; render binding | Phase 1 done (`GATE` and `PROTOCOL: v0.2` exist) | `PROOF` on the latest green e2e doc reports `3 proven`; v0.2 docs run `standard` |
| **3** | Enforcement (observe) and a PR check | Phase 2 done **and** the A-00 decision taken | hook reports out-of-phase writes; CI check passes a valid PR and fails a moved branch, labelled "consistency and binding" |
| **4** | Measure and decide | Phase 3 done **and** the real-ticket data threshold met | cost and calibration rows; decisions on protocol v1.0 and the Later list |

Rules: one phase at a time on the main line; independent tasks of the next phase may start early if
they touch nothing the current phase changes. Real-ticket data collection runs from Phase 1 onward.
Between phases, the docs get one independent review against the code.

### Phase 0 — Publish, and stop doc growth
- `PROTOCOL.md`, `ROADMAP.md`, `WRITING.md`, templates; README states the position.
- Budget ledger generalising the existing one-screen README check; `--update-budgets` only lowers.
- Plugin README split into how-to, concept and generated reference pages; jargon, one-grammar and
  doc-consistency scans extended to `docs/**`.

### Phase 1 — Honest gate records
- Smoke-guard fixtures for `solve`, `quick`, `breakdown`, `doctor` first (uncovered today).
- `GATE` line with decisions by human, by phase and by autorun; replaces gate rows in the Decision log.
- The Disclosure gets a fixed path; `mango_state.py card` prints the status card from the doc and the
  Disclosure; finalise pastes it in the PR.
- Standalone challenge emits a verdict line under its own name, so it can never satisfy review.

### Phase 2 — Measured proof
- `PROOF` from the design's proving-test command on base source + head tests, then on head; classified
  by failure kind, with regression guards for refactors; reuses the e2e logic; unittest and pytest
  presets; timeout and opt-out per project.
- Profiles `standard` and `strict` for v0.2 docs; `legacy` for everything older.
- UI render proofs bound to commit, viewport and artifact hash.
- Spike: what Claude Code hooks can observe and block, including the Windows interpreter.

### Phase 3 — Observe, then attest
- Hook guard in `observe` mode; the active-ticket pointer records key, doc and time; stale pointers
  reported by `doctor`.
- Attestation bundling `check_lines`, stale-guard and `reconcile` results; deterministic CI check that
  names the profile in its title and reports lite-lane PRs as `neutral — no verifier`.
- Stretch: UI state coverage (`STATES`).

### Phase 4 — Measure and decide
- Challenger calibration and real-ticket cost from the data collected since Phase 1
  (≥ 3 tickets per lane, ≥ 20 adjudicated `not met` items).
- Decide: protocol v1.0 now or after another cycle; which Later items start.

## Measures

| Measure | Now | Target at the end of Phase 4 |
|---|---|---|
| Gate events recorded as lines (v0.2 docs) | 0 | 100%, none misattributed |
| Proving tests with measured proof | e2e only | every v0.2 ticket, or disclosed |
| Status card in PR body | no | every finalise |
| PR check without a model | none | documented, scope stated in its name |
| Plugin README | 654 lines | ≤ 120 |
| Working-doc template | 4,278 words | does not grow (ratchet); reduction is a Later item |
| e2e cost per run | $3–5.5 | no more than +20% |
| e2e working doc size | 363 lines | no more than +25% |

## Later — and what must be true first

| Item | Starts when |
|---|---|
| Shrink the working-doc template and skills | the status card ships, and a script defines "words loaded per full run" |
| Hook guard `enforce` mode | `observe` shows a low false-alarm rate on real tickets |
| FE ↔ BE contract check | a fullstack pilot project with a contract command |
| Visual diff (same-run baselines) | `sitemap` gives all reachable surfaces and the app runs on two trees in CI |
| Mutation on changed lines | `PROOF` data shows proven tests that still miss bugs |
| CI challenge run on PRs | a team asks for it and accepts the cost |
| Reviewer vs native review experiment | ≥ 5 merged tickets with known defects available |
| Preset beyond Python (vitest, go) | a second e2e sample in that language |
| Acceptance tests written blind from the ticket | calibration shows producer-written tests miss requirements |
| Org rule packs, architecture gate, risk-based lanes, signing, policy-as-code | protocol v1.0 and ≥ 3 external teams on the PR check |

## Not in this roadmap

New phases or gates in the lifecycle; approval receipts (a shell can forge them); a bundled test runner
or image comparer; a tracker; features that duplicate host commands.
