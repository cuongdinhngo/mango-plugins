#!/usr/bin/env python3
"""RUN CONTRACT — write, validate, bind, and seed the DISCLOSURE list.

Stdlib only, no network. The contract is written by THIS script from agent-supplied values in a fixed
grammar, and parsed back before the run starts: if it does not parse, the run does not start.

What this script guarantees and what it does not:

  * GUARANTEED — the contract is well-formed and internally consistent: every condition carries a
    statement, a check, a `force-broken` case and a `force-holding` case; the three floor conditions
    are present and are the shipped ones; no `${PLACEHOLDER}` survives past its binding phase.
  * NOT GUARANTEED — that any recorded value is TRUE. Machine-writing guarantees the grammar, not the
    facts. So every value that CAN be derived is derived by running a command and recording its real
    output; everything else is marked `agent-claim (unchecked)` and is carried into DISCLOSURE.

Subcommands
  write            <spec.json> [--repo DIR]   emit a contract, deriving every derivable value
  validate         <contract>  --phase t0|gate2|close
  bind             <contract>  NAME=VALUE ...  --out FILE
  disclosure-seed  <contract>

Exit codes: 0 ok · 2 the contract does not parse / refuses to bind · 1 usage or I/O error.
"""

import json
import re
import subprocess
import sys

GRAMMAR_VERSION = "RUN CONTRACT v1"

HEADER_KEYS = [
    "key",
    "started",
    "plugin-version",
    "plugin-path",
    "repo",
    "base",
    "branch",
    "remote",
    "merge-strategy",
    "challenger",
    "call-ceiling",
    "per-call-estimate",
    "ceiling-source",
    "token-budget",
]

# Every condition declares these SIX fields. `force-broken` and `force-holding` are mandatory GRAMMAR
# FIELDS, not report columns: a condition missing either does not parse, so an unforceable condition
# can never reach RECONCILE to be counted.
CONDITION_KEYS = ["statement", "origin", "derived-by", "value", "check", "force-broken", "force-holding"]

# The fixed floor — three conditions the agent may not author, may not rename, and may not drop.
FLOOR = {
    "PR-EXISTS": "the PR exists and its state is readable",
    "TREE-COMPARISON": "no commit landed on the branch beyond what the PR carries (tree comparison)",
    "LOCAL-HEAD-PUSHED": "nothing is stranded on this machine: local branch head == the remote's",
}

UNBOUND_RE = re.compile(r"UNBOUND \$\{[A-Z][A-Z0-9_]*\}")
AGENT_CLAIM = "agent-claim (unchecked)"
CONDITION_ID_RE = re.compile(r"^[A-Z][A-Z0-9-]*$")


class ContractError(Exception):
    """The contract does not parse. Carries every reason, not just the first."""

    def __init__(self, reasons):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


def sh(command, repo=None, timeout=120):
    """Run a shell command; return (exit_status, output). Never raises."""
    try:
        proc = subprocess.run(
            command, shell=True, cwd=repo, capture_output=True, text=True, timeout=timeout
        )
        return proc.returncode, (proc.stdout + proc.stderr).strip()
    except Exception as exc:  # noqa: BLE001 — a broken command is data, never a crash
        return 127, f"command did not run: {exc}"


# --------------------------------------------------------------------------- parse


def parse(text):
    """Parse a contract into (header, [conditions]). Raises ContractError with every reason."""
    reasons = []
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln and not ln.startswith("#")]
    if not lines:
        raise ContractError(["the contract is empty"])
    if lines[0] != GRAMMAR_VERSION:
        raise ContractError([f"line 1 must be exactly '{GRAMMAR_VERSION}', found '{lines[0]}'"])
    if lines[-1] != "END RUN CONTRACT":
        reasons.append("the contract must end with 'END RUN CONTRACT'")

    header = {}
    conditions = []
    current = None
    for raw in lines[1:]:
        if raw == "END RUN CONTRACT":
            if current is not None:
                reasons.append(f"CONDITION {current['id']} is not closed by 'END CONDITION'")
            continue
        if raw.startswith("CONDITION "):
            if current is not None:
                reasons.append(f"CONDITION {current['id']} is not closed by 'END CONDITION'")
            cid = raw[len("CONDITION "):].strip()
            if not CONDITION_ID_RE.match(cid):
                reasons.append(f"'{cid}' is not a valid CONDITION id (UPPER-KEBAB)")
            if any(c["id"] == cid for c in conditions):
                reasons.append(f"CONDITION {cid} is declared more than once")
            current = {"id": cid, "fields": {}}
            continue
        if raw == "END CONDITION":
            if current is None:
                reasons.append("'END CONDITION' with no open CONDITION")
                continue
            for key in CONDITION_KEYS:
                if key not in current["fields"]:
                    reasons.append(
                        f"CONDITION {current['id']} is missing the mandatory field '{key}'"
                    )
            conditions.append(current)
            current = None
            continue
        if ":" not in raw:
            reasons.append(f"line is neither a block marker nor a 'key: value' pair: '{raw}'")
            continue
        key, _, value = raw.partition(":")
        key = key.strip()
        value = value.strip()
        if current is None:
            if key not in HEADER_KEYS:
                reasons.append(f"unknown header key '{key}'")
            elif key in header:
                reasons.append(f"header key '{key}' appears more than once")
            else:
                header[key] = value
        else:
            if key not in CONDITION_KEYS:
                reasons.append(f"CONDITION {current['id']}: unknown field '{key}'")
            elif key in current["fields"]:
                reasons.append(f"CONDITION {current['id']}: field '{key}' appears more than once")
            else:
                current["fields"][key] = value

    for key in HEADER_KEYS:
        if key not in header:
            reasons.append(f"the header is missing '{key}'")
    if reasons:
        raise ContractError(reasons)
    return header, conditions


