# The mango protocol — v0.1 (Draft, revision 3)

> **In 30 seconds.** Gates closed by a named actor, claims as counted lines a script checks, a
> verifier independent of the producer, and *not checked* never read as *passed*. Your agent and host
> commands do the work; this is how mango shows it matches the ticket — and says what it could not show.
> **Status:** formalises `1.21.0`; **Planned** parts name their roadmap phase in [`ROADMAP.md`](./ROADMAP.md).
> MUST / SHOULD / MAY per RFC 2119.

## 1. Trust properties

| # | Property | Rule |
|---|---|---|
| P1 | **Independence** | The actor judging requirement coverage did not produce the change and sees nothing of how it was produced. |
| P2 | **Verifiability** | Every claim a gate depends on is a counted line or a result a script computes. |
| P3 | **Binding** | Every piece of evidence names the commit it ran on; evidence from another commit does not count. |
| P4 | **Human authority** | Only a human closes a gate **that waits for one**; silence is never approval; nothing merges without a human. |
| P5 | **Visible gaps** | Missing, waived, flaky or unrunnable evidence is reported as *not verified*, never as *passed*. |

These hold **per lane** (§7): the lite lane has no verifier, and a run with a seat switched off is
labelled. A verdict never claims a property its lane does not provide.

**Threat model.** The protocol defends against a cooperative but fallible agent: one that
over-claims, skips a requirement, proves the wrong thing, reuses a stale run or drifts outside its
approved change. It does **not** defend against an agent deliberately editing files in its own
workspace — shell access makes every v0.x artifact tamper-evident at best, never tamper-proof. The
`check_lines` verdict carries a fingerprint of the document it judged, so a quote of it against a
changed document is detectable; other verdict lines do not carry one yet.

## 2. Roles

| Role | Who | Constraint |
|---|---|---|
| **Approver** | a human | — |
| **Producer** | main agent loop, `implementer` | never closes a gate that waits for a human; never edits the raw ticket |
| **Verifier** | `challenger` | no Write/Edit tool (read-only commands only); never reads the working doc, design, PR body or the producer's summary |
| **Reviewer** | `reviewer`, `reviewer-max` | no Write/Edit tool |
| **Harness** | stdlib scripts | reports; never rewrites what it judges |
| **Unattended runner** | `autorun` | closes a gate only on its artifact condition; never merges |

## 3. Gates

| Gate | Closes | Attended | Unattended |
|---|---|---|---|
| **G0** Clarification | analysis → design, when `CLARIFICATION: j > 0` | Approver | never — the run stops |
| **G1** Analysis | analysis → design | Approver | artifact condition |
| **G2** Design | design → execute | Approver | artifact condition |
| **G3** Execute | execute → review | passes by phase (no stop) | artifact condition |
| **G4** Review | review → finalise | passes by phase when clean; Approver only when not clean | the clean definition of review (§6) — `skills/autorun` still says "reviewer LGTM" until phase 1 aligns it |
| **GF** Final | each outward action: PR, tracker, lesson | Approver, per action | run ends at the PR |
| **GC** Combined | lite lane: intake → execute | Approver | no autorun condition in 1.21.0 — `quick` stops for approval, so the run waits |
| **GB** Breakdown | epic → child tickets | Approver | — |

Unattended conditions for G0–G3 are canonical in `skills/autorun/SKILL.md`; a condition naming an
artifact that is not produced makes the gate non-closing.

**Gate record — Planned (phase 1).** Each gate decision is one counted line, written on its own line
(never inside a table — the line contains `|`):

```
GATE: <id> | <decision> | by <actor> | tree <sha|none> | at <UTC>[ | action <pr|tracker|lesson>][ | why <text>]
```

| Decision | Actor | Gates |
|---|---|---|
| `approved`, `sent-back` | `human` | any gate that waits for a human |
| `passed` | `phase` | G3; G4 when clean |
| `auto-closed`, `stopped` | `autorun` | G0–G4 under autorun (`stopped` also for any non-closing gate) |

Other pairings are contradictions. Only a gate's **final** decision is recorded (an unattended attempt
that does not close writes nothing). State is **derived** from these lines; no hand-edited copy exists.
`why` holds the reason, so `GATE` lines replace the Decision log's gate rows. A doc not declaring
`PROTOCOL: v0.2` gets **no gate axis** — neither failure nor pass. **Not checkable means not closed:**
under autorun, checker exit 3 on a v0.2 doc leaves the gate open and goes to the Disclosure.

