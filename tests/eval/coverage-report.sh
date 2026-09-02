#!/usr/bin/env bash
# coverage-report.sh — print the eval coverage state from the LEDGER, not from a hand-kept file.
#
# The ledger (tests/eval/.cache/coverage.<runner-fp>.tsv) is the authority: v1.15.0 writes one row per
# job per run carrying the job's skills-hash and all four ruler components. This script only reads it.
# It dispatches nothing, costs nothing, and never writes.
#
# It deliberately does NOT decide whether the suite is green — that is `run.sh --verify-suite`, which
# holds the ledger against the suite's own registered job list and re-checks every hash. This is a
# dashboard; --verify-suite is the gate. Do not cite this output as proof of anything.
#
# Usage:
#   bash tests/eval/coverage-report.sh              # current runner fingerprint
#   bash tests/eval/coverage-report.sh --remaining  # just the not-yet-green job names, one per line
#   bash tests/eval/coverage-report.sh --md         # a markdown table, for pasting into EVAL-STATUS.md
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
CACHE_DIR="$HERE/.cache"
RUN_SH="$HERE/run.sh"
PLUGIN_SRC="$REPO_ROOT/plugins/mango"

MODE=table
case "${1:-}" in
  --remaining) MODE=remaining ;;
  --md)        MODE=md ;;
  "")          ;;
  *) echo "usage: coverage-report.sh [--remaining|--md]" >&2; exit 2 ;;
esac

# Same derivations run.sh uses, so this report names the same fingerprint the next run will.
hash_files() { [ "$#" -gt 0 ] || return 1; cat "$@" 2>/dev/null | sha256sum 2>/dev/null | awk '{print $1}'; }
RUNNER_FP="$(hash_files "$RUN_SH")"
PLUGIN_TREE_FP="$( ( cd "$PLUGIN_SRC" 2>/dev/null &&
    find .claude-plugin scripts -type f \( -name '*.py' -o -name '*.json' \) -print0 2>/dev/null |
    LC_ALL=C sort -z | xargs -0 -r sha256sum 2>/dev/null
  ) | sha256sum 2>/dev/null | awk '{print $1}' )"
LEDGER="$CACHE_DIR/coverage.$RUNNER_FP.tsv"
RUNS="$CACHE_DIR/runs.$RUNNER_FP.tsv"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# Every fixture on disk. The scenarios are not files, so their count comes from the ledger's own
# kind column plus the known total; a scenario that has never run cannot be named from disk, which is
# exactly why --verify-suite (which reads the registered job list) is the gate and this is not.
ls "$HERE"/fixtures/*.md 2>/dev/null | sed -e 's|.*/||' -e 's|\.md$||' | LC_ALL=C sort >"$TMP/fixtures"
FIXTURE_TOTAL="$(wc -l <"$TMP/fixtures")"

# Last row wins, exactly as verify_suite reads it.
if [ -s "$LEDGER" ]; then
  awk -F'\t' 'NF>=11 {r[$1]=$0} END {for (k in r) print r[k]}' "$LEDGER" |
    LC_ALL=C sort -t$'\t' -k1,1 >"$TMP/rows"
else
  : >"$TMP/rows"
fi
awk -F'\t' '$9=="green" {print $1}' "$TMP/rows" | LC_ALL=C sort -u >"$TMP/green"
awk -F'\t' '$9!="green" {print $1}' "$TMP/rows" | LC_ALL=C sort -u >"$TMP/notgreen"
comm -23 "$TMP/fixtures" "$TMP/green" >"$TMP/remaining"

GREEN="$(wc -l <"$TMP/green")"
RED="$(wc -l <"$TMP/notgreen")"
REMAIN="$(wc -l <"$TMP/remaining")"
SCEN_GREEN="$(awk -F'\t' '$9=="green" && $2=="scenario" {print $1}' "$TMP/rows" | LC_ALL=C sort -u | wc -l)"

if [ "$MODE" = remaining ]; then
  cat "$TMP/remaining"
  exit 0
fi

