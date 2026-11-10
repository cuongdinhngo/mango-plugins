# mango roadmap — phases 0 to 4

> **In 30 seconds.** mango is Level 2 for the full lane today. Five phases take it to measured proof
> first, then honest machine-readable gates, a status card a human reads first, and a PR check that
> verifies consistency and binding — with docs and runtime text that stop growing. A phase ends when its
> exit criteria hold, not on a date. Each phase ships as a release.

## Positioning

*mango is the verification layer for AI-assisted delivery.* Your agent and your host's native
commands (`/plan`, `/code-review`, `/security-review`, `/verify`, `/run`) do the work. mango
independently checks the work against the ticket, holds the gates a human approved, binds every piece
of evidence to a commit, and says plainly what it could not verify. It never replaces native commands;
recording their output as evidence is Planned (phase 3). Verification starts before code: a spec is read by
fresh reviewers and gets a counted verdict (Track S).

## Where we are (1.21.1)

- First-run path fixed: minimal config, tracker local mode, one-screen README, `/mango:challenge`.
- `CHALLENGER VERDICT` is a counted line; evidence is bound to the reviewed commit; `(pre-change)`
  proof blocks are bound to the base and measured in the e2e run.
- On-demand e2e `autorun` judged on artifacts: $3–5.5 and ≤ 10 minutes per run; findings #1 and #5 of
  its first runs fixed in 1.21.0.
- Frontend track: falsifiable rubric, universal-surface coverage, proof tier ladder.
- `autorun` leaves one file, the run contract, and `RECONCILE` says when it can go (1.21.1).

Gaps the phases close:

1. Gate decisions are prose; G3/G4 appear only in prose, and only under autorun.
2. "Fails without the change" is measured in e2e but not in real projects.
3. No one-glance view of a ticket; what was *not* verified lives outside the working doc.
4. Nothing outside the session checks the verdict's consistency and binding.
5. Text keeps growing: plugin README 654 lines, working-doc template 4,278 words, skills 37,158 words;
   one full run loads 34,377 words (`scripts/measure_runtime.py`).
6. The whole 430-line template is copied into every working doc — under `work_doc_mode: embed`, into
   the ticket file itself — epic and frontend sections included when they do not apply.

## Phases

| Phase | Goal | Starts when | Done when |
|---|---|---|---|
| **0** | Publish; stop doc growth; split the plugin README | now | budget ledger in CI; plugin README ≤ 120 lines with no `validate.py` scan narrowed |
| **1** | Measured proof | Phase 0 done | `PROOF` on the latest green e2e doc reports `3 proven`; a doc not declaring `PROTOCOL: v0.2` gets no new axis; the local data script prints aggregate rows only |
| **2** | Honest gate records; status card; profiles; a lighter template | Phase 1 done **and** ≥ 3 real tickets recorded as aggregate rows under the data rules | e2e doc's gate history rebuilt by script, with no `by human` line; card printed into the PR body; v0.2 docs run `standard`; `ticket.md` words lower than 4,278 with the smoke guard green |
| **3** | Enforcement (observe) and a PR check | Phase 2 done **and** the A-00 decision taken | hook reports out-of-phase writes; CI check passes a valid PR and fails a moved branch, labelled "consistency and binding" |
| **4** | Measure and decide | Phase 3 done **and** the real-ticket data threshold met | cost and calibration rows; decisions on protocol v1.0 and the Later list |

Rules: one phase at a time on the main line; independent tasks of the next phase may start early if
they touch nothing the current phase changes. Real-ticket data collection runs from Phase 1 onward,
under the data rules below. Between phases, the docs get one independent review against the code.

### Standing rules (every phase)
- **Runtime cost.** A PR that changes runtime text reports `scripts/measure_runtime.py` before and after.
- **Few generated files.** What mango produces for a ticket goes into its working doc — under `embed`,
  only into the ticket's mango section below the separator — or is printed and never written. A
  separate project file only when the project's config or the ticket asks for one: a generated file
  nobody keeps current goes stale and misleads. A new protocol item is one line in an existing section.
- **Real-project data.** It stays in the project. A local script prints aggregate rows only (counts,
  tokens, minutes, dates, lane, scope — no key, path, name or text); a human reads them before any row
  reaches this public repo. Calibration keeps counts; each `not met` item stays in the project's
  working doc. No real ticket becomes a fixture, renamed or not.

### Phase 0 — Publish, and stop doc growth
- `PROTOCOL.md`, `ROADMAP.md`, `WRITING.md`, templates; README states the position.
- Budget ledger generalising the existing one-screen README check; `--update-budgets` only lowers.
- Plugin README split into how-to, concept and generated reference pages; jargon, one-grammar and
  doc-consistency scans extended to `docs/**`.

