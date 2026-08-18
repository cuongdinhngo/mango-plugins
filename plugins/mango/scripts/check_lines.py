#!/usr/bin/env python3
"""CHECK-LINES — the harness parses the counted lines; the agent reads the verdict.

Stdlib only, no network, READ-ONLY. Reads a working doc, finds every counted line in it, and verdicts
each against the ONE canonical grammar the plugin ships for that line. Nothing here is narrated: every
count comes from a parse this script performed.

  CHECK-LINES
    lines    : <n> emitted | <p> pass | <f> FAIL | <k> not-checkable | <q> pending
    required : <r> required through <phase> | <m> MISSING
    gates    : <g> arithmetic gate condition(s) read | <b> BROKEN
    restated : <d> carried-forward restatement(s), each re-checked for contradiction

Three checks, in order of value:

  1. INTERNAL CONTRADICTION — a line whose own numbers disagree: sub-counts that do not sum to the
     total, `h != t + x + u`, a stated `n` that mismatches the rows enumerated on the line itself. No
     grammar judgement is required for this one, so it runs on EVERY occurrence of a line, including a
     carried-forward restatement.
  2. MISSING WHEN REQUIRED — a line the phase was required to emit, absent. Keyed on the phase, the
     `TIER` and the `TRACK` read from the doc itself, so a lite-lane doc is only held to the lines its
     lane emits and a backend doc is never held to a frontend line.
  3. OFF-GRAMMAR — fields invented, fields omitted, order changed, the token itself misspelled.
     Verdicted against the BEST occurrence of each line (the one matching the most fields), because a
     doc that restates a line in a later self-audit is not emitting it twice.

REPORT, NEVER REWRITE. This script says a line is wrong. It does not fix it, does not reformat it, and
never opens the working doc for anything but reading. A script that edited would hide exactly the
paraphrase it exists to surface.

NOT-CHECKABLE IS A THIRD STATE, distinct from pass and fail — the same discipline as `could-not-run` in
RECONCILE, and it has its OWN EXIT STATUS (3). A counted line this script has no grammar for is reported
and counted on its own axis, never a silent pass; so is the missing-when-required axis when the doc does
not declare its phase, and so is an unreadable doc. Exit 3 means *nothing failed, but this run was not
fully verified* — a distinct answer from both clean (0) and broken (2), so a caller can tell them apart
without reading the text.

NO NEW COUNTED LINE. The verdict rides the exit status and the lines above; the calling skill quotes
them. Adding a counted line that nothing parses is the defect this script exists to end.

What this script does NOT decide: any gate condition needing judgement. `CLARIFICATION: j > 0` is a
legitimate STOP, not a broken gate, and is reported as a fact rather than a failure. Only the
arithmetic conditions the shipped skill text states as blocking — `HANDLES: u == 0`, `EXCLUSIONS:
e == n`, `RECURRING-T2: l == 0`, and the `… written: 0` / `… deleted: 0` invariants — are counted on
the `gates` axis.

Subcommands
  check     <workdoc> [--phase 0..5|refine|analysis|design|execute|review|finalise]
                      [--tier lite|full] [--track backend|frontend|fullstack] [--epic]
  grammars  print the canonical grammar of every counted line the plugin ships

WHAT THIS CANNOT PREVENT, stated plainly: an agent quoting a passing verdict it never ran. No script can
close that — RECONCILE has the same hole. What is available is a cheap tie: the `doc` line carries the
doc's byte length and a content digest, so a quoted verdict belongs to one specific doc state and a
verdict quoted against a doc that has since changed is detectable. Beyond that it is a disclosure
obligation on the caller, not a guarantee.

Exit codes: 0 clean · 2 a FAIL, a MISSING, or a BROKEN gate condition · 3 nothing failed but something
was NOT CHECKABLE (an unknown counted line, an undeclared phase, an unreadable doc) · 1 usage.
"""

import hashlib
import re
import sys

# --------------------------------------------------------------------------- grammar registry

NUM = r"(?:\d{1,3}(?:,\d{3})+|\d+)"
# An optional parenthetical annotation after a field label. The shipped grammar writes a field as
# `<t> traced (command + result)`; a zero example may write `0 traced`. Both name the same field, so the
# annotation is optional to the parser and the two are ONE grammar, not two.
ANN = r"(?:\s*\([^()]*\))?"

MANGO_SEPARATOR = "MANGO WORKING DOC (below this line is NOT part of the raw ticket)"


def pl(word, suffix="s"):
    """Natural pluralisation is tolerated; TRUNCATION is not.

    The canonical text writes `<c> claim(s)`; an agent writing `1 claim` has inflected the placeholder,
    not paraphrased the field, and failing that would make the check noise on an otherwise correct line.
    Dropping the noun outright (`0 routed` for `<d> routed to a destination`) IS a paraphrase and still
    fails. One grammar, with a stated tolerance for inflection — never two grammars.
    """
    return rf"{word}(?:\({suffix}\)|{suffix})?"

# Phase order. The lite lane's single pre-code gate sits where design does.
PHASES = ["refine", "analysis", "design", "execute", "review", "finalise"]
PHASE_ALIASES = {
    "0": "refine", "1": "analysis", "2": "design", "3": "execute", "4": "review", "5": "finalise",
    "quick": "design", "lite": "design", "breakdown": "analysis", "solve": "finalise",
    "autorun": "finalise", "finalize": "finalise", "final": "finalise",
}

