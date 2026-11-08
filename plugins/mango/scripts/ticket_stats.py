#!/usr/bin/env python3
"""TICKET-STATS — one aggregate row from a working doc, read in place.

Stdlib only, no network, READ-ONLY. Reads ONE working doc and prints ONE row of aggregate fields:

  COST: lane=<quick|full|autorun|unknown> scope=<S|M|L>/<files> dispatches=<n> dispatch_tokens=<n>
        unmeasured=<k> session_tokens=<n|unknown> minutes=<n|unknown> gates=<n>
        not_met=<real|unknown>/<raised> mango=<x.y.z|unknown> date=<YYYY-MM-DD|unknown>

AGGREGATE ONLY. The row carries counts, tokens, minutes, a lane, a scope letter, a version and a date
— never a ticket key, a path, a name or any text from the doc. Every field is built from a parsed
number or a fixed word and must match its pattern in FIELDS before it is printed; a value that does
not is printed as `unknown`. No message this script prints quotes the doc. The doc's data stays in
the project: a human reads the row before it goes anywhere else.

Where each field comes from (the doc's own records; nothing is estimated):
  lane            `TIER: lite` -> quick. `TIER: full` with a `DISCLOSURE` line under `## Phase 5` ->
                  autorun; otherwise full. `--lane` overrides it.
  scope           the `SCOPE:` letter / the number of files on the `Reviewed at` line.
  dispatches      rows of the `## Cost ledger` table.
  dispatch_tokens the sum of their Tokens cells; unmeasured = cells marked `unmeasured`.
  gates           `Gate <n> status:` lines that read `cleared` (in autorun, closed on artifacts).
  not_met         raised = `not met` on the first `CHALLENGER VERDICT` line; `n/a` on the lite lane
                  with none. Real is a human judgement: `--real` (<= raised), else 0 when raised is 0,
                  else `unknown`.
  date            the `Last updated:` date in Session status.
  session_tokens, minutes, mango   not in the doc: `--session-tokens`, `--minutes`, `--mango`, else
                  `unknown`. Never estimated.

Usage
  ticket_stats.py <workdoc> [--row] [--lane quick|full|autorun] [--session-tokens <n>]
                  [--minutes <n>] [--real <n>] [--mango <x.y.z>]

  --row  prints the row as a docs/COST.md table row instead of the COST line.

Exit codes: 0 every field read from the doc was read · 3 the row printed, but a field the doc should
carry (lane, scope, ledger, gates, not_met, date) was unreadable and is `unknown` · 1 usage, an
invalid option value, or an unreadable file.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_lines import MANGO_SEPARATOR, working_doc_body  # noqa: E402  the one reading of `embed`

UNKNOWN = "unknown"

# (key, docs/COST.md column header, the only shape the value may take). The single source for both
# this script and validate.py's check of docs/COST.md.
FIELDS = (
    ("lane", "Lane", r"quick|full|autorun|unknown"),
    ("scope", "Scope (S/M/L / files)", r"(S|M|L|unknown)/(\d+|unknown)"),
    ("dispatches", "Dispatches", r"\d+|unknown"),
    ("dispatch_tokens", "Dispatch tokens", r"\d+|unknown"),
    ("unmeasured", "Unmeasured", r"\d+|unknown"),
    ("session_tokens", "Session tokens", r"\d+|unknown"),
    ("minutes", "Minutes", r"\d+|unknown"),
    ("gates", "Gates cleared", r"\d+|unknown"),
    ("not_met", "Not met (real/raised)", r"(\d+|unknown)/(\d+|unknown)|n/a"),
    ("mango", "mango", r"\d+\.\d+\.\d+|unknown"),
    ("date", "Date", r"\d{4}-\d{2}-\d{2}|unknown"),
)
PATTERNS = {key: re.compile(rf"(?:{pattern})\Z") for key, _, pattern in FIELDS}
FROM_DOC = ("lane", "scope", "dispatches", "dispatch_tokens", "unmeasured", "gates", "not_met", "date")

# --------------------------------------------------------------------------- doc reading


def sections(text):
    """`## ` heading text -> the lines under it, up to the next `## ` heading. The header zone is ''."""
    out, name = {"": []}, ""
    for line in text.splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            out.setdefault(name, [])
        else:
            out[name].append(line)
    return out


def section(secs, prefix):
    return next((lines for name, lines in secs.items() if name.startswith(prefix)), [])


def header_value(header, label):
    """The first word after `**<label>:**` (or in `` `<label>: x` ``) in the header zone, or None."""
    for line in header:
        m = (re.search(rf"\*\*{label}:\*\*\s*([A-Za-z0-9.]+)", line)
             or re.search(rf"`{label}:\s*([A-Za-z0-9.]+)`", line))
        if m:
            rest = line[m.end():].lstrip()
            # The template's own placeholder (`S | M | L`) is not a value.
            return None if rest.startswith("|") else m.group(1)
    return None


def table_rows(lines):
    """Data rows of the first markdown table in `lines`, as lists of stripped cells."""
    rows, seen_sep = [], False
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if seen_sep:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells if c) and any(cells):
            seen_sep = True
            continue
        if seen_sep and any(cells):
            rows.append(cells)
    return rows


def read_ledger(lines):
    """(dispatches, tokens, unmeasured) from the Cost ledger table; tokens None if a cell is unreadable."""
    rows = table_rows(lines)
    if not lines or not any(line.strip().startswith("|") for line in lines):
        return None, None, None
    total, unmeasured, readable = 0, 0, True
    for cells in rows:
        cell = cells[3] if len(cells) > 3 else ""
        number = cell.replace(",", "").replace("_", "")
        if re.fullmatch(r"\d+", number):
            total += int(number)
        elif cell.lower().startswith("unmeasured"):
            unmeasured += 1
        else:
            readable = False
    return len(rows), (total if readable else None), unmeasured


def read_files(review):
    for line in review:
        if "Reviewed at" in line and "reviewed files:" in line:
            listed = line.split("reviewed files:", 1)[1]
            return len(re.findall(r"`[^`]+`", listed)) or None
    return None


def read_raised(review):
    for line in review:
        m = re.search(r"CHALLENGER VERDICT:.*?\|\s*(\d+)\s+not met\b", line)
        if m:
            return int(m.group(1))
    return None


def read_date(status):
    for line in status:
        if "Last updated:" in line:
            m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", line)
            return m.group(1) if m else None
    return None


def stats(text, lane=None, session_tokens=None, minutes=None, real=None, mango=None):
    """The row's fields (each a string matching FIELDS) and the doc-derived keys left unknown."""
    # Under `work_doc_mode: embed` the working doc is the part below the separator; the ticket's own
    # `## ` sections above it are never read.
    body = working_doc_body(text)[0]
    if MANGO_SEPARATOR in text:
        body = body.split("\n", 1)[-1]          # the separator line itself is not the header
    secs = sections(body)
    header = secs[""]
    tier = header_value(header, "TIER")
    phase5 = section(secs, "Phase 5")
    review = section(secs, "Phase 4")
    if lane is None:
        if tier == "lite":
            lane = "quick"
        elif tier == "full":
            disclosed = any(re.match(r"[\s>#*`-]*DISCLOSURE\b", line) for line in phase5)
            lane = "autorun" if disclosed else "full"
    scope = header_value(header, "SCOPE")
    files = read_files(review)
    dispatches, tokens, unmeasured = read_ledger(section(secs, "Cost ledger"))
    gates = sum(1 for line in text.splitlines()
                if re.match(r"\s*-\s*\*\*Gate \w+ status:\*\*\s*cleared\b", line))
    gate_lines = any(re.match(r"\s*-\s*\*\*Gate \w+ status:\*\*", line) for line in text.splitlines())
    raised = read_raised(review)
    if raised is None:
        not_met = "n/a" if lane == "quick" else None
    else:
        if real is None:
            real = 0 if raised == 0 else UNKNOWN
        not_met = f"{real}/{raised}"
    row = {
        "lane": lane,
        "scope": f"{scope if scope in ('S', 'M', 'L') else UNKNOWN}/{files if files else UNKNOWN}",
        "dispatches": dispatches,
        "dispatch_tokens": tokens,
        "unmeasured": unmeasured,
        "session_tokens": session_tokens,
        "minutes": minutes,
        "gates": gates if gate_lines else None,
        "not_met": not_met,
        "mango": mango,
        "date": read_date(section(secs, "Session status")),
    }
    fallback = {"scope": f"{UNKNOWN}/{UNKNOWN}", "not_met": f"{UNKNOWN}/{UNKNOWN}"}
    unread = []
    for key, _, _ in FIELDS:
        value = UNKNOWN if row[key] is None else str(row[key])
        if not PATTERNS[key].match(value):
            value = fallback.get(key, UNKNOWN)
        if key in FROM_DOC and UNKNOWN in value:
            unread.append(key)
        row[key] = value
    return row, unread