### Phase 1 — Measured proof
- `PROTOCOL: v0.2` read from the working doc; a doc without it keeps today's behaviour (`legacy`).
- `PROOF` from the design's proving-test command on base source + head tests, then on head; classified
  by failure kind, with regression guards for refactors; reuses the e2e logic; unittest and pytest
  presets; timeout and opt-out per project.
- The local, aggregate-only data script for real tickets.

### Phase 2 — Honest gate records, status card, a lighter template
- Smoke-guard fixtures for `solve`, `quick`, `breakdown`, `doctor` first (uncovered today).
- `GATE` line with decisions by human, by phase and by autorun; replaces gate rows in the Decision log.
- `autorun`'s run contract moves from `.mango/` into the working doc (since 1.21.1 the Disclosure is
  already in the PR body and the doc, the spec is scratch, and `.mango/` ignores itself); `mango_state.py card` prints the status card from the doc; finalise
  pastes it in the PR. Standalone challenge gets a verdict line of its own.
- Profiles `standard` and `strict`; UI render proofs bound to commit, viewport and artifact hash.
- `ticket.md`: epic and frontend sections added only when the path or track applies; instruction
  comments moved to the skill that fills them; its header agrees with `embed` placement.
- Spike: what Claude Code hooks can observe and block, including the Windows interpreter.

### Phase 3 — Observe, then attest
- Decision first (A-00): whether the working doc and attestation go on the PR branch, and where, for
  both a separate `<KEY>.work.md` and a doc embedded in the ticket file.
- Hook guard in `observe` mode: warnings are printed, not logged to a file; the active-ticket pointer
  (key, doc, time) is runtime state, never committed; stale pointers reported by `doctor`.
- Attestation bundling `check_lines`, stale-guard and `reconcile` results — no committed file unless
  A-00 decides one; deterministic CI check that
  names the profile in its title and reports lite-lane PRs as `neutral — no verifier`.
- Stretch: UI state coverage (`STATES`).

### Phase 4 — Measure and decide
- Challenger calibration and real-ticket cost from the aggregate rows collected since Phase 1
  (≥ 3 tickets per lane, ≥ 20 adjudicated `not met` items, counts only).
- Decide: protocol v1.0 now or after another cycle; which Later items start.

## Track S — the spec track (pre-ticket, Experimental)

Three advisory skills before a ticket: `brainstorm` (idea → brief), `spec` (brief → spec), `spec-review` (fresh
read-only reviewers, counted verdict). No gate; S4 is the one lifecycle link. Runs **alongside Phase 2**; its
grammars shipped in 1.24.0, ahead of Phase 2's `GATE`, as registry additions only. Lines and roles: [`PROTOCOL.md`](./PROTOCOL.md).

| Phase | Goal | Starts when | Done when |
|---|---|---|---|
| **S0** | Spike and contract | now | [host spike](./spikes/spec-track-host.md) answered with sources; Planned entries in `PROTOCOL.md` and here |
| **S1** | `spec-reviewer` agent + `/mango:spec-review` | S0 done | reviews a sample spec and a third-party design doc; a simulated failed lens gives `not run` and an unclean round |
| **S2** | `/mango:spec` | S1 done | a sample brief yields a spec whose `SPEC` line is ready; `DIVERGENCE` catches a planted contradiction |
| **S3** | `/mango:brainstorm` | S1 done (parallel to S2) | no dispatch before the readiness gate; brief carries `BRIEF`; `spec` reads the brief |
| **S4** | One data link to the lifecycle | S2 done | an epic or ticket the user marks `Spec: <path>` gets design evidence at G2, never an auto-closed G2; no spec skill calls a lifecycle skill or creates a ticket |
| **S5** | Measure | S1–S3 released | cost per skill; `not run` rate; rounds to convergence |

## Measures

| Measure | Now | Target at the end of Phase 4 |
|---|---|---|
| Gate events recorded as lines (v0.2 docs) | 0 | 100%, none misattributed |
| Proving tests with measured proof | e2e only | every v0.2 ticket, or disclosed |
| Status card in PR body | no | every finalise |
| PR check without a model | none | documented, scope stated in its name |
| Plugin README | 654 lines | ≤ 120 |
| Working-doc template | 4,278 words | lower, measured by `--update-budgets` |
| Runtime words per full run | 34,377 | reported on every runtime PR; no more than +10% |
| e2e cost per run | $3–5.5 | no more than +20% |
| e2e working doc size | 363 lines | no more than +25% |

## Later — and what must be true first

| Item | Starts when |
|---|---|
| Shrink the skills | the lighter template has shipped and real-ticket rows show where words are spent |
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