def check_floor(header, conditions):
    """The three floor conditions must be present, marked `origin: floor`, and shaped as shipped."""
    reasons = []
    by_id = {c["id"]: c for c in conditions}
    for cid, statement in FLOOR.items():
        cond = by_id.get(cid)
        if cond is None:
            reasons.append(f"floor condition {cid} is missing — the agent may not drop it")
            continue
        if cond["fields"].get("origin") != "floor":
            reasons.append(f"floor condition {cid} must be marked 'origin: floor'")
        if statement.split("(")[0].strip()[:12].lower() not in cond["fields"].get("statement", "").lower():
            reasons.append(
                f"floor condition {cid} does not state the shipped requirement: {statement}"
            )

    tree = by_id.get("TREE-COMPARISON")
    if tree is not None:
        chk = tree["fields"].get("check", "")
        if not UNBOUND_RE.search(chk):
            if "git diff" not in chk or "--quiet" not in chk:
                reasons.append(
                    "TREE-COMPARISON must be a TREE comparison — `git diff --quiet <base> <branch> "
                    "-- <paths>` — never a content grep for text named at t0"
                )
            if re.search(r"\bgrep\b", chk):
                reasons.append(
                    "TREE-COMPARISON must not grep for content: a post-merge correction is unnamed "
                    "at t0, so a grep returns HOLDING on the very incident this condition catches"
                )
            if re.search(r"merge-base|--is-ancestor", chk):
                reasons.append(
                    "TREE-COMPARISON must not use an ancestry predicate (`merge-base --is-ancestor`) "
                    "— it is a false-red under a squash merge"
                )
    head = by_id.get("LOCAL-HEAD-PUSHED")
    if head is not None:
        chk = head["fields"].get("check", "")
        if not UNBOUND_RE.search(chk):
            if "rev-parse" not in chk:
                reasons.append(
                    "LOCAL-HEAD-PUSHED must compare the two heads with `git rev-parse` "
                    "(local branch head vs the remote's)"
                )
            remote = header.get("remote", "origin")
            if f"{remote}/" not in chk:
                reasons.append(
                    f"LOCAL-HEAD-PUSHED must name the remote ref ({remote}/<branch>) — a local-only "
                    "comparison cannot see what never left this machine"
                )
            if "--verify" not in chk:
                reasons.append(
                    "LOCAL-HEAD-PUSHED must resolve each ref with `git rev-parse --verify` before "
                    "comparing: when BOTH lookups fail, a bare `test \"$(...)\" = \"$(...)\"` "
                    "compares empty to empty and reports HOLDING — a false green exactly where the "
                    "branch does not exist"
                )
    pr = by_id.get("PR-EXISTS")
    if pr is not None:
        if pr["fields"].get("check", "") in ("", AGENT_CLAIM):
            reasons.append(
                "PR-EXISTS must carry a real command whose exit status is the verdict — RECONCILE "
                "runs it; an agent's word that the PR exists is not the condition"
            )
    return reasons


def check_phase(conditions, phase):
    """Phase rules. `t0` tolerates UNBOUND placeholders; `gate2` and `close` refuse every survivor."""
    reasons = []
    for cond in conditions:
        fields = cond["fields"]
        if UNBOUND_RE.search(fields.get("statement", "")):
            reasons.append(f"CONDITION {cond['id']}: 'statement' may never be UNBOUND")
        if fields.get("origin") not in ("floor", "agent"):
            reasons.append(f"CONDITION {cond['id']}: 'origin' must be 'floor' or 'agent'")
        for key in ("value", "check", "force-broken", "force-holding"):
            val = fields.get(key, "")
            if "UNBOUND" in val and not UNBOUND_RE.search(val):
                reasons.append(
                    f"CONDITION {cond['id']}: '{key}' says UNBOUND but names no ${{PLACEHOLDER}}"
                )
            if phase in ("gate2", "close") and UNBOUND_RE.search(val):
                reasons.append(
                    f"CONDITION {cond['id']}: '{key}' is still UNBOUND at {phase} — "
                    "re-validation refuses a surviving placeholder"
                )
    return reasons


def validate(text, phase):
    """Full validation. Returns the parsed (header, conditions) or raises ContractError."""
    header, conditions = parse(text)
    reasons = check_floor(header, conditions) + check_phase(conditions, phase)
    if header.get("challenger") not in ("on", "off"):
        reasons.append("header 'challenger' must be exactly 'on' or 'off'")
    ceiling = header.get("call-ceiling", "")
    if ceiling != "unknown" and not re.match(r"^\d+$", ceiling):
        reasons.append("header 'call-ceiling' must be an integer or the literal 'unknown'")
    if reasons:
        raise ContractError(reasons)
    return header, conditions


