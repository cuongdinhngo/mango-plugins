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
    "refine": [r"scan", r"want-decision", r"how-decision", r"cite", r"ASSUMED", r"skip", r"exposure-checker",
               r"acceptance-bar", r"want-decision by default", r"resolve-by-citation",
               r"uncited how-decision", r"next-gate confirm", r"epic.{0,60}exposure-checker"],
    "breakdown": [r"INVEST", r"ticket boundary", r"counted", r"enumerate",
                  r"Independent", r"Negotiable", r"Valuable", r"Estimable", r"Small", r"Testable",
                  r"re-?split", r"re-?ratif", r"delta", r"re-?approve", r"scaffold committed before child",
                  r"Experimental", r"work_doc_mode", r"separate"],
    "analysis": [r"SECTIONS:", r"CLARIFICATION:", r"AC validation", r"Gate 1", r"denominator", r"for each", r"TRACK", r"SURFACES", r"falsifiable", r"manual-check", r"baseline", r"uncodified", r"ratif",
                 r"applicable .{0,12}section", r"change[ -]type", r"enumerate"],
    "design": [r"proving test", r"Gate 2", r"risk layer", r"Assumptions", r"coverage-gap", r"layer-match", r"block", r"DESIGN\.md", r"data-core", r"responsive", r"blast[ -]radius",
               r"real producers", r"(all|every) .{0,8}test root", r"typecheck", r"builder call site"],
    "execute": [r"verification sweep", r"reformat", r"stuck", r"design[ -]invalidat", r"token-first", r"pointer", r"render", r"proof[ -]manifest", r"ui-proof-scaffold", r"(per|each) clause", r"format[ -]scope", r"approved design", r"both axes", r"baseline", r"unchanged except", r"complete on disk"],
    "review": [r"reviewer", r"challenger", r"not clean", r"coverage-gap", r"item-by-item", r"per-item", r"layer-match", r"Reviewed at", r"a11y", r"DESIGN\.md", r"touch-target", r"proof[ -]manifest", r"surfaces proven", r"conditional", r"verify-only", r"baseline", r"reuse", r"only the proof affected", r"main[ -]loop", r"re-?dispatch", r"changed scope", r"bookkeeping", r"exempt", r"carve-?out",
               r"ref-based", r"worktree", r"checkout"],
    "finalise": [r"dry-run", r"per[- ]action", r"durable lesson", r"checklist", r"stale", r"beyond the reviewed set", r"exempt", r"dispatch[ -]only", r"not measured", r"rtk gain", r"dispatch[ -]count", r"ledger complet", r"content", r"token value", r"unmeasured", r"push", r"shared ref", r"unchanged except", r"complete on disk"],
    "solve": [r"Session status", r"self-approve", r"TIER", r"design[ -]invalidat", r"outgrew", r"per dispatch", r"unmeasured \(blocking retrieval\)", r"delta", r"unchanged except", r"complete on disk"],
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


def validate_eval_isolation():
    """The behavioural eval must isolate execute-touching fixtures from the live checkout (v1.6.1 Fix 1).
    tests/eval/run.sh must run fixtures in a throwaway clone/worktree AND carry the post-run safety guard
    that asserts the live checkout is untouched. Guards that a future edit cannot silently drop the
    isolation or its guard — the leak that once stranded a commit on a stray branch could never recur."""
    runsh = ROOT / "tests" / "eval" / "run.sh"
    if not check(runsh.exists(), "eval-isolation: tests/eval/run.sh is missing"):
        return
    try:
        body = runsh.read_text(encoding="utf-8")
    except OSError as exc:
        check(False, f"eval-isolation: cannot read tests/eval/run.sh ({exc})")
        return
    check(re.search(r"throwaway|worktree|git clone", body, re.IGNORECASE) is not None,
          "eval-isolation: run.sh must run fixtures in a throwaway clone/worktree, never the live checkout")
    check(re.search(r"live checkout", body, re.IGNORECASE) is not None,
          "eval-isolation: run.sh must document that the live checkout is never touched")
    check(re.search(r"assert_checkout_clean", body) is not None,
          "eval-isolation: run.sh must define the post-run guard assert_checkout_clean (the safety check)")
    check(re.search(r"non-vacuous|injected leak|VACUOUS", body, re.IGNORECASE) is not None,
          "eval-isolation: run.sh must self-test the guard against an injected leak (non-vacuous)")


