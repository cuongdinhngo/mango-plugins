# mango-plugins

A Claude Code **marketplace** hosting the [`mango`](./plugins/mango) plugin — a portable, gated
ticket-lifecycle harness. The repo root *is* the marketplace; the plugin lives in
[`plugins/mango/`](./plugins/mango).

> **Status: 1.6.0 — stable API.** Proven across multiple real projects (two stacks) by its author,
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

Run the whole thing with `/mango:solve`, or invoke any phase directly. mango **stops at every ✋
gate** — silence is never approval — and each phase emits counted, gate-blocking artifacts.

**TIER** (`lite | full`, declared by `analysis`) sets process weight. Lite — the `/mango:quick`
lane — needs *all* of: `SCOPE=S`, a single file/requirement, no universal requirement resolving to
**N > 1**, and no security tag; anything else is full. The test is the **resolved denominator N**,
not keywords, so a requirement that only *sounds* universal but hits one site stays lite.
`/mango:quick` hard-refuses and routes to `/mango:solve` when those bounds are exceeded.

**Track** (`config.track`: `backend | frontend | fullstack`, default `backend`) picks the gate set,
orthogonal to TIER. The frontend track adds a **`DESIGN.md`** contract and a falsifiable a11y/token +
**M1–M10** rubric on top of the shared layer-match gate; mango owns the measurable part and
*composes* the aesthetic layer (a taste skill if installed, else `DESIGN.md`), never blocking because
taste is absent. For app-wide UI the denominator is the **reachable surfaces enumerated from code**,
each carrying its highest-tier proof; `review` blocks until every surface is covered.

| Skill | Phase / Gate | Produces |
|-------|--------------|----------|
| `/mango:analysis` | 1 → Gate 1 | Requirements matrix (C/R/G/AC) with counts, falsifiable-AC check (no bare `✅`), root-cause & blast radius, scope, and a `BASELINE` capture from the untouched checkout. |
| `/mango:design` | 2 → Gate 2 | Approach + rejected alternatives, assumptions, smallest row-traced change list, the proving test, and a **per-AC verification plan whose layer-match is a hard gate**. Frontend: builds `DESIGN.md`, one row per (AC × surface). |
| `/mango:execute` | 3 (autonomous) | Branch + approved changes only, the proving test, a two-axis sweep (files ⊆ approved list; behaviour matches the approved design), baseline-aware DoD, scoped formatting. STOPs to re-gate on an invalidated design or a stuck-detector. Frontend: emits the proof manifest. |
| `/mango:review` | 4 (stop if not clean) | `reviewer` + ticket-blind `challenger`, two-axis scope reconciliation, regression + layer-match re-check, proving-test result vs `BASELINE`. A conditional LGTM triggers a verify-only re-review. Frontend: scores the M1–M10 rubric + surface coverage. |
| `/mango:finalise` | 5 → final gate | PR draft, per-action approval, tracker writes, a cost-ledger completeness gate, follow-up tickets for deferred rows, and a **durable lesson** pushed to a shared ref. |
| `/mango:quick` | lite lane | One combined pre-code gate → execute → reviewer check → final gate, for trivial tickets. |
| `/mango:solve` | orchestrator | Doctor preflight, then every phase in order honouring `TIER`, holding each gate; resumes from `Session status`. |

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
expected artifacts. It costs tokens, so CI runs it only via the manual `eval.yml` workflow
(`workflow_dispatch`, needs the `ANTHROPIC_API_KEY` secret).

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