# ALL-CAPS labels the working doc and the envelope legitimately use that are NOT counted lines. Without
# this, every `**TIER:** full` header field would be reported not-checkable and the report would be
# noise on a perfectly clean doc.
NOT_COUNTED = {
    "SCOPE", "STRUCTURE", "TRACK", "TIER", "BASELINE", "INPUT KIND", "TYPE", "KEY", "ID", "AC", "R",
    "C", "G", "ROWS", "PHASE", "CHALLENGER", "DISCLOSURE", "RECONCILE", "RUN CONTRACT", "CONDITION",
    "END CONDITION", "END RUN CONTRACT", "NOTE", "TODO", "WARNING", "STOP", "OK", "PR", "SHA",
    "UNCHECKED AGENT CLAIMS", "MERGE STRATEGY", "CHECK-LINES", "SURFACE", "GATE", "DOD", "N",
}


def seg(key, label_rx, human):
    """One `<count> <label>` segment of a counted line, with the annotation optional."""
    return (rf"(?P<{key}>{NUM})\s+{label_rx}{ANN}", human)


def _entries(text):
    """Split an enumerated tail into entries, delimiter by precedence: `·`, then `|`, then `,`.

    `·` and `|` are only ever separators in the shipped grammar, while a section name or a reason
    legitimately carries a comma — so a comma is the LAST resort, never chosen over an unambiguous one."""
    if text is None:
        return []
    delim = "·" if "·" in text else ("|" if "|" in text else ",")
    return [p.strip() for p in text.split(delim) if p.strip()]


def _count_named(text):
    """Count the names enumerated in a `(names)` parenthetical. Returns None when the delimiter is
    ambiguous (both `·` and `,` present) — a not-checkable sub-check, never a guessed count."""
    if text is None:
        return None
    if "·" in text and "," in text:
        return None
    return len(_entries(text))


def _count_sections(text):
    """Count the rulebook sections enumerated on a RULE SECTIONS line: entries that START with a
    section id (`§…`, `R1.2`, `P4`). A comma inside one entry's reason therefore cannot inflate it."""
    if text is None:
        return None
    return sum(1 for part in _entries(text)
               if re.match(r"^(§|\*{0,2}§|[A-Z]?\d+(\.\d+)*\b|[A-Z]\d)", part))


