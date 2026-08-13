---
name: promote
description: Cross-ticket promotion of a RECURRING type-2 heuristic into a proposed project rule. Use when two or more lesson entries in config.lessons_path record the same class of heuristic — it groups them by handle, proposes one candidate rule per class citing every instance, and STOPS for a human to ratify. It never writes a rule, never invents policy, and never touches a mango file.
---

**What this does.** Reads the claim records in `config.lessons_path`, groups **type-2** claims by their
`handle:`, and for each handle seen on **≥ 2 tickets** emits **one proposed rule** whose every clause is
traceable to the recorded lesson text, then **stops for a human to ratify**.
**What this does NOT do.** It writes no rule, edits no rule book, invents no policy, promotes no type
other than 2, and touches no mango file. It proposes; the human decides.

## Vocabulary (each term is used only after this line)

- **claim** — one falsifiable sentence in `config.lessons_path`, carrying `type:`, `evidence:`, `seen:`,
  `destination:` and — for type 2 — `handle:`. The field names are inlined here so this skill needs no
  file outside the project to run.
- **type 2** — a *generalisable heuristic*, a principle that holds across tools. The only type in scope.
- **handle** — a short kebab-case slug naming the **class** of heuristic (e.g. `blast-radius-grep`); the
  grouping key.
- **recurrence** — the number of **distinct ticket keys** in a claim's `seen:` list.
- **destination** — the project path a promoted rule goes to: `config.rulebook_path` for a **code**
  subject, `config.agent_brief_path` for a **process** one. Never guessed.
- **ratify** — an explicit, per-candidate human "yes". Nothing is written before it.

## Emit this FIRST, before any proposed rule text

Print the counted line, then the per-class table, **then** the rule proposals — never the count after.

`PROMOTE: <n> class(es) with recurrence >= 2 | <p> candidate(s) proposed | <e> already recorded (skipped) | <b> blocked (reason) | rules written: 0`

Per-class table, one row per handle: `handle | recurrence | ticket keys | subject (code|process) | destination | verdict (proposed|skipped|blocked)`.

`rules written: 0` is not decoration: a non-zero value before a ratify means this skill wrote a rule and
the run is wrong. Emit the line on **every** run, zeros included.

## Steps

1. **Read the corpus.** Read `config.lessons_path`. Unset or absent → emit the counted line with all
   zeros, say the corpus is not configured, and stop. **Output:** the counted line with zeros.
2. **Select.** Keep only claims with `type: 2`; discard every other type — 1, 3, 4, 5 and 6 are **out of
   scope**. Read each kept claim's `handle:` and `seen:`. A type-2 claim with **no** `handle:` is reported
   `blocked (no handle — unrecallable)`.
   **Output:** one line per discarded type with its count, e.g. `skipped: type 5 x 11`.
3. **Group and gate on recurrence.** Group kept claims by `handle:`; recurrence is the number of
   **distinct** ticket keys across the group's `seen:` lists. Keep a group only at recurrence **>= 2**. A
   handle at recurrence 1 gets `verdict: skipped (recurrence 1)` and no candidate.
   **Output:** the per-class table above.
4. **Check idempotency BEFORE proposing.** Grep each remaining handle's destination file for the handle
   slug and the group's claim IDs. A destination already carrying a rule for the class gets
   `skipped (already recorded at <path>:<line>)` and **no candidate**, so a re-run on an unchanged corpus
   proposes nothing new.
   **Output — per handle, the grep command and its actual result, whether or not it matched.** Paste the
   command and its output verbatim: the matching `<path>:<line>` on a hit, the empty result on a miss. A
   handle reported as "not yet recorded" **with no command shown is not a check** — a skipped grep and a
   genuine empty result otherwise produce identical output, which is how this step goes missing unnoticed.
