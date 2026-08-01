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
               r"RECALL:", r"advisory", r"retired", r"by symbol", r"by area"],
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
               r"real producers", r"(all|every) .{0,8}test root", r"typecheck", r"builder call site"],
    "execute": [r"verification sweep", r"reformat", r"stuck", r"design[ -]invalidat", r"token-first", r"pointer", r"render", r"proof[ -]manifest", r"ui-proof-scaffold", r"(per|each) clause", r"format[ -]scope", r"approved design", r"both axes", r"baseline", r"unchanged except", r"complete on disk",
                r"commit(ted)? .{0,24}before .{0,20}review", r"ref-based", r"empty"],
    "review": [r"reviewer", r"challenger", r"not clean", r"coverage-gap", r"item-by-item", r"per-item", r"layer-match", r"Reviewed at", r"a11y", r"DESIGN\.md", r"touch-target", r"proof[ -]manifest", r"surfaces proven", r"conditional", r"verify-only", r"baseline", r"reuse", r"only the proof affected", r"main[ -]loop", r"re-?dispatch", r"changed scope", r"bookkeeping", r"exempt", r"carve-?out",
               r"ref-based", r"worktree", r"checkout",
               r"env-?parity|environment-equivalence", r"env-?fault|environment fault", r"untracked",
               r"near-total", r"git diff HEAD", r"porcelain"],
    "finalise": [r"dry-run", r"per[- ]action", r"durable lesson", r"checklist", r"stale", r"beyond the reviewed set", r"exempt", r"dispatch[ -]only", r"not measured", r"rtk gain", r"dispatch[ -]count", r"ledger complet", r"content", r"token value", r"unmeasured", r"push", r"shared ref", r"unchanged except", r"complete on disk",
                 r"CLAIMS:", r"RECURRENCE:", r"FALSIFY:", r"PROMOTION:", r"atomic claim",
                 r"supersed", r"retired", r"falsif", r"skill_gap_path", r"agent_brief_path",
                 r"mango files written: 0"],
    "solve": [r"Session status", r"self-approve", r"TIER", r"design[ -]invalidat", r"outgrew", r"per dispatch", r"unmeasured \(blocking retrieval\)", r"delta", r"unchanged except", r"complete on disk",
              r"work_doc_mode", r"committed-?stub", r"separate",
              r"learning loop", r"falsification", r"skill_gap_path", r"no lesson edits a mango skill"],
    "quick": [r"proving test", r"combined gate", r"stuck"],
    "doctor": [r"running[ -]version", r"base path", r"\$\{CLAUDE_PLUGIN_ROOT\}",
               r"mango:standing-context", r"CLAUDE\.md",
               r"skill_gap_path", r"inside the project repo"],
    "init": [r"\.harness\.json", r"UNVERIFIED", r"rulebook", r"never overwrite",
             r"CLAUDE\.md", r"mango:standing-context", r"pointer", r"secret"],
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
        plugin / "PRINCIPLES.md",
    ]
    for path in targets:
        rel = path.relative_to(ROOT)
        if not check(path.exists(), f"premise-preflight: {rel} is missing"):
            continue
        try:
            body = path.read_text(encoding="utf-8")
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
    principles = plugin / "PRINCIPLES.md"
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

    # --- The contract: PRINCIPLES.md carries the six types, both tiebreaks, and the five invariants.
    pb = body_of(principles)
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