# Each grammar: the canonical shipped form, the ordered segments (regex + human label), the
# internal-contradiction rules, and which phase/lane requires it. `gates` entries are the arithmetic
# conditions the shipped skill text states as BLOCKING.
GRAMMARS = {
    "PREMISE FALSIFIED": {
        "canonical": "PREMISE FALSIFIED: <n> referenced-as-existing source(s) missing — <ref> "
                     "(<ticket line naming it>), …",
        "segments": [
            (rf"(?P<n>{NUM})\s+referenced.as.existing {pl('source')} missing(?:\s*—\s*(?P<refs>.*))?",
             "<n> referenced-as-existing source(s) missing — <ref>, …"),
        ],
        "rules": [], "gates": [],
        "required_at": None,          # conditional: emitted only when PREMISE reports m > 0
        "emitter": "refine, analysis",
    },
    "PREMISE": {
        "canonical": "PREMISE: <r> reference(s) checked | <m> missing | <a> ambiguous "
                     "(surfaced, not blocking)",
        "segments": [
            seg("r", pl("reference") + " checked", "<r> reference(s) checked"),
            seg("m", r"missing", "<m> missing"),
            seg("a", r"ambiguous", "<a> ambiguous (surfaced, not blocking)"),
        ],
        "rules": [
            (lambda c: c["m"] <= c["r"], "m > r — more references missing than were checked"),
            (lambda c: c["a"] <= c["r"], "a > r — more references ambiguous than were checked"),
            (lambda c: c["m"] + c["a"] <= c["r"],
             "m + a > r — missing plus ambiguous exceeds the references checked"),
        ],
        "gates": [],
        "required_at": "refine",
        "emitter": "refine, analysis",
    },
    "RECALL": {
        "canonical": "RECALL: <n> claim(s) surfaced | <s> by symbol | <h> by handle | <a> by area | "
                     "<f> by finding | <r> retired skipped — advisory (blocks nothing)",
        "segments": [
            seg("n", pl("claim") + " surfaced", "<n> claim(s) surfaced"),
            seg("s", r"by symbol", "<s> by symbol"),
            seg("h", r"by handle", "<h> by handle"),
            seg("a", r"by area", "<a> by area"),
            seg("f", r"by finding", "<f> by finding"),
            seg("r", r"retired skipped", "<r> retired skipped — advisory (blocks nothing)"),
        ],
        "rules": [
            (lambda c: c["n"] == c["s"] + c["h"] + c["a"] + c["f"],
             "n != s + h + a + f — the claim TYPE decides ONE recall key, so the four keys partition "
             "the surfaced claims"),
        ],
        "gates": [],
        "required_at": "refine", "lite_required": True,
        "emitter": "refine, analysis, quick",
    },
    "REFINE": {
        "canonical": "REFINE: <U> unresolved surfaced | <a> want-decision asked | "
                     "<b> how-decision resolved+cited | <s> ASSUMED | skip: yes/no",
        "segments": [
            seg("U", r"unresolved surfaced", "<U> unresolved surfaced"),
            seg("a", r"want-decision asked", "<a> want-decision asked"),
            seg("b", r"how-decision resolved\+cited", "<b> how-decision resolved+cited"),
            seg("s", r"ASSUMED", "<s> ASSUMED"),
            (r"skip:\s*(?P<skip>yes|no)\b", "skip: yes/no"),
        ],
        "rules": [
            (lambda c: c["U"] == c["a"] + c["b"],
             "U != a + b — every surfaced decision is classified want-decision OR how-decision, an "
             "exhaustive binary"),
            (lambda c: c["s"] <= c["U"], "s > U — more ASSUMED than decisions surfaced"),
        ],
        "gates": [],
        "required_at": "refine",
        "emitter": "refine",
    },
    "BREAKDOWN": {
        "canonical": "BREAKDOWN: <N> tickets proposed | <N> INVEST self-checks emitted (6 letters each) "
                     "| <f> tickets flagged for re-split",
        "segments": [
            seg("N", r"tickets proposed", "<N> tickets proposed"),
            seg("checks", r"INVEST self-checks emitted",
                "<N> INVEST self-checks emitted (6 letters each)"),
            seg("f", r"tickets flagged for re-split", "<f> tickets flagged for re-split"),
        ],
        "rules": [
            (lambda c: c["N"] == c["checks"],
             "tickets proposed != INVEST self-checks emitted — the check is enumerated PER ticket"),
            (lambda c: c["f"] <= c["N"], "f > N — more tickets flagged for re-split than proposed"),
        ],
        "gates": [],
        "required_at": None, "epic_required": True,
        "emitter": "breakdown",
    },
    "SECTIONS": {
        "canonical": "SECTIONS: <n> found (names) | <n> decomposed | ROWS: C=.. R=.. G=.. AC=..",
        "segments": [
            (rf"(?P<found>{NUM})\s+found(?:\s*\((?P<names>[^)]*)\))?", "<n> found (names)"),
            seg("decomposed", r"decomposed", "<n> decomposed"),
            (rf"ROWS:\s*C=(?P<C>{NUM})\s+R=(?P<R>{NUM})\s+G=(?P<G>{NUM})\s+AC=(?P<AC>{NUM})",
             "ROWS: C=.. R=.. G=.. AC=.."),
        ],
        "rules": [
            (lambda c: c["found"] == c["decomposed"],
             "sections found != sections decomposed — every ticket section maps to >= 1 matrix row"),
        ],
        "text_rules": [
            (lambda c, t: _count_named(t.get("names")) in (None, c["found"]),
             "the count of section names enumerated on the line does not match `<n> found`"),
        ],
        "gates": [],
        "required_at": "analysis",
        "emitter": "analysis",
    },
    "SURFACES": {
        "canonical": "SURFACES: <N> — <surface>, <surface>, …",
        "segments": [
            (rf"(?P<N>{NUM})(?:\s*—\s*(?P<list>.*))?",
             "<N> — <route / overlay / modal / mounted state>, …"),
        ],
        "rules": [],
        "text_rules": [
            (lambda c, t: c["N"] == 0 or _count_named(t.get("list")) in (None, c["N"]),
             "the count of surfaces enumerated on the line does not match `<N>`"),
        ],
        "gates": [],
        "required_at": None, "frontend_only": True,
        "emitter": "analysis",
    },
    "CLARIFICATION": {
        "canonical": "CLARIFICATION: <M> raised | <k> self-resolved (cited) | <j> for human decision",
        "segments": [
            seg("M", r"raised", "<M> raised"),
            seg("k", r"self-resolved", "<k> self-resolved (cited)"),
            seg("j", r"for human decision", "<j> for human decision"),
        ],
        "rules": [
            (lambda c: c["M"] == c["k"] + c["j"],
             "M != k + j — every raised clarification is self-resolved or for a human, an exhaustive "
             "binary"),
        ],
        "gates": [],                  # j > 0 is a legitimate STOP, never a broken gate
        "required_at": "analysis",
        "emitter": "analysis",
    },
    "RULE SECTIONS": {
        "canonical": "RULE SECTIONS: <n> applicable — <k> by change-type | <m> by recalled handle — "
                     "§<id> (<source>) ✅ / N/A (reason), …",
        "segments": [
            (rf"(?P<n>{NUM})\s+applicable\s*—\s*(?P<k>{NUM})\s+by change-type",
             "<n> applicable — <k> by change-type"),
            (rf"(?P<m>{NUM})\s+by recalled handle\s*—\s*(?P<list>.+)",
             "<m> by recalled handle — §<id> (<source>) ✅ / N/A (reason), …"),
        ],
        "rules": [
            (lambda c: c["n"] == c["k"] + c["m"],
             "n != k + m — the applicable set is the UNION of the change-type and recalled-handle "
             "sources, counted once each"),
        ],
        "text_rules": [
            (lambda c, t: _count_sections(t.get("list")) in (None, c["n"]),
             "the count of sections enumerated on the line does not match `<n> applicable`"),
        ],
        # The enumerated tail is a free list; a real doc separates its entries with `|`, the same
        # character the grammar uses between FIELDS. That ambiguity is the shipped grammar's, not the
        # agent's, so the tail is consumed greedily rather than reported as invented fields.
        "greedy_tail": True,
        "gates": [],
        "required_at": "analysis", "lite_required": True,
        "emitter": "analysis, quick",
    },
    "HANDLES": {
        "canonical": "HANDLES: <h> recalled | <t> traced (command + result) | "
                     "<x> does not apply (reason) | <u> unanswered",
        "segments": [
            seg("h", r"recalled", "<h> recalled"),
            seg("t", r"traced", "<t> traced (command + result)"),
            seg("x", r"does not apply", "<x> does not apply (reason)"),
            seg("u", r"unanswered", "<u> unanswered"),
        ],
        "rules": [
            (lambda c: c["h"] == c["t"] + c["x"] + c["u"],
             "h != t + x + u — every recalled handle is traced, closed as does-not-apply, or "
             "unanswered"),
        ],
        "gates": [
            (lambda c: c["u"] == 0,
             "u > 0 — an unanswered recalled handle BLOCKS Gate 2 (design step 4)"),
        ],
        "required_at": "design",
        "emitter": "design",
    },
    "EXCLUSIONS": {
        "canonical": "EXCLUSIONS: <n> recorded | <e> with a checkable expiry | <r> recurring "
                     "(class seen ≥ 3 → discharged/escalated) | <o> with an overdue predecessor",
        "segments": [
            seg("n", r"recorded", "<n> recorded"),
            seg("e", r"with a checkable expiry", "<e> with a checkable expiry"),
            seg("r", r"recurring", "<r> recurring (class seen ≥ 3 → discharged/escalated)"),
            seg("o", r"with an overdue predecessor", "<o> with an overdue predecessor"),
        ],
        "rules": [
            (lambda c: c["e"] <= c["n"], "e > n — more checkable expiries than exclusions recorded"),
            (lambda c: c["r"] <= c["n"], "r > n — more recurring classes than exclusions recorded"),
            (lambda c: c["o"] <= c["n"], "o > n — more overdue predecessors than exclusions recorded"),
        ],
        "gates": [
            (lambda c: c["e"] == c["n"],
             "e != n — an exclusion with no checkable expiry BLOCKS Gate 2 (design step 6)"),
        ],
        "required_at": "design",
        "emitter": "design",
    },
    "CLAIMS": {
        "canonical": "CLAIMS: <c> claim(s) from <e> lesson entr(ies) | T1=<n> T2=<n> T3=<n> T4=<n> "
                     "T5=<n> T6=<n> | <u> unclassified",
        "segments": [
            (rf"(?P<c>{NUM})\s+{pl('claim')} from\s+(?P<e>{NUM})\s+lesson entr(?:y|ies|\(ies\))",
             "<c> claim(s) from <e> lesson entr(ies)"),
            (rf"T1=(?P<T1>{NUM})\s+T2=(?P<T2>{NUM})\s+T3=(?P<T3>{NUM})\s+T4=(?P<T4>{NUM})"
             rf"\s+T5=(?P<T5>{NUM})\s+T6=(?P<T6>{NUM})",
             "T1=<n> T2=<n> T3=<n> T4=<n> T5=<n> T6=<n>"),
            seg("u", r"unclassified", "<u> unclassified"),
        ],
        "rules": [
            (lambda c: c["c"] == sum(c[f"T{i}"] for i in range(1, 7)) + c["u"],
             "c != T1..T6 + u — every claim is classified into exactly one type or counted "
             "unclassified"),
        ],
        "gates": [],
        "required_at": "finalise", "lite_required": True,
        "emitter": "finalise, breakdown",
    },
    "RECURRENCE": {
        "canonical": "RECURRENCE: <n> recurring | <s> superseded (<r> retired) | "
                     "<p> promotion candidate(s)",
        "segments": [
            seg("n", r"recurring", "<n> recurring"),
            (rf"(?P<s>{NUM})\s+superseded(?:\s*\((?P<r>{NUM})\s+retired\))?",
             "<s> superseded (<r> retired)"),
            seg("p", "promotion " + pl("candidate"), "<p> promotion candidate(s)"),
        ],
        "rules": [
            (lambda c: c.get("r", 0) <= c["s"], "r > s — more retired than superseded"),
            (lambda c: c["p"] <= c["n"], "p > n — more promotion candidates than recurring claims"),
        ],
        "gates": [],
        "required_at": "finalise", "lite_required": True,
        "emitter": "finalise",
    },
    "FALSIFY": {
        "canonical": "FALSIFY: <c> candidate(s) checked | <t> still-true (proceed) | "
                     "<f> falsified (BLOCKED) | <u> not cheaply checkable (BLOCKED)",
        "segments": [
            seg("c", pl("candidate") + " checked", "<c> candidate(s) checked"),
            seg("t", r"still-true", "<t> still-true (proceed)"),
            seg("f", r"falsified", "<f> falsified (BLOCKED)"),
            seg("u", r"not cheaply checkable", "<u> not cheaply checkable (BLOCKED)"),
        ],
        "rules": [
            (lambda c: c["c"] == c["t"] + c["f"] + c["u"],
             "c != t + f + u — every candidate checked lands in exactly one of the three outcomes"),
        ],
        "gates": [],
        "required_at": "finalise", "lite_required": True,
        "emitter": "finalise",
    },
    "RECURRING-T2": {
        "canonical": "RECURRING-T2: <n> type-2 claim(s) with seen ≥ 2 | <d> routed to a destination | "
                     "<b> cannot promote (reason) | <l> left in lessons_path",
        "segments": [
            (rf"(?P<n>{NUM})\s+type-2 {pl('claim')} with seen\s*(?:>=|≥)\s*2",
             "<n> type-2 claim(s) with seen ≥ 2"),
            seg("d", r"routed to a destination", "<d> routed to a destination"),
            seg("b", r"cannot promote", "<b> cannot promote (reason)"),
            seg("l", r"left in lessons_path", "<l> left in lessons_path"),
        ],
        "rules": [
            (lambda c: c["n"] == c["d"] + c["b"] + c["l"],
             "n != d + b + l — finalise step 3e states `n` must equal `d + b` with `l` at 0"),
        ],
        "gates": [
            (lambda c: c["l"] == 0,
             "l > 0 — a recurring type-2 claim still reading `stays in lessons_path` BLOCKS finalise"),
        ],
        "required_at": "finalise", "lite_required": True,
        "emitter": "finalise",
    },
    "PROMOTION": {
        "canonical": "PROMOTION: <p> proposed | <k> human-ratified | destinations: <path>, … | "
                     "mango files written: 0",
        "segments": [
            seg("p", r"proposed", "<p> proposed"),
            seg("k", r"human-ratified", "<k> human-ratified"),
            (r"destinations:\s*(?P<destinations>.*)", "destinations: <path>, …"),
            (rf"mango files written:\s*(?P<written>{NUM})", "mango files written: 0"),
        ],
        "rules": [
            (lambda c: c["k"] <= c["p"], "k > p — more ratified promotions than were proposed"),
        ],
        "gates": [
            (lambda c: c["written"] == 0,
             "mango files written != 0 — no lesson, however ratified, edits a mango file"),
        ],
        "required_at": "finalise", "lite_required": True,
        "emitter": "finalise",
    },
    "PROMOTE": {
        "canonical": "PROMOTE: <n> class(es) with recurrence >= 2 | <p> candidate(s) proposed | "
                     "<e> already recorded (skipped) | <b> blocked (reason) | rules written: 0",
        "segments": [
            (rf"(?P<n>{NUM})\s+{pl('class', 'es')} with recurrence\s*(?:>=|≥)\s*2",
             "<n> class(es) with recurrence >= 2"),
            seg("p", pl("candidate") + " proposed", "<p> candidate(s) proposed"),
            seg("e", r"already recorded", "<e> already recorded (skipped)"),
            seg("b", r"blocked", "<b> blocked (reason)"),
            (rf"rules written:\s*(?P<written>{NUM})", "rules written: 0"),
        ],
        "rules": [
            (lambda c: c["n"] == c["p"] + c["e"] + c["b"],
             "n != p + e + b — every class with recurrence >= 2 is proposed, skipped, or blocked"),
        ],
        "gates": [
            (lambda c: c["written"] == 0,
             "rules written != 0 — promote proposes a rule, it never writes one"),
        ],
        "required_at": None,          # a cross-ticket pass, not a lifecycle phase
        "emitter": "promote",
    },
    "RETIRE": {
        "canonical": "RETIRE: <o> offered | <a> retired on the human's answer | "
                     "<s> declined/unanswered | records deleted: 0",
        "segments": [
            seg("o", r"offered", "<o> offered"),
            seg("a", r"retired on the human's answer", "<a> retired on the human's answer"),
            seg("s", r"declined/unanswered", "<s> declined/unanswered"),
            (rf"records deleted:\s*(?P<deleted>{NUM})", "records deleted: 0"),
        ],
        "rules": [
            (lambda c: c["o"] == c["a"] + c["s"],
             "o != a + s — every retirement offered is accepted or declined/unanswered"),
        ],
        "gates": [
            (lambda c: c["deleted"] == 0,
             "records deleted != 0 — retiring never deletes a record; recall skips it, history stays"),
        ],
        "required_at": None,
        "emitter": "promote",
    },
    "DRIFT": {
        "canonical": "DRIFT: <n> entries | <m> tickets",
        "segments": [
            seg("n", r"entries", "<n> entries"),
            seg("m", r"tickets", "<m> tickets"),
        ],
        "rules": [], "gates": [],
        "required_at": None,          # codify is opt-in, not a lifecycle phase
        "emitter": "codify",
    },
    "LEDGER TOTAL": {
        "canonical": "LEDGER TOTAL: <tokens> · top cost driver: <phase/subagent>",
        "segments": [
            (r"(?P<total>[^·]+?)\s*·\s*top cost driver:\s*(?P<driver>.+)",
             "<tokens> · top cost driver: <phase/subagent>"),
        ],
        "rules": [], "gates": [],
        "required_at": "finalise", "lite_required": True,
        "emitter": "finalise",
    },
}

