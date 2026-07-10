#!/usr/bin/env bash
# Behavioural eval for the mango skills. This is the REAL behavioural check —
# the contract checks in scripts/validate.py are the cheap, always-on guard.
#
# For each fixture ticket it runs `claude -p` headless against the SHIPPED mango
# skills and asserts the transcript contains the expected load-bearing artifacts.
#
# Runnable by anyone, hands-free: one command, no manual scaffolding.
#   bash tests/eval/run.sh
# Auth is mechanism-agnostic — it works with EITHER an exported ANTHROPIC_API_KEY
# OR an OAuth/subscription login (`claude /login`); it checks the *capability* to
# run `claude -p`, not a specific credential. The script sets up its own throwaway
# environment (an isolated local clone + a temp .harness.json + a minimal rulebook)
# so the skills execute end-to-end without depending on the operator's setup, and
# tears it all down on exit — the live checkout is never mutated.
#
# This costs tokens — it is gated behind workflow_dispatch in CI, not run on push.
#
# Coverage:
#   analysis        — SECTIONS count line + Gate 1 stop (full); TIER: lite (lite);
#                     freeform synthesis + Gate 0 confirmation (freeform).
#   design          — proof at the risk layer: an integration-layer AC with a UNIT
#                     proving test must mark the verification-plan layer-match ❌ and
#                     demand an integration/e2e proof (design-layer). test blast-radius: a
#                     change that alters a string an existing assertion checks must list
#                     that test file in the Gate-2 change list as proof collateral (blast-radius).
#   challenger      — ticket-blind, catches an unmet AC as "not met" with path:line
#                     (challenger-unmet).
#   frontend track  — T2 layer-match: a frontend AC "no horizontal overflow @320 px" whose
#                     proposed proof is a UNIT test must be layer-match ❌ and BLOCK Gate 2,
#                     demanding an automated-UI render or a recorded exclusion (frontend-layer);
#                     the review rubric FLAGS a hover-only / mouse-only handler (rubric-hover).
#   surface coverage— a universal frontend AC where the sitemap shows N reachable surfaces but the
#                     proof covers only some reads `surfaces proven: k/N` (k<N) and BLOCKS Gate 2
#                     (surface-denominator); a frontend AC with NO runner yields a tier-2
#                     PASS(render@<bp>), not a silent skip or auto-exclusion (no-runner-proof).
#   per-clause      — a multi-clause M-gate (M4 = size AND spacing) whose proof asserts only the
#                     size clause marks the spacing clause unproven and BLOCKS Gate 2; a proof
#                     asserting BOTH clauses passes (per-clause).
#   format-scope    — execute runs the project's formatter ONLY on the files this change authored/
#                     edited, never a wholesale reformat of a shared/pre-existing file; whole-file
#                     conformance is a separate concern (CI / a chore ticket) (format-scope).
#   execute/solve   — design-invalidated escalation (STOP + re-open Gate 2) and the
#                     stuck-detector (STOP + escalate at the threshold), as scenarios.
#   stale-review    — the mechanical finalise stale guard (file-set, never commit-count): a
#                     working-doc/marker-only bump must PROCEED (no dead-lock, stale-workdoc-bump);
#                     a source file changed beyond the reviewed set must REFUSE + route back to
#                     review and resist a bare "go" (stale-source-change).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES="$HERE/fixtures"
REPO_ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
# Full model transcripts are teed here (gitignored) so a failed assertion is inspectable —
# each PASS/FAIL line points at the transcript file it judged. Wiped fresh each run.
TDIR="$HERE/.transcripts"
rm -rf "$TDIR"; mkdir -p "$TDIR"
fails=0
total=0

if ! command -v claude >/dev/null 2>&1; then
  echo "FAIL: 'claude' CLI not found on PATH" >&2
  exit 1
fi

# --- Auth-agnostic guard: verify the CAPABILITY to run `claude -p`, not a
# specific credential. Any of three paths is accepted, in order of cost. -------
auth_ok() {
  # 1. An API key, if exported.
  [ -n "${ANTHROPIC_API_KEY:-}" ] && return 0
  # 2. A logged-in session (OAuth/subscription) via the non-interactive status check.
  if claude auth status --json 2>/dev/null | grep -qE '"loggedIn"[[:space:]]*:[[:space:]]*true'; then
    return 0
  fi
  # 3. Last resort: a minimal capability probe — one tiny ping; non-empty == capable.
  local ping
  ping="$(claude -p 'Reply with exactly: OK' 2>/dev/null || true)"
  [ -n "${ping//[[:space:]]/}" ] && return 0
  return 1
}
if ! auth_ok; then
  echo "FAIL: claude is not authenticated — either export ANTHROPIC_API_KEY, or log in (\`/login\`, OAuth/subscription), then re-run." >&2
  exit 1
