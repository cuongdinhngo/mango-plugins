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
               r"uncited how-decision", r"next-gate confirm", r"epic.{0,60}exposure-checker",
               r"PREMISE FALSIFIED", r"PREMISE:", r"to-be-created", r"ambiguous",
               r"RECALL:", r"advisory", r"retired", r"by symbol", r"by area",
               r"numbered", r"host"],
    "breakdown": [r"INVEST", r"ticket boundary", r"counted", r"enumerate",
                  r"Independent", r"Negotiable", r"Valuable", r"Estimable", r"Small", r"Testable",
                  r"re-?split", r"re-?ratif", r"delta", r"re-?approve", r"scaffold committed before child",
                  r"Experimental", r"work_doc_mode", r"separate",
                  r"EPIC LESSON:", r"lessons_path", r"durable lesson", r"close-?out",
                  r"CLAIMS:", r"atomic claim", r"skill_gap_path"],
    "analysis": [r"SECTIONS:", r"CLARIFICATION:", r"AC validation", r"Gate 1", r"denominator", r"for each", r"TRACK", r"SURFACES", r"falsifiable", r"manual-check", r"baseline", r"uncodified", r"ratif",
                 r"applicable .{0,12}section", r"change[ -]type", r"enumerate",
                 r"multi-clause", r"one row per clause", r"want-decision",
                 r"PREMISE FALSIFIED", r"premise check",
                 r"RECALL:", r"advisory", r"retired"],
    "design": [r"proving test", r"Gate 2", r"risk layer", r"Assumptions", r"coverage-gap", r"layer-match", r"block", r"DESIGN\.md", r"data-core", r"responsive", r"blast[ -]radius",
               r"real producers", r"(all|every) .{0,8}test root", r"typecheck", r"builder call site",
               r"side-effect surface", r"none identified"],
    "execute": [r"verification sweep", r"reformat", r"stuck", r"design[ -]invalidat", r"token-first", r"pointer", r"render", r"proof[ -]manifest", r"ui-proof-scaffold", r"(per|each) clause", r"format[ -]scope", r"approved design", r"both axes", r"baseline", r"unchanged except", r"complete on disk",
                r"commit(ted)? .{0,24}before .{0,20}review", r"ref-based", r"empty",
                r"empirical output", r"verbatim", r"golden", r"docstring", r"interface contract"],
    "review": [r"reviewer", r"challenger", r"not clean", r"coverage-gap", r"item-by-item", r"per-item", r"layer-match", r"Reviewed at", r"a11y", r"DESIGN\.md", r"touch-target", r"proof[ -]manifest", r"surfaces proven", r"conditional", r"verify-only", r"baseline", r"reuse", r"only the proof affected", r"main[ -]loop", r"re-?dispatch", r"changed scope", r"bookkeeping", r"exempt", r"carve-?out",
               r"ref-based", r"worktree", r"checkout",
               r"env-?parity|environment-equivalence", r"env-?fault|environment fault", r"untracked",
               r"near-total", r"git diff HEAD", r"porcelain"],
    "finalise": [r"dry-run", r"per[- ]action", r"durable lesson", r"checklist", r"stale", r"beyond the reviewed set", r"exempt", r"dispatch[ -]only", r"not measured", r"rtk gain", r"dispatch[ -]count", r"ledger complet", r"content", r"token value", r"unmeasured", r"push", r"shared ref", r"unchanged except", r"complete on disk",
                 r"CLAIMS:", r"RECURRENCE:", r"FALSIFY:", r"PROMOTION:", r"atomic claim",
                 r"supersed", r"retired", r"falsif", r"skill_gap_path", r"agent_brief_path",
                 r"mango files written: 0",
                 r"host does not surface usage", r"empirical output", r"verbatim"],
    "solve": [r"Session status", r"self-approve", r"TIER", r"design[ -]invalidat", r"outgrew", r"per dispatch", r"unmeasured \(blocking retrieval\)", r"delta", r"unchanged except", r"complete on disk",
              r"work_doc_mode", r"committed-?stub", r"separate",
              r"learning loop", r"falsification", r"skill_gap_path", r"no lesson edits a mango skill",
              r"host does not surface usage"],
    "quick": [r"proving test", r"combined gate", r"stuck"],
    "doctor": [r"running[ -]version", r"base path", r"\$\{CLAUDE_PLUGIN_ROOT\}",
               r"mango:standing-context", r"CLAUDE\.md",
               r"skill_gap_path", r"inside the project repo",
               r"config\.context_file", r"AGENTS\.md", r"always-on"],
    "init": [r"\.harness\.json", r"UNVERIFIED", r"rulebook", r"never overwrite",
             r"CLAUDE\.md", r"mango:standing-context", r"pointer", r"secret",
             r"config\.context_file", r"AGENTS\.md", r"always-on"],
    "version-check": [r"update_check_url", r"never updates", r"/plugin", r"plugin\.json"],
    "codify": [r"count", r"PROVISIONAL", r"ratif", r"author", r"recommend", r"uncodified",
               r"DRIFT:", r"counting line", r"drift",
               r"promoted claim|promoted CLAIM", r"falsification", r"agent_brief_path",
               r"expiry", r"never .{0,20}CLAUDE\.md|never into `CLAUDE\.md`"],
    "budget": [r"[Dd]etect", r"[Ii]nform", r"recorded", r"never.{0,15}install", r"depend",
               r"RTK", r"[Cc]aveman", r"safety axis", r"degrade clean", r"PROVISIONAL",
               r"non-critic-only", r"descriptive", r"wire", r"you must run this",
               r"dispatch-scoped", r"rtk gain"],
}

# Critic agents whose output must never be terse-compressed. Each brief MUST carry the
# Caveman-critic guardrail so a token optimizer cannot strip the evidence a gate relies on.
CRITIC_AGENTS = ["reviewer", "reviewer-max", "challenger"]

# Internal jargon banned from SHIPPED OPERATIONAL TEXT (the behavioural instruction surface a stranger
# reads). Each entry is (regex, reason, flags). v1.7.5 Fix 1b: the v1.7.4 grep carried only the first two
# patterns, so the pre-relabel framing `v1 — "enough to run and learn"` passed straight through it in
# shipped files while the validator reported OK — a false-green at the verify layer itself.
# The maturity vocabulary (Stable / Experimental) is the replacement; see PRINCIPLES.md (Maturity).
# `n=[12]` stays CASE-SENSITIVE on purpose: upper-case `N=1` / `N>1` is the requirements-matrix
# denominator in `analysis/SKILL.md` — a different meaning, not jargon.
BANNED_JARGON = [
    (r"v1-learning", "the internal jargon 'v1-learning' (use Stable/Experimental)", re.IGNORECASE),
    (r"\bn=[12]\b", "internal evidence jargon 'n=1'/'n=2'", 0),
    (r"enough to run and learn", "the pre-relabel framing 'enough to run and learn' (say 'only enough to split', and label maturity Stable/Experimental)", re.IGNORECASE),
    (r"\bv1\s*[—–]", "the pre-relabel maturity label 'v1 — …' (use Stable/Experimental)", re.IGNORECASE),
]

# Rationale markers banned from `skills/*/SKILL.md` (v1.7.6). Skill text is runtime-loaded and IS
# behaviour (prose-IS-behaviour), so every token is paid on every ticket run: a SKILL.md carries
# DIRECTIVES ONLY. The "why" — rationale, an "observed failure" war-story, a historical justification —
# lives in CHANGELOG.md or the non-runtime RATIONALE.md. Scanned CASE-INSENSITIVELY over skills only:
# PRINCIPLES.md is the contract doc, agents/*.md are critic briefs, and CHANGELOG.md is the history.
RATIONALE_MARKERS = [
    (r"observed failure", "an 'Observed failure: …' war-story"),
    (r"field-?observed", "a 'Field-observed: …' war-story"),
    (r"exists because", "a 'this exists because …' justification"),
    (r"the reason (we|this|it|they|for)\b", "a 'the reason …' justification"),
    (r"\bhistorically\b", "a historical justification"),
    (r"war-?stor", "a war-story"),
    (r"retro-#\d", "a past-incident reference ('retro-#N')"),
]

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


def principles_paths():
    """The PRINCIPLES contract surface: the always-loaded core PLUS every on-demand companion.

    v1.10.0 relocated whole sections out of `PRINCIPLES.md` into `principles/*.md`, read on demand at
    their point of use. The contract did not move — only the file it lives in — so every check that
    asserted a token in `PRINCIPLES.md` now asserts it across this WHOLE surface. Passing the list
    (rather than one path) keeps the failure message naming a real file, and keeps `principles/` from
    becoming a place a required token can quietly go missing from.
    """
    plugin = ROOT / "plugins" / "mango"
    return [plugin / "PRINCIPLES.md"] + sorted((plugin / "principles").glob("*.md"))


def principles_text():
    """The concatenated PRINCIPLES contract surface (core + companions) as one string."""
    out = []
    for path in principles_paths():
        try:
            out.append(path.read_text(encoding="utf-8"))
        except OSError:
            pass
    return "\n".join(out)


def skill_text(name):
    """A skill's whole directive surface: SKILL.md PLUS any on-demand companion beside it.

    v1.10.0 moved each skill's frontend-only block to `skills/<name>/frontend.md`, read on demand when
    `config.track` includes frontend. A required token may live in either file — but it must live in one
    of them, so no contract token is lost to the relocation.
    """
    d = ROOT / "plugins" / "mango" / "skills" / name
    out = []
    for path in sorted(d.glob("*.md")):
        try:
            out.append(path.read_text(encoding="utf-8"))
        except OSError:
            pass
    return "\n".join(out)


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
        body = skill_text(skill)          # SKILL.md + its on-demand companions (v1.10.0)
        if not check(bool(body), f"skill-contract: cannot read skills/{skill}/"):
            continue
        for pattern in patterns:
            check(
                re.search(pattern, body, re.IGNORECASE) is not None,
                f"skill-contract: skills/{skill}/ missing required token /{pattern}/ "
                "(searched SKILL.md and every companion beside it)",
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
        # v1.10.0: the invariant moved to principles/git-isolation.md. Assert it over the WHOLE
        # PRINCIPLES surface (core + companions) so relocation cannot drop the check.
        None,
    ]
    for path in targets:
        if path is None:
            rel, body = "plugins/mango/PRINCIPLES.md + principles/*.md", principles_text()
            if not check(bool(body), f"review-git-isolation: {rel} is missing"):
                continue
        else:
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


def validate_worktree_env_parity():
    """v1.7.5 Fix 2 — a review subagent that creates an isolated worktree in order to RUN a suite must
    carry the project's required UNTRACKED environment into it (or run read-only in place when the tree
    is already at the reviewed SHA), and must treat a NEAR-TOTAL worktree failure as an ENV-FAULT rather
    than a review finding. A fresh worktree holds only tracked files, so a missing `.env` fails every
    test for an environmental reason that reads exactly like a catastrophic regression. Guarded across
    review/SKILL.md, the reviewer/challenger briefs, and the PRINCIPLES invariant. This only ADDS a
    guard — it reclassifies an environment artifact and never suppresses a real finding, which is why
    each file must ALSO keep the partial/targeted-failure-is-still-real carve-out."""
    plugin = ROOT / "plugins" / "mango"
    targets = [
        plugin / "skills" / "review" / "SKILL.md",
        plugin / "agents" / "reviewer.md",
        plugin / "agents" / "challenger.md",
        # v1.10.0: the invariant moved to principles/git-isolation.md. Assert it over the WHOLE
        # PRINCIPLES surface (core + companions) so relocation cannot drop the check.
        None,
    ]
    for path in targets:
        if path is None:
            rel, body = "plugins/mango/PRINCIPLES.md + principles/*.md", principles_text()
            if not check(bool(body), f"worktree-env-parity: {rel} is missing"):
                continue
        else:
            rel = path.relative_to(ROOT)
            if not check(path.exists(), f"worktree-env-parity: {rel} is missing"):
                continue
            try:
                body = path.read_text(encoding="utf-8")
            except OSError as exc:
                check(False, f"worktree-env-parity: cannot read {rel} ({exc})")
                continue
        check(re.search(r"env-?parity|environment-equivalence|environment parity", body, re.IGNORECASE) is not None,
              f"worktree-env-parity: {rel} must state that a worktree is NOT environment-equivalent")
        check(re.search(r"untracked", body, re.IGNORECASE) is not None,
              f"worktree-env-parity: {rel} must name the missing UNTRACKED environment as the cause")
        check(re.search(r"\.env", body) is not None,
              f"worktree-env-parity: {rel} must name `.env` / local config as the minimum to carry in")
        check(re.search(r"in place", body, re.IGNORECASE) is not None
              and re.search(r"reviewed\s+SHA", body, re.IGNORECASE) is not None,
              f"worktree-env-parity: {rel} must offer running read-only in place at the reviewed SHA")
        check(re.search(r"near-?total", body, re.IGNORECASE) is not None,
              f"worktree-env-parity: {rel} must state the near-total-failure sanity rule")
        check(re.search(r"env-?fault|environment fault", body, re.IGNORECASE) is not None,
              f"worktree-env-parity: {rel} must classify a near-total worktree failure as an env-fault")
        check(re.search(r"until proven otherwise", body, re.IGNORECASE) is not None,
              f"worktree-env-parity: {rel} must scope the reclassification with 'until proven otherwise'")
        check(re.search(r"partial", body, re.IGNORECASE) is not None,
              f"worktree-env-parity: {rel} must keep the carve-out that a PARTIAL/targeted failure is still a real finding (the rule may not suppress findings)")


