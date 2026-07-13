#!/usr/bin/env python3
"""Deterministic, stdlib-only validator for the mango-plugins marketplace.

No network, no auth, no third-party deps. Parses every JSON file, validates the
marketplace and plugin manifests, and checks that every skill/agent markdown file
carries `name` + `description` frontmatter. Prints a count of checks run and exits
non-zero on any failure (listing each one).
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+([-+][0-9A-Za-z.\-]+)*$")
# Names a third party may not claim for a marketplace.
RESERVED_NAMES = {
    "anthropic",
    "claude",
    "claude-code",
    "claude-code-plugins",
    "claude-plugins-official",
    "anthropic-marketplace",
    "anthropic-plugins",
    "agent-skills",
}

# Skill-contract assertions: each skill body MUST contain its load-bearing tokens
# (case-insensitive regex). This guards that an edit cannot quietly drop the
# counted, gate-blocking artifact a skill is responsible for.
SKILL_CONTRACTS = {
    "analysis": [r"SECTIONS:", r"CLARIFICATION:", r"AC validation", r"Gate 1", r"denominator", r"for each", r"TRACK", r"SURFACES", r"falsifiable", r"manual-check", r"baseline", r"uncodified", r"ratif"],
    "design": [r"proving test", r"Gate 2", r"risk layer", r"Assumptions", r"coverage-gap", r"layer-match", r"block", r"DESIGN\.md", r"data-core", r"responsive", r"blast[ -]radius"],
    "execute": [r"verification sweep", r"reformat", r"stuck", r"design[ -]invalidat", r"token-first", r"pointer", r"render", r"proof[ -]manifest", r"ui-proof-scaffold", r"(per|each) clause", r"format[ -]scope", r"approved design", r"both axes", r"baseline"],
    "review": [r"reviewer", r"challenger", r"not clean", r"coverage-gap", r"item-by-item", r"per-item", r"layer-match", r"Reviewed at", r"a11y", r"DESIGN\.md", r"touch-target", r"proof[ -]manifest", r"surfaces proven", r"conditional", r"verify-only", r"baseline", r"reuse", r"only the proof affected", r"main[ -]loop", r"re-?dispatch", r"changed scope", r"bookkeeping", r"exempt", r"carve-?out"],
    "finalise": [r"dry-run", r"per[- ]action", r"durable lesson", r"checklist", r"stale", r"beyond the reviewed set", r"exempt", r"dispatch[ -]only", r"not measured", r"rtk gain", r"dispatch[ -]count", r"ledger complet", r"content", r"token value", r"unmeasured", r"push", r"shared ref"],
    "solve": [r"Session status", r"self-approve", r"TIER", r"design[ -]invalidat", r"outgrew", r"per dispatch", r"unmeasured \(blocking retrieval\)"],
    "quick": [r"proving test", r"combined gate", r"stuck"],
    "doctor": [r"running[ -]version", r"base path", r"\$\{CLAUDE_PLUGIN_ROOT\}"],
    "version-check": [r"update_check_url", r"never updates", r"/plugin", r"plugin\.json"],
    "codify": [r"count", r"PROVISIONAL", r"ratif", r"author", r"recommend", r"uncodified"],
    "budget": [r"[Dd]etect", r"[Ii]nform", r"recorded", r"never.{0,15}install", r"depend",
               r"RTK", r"[Cc]aveman", r"safety axis", r"degrade clean", r"PROVISIONAL",
               r"non-critic-only", r"descriptive", r"wire", r"you must run this",
               r"dispatch-scoped", r"rtk gain"],
}

# Critic agents whose output must never be terse-compressed. Each brief MUST carry the
# Caveman-critic guardrail so a token optimizer cannot strip the evidence a gate relies on.
CRITIC_AGENTS = ["reviewer", "reviewer-max", "challenger"]

failures = []
checks = 0


def check(condition, message):
    """Record one check; remember the message if it fails."""
    global checks
    checks += 1
    if not condition:
        failures.append(message)
    return bool(condition)


def load_json(path):
    """Parse JSON, counting it as a check. Returns the object or None."""
    global checks
    checks += 1
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        failures.append(f"{path.relative_to(ROOT)}: invalid JSON ({exc})")
        return None


def parse_frontmatter(path):
    """Return the YAML-ish frontmatter block as a dict of top-level scalar keys.

    Intentionally minimal (no YAML dep): reads the leading `---` fenced block and
    pulls `key: value` pairs. Enough to assert presence of name/description.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(f"{path.relative_to(ROOT)}: cannot read ({exc})")
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    fields = {}
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def validate_all_json_parse():
    """Every .json file in the repo must parse (skip dependency/vcs dirs)."""
    skip = {"node_modules", ".git", "__pycache__"}
    for path in sorted(ROOT.rglob("*.json")):
        if any(part in skip for part in path.relative_to(ROOT).parts):
            continue
        load_json(path)