# --------------------------------------------------------------------------- write


def render(header, conditions):
    out = [GRAMMAR_VERSION]
    for key in HEADER_KEYS:
        out.append(f"  {key}: {header.get(key, '')}")
    for cond in conditions:
        out.append(f"  CONDITION {cond['id']}")
        for key in CONDITION_KEYS:
            out.append(f"    {key}: {cond['fields'].get(key, '')}")
        out.append("  END CONDITION")
    out.append("END RUN CONTRACT")
    return "\n".join(out) + "\n"


def write(spec, repo=None):
    """Build a contract from an agent-supplied spec, DERIVING every derivable value by command."""
    header = {key: str(spec.get(key, "")) for key in HEADER_KEYS}
    conditions = []
    for raw in spec.get("conditions", []):
        fields = {key: str(raw.get(key, "")) for key in CONDITION_KEYS}
        derived_by = fields.get("derived-by", "")
        if derived_by and derived_by != AGENT_CLAIM and not UNBOUND_RE.search(derived_by):
            status, output = sh(derived_by, repo=repo)
            first = output.splitlines()[0] if output.splitlines() else ""
            fields["value"] = f"{first} (exit {status})"
        conditions.append({"id": str(raw.get("id", "")), "fields": fields})

    present = {c["id"] for c in conditions}
    for cid in FLOOR:
        if cid not in present:
            raise ContractError(
                [f"floor condition {cid} is missing from the spec — it is shipped, not authored"]
            )
    return render(header, conditions)


# --------------------------------------------------------------------------- bind


def bind(text, bindings, phase="gate2"):
    """Substitute `UNBOUND ${NAME}` → value, then RE-VALIDATE and refuse every survivor."""
    bound = text
    for name, value in bindings.items():
        bound = bound.replace("UNBOUND ${%s}" % name, value)
    validate(bound, phase)  # raises on any survivor
    return bound


# --------------------------------------------------------------------------- disclosure


def disclosure_seed(header, conditions):
    """The machine-writable floor of DISCLOSURE. Everything else only the agent knows."""
    out = ["DISCLOSURE"]
    state = header.get("challenger", "")
    if state == "off":
        out.append(
            "  1. CHALLENGER: OFF — waived by `--no-challenger`. Nothing independent re-derived the "
            "requirements from the raw ticket. A clean result below is not evidence of independence."
        )
    else:
        out.append("  1. CHALLENGER: ON — the ticket-blind challenger ran.")
    claims = [c for c in conditions if c["fields"].get("derived-by") == AGENT_CLAIM]
    out.append(f"  2. UNCHECKED AGENT CLAIMS: {len(claims)} — no command derived these values.")
    for cond in claims:
        out.append(f"       - {cond['id']}: {cond['fields'].get('value', '')}")
    if header.get("call-ceiling") == "unknown":
        out.append("  3. BUDGET: call-count ceiling unknown — no ledger history for this tier.")
    else:
        out.append(
            f"  3. BUDGET: call-count ceiling {header.get('call-ceiling')} "
            f"(proxy, per-call estimate {header.get('per-call-estimate')}, "
            f"source: {header.get('ceiling-source')}) — a proxy, not a measurement."
        )
    out.append(
        "  4. This list is the ONE artifact nothing can check: only the agent knows what it chose "
        "not to verify. A near-empty list on a long run is a reason to distrust the run, not to "
        "trust it. Every line below this one is appended by the agent."
    )
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- cli


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    args = argv[2:]

    def opt(name, default=None):
        return args[args.index(name) + 1] if name in args else default

    try:
        if cmd == "write":
            spec = json.loads(open(args[0], encoding="utf-8").read())
            sys.stdout.write(write(spec, repo=opt("--repo")))
            return 0
        if cmd == "validate":
            text = open(args[0], encoding="utf-8").read()
            phase = opt("--phase", "t0")
            validate(text, phase)
            print(f"RUN CONTRACT: parses at phase {phase}")
            return 0
        if cmd == "bind":
            text = open(args[0], encoding="utf-8").read()
            bindings = dict(
                a.split("=", 1) for a in args[1:] if "=" in a and not a.startswith("--")
            )
            bound = bind(text, bindings, opt("--phase", "gate2"))
            out = opt("--out")
            if out:
                open(out, "w", encoding="utf-8").write(bound)
            else:
                sys.stdout.write(bound)
            return 0
        if cmd == "disclosure-seed":
            text = open(args[0], encoding="utf-8").read()
            header, conditions = parse(text)
            sys.stdout.write(disclosure_seed(header, conditions))
            return 0
    except ContractError as exc:
        print("RUN CONTRACT: DOES NOT PARSE — the run does not start.")
        for reason in exc.reasons:
            print(f"  - {reason}")
        return 2
    except OSError as exc:
        print(f"run_contract: {exc}")
        return 1
    print(f"run_contract: unknown subcommand '{cmd}'")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
