# The learning loop — recall, propose, never self-modify

> **In 30 seconds.** A ticket's durable lesson is split into atomic claims, classified, checked, and
> proposed for promotion into a project file a human ratifies; later tickets get it back as advisory
> recall. mango itself is never modified. **Status:** classification and promotion are Experimental — see [`principles/maturity.md`](../../plugins/mango/principles/maturity.md).

## The idea

A durable lesson used to sit in `lessons_path` and be re-read by nobody. The loop makes it act on the
next ticket — **without** mango ever changing itself. Full contract in
[`PRINCIPLES.md`](../../plugins/mango/PRINCIPLES.md) → *The learning loop*.

```
finalise: lesson → split into atomic CLAIMS → classify (a PROPOSAL, 6 types) → recurrence / supersession
             → FALSIFY (still true? cheaply checkable? checked, or only repeated?) → propose promotion
             → ✋ HUMAN RATIFIES, per claim → a PROJECT file
refine/analysis: advisory RECALL — type 1 by symbol, type 5 by area, type 6 by the re-raised finding
```

## How it works

- **The unit is the atomic claim, not the entry.** A bundled lesson classified as one thing routes its
  other halves wrong, so `finalise` splits it first and emits `CLAIMS: <c> claim(s) from <e> entr(ies) |
  T1=… T6=… | <u> unclassified`.
- **Six types decide the destination and the recall key:** 1 tool-constraint (stays in `lessons_path`,
  recalled by **symbol**), 2 heuristic (`rulebook_path` for code, `agent_brief_path` for process),
  3 skill-gap **signal** (`skill_gap_path`), 4 world-fact (`gotchas_path`), 5 project ground-truth
  (recalled by **area**; descriptive → `design_doc_path`, normative → a rule-book entry with ID +
  blocking, environment → a `verified-at:` stamp), 6 adjudicated non-defect (`drift_path`, with an
  `expiry:`, recalled by the finding it pre-empts).
- **Recall is advisory, and that is all it is.** It surfaces claims at `refine`/`analysis` with
  `RECALL: <n> surfaced | … — advisory (blocks nothing)`; it never injects a requirement, adds a matrix
  row, blocks a gate, or edits a file. A `retired:` claim is skipped (a human retires it; no auto-retire).
- **Falsification sits in FRONT of the ratification gate.** Recurrence measures how often a claim was
  *restated*, not whether it was ever *checked* — the most-repeated lesson can be the false one. A
  recurring claim that is falsified, or that cannot be cheaply checked, is **blocked from promotion** and
  stays a lesson.
- **Every promotion is human-ratified and lands in a PROJECT file.** The rule goes into
  `rulebook_path` (via `codify`'s provisional→ratify), **never copied into `CLAUDE.md`** — `CLAUDE.md`
  carries only the pointer `init` wrote, and the promotion is not done until `doctor` is green on it.
- **Lessons never modify mango.** No lesson — however recurrent, however ratified — edits a mango skill.
  A type-3 skill-gap is a **signal** for mango's maintainer, who changes mango through a normal version.
  `PROMOTION: … | mango files written: 0` is the falsifiable form of that rule.