def cost_line(row):
    return "COST: " + " ".join(f"{key}={row[key]}" for key, _, _ in FIELDS)


def table_row(row):
    return "| " + " | ".join(row[key] for key, _, _ in FIELDS) + " |"


def header_row():
    return "| " + " | ".join(head for _, head, _ in FIELDS) + " |"


# --------------------------------------------------------------------------- cli

OPTIONS = {
    "--lane": r"quick|full|autorun",
    "--session-tokens": r"\d+",
    "--minutes": r"\d+",
    "--real": r"\d+",
    "--mango": r"\d+\.\d+\.\d+",
}


def main(argv):
    args = argv[1:]
    as_row = "--row" in args
    args = [a for a in args if a != "--row"]
    values, doc = {}, None
    i = 0
    while i < len(args):
        if args[i] in OPTIONS:
            if i + 1 >= len(args) or not re.fullmatch(OPTIONS[args[i]], args[i + 1]):
                print(f"ticket_stats: {args[i]} needs a value of the form {OPTIONS[args[i]]}")
                return 1
            values[args[i]] = args[i + 1]
            i += 2
        elif doc is None and not args[i].startswith("--"):
            doc, i = args[i], i + 1
        else:
            print(__doc__)
            return 1
    if doc is None:
        print(__doc__)
        return 1
    try:
        with open(doc, encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError):
        print("ticket_stats: cannot read the working doc")
        return 1
    row, unread = stats(
        text,
        lane=values.get("--lane"),
        session_tokens=values.get("--session-tokens"),
        minutes=values.get("--minutes"),
        real=values.get("--real"),
        mango=values.get("--mango"),
    )
    raised = row["not_met"].split("/")[-1]
    if "--real" in values and raised.isdigit() and int(values["--real"]) > int(raised):
        print("ticket_stats: --real cannot exceed the raised `not met` count")
        return 1
    print(table_row(row) if as_row else cost_line(row))
    if unread:
        print(f"  unread : {', '.join(unread)} (not found in the doc; printed as unknown)")
        return 3
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
