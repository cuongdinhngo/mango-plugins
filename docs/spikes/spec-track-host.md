# Spike — host capabilities for the spec track

> **In 30 seconds.** Before the spec track (Track S in [`ROADMAP.md`](../ROADMAP.md)) builds a
> read-only `spec-reviewer` and three manual skills, this page records what Claude Code actually does
> with the frontmatter they rely on. Each answer cites the official docs **and** a reproducible test.
> Read it before writing the agent or the skills' frontmatter.
> **Status:** spike, run on Claude Code `2.1.321` (2026-11-10). Answers go stale with the host; re-run the test below on upgrade.

## The idea

The spec track leans on four host behaviours: a plugin agent limited to `Read, Grep, Glob`; that agent
starting without CLAUDE.md; skills the model cannot invoke but the user can; and several reviewers
dispatched in parallel, with a failed one detectable. Each was checked twice — against the docs, and by
a throwaway plugin run with `claude -p --plugin-dir`.

## How it works — the answers

| # | Question | Answer | Docs | Test | Min version |
|---|---|---|---|---|---|
| 1 | Does a **plugin** agent honour `tools: Read, Grep, Glob`? | **Yes.** The agent listed only `Read, Grep, Glob` (plus the host's hand-back tool) and could not run a shell command. | [sub-agents](https://code.claude.com/docs/en/sub-agents.md) — *Restrict which tools a subagent can use*; plugin agents ignore only `hooks`, `mcpServers`, `permissionMode`, `initialPrompt` | T1 | not stated; observed on 2.1.321 |
| 1b | Does a plugin agent honour `omitClaudeMd: true`? | **Yes.** With it, the project CLAUDE.md canary was absent at start; without it, present. | sub-agents frontmatter table; CHANGELOG 2.1.271 *"Added `omitClaudeMd` … letting custom and plugin subagents run without user, project and local CLAUDE.md files; managed policy files still load"* | T1 | **2.1.271** |
| 2 | Does `omitClaudeMd` stop a **subdirectory** CLAUDE.md attached when the agent reads a file there? | **No.** Reading `sub/data.txt` attached `sub/CLAUDE.md` to the agent's context, with or without the key. | sub-agents, *What loads at startup*: *"a subdirectory's `CLAUDE.md` and matching path-scoped rules still load when the subagent works with files there"* | T1 | — |
| 3 | Does `disable-model-invocation: true` on a **plugin** skill hide it from the model, and can the user still run `/<plugin>:<skill>`? | **Yes to both.** The model's skill list omitted the skill and the model picked another; `/spk:hello` ran it. | [skills](https://code.claude.com/docs/en/skills.md) — *"Claude can't invoke the skill on its own"*; plugin skills run as `/plugin-name:skill-name` | T2 | not stated; observed on 2.1.321 (fix 2.1.110 for mid-message `/skill`) |
| 4a | Limit on parallel subagents? | **20 running at once** by default (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`); the 21st fails with `Concurrent subagent limit reached`. No limit on the total. | sub-agents, *Concurrent subagent limit*; CHANGELOG 2.1.217 | docs only | **2.1.217** |
| 4b | How does a failed subagent show? | Cut off after some text → partial output **with a note that it did not finish**; nothing produced → `Agent terminated early due to an API error`; background → marked failed. `maxTurns` → output marked partial. **No wall-clock timeout is documented.** | sub-agents, *API errors in subagents* | docs only | partial marking 2.1.246 |

## What it means for the track

| Finding | Decision for the track |
|---|---|
| 1, 1b | `spec-reviewer` ships `tools: Read, Grep, Glob` and `omitClaudeMd: true`; `validate.py` pins both. |
| 1b min version | `doctor` warns when the host is older than **2.1.271**: the reviewer would then start with CLAUDE.md, so its *fresh context* claim does not hold. |
| 2 | "No CLAUDE.md" means **at start only**. The reviewer brief names the files it may read; a nested CLAUDE.md it attaches is disclosed, not prevented. Never claim the reviewer saw no project instructions. |
| 3 | 🧑 **Maintainer decides.** Proposal: `brainstorm` and `spec` set `disable-model-invocation: true` (manual entry only); `spec-review` stays model-invocable so `spec` can hand off to it. |
| 4a | Lens counts (3–4 per round) are far below the limit; no throttling needed. |
| 4b | A lens is `not run` when its report has **no `LENS RESULT` line** — this covers the partial-output note, the API-error result and the turn limit alike. Retry once, then `not run`. There is no timeout to rely on. |

## What it guarantees — and what it does not

| Guarantees | Does not guarantee |
|---|---|
| The four behaviours held on 2.1.321 with the throwaway plugin below. | That they hold on a later host — re-run on upgrade. |
| The model could not call a `disable-model-invocation` plugin skill in the test. | That the model never imitates the skill's workflow by hand (the host tells it to ask the user instead, since 2.1.222). |
| A reviewer without Bash cannot run a command. | That it read no project instructions: a subdirectory CLAUDE.md still attaches (row 2). |

## How to reproduce

A throwaway plugin `spk` with two agents and two skills, in a git repo whose root `CLAUDE.md` and
`sub/CLAUDE.md` each hold a distinct canary sentence; run with `--model haiku` to keep it cheap.

| Part | Content |
|---|---|
| `agents/ro-omit.md` | `tools: Read, Grep, Glob`, `omitClaudeMd: true`, `model: haiku` |
| `agents/ro-keep.md` | the same without `omitClaudeMd` |
| `skills/hello/SKILL.md` | `disable-model-invocation: true`; replies `PINEAPPLE-HELLO` |
| `skills/auto/SKILL.md` | no flag; replies `MANGO-AUTO` (control) |

- **T1** — `claude -p "Dispatch spk:<agent> with: (1) quote any canary sentence in your context without reading a file; (2) list your tools; (3) try echo BASHPROBE; (4) read sub/data.txt, then quote any canary sentence" --plugin-dir <plugin>`.
  Observed: `ro-omit` → (1) none, (2) Read/Grep/Glob, (3) no shell, (4) sub canary. `ro-keep` → (1) root canary, then as `ro-omit`.
- **T2** — `claude -p "List every skill you can invoke, then give a fruit greeting with the matching skill"` → `spk:hello` absent from the list; the model called `spk:auto`. `claude -p "/spk:hello"` → `PINEAPPLE-HELLO`.

## Related

- [`ROADMAP.md`](../ROADMAP.md) — Track S.
- [`PROTOCOL.md`](../PROTOCOL.md) — the spec reviewer role.