TOKEN_RE = re.compile(r"^([A-Z][A-Z0-9]*(?:[ -][A-Z0-9]+)*):\s*(.+)$")

PASS, FAIL, NOT_CHECKABLE = "PASS", "FAIL", "NOT-CHECKABLE"


def canonical_token(token):
    """The canonical token a near-miss names, or None. `CLARIFICATIONS` -> `CLARIFICATION`."""
    if token in GRAMMARS:
        return token
    squashed = re.sub(r"[^A-Z0-9]", "", token)
    for known in GRAMMARS:
        k = re.sub(r"[^A-Z0-9]", "", known)
        if squashed == k or squashed == k + "S" or squashed + "S" == k:
            return known
    return None


# --------------------------------------------------------------------------- extraction


def working_doc_body(text):
    """The working-doc portion and its 0-based line offset in the file.

    Under `work_doc_mode: embed` the doc sits below the separator line; a doc without one is scanned
    whole (fail-safe to scanning MORE, never less)."""
    idx = text.find(MANGO_SEPARATOR)
    if idx == -1:
        return text, 0
    return text[idx:], text.count("\n", 0, idx)


def _join_wrapped(lines):
    """Rejoin a backtick-quoted counted line that markdown wrapped across source lines.

    Yields (0-based index, joined text). The join is attempted ONLY on a line whose unterminated
    backtick span opens with a counted-line token, so ordinary prose carrying an odd backtick count is
    never allowed to swallow the lines after it.
    """
    opens = re.compile(r"`\s*[A-Z][A-Z0-9]*(?:[ -][A-Z0-9]+)*:")
    out, i = [], 0
    while i < len(lines):
        buf, first, j = lines[i], i, i
        if buf.count("`") % 2 == 1 and opens.search(buf):
            while buf.count("`") % 2 == 1 and j + 1 < len(lines) and j - i < 4:
                j += 1
                buf = buf + " " + lines[j].strip()
        out.append((first, buf))
        i = j + 1
    return out