def validate_marketplace():
    path = ROOT / ".claude-plugin" / "marketplace.json"
    if not check(path.exists(), "missing .claude-plugin/marketplace.json"):
        return
    data = load_json(path)
    if data is None:
        return
    check("name" in data, "marketplace.json: missing 'name'")
    check("owner" in data, "marketplace.json: missing 'owner'")
    check("plugins" in data, "marketplace.json: missing 'plugins'")

    name = data.get("name", "")
    check(bool(KEBAB.match(name)), f"marketplace.json: name '{name}' is not kebab-case")
    check(
        name.lower() not in RESERVED_NAMES,
        f"marketplace.json: name '{name}' is a reserved Anthropic name",
    )

    plugins = data.get("plugins", [])
    check(isinstance(plugins, list) and len(plugins) > 0, "marketplace.json: 'plugins' must be a non-empty array")
    for i, entry in enumerate(plugins if isinstance(plugins, list) else []):
        check("name" in entry, f"marketplace.json: plugins[{i}] missing 'name'")
        if not check("source" in entry, f"marketplace.json: plugins[{i}] missing 'source'"):
            continue
        source = entry["source"]
        # Only relative paths are resolved against the repo; remote sources are skipped.
        if isinstance(source, str) and (source.startswith("./") or source.startswith("../")):
            check(
                (ROOT / source).resolve().exists(),
                f"marketplace.json: plugins[{i}] source path '{source}' does not exist",
            )


def validate_plugin_manifests():
    for manifest in sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json")):
        data = load_json(manifest)
        if data is None:
            continue
        rel = manifest.relative_to(ROOT)
        name = data.get("name", "")
        check(bool(KEBAB.match(name)), f"{rel}: name '{name}' is not kebab-case")
        version = data.get("version", "")
        check(bool(SEMVER.match(version)), f"{rel}: version '{version}' is not semver")


def validate_frontmatter_files():
    for plugin_dir in sorted(ROOT.glob("plugins/*")):
        if not plugin_dir.is_dir():
            continue
        targets = sorted(plugin_dir.glob("skills/*/SKILL.md")) + sorted(plugin_dir.glob("agents/*.md"))
        for path in targets:
            rel = path.relative_to(ROOT)
            fields = parse_frontmatter(path)
            check(bool(fields.get("name")), f"{rel}: missing 'name' frontmatter")
            check(bool(fields.get("description")), f"{rel}: missing 'description' frontmatter")


def validate_skill_contracts():
    """Each skill named in SKILL_CONTRACTS must contain its required tokens."""
    for skill, patterns in SKILL_CONTRACTS.items():
        path = ROOT / "plugins" / "mango" / "skills" / skill / "SKILL.md"
        if not check(path.exists(), f"skill-contract: skills/{skill}/SKILL.md is missing"):
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except OSError as exc:
            check(False, f"skill-contract: cannot read skills/{skill}/SKILL.md ({exc})")
            continue
        for pattern in patterns:
            check(
                re.search(pattern, body, re.IGNORECASE) is not None,
                f"skill-contract: skills/{skill}/SKILL.md missing required token /{pattern}/",
            )


def validate_token_optimizer():
    """The token_optimizer block ships descriptive + human-gated with two HARD-PINNED invariants:
    RTK default-expect (degrade clean), headroom.output_shaper OFF (never shapes critic output),
    caveman scoped non-critic-only. Guards that an edit cannot silently flip a safety invariant."""
    example = ROOT / "plugins" / "mango" / "config" / "harness.example.json"
    data = load_json(example)
    if not isinstance(data, dict):
        return
    to = data.get("token_optimizer")
    if not check(isinstance(to, dict), "token_optimizer: missing or not an object in harness.example.json"):
        return
    check(to.get("rtk") == "expect", "token_optimizer: rtk default must be 'expect' (degrade-clean)")
    headroom = to.get("headroom", {})
    check(isinstance(headroom, dict) and headroom.get("output_shaper") is False,
          "token_optimizer: headroom.output_shaper must be false (never shapes critic output)")
    caveman = to.get("caveman", {})
    check(isinstance(caveman, dict) and caveman.get("scope") == "non-critic-only",
          "token_optimizer: caveman.scope must be 'non-critic-only' (Caveman never touches critic output)")


def validate_critic_guardrail():
    """Every critic agent brief MUST carry the Caveman-critic guardrail: critic output keeps full
    evidence detail and is never terse-compressed. The build fails if the prohibition is dropped."""
    for agent in CRITIC_AGENTS:
        path = ROOT / "plugins" / "mango" / "agents" / f"{agent}.md"
        if not check(path.exists(), f"critic-guardrail: agents/{agent}.md is missing"):
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except OSError as exc:
            check(False, f"critic-guardrail: cannot read agents/{agent}.md ({exc})")
            continue
        check(re.search(r"Caveman", body) is not None,
              f"critic-guardrail: agents/{agent}.md missing the Caveman-critic prohibition")
        check(re.search(r"full evidence", body, re.IGNORECASE) is not None,
              f"critic-guardrail: agents/{agent}.md must state critic output retains full evidence detail")