5. **Draft one candidate rule per remaining handle — every clause traceable to lesson text.** The
   candidate must be **specific enough to fail**: it names the trigger condition, the required action, and
   the observable that shows the action happened. Then run these three rejections on your own draft, and
   report each verdict in the proposal:
   - **restatement test** — could this sentence be produced by paraphrasing the lesson without adding a
     trigger, an action **and** an observable? If yes it is a **restatement, not a rule**: reject and
     redraft. "Be careful with blast radius" restates; "when the change-list touches a shared symbol,
     enumerate every test root and paste the command output" does not.
   - **traceability test** — quote, per **clause**, the lesson text it comes from, as
     `<CLAIM-ID>: "<quoted words>"`. A clause with no quote is **invented policy**: delete it.
   - **falsifiability test** — name the grep, command, or gate output that would show the rule violated. A
     clause nothing could disprove is deleted.
   **Output:** per candidate — the rule text, the per-clause quote list, the falsifier, and the three
   verdicts.
6. **Route.** Destination from subject: **code → `config.rulebook_path`**, **process →
   `config.agent_brief_path`**. Never file a process heuristic in the code rule book. An **unset** key
   gives `blocked (destination key <key> unset)` — surface the candidate anyway; never redirect, never drop.
   **Output:** the destination path, or the `blocked` reason, per candidate.

## The human gate — stop here and ask

Print each candidate, then stop with **this question**, and take no further action until it is answered
per candidate:

> **For each candidate above, answer `ratify`, `reject`, or `edit: <your text>`. Which candidates do you
> ratify, and into which file? I will write nothing until you answer.**

Silence is not an answer and not approval; a blanket "looks good" is not a per-candidate ratify. On
`ratify`, write **only** that candidate, **only** into the destination it named, through `codify`'s
provisional -> ratify flow — tagged `PROVISIONAL (awaiting ratification)`, citing every claim ID in its
group. On `edit`, the human's text is authoritative and replaces the draft verbatim.

**No promotion ever writes into a mango directory** — no skill, agent brief, template or `PRINCIPLES.md`.
A recurring gap in mango itself is a **type-3 signal** in `config.skill_gap_path` for mango's maintainer,
and type 3 is out of scope here.

## When NOT to run this

- **Mid-ticket.** This is a cross-ticket pass — run it between tickets, never inside one.
- **On one lesson.** Recurrence 1 is out of scope. Propose nothing.
- **On any type other than 2.** A type-5 project fact stays in `config.lessons_path` however often it
  recurs; a type-3 skill gap is a maintainer signal; types 1, 4 and 6 have their own destinations.
- **When the corpus has not changed since the last run.** Step 4 skips everything; the run is a no-op.
- **To satisfy a gate.** No mango gate requires a promotion. A weak rule proposed to show activity is
  worse than none.

## Worked example

Corpus: three lesson entries — tickets `PROJ-069`, `PROJ-072`, `PROJ-080` — each recording that a
name-grep of one directory stood in for a blast-radius estimate and each time missed a real consumer only
a producer/consumer trace would find. All three carry `type: 2` and `handle: blast-radius-grep`.

`PROMOTE: 1 class(es) with recurrence >= 2 | 1 candidate(s) proposed | 0 already recorded (skipped) | 0 blocked (reason) | rules written: 0`

| handle | recurrence | ticket keys | subject | destination | verdict |
|---|---|---|---|---|---|
| `blast-radius-grep` | 3 | PROJ-069, PROJ-072, PROJ-080 | code | `config.rulebook_path` | proposed |

**Candidate rule.** *When a change touches a shared symbol, type, or a value threaded to a downstream
consumer, the blast-radius estimate enumerates the real producers and consumers — every test root, not
only `src` — and records the command run and its output. A name-grep of one directory is not an estimate.*

- clause 1 trigger — `CLM-069: "the change altered a shared symbol"`
- clause 2 action — `CLM-072: "only a producer/consumer trace found the missing call site"`
- clause 3 observable — `CLM-080: "the grep was never recorded, so nobody could see it covered one root"`
- **falsifier:** a Gate-2 blast-radius cell with no pasted command output.
- restatement test: **passes** (names trigger, action and observable). traceability: **3/3 clauses
  quoted**. falsifiability: **passes**.

Written now: **nothing**. The gate question above is asked, and the rule is written only on `ratify`.