def find_emissions(text):
    """Every counted-line EMISSION in the doc, as a list of dicts.

    An emission is a line that STARTS with `<TOKEN>:` — inside backticks, or bare when the token is one
    this script has a grammar for. A token merely MENTIONED mid-prose is not an emission: the shipped
    text is explicit that a narrated count is an addition, never a substitute.

    An unknown ALL-CAPS token only qualifies when it is quoted AND its body carries both a `|` field
    separator and a digit — the shape of a counted line. Without that discriminator every `**TIER:**
    full` header field would be reported not-checkable, and a clean doc would produce noise.
    """
    body, offset = working_doc_body(text)
    found = []
    for idx, raw in _join_wrapped(body.splitlines()):
        lineno = offset + idx + 1
        spans = re.findall(r"`([^`]+)`", raw)
        stripped = re.sub(r"^[\s>]*(?:[-*+]|\d+\.)?\s*\*{0,2}", "", raw).rstrip()
        for cand, quoted in [(s, True) for s in spans] + [(stripped, False)]:
            cand = cand.strip().strip("*").strip()
            m = TOKEN_RE.match(cand)
            if not m:
                continue
            token, tail = m.group(1).strip(), m.group(2).strip()
            known = canonical_token(token)
            if known is None:
                if not quoted or token in NOT_COUNTED:
                    continue
                if "|" not in tail or not re.search(r"\d", tail):
                    continue
            found.append({"line": lineno, "token": token, "canonical": known, "body": tail})
            break
    return found