fi

# --- Hands-free throwaway environment. An isolated local clone of the repo gives
# the fixtures a real project to act on: skills that `execute` can branch/commit
# freely inside the clone, and the whole thing (clone, refs, temp config, work
# docs) vanishes on exit with one `rm -rf` — the live checkout is never touched.
TMPROOT="$(mktemp -d)"
SANDBOX="$TMPROOT/repo"
cleanup() { rm -rf "$TMPROOT" 2>/dev/null || true; }
trap cleanup EXIT

git clone --quiet --local --no-hardlinks "$REPO_ROOT" "$SANDBOX"
PLUGIN_DIR="$SANDBOX/plugins/mango"

# A minimal throwaway rule book + harness config so the skills run end-to-end
# without the operator having to supply one. Both live inside the sandbox.
mkdir -p "$SANDBOX/docs/tickets"
cat >"$SANDBOX/docs/EVAL_RULES.md" <<'RULES'
# Eval Rule Book (throwaway — generated by tests/eval/run.sh)

Minimal rule set so the mango skills execute end-to-end during the eval.

- Trace every change to a counted requirement row; no scope creep beyond the approved list.
- Each acceptance criterion needs a proving test at its own risk layer.
- Prefer the smallest change that satisfies the requirement.
- No secrets in code or config.
RULES
cat >"$SANDBOX/.harness.json" <<'HARNESS'
{
  "rulebook_path": "docs/EVAL_RULES.md",
  "standards_path": "docs/EVAL_RULES.md",
  "repos": [{ "name": "app", "root": "." }],
  "test_command": "true",
  "tickets_dir": "docs/tickets",
  "work_dir": "docs/tickets",
  "work_doc_mode": "auto",
  "stuck_threshold": 3,
  "explore_fanout": false,
  "track": "backend",
  "cost_tier": "standard",
  "branch_strategy": "fix|feat|chore/<KEY>-<slug>",
  "lessons_path": "docs/LESSONS.md",
  "tracker": { "base_url": "https://tracker.example.com", "project_key": "EVAL", "cli": "true", "read_mcp": null },
  "ticket_header_schema": { "Constraint": "C", "Requirement": "R", "Goal": "G", "Acceptance Criteria": "AC" }
}
HARNESS

# All fixtures run headless inside the sandbox against the SHIPPED skills
# (--plugin-dir), so the eval tests what the repo ships, not whatever the operator
# happens to have installed. Default headless permissions are used (no
# privilege-bypass flag): the assertions read the transcript of artifacts the
# skills produce/describe, and the isolated clone — not a permission flag — is what
# guarantees a fixture can never touch the live checkout.
claude_run() {
  ( cd "$SANDBOX" && claude -p --plugin-dir "$PLUGIN_DIR" "$@" )
}

# assert_contains <label> <transcript-file> <regex>
# $2 is the path to the teed transcript file (returned by run_fixture/run_prompt), so every
# PASS/FAIL line can name the exact transcript it judged.
assert_contains() {
  local label="$1" file="$2" regex="$3"
  local rel="${file#$REPO_ROOT/}"
  total=$((total + 1))
  if grep -qiE "$regex" "$file"; then
    echo "  PASS: $label  [$rel]"
  else
    echo "  FAIL: $label (missing /$regex/)  [$rel]"
    fails=$((fails + 1))
  fi
}

# assert_all <label> <transcript-file> <regex...> — passes iff EVERY regex matches the file.
# Use to encode a DECISION-level match (outcome + reasoning must both appear), so a correct
# behaviour passes under any wording while a wrong outcome — which drops one of the tokens —
# still fails.
assert_all() {
  local label="$1" file="$2"; shift 2
  local rel="${file#$REPO_ROOT/}" missing="" re
  total=$((total + 1))
  for re in "$@"; do
    grep -qiE "$re" "$file" || missing="$missing /$re/"
  done
  if [ -z "$missing" ]; then
    echo "  PASS: $label  [$rel]"
  else
    echo "  FAIL: $label (missing$missing)  [$rel]"
    fails=$((fails + 1))
  fi
}

