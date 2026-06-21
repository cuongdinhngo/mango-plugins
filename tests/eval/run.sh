#!/usr/bin/env bash
# Behavioural eval for the mango skills. This is the REAL behavioural check —
# the contract checks in scripts/validate.py are the cheap, always-on guard.
#
# For each fixture ticket it runs `claude -p` headless against the mango skill
# and asserts the transcript contains the expected load-bearing artifacts.
# Requires: the `claude` CLI on PATH and ANTHROPIC_API_KEY in the environment.
# This costs tokens — it is gated behind workflow_dispatch in CI, not run on push.
#
# Coverage:
#   analysis        — SECTIONS count line + Gate 1 stop (full); TIER: lite (lite);
#                     freeform synthesis + Gate 0 confirmation (freeform).
#   design          — proof at the risk layer: an integration-layer AC with a UNIT
#                     proving test must mark the verification-plan layer-match ❌ and
#                     demand an integration/e2e proof (design-layer).
#   challenger      — ticket-blind, catches an unmet AC as "not met" with path:line
#                     (challenger-unmet).
#   execute/solve   — design-invalidated escalation (STOP + re-open Gate 2) and the
#                     stuck-detector (STOP + escalate at the threshold), as scenarios.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES="$HERE/fixtures"
fails=0

if ! command -v claude >/dev/null 2>&1; then
  echo "FAIL: 'claude' CLI not found on PATH" >&2
  exit 1
fi
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY must be set}"

# assert_contains <label> <transcript> <regex>
assert_contains() {
  local label="$1" transcript="$2" regex="$3"
  if grep -qiE "$regex" <<<"$transcript"; then
    echo "  PASS: $label"
  else
    echo "  FAIL: $label (missing /$regex/)"
    fails=$((fails + 1))
  fi
}

run_fixture() {
  local name="$1" prompt="$2"
  echo "== fixture: $name =="
  local ticket transcript
  ticket="$(cat "$FIXTURES/$name.md")"
  transcript="$(claude -p "$prompt"$'\n\nTicket:\n'"$ticket" 2>&1 || true)"
  echo "$transcript"
}

# run_prompt <label> <prompt> — a fixture-less scenario prompt (no ticket attached).
run_prompt() {
  local label="$1" prompt="$2"
  echo "== scenario: $label =="
  local transcript
  transcript="$(claude -p "$prompt" 2>&1 || true)"
  echo "$transcript"
}

# full: expects the SECTIONS count line and a Gate 1 stop.
t="$(run_fixture full 'Run the mango analysis skill on this ticket. Do not stop for my input; show the artifacts you would produce.')"
assert_contains "full: SECTIONS count line" "$t" 'SECTIONS:'
assert_contains "full: Gate 1"             "$t" 'Gate 1'

# lite: a trivial ticket should be triaged TIER: lite.
t="$(run_fixture lite 'Run the mango analysis skill on this ticket and declare the TIER.')"
assert_contains "lite: TIER lite" "$t" 'TIER:[[:space:]]*lite'

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

# challenger: ticket-blind on (raw ticket + diff) must report the one unmet AC as not met + path:line.
t="$(run_fixture challenger-unmet 'Run the mango challenger agent ticket-blind on the raw ticket and the diff below. Rebuild the acceptance criteria yourself and judge each met / not met / can'\''t tell with path:line. Do not read any working doc.')"
assert_contains "challenger: reports a not-met AC" "$t" 'not[[:space:]_-]*met'
assert_contains "challenger: cites path:line"      "$t" '[A-Za-z0-9_./-]+:[0-9]+'

# design-invalidated scenario: execute must STOP and re-open Gate 2, never work around it.
t="$(run_prompt design-invalidated 'In the mango ticket lifecycle, during the execute phase a test reveals that the approved Gate-2 design approach cannot work as designed. Per the mango execute/solve skill, exactly what do you do next? Be specific.')"
assert_contains "design-invalidated: STOP"          "$t" 'stop'
assert_contains "design-invalidated: re-open Gate 2" "$t" 're-?open|re-?gate|reopen|Gate 2'

# stuck-detector scenario: repeated failures at the same proof must escalate, not keep trying.
t="$(run_prompt stuck-detector 'In the mango ticket lifecycle, the same proving test has failed 4 times with the same error during execute. Per the mango skill, what do you do? Be specific.')"
assert_contains "stuck: STOP and escalate" "$t" 'escalat|stop'

echo
if [ "$fails" -gt 0 ]; then
  echo "EVAL: $fails assertion(s) failed"
  exit 1
fi
echo "EVAL: all assertions passed"