# --------------------------------------------------------------------------- parsing one line


PLACEHOLDER_RE = re.compile(r"<[A-Za-z][A-Za-z0-9 _/+()-]*>|\.\.(?!\d)")


def parse_line(token, body):
    """Match one emission body against its canonical grammar.

    Returns (counts, texts, problems). `problems` is a list of off-grammar findings — an omitted field,
    an invented field, a reordering, or an unfilled template placeholder.
    """
    spec = GRAMMARS[token]
    expected = spec["segments"]
    limit = len(expected) - 1 if spec.get("greedy_tail") else -1
    segments = [s.strip() for s in body.split("|", limit)]
    problems, counts, texts = [], {}, {}

    if PLACEHOLDER_RE.search(body):
        return counts, texts, ["unfilled template placeholder — the line was copied, not emitted"]

    def compile_seg(pattern, last):
        return re.compile("^" + pattern + (r"(?:\s*[—·].*)?$" if last else "$"))

    def absorb(match):
        for key, val in match.groupdict().items():
            if val is None:
                continue
            if re.fullmatch(NUM, val):
                counts[key] = int(val.replace(",", ""))
            else:
                texts[key] = val.strip()

    if len(segments) == len(expected):
        # Positional: one clean message per bad field, and no field is double-reported as invented.
        for idx, (pattern, human) in enumerate(expected):
            m = compile_seg(pattern, idx == len(expected) - 1).match(segments[idx])
            if m:
                absorb(m)
            else:
                problems.append(
                    f"field {idx + 1} off-grammar: expected `{human}`, found `{segments[idx][:70]}`")
        return counts, texts, problems

    problems.append(f"field count off-grammar: the canonical line has {len(expected)} field(s), this "
                    f"one has {len(segments)}")
    used, order = [False] * len(segments), []
    for idx, (pattern, human) in enumerate(expected):
        rx = compile_seg(pattern, idx == len(expected) - 1)
        hit = next(((si, rx.match(s)) for si, s in enumerate(segments)
                    if not used[si] and rx.match(s)), None)
        if hit is None:
            problems.append(f"field omitted: `{human}`")
            continue
        si, m = hit
        used[si], _ = True, order.append(si)
        absorb(m)
    for si, sgm in enumerate(segments):
        if not used[si] and sgm:
            problems.append(f"field invented: `{sgm[:70]}` is not part of the canonical grammar")
    if order and order != sorted(order):
        problems.append("field order changed from the canonical grammar")
    return counts, texts, problems