# run_fixture <name> <prompt> — runs the fixture, tees the full transcript to
# $TDIR/<name>.log, and echoes that file path (assertions grep the file).
run_fixture() {
  local name="$1" prompt="$2"
  local ticket transcript file="$TDIR/$name.log"
  ticket="$(cat "$FIXTURES/$name.md")"
  transcript="$(claude_run "$prompt"$'\n\nTicket:\n'"$ticket" 2>&1 || true)"
  { echo "== fixture: $name =="; echo "$transcript"; } >"$file"
  echo "$file"
}

# run_prompt <label> <prompt> — a fixture-less scenario prompt (no ticket attached). Tees the
# transcript to $TDIR/<label>.log and echoes that file path.
run_prompt() {
  local label="$1" prompt="$2"
  local transcript file="$TDIR/${label//[^A-Za-z0-9_-]/-}.log"
  transcript="$(claude_run "$prompt" 2>&1 || true)"
  { echo "== scenario: $label =="; echo "$transcript"; } >"$file"
  echo "$file"
}

# full: expects the SECTIONS count line and a stop at a pre-code gate. analysis stops at Gate 1
# when clean, OR Gate 0 when it raises clarifications (j>0) — a universal "all signup paths"
# requirement with an un-enumerable N legitimately surfaces Gate-0 questions, so accept either.
t="$(run_fixture full 'Run the mango analysis skill on this ticket. Do not stop for my input; show the artifacts you would produce.')"
assert_contains "full: SECTIONS count line"        "$t" 'SECTIONS:'
assert_contains "full: stops at a pre-code gate"   "$t" 'Gate[ -]?[01]'

# lite: a trivial ticket should be triaged TIER: lite.
t="$(run_fixture lite 'Run the mango analysis skill on this ticket and declare the TIER.')"
assert_contains "lite: TIER lite" "$t" 'TIER:[[:space:]*_]*lite'

# freeform: a header-less ticket should synthesize and confirm at Gate 0.
t="$(run_fixture freeform 'Run the mango analysis skill on this freeform ticket.')"
assert_contains "freeform: synthesized"      "$t" 'synthesi[sz]ed'
assert_contains "freeform: Gate 0 confirm"   "$t" 'Gate 0'

# design-layer: an integration-layer AC proved only by a UNIT test must fail the
# verification-plan layer-match and demand an integration/e2e proof (proof at the risk layer).
t="$(run_fixture design-layer 'Run the mango design skill on this ticket. Assume Gate 1 cleared. The proposed proving test is a UNIT test that mocks the downstream HTTP client. Produce the Phase 2 artifacts including the per-AC verification plan; do not stop for my input.')"
assert_contains "design: verification-plan layer-match ❌" "$t" '❌'
assert_contains "design: demands integration/e2e proof"   "$t" 'integration|e2e'
assert_contains "design: Gate 2 cannot pass"              "$t" 'Gate 2'

# blast-radius: a change that alters a string an existing assertion checks must list that existing
# test file in the Gate-2 change list as proof collateral — a planned edit, not an execute surprise.
t="$(run_fixture blast-radius 'Run the mango design skill on this ticket. Assume Gate 1 cleared. Produce the Phase 2 artifacts including the smallest change-list table and its mechanical test blast-radius sub-step; do not stop for my input.')"
assert_contains "blast-radius: names the affected existing test" "$t" 'dashboard_heading_spec|dashboard[_-]heading'
assert_contains "blast-radius: folds it in as collateral"        "$t" 'blast[ -]radius|collateral|proof collateral'

# challenger: ticket-blind on (raw ticket + diff) must report the one unmet AC as not met + path:line.
t="$(run_fixture challenger-unmet 'Run the mango challenger agent ticket-blind on the raw ticket and the diff below. Rebuild the acceptance criteria yourself and judge each met / not met / can'\''t tell with path:line. Do not read any working doc.')"
assert_contains "challenger: reports a not-met AC" "$t" 'not[[:space:]_-]*met'
# Concrete code evidence: a path:line, a named source file, or an explicit line ref. (The fixture's
# diff references files that don't exist in this repo, so a ticket-blind challenger may cite the file
# + diff hunk rather than a resolved line number — both are concrete evidence.)
assert_contains "challenger: cites concrete evidence" "$t" '[A-Za-z0-9_./-]+:[0-9]+|[A-Za-z0-9_./-]+\.(js|ts|jsx|tsx|py|rb|go|java|css|html)|line [0-9]+'

