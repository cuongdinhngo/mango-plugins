# Writing mango docs

> **In 30 seconds.** Every mango page has one job, one reader and a size budget. Start with a
> 30-second box, put rules before examples, link instead of repeating, and never put history in a
> page that is not the CHANGELOG. Pick a template from [`templates/`](./templates/) before you write.

## Why this page exists

mango's text grew faster than its behaviour: at 1.21.0 the plugin README is 654 lines, the
working-doc template 4,278 words, and the 19 skills 37,158 words in total. Long text costs twice — users stop reading it, and
the model, which loads skill text as instructions, follows it less reliably. This page sets the rules
that stop the growth and the templates that make each page easy to follow.

## Two kinds of text

| Kind | Read by | Lives in | What "too long" costs |
|---|---|---|---|
| **Human docs** | users and contributors | `README.md`, `docs/**`, `plugins/mango/README.md`, `CONTRIBUTING.md`, `tests/**/README.md` | people stop reading |
| **Runtime text** | the model, as instructions | `skills/`, `agents/`, `principles/`, `PRINCIPLES.md`, `plugins/mango/templates/` | tokens, and lower instruction-following |
| **Exempt** | — | `CHANGELOG.md`, `RATIONALE.md`, `CLAUDE.md`, `tests/eval/history/`, `docs/templates/` | measured, not budgeted |

Runtime text **is behaviour**: shortening it is a behaviour change and goes through the smoke guard
(a skill without a fixture gets one first, or the PR says `not covered`). Human docs are not
behaviour: shorten them freely — but every `validate.py` scan that covered the old page (jargon,
one-grammar, doc consistency) must cover the page the text moves to.

## Seven rules

1. **One page, one job.** Each page is one type from the table below. A page that needs two types is
   two pages.
2. **30-second box first.** Every human doc opens with an *In 30 seconds* box of five lines or fewer:
   what it is, who reads it, what they can do after.
3. **Rule, then example. Never history.** Say what is true now. Why it changed goes in `CHANGELOG.md`;
   why it was designed so goes in `RATIONALE.md`.
4. **One fact, one place.** If a fact already lives somewhere (a grammar in `check_lines.py`, a key in
   `harness.example.json`), link to it. Copies drift.
5. **Tables over paragraphs** for anything compared, listed or mapped. No paragraph longer than five
   lines. No list nested deeper than one level.
6. **Label status.** Anything not shipped is marked **Planned** with its roadmap phase; anything shipped
   but not yet field-proven is **Experimental**. Unlabelled means shipped and stable.
7. **Stay inside the budget.** Each page type has a budget (below). Going over means splitting the
   page or moving detail to a reference page, not raising the number.

## Page types and budgets

| Type | Answers | Template | Budget |
|---|---|---|---|
| **README** | What is this, should I try it, how do I start? | [`readme.md`](./templates/readme.md) | 120 lines |
| **How-to** | How do I do one task? | [`howto.md`](./templates/howto.md) | 80 lines |
| **Concept** | How does this work, and why should I trust it? | [`concept.md`](./templates/concept.md) | 200 lines |
| **Reference** | What exactly is X (keys, lines, fields)? | [`reference.md`](./templates/reference.md) | no line limit; tables only, no prose beyond one line per entry |
| **Roadmap** | What happens next, and when is it done? | [`roadmap.md`](./templates/roadmap.md) | 150 lines |
| **Skill** (runtime) | What does the model do in this phase? | [`skill.md`](./templates/skill.md) | 2,000 words for a new skill; existing skills ratchet (below) |
| **Agent, principle, plugin template** (runtime) | — | — | ratchet only: never grows without a recorded reason |
| **Working-doc status card** | Where is this ticket right now? | [`status-card.md`](./templates/status-card.md) | 12 rows, printed by the harness (Planned, phase 2), never hand-written |

## The ratchet for existing text

Existing pages over budget are not rewritten in one go; they are **not allowed to grow**.

- `docs/budgets.json` records, for every file over its budget, its current size (lines for human docs,
  words for runtime text).
- `validate.py` fails when a recorded file grows beyond its recorded size, when a file not in the
  ledger exceeds its type's budget, and when an entry is higher than the file's real size.
- `python3 scripts/validate.py --update-budgets` **only lowers** entries to the measured size, and
  removes an entry once its file is within budget. It never raises one. Sizes always come from this
  command, never from a number quoted in a doc.
- The root README's one-screen limit is this mechanism's README budget, not a second rule.
- A human doc of no other type is budgeted as a Concept page; `docs/reference/` is not budgeted.
- Words loaded per full run are measured by `python3 scripts/measure_runtime.py`, which defines the run.
- Raising an entry is allowed only in a PR whose description says why the text could not be moved or
  cut. It is a visible decision, never a silent one.

## Translations

English is canonical, and the repo holds English only. Translations for a team's own use live
outside the repo and name, on their first line, the English commit they were translated from.

## Before you open a PR

- [ ] The page matches one type and uses its template.
- [ ] It opens with the 30-second box (human docs) or the skill header (runtime text).
- [ ] Nothing is copied from another page; facts are linked.
- [ ] No history outside `CHANGELOG.md` / `RATIONALE.md`.
- [ ] `python3 scripts/validate.py` passes, budgets included.