def validate_empty_diff_fallback():
    """v1.7.5 Fix 3b — two guards against a false 'no changes' verdict. (a) `execute` COMMITS the
    change-set BEFORE review is dispatched, so the ref-based `<base>..<branch>` inspection has a real
    committed diff. (b) Both critic briefs (and review/SKILL.md) carry the fallback: an EMPTY range means
    the change may be uncommitted — check `git diff HEAD` + `git status --porcelain -uall` before
    concluding no-change. Field near-miss: an empty A..B diff nearly rubber-stamped a real two-file
    change-set."""
    plugin = ROOT / "plugins" / "mango"
    ex = plugin / "skills" / "execute" / "SKILL.md"
    if check(ex.exists(), "empty-diff: skills/execute/SKILL.md is missing"):
        body = ex.read_text(encoding="utf-8")
        check(re.search(r"commit(ted)?[^.\n]{0,40}before[^.\n]{0,30}review", body, re.IGNORECASE) is not None,
              "empty-diff: execute must commit the change-set BEFORE review is dispatched")
        check(re.search(r"empty", body, re.IGNORECASE) is not None,
              "empty-diff: execute must explain that an uncommitted change-set makes the ref-based range EMPTY")
    for rel_path in ("agents/reviewer.md", "agents/challenger.md", "skills/review/SKILL.md"):
        path = plugin / rel_path
        rel = path.relative_to(ROOT)
        if not check(path.exists(), f"empty-diff: {rel} is missing"):
            continue
        body = path.read_text(encoding="utf-8")
        check(re.search(r"empty", body, re.IGNORECASE) is not None,
              f"empty-diff: {rel} must handle an EMPTY <base>..<branch> range")
        check(re.search(r"git diff HEAD", body) is not None,
              f"empty-diff: {rel} must name the `git diff HEAD` fallback")
        check(re.search(r"porcelain", body) is not None,
              f"empty-diff: {rel} must name the `git status --porcelain -uall` fallback")
        check(re.search(r"uncommitted", body, re.IGNORECASE) is not None,
              f"empty-diff: {rel} must state the change may simply be UNCOMMITTED")


def validate_epic_lesson_owner():
    """v1.7.5 Fix 3c — an epic ends at `breakdown` and never reaches `finalise`, so mango's
    always-capture-a-durable-lesson rule had NO OWNER on the epic path: the split rationale and the
    overlap rulings reached no `config.lessons_path`. `breakdown` now owns it at ratification/close-out
    and emits the `EPIC LESSON:` counting line — a counted artifact, not prose, so it cannot silently
    not-happen."""
    bd = ROOT / "plugins" / "mango" / "skills" / "breakdown" / "SKILL.md"
    if not check(bd.exists(), "epic-lesson: skills/breakdown/SKILL.md is missing"):
        return
    body = bd.read_text(encoding="utf-8")
    check(re.search(r"EPIC LESSON:\s*<", body) is not None,
          "epic-lesson: breakdown must emit the `EPIC LESSON: <n> lesson(s) written to …` counting line")
    check(re.search(r"config\.lessons_path", body) is not None,
          "epic-lesson: breakdown must write the epic lesson to config.lessons_path")
    check(re.search(r"never reaches .{0,12}finalise|ends here|no owner", body, re.IGNORECASE) is not None,
          "epic-lesson: breakdown must explain WHY it owns this (an epic never reaches finalise)")
    check(re.search(r"split rationale", body, re.IGNORECASE) is not None
          and re.search(r"overlap|boundary ruling", body, re.IGNORECASE) is not None,
          "epic-lesson: breakdown must name the split rationale + overlap/boundary rulings as lesson content")


def validate_drift_count_line():
    """v1.7.5 Fix 3d — codify's drift-entry count is a PREFIXED COUNTING LINE (`DRIFT: <n> entries |
    <m> tickets`), matching the other counted artifacts (`REFINE:` / `BREAKDOWN:` / `SECTIONS:`) that
    resist fudging. A prose count drove a near-miss where '6' should have been '5'."""
    cd = ROOT / "plugins" / "mango" / "skills" / "codify" / "SKILL.md"
    if not check(cd.exists(), "drift-count: skills/codify/SKILL.md is missing"):
        return
    body = cd.read_text(encoding="utf-8")
    check(re.search(r"`DRIFT:\s*<n>\s*entries\s*\|\s*<m>\s*tickets`", body) is not None,
          "drift-count: codify must emit the `DRIFT: <n> entries | <m> tickets` counting line")
    check(re.search(r"not prose|never .{0,12}prose|prose count", body, re.IGNORECASE) is not None,
          "drift-count: codify must state the count is a counted line, not prose")
    check(re.search(r"REFINE:", body) is not None and re.search(r"BREAKDOWN:", body) is not None,
          "drift-count: codify must tie the DRIFT line to the existing counted-artifact shape (REFINE:/BREAKDOWN:)")


def validate_multi_clause_want():
    """v1.7.5 Fix 3e — a ratified want-decision carrying MORE THAN ONE clause is split at Gate 1 into one
    matrix row AND one proof row PER CLAUSE, so the design-conformance self-check cannot certify the half
    it enumerated while the other half silently drops out of the count. Same per-item-inventory discipline
    as the 'for each of N' rule and execute's one-assertion-per-clause M-gate rule."""
    an = ROOT / "plugins" / "mango" / "skills" / "analysis" / "SKILL.md"
    if not check(an.exists(), "multi-clause: skills/analysis/SKILL.md is missing"):
        return
    body = an.read_text(encoding="utf-8")
    check(re.search(r"multi-clause want-decision", body, re.IGNORECASE) is not None,
          "multi-clause: analysis must name the multi-clause want-decision case")
    check(re.search(r"one row per clause", body, re.IGNORECASE) is not None,
          "multi-clause: analysis must require one matrix + proof row PER CLAUSE")
    check(re.search(r"Gate 1", body) is not None,
          "multi-clause: analysis must place the clause split at Gate 1")
    check(re.search(r"finding", body, re.IGNORECASE) is not None,
          "multi-clause: analysis must make a clause with no row of its own a FINDING")
    check(re.search(r"self-check", body, re.IGNORECASE) is not None,
          "multi-clause: analysis must explain the design-conformance self-check half-certification failure")


def validate_solve_workdoc_route():
    """v1.7.5 Fix 3a — the v1.7.3/v1.7.4 committed-stub → `separate` guidance lived in breakdown/analysis
    but `solve`'s `auto` path still embedded regardless. `solve` now routes the committed-stub shape to
    `separate` at the place it actually sets the working-doc mode, and records the resolved mode in
    Session status so every later phase reads the same answer."""
    sv = ROOT / "plugins" / "mango" / "skills" / "solve" / "SKILL.md"
    if not check(sv.exists(), "solve-workdoc: skills/solve/SKILL.md is missing"):
        return
    body = sv.read_text(encoding="utf-8")
    check(re.search(r"committed-?stub", body, re.IGNORECASE) is not None,
          "solve-workdoc: solve must name the committed-stub ticket shape")
    check(re.search(r"even under .{0,4}`?auto`?", body, re.IGNORECASE) is not None,
          "solve-workdoc: solve must route a committed stub to `separate` EVEN UNDER `auto`")
    check(re.search(r"tracked", body, re.IGNORECASE) is not None,
          "solve-workdoc: solve must explain the committed/tracked-file fragility")
    check(re.search(r"Session status", body) is not None,
          "solve-workdoc: solve must record the resolved work_doc_mode in Session status")


def operational_text_files():
    """The SHIPPED OPERATIONAL TEXT set the jargon grep scans — the behavioural instruction surface a
    stranger reads. Exactly: every `plugins/mango/skills/*/SKILL.md`, every `plugins/mango/agents/*.md`,
    every `plugins/mango/templates/*.md`, `plugins/mango/PRINCIPLES.md`, the plugin `README.md`, AND the
    repo-root `README.md`. The root README was MISSING from this set in v1.7.4 — part of that version's
    false-green. `CHANGELOG.md` is deliberately EXCLUDED: a changelog documenting past versions is a
    historical record, not operational text.

    v1.10.0 widened the set to the ON-DEMAND companions — every `plugins/mango/principles/*.md` and every
    non-SKILL `plugins/mango/skills/*/*.md`. Relocated text is still shipped operational text: leaving the
    companions out would have let a jargon term survive by being moved out of a scanned file, which is the
    same false-green class as the v1.7.4 root-README omission."""
    plugin = ROOT / "plugins" / "mango"
    return (sorted(plugin.glob("skills/*/*.md"))
            + sorted(plugin.glob("agents/*.md"))
            + sorted(plugin.glob("templates/*.md"))
            + sorted(plugin.glob("principles/*.md"))
            + [plugin / "PRINCIPLES.md", plugin / "README.md", ROOT / "README.md",
               ROOT / "CLAUDE.md"])


def validate_maturity_labels():
    """v1.7.4 Fix 2 + v1.7.5 Fix 1b — shipped OPERATIONAL text (see `operational_text_files`) uses
    standard maturity vocabulary and carries NO internal jargon: every `BANNED_JARGON` pattern
    (`v1-learning`, `n=1`/`n=2`, `enough to run and learn`, `v1 — …`) must be ABSENT from EVERY file in
    that set. breakdown re-ratification is labelled Experimental with a plain graduation line; a Maturity
    definition (Stable + Experimental + graduation) exists in PRINCIPLES.md.

    v1.7.5 closes a false-green: v1.7.4 claimed to enforce a zero-jargon grep but its pattern set held
    only `v1-learning` / `n=[12]`, so `v1 — "enough to run and learn"` survived in `skills/solve/SKILL.md`
    and the plugin README while the validator reported OK, and the root README was never scanned at all.
    (Version references like `v1.6.1` are NOT jargon and are unaffected; `N=1`/`N>1` as a matrix
    denominator in `analysis/SKILL.md` is a different meaning, not jargon — the pattern is lower-case
    `n=1`/`n=2` only.)"""
    plugin = ROOT / "plugins" / "mango"
    for path in operational_text_files():
        if not path.exists():
            continue
        rel = path.relative_to(ROOT)
        try:
            body = path.read_text(encoding="utf-8")
        except OSError as exc:
            check(False, f"maturity: cannot read {rel} ({exc})")
            continue
        for pattern, reason, flags in BANNED_JARGON:
            check(re.search(pattern, body, flags) is None,
                  f"maturity: {rel} must not use {reason} in shipped operational text")
    bd = plugin / "skills" / "breakdown" / "SKILL.md"
    if check(bd.exists(), "maturity: skills/breakdown/SKILL.md is missing"):
        body = bd.read_text(encoding="utf-8")
        check(re.search(r"Experimental", body) is not None,
              "maturity: breakdown must label its re-ratification behaviour Experimental")
        check(re.search(r"graduat", body, re.IGNORECASE) is not None,
              "maturity: breakdown must state a plain graduation condition (Experimental → Stable)")
    # v1.10.0: the Maturity section moved to principles/maturity.md — assert it over the WHOLE
    # PRINCIPLES surface (core + companions) so the relocation cannot drop the check.
    body = principles_text()
    if check(bool(body), "maturity: the PRINCIPLES surface (PRINCIPLES.md + principles/*.md) is missing"):
        check(re.search(r"^##\s*Maturity", body, re.MULTILINE) is not None,
              "maturity: PRINCIPLES.md or principles/maturity.md must carry a Maturity section defining the vocabulary")
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


