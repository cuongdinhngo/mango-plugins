#!/usr/bin/env bash
# Behavioural eval for the mango skills. This is the REAL behavioural check —
# the contract checks in scripts/validate.py are the cheap, always-on guard.
#
# For each fixture ticket it runs `claude -p` headless against the mango skill
# and asserts the transcript contains the expected load-bearing artifacts.
# Requires: the `claude` CLI on PATH and ANTHROPIC_API_KEY in the environment.
# This costs tokens — it is gated behind workflow_dispatch in CI, not run on push.
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

echo
if [ "$fails" -gt 0 ]; then
  echo "EVAL: $fails assertion(s) failed"
  exit 1
fi
echo "EVAL: all assertions passed"
