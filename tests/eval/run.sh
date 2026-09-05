#!/usr/bin/env bash
# Per-skill behavioural smoke guard for the mango skills.
#
# WHAT THIS IS, AND WHAT IT IS NOT. mango has NO behavioural regression suite. It has this: six
# fixtures, run when a skill is edited, answering one question — "does the skill I just edited still
# behave?" It does NOT answer "is mango green?", and nothing here should be read as though it did.
#
# The 126-job suite this replaces was retired in v1.16.0. Over its whole life it produced 30 reds,
# of which ZERO were mango behaving wrongly (12 assertion wording, 10 harness defects, 7 environment,
# 1 fixture), and it never once caught a cross-skill regression. The reasoning, the 24 harness
# defects it did find, and the numbers behind the decision are in tests/eval/history/.
#
# TWO STATED LIMITS, so they are not discovered later:
#   * NO CROSS-SKILL REGRESSION DETECTION. Editing `design` and breaking `finalise` is not caught
#     here. Accepted because it never once happened in this repo's recorded history.
#   * `RETIRE:` IS UNCOVERED. It has no assertion here — and it had none in the 511 the old suite
#     carried either. `promote` emits it at the ratify step; the promote fixture kept below is the
#     zero case, which by construction never reaches a ratify.
#
# The always-on, dispatch-free guards are elsewhere and are unaffected: scripts/validate.py (shipped
# contract text), plugins/mango/scripts/check_lines.py (counted lines), tests/envelope/.
#
# HOW TO RUN IT. Hands-free: one command, no manual scaffolding.
#   bash tests/eval/run.sh                       # all six  (~6 dispatches)
#   bash tests/eval/run.sh --only '^(a|b)$'      # the fixtures mapped to the skill you edited
#   bash tests/eval/run.sh --workers 1           # sequential — debugging one transcript
#   bash tests/eval/run.sh --no-cache            # full fresh run: nothing is reused
#
# ALWAYS ANCHOR AN --only SELECTOR. `--only refine` once matched a scenario inside a fixture name and
# reported success on a job nobody meant to run. Write `^(name-a|name-b)$`.
#
# Auth is mechanism-agnostic — EITHER an exported ANTHROPIC_API_KEY OR an OAuth/subscription login
# (`claude /login`); it checks the *capability* to run `claude -p`, not a specific credential. The
# script builds its own throwaway environment (an isolated local clone + a temp .harness.json + a
# minimal rule book) so the skills execute end-to-end without depending on the operator's setup, and
# tears it down on exit — the live checkout is never mutated.
#
# This costs tokens. Six fixtures is roughly $3; a typical one- or two-fixture selection is under
# $1.50 and under a minute.
#
# --- How the runner works: PARALLEL DISPATCH over a TWO-PASS body ---------------
# The run is 100% `claude -p` latency (harness overhead is ~0.03%), so wall-time comes from
# dispatching concurrently. `suite()` below therefore runs TWICE over the SAME code, so a prompt can
# never drift from the assertions that judge it:
#   pass 1  PHASE=collect — every run_fixture REGISTERS a dispatch job (name, prompt, and the
#                           .harness.json test_command in force at that point); every assert_* is
#                           a no-op.
#   dispatch              — the registered jobs run CONCURRENTLY across --workers N workers, each in
#                           its OWN throwaway clone.
#   pass 2  PHASE=assert  — every run_fixture resolves the transcript the dispatch produced; every
#                           assert_* judges it.
# Assertion OUTPUT stays in script order (the assert pass is sequential), so a parallel run reads
# exactly like a sequential one.
#
# PER-WORKER ISOLATION IS MANDATORY, for reasons that are structural rather than stylistic: a
# fixture that lets `execute` branch and commit would race inside one shared clone, and a fixture
# that repoints config.test_command would flip .harness.json under another in-flight dispatch. Each
# worker gets its own clone AND writes its own per-JOB harness; the worker tree is disposed after its
# last job and the disposal is a counted assertion, alongside the live-checkout guard.
#
# --- The six, and what each one is for ------------------------------------------
#   refine-want-unattended-stops  refine, autorun  Gate 0. The worked example of a claim bound to a
#                     COUNTED LINE: an unresolved want-decision counts toward `j`, autorun stops, and
#                     it is never a silent ASSUMED — asserted against the REFINE: line's own arithmetic.
#   multi-clause-want             analysis         Gate 1. A two-clause want-decision becomes two
#                     matrix rows and two proof rows; the injected single-row certification is flagged.
#   provenance-authored-blocks    design           Gate 2. An AC about a grouping heuristic proven on
#                     authored fixtures alone blocks the gate; anchors on the EXCLUSIONS: line. This
#                     gate exists because of four real-data defects the old fixture suite never saw.
#   execute-commit-before-review  execute, review  Gate 3-4. Commit ordering across two skills, plus
#                     the empty-diff fallback.
#   lesson-claim-split            finalise         Gate 4. Anchors on the CLAIMS: line, whose per-type
#                     counts carry internal arithmetic check_lines.py can verify with no grammar
#                     judgement. finalise emits 6 of the 20 counted grammars — more than any skill.
#   greenfield-promote-zeros      promote          NEGATIVE CONTROL. An empty corpus emits zeros,
#                     proposes nothing, writes nothing: `absent rules written[ *_:=]*[1-9]`.
#
# ASSERTION CONVENTION (tests/eval/README.md): match the DECISION, not one phrasing; tolerate
# markdown emphasis; widen over wording, NEVER over outcome. Every widened token is proven both ways
# by the dispatch-free assertion-convention self-test below.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES="$HERE/fixtures"
REPO_ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
# The branch this run STARTED on, captured before anything can move it. The isolation guard asserts
# the checkout is left on this, not on the literal `main`: the property being checked is "the guard
# left the checkout where it found it", and skill work happens on a topic branch. Hardcoding `main`
# made the guard fail 100% of the time off main — a false red, not a check — while telling the
# operator a fixture had leaked. Not a loosening: on main the two are identical, and the
# stray-`*PROJ-*`-branch and work-doc rules are untouched.
EVAL_START_BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo UNKNOWN)"
# Full model transcripts are teed here (gitignored) so a failed assertion is inspectable — each
# PASS/FAIL line points at the transcript file it judged. Wiped fresh each run.
TDIR="$HERE/.transcripts"
rm -rf "$TDIR"; mkdir -p "$TDIR"
# The ARCHIVE is the one directory this script never wipes. `.transcripts/` above is cleared on every
# run, which means an assertion can only ever be re-judged against the last run. Every judged
# transcript is copied here, red ones included: a red transcript is the only record of the phrasing an
# assertion failed to match, and the greens are what show a widened token has not gone toothless
# elsewhere. Nothing is ever read back from here as a verdict — it is evidence for offline token work,
# never an input to judging — so it cannot become a false green.
ARCHIVE_DIR="$HERE/.archive"
mkdir -p "$ARCHIVE_DIR" 2>/dev/null || true
fails=0
total=0
skipped=0        # assertions not judged because --only filtered their dispatch out


# --- CLI -----------------------------------------------------------------------
#   --workers N  concurrent dispatch workers (default 4 — a safe value that is kind
#                to API rate limits). N=1 is a genuinely sequential run, kept for
#                debugging a single transcript.
#   --only RE    dispatch only fixtures whose name matches the regex RE, and judge
#                only those. This is the per-skill trigger: select the fixtures
#                mapped to the skill you edited. ANCHOR IT — `^(a|b)$` — because an
#                unanchored selector once matched more than it named.
#   --no-cache   full fresh run: every fixture dispatches, nothing is reused.
WORKERS="${MANGO_EVAL_WORKERS:-4}"
ONLY=""
_args=("$@")
_i=0
while [ "$_i" -lt "${#_args[@]}" ]; do
  case "${_args[$_i]}" in
    --workers) _i=$((_i + 1)); WORKERS="${_args[$_i]:-}" ;;
    --workers=*) WORKERS="${_args[$_i]#*=}" ;;
    --only) _i=$((_i + 1)); ONLY="${_args[$_i]:-}" ;;
    --only=*) ONLY="${_args[$_i]#*=}" ;;
    --no-cache) : ;;   # handled in the cache block below
    *) echo "FAIL: unknown argument '${_args[$_i]}' (expected --workers N | --only REGEX | --no-cache)" >&2; exit 1 ;;
  esac
  _i=$((_i + 1))
done
case "$WORKERS" in ''|*[!0-9]*) echo "FAIL: --workers must be a positive integer" >&2; exit 1 ;; esac
[ "$WORKERS" -ge 1 ] || { echo "FAIL: --workers must be >= 1" >&2; exit 1; }
# --- Measurement instrumentation (opt-in: MANGO_EVAL_PROFILE=<path-prefix>) ---
# Records per-dispatch wall-time and per-assertion attribution into
# $MANGO_EVAL_PROFILE.timing / .asserts so a run can be profiled. It writes
# nothing else and changes NO assertion, fixture or dispatch behaviour; with the
# variable unset every hook is a no-op.
PROFILE="${MANGO_EVAL_PROFILE:-}"
prof_now()    { date +%s%N; }
prof_time()   { # <name> <start-ns> <hit|fresh|n-a> <fixture|scenario>
  [ -n "$PROFILE" ] || return 0
  printf '%s\t%s\t%s\t%s\n' "$1" "$(( ($(prof_now) - $2) / 1000000 ))" "$3" "$4" >>"$PROFILE.timing"
}
prof_assert() { [ -n "$PROFILE" ] || return 0; printf '%s\t%s\n' "$1" "$2" >>"$PROFILE.asserts"; }

# --- Transcript cache (Fix E, v1.7.3) — keyed on (fixture-id + skills-hash) ----
# The common case for a small version: only 1–2 skills change, so most fixtures'
# skills are UNCHANGED and their last GREEN transcript can be REUSED without a
# `claude -p` dispatch (a cache-hit). Any change — or ANY uncertainty (missing
# cache, unreadable hash, changed file, changed runner) — runs the fixture FRESH:
# the cache is **fail-safe to run** and only ever avoids a re-run it can PROVE is
# unnecessary (skills unchanged ⇒ behaviour unchanged — the same prose-is-behaviour
# invariant mango already relies on). It NEVER drops a fixture from coverage.
#   --no-cache  forces a full fresh run (every fixture dispatches) — the
#               milestone/release bar; the cache only accelerates the dev loop.
# The cache lives OUTSIDE the committed tree and is git-ignored (like .transcripts).
PLUGIN_SRC="$REPO_ROOT/plugins/mango"
CACHE_ENABLED=1
for _arg in "$@"; do [ "$_arg" = "--no-cache" ] && CACHE_ENABLED=0; done
CACHE_DIR="${MANGO_EVAL_CACHE_DIR:-$HERE/.cache}"
# Cache tallies live in FILES, not shell variables (v1.7.5 Fix 4). Every fixture is invoked as
# `t="$(run_fixture …)"` — a command substitution, i.e. a SUBSHELL — so a `VAR=$((VAR+1))` inside
# run_fixture is discarded when that subshell exits. That lost the hit/fresh counters (printing
# "0 fixtures ran fresh" when they all did) AND the FRESH_FIXTURES list the end-of-run cache WRITE
# iterates, so the cache was never populated and could never hit. A side-channel file survives the
# subshell; the parent reads it back before the tally.
CACHE_TALLY_DIR=""   # set once TMPROOT exists (below); the ledger files live inside it
tally_add() {  # <ledger-name> <line> — append one record; survives command-substitution subshells
  [ -n "$CACHE_TALLY_DIR" ] || return 0
  printf '%s\n' "$2" >>"$CACHE_TALLY_DIR/$1"
}
tally_count() { [ -s "${CACHE_TALLY_DIR:-/nonexistent}/$1" ] && wc -l <"$CACHE_TALLY_DIR/$1" | tr -d ' ' || echo 0; }
tally_list()  { [ -s "${CACHE_TALLY_DIR:-/nonexistent}/$1" ] && tr '\n' ' ' <"$CACHE_TALLY_DIR/$1" || true; }