## 4. Artifacts

| Artifact | Rule | Status |
|---|---|---|
| **Raw ticket** | Never edited by the producer; the verifier reads only the text above the working-doc separator. | Implemented |
| **Working doc** | One per ticket; the single source of truth; declares `TIER`, `TRACK`, and (Planned) `PROTOCOL`, `PROFILE`. Whether it is committed to the PR branch is **undecided** — see §4.1. | Implemented |
| **Counted line** | One canonical grammar per line; no line without a parser. Registry: `check_lines.py grammars`. | Implemented |
| **Evidence record** | Every output a gate relies on carries `Ran at <sha>`; `(pre-change)` blocks are bound to the base. Render proofs add `viewport <w>x<h>` and `artifact sha256:<…> <path>`. | Implemented; render binding Planned (phase 2) |
| **Review marker** | `Reviewed at <sha>` + reviewed files; finalise refuses a PR if HEAD moved beyond them. | Implemented |
| **Run contract, Reconcile, Disclosure** | Unattended-run conditions, their checked states, and what was not verified. The Disclosure gets a fixed path, `.mango/disclosure-<KEY>.txt` (today the skill names none). | Implemented; fixed path Planned (phase 1) |
| **Status card** | ≤ 12 rows **printed** by the harness from the working doc **and the Disclosure**; never written into the doc; pasted at the top of the PR body. A row without data prints `not-checkable`. Attended vs unattended is read from the presence of `.mango/run-contract-<KEY>.txt`. | Planned (phase 1) |
| **Attestation** | Per-ticket JSON bundling the results of `check_lines`, the stale-review guard and `reconcile`, with digests. | Planned (phase 3) |

### 4.1 What a pull request can prove — Planned (phase 3)

A check outside the session verifies **consistency** (`check_lines`) and **binding** (head vs
`Reviewed at`, diff ⊆ change list, evidence SHAs). It cannot re-derive **judgement** (challenger and
reviewer verdicts): those are *carried*, source named. Each attestation field is labelled `recomputed`
or `carried`; a CI check says "consistency and binding verified; judgement carried", never
"requirements verified". It needs the working doc and attestation on the PR branch at a path exempt
from the stale guard — decided first.

## 5. Verification

Verification asks what review cannot: **does the evidence actually prove the requirement?** It adds
no phase and no gate: the plan is approved at G2, its results decide G4.

### 5.1 Profiles — Planned (phase 2)

| Profile | Applies to | Proof | UI state coverage |
|---|---|---|---|
| **legacy** | working docs that do not declare `PROTOCOL: v0.2` | today's behaviour (`(pre-change)` block bound to base) | no |
| **standard** | default for v0.2 docs | ✅ | ✅ (frontend, fullstack) |
| **strict** | chosen per project or ticket; forced when the diff touches `high_stakes_paths` | ✅, `p = n` | ✅ |

A check skipped by the profile is `waived` and shows in the status card, Disclosure and attestation.
A CI check names the profile in its title and MAY require a minimum. No new line is required of a doc
that has not opted into v0.2: upgrading never turns a passing doc into a failing one.

mango bundles no test runner; with no project command a check is `could-not-run` — disclosed.

### 5.2 Verification lines — Planned

Each line has an **identity** (the numbers must add up, or the line is written wrong) and a **clean
condition** (what G4 needs).

| Line | Grammar | Identity | Clean when |
|---|---|---|---|
| `VERIFY` | `profile <p> \| <r> required \| <d> done \| <x> failed \| <w> waived \| <c> could-not-run \| <f> flaky` | `r = d+x+w+c+f` | `x = 0` |
| `PROOF` | `<n> proving test(s) \| <p> proven \| <r> regression-guard \| <z> green@base \| <e> env-fault@base \| <g> not green@head \| <f> flaky \| <c> could-not-run` | `n = p+r+z+e+g+f+c` | `z = 0`, `g = 0`; at strict also `e = 0`, `c = 0` |
| `STATES` | `<n> required \| <p> proven \| <m> missing \| <x> excluded` | `n = p+m+x` | `m = 0` |

**Proof.** The harness runs the design's **proving-test command** twice: on the base source with the
head's tests (the setup execute already uses for its `(pre-change)` block), then on the reviewed
commit. Classification is **by the kind of failure, never by how many tests fail** — at base every
new proving test is expected to fail:

| First run (base source + head tests) | Second run (head) | Result |
|---|---|---|
| fails or errors, including an import of a module or symbol **the diff adds** | passes | `proven` |
| collection error, connection error, or an import of something present in **both** trees | — | `env-fault@base` |
| passes, and the design declared the test a **regression guard** (approved at G2) | passes | `regression-guard` — expected, never blocks |
| passes, and the design declared it as proof | — | `green@base` — proves nothing, blocks |
| — | fails | `not green@head` |
| fails once, passes on one re-run | — | `flaky` |

Refactor, docs and config tickets use regression guards. *Open:* in compiled languages a new API breaks
the build at base; until a second e2e sample proves a rule, such tests are `env-fault@base`, disclosed.

### 5.3 UI verification

The frontend track already has falsifiable rubric items scored against `DESIGN.md`, surface coverage
for universal requirements (`SURFACES`, `N = M + X`), and the proof tier ladder (automated C1–C8 →
recorded render → exclusion).

| Gap | Check | Status |
|---|---|---|
| Only the happy path built | **State coverage** — required states per component kind come from `DESIGN.md`; each affected surface proves or excludes each one | Planned (phase 3, stretch) |
| Render proof reused from another commit | **Render binding** (§4) | Planned (phase 2) |
| FE and BE disagree at the seam | **Contract** — the project's contract command for each endpoint the diff touches | Later |
| A change leaked to other screens | **Visual diff** — base and head rendered in one run, no committed baselines | Later |
| Console errors, failed requests | **Runtime health** — taken from the host's `/run`, `/verify` or browser tools as evidence, never re-implemented | Planned (phase 3) |

## 6. Verdicts

| Script | Exit codes | Read results from |
|---|---|---|
| `check_lines.py` | 0 clean · 2 failure · 3 nothing failed but something not checkable · 1 usage | exit code + axes |
| `reconcile.py` | 0 ok · 2 contract unparseable, or at t0 a condition already holding or could-not-run · 1 usage | **the `RECONCILE` line** — `BROKEN` and `could-not-run` are axes, and exit stays 0 at close/post-merge |
| `run_contract.py` | 0 · 2 · 1 | exit code |
| `budget.py` | always 0 (advisory) | its output |
| new scripts | follow `check_lines.py` | exit code + axes |

A harness reports and never rewrites. A **clean review** (G4) requires: no Critical reviewer finding;
`CHALLENGER VERDICT` with `m + g = n`; no unresolved layer-match `❌`; no design-conformance drift;
every matrix row `k = N` or excluded; for universal frontend requirements `N = M + X`; the proving test
green against `BASELINE`; and (Planned) every verification line clean for the profile. A clean verdict
with a seat switched off is **labelled** with the missing seat.

## 7. Evidence from other tools and conformance

A native command, scanner or CI job MAY be recorded as an evidence source (`source`, `tree`,
`invocation`, `result`, `provenance`: `observed` | `reported`). It informs; it never replaces the
verifier or closes a gate. (**Planned, phase 3.**)

| Level | Requires | Full lane, both seats | Lite lane / seat off |
|---|---|---|---|
| **L1** Documented | lanes, gates, raw ticket, working doc | ✅ | ✅ |
| **L2** Machine-checked | counted lines, verdict states, evidence binding, review marker, verifier verdict line | ✅ 1.21.0 | partial: no verifier, labelled |
| **L3** Enforced | `GATE` lines, derived state, status card, proof under profiles, hooks that report or block out-of-phase writes | Planned, phases 1–3 | as L2 |
| **L4** Portable | attestation; CI check of consistency and binding (§4.1) | Planned, phase 3 | CI reports `neutral — no verifier` |
| **L5** Organisational | signed attestations, policy-as-code, approver separation of duties | later | — |

## 8. Versioning

`v0.x` is Draft and may change meaning between minors. `v1.0` freezes it under
[`STABILITY.md`](./STABILITY.md). **One fact, one place:** a grammar is written here only while it is
Planned. The PR that implements it moves the grammar into `check_lines.py` and leaves here only the
line's name, its identity and its clean condition, with a link to the generated
`reference/lines.md` (Planned, phase 0). `validate.py` fails if this page still spells out a
grammar the registry already has.

| Version | Plugin | Change |
|---|---|---|
| v0.1 | 1.21.0 | First draft. |
| v0.1 rev 2–3 | 1.21.0 | Two rounds of independent review: gates pass by phase; conformance per lane; exit codes per script; PROOF by failure kind with regression guards; `legacy` profile; printed status card reading a fixed Disclosure path; attestation recomputed vs carried; one place per grammar. |