def validate_verify_incremental():
    """The verify-incremental build discipline (v1.6.1 Fix 3) must be documented where an eval author
    will see it: run only the AFFECTED fixture(s) mid-build, the FULL SUITE ONCE at the end, and keep
    each new fixture 3x fresh. Guards that the cost-saving discipline cannot silently vanish, and that
    it never weakens the Finish bar (coverage unchanged)."""
    for rel in ("tests/eval/README.md", "CONTRIBUTING.md"):
        path = ROOT / rel
        if not check(path.exists(), f"verify-incremental: {rel} is missing"):
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except OSError as exc:
            check(False, f"verify-incremental: cannot read {rel} ({exc})")
            continue
        check(re.search(r"affected fixture", body, re.IGNORECASE) is not None,
              f"verify-incremental: {rel} must state affected-fixture-only during a build")
        check(re.search(r"full suite once", body, re.IGNORECASE) is not None,
              f"verify-incremental: {rel} must state the full suite runs once at the end before push")
        check(re.search(r"3.{0,3}fresh|three .{0,12}fresh", body, re.IGNORECASE) is not None,
              f"verify-incremental: {rel} must state each new fixture stays 3x fresh (coverage unchanged)")


def validate_changelog_shipped():
    """The CHANGELOG must ship INSIDE the plugin dir (the retro convention's neutral source) and carry an
    entry matching plugin.json's version. Guards Fix D (v1.7.3) — the retro convention may not point at a
    file that does not ship under the plugin dir, and a version bump may not forget its CHANGELOG entry."""
    plugin = ROOT / "plugins" / "mango"
    changelog = plugin / "CHANGELOG.md"
    if not check(changelog.exists(), "changelog: plugins/mango/CHANGELOG.md must ship inside the plugin dir"):
        return
    data = load_json(plugin / ".claude-plugin" / "plugin.json")
    version = data.get("version", "") if isinstance(data, dict) else ""
    try:
        body = changelog.read_text(encoding="utf-8")
    except OSError as exc:
        check(False, f"changelog: cannot read plugins/mango/CHANGELOG.md ({exc})")
        return
    check(
        version != "" and re.search(r"^\#\#\s*\[" + re.escape(version) + r"\]", body, re.MULTILINE) is not None,
        f"changelog: plugins/mango/CHANGELOG.md has no '## [{version}]' entry matching plugin.json version",
    )


def validate_eval_cache():
    """The eval transcript-cache (Fix E, v1.7.3) must stay wired in run.sh: a per-fixture skills-hash key,
    a cache-hit reuse path, a --no-cache full-fresh milestone flag, and the fail-safe-to-run default.
    Guards that the cost-saving cache cannot silently drop coverage or lose its milestone escape hatch."""
    runsh = ROOT / "tests" / "eval" / "run.sh"
    if not check(runsh.exists(), "eval-cache: tests/eval/run.sh is missing"):
        return
    try:
        body = runsh.read_text(encoding="utf-8")
    except OSError as exc:
        check(False, f"eval-cache: cannot read tests/eval/run.sh ({exc})")
        return
    check(re.search(r"skills-hash", body, re.IGNORECASE) is not None,
          "eval-cache: run.sh must key the cache on a skills-hash")
    check(re.search(r"cache-hit", body, re.IGNORECASE) is not None,
          "eval-cache: run.sh must reuse a cached green transcript on a cache-hit")
    check(re.search(r"--no-cache", body) is not None,
          "eval-cache: run.sh must support --no-cache (a full fresh milestone run)")
    check(re.search(r"fail-safe to run", body, re.IGNORECASE) is not None,
          "eval-cache: run.sh must document the fail-safe-to-run default (uncertainty → run fresh)")


def validate_review_git_isolation():
    """v1.7.4 Fix 1 — a review subagent inspecting a branch must use read-only, ref-based git OR an
    isolated worktree, and MUST NOT run stateful git (checkout/switch/stash) in the shared working tree
    (the live checkout). Guards review/SKILL.md, the reviewer/challenger briefs, and the PRINCIPLES
    invariant — the same class as the v1.6.1 eval-isolation fix, now on the review surface. A future edit
    cannot silently drop the isolation."""
    plugin = ROOT / "plugins" / "mango"
    targets = [
        plugin / "skills" / "review" / "SKILL.md",
        plugin / "agents" / "reviewer.md",
        plugin / "agents" / "challenger.md",
        plugin / "PRINCIPLES.md",
    ]
    for path in targets:
        rel = path.relative_to(ROOT)
        if not check(path.exists(), f"review-git-isolation: {rel} is missing"):
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except OSError as exc:
            check(False, f"review-git-isolation: cannot read {rel} ({exc})")
            continue
        check(re.search(r"ref-based", body, re.IGNORECASE) is not None,
              f"review-git-isolation: {rel} must require ref-based branch inspection (git diff/show/log <base>..<branch>)")
        check(re.search(r"worktree", body, re.IGNORECASE) is not None,
              f"review-git-isolation: {rel} must allow an isolated git worktree for running the suite against a branch")
        check(re.search(r"checkout|switch|stash", body, re.IGNORECASE) is not None,
              f"review-git-isolation: {rel} must name the forbidden stateful git ops (checkout/switch/stash)")
        check(re.search(r"MUST NOT|must not|never|not run", body) is not None,
              f"review-git-isolation: {rel} must forbid stateful git in the shared working tree")
        check(re.search(r"shared (working tree|cwd|git state)|live checkout", body, re.IGNORECASE) is not None,
              f"review-git-isolation: {rel} must scope the prohibition to the shared working tree / live checkout")