# --- Per-job result tally ------------------------------------------------------
# One record per judged assertion, keyed by job. Its only consumer is the cache mint at the
# bottom: a fixture may only mint a cached transcript if it passed ALL of its own assertions.
# It is not a ledger and it is not read across runs — the retired suite's coverage ledger,
# --verify-suite and the two-tier job fingerprint went with the whole-suite goal.
COV_DIR=""   # set once TMPROOT exists (below)
cov_job()    { local b="${1##*/}"; printf '%s' "${b%.log}"; }
cov_assert() { [ -n "$COV_DIR" ] || return 0; printf '%s\t%s\n' "$(cov_job "$1")" "$2" >>"$COV_DIR/judged"; }
cov_count()  { awk -F'\t' -v j="$2" -v v="$3" '$1==j && (v=="" || $2==v) {n++} END {print n+0}' "$1" 2>/dev/null || echo 0; }
# The fixture→skill map keys the per-fixture skills-hash: a fixture whose mapped
# SKILL.md file(s) are unchanged can cache-hit. An UNMAPPED fixture hashes over ALL
# skills (fail-safe: any skill change invalidates it). PRINCIPLES.md, every agent
# brief, and every template are ALWAYS in the hash, so a change to any of them
# invalidates every cache — only the per-skill selectivity is the acceleration.
# RATIONALE.md is deliberately NOT in the hash: no skill loads it, so it cannot
# change behaviour and must never invalidate a cache. Do not add it.
declare -A FIXTURE_SKILLS=(
  [refine-want-unattended-stops]="refine autorun"
  [multi-clause-want]="analysis"
  [provenance-authored-blocks]="design"
  [execute-commit-before-review]="execute review"
  [lesson-claim-split]="finalise"
  [greenfield-promote-zeros]="promote"
)
# make `cat` block on stdin): no args → empty hash → treated as a MISS (run fresh), never a hang.
hash_files() { [ "$#" -gt 0 ] || return 1; cat "$@" 2>/dev/null | sha256sum 2>/dev/null | awk '{print $1}'; }
skills_files() {  # <fixture-name> — the files whose contents key this fixture's cache
  local name="$1"                         # keep on its own line: a single `local a=.. b=${a}`
  local mapped="${FIXTURE_SKILLS[$name]:-}"  # evaluates b's RHS before a binds under `set -u`
  local s
  if [ -n "$mapped" ]; then
    # v1.10.0: hash the whole skill DIRECTORY, not just SKILL.md — a skill's on-demand companion
    # (skills/<s>/frontend.md) is read at its point of use, so editing it changes behaviour.
    for s in $mapped; do ls "$PLUGIN_SRC"/skills/"$s"/*.md 2>/dev/null; done
  else
    ls "$PLUGIN_SRC"/skills/*/*.md 2>/dev/null
  fi
  echo "$PLUGIN_SRC/PRINCIPLES.md"
  # v1.10.0: every on-demand PRINCIPLES companion keys every fixture, exactly as PRINCIPLES.md does —
  # relocating a section may never move it outside the cache key.
  ls "$PLUGIN_SRC"/principles/*.md 2>/dev/null
  ls "$PLUGIN_SRC"/agents/*.md 2>/dev/null
  ls "$PLUGIN_SRC"/templates/*.md 2>/dev/null
  # A job with no fixture file on disk must not make `cat` fail inside hash_files: under
  # `pipefail`+`errexit` that failure propagates out of the `_h="$(skills_hash "$_name")"` assignment
  # in the cache mint and kills the run at its last step. Emit the path only when it exists, and never
  # let the guard become this function's exit status.
  [ ! -f "$FIXTURES/$name.md" ] || echo "$FIXTURES/$name.md"
  return 0
}
# skills-hash — empty on any failure → treated as a MISS (run fresh), never a silent hit.
skills_hash() { hash_files $(skills_files "$1"); }

# cache_hit_path <candidate-green-file> — echoes it iff cache reads are ENABLED and
# the file exists+nonempty; otherwise a miss. The single gate honouring --no-cache.
cache_hit_path() {
  [ "$CACHE_ENABLED" -eq 1 ] || return 1
  [ -s "$1" ] || return 1
  echo "$1"
}
# cache_get <fixture-name> — echoes the cached GREEN transcript on a cache-hit, empty on miss.
cache_get() {
  local name="$1" h
  h="$(skills_hash "$name")"; [ -n "$h" ] || return 1   # unhashable → fail-safe miss
  cache_hit_path "$CACHE_DIR/$name.$h.green"
}

# Runner fingerprint: if run.sh itself changed since the cache was written (harness
# blocks, assertions, dispatch wiring), invalidate the WHOLE cache — fail-safe to
# run everything fresh. So a version that edits the runner (like this one) re-runs
# every fixture; the per-skill selectivity only bites on a skills-only version.
mkdir -p "$CACHE_DIR"
# RUNNER_FP hashes the WHOLE of this file. It keys the transcript-cache wipe (further down, once
# CACHE_ENABLED is known) and is stamped on every archived run, so a transcript can be traced to the
# exact file that judged it.
RUNNER_FP="$(hash_files "${BASH_SOURCE[0]}")"

# --- Measurement identity (v1.15.0) -------------------------------------------
# A green is a MEASUREMENT, and two measurements only add up if they were taken with the same
# ruler. The per-fixture skills-hash already keys everything a fixture READS from the skill
# corpus — but it deliberately keys nothing else, so three things could change between two
# partial runs without any hash noticing:
#   * plugins/mango/scripts/*.py and .claude-plugin/plugin.json — executed / loaded at runtime,
#     outside skills_files() by construction;
#   * the MODEL behind `claude -p`;
#   * the `claude` CLI itself.
# All three are stamped into each archived run's IDENTITY.tsv, so a transcript can always be traced
# to the ruler that produced it. Docs that are never read at runtime (RATIONALE.md, CHANGELOG.md,
# README.md, config/harness.example.json) are excluded on the same "read at runtime" criterion
# skills_files() uses — RATIONALE.md's exclusion from the cache key would otherwise be undone here.
plugin_tree_fp() {
  ( cd "$PLUGIN_SRC" 2>/dev/null &&
      find .claude-plugin scripts -type f \( -name '*.py' -o -name '*.json' \) -print0 2>/dev/null |
      LC_ALL=C sort -z | xargs -0 -r sha256sum 2>/dev/null
  ) | sha256sum 2>/dev/null | awk '{print $1}'
}
PLUGIN_TREE_FP="$(plugin_tree_fp)"; [ -n "$PLUGIN_TREE_FP" ] || PLUGIN_TREE_FP="unhashable"
# The model is a SETTING, not something the runner can observe per dispatch without paying for a
# JSON round-trip. When it is explicit we record it; when it is the CLI default we record that
# fact, and the CLI version — which pins that default — is recorded alongside and asserted uniform.
MODEL_SETTING="${ANTHROPIC_MODEL:-}"; [ -n "$MODEL_SETTING" ] || MODEL_SETTING="cli-default"
CLI_VERSION="$(claude --version 2>/dev/null | head -1 | tr -d '\t\n' || true)"
[ -n "$CLI_VERSION" ] || CLI_VERSION="unknown"
RUN_ID="${MANGO_EVAL_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
RUN_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

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
  if grep -qE '"loggedIn"[[:space:]]*:[[:space:]]*true' <<<"$(claude auth status --json 2>/dev/null || true)"; then
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
# $SANDBOX is the TEMPLATE/reference clone: the two validator self-tests run
# inside it, and every WORKER gets its own independent clone of the same shape
# (see provision_sandbox / the dispatcher) so concurrent dispatches share nothing.
TMPROOT="$(mktemp -d)"
SANDBOX="$TMPROOT/repo"
cleanup() { rm -rf "$TMPROOT" 2>/dev/null || true; }
trap cleanup EXIT
# The cache tally ledgers (see tally_add above) — outside the sandbox, gone with TMPROOT on exit.
CACHE_TALLY_DIR="$TMPROOT/tally"; mkdir -p "$CACHE_TALLY_DIR"
# The per-job result tally (see cov_assert above) — same lifetime, same reason.
COV_DIR="$TMPROOT/coverage"; mkdir -p "$COV_DIR"; : >"$COV_DIR/expected"; : >"$COV_DIR/judged"

# A minimal throwaway rule book + harness config so the skills run end-to-end
# without the operator having to supply one. Both live inside the sandbox.
EVAL_RULES_BODY="$(cat <<'RULES'
# Eval Rule Book (throwaway — generated by tests/eval/run.sh)

Minimal rule set so the mango skills execute end-to-end during the eval.

- Trace every change to a counted requirement row; no scope creep beyond the approved list.
- Each acceptance criterion needs a proving test at its own risk layer.
- Prefer the smallest change that satisfies the requirement.
- No secrets in code or config.
- **Tickets in this project are SYNTHETIC eval fixtures** describing a hypothetical application. A source
  a ticket references may legitimately be absent from this checkout, so treat its references as synthetic
  and continue — UNLESS a ticket states that its references are claims about THIS checkout, in which case
  resolve them against it. (This is the premise check's `declared synthetic` carve-out, declared once for
  the whole throwaway project instead of in every fixture. Without it, every fixture ticket about an
  application halts on a premise the eval sandbox can never satisfy — it ships no application source.)
RULES
)"
# The sandbox harness, parameterized on test_command. Default is `true` (a green baseline). A fixture
# may point it at the committed pre-existing failing check below so the baseline is GENUINELY red —
# so the harness JSON stays in one place and only the one field that must vary does. None of the six
# does so today; the parameterisation is kept because it is what makes the per-JOB write safe, and it
# is proven by the harness-parameterisation self-test rather than by a fixture.
# Written PER WORKER, PER JOB (see dispatch_one): each worker writes it into its OWN clone right
# before each dispatch, so a fixture that repoints test_command can never flip `.harness.json` under
# another dispatch that is still in flight. That was hazard (2) of parallelising this runner.
write_harness_at() {  # <repo-dir> <test_command>
  cat >"$1/.harness.json" <<HARNESS
{
  "rulebook_path": "docs/EVAL_RULES.md",
  "standards_path": "docs/EVAL_RULES.md",
  "repos": [{ "name": "app", "root": "." }],
  "test_command": "$2",
  "tickets_dir": "docs/tickets",
  "work_dir": "docs/tickets",
  "work_doc_mode": "auto",
  "stuck_threshold": 3,
  "explore_fanout": false,
  "track": "backend",
  "cost_tier": "standard",
  "token_optimizer": { "rtk": "expect", "headroom": { "enabled": false, "output_shaper": false }, "caveman": { "enabled": false, "scope": "non-critic-only" } },
  "branch_strategy": "fix|feat|chore/<KEY>-<slug>",
  "lessons_path": "docs/LESSONS.md",
  "tracker": { "base_url": "https://tracker.example.com", "project_key": "EVAL", "cli": "true", "read_mcp": null },
  "ticket_header_schema": { "Constraint": "C", "Requirement": "R", "Goal": "G", "Acceptance Criteria": "AC" }
}
HARNESS
}

# write_harness <test_command> — the SUITE-FACING form, called from `suite()`. It records the
# test_command that every job registered AFTER it carries; the job's worker writes it into that
# worker's own clone at dispatch time. So a fixture needing a red command gets one without any shared
# mid-run mutation, and no "restore the default afterwards" ordering dependency survives.
JOB_TEST_COMMAND="true"
write_harness() { JOB_TEST_COMMAND="$1"; }

# A committed pre-existing failing check, so a fixture can be given a GENUINELY red
# config.test_command to detect on a clean checkout (not a red baseline narrated in the ticket). The
# failing item names (pdf_snapshot_spec / snapshot drift / sub-pixel / "1 failed") appear ONLY here,
# never in the ticket text — so their presence in a transcript proves the model MEASURED the baseline
# by running the command rather than reading "red" off the ticket. Committed so it is part of the
# untouched checkout.
BASELINE_VERIFY_BODY="$(cat <<'VERIFY'
#!/bin/sh
# Simulated project verification command. On a CLEAN checkout it already fails on a pre-existing item
# OUTSIDE any single ticket's area — a genuinely RED baseline the analysis phase must DETECT by running
# it (never assume green, never narrate red from the ticket).
echo "PASS  spec/invoice/export_spec"
echo "FAIL  spec/legacy/pdf_snapshot_spec   — pre-existing snapshot drift (1 sub-pixel), unrelated to invoice export"
echo "1 failed, 1 passed"
exit 1
VERIFY
)"

# provision_sandbox <dir> — build one COMPLETE, INDEPENDENT throwaway project: a local clone of the
# repo, the throwaway rule book, the green-default harness, and the committed failing baseline check.
# Called once for the template $SANDBOX (which the dispatch-free validator self-tests run inside) and
# once PER WORKER. `git clone --local --no-hardlinks` is cheap, which is what makes per-worker
# isolation affordable: it removes hazard (1) of parallelising this runner — fixtures whose `execute`
# branches and commits would otherwise race inside one shared clone.
provision_sandbox() {  # <dir>
  local dir="$1"
  mkdir -p "$(dirname "$dir")"
  git clone --quiet --local --no-hardlinks "$REPO_ROOT" "$dir"
  mkdir -p "$dir/docs/tickets"
  printf '%s\n' "$EVAL_RULES_BODY" >"$dir/docs/EVAL_RULES.md"
  write_harness_at "$dir" "true"
  mkdir -p "$dir/tests/baseline"
  printf '%s\n' "$BASELINE_VERIFY_BODY" >"$dir/tests/baseline/verify.sh"
  git -C "$dir" -c user.email=eval@example.com -c user.name=mango-eval add tests/baseline/verify.sh >/dev/null 2>&1
  git -C "$dir" -c user.email=eval@example.com -c user.name=mango-eval commit -q -m "eval: pre-existing red baseline check (fixture scaffolding)" >/dev/null 2>&1
  # Record the baseline this tree must be restored to before EVERY job (see reset_sandbox). Kept
  # BESIDE the tree, not inside it, so `git clean -fdx` can never delete the thing that defines clean.
  printf '%s\t%s\n' "$(git -C "$dir" rev-parse --abbrev-ref HEAD)" "$(git -C "$dir" rev-parse HEAD)" >"${dir}.base"
}
provision_sandbox "$SANDBOX"

# reset_sandbox <dir> — restore a worker clone to the state provision_sandbox left it in.
# Per-worker isolation was only HALF the invariant. A worker claims MANY jobs and ran every one of
# them in ONE tree, with no reset in between: whatever job N wrote — a work doc, a docs/LESSONS.md, a
# stray branch, a commit — was still on disk when job N+1 started. That residue does not race; it
# silently FALSIFIES the premise of any fixture whose ticket describes a project state. A greenfield
# fixture that injects "no lesson record has ever been written" reads the previous job's LESSONS.md,
# correctly refuses its own ticket as false, and fails an assertion that was right all along — and
# which job lands where depends on the scheduler, so it fails intermittently. Every job now starts
# from the recorded baseline, and assert_job_start_clean below turns that into a counted assertion.
reset_sandbox() {  # <dir>
  local dir="$1" branch base b
  [ -f "${dir}.base" ] || return 0
  IFS=$'\t' read -r branch base <"${dir}.base"
  [ -n "${base:-}" ] || return 0
  git -C "$dir" checkout -q --force "$branch" 2>/dev/null || git -C "$dir" checkout -q --force "$base"
  git -C "$dir" reset -q --hard "$base"
  for b in $(git -C "$dir" for-each-ref --format='%(refname:short)' refs/heads/ 2>/dev/null || true); do
    [ "$b" = "$branch" ] || git -C "$dir" branch -q -D "$b" >/dev/null 2>&1 || true
  done
  git -C "$dir" clean -qfdx >/dev/null 2>&1 || true
  # The rule book and the tickets dir are UNTRACKED scaffolding, so `clean` takes them: re-lay them
  # exactly as provision_sandbox did. The baseline check is committed, so `reset --hard` has it.
  mkdir -p "$dir/docs/tickets"
  printf '%s\n' "$EVAL_RULES_BODY" >"$dir/docs/EVAL_RULES.md"
}

# assert_job_start_clean <dir> — echoes each residue it finds and returns non-zero on any; returns 0
# iff <dir> is at its provisioned baseline: on the base branch, no branch from an earlier job, no
# work doc, no lessons file, rule book present. Parameterized on the dir so the guard is self-tested
# below against a THROWAWAY dirtied repo — its teeth are proven without dirtying a real worker tree.
assert_job_start_clean() {  # <dir>
  local dir="$1" bad=0 branch base head stray docs
  [ -f "${dir}.base" ] || { echo "    RESIDUE: no provisioning baseline recorded for $dir"; return 1; }
  IFS=$'\t' read -r branch base <"${dir}.base"
  head="$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo UNKNOWN)"
  [ "$head" = "$branch" ] || { echo "    RESIDUE: HEAD is on '$head', not '$branch'"; bad=1; }
  stray="$(git -C "$dir" for-each-ref --format='%(refname:short)' refs/heads/ 2>/dev/null | grep -v "^${branch}$" || true)"
  [ -z "$stray" ] || { echo "    RESIDUE: branch(es) left by an earlier job: $(echo $stray)"; bad=1; }
  docs="$( (cd "$dir" && ls docs/tickets/*.work.md docs/LESSONS.md) 2>/dev/null || true)"
  [ -z "$docs" ] || { echo "    RESIDUE: artifact(s) left by an earlier job: $(echo $docs)"; bad=1; }
  [ -s "$dir/docs/EVAL_RULES.md" ] || { echo "    RESIDUE: the scaffolded rule book is missing"; bad=1; }
  [ "$bad" -eq 0 ]
}

# assert_job_starts_clean <ledger-file> — the run-level half: zero jobs started on a dirtied tree.
# Parameterized on the ledger so it is self-tested against a synthetic residue row.
assert_job_starts_clean() {  # <ledger-file>
  local ledger="$1" residue
  residue="$(grep -c '^residue' "$ledger" 2>/dev/null || true)"; residue="${residue:-0}"
  [ "$residue" -eq 0 ] && return 0
  echo "    RESIDUE: $residue job(s) started on a tree an earlier job had dirtied:"
  grep '^residue' "$ledger" | sed 's/^/      /'
  return 1
}

PLUGIN_DIR="$SANDBOX/plugins/mango"

# All fixtures run headless inside a throwaway clone against the SHIPPED skills
# (--plugin-dir), so the eval tests what the repo ships, not whatever the operator
# happens to have installed. Default headless permissions are used (no
# privilege-bypass flag): the assertions read the transcript of artifacts the
# skills produce/describe, and the isolated clone — not a permission flag — is what
# guarantees a fixture can never touch the live checkout.
claude_run() {  # <repo-dir> <prompt...>
  local repo="$1"; shift
  # </dev/null (v1.15.0): the worker loop reads the job schedule on ITS OWN stdin
  # (`while read -r idx; do … done <"$JOBS_DIR/schedule"`). Without this redirection every
  # dispatched `claude -p` inherits that descriptor and may CONSUME schedule lines, silently
  # dropping jobs from the run — a coverage hole no assertion can see, because the dropped job
  # is never asserted either. The prompt travels in argv; a dispatch needs no stdin at all.
  ( cd "$repo" && claude -p --plugin-dir "$repo/plugins/mango" "$@" </dev/null )
}

# --- Job registry + parallel dispatcher ---------------------------------------
# The collect pass fills this registry; the dispatcher drains it. Every piece of cross-process
# state is a FILE, never a shell variable: workers are background subshells, exactly like the
# command-substitution subshells that once silently lost the cache tallies (v1.7.5 Fix 4).
JOBS_DIR="$TMPROOT/jobs";     mkdir -p "$JOBS_DIR"
CLAIMS_DIR="$TMPROOT/claims"; mkdir -p "$CLAIMS_DIR"
WORKER_LEDGER="$TMPROOT/worker-trees"; : >"$WORKER_LEDGER"
JOB_START_LEDGER="$TMPROOT/job-starts";   : >"$JOB_START_LEDGER"
DONE_LEDGER="$TMPROOT/dispatched";     : >"$DONE_LEDGER"
JOB_COUNT=0
PHASE=collect        # collect | assert — see the two-pass note in the header

# Scheduling weights, derived from the fixture→skill map. Longest-first (LPT) ordering keeps a slow
# dispatch from being the last one to start. This is a HINT ONLY: it changes the ORDER jobs are
# claimed in, never which jobs run, what is asserted, or any count. A wrong weight costs seconds.
declare -A SKILL_WEIGHT=(
  [refine]=4 [analysis]=4 [design]=4 [autorun]=4 [breakdown]=3 [execute]=2
  [review]=1 [finalise]=1 [solve]=1 [budget]=1 [codify]=1
)
job_weight() {  # <fixture-name>
  local mapped="${FIXTURE_SKILLS[$1]:-}" w=1 s
  for s in $mapped; do [ "${SKILL_WEIGHT[$s]:-1}" -gt "$w" ] && w="${SKILL_WEIGHT[$s]}"; done
  echo "$w"
}

# transcript_path <name> — ONE rule for the transcript filename, so the dispatcher that writes it
# and the assert pass that greps it can never disagree.
transcript_path() { echo "$TDIR/${1//[^A-Za-z0-9_-]/-}.log"; }

# job_selected <name> — honours --only. With no --only, every job is selected (the full suite).
job_selected() { [ -z "$ONLY" ] && return 0; grep -qE "$ONLY" <<<"$1"; }

# job_register <kind> <name> <prompt> — record one dispatch. The prompt goes to a FILE (prompts carry
# newlines and quotes), the rest to a tab-separated meta file.
# The job INDEX comes from a counter FILE, not a shell variable: every registration happens inside
# `t="$(run_fixture …)"` — a command substitution, i.e. a SUBSHELL — so `JOB_COUNT=$((JOB_COUNT+1))`
# would be discarded on exit and every job would overwrite job 1 (the v1.7.5 Fix 4 trap, one layer up).
: >"$JOBS_DIR/.count"
job_register() {  # <fixture|scenario> <name> <prompt>
  local idx
  idx=$(( $(cat "$JOBS_DIR/.count" 2>/dev/null || echo 0) + 0 ))
  idx=$((idx + 1))
  printf '%s' "$idx" >"$JOBS_DIR/.count"
  printf '%s' "$3" >"$JOBS_DIR/$idx.prompt"
  printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$JOB_TEST_COMMAND" "$(job_weight "$2")" >"$JOBS_DIR/$idx.meta"
}

# dispatch_one <job-idx> <repo-dir> — run one registered job inside the calling worker's OWN clone.
# The cache path is unchanged: a fixture whose skills-hash is unchanged reuses its last GREEN
# transcript with no `claude -p` dispatch at all.
dispatch_one() {
  local idx="$1" repo="$2" wid="${3:-?}" kind name testcmd weight file prompt transcript hit t0 secs
  IFS=$'\t' read -r kind name testcmd weight <"$JOBS_DIR/$idx.meta"
  file="$(transcript_path "$name")"
  t0="$(prof_now)"
  if [ "$kind" = fixture ] && hit="$(cache_get "$name")"; then
    { echo "== fixture: $name (CACHE-HIT — skills-hash unchanged, reused GREEN transcript; no claude -p dispatch) =="
      cat "$hit"; } >"$file"
    tally_add cache-hits "$name"
    tally_add timing "$(printf '%s\t%s\thit' "$name" "$(( ($(prof_now) - t0) / 1000000000 ))")"
    prof_time "$name" "$t0" hit fixture
    printf '%s\n' "$name" >>"$DONE_LEDGER"
    echo "  cache-hit: $name (skills unchanged — reused green transcript, no dispatch)" >&2
    return 0
  fi
  write_harness_at "$repo" "$testcmd"
  prompt="$(cat "$JOBS_DIR/$idx.prompt")"
  if [ "$kind" = fixture ]; then
    transcript="$(claude_run "$repo" "$prompt"$'\n\nTicket:\n'"$(cat "$FIXTURES/$name.md")" 2>&1 || true)"
    { echo "== fixture: $name =="; echo "$transcript"; } >"$file"
    tally_add fresh-runs "$name"
    prof_time "$name" "$t0" fresh fixture
  else
    transcript="$(claude_run "$repo" "$prompt" 2>&1 || true)"
    { echo "== scenario: $name =="; echo "$transcript"; } >"$file"
    prof_time "$name" "$t0" n-a scenario
  fi
  printf '%s\n' "$name" >>"$DONE_LEDGER"
  secs=$(( ($(prof_now) - t0) / 1000000000 ))
  # Recorded for EVERY run, not only under MANGO_EVAL_PROFILE: the end-of-run summary below needs it,
  # and batch sizing needs the summary.
  tally_add timing "$(printf '%s\t%s\t%s' "$name" "$secs" "$kind")"
  echo "  dispatched $(wc -l <"$DONE_LEDGER" | tr -d ' ')/$JOB_COUNT  $name  (worker $wid, ${secs}s)" >&2
}

# worker <index> — provisions its OWN clone, then claims jobs until none are left. A job is claimed
# by an ATOMIC `mkdir`, so two workers can never take the same job and no lock/flock dependency is
# needed. The worker DISPOSES its tree when it is out of work; both events are recorded in the
# worker-tree ledger, which the disposal guard asserts against.
worker() {  # <index>
  local w="$1" wtree="$TMPROOT/w$w" repo="$TMPROOT/w$w/repo" idx
  provision_sandbox "$repo"
  printf 'created\t%s\n' "$wtree" >>"$WORKER_LEDGER"
  while read -r idx; do
    mkdir "$CLAIMS_DIR/$idx" 2>/dev/null || continue   # already claimed — next
    # Every job starts from the provisioned baseline, never from the previous job's leftovers, and
    # the outcome is RECORDED so "each job started clean" is a counted assertion, not a comment.
    reset_sandbox "$repo"
    if assert_job_start_clean "$repo" >/dev/null 2>&1; then
      printf 'clean\t%s\n' "$idx" >>"$JOB_START_LEDGER"
    else
      printf 'residue\t%s\t%s\n' "$idx" "$(cut -f2 <"$JOBS_DIR/$idx.meta")" >>"$JOB_START_LEDGER"
    fi
    dispatch_one "$idx" "$repo" "$w"
  done <"$JOBS_DIR/schedule"
  rm -rf "$wtree"
  printf 'disposed\t%s\n' "$wtree" >>"$WORKER_LEDGER"
}

# dispatch_jobs — run every registered job across $WORKERS workers. Returns once all are done;
# the assert pass then judges the transcripts in script order, so output stays deterministic.
dispatch_jobs() {
  local idx nw w p pids=()
  [ "$JOB_COUNT" -gt 0 ] || { echo "== no jobs registered (check --only) ==" >&2; return 0; }
  : >"$JOBS_DIR/weights"
  for idx in $(seq 1 "$JOB_COUNT"); do
    printf '%s %s\n' "$(cut -f4 <"$JOBS_DIR/$idx.meta")" "$idx" >>"$JOBS_DIR/weights"
  done
  sort -k1,1nr -k2,2n "$JOBS_DIR/weights" | awk '{print $2}' >"$JOBS_DIR/schedule"
  nw="$WORKERS"; [ "$nw" -le "$JOB_COUNT" ] || nw="$JOB_COUNT"
  echo >&2
  echo "== dispatching $JOB_COUNT job(s) across $nw worker(s), each in its OWN throwaway clone ==" >&2
  for w in $(seq 1 "$nw"); do worker "$w" & pids+=("$!"); done
  for p in "${pids[@]}"; do wait "$p" || true; done
  echo "== dispatch complete: $(wc -l <"$DONE_LEDGER" | tr -d ' ')/$JOB_COUNT job(s) ==" >&2
}

# assert_worker_trees_disposed <ledger-file> — echoes each leak and returns non-zero on any; returns
# 0 iff every worker tree the ledger recorded as created was also recorded disposed AND is gone from
# disk. Parameterized on the ledger so it is self-tested below against a synthetic UNdisposed tree —
# the guard's teeth are proven without leaving a real one behind.
assert_worker_trees_disposed() {  # <ledger-file>
  local ledger="$1" created disposed bad=0 d
  created="$(grep -c '^created' "$ledger" 2>/dev/null || true)"; created="${created:-0}"
  disposed="$(grep -c '^disposed' "$ledger" 2>/dev/null || true)"; disposed="${disposed:-0}"
  [ "$created" = "$disposed" ] || { echo "    LEAK: $created worker tree(s) created but $disposed disposed"; bad=1; }
  while read -r _tag d; do
    [ -n "${d:-}" ] || continue
    [ -e "$d" ] && { echo "    LEAK: worker tree still on disk: $d"; bad=1; }
  done < <(grep '^created' "$ledger" 2>/dev/null || true)
  [ "$bad" -eq 0 ]
}

# judged_body <transcript-file> — the transcript AS JUDGED. The harness writes its OWN provenance
# header into the file (`== fixture: <name> ==`), and that header carries the fixture NAME: for a
# a fixture whose NAME contains a word an assertion looks for, that assertion matched the
# HARNESS's text, not the model's, and passed no matter what the model said. Every regex is judged
# against the body with those header lines removed, so an assertion can only ever pass on output the
# model actually produced. (v1.15.0 — one fully-unfalsifiable assertion and ~54 partial ones had this
# escape hatch at their root; no assertion could have found it, because the vacuity was in the
# harness rather than in any single check.)
judged_body() { grep -v -e '^== fixture: ' -e '^== scenario: ' -- "$1" 2>/dev/null || true; }

# transcript_unusable <transcript-file> — echoes a REASON and returns 0 when this file is not a
# judgeable record of a mango run. It exists because a `claude -p` that dies on `API Error: 529
# Overloaded` still writes a file, and a file that never ran is the perfect false-green: three
# assertions in this suite once PASSED on 529 transcripts. A no-run must never be scored — not as a
# pass, and not as a skip. The markers are the CLI's own error shape, anchored, so a transcript that
# merely DISCUSSES error handling cannot trip it.
transcript_unusable() {
  local file="$1" body marker
  body="$(judged_body "$file")"
  case "$body" in
    *[![:space:]]*) ;;
    *) echo "the dispatch produced an EMPTY transcript body"; return 0 ;;
  esac
  marker="$(grep -m1 -E '^[[:space:]]*(API Error|Execution error)[: ]|API Error: [0-9]{3}' <<<"$body" || true)"
  if [ -n "$marker" ]; then
    echo "the dispatch failed with a CLI/API error, so the fixture NEVER RAN: $(printf '%s' "$marker" | cut -c1-90)"
    return 0
  fi
  return 1
}

# assert_judgeable <label> <transcript-file> — is there a transcript to judge? Returns 0 when yes.
# Three outcomes, and only the first is coverage:
#   * a usable transcript                      → judge it.
#   * a transcript that records a FAILED DISPATCH (API error, or an empty body) → FAIL loudly,
#     always, --only or not. The fixture did not run, so nothing about it has been proven, and the
#     one thing that must never happen is scoring it.
#   * no transcript at all → under --only the job was filtered out: SKIPPED and counted skipped
#     (never silently passed, and the run names the selection). With no --only there is no legitimate
#     way for a transcript to be missing — a job was asserted but never registered — so it FAILS.
assert_judgeable() {
  local label="$1" file="$2" why
  if [ -s "$file" ]; then
    why="$(transcript_unusable "$file")" || return 0
    total=$((total + 1)); fails=$((fails + 1))
    echo "  FAIL: $label (NOT JUDGEABLE — $why)  [${file#$REPO_ROOT/}]"
    cov_assert "$file" FAIL
    return 1
  fi
  if [ -n "$ONLY" ]; then
    skipped=$((skipped + 1))
    return 1
  fi
  total=$((total + 1)); fails=$((fails + 1))
  echo "  FAIL: $label (NO TRANSCRIPT — this assertion's dispatch was never registered)  [${file#$REPO_ROOT/}]"
  cov_assert "$file" FAIL
  return 1
}

# assert_contains <label> <transcript-file> <regex>
# $2 is the path to the teed transcript file (returned by run_fixture/run_prompt), so every
# PASS/FAIL line can name the exact transcript it judged. A no-op during the collect pass.
assert_contains() {
  local label="$1" file="$2" regex="$3"
  local rel="${file#$REPO_ROOT/}"
  if [ "$PHASE" != assert ]; then return 0; fi
  assert_judgeable "$label" "$file" || return 0
  total=$((total + 1))
  if grep -qiE -- "$regex" <<<"$(judged_body "$file")"; then
    echo "  PASS: $label  [$rel]"
    prof_assert "$(basename "$file" .log)" PASS
    cov_assert "$file" PASS
  else
    echo "  FAIL: $label (missing /$regex/)  [$rel]"
    fails=$((fails + 1))
    prof_assert "$(basename "$file" .log)" FAIL
    cov_assert "$file" FAIL
  fi
}

# assert_all <label> <transcript-file> <regex...> — passes iff EVERY regex matches the file.
# Use to encode a DECISION-level match (outcome + reasoning must both appear), so a correct
# behaviour passes under any wording while a wrong outcome — which drops one of the tokens —
# still fails.
assert_all() {
  local label="$1" file="$2"; shift 2
  local rel="${file#$REPO_ROOT/}" missing="" re body
  if [ "$PHASE" != assert ]; then return 0; fi
  assert_judgeable "$label" "$file" || return 0
  total=$((total + 1))
  # One strip, N regexes: the body is materialised ONCE so a multi-token assertion cannot pay the
  # strip N times, and so every token is judged against exactly the same text.
  body="$(judged_body "$file")"
  for re in "$@"; do
    grep -qiE -- "$re" <<<"$body" || missing="$missing /$re/"
  done
  if [ -z "$missing" ]; then
    echo "  PASS: $label  [$rel]"
    prof_assert "$(basename "$file" .log)" PASS
    cov_assert "$file" PASS
  else
    echo "  FAIL: $label (missing$missing)  [$rel]"
    fails=$((fails + 1))
    prof_assert "$(basename "$file" .log)" FAIL
    cov_assert "$file" FAIL
  fi
}

# assert_absent <label> <transcript-file> <regex> — passes iff the regex does NOT match. For a
# NEGATIVE control, where a match IS the failure (a guard that must stay silent). Keep the regex
# specific to what a real firing emits, so a transcript merely DISCUSSING the guard cannot fail it.
assert_absent() {
  local label="$1" file="$2" regex="$3"
  local rel="${file#$REPO_ROOT/}"
  if [ "$PHASE" != assert ]; then return 0; fi
  assert_judgeable "$label" "$file" || return 0
  total=$((total + 1))
  if grep -qiE -- "$regex" <<<"$(judged_body "$file")"; then
    echo "  FAIL: $label (present, must be absent: /$regex/)  [$rel]"
    fails=$((fails + 1))
    prof_assert "$(basename "$file" .log)" FAIL
    cov_assert "$file" FAIL
  else
    echo "  PASS: $label  [$rel]"
    prof_assert "$(basename "$file" .log)" PASS
    cov_assert "$file" PASS
  fi
}

# run_fixture <name> <prompt> — TWO-PASS (see the header). It always echoes the path of the
# transcript for this fixture, which is what the following assertions grep:
#   collect pass — REGISTERS the dispatch (prompt + the harness test_command in force here) and
#                  echoes the path the dispatcher WILL write. Assertions are no-ops this pass.
#   assert pass  — echoes the path the dispatcher DID write.
# Because both passes execute the same call site, a prompt can never drift from the assertions
# that judge it, and a fixture cannot be asserted without also being dispatched.
run_fixture() {
  local name="$1" prompt="$2"
  if [ "$PHASE" = collect ] && job_selected "$name"; then job_register fixture "$name" "$prompt"; fi
  transcript_path "$name"
}

# run_prompt <label> <prompt> — a fixture-less scenario prompt (no ticket attached). Same two-pass
# contract as run_fixture; scenarios have no cache path and always dispatch fresh.
run_prompt() {
  local label="$1" prompt="$2"
  if [ "$PHASE" = collect ] && job_selected "$label"; then job_register scenario "$label" "$prompt"; fi
  transcript_path "$label"
}

# banner <text> — a section header, printed once (assert pass only, so the collect pass is silent).
banner() { [ "$PHASE" = assert ] || return 0; echo; echo "$1"; }

# --- Emphasis/glyph-agnostic assertion tokens ---------------------------------
# EVERY regex reaches grep after `--`. A regex that starts with `-` (the fixtures assert on literal
# flags: `--tree`, `--no-reviewer`, `--no-challenger`) is otherwise parsed as an OPTION: grep exits 2
# with "unrecognized option", which assert_contains/assert_all read as "no match" and assert_absent
# would read as "absent" — a permanent red that no wording can clear, and a permanent GREEN on the
# absent side. Four assertions were unpassable this way from the day they shipped.
#
# The convention lives in tests/eval/README.md: match the DECISION, tolerate markdown emphasis,
# widen over wording — NEVER over outcome. Three shapes broke assertions that were judging
# demonstrably CORRECT behaviour, so they are named once here and reused:
#   * emphasis INSIDE a word — `**S**mall` / `**I**ndependent` breaks a contiguous substring match;
#   * a count-form negative — a skill emits `0 want-decisions asked` where a regex demanded a
#     negation phrase;
#   * a single glyph — `❌` may land in the work-doc table rather than the response text.
# Every token below is used BOTH by its fixture assertion AND by the dispatch-free
# assertion-convention self-test, so the self-test can never drift from the regex that ships. Each
# still requires the load-bearing outcome: a wrong decision matches none of them (proven, per token,
# by the self-test's WRONG transcript).
# RE_NOT_SILENT_ASSUMED is the one shared token that survives the retirement: refine-want-unattended-
# stops asserts it, and the assertion-convention self-test below proves it BOTH ways against synthetic
# transcripts (matches the correct wording, still misses the wrong behaviour). It was widened twice,
# each time over WORDING — a correct run writes the negative with the negation emphasised, and the
# counted REFINE: line carries the same claim as `0 ASSUMED`. Never widen a token over OUTCOME.
RE_NOT_SILENT_ASSUMED='not[ *_]{0,4}[^.]{0,30}(silen|fallback|hand.?back)|never[ *_]{1,4}(silent|assum)|no[ *_]{1,4}silent|REFINE:[^.]{0,120}[^0-9]0[ *_]{0,4}ASSUMED'
# The rationale is written subject-first as often as verb-first ("coverage removed, not moved", "takes
# the claims out of recall while nothing yet replaces them").

# --- Post-run safety guard (v1.6.1, Fix 1) -----------------------------------
# Every fixture runs inside $SANDBOX, so the LIVE checkout must stay pristine. This
# ASSERTS it — belt-and-suspenders over the structural isolation. If a future edit
# ever broke the `cd "$SANDBOX"` discipline (or a fixture ran `execute` in the wrong
# cwd), a leak into the live checkout could otherwise pass silently.
#
# assert_checkout_clean <repo-dir> [expected-branch] — echoes each leak it finds and returns non-zero
# on any; returns 0 iff <repo-dir> is pristine: HEAD on <expected-branch> (default: the branch this
# run started on), no stray *PROJ-* branch, no docs/tickets/*.work.md, no docs/EVAL_RULES.md.
# Parameterized on BOTH the dir and the branch so it is self-tested below on throwaway repos — a
# dirty one that must be caught, and a clean one on a non-main branch that must pass — proving the
# guard's teeth without ever risking the live checkout.
assert_checkout_clean() {
  local dir="$1" want="${2:-${EVAL_START_BRANCH:-main}}" bad=0 head stray docs
  head="$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo UNKNOWN)"
  [ "$head" = "$want" ] || { echo "    LEAK: HEAD is on '$head', not '$want' (the branch this run started on)"; bad=1; }
  # v1.16.0: list every branch and filter in grep, rather than passing 'refs/heads/*PROJ-*' to
  # for-each-ref. That pattern is fnmatch with FNM_PATHNAME, so its `*` does NOT cross a `/` — it
  # matched a top-level `PROJ-777` and MISSED `feat/PROJ-999-leak`, which is the shape mango's own
  # fixtures create and the shape this guard's own injection test uses. The miss was invisible
  # because that test's repo also had HEAD off main and a stray work doc, so the guard failed for
  # other reasons and the stray-branch rule was never once proven on its own. Each rule now has an
  # isolated non-vacuity test below.
  stray="$(git -C "$dir" for-each-ref --format='%(refname:short)' refs/heads 2>/dev/null |
             grep -E 'PROJ-' || true)"
  [ -z "$stray" ] || { echo "    LEAK: stray fixture branch(es): $(echo $stray)"; bad=1; }
  docs="$(git -C "$dir" ls-files 'docs/tickets/*.work.md' 'docs/EVAL_RULES.md' 2>/dev/null || true)"
  docs="$docs $( (cd "$dir" && ls docs/tickets/*.work.md docs/EVAL_RULES.md) 2>/dev/null || true)"
  docs="$(echo "$docs" | tr ' ' '\n' | sort -u | grep -v '^$' || true)"
  [ -z "$docs" ] || { echo "    LEAK: eval artifact(s) in live checkout: $(echo $docs)"; bad=1; }
  if [ "$bad" -ne 0 ]; then
    echo "    RECOVERY: git switch $want && git branch -D <stray> && rm -f docs/EVAL_RULES.md docs/tickets/*.work.md"
    echo "    (if a real commit stranded on the stray branch, cherry-pick it onto main FIRST)"
    return 1
  fi
  return 0
}

# --- Transcript-cache invalidation --------------------------------------------
# The cache is wiped whenever run.sh itself changes. A cached transcript is a record of what the
# model answered; it is re-judged from scratch on every reuse, so an edited assertion does not
# invalidate it — it re-reads it. Keying the wipe on the WHOLE file is coarser than the two-tier
# identity the retired suite carried, and deliberately so: with six fixtures the saving that bought
# is worth less than the machinery, and a coarse key can only ever err toward running fresh.
if [ "$CACHE_ENABLED" -eq 1 ]; then
  FP_FILE="$CACHE_DIR/.runner.fp"
  if [ ! -f "$FP_FILE" ] || [ "$(cat "$FP_FILE" 2>/dev/null)" != "$RUNNER_FP" ]; then
    rm -f "$CACHE_DIR"/*.green 2>/dev/null || true
    printf '%s' "$RUNNER_FP" >"$FP_FILE"
  fi
fi

# --- The suite ----------------------------------------------------------------
# Everything below runs TWICE: once with PHASE=collect (registering dispatches) and once with
# PHASE=assert (judging their transcripts) — see the header. The body is intentionally NOT
# re-indented into the function: keeping every fixture line byte-identical to its pre-parallel form
# is what makes "this is a scheduling change, not a coverage change" reviewable in the diff.
suite() {

banner "== refine-want-unattended-stops  (refine, autorun — Gate 0) =="
# T7/T8 refine-want-unattended-stops: an unresolved refine want-decision counts toward `j` and autorun
# stops; it is never a silent ASSUMED. A fully-locked ticket refine self-skipped on leaves `j` untouched.
t="$(run_fixture refine-want-unattended-stops 'Run the mango autorun skill against the injected run state in this ticket and answer the four numbered questions in order. Do not stop for my input.')"
assert_all "want-j: the unresolved want-decision counts toward j" "$t" 'want-decision' 'counts? toward|into[ *_]{1,4}j|j[ *_=:]{0,4}1|toward the (j|clarification)|clarification'
assert_all "want-j: the run STOPS at Gate 0 rather than guessing" "$t" 'stop|halt|does not (continue|proceed)|not[ *_]{1,4}(continue|proceed)' 'j[ *_=:]{0,4}1|Gate 0|human'
assert_all "want-j: it is NOT recorded as a silent ASSUMED that ships a PR" "$t" 'ASSUMED' "$RE_NOT_SILENT_ASSUMED"
assert_all "want-j: the open question reaches the operator verbatim" "$t" 'recommend|likely to want|activity|editorial' 'question|state|report|surfac|morning|verbatim'
assert_all "want-j: the fully-locked ticket self-skips and leaves j untouched" "$t" 'PROJ-903|self-skip|locked' 'j[ *_=:]{0,4}0|untouched|unaffected|no want|zero|correct'
assert_absent "want-j: no product decision is invented at 3am" "$t" '(I|we) (chose|picked|selected) (recent activity|similar users|editorial|option [abc])'

banner "== multi-clause-want  (analysis — Gate 1) =="
# multi-clause-want (v1.7.5 Fix 3e): a ratified want-decision with TWO clauses ("place the rows under the
# summary" AND "tappable through to detail") must become TWO matrix rows + TWO proof rows at Gate 1 — the
# injected single-row ✅ certification is FLAGGED (non-vacuous), not accepted.
t="$(run_fixture multi-clause-want 'Run the mango analysis skill on this ticket. Decompose the ratified want-decision into the requirements matrix and the verification plan, state how many rows it produces and why, and judge the single-row certification shown in the ticket. Do not stop for my input.')"
# Decision-level: the want-decision has TWO clauses and gets one row PER CLAUSE (outcome + reasoning).
assert_all "multi-clause-want: two clauses → one row per clause" "$t" 'two|2[[:space:]*_]*(rows|clause)|per clause|each clause' 'clause'
assert_all "multi-clause-want: both clauses are named (placement + tappable)" "$t" 'placement|under the summary|position' 'tappable|tap|navigat|detail view'
# Non-vacuous: the injected single-row certification is REJECTED / flagged as a finding.
assert_all "multi-clause-want: the injected 1-row certification is flagged (non-vacuous)" "$t" 'single[ -]row|one row|R-1|certif' 'not acceptable|unacceptable|reject|finding|insufficient|blocks?|must .{0,16}split|cannot .{0,16}(stand|certif)|flag'

banner "== provenance-authored-blocks  (design — Gate 2) =="
# ===========================================================================================
# v1.14.0 — fixture provenance (A), evidence provenance (E), the review-seat split (F)
# ===========================================================================================

# T1/T4 provenance-authored-blocks: an AC about a GROUPING HEURISTIC proven on authored fixtures alone
# is a layer-match failure that blocks Gate 2; an exclusion with no expiry does not rescue it.
t="$(run_fixture provenance-authored-blocks 'Run the mango design skill against the injected design state in this ticket and answer the four numbered questions in order. Do not stop for my input.')"
assert_all "prov-authored: AC2 is input-shape-dependent" "$t" 'AC2' 'input-shape|shape of (real )?input|heuristic|grouping|sensible|cannot be written'
assert_all "prov-authored: authored alone is not acceptable for AC2" "$t" 'authored' 'not[ *_]{1,4}(acceptable|sufficient|enough)|insufficient|❌|mismatch|fails'
assert_all "prov-authored: Gate 2 is blocked" "$t" 'Gate 2' 'block|not[ *_]{1,4}close|does not close|fails'
assert_all "prov-authored: the expiry-less exclusion does not rescue it" "$t" 'expiry|variant B' 'not[ *_]{1,4}(count|recorded|rescue)|still block|does not close|missing'
assert_contains "prov-authored: the EXCLUSIONS counted line is emitted" "$t" 'EXCLUSIONS:'

banner "== execute-commit-before-review  (execute, review — Gate 3-4) =="
# execute-commit-before-review (v1.7.5 Fix 3b): execute COMMITS the change-set BEFORE dispatching review
# (so a real committed diff exists for the ref-based inspection), AND an empty <base>..<branch> range
# triggers the `git diff HEAD` + `git status --porcelain -uall` fallback rather than a false "no changes".
t="$(run_fixture execute-commit-before-review 'Run the mango execute→review handoff on this ticket. State when execute commits relative to dispatching review and why, then state exactly what a reviewer does when the base..branch diff is empty. Do not stop for my input.')"
# Decision-level: commit happens BEFORE the review dispatch (outcome) because the review is ref-based (reasoning).
assert_all "execute-commit-before-review: commits before review is dispatched" "$t" 'commit' 'before .{0,30}(review|dispatch)|prior to .{0,24}(review|dispatch)|then .{0,12}(dispatch|flow).{0,20}review|first.{0,30}review'
assert_contains "execute-commit-before-review: because review is ref-based"      "$t" 'ref-based|<base>\.\.|base\.\.branch|git diff .{0,24}\.\.'
# Empty-diff fallback: git diff HEAD + git status --porcelain, not a "no changes" conclusion.
assert_all "execute-commit-before-review: empty range → git diff HEAD + status fallback" "$t" 'git diff head' 'porcelain|git status|uncommitted'
# Widened over WORDING (v1.8.0): the separator class again — a correct run writes "not a **no-change**
# LGTM" (hyphen, not space) and "falls back **before it concludes** anything".
assert_all "execute-commit-before-review: empty range is never a no-change verdict (non-vacuous)" "$t" 'empty' 'not .{0,30}(conclude|assume|no[ -]change)|never .{0,26}(conclude|no[ -]change|rubber)|must .{0,20}(fall ?back|check|verify)|before .{0,16}conclud|falls? back before'

banner "== lesson-claim-split  (finalise — Gate 4) =="
# lesson-claim-split (v1.9.0): the unit is the ATOMIC CLAIM, not the entry. One bundled lesson carrying a
# tool fact + a principle + a project fact + a demonstrably-skipped check must split into FOUR claims and
# classify each by type — and the classification must be a PROPOSAL the human confirms, never a decision.
t="$(run_fixture lesson-claim-split 'Run the mango finalise phase learning loop on the bundled durable lesson in this ticket. Split it, classify each claim with its type and evidence and recall handle, and emit the counted lines. Do not stop for my input.')"
assert_contains "claim-split: emits the CLAIMS counting line" "$t" 'CLAIMS:'
# Decision-level: FOUR atomic claims come out of ONE entry (outcome + the reasoning token).
assert_all "claim-split: one entry splits into four atomic claims" "$t" 'four|4[ *_]*(atomic[ *_]*)?claim' 'claim'
assert_all "claim-split: the helper fact is type 1 (tool-constraint)" "$t" 'get_or_set|cache client|swallow' 'tool.constraint|type[ *_:]*1'
assert_all "claim-split: the guard principle is type 2 (heuristic)" "$t" 'guard' 'heuristic|type[ *_:]*2'
assert_all "claim-split: the settings-table fact is type 5 (project ground-truth)" "$t" 'settings' 'ground.truth|type[ *_:]*5|project/domain'
assert_all "claim-split: the skipped rule-book check is type 3 (skill-gap SIGNAL)" "$t" 'skill.gap|type[ *_:]*3' 'signal|skill_gap_path|maintainer'
# Non-vacuous the other way: the classification PROPOSES; it does not decide.
assert_all "claim-split: classification is a proposal, not a decision" "$t" 'propos' 'confirm|ratif|human|you '

banner "== greenfield-promote-zeros  (promote — negative control) =="
# G3 greenfield-promote-zeros: promote on an empty corpus emits zeros, proposes nothing and stops.
t="$(run_fixture greenfield-promote-zeros 'Run the mango promote skill against the project state described here and answer the five numbered questions, emitting the counted PROMOTE: line and the per-class table first. Do not stop for my input.')"
assert_contains "greenfield-promote: the PROMOTE counted line is emitted" "$t" 'PROMOTE:'
assert_all "greenfield-promote: zero classes and zero candidates" "$t" '0 class|no class|zero class|0 candidate|no candidate|zero candidate' 'propos|class|candidate'
assert_all "greenfield-promote: nothing is drafted and nothing is written" "$t" 'rules written[ *_:=]*0|nothing[^.]{0,24}(writ|draft|creat)|no rule text' 'writ|draft|propos'
assert_all "greenfield-promote: it stops rather than asking a ratification question" "$t" 'stop|halt|end|no candidate' 'no[^.]{0,30}(question|gate|ratif)|nothing to ratify|stops'
assert_all "greenfield-promote: an absent corpus is not an error" "$t" 'not[ *_]{1,4}(an )?error|no[ *_]{1,4}error|neither|not configured|says so' 'corpus|LESSONS|lessons_path|absent|missing'
assert_absent "greenfield-promote: no rule is written" "$t" 'rules written[ *_:=]*[1-9]'

}   # end suite()

# --- Drive the two passes ------------------------------------------------------
# collect (silent, no dispatch) → dispatch in parallel → assert (sequential output).
RUN_T0="$(prof_now)"
PHASE=collect; suite
# Read the registered job count back out of its counter file (registration happens in subshells).
JOB_COUNT="$(cat "$JOBS_DIR/.count" 2>/dev/null || echo 0)"; JOB_COUNT="${JOB_COUNT:-0}"

DISPATCH_T0="$(prof_now)"
dispatch_jobs
DISPATCH_SECS=$(( ($(prof_now) - DISPATCH_T0) / 1000000000 ))
echo
echo "== assertions (judged in script order — a parallel run reads like a sequential one) =="
PHASE=assert;  suite

# --- eval transcript-cache self-test (v1.7.3 Fix E) --------------------------
# Runner self-test (no `claude -p`): the cache's three guarantees, tested against the REAL gate
# functions with synthetic inputs — (a) hash-match → cache-hit (skip the dispatch); (b) hash-change →
# run fresh (fail-safe to run); (c) --no-cache → all fresh (milestone run). Keeps coverage cheap.
echo
echo "== eval transcript-cache self-test =="
_std="$TMPROOT/cache-selftest"; mkdir -p "$_std"
_sti="$TMPROOT/st-input"; echo v1 >"$_sti"
: >"$_std/fix.$(hash_files "$_sti").green"; echo "green transcript" >"$_std/fix.$(hash_files "$_sti").green"
_saved_cache_enabled="$CACHE_ENABLED"; CACHE_ENABLED=1
# (a) hash-match → cache-hit
total=$((total + 1))
if [ -n "$(cache_hit_path "$_std/fix.$(hash_files "$_sti").green")" ]; then
  echo "  PASS: cache self-test: hash-match → cache-hit (reuse, no dispatch)"
else
  echo "  FAIL: cache self-test: hash-match should be a cache-hit"; fails=$((fails + 1))
fi
# (b) hash-change → run fresh (no green under the new hash)
echo v2 >>"$_sti"
total=$((total + 1))
if [ -z "$(cache_hit_path "$_std/fix.$(hash_files "$_sti").green" 2>/dev/null)" ]; then
  echo "  PASS: cache self-test: hash-change → run fresh (fail-safe to run)"
else
  echo "  FAIL: cache self-test: hash-change should miss (must run fresh)"; fails=$((fails + 1))
fi
# (c) --no-cache → miss even on a matching hash (all fresh)
echo v1 >"$_sti"; _stg="$_std/fix.$(hash_files "$_sti").green"; echo green >"$_stg"
CACHE_ENABLED=0
total=$((total + 1))
if [ -z "$(cache_hit_path "$_stg" 2>/dev/null)" ]; then
  echo "  PASS: cache self-test: --no-cache → all fresh (milestone run)"
else
  echo "  FAIL: cache self-test: --no-cache must disable reuse"; fails=$((fails + 1))
fi
CACHE_ENABLED="$_saved_cache_enabled"

# --- harness-parameterisation self-test (v1.8.0) ------------------------------
# The per-JOB harness write is what makes concurrency safe, so it must actually write the command it
# is handed. A stray `$1` in `write_harness_at` once wrote the repo PATH into `test_command`, which
# broke a fixture's premise (a genuinely red command) while its assertions still passed, because the
# model found the committed check by itself. Two counted assertions, no dispatch.
banner "== harness parameterisation self-test =="
_hp="$TMPROOT/harness-selftest"; mkdir -p "$_hp"
write_harness_at "$_hp" "true"
total=$((total + 1))
if grep -q '"test_command": "true"' "$_hp/.harness.json"; then
  echo "  PASS: harness-parameterisation: the green default lands in test_command"
else
  echo "  FAIL: harness-parameterisation: test_command is not the command it was given — $(grep '"test_command"' "$_hp/.harness.json")"
  fails=$((fails + 1))
fi
write_harness_at "$_hp" "sh tests/baseline/verify.sh"
total=$((total + 1))
if grep -q '"test_command": "sh tests/baseline/verify.sh"' "$_hp/.harness.json"; then
  echo "  PASS: harness-parameterisation: a per-job override (the failing baseline command) lands in test_command"
else
  echo "  FAIL: harness-parameterisation: a per-job override did not land — $(grep '"test_command"' "$_hp/.harness.json")"
  fails=$((fails + 1))
fi

# --- matcher-under-pipefail self-test -----------------------------------------
# Four counted assertions against a 250 KB transcript whose token sits on line 1 — the shape that made
# `printf | grep -q` fail 30 times out of 30. Judged through the SHIPPED assert_all and
# assert_contains, twenty times each, because the defect is a RACE: one evaluation proves nothing, and
# a check that ran once would have passed on the broken code roughly as often as not.
#
# Under `set -o pipefail`, `grep -q` exits at the FIRST match; the writer, still writing, takes SIGPIPE
# and exits 141, and pipefail hands 141 to the caller — so a token that is plainly PRESENT is read as
# missing. It affected assert_all, which is what the six fixtures below are mostly built from. Within
# one run the failure is invisible; across runs it is indistinguishable from the model phrasing things
# differently, and the standing response to that signature was to widen the token. The fix is the
# herestring at every site; this is the check that keeps the piped shape from coming back.
echo
echo "== matcher-under-pipefail self-test (a present token is never read as missing) =="
_mp="$TMPROOT/matcher-pipefail"; mkdir -p "$_mp"
_mp_t="$_mp/big.log"
{ echo "== fixture: _selftest_big =="
  echo "MATCHTOKEN and SECONDTOKEN on one line, where grep -q stops reading and leaves"
  echo "a quarter of a megabyte still to be written by whatever is feeding it."
  base64 </dev/urandom 2>/dev/null | head -c 250000 || true
  echo; } >"$_mp_t" 2>/dev/null || true
total=$((total + 1))
if [ "$(wc -c <"$_mp_t")" -gt 200000 ]; then
  echo "  PASS: matcher: the probe body is $(wc -c <"$_mp_t") bytes (big enough to lose the race)"
else
  echo "  FAIL: matcher: the probe body is too small to exercise the defect — the test is vacuous"
  fails=$((fails + 1))
fi
# (2) THE ONE THAT MATTERS — assert_all is the shape that raced. Two tokens, both plainly present,
#     twenty evaluations of the SHIPPED function. On the piped form this reports missing tokens.
_mp_miss=0; _mp_i=0
while [ "$_mp_i" -lt 20 ]; do
  _mp_i=$((_mp_i + 1))
  _mp_out="$( PHASE=assert; COV_DIR=""; ONLY=""; PROFILE=""; total=0; fails=0; skipped=0
              assert_all "probe" "$_mp_t" 'MATCHTOKEN' 'SECONDTOKEN' 2>&1 )" || true
  case "$_mp_out" in "  PASS:"*) ;; *) _mp_miss=$((_mp_miss + 1)) ;; esac
done
total=$((total + 1))
if [ "$_mp_miss" -eq 0 ]; then
  echo "  PASS: matcher: assert_all matched two PRESENT tokens 20/20 on a 250 KB body"
else
  echo "  FAIL: matcher: assert_all lost a PRESENT token $_mp_miss time(s) in 20 — a spurious red"
  fails=$((fails + 1))
fi
# (3) and it must still MISS a token that is genuinely absent, or (2) is satisfied by a matcher that
#     always says yes.
total=$((total + 1))
_mp_out="$( PHASE=assert; COV_DIR=""; ONLY=""; PROFILE=""; total=0; fails=0; skipped=0
            assert_all "probe" "$_mp_t" 'MATCHTOKEN' '__absent_token__' 2>&1 )" || true
case "$_mp_out" in
  *"/__absent_token__/"*) echo "  PASS: matcher: an ABSENT token still fails (the probe is not vacuous)" ;;
  *) echo "  FAIL: matcher: an absent token passed — the matcher is answering yes unconditionally"
     fails=$((fails + 1)) ;;
esac
# (4) assert_contains was protected only by judged_body's trailing `|| true`. Keep that a tested
#     property rather than an accident: if the guard is ever removed, this starts failing.
_mp_miss=0; _mp_i=0
while [ "$_mp_i" -lt 20 ]; do
  _mp_i=$((_mp_i + 1))
  _mp_out="$( PHASE=assert; COV_DIR=""; ONLY=""; PROFILE=""; total=0; fails=0; skipped=0
              assert_contains "probe" "$_mp_t" 'MATCHTOKEN' 2>&1 )" || true
  case "$_mp_out" in "  PASS:"*) ;; *) _mp_miss=$((_mp_miss + 1)) ;; esac
done
total=$((total + 1))
if [ "$_mp_miss" -eq 0 ]; then
  echo "  PASS: matcher: assert_contains found a present token 20/20 on the same body"
else
  echo "  FAIL: matcher: assert_contains lost a PRESENT token $_mp_miss time(s) in 20"
  fails=$((fails + 1))
fi
# The rule itself, stated as a check: no matcher in this file may pipe into a short-circuiting grep.
total=$((total + 1))
# Comment lines are stripped first: the rule's own explanation above SPELLS the bad shape, and a check
# that trips over its own documentation teaches the next person to delete the documentation.
# `grep -c` reads all of its input, so this pipeline cannot be poisoned the way -q can.
_mp_pipes="$(awk '!/^[[:space:]]*#/' "${BASH_SOURCE[0]}" | grep -cE '\| *grep +-[A-Za-z]*(q|m1)' || true)"
if [ "${_mp_pipes:-0}" -eq 0 ]; then
  echo "  PASS: matcher: no pipeline in this file feeds a short-circuiting grep (the shape cannot return)"
else
  echo "  FAIL: matcher: $_mp_pipes pipeline(s) still feed a short-circuiting grep — pipefail can poison them"
  fails=$((fails + 1))
fi

# --- assertion-convention self-test (v1.8.0) ---------------------------------
# The teeth of the brittleness fix. Five assertions were FAILING ON CORRECT BEHAVIOUR — emphasis
# inside a word (`**S**mall`), a count-form negative (`0 want-decisions asked`), a control reported
# "unsplit"/"untouched", a bold `**before**`, and a `❌` written to the work doc instead of the
# response. Widening those regexes is only safe if they still MISS a wrong decision, so each widened
# token is proven BOTH ways here against synthetic transcripts: it must MATCH the correct wording
# that used to fail, and still MISS the wrong behaviour. No `claude -p` — free and deterministic, and
# it uses the SAME RE_* variables the fixtures use, so a future re-pinning of a glyph or a narrowing
# of a token breaks this self-test rather than silently returning to a flaky assertion.
banner "== assertion-convention self-test (widened over wording, never over outcome) =="
_ac="$TMPROOT/assertion-convention"; mkdir -p "$_ac"

# re_all_match <file> <regex...> — 0 iff EVERY regex matches, using the same grep the assertions use.
re_all_match() {
  local f="$1"; shift
  local re
  for re in "$@"; do grep -qiE -- "$re" "$f" || return 1; done
  return 0
}
# selftest_assertion <label> <correct-file> <wrong-file> <regex...> — one counted assertion: the
# SHIPPED regex set must match the correct transcript and miss the wrong one.
selftest_assertion() {
  local label="$1" good="$2" bad="$3"; shift 3
  total=$((total + 1))
  if ! re_all_match "$good" "$@"; then
    echo "  FAIL: assertion-convention: $label — MISSES the correct transcript (still brittle)"
    fails=$((fails + 1))
  elif re_all_match "$bad" "$@"; then
    echo "  FAIL: assertion-convention: $label — VACUOUS: also matches the WRONG behaviour"
    fails=$((fails + 1))
  else
    echo "  PASS: assertion-convention: $label (matches correct wording, still misses wrong behaviour)"
  fi
}

cat >"$_ac/assumed-window.correct" <<'AC'
**2. No — `ASSUMED` is not the fallback for silence.**
The `ASSUMED (awaiting ratification)` path applies only where the user explicitly hands the decision
back ("your call"). Recording an unanswered want-decision that way at 23:00 would invent the answer.
AC
cat >"$_ac/assumed-window.wrong" <<'AC'
**2. Yes — with no answer by 23:00 I recorded the want-decision ASSUMED (awaiting ratification),
adopted the recommendation, and shipped the PR.** Overnight quiet is a hand-back in practice, and the
merge-strategy note narrows, does not remove, the judgement.
AC
selftest_assertion "subject inside the window — \"not the fallback for silence\" (R5)" \
  "$_ac/assumed-window.correct" "$_ac/assumed-window.wrong" \
  'ASSUMED' "$RE_NOT_SILENT_ASSUMED"

cat >"$_ac/assumed-count.correct" <<'AC'
REFINE: 1 unresolved surfaced | 1 want-decision asked | 0 how-decision resolved+cited | 0 ASSUMED | skip: no
Gate 0 holds: the want-decision is unresolved, so j = 1 and the run stops for the operator.
AC
cat >"$_ac/assumed-count.wrong" <<'AC'
REFINE: 1 unresolved surfaced | 1 want-decision asked | 0 how-decision resolved+cited | 1 ASSUMED | skip: no
I recorded the unanswered want-decision as ASSUMED and opened the PR.
AC
selftest_assertion "counted artifact carries it — 0 ASSUMED in the REFINE line (R5)" \
  "$_ac/assumed-count.correct" "$_ac/assumed-count.wrong" \
  'ASSUMED' "$RE_NOT_SILENT_ASSUMED"

# --- option-shaped regex self-test -------------------------------------------
# The fixtures assert on literal flags (`--tree`, `--no-reviewer`, `--no-challenger`). Without `--`,
# grep parses those as OPTIONS and exits 2, which reads as "no match" on assert_contains/assert_all
# and as "absent" on assert_absent — four assertions were unpassable, and the absent side would have
# been silently green. This proves the judgement, not the wording: a flag PRESENT must match, a flag
# ABSENT must not.
cat >"$_ac/flag.correct" <<'AC'
Re-run the check on the tree under review: check_lines.py check <doc> --phase review --tree $(git rev-parse HEAD).
The seat that was waived is named in the verdict: REVIEWER: OFF (--no-reviewer); the challenger still ran.
AC
cat >"$_ac/flag.wrong" <<'AC'
Re-run the check on the tree under review: check_lines.py check <doc> --phase review.
The seat that was waived is named in the verdict; the challenger still ran.
AC
selftest_assertion "option-shaped regex is judged, not swallowed by grep (--tree / --no-reviewer)" \
  "$_ac/flag.correct" "$_ac/flag.wrong" \
  '--tree' '--no-reviewer'

# --- validator jargon-guard self-test (v1.7.5 Fix 1b) ------------------------
# The TEETH of the false-green fix. v1.7.4 claimed validate.py enforced a zero-jargon grep over shipped
# operational text while two shipped files still carried `v1 — "enough to run and learn"` and the
# validator PASSED — a false-green at the verification layer itself. This proves the fixed grep is
# NON-VACUOUS: inject a banned phrase into a shipped operational file → validate.py must FAIL; remove it
# → it must pass again. Runs entirely inside $SANDBOX (the throwaway clone), so the live checkout is
# never touched. No `claude -p` dispatch — deterministic and free.
echo
echo "== validator jargon-guard self-test =="
_vjg_run() { ( cd "$SANDBOX" && python3 scripts/validate.py 2>&1 ); }
# (0) Baseline: the sandbox clone (== the shipped tree) is clean of banned jargon.
total=$((total + 1))
if _vjg_run >/dev/null 2>&1; then
  echo "  PASS: validator jargon-guard: shipped tree passes with zero banned jargon"
else
  echo "  FAIL: validator jargon-guard: shipped tree does NOT pass validate.py"; fails=$((fails + 1))
  _vjg_run | tail -8
fi
# (1) Non-vacuous, per banned phrase, in a file that is IN the operational scan set. `README.md` is the
# repo-root README — the file v1.7.4's scan scope omitted entirely.
for _vjg_target in plugins/mango/skills/solve/SKILL.md README.md; do
  for _vjg_phrase in 'v1 — the old label' 'enough to run and learn' 'evidence: n=1' 'v1-learning'; do
    cp "$SANDBOX/$_vjg_target" "$TMPROOT/vjg.bak"
    printf '\n<!-- %s -->\n' "$_vjg_phrase" >>"$SANDBOX/$_vjg_target"
    total=$((total + 1))
    if _vjg_run >/dev/null 2>&1; then
      echo "  FAIL: validator jargon-guard: VACUOUS — '$_vjg_phrase' in $_vjg_target did not fail validate.py"
      fails=$((fails + 1))
    else
      echo "  PASS: validator jargon-guard: '$_vjg_phrase' in $_vjg_target → validate.py FAILS (non-vacuous)"
    fi
    cp "$TMPROOT/vjg.bak" "$SANDBOX/$_vjg_target"
  done
done
# (2) Removal restores green — the guard fails on the phrase, not permanently.
total=$((total + 1))
if _vjg_run >/dev/null 2>&1; then
  echo "  PASS: validator jargon-guard: removing the injected phrase restores a passing validate.py"
else
  echo "  FAIL: validator jargon-guard: tree not restored after injection"; fails=$((fails + 1))
fi

# --- validator no-rationale-guard self-test (v1.7.6) -------------------------
# Skill text is runtime-loaded and IS behaviour (prose-IS-behaviour), so a SKILL.md carries DIRECTIVES
# ONLY — the "why" lives in CHANGELOG.md / the non-runtime RATIONALE.md (PRINCIPLES.md, "Skills are
# directive-only"). v1.7.6 trimmed the accumulated rationale and added validate_no_rationale_in_skills
# to stop it creeping back one "observed failure:" at a time. Same teeth as the jargon guard above:
# proven by INJECTION, never by assertion. Runs entirely inside $SANDBOX; no `claude -p` — free and
# deterministic.
echo
echo "== validator no-rationale-guard self-test =="
_vnr_run() { ( cd "$SANDBOX" && python3 scripts/validate.py 2>&1 ); }
# (0) Baseline: the shipped skills carry zero rationale markers.
total=$((total + 1))
if _vnr_run >/dev/null 2>&1; then
  echo "  PASS: validator no-rationale-guard: shipped skills pass with zero rationale markers"
else
  echo "  FAIL: validator no-rationale-guard: shipped tree does NOT pass validate.py"; fails=$((fails + 1))
  _vnr_run | tail -8
fi
# (1) Non-vacuous, per marker, in a real runtime skill.
for _vnr_target in plugins/mango/skills/quick/SKILL.md plugins/mango/skills/analysis/SKILL.md; do
  for _vnr_phrase in '(Observed failure: a past run shipped a wrong thing.)' \
                     '(Field-observed: the gate was skipped once.)' \
                     'This rule exists because an earlier version got it wrong.' \
                     'Historically this was handled differently.'; do
    cp "$SANDBOX/$_vnr_target" "$TMPROOT/vnr.bak"
    printf '\n%s\n' "$_vnr_phrase" >>"$SANDBOX/$_vnr_target"
    total=$((total + 1))
    if _vnr_run >/dev/null 2>&1; then
      echo "  FAIL: validator no-rationale-guard: VACUOUS — '$_vnr_phrase' in $_vnr_target did not fail validate.py"
      fails=$((fails + 1))
    else
      echo "  PASS: validator no-rationale-guard: rationale in $_vnr_target → validate.py FAILS (non-vacuous)"
    fi
    cp "$TMPROOT/vnr.bak" "$SANDBOX/$_vnr_target"
  done
done
# (2) The why must not be pulled back onto the runtime path: a SKILL.md referencing RATIONALE.md fails.
cp "$SANDBOX/plugins/mango/skills/quick/SKILL.md" "$TMPROOT/vnr.bak"
printf '\nSee RATIONALE.md for the background.\n' >>"$SANDBOX/plugins/mango/skills/quick/SKILL.md"
total=$((total + 1))
if _vnr_run >/dev/null 2>&1; then
  echo "  FAIL: validator no-rationale-guard: VACUOUS — a SKILL.md referencing RATIONALE.md did not fail validate.py"
  fails=$((fails + 1))
else
  echo "  PASS: validator no-rationale-guard: a SKILL.md referencing RATIONALE.md → validate.py FAILS (why stays off the runtime path)"
fi
cp "$TMPROOT/vnr.bak" "$SANDBOX/plugins/mango/skills/quick/SKILL.md"
# (3) Removal restores green.
total=$((total + 1))
if _vnr_run >/dev/null 2>&1; then
  echo "  PASS: validator no-rationale-guard: removing the injected rationale restores a passing validate.py"
else
  echo "  FAIL: validator no-rationale-guard: tree not restored after injection"; fails=$((fails + 1))
fi

# --- envelope script suite (v1.11.0) -----------------------------------------
# The three envelope scripts (RUN CONTRACT / RECONCILE / BUDGET) carry their own stdlib-only test
# suite. It is dispatch-free and takes under a second, so the eval runs it too rather than leaving it
# to a separate command someone can forget. Every git test inside it builds its own throwaway repo
# under `tempfile`; the live checkout is never touched. Run against the SANDBOX clone, like every
# other validator self-test here.
echo
echo "== envelope script suite (RUN CONTRACT / RECONCILE / BUDGET) =="
total=$((total + 1))
_env_out="$( ( cd "$SANDBOX" && python3 tests/envelope/test_envelope.py 2>&1 ) || true )"
if grep -qE '^OK$' <<<"$_env_out"; then
  echo "  PASS: envelope suite green — $(printf '%s' "$_env_out" | grep -oE 'Ran [0-9]+ tests?' | tail -1)"
else
  echo "  FAIL: envelope suite is RED"
  fails=$((fails + 1))
  printf '%s\n' "$_env_out" | tail -20
fi

# eval-isolation-guard (v1.6.1 Fix 1): the SAFETY check — the whole point. Two counted assertions:
# (1) the guard is NON-VACUOUS — it catches an injected leak in a throwaway repo; (2) the LIVE checkout
# is untouched after the full eval. Neither ever mutates the live checkout.
echo
echo "== eval isolation guard =="

# (1) Non-vacuous: a throwaway repo with an injected leak (stray *PROJ-* branch + work doc + HEAD off
# main) MUST be caught. Built and destroyed here; the live checkout is never touched.
LEAKROOT="$(mktemp -d)"; LEAKREPO="$LEAKROOT/leak"
git init -q "$LEAKREPO"
git -C "$LEAKREPO" -c user.email=eval@example.com -c user.name=mango-eval commit -q --allow-empty -m init
git -C "$LEAKREPO" branch -q -M main
mkdir -p "$LEAKREPO/docs/tickets"
: >"$LEAKREPO/docs/tickets/PROJ-999.work.md"
git -C "$LEAKREPO" checkout -q -b feat/PROJ-999-leak
total=$((total + 1))
if assert_checkout_clean "$LEAKREPO" main >/dev/null 2>&1; then
  echo "  FAIL: eval-isolation-guard: guard is VACUOUS — missed an injected leak"
  fails=$((fails + 1))
else
  echo "  PASS: eval-isolation-guard: catches an injected leak (non-vacuous)"
fi

# (1b)-(1c) The PAIRED proof for the branch rule (v1.16.0). Making the expected branch a parameter
# could have quietly turned the HEAD check into a no-op, so both directions are asserted on a repo
# that is pristine but NOT on main: it must PASS when checked against its own branch, and must still
# FAIL when checked against a different one. Without the second half the first is indistinguishable
# from having deleted the rule.
git -C "$LEAKREPO" checkout -q main
git -C "$LEAKREPO" branch -q -D feat/PROJ-999-leak
rm -rf "$LEAKREPO/docs" 2>/dev/null || true
git -C "$LEAKREPO" checkout -q -b wip/topic
total=$((total + 1))
if assert_checkout_clean "$LEAKREPO" wip/topic >/dev/null 2>&1; then
  echo "  PASS: eval-isolation-guard: a clean checkout on a NON-main branch passes against its own branch (no false red off main)"
else
  echo "  FAIL: eval-isolation-guard: a clean non-main checkout was reported as leaked — the guard is a false red off main"
  fails=$((fails + 1))
fi
total=$((total + 1))
if assert_checkout_clean "$LEAKREPO" main >/dev/null 2>&1; then
  echo "  FAIL: eval-isolation-guard: the HEAD rule is VACUOUS — a checkout on the wrong branch passed"
  fails=$((fails + 1))
else
  echo "  PASS: eval-isolation-guard: the HEAD rule still bites — wrong branch is caught (non-vacuous)"
fi
# (1d)-(1e) Each rule proven ALONE, so no rule can hide behind another failing at the same time —
# the vacuity that let the stray-branch pattern be wrong through nine batches. HEAD is correct and no
# work doc exists in either case; only the named artifact is present.
git -C "$LEAKREPO" branch -q feat/PROJ-555-nested
total=$((total + 1))
if assert_checkout_clean "$LEAKREPO" wip/topic >/dev/null 2>&1; then
  echo "  FAIL: eval-isolation-guard: a stray NESTED fixture branch (feat/PROJ-*) is missed — the shape every fixture creates"
  fails=$((fails + 1))
else
  echo "  PASS: eval-isolation-guard: a stray NESTED fixture branch is caught on its own (non-vacuous)"
fi
git -C "$LEAKREPO" branch -q -D feat/PROJ-555-nested
mkdir -p "$LEAKREPO/docs/tickets"; : >"$LEAKREPO/docs/tickets/PROJ-555.work.md"
total=$((total + 1))
if assert_checkout_clean "$LEAKREPO" wip/topic >/dev/null 2>&1; then
  echo "  FAIL: eval-isolation-guard: a leaked work doc is missed when HEAD and branches are clean"
  fails=$((fails + 1))
else
  echo "  PASS: eval-isolation-guard: a leaked work doc is caught on its own (non-vacuous)"
fi
rm -rf "$LEAKROOT" 2>/dev/null || true

# (2) The whole point: after the full eval, the LIVE checkout is pristine. On a leak this prints the
# recovery commands and FAILS loudly, so a leak can never pass silently.
total=$((total + 1))
if assert_checkout_clean "$REPO_ROOT"; then
  echo "  PASS: eval-isolation-guard: live checkout untouched after full eval (HEAD on $EVAL_START_BRANCH, no stray *PROJ-* branch, no work doc)"
else
  echo "  FAIL: eval-isolation-guard: LIVE CHECKOUT MUTATED — a fixture leaked (recovery printed above)"
  fails=$((fails + 1))
fi

# (3) Per-worker isolation, the parallel dispatcher's half of the same invariant: every worker tree
# that was created was DISPOSED and is gone from disk. Non-vacuous first — the guard must catch an
# UNdisposed tree recorded in a synthetic ledger — then asserted against the real run's ledger.
_wl="$TMPROOT/worker-ledger-selftest"; _wt="$TMPROOT/worker-leak-tree"; mkdir -p "$_wt"
printf 'created\t%s\n' "$_wt" >"$_wl"
total=$((total + 1))
if assert_worker_trees_disposed "$_wl" >/dev/null 2>&1; then
  echo "  FAIL: worker-isolation-guard: guard is VACUOUS — missed an undisposed worker tree"
  fails=$((fails + 1))
else
  echo "  PASS: worker-isolation-guard: catches an undisposed worker tree (non-vacuous)"
fi
rm -rf "$_wt" "$_wl" 2>/dev/null || true
total=$((total + 1))
if assert_worker_trees_disposed "$WORKER_LEDGER"; then
  _wcreated="$(grep -c '^created' "$WORKER_LEDGER" 2>/dev/null || true)"; _wcreated="${_wcreated:-0}"
  echo "  PASS: worker-isolation-guard: all $_wcreated per-worker clone(s) disposed (no worker tree left on disk)"
else
  echo "  FAIL: worker-isolation-guard: a per-worker clone was not disposed (leaks printed above)"
  fails=$((fails + 1))
fi

# (4) Per-JOB isolation, the third face of the same invariant: a worker tree is shared by every job
# that worker claims, so "each job started from the provisioned baseline" needs its own teeth. Both
# guards are proven NON-VACUOUS first — one against a throwaway repo dirtied exactly the way a
# fixture dirties a tree, one against a synthetic residue ledger — then asserted against the real run.
_jd="$TMPROOT/job-start-selftest"; rm -rf "$_jd"; mkdir -p "$_jd"
git init -q "$_jd/repo"
git -C "$_jd/repo" -c user.email=eval@example.com -c user.name=mango-eval commit -q --allow-empty -m init
git -C "$_jd/repo" branch -q -M main
mkdir -p "$_jd/repo/docs/tickets"
printf 'x\n' >"$_jd/repo/docs/EVAL_RULES.md"
printf '%s\t%s\n' main "$(git -C "$_jd/repo" rev-parse HEAD)" >"$_jd/repo.base"
total=$((total + 1))
if ! assert_job_start_clean "$_jd/repo" >/dev/null 2>&1; then
  echo "  FAIL: job-isolation-guard: guard rejects an already-CLEAN tree (unusable)"
  fails=$((fails + 1))
else
  : >"$_jd/repo/docs/LESSONS.md"; : >"$_jd/repo/docs/tickets/PROJ-999.work.md"
  git -C "$_jd/repo" checkout -q -b feat/PROJ-999-residue
  if assert_job_start_clean "$_jd/repo" >/dev/null 2>&1; then
    echo "  FAIL: job-isolation-guard: guard is VACUOUS — missed a tree dirtied by an earlier job"
    fails=$((fails + 1))
  else
    echo "  PASS: job-isolation-guard: catches a tree dirtied by an earlier job (non-vacuous)"
  fi
fi
rm -rf "$_jd" 2>/dev/null || true

_jl="$TMPROOT/job-start-ledger-selftest"
printf 'residue\t1\tsynthetic-fixture\n' >"$_jl"
total=$((total + 1))
if assert_job_starts_clean "$_jl" >/dev/null 2>&1; then
  echo "  FAIL: job-isolation-guard: ledger guard is VACUOUS — missed a recorded residue row"
  fails=$((fails + 1))
else
  echo "  PASS: job-isolation-guard: catches a recorded residue row (non-vacuous)"
fi
rm -f "$_jl" 2>/dev/null || true

total=$((total + 1))
if assert_job_starts_clean "$JOB_START_LEDGER"; then
  _jclean="$(grep -c '^clean' "$JOB_START_LEDGER" 2>/dev/null || true)"; _jclean="${_jclean:-0}"
  echo "  PASS: job-isolation-guard: all $_jclean job(s) started from the provisioned baseline (no residue from an earlier job)"
else
  echo "  FAIL: job-isolation-guard: a job started on a tree an earlier job had dirtied (rows printed above)"
  fails=$((fails + 1))
fi

# --- Record what this run proved, and mint the cache it earned -----------------
# Read the cache tallies back out of their ledger files (they were written inside
# command-substitution subshells, so the shell variables never survived).
CACHE_HITS="$(tally_count cache-hits)"; FRESH_RUNS="$(tally_count fresh-runs)"

# Split this run's assertions into the ones attributable to a JOB and the ones that are the harness
# testing ITSELF (the dispatch-free self-tests above). A transcript is only worth caching if the
# harness that judged it was sound, so a self-test failure suppresses every mint.
COV_JOB_JUDGED="$([ -s "$COV_DIR/judged" ] && wc -l <"$COV_DIR/judged" | tr -d ' ' || echo 0)"
COV_JOB_FAILS="$(awk -F'\t' '$2=="FAIL" {n++} END {print n+0}' "$COV_DIR/judged" 2>/dev/null || echo 0)"
SELFTESTS=$(( total - COV_JOB_JUDGED )); [ "$SELFTESTS" -ge 0 ] || SELFTESTS=0
SELFTEST_FAILS=$(( fails - COV_JOB_FAILS )); [ "$SELFTEST_FAILS" -ge 0 ] || SELFTEST_FAILS=0

# Archive every transcript this run judged, and mint a cache entry for a fixture that passed ALL of
# its own assertions. The evidence for a mint is per fixture and exact:
#   * the fixture's own assertions all passed;
#   * a failed dispatch can never be green at all (assert_judgeable rejects an API-error or empty
#     transcript outright, so a no-run fails every one of its assertions);
#   * no assertion here reads across two transcripts, so a sibling failing tells you nothing.
# Still fail-safe to run: an unhashable fixture, a --no-cache run, or any doubt mints nothing.
_judged=0; _green=0; _minted=0
for _idx in $(seq 1 "$JOB_COUNT"); do
  [ -f "$JOBS_DIR/$_idx.meta" ] || continue
  IFS=$'\t' read -r _kind _name _ _ <"$JOBS_DIR/$_idx.meta"
  _p="$(cov_count "$COV_DIR/judged" "$_name" PASS)"
  _f="$(cov_count "$COV_DIR/judged" "$_name" FAIL)"
  # Not judged in this run → nothing to record. Silence is never a verdict.
  [ "$((_p + _f))" -gt 0 ] || continue
  _judged=$((_judged + 1))
  if [ "$_f" -eq 0 ]; then _v=green; _green=$((_green + 1)); else _v=red; fi
  if [ -s "$(transcript_path "$_name")" ]; then
    mkdir -p "$ARCHIVE_DIR/$RUN_ID" 2>/dev/null || true
    cp "$(transcript_path "$_name")" "$ARCHIVE_DIR/$RUN_ID/$_name.$_v.log" 2>/dev/null || true
  fi
  if [ "$_v" = green ] && [ "$_kind" = fixture ] && [ "$CACHE_ENABLED" -eq 1 ] &&
     [ "$SELFTEST_FAILS" -eq 0 ] && [ -s "$(transcript_path "$_name")" ]; then
    _h="$(skills_hash "$_name" 2>/dev/null || true)"
    if [ -n "$_h" ]; then
      cp "$(transcript_path "$_name")" "$CACHE_DIR/$_name.$_h.green" 2>/dev/null &&
        _minted=$((_minted + 1)) || true
    fi
  fi
done

# Stamp the archived run with the ruler that produced it. Without this the archive is a pile of
# transcripts with no way to tell which run.sh, plugin tree or CLI wrote them.
if [ -d "$ARCHIVE_DIR/$RUN_ID" ]; then
  printf 'run\t%s\nutc\t%s\nrunner_fp\t%s\nplugin_tree_fp\t%s\nmodel\t%s\ncli\t%s\nonly\t%s\n' \
    "$RUN_ID" "$RUN_UTC" "$RUNNER_FP" "$PLUGIN_TREE_FP" "$MODEL_SETTING" "$CLI_VERSION" "$ONLY" \
    >"$ARCHIVE_DIR/$RUN_ID/IDENTITY.tsv" 2>/dev/null || true
fi

# --- Per-job dispatch timing --------------------------------------------------
_tl="${CACHE_TALLY_DIR:-/nonexistent}/timing"
if [ -s "$_tl" ]; then
  echo
  echo "== per-job dispatch timing =="
  # The row limit lives in awk, not in `head`: `sort | head -25` leaves sort writing to a closed pipe,
  # and under `pipefail` a SIGPIPE'd sort makes this pipeline exit 141 — which `errexit` would turn
  # into a failed run at the very last step of a green run. awk reads all of its input.
  LC_ALL=C sort -t"$(printf '\t')" -k2,2nr "$_tl" |
    awk -F'\t' '{ printf "  %5ds  %-9s %s\n", $2, $3, $1 }'
fi

RUN_SECS=$(( ($(prof_now) - RUN_T0) / 1000000000 ))
echo
echo "EVAL dispatch: $JOB_COUNT job(s) across $WORKERS worker(s) in ${DISPATCH_SECS}s  (total run ${RUN_SECS}s)"
if [ "$CACHE_ENABLED" -eq 1 ]; then
  echo "EVAL cache: $CACHE_HITS cache-hit(s), $FRESH_RUNS fresh run(s)  [--no-cache forces a full fresh run]"
else
  echo "EVAL cache: disabled (--no-cache) — all $FRESH_RUNS fixture(s) ran fresh"
fi
echo "EVAL guard: $_green/$_judged fixture(s) judged green this run, $_minted cache entry(ies) minted"
echo "EVAL identity: runner ${RUNNER_FP:0:12}  plugin-tree ${PLUGIN_TREE_FP:0:12}  model $MODEL_SETTING  CLI $CLI_VERSION  run $RUN_ID"
# What this run does and does not say, printed every time so it cannot be over-read.
echo "EVAL scope: this is a per-skill smoke guard. It reports that these fixtures passed just now."
echo "            It is NOT a regression suite: no cross-skill detection, and RETIRE: is uncovered."
if [ -n "$ONLY" ]; then
  echo "EVAL: selection --only '$ONLY' — $skipped assertion(s) skipped (the unselected fixtures)."
fi
if [ "$fails" -gt 0 ]; then
  echo "EVAL: $((total - fails))/$total assertions pass — $fails assertion(s) failed"
  exit 1
fi
echo "EVAL: all assertions passed — $total/$total assertions pass"