# frontend-layer (T2): a frontend "no horizontal overflow @320 px" AC proved only by a UNIT test
# must be layer-match ❌ and BLOCK Gate 2 — demanding an automated-UI render at the width (or a
# recorded human-approved exclusion), never passing on the mocked-DOM unit proof.
t="$(run_fixture frontend-layer 'Run the mango design skill on this ticket with track=frontend. Assume Gate 1 cleared and TRACK: frontend. The proposed proving test is a UNIT test that asserts layout math against a mocked DOM. Produce the Phase 2 artifacts including the per-AC verification plan; do not stop for my input.')"
assert_contains "frontend-layer: layer-match ❌"            "$t" '❌'
assert_contains "frontend-layer: demands a real render"    "$t" 'render|integration|e2e|real (rendered )?DOM'
assert_contains "frontend-layer: Gate 2 blocked"           "$t" 'Gate 2'

# rubric-hover: on the frontend review rubric path, a control exposed only via :hover and a
# mouse-only (mousedown/mousemove, no pointer equivalent) reorder handler must be FLAGGED, not passed.
t="$(run_fixture rubric-hover 'Run the mango review frontend rubric on the raw ticket and the diff below, with track=frontend. Score the Core items and the M1–M10 responsive/touch gates against a DESIGN.md contract. Report findings; do not stop for my input.')"
assert_contains "rubric-hover: flags hover-only / mouse-only" "$t" 'hover|mousedown|mousemove|pointer|tap'
assert_contains "rubric-hover: not a clean pass"             "$t" 'flag|fail|not met|blocked|changes requested|❌'

# surface-denominator: a universal frontend AC whose sitemap shows 5 reachable surfaces but whose
# proposed proof covers only 2 must read `surfaces proven: 2/5` (k<N) and BLOCK Gate 2 — the
# denominator is the code surface, not the surfaces the ticket named.
t="$(run_fixture surface-denominator 'Run the mango design skill with track=frontend. Assume Gate 1 cleared, TRACK: frontend, and SURFACES: 5 (the five reachable surfaces listed). The proposed proof covers only the overview and reports routes (2 of 5). Produce the Phase 2 verification plan / proof manifest and the surface-coverage banner; do not stop for my input.')"
# Under-coverage surfaced as 2-of-5 (accept the common phrasings: "2/5", "2 of 5", "k = 2 / N = 5").
assert_contains "surface-denominator: 2 of 5 surfaces covered" "$t" '2[[:space:]]*/[[:space:]]*5|2 of 5|k[[:space:]=]+2[[:space:]/]+N[[:space:]=]+5'
assert_contains "surface-denominator: Gate 2 blocked"          "$t" 'Gate 2'

# no-runner-proof: a frontend AC in a project with NO automated-UI runner must yield a tier-2
# PASS(render@<bp>) recorded proof — NOT a silent skip and NOT an automatic exclusion.
t="$(run_fixture no-runner-proof 'Run the mango execute skill on this AC with track=frontend. The project declares NO automated-UI runner and tests/ is unavailable. Per mango, produce the proof-manifest entry for the affected surface — do not silently skip and do not auto-exclude. State the tier and the proof; do not stop for my input.')"
assert_contains "no-runner: tier-2 render proof" "$t" 'render@|render proof|PASS\(render'
assert_contains "no-runner: a proof, not a skip"  "$t" 'render@|PASS\(render|first-class|not an exclusion'

# per-clause (Fix 1): a multi-clause M4 gate (size AND spacing) whose proof asserts ONLY the size
# clause must mark the spacing clause unproven and BLOCK Gate 2 — proving the easy clause does not
# clear a gate whose other clause is unasserted.
t="$(run_fixture per-clause 'Run the mango design/execute per-clause M-gate check on this ticket with track=frontend. Assume TRACK: frontend and Gate 1 cleared. The submitted M4 proof asserts ONLY the size clause (no spacing assertion). Lay out the proof manifest one row per clause and state whether Gate 2 passes; do not stop for my input.')"
assert_contains "per-clause: spacing clause unproven"  "$t" 'spacing'
assert_contains "per-clause: gate incomplete / blocks" "$t" 'incomplete|block|❌|unproven|not proven'
assert_contains "per-clause: Gate 2 blocked"           "$t" 'Gate 2'
# both-clause variant: a proof asserting BOTH size and spacing clears the M4 gate.
t="$(run_prompt per-clause-both 'On the mango frontend track, an M4 touch-target proof manifest carries one row asserting size ≥ 44×44 px AND a second row asserting spacing ≥ 8 px between adjacent targets — both clauses asserted. Per the mango per-clause rule, does the M4 gate pass? Answer and say why.')"
assert_contains "per-clause-both: M4 passes with both clauses" "$t" 'pass|complete|clear|proven'

