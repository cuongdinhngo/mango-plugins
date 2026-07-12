# mango-plugins

A Claude Code **marketplace** hosting the [`mango`](./plugins/mango) plugin — a portable, gated
ticket-lifecycle harness. The repo root *is* the marketplace; the plugin lives in
[`plugins/mango/`](./plugins/mango).

> **Status: 1.4.0 — stable API.** Proven across multiple real projects (two stacks) by its author,
> with a green behavioural eval and fault-injection-tested escalation paths; the public skill/config
> API has been stable since 1.0. Independent-operator validation is ongoing.

## Install

In Claude Code:

```
/plugin marketplace add cuongdinhngo/mango-plugins
/plugin install mango@mango-plugins
```

Then, in any project you want to use it in, bootstrap the per-project contract:

```
/mango:init      # detects your stack, writes .harness.json, scaffolds a starter rule book
/mango:doctor    # health-checks the setup (✅/⚠/❌ with remediation)
```

`/mango:init` marks every guessed value `UNVERIFIED` for you to confirm. Prefer to fill it by hand?
Copy `<plugin>/config/harness.example.json` to `.harness.json` and edit it (rule-book, repos, test
command, tracker). `.harness.json` is gitignored by this marketplace; in your project treat it as
committed config — never put secrets in it (those live in a gitignored `.env`).

No rule book yet, or a thin/inconsistent one? Run `/mango:codify` — it **counts** the conventions your
code and schema already use, asks **you** to choose each standard, and records them as **provisional
until you ratify**. mango facilitates the rule book; it never authors it. Two opt-in descriptive maps,
`/mango:sitemap` (code surface) and `/mango:db-map` (database schema), generate regenerable facts when
configured — see the [plugin README](./plugins/mango/README.md).

Run a ticket with `/mango:solve <KEY>` (full lifecycle) or `/mango:quick <KEY>` (lite lane for
trivial fixes). See the [plugin README](./plugins/mango/README.md) for the lite/full tiers, the
cost profile, and the model-delegation map (`cost_tier`: Opus decides, Sonnet executes, Haiku
gathers).

## The lifecycle

Run the whole thing with `/mango:solve`, or invoke a phase directly. mango **stops and waits at
every ✋ gate** — silence is never approval. Each phase emits counted, gate-blocking artifacts.

`analysis` declares `TIER: lite | full`. **Lite** (the `/mango:quick` lane) is chosen only when ALL
hold: `SCOPE=S`, a single file / single requirement row, no universal requirement **with N > 1**, and
not security-tagged — otherwise **full**. The decision keys on the **resolved inventory denominator
N**, not on keywords: a requirement that *sounds* universal but resolves to a single site (**N = 1**)
is lite-eligible. `/mango:quick` enforces this with a hard entry check: it **refuses** and routes to
`/mango:solve` if the ticket is security-tagged, touches more than one file, or has a universal
requirement that resolves to N > 1.