def validate_maturity_labels():
    """v1.7.4 Fix 2 — shipped OPERATIONAL plugin text (the behavioural instruction surface a stranger
    reads: skills, agents, templates, PRINCIPLES, README) uses standard maturity vocabulary and carries
    NO internal jargon (`v1-learning`, `n=1`, `n=2`). breakdown re-ratification is labelled Experimental
    with a plain graduation line; a Maturity definition (Stable + Experimental + graduation) exists in
    PRINCIPLES.md. (Version references like `v1.6.1` are NOT jargon and are unaffected.)"""
    plugin = ROOT / "plugins" / "mango"
    operational = (sorted(plugin.glob("skills/*/SKILL.md"))
                   + sorted(plugin.glob("agents/*.md"))
                   + sorted(plugin.glob("templates/*.md"))
                   + [plugin / "PRINCIPLES.md", plugin / "README.md"])
    for path in operational:
        if not path.exists():
            continue
        rel = path.relative_to(ROOT)
        try:
            body = path.read_text(encoding="utf-8")
        except OSError as exc:
            check(False, f"maturity: cannot read {rel} ({exc})")
            continue
        check(re.search(r"v1-learning", body, re.IGNORECASE) is None,
              f"maturity: {rel} must not use the internal jargon 'v1-learning' (use Stable/Experimental)")
        check(re.search(r"\bn=[12]\b", body) is None,
              f"maturity: {rel} must not use internal evidence jargon 'n=1'/'n=2' in shipped plugin text")
    bd = plugin / "skills" / "breakdown" / "SKILL.md"
    if check(bd.exists(), "maturity: skills/breakdown/SKILL.md is missing"):
        body = bd.read_text(encoding="utf-8")
        check(re.search(r"Experimental", body) is not None,
              "maturity: breakdown must label its re-ratification behaviour Experimental")
        check(re.search(r"graduat", body, re.IGNORECASE) is not None,
              "maturity: breakdown must state a plain graduation condition (Experimental → Stable)")
    pr = plugin / "PRINCIPLES.md"
    if check(pr.exists(), "maturity: PRINCIPLES.md is missing"):
        body = pr.read_text(encoding="utf-8")
        check(re.search(r"^##\s*Maturity", body, re.MULTILINE) is not None,
              "maturity: PRINCIPLES.md must carry a Maturity section defining the vocabulary")
        check(re.search(r"\bStable\b", body) is not None and re.search(r"\bExperimental\b", body) is not None,
              "maturity: PRINCIPLES.md Maturity section must define both Stable and Experimental")
        check(re.search(r"graduat", body, re.IGNORECASE) is not None,
              "maturity: PRINCIPLES.md must state the graduation convention (CHANGELOG records it)")


def validate_workdoc_committed_stub():
    """v1.7.4 Fix 3 — for a local-file ticket that is ALSO a committed scaffold stub, work_doc_mode:
    separate is recommended over auto/embed (embedding the mutable working doc in a committed tracked
    file is fragile to a stray subagent git-state op). Guards the config comment and the epic-scaffold
    path (breakdown). Guidance + a sensible default, never a behavioural gate."""
    plugin = ROOT / "plugins" / "mango"
    example = plugin / "config" / "harness.example.json"
    if check(example.exists(), "workdoc-stub: config/harness.example.json is missing"):
        body = example.read_text(encoding="utf-8")
        check(re.search(r"committed .{0,24}stub", body, re.IGNORECASE) is not None
              and re.search(r"separate", body) is not None,
              "workdoc-stub: harness.example.json must recommend 'separate' for a committed-stub ticket")
    bd = plugin / "skills" / "breakdown" / "SKILL.md"
    if check(bd.exists(), "workdoc-stub: skills/breakdown/SKILL.md is missing"):
        body = bd.read_text(encoding="utf-8")
        check(re.search(r"work_doc_mode", body) is not None and re.search(r"separate", body) is not None,
              "workdoc-stub: breakdown must advise work_doc_mode: separate for the committed child stubs")
        check(re.search(r"committed .{0,30}stub|committed, tracked", body, re.IGNORECASE) is not None,
              "workdoc-stub: breakdown must explain the committed-stub fragility")


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
    validate_eval_isolation()
    validate_verify_incremental()
    validate_changelog_shipped()
    validate_eval_cache()
    validate_review_git_isolation()
    validate_maturity_labels()
    validate_workdoc_committed_stub()
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
