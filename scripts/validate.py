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
                  r"Experimental", r"work_doc_mode", r"separate",
                  r"EPIC LESSON:", r"lessons_path", r"durable lesson", r"close-?out"],
    "analysis": [r"SECTIONS:", r"CLARIFICATION:", r"AC validation", r"Gate 1", r"denominator", r"for each", r"TRACK", r"SURFACES", r"falsifiable", r"manual-check", r"baseline", r"uncodified", r"ratif",
                 r"applicable .{0,12}section", r"change[ -]type", r"enumerate",
                 r"multi-clause", r"one row per clause", r"want-decision"],
    "design": [r"proving test", r"Gate 2", r"risk layer", r"Assumptions", r"coverage-gap", r"layer-match", r"block", r"DESIGN\.md", r"data-core", r"responsive", r"blast[ -]radius",
               r"real producers", r"(all|every) .{0,8}test root", r"typecheck", r"builder call site"],
    "execute": [r"verification sweep", r"reformat", r"stuck", r"design[ -]invalidat", r"token-first", r"pointer", r"render", r"proof[ -]manifest", r"ui-proof-scaffold", r"(per|each) clause", r"format[ -]scope", r"approved design", r"both axes", r"baseline", r"unchanged except", r"complete on disk",
                r"commit(ted)? .{0,24}before .{0,20}review", r"ref-based", r"empty"],
    "review": [r"reviewer", r"challenger", r"not clean", r"coverage-gap", r"item-by-item", r"per-item", r"layer-match", r"Reviewed at", r"a11y", r"DESIGN\.md", r"touch-target", r"proof[ -]manifest", r"surfaces proven", r"conditional", r"verify-only", r"baseline", r"reuse", r"only the proof affected", r"main[ -]loop", r"re-?dispatch", r"changed scope", r"bookkeeping", r"exempt", r"carve-?out",
               r"ref-based", r"worktree", r"checkout",
               r"env-?parity|environment-equivalence", r"env-?fault|environment fault", r"untracked",
               r"near-total", r"git diff HEAD", r"porcelain"],
    "finalise": [r"dry-run", r"per[- ]action", r"durable lesson", r"checklist", r"stale", r"beyond the reviewed set", r"exempt", r"dispatch[ -]only", r"not measured", r"rtk gain", r"dispatch[ -]count", r"ledger complet", r"content", r"token value", r"unmeasured", r"push", r"shared ref", r"unchanged except", r"complete on disk"],
    "solve": [r"Session status", r"self-approve", r"TIER", r"design[ -]invalidat", r"outgrew", r"per dispatch", r"unmeasured \(blocking retrieval\)", r"delta", r"unchanged except", r"complete on disk",
              r"work_doc_mode", r"committed-?stub", r"separate"],
    "quick": [r"proving test", r"combined gate", r"stuck"],
    "doctor": [r"running[ -]version", r"base path", r"\$\{CLAUDE_PLUGIN_ROOT\}"],
    "version-check": [r"update_check_url", r"never updates", r"/plugin", r"plugin\.json"],
    "codify": [r"count", r"PROVISIONAL", r"ratif", r"author", r"recommend", r"uncodified",
               r"DRIFT:", r"counting line", r"drift"],
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
        plugin / "PRINCIPLES.md",
    ]
    for path in targets:
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
    historical record, not operational text."""
    plugin = ROOT / "plugins" / "mango"
    return (sorted(plugin.glob("skills/*/SKILL.md"))
            + sorted(plugin.glob("agents/*.md"))
            + sorted(plugin.glob("templates/*.md"))
            + [plugin / "PRINCIPLES.md", plugin / "README.md", ROOT / "README.md"])


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


def validate_no_rationale_in_skills():
    """v1.7.6 — a SKILL.md is DIRECTIVES ONLY (PRINCIPLES.md, 'Skills are directive-only').

    Because prose-IS-behaviour, every token of a runtime-loaded skill is paid on every ticket run.
    Rationale, 'observed failure' war-stories, and historical justification instruct nothing, so they
    are a permanent tax — they belong in CHANGELOG.md or the non-runtime RATIONALE.md. This check
    fails the build if any RATIONALE_MARKERS pattern reappears in a skill body, so the bloat the
    v1.7.6 trim removed cannot creep back one 'observed failure:' at a time.
    """
    for path in sorted((ROOT / "plugins" / "mango").glob("skills/*/SKILL.md")):
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