def contradictions(token, counts, texts):
    """Every internal-contradiction finding for one occurrence. Needs no grammar judgement."""
    spec, out = GRAMMARS[token], []
    for predicate, message in spec.get("rules", []) :
        try:
            if not predicate(counts):
                out.append(message)
        except KeyError:
            pass                      # a field the parse never reached; off-grammar reports that
    for predicate, message in spec.get("text_rules", []):
        try:
            if not predicate(counts, texts):
                out.append(message)
        except (KeyError, TypeError):
            pass
    return out


def broken_gates(token, counts):
    """The arithmetic gate conditions the shipped skill text states as BLOCKING, and their verdict."""
    read, broken = 0, []
    for predicate, message in GRAMMARS[token].get("gates", []):
        try:
            ok = predicate(counts)
        except KeyError:
            continue
        read += 1
        if not ok:
            broken.append(message)
    return read, broken


# --------------------------------------------------------------------------- required set


def read_header(text):
    """Read the doc's own declared phase / TIER / TRACK. Absent -> None, never a guess."""
    body, _ = working_doc_body(text)
    out = {"phase": None, "tier": None, "track": None, "epic": False}
    m = re.search(r"\*\*(?:Current phase|Phase)\s*:?\*\*\s*:?\s*([^\n·|]+)", body)
    if m:
        raw = m.group(1).strip().strip("*").lower()
        for key, val in PHASE_ALIASES.items():
            if re.search(rf"(?<![\w.]){re.escape(key)}(?![\w.])", raw):
                out["phase"] = val
                break
        if out["phase"] is None:
            out["phase"] = next((n for n in PHASES if n in raw), None)
    for key, field in (("tier", "TIER"), ("track", "TRACK")):
        # Both shipped shapes: the template's `- **TIER:** full`, and the backticked `` `TIER: full` ``
        # a real doc writes on a `·`-joined header line.
        for pattern in (rf"\*\*{field}:?\*\*:?\s*(\w+)", rf"`{field}:\s*(\w+)`"):
            m = re.search(pattern, body)
            if m:
                out[key] = m.group(1).strip().lower()
                break
    if re.search(r"INPUT KIND:\s*epic|\bepic path\b", body, re.IGNORECASE):
        out["epic"] = True
    return out


def required_tokens(phase, tier, track, epic):
    """The lines this doc was required to emit, through `phase`. None when the phase is undeclared.

    Keyed on the doc's own lane so the check is never a tax: a `TIER: lite` doc is held only to the two
    reads the lite lane makes plus the learning-loop set, and a backend doc is never held to a
    frontend-only line.
    """
    if phase is None:
        return None
    reached, out = PHASES[: PHASES.index(phase) + 1], []
    for token, spec in GRAMMARS.items():
        if spec.get("epic_required"):
            if epic:
                out.append(token)
            continue
        at = spec.get("required_at")
        if at is None or at not in reached:
            continue
        if tier == "lite" and not spec.get("lite_required"):
            continue
        if spec.get("frontend_only") and (track or "backend") == "backend":
            continue
        out.append(token)
    return out


# --------------------------------------------------------------------------- the check


def doc_fingerprint(text):
    """Byte length plus a short content digest, so a QUOTED verdict belongs to one doc state.

    This does not prove who ran the script — nothing here can. It does make a verdict quoted against a
    doc that has since changed detectable, which is the cheap half of the problem."""
    raw = text.encode("utf-8")
    return f"{len(raw)}B/{hashlib.sha256(raw).hexdigest()[:12]}"