def validate_no_rationale_in_skills():
    """v1.7.6 — a SKILL.md is DIRECTIVES ONLY (PRINCIPLES.md, 'Skills are directive-only').

    Because prose-IS-behaviour, every token of a runtime-loaded skill is paid on every ticket run.
    Rationale, 'observed failure' war-stories, and historical justification instruct nothing, so they
    are a permanent tax — they belong in CHANGELOG.md or the non-runtime RATIONALE.md. This check
    fails the build if any RATIONALE_MARKERS pattern reappears in a skill body, so the bloat the
    v1.7.6 trim removed cannot creep back one 'observed failure:' at a time.

    v1.10.0 widened the scan from `SKILL.md` to every `skills/*/*.md`: a skill's on-demand companion is
    read at its point of use, so it is runtime-loaded text under exactly the same rule. `principles/*.md`
    stays exempt for the same reason `PRINCIPLES.md` always was — it is the contract doc, not a directive
    surface, and `principles/authoring.md` names RATIONALE.md by design.
    """
    for path in sorted((ROOT / "plugins" / "mango").glob("skills/*/*.md")):
        rel = path.relative_to(ROOT)
        try:
            body = path.read_text(encoding="utf-8")
        except OSError as exc:
            check(False, f"no-rationale: cannot read {rel} ({exc})")
            continue
        for pattern, reason in RATIONALE_MARKERS:
            match = re.search(pattern, body, re.IGNORECASE)
            check(
                match is None,
                f"no-rationale: {rel} carries {reason} "
                f"({'' if match is None else match.group(0)!r}) — skills are directive-only; "
                f"move the why to CHANGELOG.md / RATIONALE.md",
            )


def validate_rationale_doc():
    """v1.7.6 — the 'why' the trim removed must still exist SOMEWHERE, just not on the runtime path.
    RATIONALE.md ships inside the plugin dir beside CHANGELOG.md and is loaded by no skill."""
    path = ROOT / "plugins" / "mango" / "RATIONALE.md"
    if not check(path.exists(), "rationale-doc: plugins/mango/RATIONALE.md must exist (the non-runtime home for the why)"):
        return
    try:
        body = path.read_text(encoding="utf-8")
    except OSError as exc:
        check(False, f"rationale-doc: cannot read plugins/mango/RATIONALE.md ({exc})")
        return
    check(re.search(r"not (loaded|read) at runtime|never loaded at runtime", body, re.IGNORECASE) is not None,
          "rationale-doc: RATIONALE.md must state it is not loaded at runtime")
    check(re.search(r"observed failure", body, re.IGNORECASE) is not None,
          "rationale-doc: RATIONALE.md must actually carry the observed-failure records the skills no longer hold")
    for skill in ("analysis", "design", "execute", "finalise", "breakdown", "refine"):
        check(re.search(rf"\b{skill}\b", body) is not None,
              f"rationale-doc: RATIONALE.md must record the '{skill}' rationale it inherited from the skill")
    # The rationale doc is NOT a skill and must never be pulled onto the runtime path.
    for sk in sorted((ROOT / "plugins" / "mango").glob("skills/*/SKILL.md")):
        check("RATIONALE.md" not in sk.read_text(encoding="utf-8"),
              f"rationale-doc: {sk.relative_to(ROOT)} references RATIONALE.md — that would put the why back on the runtime path")


def validate_eval_parallel():
    """v1.8.0 A1 — the eval dispatches CONCURRENTLY, and every worker runs in its OWN throwaway clone.
    Two hazards make per-worker isolation load-bearing rather than tidy: fixtures whose `execute`
    branches and commits would race inside one shared clone, and `red-baseline` repoints
    `config.test_command`, which under concurrency would flip `.harness.json` under another in-flight
    dispatch. So run.sh must keep: a --workers knob (with a sequential mode for debugging), a
    per-worker provisioning step, a per-JOB harness write, the two-pass collect/assert structure that
    keeps a prompt beside its assertions, and the worker-tree disposal guard proven non-vacuous."""
    runsh = ROOT / "tests" / "eval" / "run.sh"
    if not check(runsh.exists(), "eval-parallel: tests/eval/run.sh is missing"):
        return
    try:
        body = runsh.read_text(encoding="utf-8")
    except OSError as exc:
        check(False, f"eval-parallel: cannot read tests/eval/run.sh ({exc})")
        return
    check(re.search(r"--workers", body) is not None,
          "eval-parallel: run.sh must support --workers N (concurrent dispatch)")
    check(re.search(r"--workers 1", body) is not None,
          "eval-parallel: run.sh must document --workers 1 as the sequential debugging mode")
    check(re.search(r"provision_sandbox", body) is not None,
          "eval-parallel: run.sh must provision one throwaway clone PER WORKER (provision_sandbox)")
    check(re.search(r"write_harness_at", body) is not None,
          "eval-parallel: run.sh must write .harness.json per worker/per job (write_harness_at), so a "
          "fixture that repoints test_command cannot flip it under another in-flight dispatch")
    check(re.search(r"assert_worker_trees_disposed", body) is not None,
          "eval-parallel: run.sh must assert every per-worker clone was disposed")
    check(re.search(r"worker-isolation-guard: catches an undisposed worker tree", body) is not None,
          "eval-parallel: run.sh must prove the disposal guard NON-VACUOUS against an undisposed tree")
    check(re.search(r"assert_checkout_clean", body) is not None,
          "eval-parallel: run.sh must keep the live-checkout guard alongside the per-worker guard")
    check(re.search(r"PHASE=collect", body) is not None and re.search(r"PHASE=assert", body) is not None,
          "eval-parallel: run.sh must keep the two-pass collect/assert structure (a prompt registered "
          "at the same call site that asserts it, so the two cannot drift apart)")
    check(re.search(r"NO TRANSCRIPT", body) is not None,
          "eval-parallel: run.sh must FAIL an assertion whose dispatch was never registered (never "
          "let a missing transcript read as coverage)")
    check(re.search(r"PARTIAL RUN", body) is not None,
          "eval-parallel: run.sh must report an --only run as PARTIAL (never a milestone run)")
    check(re.search(r"cache-hit", body, re.IGNORECASE) is not None,
          "eval-parallel: run.sh must preserve the transcript-cache path through the parallel dispatcher")
    check(re.search(r"harness parameterisation self-test", body, re.IGNORECASE) is not None,
          "eval-parallel: run.sh must self-test that the per-job harness write actually carries the "
          "command it is given (a stray positional once wrote the repo PATH into test_command, "
          "silently breaking the red-baseline fixture's premise while its assertions still passed)")


def validate_assertion_convention():
    """v1.8.0 A2 — assertions may be widened over WORDING/EMPHASIS, never over outcome, and they may
    not be pinned to a single glyph or to emphasis-free spelling. Five assertions were failing on
    demonstrably CORRECT behaviour: `**S**mall` (emphasis inside a word), `0 want-decisions asked` (a
    count-form negative where a negation phrase was demanded), a control reported "unsplit"/"untouched",
    a bold `**before**`, and a `❌` that landed in the work-doc table instead of the response. This
    check locks the fix in place: the shared emphasis-agnostic tokens exist, NO assertion regex is a
    bare glyph again, and the dispatch-free self-test proves each widened token both ways (matches the
    correct wording, still misses the wrong behaviour)."""
    runsh = ROOT / "tests" / "eval" / "run.sh"
    if not check(runsh.exists(), "assertion-convention: tests/eval/run.sh is missing"):
        return
    try:
        body = runsh.read_text(encoding="utf-8")
    except OSError as exc:
        check(False, f"assertion-convention: cannot read tests/eval/run.sh ({exc})")
        return
    for token in ("RE_INVEST_LETTERS", "RE_INVEST_SMALL", "RE_NOT_SPLIT", "RE_ZERO_WANTS",
                  "RE_LAYER_MISMATCH", "RE_BEFORE_CHILD", "RE_BEFORE_GATE", "RE_NO_BLANKET_RERUN"):
        check(re.search(rf"^{token}=", body, re.MULTILINE) is not None,
              f"assertion-convention: run.sh must define the shared emphasis-agnostic token {token}")
    # No assertion may re-pin a single glyph: `assert_contains … '❌'` is exactly the shape that flapped.
    glyph_pinned = re.findall(r"assert_contains[^\n]*'(?:❌|✅|✗)'", body)
    check(not glyph_pinned,
          "assertion-convention: an assertion regex is a bare glyph "
          f"({glyph_pinned[:1]}) — a glyph may be written to the working doc instead of the response; "
          "assert the decision with the layer/outcome tokens instead")
    check(re.search(r"assertion-convention self-test", body) is not None,
          "assertion-convention: run.sh must carry the dispatch-free assertion-convention self-test")
    check(re.search(r"selftest_assertion", body) is not None,
          "assertion-convention: the self-test must judge the SHIPPED regexes (selftest_assertion)")
    check(re.search(r"VACUOUS: also matches the WRONG behaviour", body) is not None,
          "assertion-convention: the self-test must fail a token that also matches the WRONG behaviour")
    check(re.search(r"MISSES the correct transcript", body) is not None,
          "assertion-convention: the self-test must fail a token that misses the CORRECT transcript")


def validate_premise_preflight():
    """v1.8.0 B1 — a phase pointed at a ticket whose referenced sources do not exist must say so and
    STOP, not spend turns on archaeology. `refine` resolves every source the ticket references AS
    ALREADY EXISTING at the top of its scan; a miss emits the counted `PREMISE FALSIFIED: …` and halts
    for the human. Two carve-outs keep it from blocking legitimate work: a **to-be-created** path never
    counts as missing, and an **ambiguous** framing is surfaced rather than blocking. `analysis` carries
    the same check for the path where refine did not run, and the `PREMISE:` counting line is emitted
    every run (zero included) so the check cannot silently not-happen."""
    plugin = ROOT / "plugins" / "mango"
    targets = [
        plugin / "skills" / "refine" / "SKILL.md",
        plugin / "skills" / "analysis" / "SKILL.md",
        # v1.10.0: the refine contract moved to principles/refine.md — assert over the WHOLE surface.
        None,
    ]
    for path in targets:
        if path is None:
            rel, body = "plugins/mango/PRINCIPLES.md + principles/*.md", principles_text()
            if not check(bool(body), f"premise-preflight: {rel} is missing"):
                continue
            _skip_read = True
        else:
            _skip_read = False
            rel = path.relative_to(ROOT)
            if not check(path.exists(), f"premise-preflight: {rel} is missing"):
                continue
        try:
            body = body if _skip_read else path.read_text(encoding="utf-8")
        except OSError as exc:
            check(False, f"premise-preflight: cannot read {rel} ({exc})")
            continue
        check(re.search(r"PREMISE FALSIFIED", body) is not None,
              f"premise-preflight: {rel} must emit `PREMISE FALSIFIED` on an unresolvable referenced source")
        check(re.search(r"PREMISE:", body) is not None,
              f"premise-preflight: {rel} must emit the `PREMISE: <r> … | <m> missing | <a> ambiguous` counting line")
        check(re.search(r"referenced.as.existing|references? .{0,24}as already existing|already existing", body, re.IGNORECASE) is not None,
              f"premise-preflight: {rel} must scope the check to sources referenced AS ALREADY EXISTING")
        check(re.search(r"to.be.created", body, re.IGNORECASE) is not None,
              f"premise-preflight: {rel} must carve out a TO-BE-CREATED path (it never counts as missing)")
        check(re.search(r"ambiguous", body, re.IGNORECASE) is not None,
              f"premise-preflight: {rel} must SURFACE an ambiguous reference rather than block on it")
        check(re.search(r"resolvable", body, re.IGNORECASE) is not None,
              f"premise-preflight: {rel} must scope the check to a RESOLVABLE identifier (a path / file / "
              f"symbol / config key / table a grep can decide)")
        check(re.search(r"prose noun", body, re.IGNORECASE) is not None,
              f"premise-preflight: {rel} must classify a PROSE NOUN as ambiguous, never a falsified premise "
              f"(locating a described thing is ordinary analysis work)")
        check(re.search(r"STOP|halt", body) is not None,
              f"premise-preflight: {rel} must STOP for the human on a falsified premise")
        check(re.search(r"archaeolog|hunt|reconstruct|renamed", body, re.IGNORECASE) is not None,
              f"premise-preflight: {rel} must forbid the archaeology (rename hunt / history reconstruction) it replaces")
    fixtures = ROOT / "tests" / "eval" / "fixtures"
    check((fixtures / "premise-falsified.md").exists(),
          "premise-preflight: tests/eval/fixtures/premise-falsified.md must exist (the firing case)")
    check((fixtures / "premise-to-be-created.md").exists(),
          "premise-preflight: tests/eval/fixtures/premise-to-be-created.md must exist (the negative control — "
          "a guard that fires on a to-be-created path would block every net-new ticket)")


