# mango-plugins

A Claude Code **marketplace** hosting the [`mango`](./plugins/mango) plugin — a portable, gated
ticket-lifecycle harness. The repo root *is* the marketplace; the plugin lives in
[`plugins/mango/`](./plugins/mango).

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

Run a ticket with `/mango:solve <KEY>` (full lifecycle) or `/mango:quick <KEY>` (lite lane for
trivial fixes). See the [plugin README](./plugins/mango/README.md) for the lite/full tiers, the
cost profile, and the model-delegation map (`cost_tier`: Opus decides, Sonnet executes, Haiku
gathers).

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

## Publish

1. Create the GitHub repo `mango-plugins` under your account.
2. `git remote add origin git@github.com:<user>/mango-plugins.git`
3. `git push -u origin main`
4. Users install with the two commands above (`/plugin marketplace add <user>/mango-plugins`).

## License

MIT — see [LICENSE](./LICENSE).
