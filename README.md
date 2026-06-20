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

Then, in any project you want to use it in, copy the per-project contract and fill it in:

```
cp <plugin>/config/harness.example.json .harness.json
# edit .harness.json — point it at your rule-book, repos, test command, and tracker
```

`.harness.json` is gitignored by this marketplace; in your project, treat it as committed config —
never put secrets in it (those live in a gitignored `.env`).

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

CI additionally runs `claude plugin validate ./plugins/mango --strict` and
`claude plugin validate . --strict` as a **best-effort, non-blocking** step.

## Publish

1. Create the GitHub repo `mango-plugins` under your account.
2. `git remote add origin git@github.com:<user>/mango-plugins.git`
3. `git push -u origin main`
4. Users install with the two commands above (`/plugin marketplace add <user>/mango-plugins`).

## License

MIT — see [LICENSE](./LICENSE).