def validate_ledger_label():
    """The Cost-ledger column must be labelled to match what is measured: a single per-dispatch figure
    with NO in/out split. Guards Fix v1.4-4 — the false-precision `(out)` / `(in / out)` label may not
    reappear over an unsplit metric, and the plain `Tokens` column header must be present."""
    ticket = ROOT / "plugins" / "mango" / "templates" / "ticket.md"
    if not check(ticket.exists(), "ledger-label: templates/ticket.md is missing"):
        return
    try:
        body = ticket.read_text(encoding="utf-8")
    except OSError as exc:
        check(False, f"ledger-label: cannot read templates/ticket.md ({exc})")
        return
    check(re.search(r"Tokens\s*\(out\)", body) is None,
          "ledger-label: templates/ticket.md ledger must not label the column 'Tokens (out)' (false precision over an unsplit metric)")
    check(re.search(r"Tokens\s*\(in\s*/\s*out\)", body) is None,
          "ledger-label: templates/ticket.md ledger must not label the column 'Tokens (in / out)' (harness exposes no in/out split)")
    check(re.search(r"\|\s*Tokens\s*\|", body) is not None,
          "ledger-label: templates/ticket.md ledger must carry a plain '| Tokens |' column header")


def validate_eval_convention():
    """The multi-run eval-variance convention (v1.5 Fix 4) must be documented where assertion authors
    will see it: tests/eval/README.md records that every new assertion matches the decision (not one
    phrasing), tolerates markdown emphasis, passes 3x fresh before it counts green, and is widened over
    wording/emphasis but never over outcome. Guards that this standing practice cannot silently vanish."""
    readme = ROOT / "tests" / "eval" / "README.md"
    if not check(readme.exists(), "eval-convention: tests/eval/README.md is missing"):
        return
    try:
        body = readme.read_text(encoding="utf-8")
    except OSError as exc:
        check(False, f"eval-convention: cannot read tests/eval/README.md ({exc})")
        return
    check(re.search(r"decision", body, re.IGNORECASE) is not None,
          "eval-convention: README must state assertions match the decision, not one phrasing")
    check(re.search(r"emphasis", body, re.IGNORECASE) is not None,
          "eval-convention: README must state assertions are emphasis-agnostic")
    check(re.search(r"3.{0,3}fresh|three .{0,12}fresh", body, re.IGNORECASE) is not None,
          "eval-convention: README must state a new assertion passes 3x fresh before it counts green")
    check(re.search(r"never .{0,20}outcome|not .{0,12}over outcome|over outcome", body, re.IGNORECASE) is not None,
          "eval-convention: README must state widening is over wording/emphasis, never over outcome")


def validate_doc_consistency():
    """Docs must reflect reality: the plugin README's skill list matches the skills/
    directory exactly, and every config key in harness.example.json is documented.

    Guards against doc drift — a skill added/removed without a README update, a README
    naming a skill that does not exist, or a new config key shipping undocumented.
    """
    plugin = ROOT / "plugins" / "mango"
    readme = plugin / "README.md"
    if not check(readme.exists(), "doc-consistency: plugins/mango/README.md is missing"):
        return
    try:
        readme_text = readme.read_text(encoding="utf-8")
    except OSError as exc:
        check(False, f"doc-consistency: cannot read plugins/mango/README.md ({exc})")
        return

    # Skill directories (those carrying a SKILL.md).
    skill_dirs = {
        p.parent.name for p in plugin.glob("skills/*/SKILL.md")
    }
    # Every skill directory must be named in the README.
    for skill in sorted(skill_dirs):
        check(
            skill in readme_text,
            f"doc-consistency: skill '{skill}' exists under skills/ but is not named in the plugin README",
        )
    # The README must not reference a /mango:<skill> that does not exist.
    for referenced in sorted(set(re.findall(r"/mango:([a-z][a-z0-9-]*)", readme_text))):
        check(
            referenced in skill_dirs,
            f"doc-consistency: plugin README references /mango:{referenced} but no skills/{referenced}/ exists",
        )

    # Every top-level config key in harness.example.json must be documented in the README.
    example = plugin / "config" / "harness.example.json"
    data = load_json(example)
    if isinstance(data, dict):
        for key in data:
            if key.startswith("//"):
                continue
            check(
                key in readme_text,
                f"doc-consistency: config key '{key}' in harness.example.json is not documented in the plugin README",
            )


def main():
    validate_all_json_parse()
    validate_marketplace()
    validate_plugin_manifests()
    validate_frontmatter_files()
    validate_skill_contracts()
    validate_token_optimizer()
    validate_critic_guardrail()
    validate_ledger_label()
    validate_eval_convention()
    validate_doc_consistency()

    print(f"mango validate: {checks} checks run, {len(failures)} failed.")
    if failures:
        for f in failures:
            print(f"  FAIL: {f}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