# A stale green: its skills-hash no longer matches the files as they are now. Recomputed here with the
# same inputs run.sh uses, so this column means what --verify-suite means by "stale".
FIXTURE_SKILLS_SRC="$(sed -n '/FIXTURE_SKILLS=(/,/^)/p' "$RUN_SH")"
skills_hash_now() {
  local name="$1" mapped s
  mapped="$(printf '%s\n' "$FIXTURE_SKILLS_SRC" | grep -oE "\[$name\]=\"[a-z ]+\"" | sed -e 's|.*="||' -e 's|"$||' || true)"
  {
    if [ -n "$mapped" ]; then
      for s in $mapped; do ls "$PLUGIN_SRC"/skills/"$s"/*.md 2>/dev/null; done
    else
      ls "$PLUGIN_SRC"/skills/*/*.md 2>/dev/null
    fi
    echo "$PLUGIN_SRC/PRINCIPLES.md"
    ls "$PLUGIN_SRC"/principles/*.md 2>/dev/null
    ls "$PLUGIN_SRC"/agents/*.md 2>/dev/null
    ls "$PLUGIN_SRC"/templates/*.md 2>/dev/null
    echo "$HERE/fixtures/$name.md"
  } >"$TMP/f.list"
  hash_files $(cat "$TMP/f.list") 2>/dev/null || true
}
STALE=0; : >"$TMP/stale"
while IFS=$'\t' read -r job kind shash rest; do
  [ "$kind" = fixture ] || continue
  cur="$(skills_hash_now "$job")"
  if [ -n "$cur" ] && [ "$cur" != "$shash" ]; then
    STALE=$((STALE + 1)); printf '%s\n' "$job" >>"$TMP/stale"
  fi
done < <(awk -F'\t' '$9=="green" {print $1"\t"$2"\t"$3}' "$TMP/rows")

# Ruler uniformity across surviving rows.
RULERS="$(awk -F'\t' '{print $4"\t"$5"\t"$6}' "$TMP/rows" | LC_ALL=C sort -u | wc -l)"

if [ "$MODE" = md ]; then
  echo "| Metric | Value |"
  echo "|---|---|"
  echo "| Runner fingerprint | \`${RUNNER_FP:0:12}\` |"
  echo "| Plugin-tree fingerprint | \`${PLUGIN_TREE_FP:0:12}\` |"
  echo "| Fixtures green | ${GREEN} of ${FIXTURE_TOTAL} on disk (+${SCEN_GREEN} scenario rows) |"
  echo "| Rows not green | ${RED} |"
  echo "| Stale greens | ${STALE} |"
  echo "| Distinct rulers among rows | ${RULERS} (must be 1) |"
  echo "| Fixtures with no green row | ${REMAIN} |"
  exit 0
fi

echo "== eval coverage, read from the ledger (no dispatch, no cost) =="
echo "  runner fingerprint : $RUNNER_FP"
echo "  plugin-tree fp     : $PLUGIN_TREE_FP"
echo "  ledger             : ${LEDGER#$REPO_ROOT/}"
if [ ! -s "$LEDGER" ]; then
  echo "  (no ledger for this fingerprint — no job has ever been recorded under this runner)"
  echo
  echo "  fixtures on disk with no green row : $FIXTURE_TOTAL of $FIXTURE_TOTAL"
  echo "  next: bash tests/eval/run.sh --workers 8 --only '<selector>'"
  exit 0
fi
echo "  runs recorded      : $( [ -s "$RUNS" ] && wc -l <"$RUNS" || echo 0 )"
echo
printf '  %-34s %s\n' "green rows"                 "$GREEN  (fixtures $((GREEN - SCEN_GREEN)) of $FIXTURE_TOTAL on disk, scenarios $SCEN_GREEN)"
printf '  %-34s %s\n' "rows NOT green"             "$RED"
printf '  %-34s %s\n' "STALE greens (hash moved)"  "$STALE"
printf '  %-34s %s\n' "distinct rulers among rows" "$RULERS  $( [ "$RULERS" -eq 1 ] && echo '(uniform)' || echo '(NOT uniform — --verify-suite will refuse)' )"
printf '  %-34s %s\n' "fixtures with no green row" "$REMAIN"

if [ "$RED" -gt 0 ]; then
  echo; echo "  rows not green:"
  awk -F'\t' '$9!="green" {printf "    %-38s %s  (%s/%s passed)\n", $1, $9, $8, $7}' "$TMP/rows"
fi
if [ "$STALE" -gt 0 ]; then
  echo; echo "  STALE greens — proven, then their skills changed:"
  sed 's|^|    |' "$TMP/stale"
fi
if [ "$RULERS" -gt 1 ]; then
  echo; echo "  rulers found (plugin-fp / model / CLI):"
  awk -F'\t' '{print "    "$4"  "$5"  "$6}' "$TMP/rows" | LC_ALL=C sort -u
fi
if [ "$REMAIN" -gt 0 ]; then
  echo; echo "  fixtures with no green row ($REMAIN) — see --remaining for a bare list:"
  paste -sd' ' "$TMP/remaining" | fold -s -w 96 | sed 's|^|    |'
fi

echo
echo "  This is a dashboard, not the gate. Prove the suite with:"
echo "    bash tests/eval/run.sh --verify-suite"