def check_doc(text, phase=None, tier=None, track=None, epic=False, path="<doc>"):
    """Verdict every counted line in one working doc. Returns (lines, exit_status)."""
    header = read_header(text)
    phase = phase or header["phase"]
    tier = tier or header["tier"]
    track = track or header["track"]
    epic = epic or header["epic"]

    emissions = find_emissions(text)
    by_token = {}
    for em in emissions:
        by_token.setdefault(em["canonical"] or em["token"], []).append(em)

    details, gate_read, gate_broken, verdicts, restated = [], 0, [], {}, 0

    for key in sorted(by_token, key=lambda t: by_token[t][0]["line"]):
        occurrences = by_token[key]
        if key not in GRAMMARS:
            verdicts[key] = NOT_CHECKABLE
            details.append(
                f"    {key}: {NOT_CHECKABLE} (line {occurrences[0]['line']}) — mango ships no grammar "
                f"for this line. Counted on its own axis, never passed silently; a line naming an "
                f"artifact mango does not produce is non-closing (see autorun)."
            )
            continue
        restated += max(0, len(occurrences) - 1)
        parsed, bad_all = [], []
        for em in occurrences:
            counts, texts, problems = parse_line(key, em["body"])
            if em["token"] != key:
                problems = [f"token off-grammar: `{em['token']}:` — the canonical token is `{key}:`"] \
                    + problems
            bad = contradictions(key, counts, texts)
            parsed.append((em, counts, problems))
            bad_all.extend((em["line"], message) for message in bad)
        best = min(parsed, key=lambda p: (len(p[2]), p[0]["line"]))
        em, counts, problems = best
        read, broken = broken_gates(key, counts)
        gate_read += read
        gate_broken.extend(f"{key} (line {em['line']}): {msg}" for msg in broken)
        if problems or bad_all:
            verdicts[key] = FAIL
            for message in problems:
                details.append(f"    {key}: {FAIL} (line {em['line']}) — {message}")
            for lineno, message in bad_all:
                details.append(f"    {key}: {FAIL} (line {lineno}) — contradiction: {message}")
        else:
            verdicts[key] = PASS
            details.append(f"    {key}: {PASS} (line {em['line']})")

    required = required_tokens(phase, tier, track, epic)
    missing = [t for t in (required or []) if t not in verdicts]

    notes = []
    # A frontend doc with no SURFACES line: required only for a universal/app-wide requirement, which is
    # a judgement this script does not make. Counted not-checkable — reported, never a silent pass.
    if (track or "backend") != "backend" and "SURFACES" not in verdicts:
        verdicts["SURFACES"] = NOT_CHECKABLE
        notes.append("    SURFACES: NOT-CHECKABLE — absent on a frontend/fullstack doc. It is required "
                     "only for a universal/app-wide requirement, a judgement this script does not make.")

    pending = sorted(t for t, s in GRAMMARS.items()
                     if t not in verdicts and s.get("required_at") and t not in (required or []))

    npass = sum(1 for v in verdicts.values() if v == PASS)
    nfail = sum(1 for v in verdicts.values() if v == FAIL)
    nnc = sum(1 for v in verdicts.values() if v == NOT_CHECKABLE)

    lines = [
        "CHECK-LINES",
        f"  lines    : {len(emissions)} emitted | {npass} pass | {nfail} FAIL | "
        f"{nnc} not-checkable | {len(pending)} pending",
        f"  required : {len(required or [])} required through {phase or 'UNKNOWN'} | "
        f"{len(missing)} MISSING",
        f"  gates    : {gate_read} arithmetic gate condition(s) read | {len(gate_broken)} BROKEN",
        f"  restated : {restated} carried-forward restatement(s), each re-checked for contradiction",
        f"  doc      : {path} | {doc_fingerprint(text)} | phase: {phase or 'UNKNOWN'} | "
        f"TIER: {tier or 'unstated'} | TRACK: {track or 'unstated'}",
    ]
    lines.extend(details)
    lines.extend(notes)
    for token in missing:
        lines.append(
            f"    MISSING {token}: required through {phase} and not emitted anywhere in the doc — "
            f"canonical form: `{GRAMMARS[token]['canonical']}` (emitted by {GRAMMARS[token]['emitter']})")
    for message in gate_broken:
        lines.append(f"    GATE BROKEN {message}")
    if required is None:
        lines.append(
            "    NOT-CHECKABLE: the doc does not declare its phase, so the missing-when-required axis "
            "did not run. That axis is UNVERIFIED, not clean — declare the phase or pass --phase.")
    if pending:
        lines.append(f"    pending (not yet required at {phase}): {', '.join(pending)}")
    if nfail or missing or gate_broken:
        status = 2
    elif nnc or required is None:
        status = 3
    else:
        status = 0
    return lines, status


# --------------------------------------------------------------------------- cli


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd, args = argv[1], argv[2:]

    def opt(name, default=None):
        i = args.index(name) if name in args else -1
        return args[i + 1] if 0 <= i < len(args) - 1 else default

    if cmd == "grammars":
        print("CANONICAL COUNTED-LINE GRAMMARS — one form per line, no variants")
        for token in sorted(GRAMMARS):
            spec = GRAMMARS[token]
            at = spec.get("required_at") or ("epic path" if spec.get("epic_required") else "conditional")
            print(f"  {token}\n    emitted by : {spec['emitter']}\n    required at: {at}\n"
                  f"    canonical  : {spec['canonical']}")
        return 0

    if cmd != "check":
        print(f"check_lines: unknown subcommand '{cmd}'")
        return 1
    if not args or args[0].startswith("--"):
        print("check_lines: check <workdoc> [--phase P] [--tier T] [--track TR] [--epic]")
        return 1

    path, phase = args[0], opt("--phase")
    if phase:
        phase = PHASE_ALIASES.get(phase.strip().lower(), phase.strip().lower())
        if phase not in PHASES:
            print(f"check_lines: unknown --phase (expected one of {', '.join(PHASES)} or 0-5)")
            return 1
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        # Never a pass by default. An unreadable doc is reported plainly and exits non-zero.
        print("CHECK-LINES")
        print("  lines    : 0 emitted | 0 pass | 0 FAIL | 0 not-checkable | 0 pending")
        print(f"  doc      : {path} — CANNOT READ ({exc})")
        print("    NOT-CHECKABLE: the working doc could not be read, so NOTHING was checked. That is "
              "UNVERIFIED, not clean — it never passes by default.")
        return 3
    lines, status = check_doc(text, phase=phase, tier=opt("--tier"), track=opt("--track"),
                              epic="--epic" in args, path=path)
    print("\n".join(lines))
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
