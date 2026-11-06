#!/usr/bin/env python3
"""List every tool call denied by the permission allowlist during one e2e dispatch.

    python3 tests/e2e/denials.py <result.json> [--projects <dir>]

result.json is the dispatch's `claude -p --output-format json` output. Its `permission_denials`
covers the main session only, so the session's transcripts under ~/.claude/projects are read as well:
the main one and every subagent's (the challenger, reviewer, implementer, explorers). One line per
denial, `<agent>: <tool>: <command or input>`. No output means no denial. Exit 0 always: it reports.
"""
import json
import sys
from pathlib import Path

DENIED = "has been denied"


def is_denial(name, body, is_error):
    """A permission refusal, not a command that ran and failed: a refused Bash call comes back as an
    error that never ran, so it carries no `Exit code` line."""
    if DENIED in body:
        return True
    return bool(is_error) and name == "Bash" and not body.startswith("Exit code") \
        and "timed out" not in body


def agent_label(rows, default):
    for r in rows:
        if r.get("type") == "user":
            c = r.get("message", {}).get("content")
            text = c if isinstance(c, str) else " ".join(
                x.get("text", "") for x in (c or []) if isinstance(x, dict))
            return " ".join(text.split())[:60] or default
    return default


def denials(path, label=None):
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    label = label or agent_label(rows, path.stem)
    uses, out = {}, []
    for r in rows:
        content = r.get("message", {}).get("content")
        if not isinstance(content, list):
            continue
        for x in content:
            if not isinstance(x, dict):
                continue
            if x.get("type") == "tool_use":
                uses[x.get("id")] = (x.get("name"), x.get("input") or {})
            elif x.get("type") == "tool_result" and x.get("tool_use_id") in uses:
                body = x.get("content")
                body = body if isinstance(body, str) else json.dumps(body)
                name, inp = uses[x["tool_use_id"]]
                if is_denial(name, body, x.get("is_error")):
                    why = " ".join(body.split())[:90]
                    shown = inp.get("command") or inp.get("file_path") or json.dumps(inp)
                    out.append(f"{label}: {name}: {' '.join(str(shown).split())[:160]}  [{why}]")
    return out


def main(argv):
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 0
    projects = Path.home() / ".claude" / "projects"
    if "--projects" in argv:
        projects = Path(argv[argv.index("--projects") + 1])
    try:
        result = json.load(open(argv[0], encoding="utf-8"))
    except (OSError, ValueError):
        print(f"denials: no JSON result at {argv[0]}")
        return 0
    session = result.get("session_id")
    lines = []
    found = sorted(projects.glob(f"*/{session}.jsonl")) if session else []
    if not found:
        for d in result.get("permission_denials") or []:
            inp = d.get("tool_input") or {}
            lines.append(f"main: {d.get('tool_name')}: {' '.join(str(inp.get('command', inp)).split())[:200]}")
        if session:
            lines.append(f"denials: transcript for session {session} not found under {projects}; subagents not read")
    for main_t in found:
        lines += denials(main_t, "main")
        for sub in sorted((main_t.parent / session / "subagents").glob("*.jsonl")):
            lines += denials(sub)
    print("\n".join(lines)) if lines else None
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
