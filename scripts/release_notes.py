#!/usr/bin/env python3
"""Print the release version or its CHANGELOG entry, for .github/workflows/release.yml.

    release_notes.py version          -> the version in plugins/mango/.claude-plugin/plugin.json
    release_notes.py notes [VERSION]  -> the body of that version's `## [VERSION]` CHANGELOG entry

Exits 1 (and prints nothing on stdout) when the version or its entry is missing or empty, so the
workflow cannot publish a release with no notes. Stdlib only.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_JSON = ROOT / "plugins" / "mango" / ".claude-plugin" / "plugin.json"
CHANGELOG = ROOT / "plugins" / "mango" / "CHANGELOG.md"


def plugin_version():
    return json.loads(PLUGIN_JSON.read_text(encoding="utf-8")).get("version", "")


def changelog_entry(version, text=None):
    """Body of the `## [version]` entry, up to the next `## [` heading; '' when absent."""
    if text is None:
        text = CHANGELOG.read_text(encoding="utf-8")
    m = re.search(r"^## \[" + re.escape(version) + r"\][^\n]*\n(.*?)(?=^## \[|\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def main(argv):
    if not argv or argv[0] not in ("version", "notes"):
        sys.stderr.write(__doc__)
        return 2
    version = plugin_version()
    if argv[0] == "version":
        if not version:
            sys.stderr.write("release_notes: plugin.json has no version\n")
            return 1
        print(version)
        return 0
    version = argv[1] if len(argv) > 1 else version
    body = changelog_entry(version)
    if not body:
        sys.stderr.write(f"release_notes: CHANGELOG.md has no non-empty entry for [{version}]\n")
        return 1
    sys.stdout.reconfigure(encoding="utf-8")
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