def validate_claude_md_hoist():
    """v1.8.0 B2 — the harness basics and mango's standing constraints are otherwise re-derived every
    session and re-read at every phase boundary. `init` hoists them into the project's `CLAUDE.md` as a
    fenced, regenerable `mango:standing-context` block: the governing config, the standing constraints,
    and a POINTER to `config.rulebook_path` — never a copy of the rules (a copy goes stale and competes
    with the source), and never a secret (CLAUDE.md is committed context). `doctor` reports the block's
    presence as informational only, so it can never gate the lifecycle. This repo's own CLAUDE.md
    carries the same block."""
    plugin = ROOT / "plugins" / "mango"
    init = plugin / "skills" / "init" / "SKILL.md"
    if check(init.exists(), "claude-md-hoist: skills/init/SKILL.md is missing"):
        body = init.read_text(encoding="utf-8")
        check(re.search(r"CLAUDE\.md", body) is not None,
              "claude-md-hoist: init must write the standing context into CLAUDE.md")
        check(re.search(r"mango:standing-context", body) is not None,
              "claude-md-hoist: init must fence the block with the `mango:standing-context` marker")
        check(re.search(r"pointer", body, re.IGNORECASE) is not None
              and re.search(r"rulebook_path", body) is not None,
              "claude-md-hoist: init must write a POINTER to config.rulebook_path, not a copy of the rules")
        check(re.search(r"never a copy|not a copy|never .{0,20}cop(y|ies)", body, re.IGNORECASE) is not None,
              "claude-md-hoist: init must state the block is a pointer/summary, never a copy that goes stale")
        check(re.search(r"secret", body, re.IGNORECASE) is not None,
              "claude-md-hoist: init must forbid writing any secret/token into CLAUDE.md")
        check(re.search(r"never overwrite|only .{0,20}between the markers|ask first|leave everything else", body, re.IGNORECASE) is not None,
              "claude-md-hoist: init must not rewrite an existing CLAUDE.md outside its own block")
    doc = plugin / "skills" / "doctor" / "SKILL.md"
    if check(doc.exists(), "claude-md-hoist: skills/doctor/SKILL.md is missing"):
        body = doc.read_text(encoding="utf-8")
        check(re.search(r"mango:standing-context", body) is not None,
              "claude-md-hoist: doctor must check for the CLAUDE.md standing-context block")
        check(re.search(r"[Nn]ever ❌|never blocks|informational", body) is not None,
              "claude-md-hoist: doctor's CLAUDE.md check must be informational — it may never gate the lifecycle")
    own = ROOT / "CLAUDE.md"
    if check(own.exists(), "claude-md-hoist: repo-root CLAUDE.md must carry this repo's standing context"):
        body = own.read_text(encoding="utf-8")
        check(re.search(r"mango:standing-context", body) is not None,
              "claude-md-hoist: root CLAUDE.md must carry the `mango:standing-context` marker block")
        check(re.search(r"scripts/validate\.py", body) is not None
              and re.search(r"tests/eval/run\.sh", body) is not None,
              "claude-md-hoist: root CLAUDE.md must point at both gates (validate.py and the behavioural eval)")
        check(re.search(r"PRINCIPLES\.md", body) is not None,
              "claude-md-hoist: root CLAUDE.md must point at PRINCIPLES.md as the binding contract")
        check(re.search(r"prose IS behaviour|prose-IS-behaviour", body, re.IGNORECASE) is not None,
              "claude-md-hoist: root CLAUDE.md must carry the prose-IS-behaviour standing constraint")
        # Committed context: pointers only. A literal credential-looking assignment must never appear.
        check(re.search(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*\S", body) is None,
              "claude-md-hoist: root CLAUDE.md must contain no secret/token value (pointers only)")


def validate_learning_loop():
    """v1.9.0 — the learning loop: lessons split into atomic CLAIMS, classified (a PROPOSAL), recalled
    ADVISORILY, deduped for recurrence/supersession, and — decisively — falsification-checked BEFORE the
    human ratification gate, because recurrence measures how often a claim was RESTATED, not CHECKED.
    Every destination is PROJECT-owned; nothing the loop does edits a mango file. Each assertion below is
    falsifiable against the shipped text: the pieces exist, the ordering holds, and both non-vacuity
    directions have a fixture."""
    plugin = ROOT / "plugins" / "mango"
    finalise = plugin / "skills" / "finalise" / "SKILL.md"
    claim_tpl = plugin / "templates" / "claim-record.md"

    def body_of(path):
        rel = path.relative_to(ROOT)
        if not check(path.exists(), f"learning-loop: {rel} is missing"):
            return None
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            check(False, f"learning-loop: cannot read {rel} ({exc})")
            return None

    # --- The contract: the PRINCIPLES surface carries the six types, both tiebreaks, and the five
    #     invariants. v1.10.0 relocated it to principles/learning-loop.md, read on demand at finalise's
    #     step 3a — so assert over core + companions, never one file.
    pb = principles_text() or None
    if pb is not None:
        check(re.search(r"##\s*The learning loop", pb) is not None,
              "learning-loop: PRINCIPLES.md must carry a `The learning loop` section (the binding contract)")
        for label in ("tool-constraint", "generalisable heuristic", "skill-gap",
                      "world-fact", "ground-truth", "adjudicated non-defect"):
            check(re.search(re.escape(label), pb, re.IGNORECASE) is not None,
                  f"learning-loop: PRINCIPLES.md must name claim type '{label}' in the six-type table")
        check(re.search(r"1\s*vs\s*4", pb, re.IGNORECASE) is not None,
              "learning-loop: PRINCIPLES.md must state the 1-vs-4 tiebreak (an imaginable gate → type 1)")
        check(re.search(r"2\s*vs\s*3", pb, re.IGNORECASE) is not None,
              "learning-loop: PRINCIPLES.md must state the 2-vs-3 tiebreak (type 3 only if a doable check "
              "was demonstrably skipped in that run)")
        check(re.search(r"never (auto-)?self-modif|self-modification|never self-modify", pb, re.IGNORECASE) is not None,
              "learning-loop: PRINCIPLES.md must forbid self-modification (auto-apply / self-patch)")
        check(re.search(r"auto-appl|self-patch", pb, re.IGNORECASE) is not None,
              "learning-loop: PRINCIPLES.md must name auto-apply / self-patch as forbidden")
        check(re.search(r"carr(?:ies|y)\s+nothing\s+home", pb, re.IGNORECASE) is not None,
              "learning-loop: PRINCIPLES.md must state the loop is PROJECT-LOCAL (mango carries nothing home)")
        check(re.search(r"never copied into `?CLAUDE\.md`?", pb, re.IGNORECASE) is not None,
              "learning-loop: PRINCIPLES.md must state a promoted rule is NEVER copied into CLAUDE.md "
              "(CLAUDE.md carries only the rule-book pointer)")
        check(re.search(r"no auto-retire|there is no auto-retire", pb, re.IGNORECASE) is not None,
              "learning-loop: PRINCIPLES.md must state a human marks a claim `retired:` — there is no auto-retire")

    # --- The claim-record shape: one shape the writer and the reader share.
    cb = body_of(claim_tpl)
    if cb is not None:
        for field in ("type:", "evidence:", "handle: symbol:", "area:", "sub-shape:", "re-raise:",
                      "expiry:", "verified-at:", "seen:", "supersedes:", "retired:", "status: proposed"):
            check(field in cb,
                  f"learning-loop: templates/claim-record.md must define the `{field}` field")

    # --- finalise owns split → classify → recurrence → FALSIFY → propose.
    fb = body_of(finalise)
    if fb is not None:
        # (1) splitter
        check(re.search(r"atomic claim", fb, re.IGNORECASE) is not None
              and re.search(r"`CLAIMS:\s*<c>\s*claim\(s\) from\s*<e>", fb) is not None,
              "learning-loop: finalise must split each lesson into atomic claims and emit the "
              "`CLAIMS: <c> claim(s) from <e> lesson entr(ies) …` counting line")
        check(re.search(r"T1=.{0,4}T2=.{0,4}T3=.{0,4}T4=.{0,4}T5=.{0,4}T6=", fb) is not None,
              "learning-loop: the CLAIMS line must count all six types (T1..T6), so a type cannot be dropped")
        # (2) classifier emits type + evidence + handle/area, and only PROPOSES
        check(re.search(r"type \+ evidence \+", fb, re.IGNORECASE) is not None,
              "learning-loop: finalise's classifier must emit type + evidence + the recall handle")
        check(re.search(r"PROPOSAL|PROPOSES", fb) is not None
              and re.search(r"status: proposed", fb) is not None,
              "learning-loop: finalise's classification must be a PROPOSAL (status: proposed) the human confirms")
        check(re.search(r"classify-and-act", fb, re.IGNORECASE) is not None,
              "learning-loop: finalise must forbid classify-and-act")
        # (3) recurrence + supersession
        check(re.search(r"`RECURRENCE:\s*<n>\s*recurring", fb) is not None,
              "learning-loop: finalise must emit the `RECURRENCE: <n> recurring | …` counting line")
        check(re.search(r"supersed", fb, re.IGNORECASE) is not None
              and re.search(r"retired", fb, re.IGNORECASE) is not None,
              "learning-loop: finalise must REPLACE a narrowed/falsified claim (supersedes) and mark the old "
              "one retired")
        check(re.search(r"never delete", fb, re.IGNORECASE) is not None,
              "learning-loop: finalise must state retiring never deletes the old record (history stays)")
        # (4) the falsification gate, and its ORDERING before ratification
        check(re.search(r"`FALSIFY:\s*<c>\s*candidate\(s\) checked", fb) is not None,
              "learning-loop: finalise must emit the `FALSIFY: <c> candidate(s) checked | …` counting line")
        check(re.search(r"still true", fb, re.IGNORECASE) is not None
              and re.search(r"cheaply verifiable|cheaply check", fb, re.IGNORECASE) is not None
              and re.search(r"only repeated|not just repeated|or only repeated", fb, re.IGNORECASE) is not None,
              "learning-loop: the falsification check must ask all three questions — still true? cheaply "
              "verifiable? checked, or only repeated?")
        check(re.search(r"BLOCKED from\s+promotion", fb) is not None,
              "learning-loop: a falsified / not-cheaply-checkable candidate must be BLOCKED from promotion")
        i_falsify = fb.find("FALSIFY:")
        i_promote = fb.find("PROMOTION:")
        check(i_falsify != -1 and i_promote != -1 and i_falsify < i_promote,
              "learning-loop: the FALSIFY gate must be documented BEFORE the PROMOTION step — falsification "
              "sits in FRONT of the human ratification gate, never after it")
        check(re.search(r"restated", fb, re.IGNORECASE) is not None,
              "learning-loop: finalise must state recurrence measures RESTATEMENT, not truth")
        # (5) promotion is human-gated, and every destination is PROJECT-owned
        check(re.search(r"`PROMOTION:\s*<p>\s*proposed\s*\|\s*<k>\s*human-ratified", fb) is not None,
              "learning-loop: finalise must emit the `PROMOTION: <p> proposed | <k> human-ratified | …` line")
        check(re.search(r"mango files written: 0", fb) is not None,
              "learning-loop: the PROMOTION line must carry `mango files written: 0` — the falsifiable form "
              "of lessons-never-modify-mango")
        check(re.search(r"only after an explicit per-claim ratify", fb, re.IGNORECASE) is not None,
              "learning-loop: a promotion write may happen ONLY after an explicit per-claim human ratify")
        for key in ("config.rulebook_path", "config.agent_brief_path", "config.gotchas_path",
                    "config.drift_path", "config.design_doc_path", "config.skill_gap_path"):
            check(key in fb,
                  f"learning-loop: finalise must name the PROJECT-owned destination {key}")
        # (6) type 3 never reaches mango; type 5 sub-shapes split; type 6 carries an expiry
        check(re.search(r"does NOT promote into mango", fb) is not None,
              "learning-loop: finalise must state type 3 does NOT promote into mango (it is a maintainer SIGNAL)")
        check(re.search(r"no lesson,?\s*\n?\s*however", fb, re.IGNORECASE) is not None
              or re.search(r"however recurrent or ratified, modifies mango", fb, re.IGNORECASE) is not None,
              "learning-loop: finalise must state no lesson — however recurrent or ratified — modifies mango")
        check(re.search(r"descriptive / normative / environment|descriptive.{0,40}normative.{0,40}environment",
                        fb, re.IGNORECASE) is not None,
              "learning-loop: finalise must split type 5's sub-shapes (descriptive / normative / environment)")
        check(re.search(r"verified-at", fb) is not None,
              "learning-loop: finalise must stamp a type-5 ENVIRONMENT claim with `verified-at:` (it rots)")
        check(re.search(r"mandatory `expiry:`|`expiry:`\*\*|carrying its `expiry:`", fb) is not None,
              "learning-loop: finalise must require an `expiry:` condition on every type-6 claim")
        check(re.search(r"process claim in the code rule book", fb, re.IGNORECASE) is not None,
              "learning-loop: finalise must forbid filing a PROCESS claim in the code rule book")

    # --- Advisory recall at refine AND analysis: surfaces only, blocks nothing, skips retired.
    for name in ("refine", "analysis"):
        rb = body_of(plugin / "skills" / name / "SKILL.md")
        if rb is None:
            continue
        check(re.search(r"`RECALL:\s*<n>\s*claim\(s\) surfaced", rb) is not None,
              f"learning-loop: {name} must emit the `RECALL: <n> claim(s) surfaced | …` counting line")
        check(re.search(r"advisory \(blocks nothing\)", rb) is not None,
              f"learning-loop: {name}'s RECALL line must declare itself advisory (blocks nothing)")
        check(re.search(r"never (injects|inject)", rb, re.IGNORECASE) is not None
              and re.search(r"never block", rb, re.IGNORECASE) is not None,
              f"learning-loop: {name} must state recall never injects a requirement and never blocks a gate")
        check(re.search(r"by\s*\*{0,2}SYMBOL|by \*\*symbol\*\*|handle: symbol", rb, re.IGNORECASE) is not None,
              f"learning-loop: {name} must recall type 1 by SYMBOL")
        check(re.search(r"by\s*\*{0,2}AREA", rb, re.IGNORECASE) is not None
              and re.search(r"not (by )?a? ?symbol|not by symbol", rb, re.IGNORECASE) is not None,
              f"learning-loop: {name} must recall type 5 by AREA, explicitly NOT by symbol")
        check(re.search(r"re-raise|would otherwise be re-raised", rb, re.IGNORECASE) is not None,
              f"learning-loop: {name} must recall type 6 by the finding that would otherwise be re-raised")
        check(re.search(r"`retired:`", rb) is not None
              and re.search(r"SKIPPED|skipped", rb) is not None,
              f"learning-loop: {name} must SKIP a `retired:` claim during recall")

    # --- Reuse, not rebuild: codify lands the rule-book write; init/doctor own the CLAUDE.md wiring.
    cd = body_of(plugin / "skills" / "codify" / "SKILL.md")
    if cd is not None:
        check(re.search(r"learning loop", cd, re.IGNORECASE) is not None,
              "learning-loop: codify must accept a promoted claim into its provisional→ratify flow")
        check(re.search(r"never into `CLAUDE\.md`", cd) is not None,
              "learning-loop: codify must state the promoted rule goes in the rule book, never into CLAUDE.md")
        check(re.search(r"doctor.{0,80}pointer|pointer.{0,80}doctor", cd, re.IGNORECASE | re.DOTALL) is not None,
              "learning-loop: codify must require doctor green on the CLAUDE.md → rule-book pointer before a "
              "promotion counts as done")

    # --- The PROJECT-owned destination keys ship in the example harness (and are README-documented by
    #     validate_doc_consistency, which reads every top-level key).
    example = load_json(plugin / "config" / "harness.example.json")
    if isinstance(example, dict):
        for key in ("skill_gap_path", "gotchas_path", "drift_path", "agent_brief_path"):
            check(key in example,
                  f"learning-loop: harness.example.json must ship the loop-destination key '{key}'")

    # --- Fixtures: every piece has one, and both non-vacuity directions are covered.
    fixtures = ROOT / "tests" / "eval" / "fixtures"
    required = {
        "lesson-claim-split": "a bundled lesson splits into the right claim count",
        "recall-symbol-type1": "type-1 recall fires on a matching symbol and NOT otherwise",
        "recall-area-type5": "type-5 recall fires by AREA while symbol recall does not",
        "recall-type6-expiry": "type-6 is recalled by the re-raised finding and carries its expiry",
        "recall-retired-skipped": "a `retired:` claim is skipped by recall",
        "recurrence-supersession": "recurrence flags a twice-seen claim; supersession replaces + retires",
        "falsify-blocks-promotion": "a recurring-but-FALSE claim is BLOCKED from promotion",
        "falsify-true-claim-promotes": "the non-vacuous control — a recurring-and-TRUE claim passes the gate",
        "promotion-human-gated": "promotion PROPOSES only; no project file written without a human ratify",
        "promotion-rulebook-wiring": "a ratified rule lands in rulebook_path, never in CLAUDE.md",
        "loop-project-local": "every loop output path is inside the PROJECT repo; no mango file is written",
    }
    for name, why in required.items():
        check((fixtures / f"{name}.md").exists(),
              f"learning-loop: tests/eval/fixtures/{name}.md must exist ({why})")
    runsh = ROOT / "tests" / "eval" / "run.sh"
    rs = body_of(runsh)
    if rs is not None:
        for name in required:
            check(re.search(rf"run_fixture {re.escape(name)} ", rs) is not None,
                  f"learning-loop: tests/eval/run.sh must dispatch the {name} fixture "
                  "(an unregistered fixture is not coverage)")
            check(re.search(rf"\[{re.escape(name)}\]=", rs) is not None,
                  f"learning-loop: run.sh's FIXTURE_SKILLS map must key {name} to the skill(s) it exercises")


def validate_host_adaptation():
    """v1.9.1 — one mango, made HOST-AWARE (never a fork). Three mechanisms that exist on some hosts and
    not others must degrade gracefully instead of being assumed: (1) the always-on context file is
    RESOLVED (`config.context_file` → an `AGENTS.md` a `CLAUDE.md` merely imports → `CLAUDE.md`), never
    hardcoded, so the hoist lands in the file the host actually loads; (2) where usage is not surfaced,
    `unmeasured` is the honest, COMPLETE value and a fabricated number is forbidden; (3) the ask-the-human
    mechanism names no single host tool — the host's question UI if present, else numbered options in
    chat. Every assertion is falsifiable against the shipped text. Nothing here changes a gate's
    decision: which file / which mechanism only."""
    plugin = ROOT / "plugins" / "mango"

    def body_of(path):
        rel = path.relative_to(ROOT)
        if not check(path.exists(), f"host-adaptation: {rel} is missing"):
            return None
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            check(False, f"host-adaptation: cannot read {rel} ({exc})")
            return None

    # --- (1) The always-on context file is resolved, not assumed — in BOTH init and doctor.
    for name in ("init", "doctor"):
        b = body_of(plugin / "skills" / name / "SKILL.md")
        if b is None:
            continue
        check(re.search(r"config\.context_file", b) is not None,
              f"host-adaptation: {name} must honour `config.context_file` as the explicit always-on-file answer")
        check(re.search(r"AGENTS\.md", b) is not None,
              f"host-adaptation: {name} must handle the AGENTS-first host (AGENTS.md as the always-on file)")
        check(re.search(r"import", b, re.IGNORECASE) is not None,
              f"host-adaptation: {name} must detect a CLAUDE.md that merely IMPORTS the real always-on file")
        check(re.search(r"do not assume `?CLAUDE\.md`?", b, re.IGNORECASE) is not None,
              f"host-adaptation: {name} must say plainly not to assume CLAUDE.md is the always-on file")
        check(re.search(r"default to `?CLAUDE\.md`?|otherwise `?CLAUDE\.md`?", b, re.IGNORECASE) is not None,
              f"host-adaptation: {name} must keep CLAUDE.md as the DEFAULT (a Claude-Code project is unchanged)")
    ib = body_of(plugin / "skills" / "init" / "SKILL.md")
    if ib is not None:
        check(re.search(r"record the resolved path in\s*\n?\s*`?config\.context_file", ib, re.IGNORECASE) is not None,
              "host-adaptation: init must RECORD the resolved context file in config.context_file so doctor "
              "and every later phase read the same answer")
        check(re.search(r"never a copy", ib, re.IGNORECASE) is not None,
              "host-adaptation: the hoist stays a POINTER, never a copy, whichever file it lands in")
    db = body_of(plugin / "skills" / "doctor" / "SKILL.md")
    if db is not None:
        check(re.search(r"[Pp]rint the resolved path", db) is not None,
              "host-adaptation: doctor must print WHICH file it judged (an invisible resolution is unreviewable)")
        check(re.search(r"host does not auto-?load", db, re.IGNORECASE) is not None,
              "host-adaptation: doctor must ⚠ when the block sits only in a file the host does not auto-load")
        check(re.search(r"[Nn]ever ❌|never blocks|informational", db) is not None,
              "host-adaptation: doctor's context-file check stays INFORMATIONAL — it may never gate the lifecycle")

    # --- The config key ships and is documented (doc-consistency also reads every top-level key).
    example = load_json(plugin / "config" / "harness.example.json")
    if isinstance(example, dict):
        check(example.get("context_file") == "CLAUDE.md",
              "host-adaptation: harness.example.json must ship `context_file` defaulting to CLAUDE.md")

    # --- (2) `unmeasured` is the honest, COMPLETE value where no usage is surfaced; no fabrication.
    for name in ("solve", "finalise"):
        b = body_of(plugin / "skills" / name / "SKILL.md")
        if b is None:
            continue
        check(re.search(r"unmeasured \(host does not surface usage\)", b) is not None,
              f"host-adaptation: {name} must bless `unmeasured (host does not surface usage)` as the expected "
              f"value on a host that surfaces no usage block")
        check(re.search(r"invent|fabricat", b, re.IGNORECASE) is not None,
              f"host-adaptation: {name} must forbid inventing/fabricating a token number")
    fb = body_of(plugin / "skills" / "finalise" / "SKILL.md")
    if fb is not None:
        check(re.search(r"is COMPLETE and\s*\n?\s*passes", fb) is not None,
              "host-adaptation: finalise's completeness gate must PASS a ledger whose rows all read "
              "`unmeasured (host does not surface usage)` — the gate checks presence, never that a number "
              "was obtained")

    # --- (3) No single ask-the-human tool is assumed.
    rb = body_of(plugin / "skills" / "refine" / "SKILL.md")
    if rb is not None:
        check(re.search(r"host's typed question UI", rb, re.IGNORECASE) is not None,
              "host-adaptation: refine must phrase the ask as the HOST's question UI, not a named tool")
        check(re.search(r"numbered", rb, re.IGNORECASE) is not None,
              "host-adaptation: refine must give the host-neutral fallback — numbered options in plain chat")
        check(re.search(r"[Nn]ever assume a specific host\s*\n?\s*tool", rb) is not None
              and re.search(r"never skip the question", rb, re.IGNORECASE) is not None,
              "host-adaptation: refine must never assume a specific host tool exists, and never skip the "
              "question because one is missing")
    # v1.10.0: the want-decision contract moved to principles/refine.md — whole surface.
    pb = principles_text() or None
    if pb is not None:
        check(re.search(r"host's typed question UI", pb, re.IGNORECASE) is not None
              and re.search(r"numbered options", pb, re.IGNORECASE) is not None,
              "host-adaptation: PRINCIPLES.md's want-decision contract must be host-neutral (question UI "
              "if present, else numbered options)")

    # --- Fixtures: both directions of the context-file resolution (default held AND AGENTS-first).
    fixtures = ROOT / "tests" / "eval" / "fixtures"
    required = {
        "host-context-file-default": "a CLAUDE.md project still targets CLAUDE.md (the default is unchanged)",
        "host-context-file-agents": "an AGENTS-first project targets AGENTS.md, not the importing CLAUDE.md",
    }
    for name, why in required.items():
        check((fixtures / f"{name}.md").exists(),
              f"host-adaptation: tests/eval/fixtures/{name}.md must exist ({why})")
    rs = body_of(ROOT / "tests" / "eval" / "run.sh")
    if rs is not None:
        for name in required:
            check(re.search(rf"run_fixture {re.escape(name)} ", rs) is not None,
                  f"host-adaptation: tests/eval/run.sh must dispatch the {name} fixture "
                  "(an unregistered fixture is not coverage)")
            check(re.search(rf"\[{re.escape(name)}\]=", rs) is not None,
                  f"host-adaptation: run.sh's FIXTURE_SKILLS map must key {name} to the skill(s) it exercises")


def validate_output_discipline():
    """v1.9.1 — four additive output-discipline directives. Each is a directive on what gets WRITTEN, not
    a change to whether any gate fires: (4) a ran-it claim is recorded as PASTED empirical output, never
    prose about it; (5) a red golden is a behaviour change to explain and ratify, never a number to bump;
    (6) a tool/API docstring describes DELIVERED behaviour — it is the interface contract the caller
    reads; (7) every change-list row names its blast radius, the side-effect surface a reviewer should
    check."""
    plugin = ROOT / "plugins" / "mango"

    def body_of(path):
        rel = path.relative_to(ROOT)
        if not check(path.exists(), f"output-discipline: {rel} is missing"):
            return None
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            check(False, f"output-discipline: cannot read {rel} ({exc})")
            return None

    ex = body_of(plugin / "skills" / "execute" / "SKILL.md")
    fi = body_of(plugin / "skills" / "finalise" / "SKILL.md")
    de = body_of(plugin / "skills" / "design" / "SKILL.md")
    tk = body_of(plugin / "templates" / "ticket.md")

    # --- (4) empirical output, pasted — in execute (the record) and finalise (the PR body).
    for name, b in (("execute", ex), ("finalise", fi)):
        if b is None:
            continue
        check(re.search(r"EMPIRICAL OUTPUT|empirical output", b) is not None,
              f"output-discipline: {name} must require the EMPIRICAL OUTPUT of a ran-it claim")
        check(re.search(r"verbatim", b, re.IGNORECASE) is not None
              and re.search(r"paste", b, re.IGNORECASE) is not None,
              f"output-discipline: {name} must require the actual output PASTED VERBATIM")
        check(re.search(r"not a (prose )?description|never a summary|prose[^.]{0,64}not[^.]{0,16}a record|"
                        r"can promise more than", b, re.IGNORECASE) is not None,
              f"output-discipline: {name} must reject a prose description standing in for the output")
    if ex is not None:
        check(re.search(r"did not run it", ex, re.IGNORECASE) is not None
              and re.search(r"unproven", ex, re.IGNORECASE) is not None,
              "output-discipline: execute must require saying so + marking the claim unproven when a "
              "command was not actually run")
        check(re.search(r"failed[^.]{0,40}verbatim|paste the failure verbatim", ex, re.IGNORECASE) is not None,
              "output-discipline: a FAILING command's output must be pasted verbatim too (not summarised)")

    # --- (5) a changed golden is a behaviour change.
    if ex is not None:
        check(re.search(r"golden", ex, re.IGNORECASE) is not None
              and re.search(r"snapshot", ex, re.IGNORECASE) is not None,
              "output-discipline: execute must cover the golden/snapshot case")
        check(re.search(r"BEHAVIOUR CHANGE, not a number to bump", ex) is not None,
              "output-discipline: execute must state a changed golden is a BEHAVIOUR CHANGE, not a number "
              "to bump")
        check(re.search(r"do not reflexively re-?record", ex, re.IGNORECASE) is not None,
              "output-discipline: execute must forbid reflexively re-recording the golden to match new output")
        check(re.search(r"ratif", ex, re.IGNORECASE) is not None,
              "output-discipline: an intentional golden change must be RATIFIED at a gate before the golden "
              "is updated")
        check(re.search(r"defect in the change", ex, re.IGNORECASE) is not None,
              "output-discipline: an unintentional golden change is a DEFECT — the fix is the code, never "
              "the golden")

    # --- (6) docstring = delivered behaviour; it IS the interface contract.
    if ex is not None:
        check(re.search(r"docstring", ex, re.IGNORECASE) is not None,
              "output-discipline: execute must carry the docstring directive")
        check(re.search(r"interface\s*\n?\s*contract", ex, re.IGNORECASE) is not None,
              "output-discipline: execute must state the docstring IS the interface contract")
        check(re.search(r"MCP tool\s*\n?\s*description", ex, re.IGNORECASE) is not None,
              "output-discipline: execute must name the MCP tool description a client LLM reads as the "
              "sharpest case")
        check(re.search(r"actually does", ex, re.IGNORECASE) is not None
              and re.search(r"not from what the ticket intended|not[^.]{0,40}intent", ex, re.IGNORECASE) is not None,
              "output-discipline: the docstring must describe what the code ACTUALLY does, not the intent")

    # --- (7) a blast-radius cell per change-list row, in the skill AND the template.
    if de is not None:
        check(re.search(r"\|\s*\*{0,2}blast radius\*{0,2}\s*\*{0,2},|`blast radius`|\*\*blast radius\*\*",
                        de, re.IGNORECASE) is not None,
              "output-discipline: design's change-list must carry a `blast radius` column")
        check(re.search(r"side-effect surface", de, re.IGNORECASE) is not None,
              "output-discipline: design must define the blast-radius cell as the SIDE-EFFECT SURFACE")
        check(re.search(r"none identified", de, re.IGNORECASE) is not None
              and re.search(r"never leave the cell blank|blank is not", de, re.IGNORECASE) is not None,
              "output-discipline: `none identified` is allowed, a BLANK blast-radius cell is not")
        check(re.search(r"where to look", de, re.IGNORECASE) is not None,
              "output-discipline: design must say the blast radius tells a reviewer WHERE TO LOOK")
    if tk is not None:
        check(re.search(r"Blast radius \(side-effect surface\)", tk, re.IGNORECASE) is not None,
              "output-discipline: templates/ticket.md's change-list table must carry the blast-radius column")
        check(re.search(r"Empirical output — PASTED, not described", tk) is not None,
              "output-discipline: templates/ticket.md Phase 3 must carry the pasted-empirical-output slot")
        check(re.search(r"Golden/snapshot change", tk) is not None,
              "output-discipline: templates/ticket.md Phase 3 must carry the golden/snapshot slot")


def validate_path_resolution():
    """v1.10.0 (A3) — every mango-shipped file resolves through a DOCUMENTED order, not through one host
    env var. `${CLAUDE_PLUGIN_ROOT}` is unset on some hosts, which made `templates/*.md` unreachable and
    silently degraded the steps that read them. The order lives once in the always-loaded PRINCIPLES core,
    every skill carries the one-line `<mango>` definition (so the notation is never used undefined), and no
    skill or companion may point at `${CLAUDE_PLUGIN_ROOT}/templates/...` any more. The check is on the
    ORDER's completeness, not on a token being present: all four steps, the never-hardcode prohibition,
    and an explicit unreachable branch must each be stated."""
    plugin = ROOT / "plugins" / "mango"
    core = plugin / "PRINCIPLES.md"
    if not check(core.exists(), "path-resolution: plugins/mango/PRINCIPLES.md is missing"):
        return
    body = core.read_text(encoding="utf-8")
    check(re.search(r"^##\s*Resolving a mango-shipped path", body, re.MULTILINE) is not None,
          "path-resolution: PRINCIPLES.md must carry a `Resolving a mango-shipped path` section (the order "
          "lives once, in the always-loaded core)")
    check(re.search(r"\$\{CLAUDE_PLUGIN_ROOT\}", body) is not None,
          "path-resolution: the order must name `${CLAUDE_PLUGIN_ROOT}` as step 1 (it is a step, not the contract)")
    check(re.search(r"skill file sits in|currently loaded skill file", body, re.IGNORECASE) is not None,
          "path-resolution: the order must offer locating the plugin root from the loaded skill file (step 2)")
    check(re.search(r"read-only.{0,20}search", body, re.IGNORECASE) is not None,
          "path-resolution: the order must offer a read-only search for the plugin root (step 3)")
    check(re.search(r"UNREACHABLE", body) is not None
          and re.search(r"inline fallback", body, re.IGNORECASE) is not None,
          "path-resolution: the order must have an explicit UNREACHABLE branch naming the inline fallback "
          "(step 4) — a degraded read must never continue as if the file had been read")
    check(re.search(r"never a hardcoded (user )?path|never guess a path", body, re.IGNORECASE) is not None,
          "path-resolution: the order must forbid a hardcoded / guessed path")

    # Every skill defines `<mango>` before using it, and no skill/companion still reads a template
    # through the bare env var.
    for path in sorted(plugin.glob("skills/*/SKILL.md")):
        rel = path.relative_to(ROOT)
        # `promote` is deliberately exempt: it inlines every field it needs and resolves no plugin path,
        # so it runs where no plugin env var exists. validate_promote_skill asserts that exemption.
        if path.parent.name == "promote":
            continue
        sbody = path.read_text(encoding="utf-8")
        check(re.search(r"`<mango>` = this plugin's root", sbody) is not None,
              f"path-resolution: {rel} must define `<mango>` before using it (one line, every skill)")
        check(re.search(r"\$\{CLAUDE_PLUGIN_ROOT\}", sbody) is not None,
              f"path-resolution: {rel}'s `<mango>` definition must still name `${{CLAUDE_PLUGIN_ROOT}}` as step 1")
    for path in sorted(plugin.glob("skills/*/*.md")) + sorted(plugin.glob("principles/*.md")) + [core]:
        rel = path.relative_to(ROOT)
        sbody = path.read_text(encoding="utf-8")
        check(re.search(r"\$\{CLAUDE_PLUGIN_ROOT\}/(templates|principles|skills|config)/", sbody) is None,
              f"path-resolution: {rel} must reach a shipped file through `<mango>/…`, never through a bare "
              "`${CLAUDE_PLUGIN_ROOT}/<dir>/` path (unreachable on a host that does not set it)")


def validate_preload_split():
    """v1.10.0 (E) — `PRINCIPLES.md` is split into an always-loaded core plus on-demand companions, and
    each skill's frontend-only block moved beside it. The saving is only real if the moved text still
    REACHES the agent, so every companion must (a) exist and be non-empty, (b) be named in the core's
    companion index, and (c) carry an explicit, unconditional READ instruction at a point of use — never
    'consult X if relevant', which is the failure mode lazy loading introduces. The index and the
    filesystem must agree in BOTH directions, so neither an orphaned file nor a dangling index row can
    hide."""
    plugin = ROOT / "plugins" / "mango"
    core = plugin / "PRINCIPLES.md"
    if not check(core.exists(), "preload-split: plugins/mango/PRINCIPLES.md is missing"):
        return
    cbody = core.read_text(encoding="utf-8")

    # (a) the core is genuinely a core: the relocated headings are gone from it.
    for heading in ("## Subagent git isolation", "## Maturity", "## Skills are directive-only",
                    "## Descriptive vs normative", "## The learning loop", "## The refine phase",
                    "## Frontend track", "## Token cost"):
        check(heading not in cbody,
              f"preload-split: PRINCIPLES.md still carries the relocated section `{heading}` — the core "
              "must not duplicate a companion (a copy goes stale and competes with its source)")
    # The four principles and the delegation map STAY in the core: every phase needs them.
    for heading in ("## 1. Think before coding", "## 2. Simplicity first", "## 3. Surgical changes",
                    "## 4. Goal-driven execution", "## Model delegation"):
        check(heading in cbody,
              f"preload-split: PRINCIPLES.md core must keep `{heading}` (every phase needs it)")

    # (b) + (c) each companion exists, is indexed, and is READ somewhere unconditionally.
    companions = {
        "git-isolation.md": ["skills/review/SKILL.md"],
        "maturity.md": ["skills/breakdown/SKILL.md"],
        "descriptive-normative.md": ["skills/codify/SKILL.md", "skills/sitemap/SKILL.md",
                                     "skills/db-map/SKILL.md"],
        "learning-loop.md": ["skills/finalise/SKILL.md"],
        "refine.md": ["skills/refine/SKILL.md"],
        # read on the frontend track only, by the four phases that apply it
        "frontend-track.md": ["skills/analysis/SKILL.md", "skills/design/SKILL.md",
                              "skills/execute/SKILL.md", "skills/review/SKILL.md"],
        "token-cost.md": ["skills/budget/SKILL.md"],
        "authoring.md": [],               # maintainer-only: its point of use is CONTRIBUTING.md
    }
    on_disk = {p.name for p in (plugin / "principles").glob("*.md")}
    check(on_disk == set(companions),
          f"preload-split: principles/ holds {sorted(on_disk)} but the check knows {sorted(companions)} — "
          "an unindexed companion is content nobody is told to read")
    for name, readers in companions.items():
        path = plugin / "principles" / name
        if not check(path.exists() and path.stat().st_size > 0,
                     f"preload-split: plugins/mango/principles/{name} must exist and be non-empty"):
            continue
        check(f"`{name}`" in cbody,
              f"preload-split: PRINCIPLES.md's companion index must name `{name}` (a companion missing "
              "from the index is a file no phase knows exists)")
        for rel in readers:
            rbody = (plugin / rel).read_text(encoding="utf-8")
            # The instruction is often line-wrapped, so match READ … <path> … NOW across a bounded
            # window rather than one line — the load-bearing parts are the imperative, the exact path,
            # and NOW (which is what makes it unconditional).
            check(re.search(rf"READ\b.{{0,200}}?`<mango>/principles/{re.escape(name)}`.{{0,120}}?NOW",
                            rbody, re.DOTALL) is not None,
                  f"preload-split: {rel} must carry an explicit `READ <mango>/principles/{name} NOW` "
                  "instruction — an on-demand block with no unconditional read never reaches the agent")
            check(re.search(r"not\s+(a\s+)?consult-if-relevant|unconditional", rbody, re.IGNORECASE) is not None,
                  f"preload-split: {rel}'s read instruction must be unconditional, not consult-if-relevant")
    check(re.search(r"principles/authoring\.md", (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")) is not None,
          "preload-split: CONTRIBUTING.md must point the maintainer at principles/authoring.md — the one "
          "companion with no runtime reader still needs a point of use")

    # The per-skill frontend companions: same contract, keyed on `config.track`.
    for skill in ("analysis", "design", "execute", "review"):
        path = plugin / "skills" / skill / "frontend.md"
        if not check(path.exists() and path.stat().st_size > 0,
                     f"preload-split: skills/{skill}/frontend.md must exist and be non-empty"):
            continue
        sbody = (plugin / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        check(re.search(rf"READ\b.{{0,200}}?`<mango>/skills/{skill}/frontend\.md`.{{0,180}}?NOW",
                        sbody, re.DOTALL) is not None,
              f"preload-split: skills/{skill}/SKILL.md must carry an explicit "
              f"`READ <mango>/skills/{skill}/frontend.md NOW` instruction")
        check(re.search(r"config\.track.{0,40}frontend|track includes frontend", sbody, re.IGNORECASE) is not None
              and re.search(r"not\s+(a\s+)?consult-if-relevant|mandatory read", sbody, re.IGNORECASE) is not None,
              f"preload-split: skills/{skill}/SKILL.md must state the condition under which the companion "
              "is read (`config.track` includes frontend)")
        check(re.search(r"does\s+not\s+resolve", sbody, re.IGNORECASE) is not None,
              f"preload-split: skills/{skill}/SKILL.md must state what it still does when `<mango>` does "
              "not resolve — a missing companion may never turn a required check into no check")


def validate_type2_recall():
    """v1.10.0 (A1) — a type-2 heuristic reaches the next ticket. It is keyed by a class `handle:` (a
    heuristic holds across tools, so neither a symbol nor an area can key it), recall surfaces it on a
    change-shape match, and — the half that matters — `design`'s blast-radius step must ANSWER each
    recalled handle by name. The gate is on the answer ACCOUNTING (`h == t + x`, `u == 0`), not on a field
    being present: a trace must carry the command AND its output, and the only other legal answer is an
    explicit `does not apply because <reason>`, which CLOSES the handle."""
    plugin = ROOT / "plugins" / "mango"
    tpl = (plugin / "templates" / "claim-record.md").read_text(encoding="utf-8")
    check("handle: <class-slug>" in tpl,
          "type2-recall: templates/claim-record.md must define the type-2 `handle: <class-slug>` field")
    check(re.search(r"type-2 claim.{0,60}MUST carry a `handle:`|type-2 claim with no `handle:` is a finding",
                    tpl, re.IGNORECASE | re.DOTALL) is not None,
          "type2-recall: the claim-record must require a `handle:` on every type-2 claim (without one it is "
          "unrecallable and cannot reach the next ticket)")
    ll = principles_text()
    check(re.search(r"\|\s*2\s*\|\s*\*\*generalisable heuristic\*\*.*handle", ll) is not None,
          "type2-recall: the six-type table's type-2 row must name **handle** as its recall key")
    for name in ("refine", "analysis"):
        body = (plugin / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        check(re.search(r"type 2.{0,40}by\s*\*{0,2}HANDLE", body, re.IGNORECASE | re.DOTALL) is not None,
              f"type2-recall: {name} must recall type 2 by HANDLE")
        check(re.search(r"<h> by handle", body) is not None,
              f"type2-recall: {name}'s RECALL counting line must count `<h> by handle`")
        for cue in (r"shared vocabular", r"new core module", r"thread"):
            check(re.search(cue, body, re.IGNORECASE) is not None,
                  f"type2-recall: {name} must name the change-shape trigger /{cue}/ for a type-2 handle")
    d = (plugin / "skills" / "design" / "SKILL.md").read_text(encoding="utf-8")
    check(re.search(r"`HANDLES: <h> recalled \| <t> traced \(command \+ result\) \| "
                    r"<x> does not apply \(reason\) \| <u> unanswered`", d) is not None,
          "type2-recall: design must emit the `HANDLES: <h> recalled | <t> traced … | <u> unanswered` line")
    check(re.search(r"`u` must be 0|`<u> unanswered`.{0,30}0", d) is not None
          and re.search(r"BLOCKS? Gate 2", d, re.IGNORECASE) is not None,
          "type2-recall: an unanswered recalled handle must BLOCK Gate 2")
    check(re.search(r"h.{0,6}must equal.{0,6}`?t \+ x`?|`h` must equal `t \+ x`", d) is not None,
          "type2-recall: design must require `h == t + x` — every recalled handle accounted for")
    check("does not apply because" in d,
          "type2-recall: design must accept the literal `does not apply because <reason>` as a legal, "
          "CLOSING answer (an always-applies gate becomes a tax and gets worked around)")
    check(re.search(r"command you ran and its actual output|command \+ result", d) is not None
          and re.search(r"is \*\*not\*\* a trace", d) is not None,
          "type2-recall: a `traced` answer must carry the command AND its output — a filled cell with no "
          "command is explicitly not a trace (adequacy, not presence)")
    check(re.search(r"`HANDLES: 0 recalled", d) is not None,
          "type2-recall: `h = 0` must close the line with zeros and add no work (no busywork on a ticket "
          "recall surfaced nothing for)")
    check(re.search(r"still advisory", d, re.IGNORECASE) is not None,
          "type2-recall: a recalled handle must stay ADVISORY — answered, never promoted into a "
          "requirement or a matrix row by recall itself")


def validate_recurring_type2_destination():
    """v1.10.0 (A2) — a type-2 claim seen on >=2 tickets may not resolve to `stays in lessons_path`:
    recording it was already the treatment. It routes to the rule book (code) or the project agent brief
    (process), or records an explicit `cannot promote: <reason>`. This REUSES the v1.6 cost-ledger
    content-completeness shape — a real value or an explicit honest marker, never the silent default —
    with the trailing count as the gate. Type 5 is explicitly exempt: all existing project facts
    legitimately stay in `lessons_path`, and sweeping them into a rule book would rot it."""
    plugin = ROOT / "plugins" / "mango"
    f = (plugin / "skills" / "finalise" / "SKILL.md").read_text(encoding="utf-8")
    check(re.search(r"`RECURRING-T2: <n> type-2 claim\(s\) with seen (>=|≥) 2 \| <d> routed to a destination \| "
                    r"<b> cannot promote \(reason\) \| <l> left in lessons_path`", f) is not None,
          "recurring-t2: finalise must emit the `RECURRING-T2: … | <l> left in lessons_path` counting line")
    check(re.search(r"`stays in lessons_path` is \*\*rejected\*\*|may NOT resolve to `stays in lessons_path`",
                    f) is not None,
          "recurring-t2: finalise must REJECT `stays in lessons_path` for a type-2 claim with seen >= 2")
    check(re.search(r"`l` must be 0", f) is not None
          and re.search(r"BLOCKS? finalise", f, re.IGNORECASE) is not None,
          "recurring-t2: any claim left in lessons_path must BLOCK finalise")
    check(re.search(r"blank ledger token\s+cell", f, re.IGNORECASE) is not None,
          "recurring-t2: the rule must name the v1.6 ledger content-gate shape it reuses (a real value or "
          "an explicit named reason, never the silent default) rather than inventing a parallel mechanism")
    check("cannot promote: <reason>" in f,
          "recurring-t2: finalise must offer the explicit `cannot promote: <reason>` resolution so an "
          "unset key or a falsification block SURFACES the claim instead of dropping it")
    check(re.search(r"\*\*Type 5 is untouched", f) is not None,
          "recurring-t2: finalise must state type 5 is UNTOUCHED — a project fact legitimately stays in "
          "lessons_path however often it recurs")
    check(re.search(r"seen\*{0,2}\s*once.{0,40}untouched|recurrence, not presence", f, re.IGNORECASE) is not None,
          "recurring-t2: the trigger must be RECURRENCE, not the mere presence of a type-2 claim")
    i_seen, i_left = f.find("RECURRING-T2:"), f.find("`PROMOTION:")
    check(i_seen != -1 and i_left != -1 and i_seen < i_left,
          "recurring-t2: the destination rule must be documented BEFORE the PROMOTION line it constrains")
    init = (plugin / "skills" / "init" / "SKILL.md").read_text(encoding="utf-8")
    check(re.search(r"`agent_brief_path`", init) is not None,
          "recurring-t2: init must write `agent_brief_path` by name (a promoted PROCESS heuristic has "
          "nowhere to go without it)")
    check(re.search(r"never omit one|Write every learning-loop destination key explicitly", init) is not None,
          "recurring-t2: init must write EVERY loop-destination key explicitly, with its default")
    example = load_json(plugin / "config" / "harness.example.json")
    if isinstance(example, dict):
        check(example.get("agent_brief_path"),
              "recurring-t2: harness.example.json must ship a non-empty `agent_brief_path` default")


def validate_finalise_claim_order():
    """v1.10.0 (A4) — the claim steps run BEFORE the outward-action list. A step at the tail of finalise
    competes with the thing the human is waiting on, and the tail is what gets dropped. Asserted
    positionally (the split/classify/falsify steps precede the outward-action enumeration in the shipped
    text) AND as an explicit directive, so a future reorder cannot silently undo it."""
    f = (ROOT / "plugins" / "mango" / "skills" / "finalise" / "SKILL.md").read_text(encoding="utf-8")
    i_claims = f.find("`CLAIMS: <c> claim(s) from <e>")
    i_falsify = f.find("`FALSIFY: <c> candidate(s) checked")
    i_outward = f.find("**List planned outward actions.**")
    i_gate = f.find("**Require explicit, separate approval per action.**")
    for label, idx in (("CLAIMS", i_claims), ("FALSIFY", i_falsify),
                       ("outward-action list", i_outward), ("final gate", i_gate)):
        check(idx != -1, f"finalise-order: cannot locate the {label} step in finalise/SKILL.md")
    if min(i_claims, i_falsify, i_outward, i_gate) != -1:
        check(i_claims < i_outward and i_falsify < i_outward,
              "finalise-order: the claim steps (split → classify → recurrence → falsify) must appear "
              "BEFORE the outward-action list — a claim step at the tail is the one that gets dropped")
        check(i_outward < i_gate,
              "finalise-order: the outward-action list must still precede the per-action approval gate")
    check(re.search(r"runs BEFORE the PR\s+body and the outward-action list", f) is not None,
          "finalise-order: finalise must STATE that the claim steps run before the PR body and the "
          "outward-action list — position alone is not a directive")
    check(re.search(r"Do not defer any part of\s+it past step 4", f) is not None
          and re.search(r"do not begin step 4", f, re.IGNORECASE) is not None,
          "finalise-order: finalise must forbid deferring any claim step past the PR-body step")


def validate_promote_skill():
    """v1.10.0 (B) — cross-ticket promotion is its own skill because its trigger is RECURRENCE ACROSS
    TICKETS, which a step at the tail of one ticket's finalise structurally cannot see. It must: propose
    only, be type-2 only, be idempotent, route by configured destination, put its counted line FIRST, hold
    the human gate as a question requiring a per-candidate answer, and depend on no host env var. The
    anti-restatement test is asserted too — a 'rule' that merely paraphrases the lesson is the way this
    skill fails while looking successful."""
    plugin = ROOT / "plugins" / "mango"
    path = plugin / "skills" / "promote" / "SKILL.md"
    if not check(path.exists(), "promote: plugins/mango/skills/promote/SKILL.md must exist"):
        return
    body = path.read_text(encoding="utf-8")
    lines = body.count("\n")
    check(lines <= 140,
          f"promote: skills/promote/SKILL.md is {lines} lines — keep it short (a long skill pushes its own "
          "tail out of attention, which is the defect it repairs)")
    check(re.search(r"^\*\*What this does NOT do\.\*\*", body, re.MULTILINE) is not None,
          "promote: the skill must state what it explicitly does NOT do, up front")
    check(re.search(r"`PROMOTE: <n> class\(es\) with recurrence >= 2 \| <p> candidate\(s\) proposed \| "
                    r"<e> already recorded \(skipped\) \| <b> blocked \(reason\) \| rules written: 0`", body) is not None,
          "promote: must emit exactly one counted line, the `PROMOTE: … | rules written: 0` form")
    check(re.search(r"rules written: 0.{0,80}non-zero value", body, re.DOTALL) is not None,
          "promote: `rules written: 0` must be falsifiable — a non-zero value before a ratify is a wrong run")
    i_count, i_gate = body.find("`PROMOTE: <n>"), body.find("## The human gate")
    i_draft = body.find("**Draft one candidate rule")
    check(i_count != -1 and i_draft != -1 and i_count < i_draft,
          "promote: the counted line must be emitted BEFORE the rule proposals — mandatory output never "
          "goes after the part the human is waiting on")
    check(re.search(r"^##\s*Emit this FIRST", body, re.MULTILINE) is not None,
          "promote: the output-first rule must be a section heading, not a buried aside")
    check(re.search(r"recurrence \*\*>= 2\*\*|recurrence\s*\*\*>= 2", body) is not None,
          "promote: the entry condition must be recurrence >= 2, not a schedule")
    check(re.search(r"`verdict: skipped \(recurrence 1\)`", body) is not None,
          "promote: recurrence 1 must propose nothing (the negative control, so this is not a tax)")
    check(re.search(r"already recorded at `?<path>:<line>`?", body) is not None,
          "promote: it must be IDEMPOTENT — a class already recorded at its destination proposes nothing")
    check(re.search(r"Check idempotency BEFORE proposing", body) is not None,
          "promote: the idempotency check must run BEFORE drafting, not after")
    check(re.search(r"whether or not it matched", body) is not None
          and re.search(r"with no command shown is not a check", body) is not None,
          "promote: the idempotency step must report its grep command AND result either way — a skipped "
          "grep and a genuine empty result otherwise produce identical output, so the check could go "
          "missing unnoticed (adequacy, not presence)")
    check(re.search(r"restatement test", body) is not None
          and re.search(r"restatement, not a rule", body) is not None,
          "promote: it must reject a candidate that merely RESTATES the lesson — a vague restatement is "
          "how this skill fails while appearing to succeed")
    check(re.search(r"traceability test", body) is not None
          and re.search(r"invented policy", body) is not None,
          "promote: every clause must quote the lesson text it came from; an unquoted clause is invented "
          "policy and is deleted")
    check(re.search(r"falsifiability test", body) is not None,
          "promote: every candidate must name what would show the rule violated")
    check(re.search(r"answer `ratify`, `reject`, or `edit", body) is not None
          and "?" in body[i_gate:i_gate + 1200],
          "promote: the human gate must be a STOP phrased as a question requiring a per-candidate answer, "
          "not a note that approval is needed")
    check(re.search(r"Silence is not an answer", body) is not None,
          "promote: silence must be explicitly not approval")
    check(re.search(r"^##\s*When NOT to run this", body, re.MULTILINE) is not None,
          "promote: the skill must carry an explicit `When NOT to run this` section")
    check(re.search(r"\$\{CLAUDE_PLUGIN_ROOT\}", body) is None
          and re.search(r"<mango>", body) is None,
          "promote: must depend on no plugin-root resolution at all — its fields are inlined, so it runs "
          "on a host that sets no plugin env var")
    check("config.rulebook_path" in body and "config.agent_brief_path" in body,
          "promote: both configured destinations must be named (code -> rule book, process -> agent brief)")
    check(re.search(r"Never file a process heuristic in the code rule book", body) is not None,
          "promote: a PROCESS heuristic must never be filed in the code rule book")
    check(re.search(r"type-3 signal", body) is not None,
          "promote: a gap in mango itself must route to config.skill_gap_path as a type-3 signal, never "
          "into a mango file")
    check(re.search(r"PROJ-069|PROJ-072|PROJ-080", body) is not None,
          "promote: the worked example must carry real content, not placeholders")

    # Wiring: the orchestrator names it (and says it does NOT invoke it), doctor reports it, README lists it.
    solve = (plugin / "skills" / "solve" / "SKILL.md").read_text(encoding="utf-8")
    check("/mango:promote" in solve,
          "promote: solve must name `/mango:promote` as the cross-ticket pass")
    check(re.search(r"`solve` never invokes it|solve never invokes", solve) is not None,
          "promote: solve must state it does NOT invoke promote (one ticket per run; a cross-ticket pass "
          "is not a lifecycle phase)")
    fin = (plugin / "skills" / "finalise" / "SKILL.md").read_text(encoding="utf-8")
    check("/mango:promote" in fin,
          "promote: finalise must hand a cross-ticket class to `/mango:promote` rather than attempting it")
    doc = (plugin / "skills" / "doctor" / "SKILL.md").read_text(encoding="utf-8")
    check("/mango:promote" in doc,
          "promote: doctor must be aware of promote and report its prerequisites")
    check(re.search(r"promote.{0,400}lessons_path", doc, re.DOTALL) is not None,
          "promote: doctor must check `lessons_path` as promote's corpus prerequisite")
    check(re.search(r"Never ❌", doc[doc.find("/mango:promote"):]) is not None,
          "promote: doctor's promote check must never ❌ (promotion is opt-in and off the lifecycle)")


def validate_v1_10_fixtures():
    """v1.10.0 — each of the five items must be shown to CATCH something, per the inject-then-catch
    standard, and each gate must have its NEGATIVE control so it cannot become a tax. A fixture that
    exists but is not dispatched is not coverage, so both are asserted: the file exists, `run.sh`
    dispatches it, and `FIXTURE_SKILLS` keys it to the skill it exercises (without that key the fixture
    hashes over every skill and never cache-hits)."""
    required = {
        # A1 — type-2 recall by handle, and the design-side answer gate
        "recall-type2-handle": "type-2 recall fires by HANDLE on a change-shape match while the symbol and area claims stay silent",
        "handle-unanswered-blocks": "a recalled handle with no trace and no `does not apply` BLOCKS Gate 2",
        "handle-does-not-apply-closes": "the control — an explicit `does not apply because <reason>` CLOSES the handle",
        "recall-zero-no-busywork": "the control — recall matching nothing closes with zeros and adds no work",
        # A2 — a recurring type-2 claim must leave lessons_path; type 5 must not be swept up
        "recurring-t2-leaves-lessons": "a type-2 claim with seen >= 2 may not resolve to `stays in lessons_path`",
        "type5-stays-in-lessons": "the control — a recurring TYPE-5 claim legitimately stays in lessons_path",
        # A3 — resolution without the host env var
        "template-resolve-no-plugin-root": "the claim-record shape still resolves with ${CLAUDE_PLUGIN_ROOT} unset",
        # B — cross-ticket promote, with both controls
        "promote-two-lessons-one-rule": "two instances of one class yield ONE candidate citing both, nothing written",
        "promote-single-lesson-noop": "the control — recurrence 1 proposes nothing",
        "promote-idempotent": "a re-run on an unchanged corpus proposes nothing new",
        # E — the on-demand split must still reach the agent, on every host
        "ondemand-companion-read": "a relocated block is READ at its point of use and the phase behaves as before",
        "ondemand-read-no-plugin-root": "an on-demand read resolves with ${CLAUDE_PLUGIN_ROOT} unset, and an unreachable companion never means no check",
    }
    fixtures = ROOT / "tests" / "eval" / "fixtures"
    runsh = ROOT / "tests" / "eval" / "run.sh"
    if not check(runsh.exists(), "v1.10-fixtures: tests/eval/run.sh is missing"):
        return
    rs = runsh.read_text(encoding="utf-8")
    for name, why in required.items():
        check((fixtures / f"{name}.md").exists(),
              f"v1.10-fixtures: tests/eval/fixtures/{name}.md must exist ({why})")
        check(re.search(rf"run_fixture {re.escape(name)} ", rs) is not None,
              f"v1.10-fixtures: run.sh must dispatch the {name} fixture "
              "(an unregistered fixture is not coverage)")
        check(re.search(rf"\[{re.escape(name)}\]=", rs) is not None,
              f"v1.10-fixtures: run.sh's FIXTURE_SKILLS map must key {name} to the skill(s) it exercises")
    # The cache key must cover the relocated text, or a companion edit would reuse a stale GREEN.
    check(re.search(r'ls "\$PLUGIN_SRC"/principles/\*\.md', rs) is not None,
          "v1.10-fixtures: run.sh's skills_files must hash every principles/*.md companion — a relocated "
          "block outside the cache key would let a companion edit reuse a stale GREEN transcript")
    check(re.search(r'ls "\$PLUGIN_SRC"/skills/"\$s"/\*\.md', rs) is not None,
          "v1.10-fixtures: run.sh's skills_files must hash a mapped skill's whole directory, so its "
          "on-demand companion is inside the cache key")


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
    validate_worktree_env_parity()
    validate_empty_diff_fallback()
    validate_epic_lesson_owner()
    validate_drift_count_line()
    validate_multi_clause_want()
    validate_solve_workdoc_route()
    validate_maturity_labels()
    validate_workdoc_committed_stub()
    validate_no_rationale_in_skills()
    validate_rationale_doc()
    validate_eval_parallel()
    validate_assertion_convention()
    validate_premise_preflight()
    validate_claude_md_hoist()
    validate_learning_loop()
    validate_host_adaptation()
    validate_output_discipline()
    validate_path_resolution()
    validate_preload_split()
    validate_type2_recall()
    validate_recurring_type2_destination()
    validate_finalise_claim_order()
    validate_promote_skill()
    validate_v1_10_fixtures()
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