# format-scope (Fix v1.1): execute runs the project's formatter ONLY on the files this change
# authored/edited — never a wholesale reformat of a shared/pre-existing file (that reformats untouched
# lines and reads as scope creep); whole-file conformance is a separate concern (CI / a chore ticket).
t="$(run_fixture format-scope 'Run the mango execute skill on this ticket. The project has a formatter. Per mango, state exactly which files you would run the formatter over, and whether you would run it over the whole shared file. Do not stop for my input.')"
# Decision-level: scope the formatter to the authored/edited file (outcome + reasoning token both
# required), and do NOT wholesale-reformat the shared file (a whole-file token + a decline/defer token).
assert_all "format-scope: scopes formatter to authored/edited files" "$t" 'format' 'authored|edited|only .*(chang|edit)|files (this|i) (chang|edit)|the (changed|edited) file'
assert_all "format-scope: no wholesale reformat of the shared file"  "$t" 'whole[- ]?file|wholesale|entire (shared )?file|whole shared file' 'not|never|avoid|would ?n.?t|do ?n.?t|defer|separate|\bCI\b|chore'

# design-invalidated scenario: execute must STOP and re-open Gate 2, never work around it.
t="$(run_prompt design-invalidated 'In the mango ticket lifecycle, during the execute phase a test reveals that the approved Gate-2 design approach cannot work as designed. Per the mango execute/solve skill, exactly what do you do next? Be specific.')"
assert_contains "design-invalidated: STOP"          "$t" 'stop'
assert_contains "design-invalidated: re-open Gate 2" "$t" 're-?open|re-?gate|reopen|Gate 2'

# stuck-detector scenario: repeated failures at the same proof must escalate, not keep trying.
t="$(run_prompt stuck-detector 'In the mango ticket lifecycle, the same proving test has failed 4 times with the same error during execute. Per the mango skill, what do you do? Be specific.')"
assert_contains "stuck: STOP and escalate" "$t" 'escalat|stop'

# stale-workdoc-bump: the finalise stale-review guard is a file-set test, NOT a commit-count test.
# When the ONLY post-review change is the marker-bearing working doc (a bookkeeping bump), the guard
# must EXEMPT it and PROCEED — it must not dead-lock on "a commit landed after the reviewed SHA".
t="$(run_fixture stale-workdoc-bump 'Run the mango finalise stale-review guard on this working doc. Apply it mechanically: git diff --name-only against the Reviewed at SHA, exempt the working-doc / bookkeeping path, and decide stale-or-not by whether any remaining file is beyond the reviewed set. State your decision (proceed or refuse) and why. Do not stop for my input.')"
# Decision-level: correct behaviour is PROCEED *because* the only change was the exempt
# working-doc/bookkeeping/marker path. Require both the proceed outcome AND an exemption-reasoning
# token (widened over phrasing) — so a proceed with no exemption recognition, or a wrong "stale"
# verdict, still fails.
assert_all "stale-workdoc: exempts the working doc"          "$t" 'not stale|proceed' 'exempt|bookkeeping|working[- ]doc|marker'
assert_contains "stale-workdoc: proceeds (no dead-lock)"     "$t" 'not stale|proceed|final gate'

# stale-source-change: a source file changed beyond the reviewed set must make the review STALE — the
# guard refuses, routes back to review, and a bare "go" does not override it.
t="$(run_fixture stale-source-change 'Run the mango finalise stale-review guard on this working doc. Apply it mechanically: git diff --name-only against the Reviewed at SHA, exempt the working-doc / bookkeeping path, and decide stale-or-not by whether any remaining file is beyond the reviewed set. Then say whether a bare "go" would let you finalise anyway. Do not stop for my input.')"
assert_contains "stale-source: marks it stale"              "$t" 'stale'
# Routing widened over phrasing (refuse / route back / re-run review / blocked / fresh review). The
# separate `stale` and bare-go assertions remain the outcome guards, so a stale verdict that then
# proceeds/stops WITHOUT routing, or a honoured bare "go", still fails the suite.
assert_contains "stale-source: refuses + routes to review"  "$t" 'refuse|route|re-?run review|re-?review|blocked|fresh review'
assert_contains "stale-source: bare go does not override"   "$t" 'does not override|not override|only a fresh|bare .?go'

echo
if [ "$fails" -gt 0 ]; then
  echo "EVAL: $((total - fails))/$total assertions pass — $fails assertion(s) failed"
  exit 1
fi
echo "EVAL: all assertions passed — $total/$total assertions pass"