`config.track` (`backend|frontend|fullstack`, default `backend`) selects which **gate set** applies —
**orthogonal to TIER** (TIER = process weight; track = which gates). `backend` runs exactly as before.
On the **frontend** track `analysis` emits a counted `TRACK` artifact, `design` builds a per-project
**`DESIGN.md`** contract, and `review` scores a falsifiable a11y/token + **M1–M10** responsive/touch
rubric — all riding the existing layer-match hard gate. mango embeds only the measurable/greppable
part (**own the durable**) and **composes, never owns,** the aesthetic layer: it calls a taste skill
if installed, else follows `DESIGN.md`, and never stops because one is missing. See the
[plugin README](./plugins/mango/README.md#frontend-track--measurable-ui-gates-composed-taste).

For a **universal / app-wide** frontend requirement, the denominator is the count of **reachable
surfaces enumerated from the code** (`analysis` emits `SURFACES: N`) — never the surfaces the ticket
named. `execute` records the **highest-tier proof per surface** (`automated` → recorded `render@<bp>`
→ `excluded`) in a proof manifest — **e2e is optional, a proof is not**, and mango never stops for a
missing runner. `review` blocks unless `N == M + X`, emitting a loud `⚠ surfaces proven: k/N` banner
when under-covered.

| Skill | Phase / Gate | Produces |
|-------|--------------|----------|
| `/mango:analysis` | 1 → Gate 1 | Requirements matrix (C/R/G/AC) + count line, AC validation (each acceptance value **falsifiable** or a recorded **manual-check exclusion** — neither → flagged, no bare `✅`), clarification tally, universal inventory, root-cause/gap, blast radius, scope, and a `BASELINE` capture (`green \| red \| flaky` from the untouched checkout; not-green → delta-green DoD). |
| `/mango:design` | 2 → Gate 2 | Approach + rejected alternatives, **Assumptions** (`verified \| novel-untested` — a novel 3p/runtime assumption needs a spike or integration-shaped proof), smallest change-list traced to rows, rule compliance, the named proving test, a **per-AC verification plan whose layer-match is a hard gate** (an integration/runtime AC backed only by a logic-layer proof is `❌` and blocks Gate 2), rollback + porting. On the **frontend** track also creates/updates the **`DESIGN.md`** contract and lays out the plan **one row per (AC × surface)** with an under-coverage banner. |
| `/mango:execute` | 3 (autonomous) | Branch, the approved change list only, the proving test, a verification sweep on **both axes** (file set: diff ⊆ approved list; **behaviour**: a design-conformance self-check that records any deviation from an approved Gate-2 Approach bullet even when the file diff is clean), a **baseline-aware DoD** (delta-green when `BASELINE ≠ green`), commits with no AI co-author trailer. Runs the project's formatter **only on authored/edited files** — never a wholesale reformat of a shared file (**format-scope rule**); whole-file conformance is a separate concern (CI / a chore ticket). STOPs to **re-gate if the design is invalidated** and via a **stuck-detector** (`stuck_threshold` failed attempts at the same signature). On the **frontend** track emits the **proof manifest** (highest tier per surface; never stops for a missing runner). |
| `/mango:review` | 4 (stop if not clean) | `reviewer` + ticket-blind `challenger` (payload excludes the `.work.md`), scope reconciliation on **both axes** (file set **and** behavioural conformance), regression check, layer-match re-confirmation, proving-test result judged against the recorded `BASELINE`, `k/N` coverage. Round 1 may return a **conditional LGTM**, making the re-review a **verify-only pass** (named-fix check + regression scan, no full re-derivation). On the **frontend** track also scores the **M1–M10** a11y/token rubric against `DESIGN.md` and the **`N == M + X`** surface-coverage check. |
| `/mango:finalise` | 5 → final gate | PR draft, per-action approval for every outward action, tracker writes via CLI, follow-up tickets for deferred rows, and a **durable lesson** captured to `lessons_path` on every run. |
| `/mango:quick` | lite lane | Single combined pre-code gate → execute → reviewer-only check → final gate, for trivial tickets. |
| `/mango:solve` | orchestrator | Doctor preflight, then runs all phases in order honouring `TIER`, holding every gate; resumes from `Session status`. |

See the [plugin README](./plugins/mango/README.md) for the full tier details, `.harness.json` keys,
cost profile, and model-delegation map.

## Supporting skills

These are **not** part of the gated lifecycle and do not run a ticket — they set up, diagnose, build
knowledge about, or describe a project. Kept separate from the lifecycle table above for that reason.

| Skill | Role | Notes |
|-------|------|-------|
| `/mango:init` | Detect the stack, write `.harness.json`, scaffold a starter rule book | Marks every guessed value `UNVERIFIED` for you to confirm. |
| `/mango:doctor` | Setup health-check — ✅/⚠/❌ checklist with exact remediation | Prints the running version + base path as its **first line**; offline — a green doctor does not prove the intended version is loaded. |
| `/mango:codify` | Count the code + DB conventions already in use → **you choose** each standard → record it | Recorded **PROVISIONAL until you ratify**; facilitates, never authors, changes no code. |
| `/mango:sitemap` | Generate a code-surface map (routes / modules) into `docs_dir` | Opt-in; needs `code_map_cmd`. |
| `/mango:db-map` | Generate a schema map (tables / columns / keys / indexes / relations) into `docs_dir` | Opt-in; **off by default**; needs `db_kind` + (`db_introspect_cmd` or `migrations_path`). |
| `/mango:version-check` | Compare running vs latest and **print the host `/plugin` commands** | Informs only, never updates; needs `update_check_url`. |
| `/mango:budget` | Detect token optimizers → inform per the safety axis → record a human's provisional adoption | Descriptive + human-gated; never installs, never depends on one, never lets one weaken a critic. mango records a descriptive **Cost ledger** (one row auto-appended per dispatch return; **dispatch-only** — it never implies a dispatch-vs-noise split), tolerates RTK's compact output but degrades cleanly without it, and — when RTK is present-but-unwired — **prints** the wiring command for the user to run (never runs it). |

The `sitemap`/`db-map` outputs are **descriptive** (facts, regenerable — what the project is);
`codify` is **normative** (what it should be). mango generates the descriptive and facilitates the
normative, but never authors the normative.

## Update

```
/plugin marketplace update mango-plugins
/plugin install mango@mango-plugins
```

## Validate locally

The required gate is deterministic, stdlib-only, and needs no network or auth:

```
python3 scripts/validate.py
```

It runs structural checks plus per-skill contract tokens (it fails if a skill loses its
load-bearing artifact). CI additionally runs `claude plugin validate ./plugins/mango --strict` and
`claude plugin validate . --strict` as a **best-effort, non-blocking** step.

The behavioural eval (`tests/eval/run.sh`) drives the model over fixture tickets and asserts the
expected artifacts — the analysis happy path, the higher-risk lifecycle behaviours (proof at the
risk layer, the ticket-blind challenger catching an unmet AC, the design-invalidated escalation, and
the stuck-detector), the **frontend track** (a "no horizontal overflow @320 px" AC backed only by
a unit proof is layer-matched `❌` and blocks Gate 2; the rubric flags a hover-only / mouse-only
handler), **surface coverage** (a universal AC covering only 2 of 5 reachable surfaces reads
`surfaces proven: 2/5` and blocks; a no-runner AC yields a tier-2 `PASS(render@<bp>)`, not a skip),
the **format-scope rule** (execute scopes the formatter to the authored/edited files, never a
wholesale reformat of a shared file), and the four **v1.2** behaviours — one fixture each so a red run
is diagnosable — (a **behavioural deviation** from the approved Gate-2 bullet is recorded despite a
clean file diff; a **vague AC** is pinned to a measurable or logged as a manual-check exclusion and
cannot carry a bare `✅`; a **red baseline** — a verification command genuinely red on a clean
checkout — is **measured by running it** (not read from the ticket) and recorded with a delta-green
DoD; a **conditional LGTM** takes a verify-only re-review) — the four **v1.3** budget behaviours (the **cost ledger** is
descriptive and never auto-cuts; an **RTK-absent** run completes identically; **Caveman is forbidden on
critic output**, which keeps its `path:line` evidence; enabling an optimizer is a **recorded provisional
decision**, not silent), and the five **v1.4** ledger-truth behaviours — one fixture each — (the ledger
**auto-appends** one row per dispatch return, not narrated bookkeeping; it is **dispatch-only** and
refuses a fabricated dispatch-vs-noise split, pointing at the optimizer's own `rtk gain`; a
conditional-LGTM **verify-only round reuses round-1 facts** and re-runs only the affected proof; the
**Tokens column** carries no false-precision `(out)`; and with RTK present-but-unwired **`budget`
prints the wiring command** + a "you run this, not mango" note and administers nothing). It
costs tokens, so CI runs it only via the manual `eval.yml` workflow (`workflow_dispatch`, needs the
`ANTHROPIC_API_KEY` secret). Assertions match at the **decision level** and are **emphasis-agnostic**
(they tolerate markdown `**`/`_` and phrasing variants around the load-bearing token), so a correct
behaviour passes under any wording while a wrong *outcome* still fails — green comes from stability
across independent fresh runs, not from tuning a regex to one transcript.

**Running the eval.** One command, hands-free:

```
bash tests/eval/run.sh
```

It works with **either** an exported `ANTHROPIC_API_KEY` **or** an OAuth/subscription login
(`claude /login`) — it verifies the capability to run `claude -p`, not a specific credential. The
script sets up its own throwaway environment (an isolated local clone, a temp `.harness.json`, and a
minimal rule book) so a fresh clone "just runs" against the **shipped** skills, then removes it all on
exit — your working tree is never mutated. It prints the per-fixture `PASS`/`FAIL` lines and exits
non-zero if any assertion fails.

## Publish

1. Create the GitHub repo `mango-plugins` under your account.
2. `git remote add origin git@github.com:<user>/mango-plugins.git`
3. `git push -u origin main`
4. Users install with the two commands above (`/plugin marketplace add <user>/mango-plugins`).

## License

MIT — see [LICENSE](./LICENSE).
