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
#   behavioural-drift — execute's design-conformance self-check (scope discipline on BOTH axes): an
#                     approach implemented differently from the approved Gate-2 bullet must be RECORDED
#                     as a deviation even when every touched file is in the change-list (clean file
#                     diff), not swept clean (behavioural-drift).
#   vague-requirement — Gate-1 falsifiability: a vaguely-worded AC must be pinned to a measurable or
#                     logged as a manual-check exclusion, and may NOT carry a bare ✅ (vague-requirement).
#   red-baseline    — baseline vocabulary against a GENUINELY red command (config.test_command points at
#                     a committed pre-existing failing check for this fixture only): analysis MEASURES
#                     baseline: red by running it (a failing-item detail present only in the command
#                     output, never the ticket, must appear), the DoD becomes delta-green, and the
#                     pre-existing failure is a recorded exclusion — neither blocks forever nor silently
#                     passes (red-baseline).
#   conditional-LGTM — a round-1 CHANGES REQUESTED with a conditional LGTM leads to a verify-only
#                     re-review (named-fix check + regression scan), not a full re-derivation, and the
#                     challenger is not re-run unless a fix changed scope (conditional-LGTM).
#   budget (v1.3)   — cost ledger is descriptive: a run records a per-phase/per-subagent cost block and
#                     finalise surfaces a summary, without auto-cutting anything (ledger-descriptive);
#                     with rtk: expect but RTK absent the run completes identically — nothing fails or
#                     changes a decision (rtk-degrade); with caveman enabled, critic output still carries
#                     path:line evidence and terse critic output is forbidden (caveman-critic-guard);
#                     enabling an optimizer lands in .harness.json token_optimizer as a recorded
#                     provisional decision, never a silent toggle, and budget installs nothing
#                     (optimizer-adoption-gated).
#   ledger truth (v1.4) — the ledger is emitted MECHANICALLY: one row per dispatch return (N dispatches
#                     → N rows), not narrated bookkeeping (ledger-auto-append); it measures subagent
#                     dispatch ONLY and refuses to fabricate a dispatch-vs-noise split, pointing at the
#                     optimizer's own analytics (rtk gain) for the noise side (ledger-dispatch-only-honesty);
#                     a conditional-LGTM verify-only round REUSES round-1 facts and re-runs only the
#                     affected proof — never a blanket suite re-run or re-derivation (verify-only-scoped);
#                     the Tokens column is labelled plainly (no false-precision "(out)" over an unsplit
#                     figure) (ledger-label); and with RTK present-but-unwired, budget PRINTS the wiring
#                     command + a "you run this, not mango" note and administers nothing (budget-rtk-wire-guidance).
#   v1.5            — the ledger's teeth: finalise runs a dispatch-count check and BLOCKS if the ledger has
#                     fewer rows than the run's dispatch count (a completeness check, like an unfilled matrix
#                     column), a complete ledger proceeds (ledger-gate); the conditional-LGTM verify-only round
#                     is main-loop-by-default — an in-scope round verifies in the main loop with NO re-dispatch,
#                     and a scope-changing fix is the only re-dispatch trigger (verify-only-main-loop); a standard
#                     applied at a gate with NO codified rule is SURFACED as an uncodified-standard item into
#                     codify's provisional→ratify flow, never silently enforced or ignored (uncodified-standard-nudge).
#   v1.6            — honest ledger + 2 small fixes: finalise's ledger gate is a CONTENT-completeness check — a
#                     ledger with all rows present but a BLANK token cell BLOCKS like an unfilled matrix column
#                     (injected, the first non-vacuous test of the teeth), a value-or-marker in every cell proceeds
#                     (ledger-content-gate); a dispatch retrieved by BLOCKING (no <usage> block) gets its tokens
#                     recovered OR its cell marked the explicit `unmeasured (blocking retrieval)`, never a silent
#                     blank or an invented number (usage-unmeasured-marker); the verify-only re-dispatch trigger has
#                     a docs/bookkeeping CARVE-OUT reusing finalise's staleness exemption set — a fix touching only
#                     exempt bookkeeping files (working doc / lessons_path / drift-list) stays main-loop, a non-exempt
#                     out-of-scope fix still re-dispatches (verify-only-bookkeeping-carveout); and the durable lesson
#                     must land on a SHARED/PUSHED ref (branch-push or a per-action "push bookkeeping"), not an
#                     orphaned local-only branch (finalise-lesson-pushed).
#   v1.6.1          — eval isolation + token: a post-run SAFETY guard asserts the LIVE checkout is
#                     untouched after the whole eval (HEAD on main, no stray *PROJ-* branch, no
#                     docs/tickets/*.work.md / docs/EVAL_RULES.md) and is proven NON-VACUOUS against an
#                     injected leak in a throwaway repo (eval-isolation-guard); mango emits only the
#                     CHANGED portion of an artifact into the response on a partial update ("ledger
#                     unchanged except row N") while the full artifact stays COMPLETE on disk and the
#                     v1.6 content-completeness gate still passes (artifact-delta-emission).
#   refine (v1.7.0) — the new Phase-0 refine phase + epic-path breakdown: a clear, convention-covered
#                     ticket → refine SELF-SKIPS ("0 unresolved product-decisions") and hands to analysis
#                     without fabricating a want-decision (refine-skip-clear-ticket); a raw ticket carrying
#                     both kinds has the how-decision (HOW) resolved-with-citation not asked and the
#                     want-decision (WANT) asked in want-language, the self-check catching a
#                     convention-answerable question as a how-decision (refine-classify-A-vs-B); a
#                     handed-back want-decision ("your call") is marked ASSUMED (awaiting ratification) and
#                     surfaced at a later gate, never silent-adopted, with the tripwire firing on a
#                     prior-decision reversal (refine-assumed-on-handback); refine stops at the solution
#                     DIRECTION (wrap vs rebuild) and does NOT pin a tool — that is analysis's job
#                     (refine-direction-not-tool); an epic input is DETECTED and routed to the epic path,
#                     breakdown emitting a counted ticket list + per-ticket INVEST self-check,
#                     human-approved before any ticket executes (refine-epic-detect-breakdown); the
#                     completeness-of-exposure backstop is the ticket-blind challenger as an
#                     exposure-checker with 1 dispatch that can surface an un-exposed decision — NOT a
#                     multi-advisor debate (refine-backstop-challenger).
#   v1.7.2          — epic-path exposure-checker + enumerated INVEST + design blast-radius trace-to-real-
#                     producers: on the EPIC path refine dispatches the SAME 1-dispatch ticket-blind
#                     exposure-checker (before breakdown, not a debate) that can surface an un-exposed
#                     decision — the epic path is not the one path that skips the backstop
#                     (epic-exposure-checker); breakdown's per-ticket INVEST self-check is ENUMERATED
#                     across all six letters (not a one-liner) and a ticket failing a letter (not Small)
#                     is flagged for re-split before ratification (breakdown-invest-enumerated); design's
#                     blast-radius traces to REAL producers/consumers — a shared-type change enumerates
#                     every test root + type factories + typecheck and a shallow src-only grep missing a
#                     factory root is a finding (design-blastradius-shared-type), a value threaded to a
#                     builder enumerates every builder call site not just the owning surface
#                     (design-blastradius-value-threading).
#   v1.7.1          — refine classifier tie-breaker + ASSUMED enforcement + analysis section coverage
#                     (buckets renamed to English want-decision/how-decision): an acceptance-BAR decision
#                     (what counts as a valid source anchor / a sourcing standard) is a WANT-decision by
#                     default even when it looks derivable — filed as want-decision/ASSUMED not a silent
#                     cited how-decision, and an UNCITED how-decision resolution is itself a finding
#                     (refine-acceptance-bar-is-want); a scope/consistency question answerable from a
#                     documented shared recipe is resolved-by-citation as a how-decision, NOT asked as an
#                     open want-decision (refine-consistency-is-how); a handed-back want-decision must
#                     carry the mandatory ASSUMED tag and be ratified only by an EXPLICIT next-gate confirm
#                     — settled prose is a finding (refine-assumed-on-handback, extended); and analysis's
#                     rule-compliance step ENUMERATES the applicable rulebook sections by change type — a
#                     migration makes the DB-conventions section mandatory (grants/soft-delete) and
#                     omitting an applicable section is a finding (analysis-section-coverage).
#   v1.7.3          — breakdown re-ratification + epic scaffold commit-before-child + INVEST force-re-split
#                     + eval transcript-cache: after a ratified split, an injected ticket-addition /
#                     ratified-decision reversal → breakdown surfaces the delta + requires explicit human
#                     re-approve, never a silent ride-in on a child Gate 1 (breakdown-reratify); an epic
#                     path commits the scaffold (stubs + BACKLOG) to a shared ref BEFORE any child branch,
#                     so a child edit reads as an edit of a committed file, not net-new
#                     (epic-scaffold-committed); an injected oversized ticket (bundles 4 deliverables →
#                     fails Small) is FLAGGED and DRIVEN to re-split before the gate while a right-sized
#                     control is not split (invest-force-resplit); and the runner's transcript-cache
#                     (keyed on fixture-id + skills-hash) reuses a fixture's last GREEN transcript when its
#                     skills are provably unchanged (cache-hit, no dispatch), runs fresh on any change or
#                     uncertainty (fail-safe to run), and --no-cache forces a full fresh run — proven by a
#                     cheap runner self-test (hash-match → skip; hash-change → run; --no-cache → all run).
#   v1.7.4          — review-phase git isolation + maturity labels + work_doc_mode guidance: a review
#                     subagent inspecting a branch uses ref-based git (git diff/show/log <base>..<branch>)
#                     or an isolated git worktree and MUST NOT run stateful git (checkout/switch/stash) in
#                     the SHARED working tree — the shared HEAD stays put and an injected shared-cwd
#                     checkout is flagged, not performed (review-git-isolation; same class as the v1.6.1
#                     eval-isolation fix, review surface). The maturity relabel (Stable/Experimental,
#                     zero v1-learning / n=1 / n=2 in shipped text) and the committed-stub → work_doc_mode
#                     separate guidance are locked at the validator level (scripts/validate.py).
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
CACHE_HITS=0; FRESH_RUNS=0; FRESH_FIXTURES=""

# The fixture→skill map keys the per-fixture skills-hash: a fixture whose mapped
# SKILL.md file(s) are unchanged can cache-hit. An UNMAPPED fixture hashes over ALL
# skills (fail-safe: any skill change invalidates it). PRINCIPLES.md, every agent
# brief, and every template are ALWAYS in the hash, so a change to any of them
# invalidates every cache — only the per-skill selectivity is the acceleration.
declare -A FIXTURE_SKILLS=(
  [full]="analysis" [lite]="analysis" [freeform]="analysis"
  [analysis-section-coverage]="analysis" [vague-requirement]="analysis"
  [red-baseline]="analysis" [uncodified-standard-nudge]="analysis"
  [design-layer]="design" [blast-radius]="design" [frontend-layer]="design"
  [surface-denominator]="design" [design-blastradius-shared-type]="design"
  [design-blastradius-value-threading]="design" [per-clause]="design execute"
  [no-runner-proof]="execute" [format-scope]="execute" [behavioural-drift]="execute"
  [challenger-unmet]="review" [rubric-hover]="review" [conditional-LGTM]="review"
  [review-git-isolation]="review"
  [caveman-critic-guard]="review" [verify-only-scoped]="review"
  [verify-only-main-loop]="review" [verify-only-bookkeeping-carveout]="review"
  [stale-workdoc-bump]="finalise" [stale-source-change]="finalise"
  [ledger-descriptive]="finalise" [ledger-dispatch-only-honesty]="finalise"
  [ledger-gate]="finalise" [ledger-content-gate]="finalise"
  [finalise-lesson-pushed]="finalise"
  [ledger-auto-append]="solve finalise" [ledger-label]="solve finalise"
  [usage-unmeasured-marker]="solve finalise"
  [rtk-degrade]="budget" [optimizer-adoption-gated]="budget"
  [budget-rtk-wire-guidance]="budget"
  [refine-skip-clear-ticket]="refine" [refine-classify-A-vs-B]="refine"
  [refine-acceptance-bar-is-want]="refine" [refine-consistency-is-how]="refine"
  [refine-assumed-on-handback]="refine" [refine-direction-not-tool]="refine"
  [refine-backstop-challenger]="refine" [epic-exposure-checker]="refine"
  [refine-epic-detect-breakdown]="refine breakdown"
  [epic-scaffold-committed]="refine breakdown"
  [breakdown-invest-enumerated]="breakdown" [breakdown-reratify]="breakdown"
  [invest-force-resplit]="breakdown"
)

# hash_files <file...> — sha256 over the concatenated files. Guards against a zero-arg call (which would
# make `cat` block on stdin): no args → empty hash → treated as a MISS (run fresh), never a hang.
hash_files() { [ "$#" -gt 0 ] || return 1; cat "$@" 2>/dev/null | sha256sum 2>/dev/null | awk '{print $1}'; }
skills_files() {  # <fixture-name> — the files whose contents key this fixture's cache
  local name="$1"                         # keep on its own line: a single `local a=.. b=${a}`
  local mapped="${FIXTURE_SKILLS[$name]:-}"  # evaluates b's RHS before a binds under `set -u`
  local s
  if [ -n "$mapped" ]; then
    for s in $mapped; do echo "$PLUGIN_SRC/skills/$s/SKILL.md"; done
  else
    ls "$PLUGIN_SRC"/skills/*/SKILL.md 2>/dev/null
  fi
  echo "$PLUGIN_SRC/PRINCIPLES.md"
  ls "$PLUGIN_SRC"/agents/*.md 2>/dev/null
  ls "$PLUGIN_SRC"/templates/*.md 2>/dev/null
  echo "$FIXTURES/$name.md"
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
if [ "$CACHE_ENABLED" -eq 1 ]; then
  mkdir -p "$CACHE_DIR"
  RUNNER_FP="$(hash_files "${BASH_SOURCE[0]}")"
  FP_FILE="$CACHE_DIR/.runner.fp"
  if [ ! -f "$FP_FILE" ] || [ "$(cat "$FP_FILE" 2>/dev/null)" != "$RUNNER_FP" ]; then
    rm -f "$CACHE_DIR"/*.green 2>/dev/null || true
    printf '%s' "$RUNNER_FP" >"$FP_FILE"
  fi
fi

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
# The sandbox harness, parameterized on test_command. Default is `true` (a green baseline). One
# fixture (red-baseline) points it at a committed pre-existing failing check so the baseline is
# GENUINELY red, then restores the green default — so the harness JSON stays in one place and only
# the one field that must vary does.
write_harness() {  # <test_command>
  cat >"$SANDBOX/.harness.json" <<HARNESS
{
  "rulebook_path": "docs/EVAL_RULES.md",
  "standards_path": "docs/EVAL_RULES.md",
  "repos": [{ "name": "app", "root": "." }],
  "test_command": "$1",
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
write_harness "true"

# A committed pre-existing failing check, so the red-baseline fixture has a GENUINELY red
# config.test_command to detect on a clean checkout (not a red baseline narrated in the ticket). The
# failing item names (pdf_snapshot_spec / snapshot drift / sub-pixel / "1 failed") appear ONLY here,
# never in the ticket text — so their presence in a transcript proves the model MEASURED the baseline
# by running the command rather than reading "red" off the ticket. Committed so it is part of the
# untouched checkout.
mkdir -p "$SANDBOX/tests/baseline"
cat >"$SANDBOX/tests/baseline/verify.sh" <<'VERIFY'
#!/bin/sh
# Simulated project verification command. On a CLEAN checkout it already fails on a pre-existing item
# OUTSIDE any single ticket's area — a genuinely RED baseline the analysis phase must DETECT by running
# it (never assume green, never narrate red from the ticket).
echo "PASS  spec/invoice/export_spec"
echo "FAIL  spec/legacy/pdf_snapshot_spec   — pre-existing snapshot drift (1 sub-pixel), unrelated to invoice export"
echo "1 failed, 1 passed"
exit 1
VERIFY
git -C "$SANDBOX" -c user.email=eval@example.com -c user.name=mango-eval add tests/baseline/verify.sh >/dev/null 2>&1
git -C "$SANDBOX" -c user.email=eval@example.com -c user.name=mango-eval commit -q -m "eval: pre-existing red baseline check (fixture scaffolding)" >/dev/null 2>&1

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
  local ticket transcript file="$TDIR/$name.log" hit
  # Cache-hit: skills-hash unchanged ⇒ reuse the last GREEN transcript, no dispatch.
  if hit="$(cache_get "$name")"; then
    { echo "== fixture: $name (CACHE-HIT — skills-hash unchanged, reused GREEN transcript; no claude -p dispatch) =="
      cat "$hit"; } >"$file"
    CACHE_HITS=$((CACHE_HITS + 1))
    echo "  cache-hit: $name (skills unchanged — reused green transcript, no dispatch)" >&2
    echo "$file"; return 0
  fi
  # Miss (changed skills / no cache / --no-cache / any uncertainty): run FRESH.
  ticket="$(cat "$FIXTURES/$name.md")"
  transcript="$(claude_run "$prompt"$'\n\nTicket:\n'"$ticket" 2>&1 || true)"
  { echo "== fixture: $name =="; echo "$transcript"; } >"$file"
  FRESH_RUNS=$((FRESH_RUNS + 1))
  FRESH_FIXTURES="$FRESH_FIXTURES $name"
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

# --- Post-run safety guard (v1.6.1, Fix 1) -----------------------------------
# Every fixture runs inside $SANDBOX, so the LIVE checkout must stay pristine. This
# ASSERTS it — belt-and-suspenders over the structural isolation. If a future edit
# ever broke the `cd "$SANDBOX"` discipline (or a fixture ran `execute` in the wrong
# cwd), a leak into the live checkout could otherwise pass silently.
#
# assert_checkout_clean <repo-dir> — echoes each leak it finds and returns non-zero
# on any; returns 0 iff <repo-dir> is pristine: HEAD on main, no stray *PROJ-*
# branch, no docs/tickets/*.work.md, no docs/EVAL_RULES.md. Parameterized on the dir
# so it is self-tested below on a THROWAWAY dirty repo — the guard's teeth are proven
# without ever risking the live checkout.
assert_checkout_clean() {
  local dir="$1" bad=0 head stray docs
  head="$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo UNKNOWN)"
  [ "$head" = "main" ] || { echo "    LEAK: HEAD is on '$head', not main"; bad=1; }
  stray="$(git -C "$dir" for-each-ref --format='%(refname:short)' 'refs/heads/*PROJ-*' 2>/dev/null || true)"
  [ -z "$stray" ] || { echo "    LEAK: stray fixture branch(es): $(echo $stray)"; bad=1; }
  docs="$(git -C "$dir" ls-files 'docs/tickets/*.work.md' 'docs/EVAL_RULES.md' 2>/dev/null || true)"
  docs="$docs $( (cd "$dir" && ls docs/tickets/*.work.md docs/EVAL_RULES.md) 2>/dev/null || true)"
  docs="$(echo "$docs" | tr ' ' '\n' | sort -u | grep -v '^$' || true)"
  [ -z "$docs" ] || { echo "    LEAK: eval artifact(s) in live checkout: $(echo $docs)"; bad=1; }
  if [ "$bad" -ne 0 ]; then
    echo "    RECOVERY: git switch main && git branch -D <stray> && rm -f docs/EVAL_RULES.md docs/tickets/*.work.md"
    echo "    (if a real commit stranded on the stray branch, cherry-pick it onto main FIRST)"
    return 1
  fi
  return 0
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

# analysis-section-coverage (v1.7.1 Fix 3): a change-list with a MIGRATION → analysis's rule-compliance
# step must ENUMERATE the applicable rulebook sections by change type and check each. Because the change
# type is a migration, the DB-conventions section is MANDATORY (grants/soft-delete). Omitting an
# applicable section is a FINDING (non-vacuous — the second assertion asks what happens if the section
# is silently dropped).
t="$(run_fixture analysis-section-coverage 'Run the mango analysis skill on this ticket, focusing on the rule-compliance section-coverage step. Enumerate the rulebook sections that apply to THIS change type and check each. State what you would do if an applicable section were silently omitted. Do not stop for my input.')"
# Decision-level: enumerates the DB-conventions section by change type (outcome) and checks grants/soft-delete (reasoning).
assert_all "section-coverage: enumerates the DB-conventions section for a migration" "$t" 'db[ -]conventions|database convention|db section|schema|migration' 'enumerat|applicable|change[ -]type|each section|RULE SECTIONS'
assert_contains "section-coverage: checks grants + soft-delete"       "$t" 'grant|permission|soft[ -]delete'
# Non-vacuous: silently omitting an applicable section is a finding.
assert_all "section-coverage: omitting an applicable section is a finding" "$t" 'omit|missing|silently|left unchecked|drop' 'finding|blocks?|not .{0,12}(allowed|silent)|flag|must .{0,12}(check|cover)'

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

# behavioural-drift (Fix v1.2): execute's design-conformance self-check. An approach implemented
# differently from the approved Gate-2 Approach bullet must be RECORDED as a deviation and surfaced to
# review — even when every touched file is inside the change-list (so the file-set sweep passes clean).
t="$(run_fixture behavioural-drift 'Run the mango execute skill on this ticket. Gate 2 is already cleared (the approved Approach bullet is quoted). Run the verification sweep on BOTH axes — the file set AND conformance to the approved design behaviour. State whether you record a design-conformance deviation, and why. Do not stop for my input.')"
# Decision-level: a deviation is recorded (outcome) BECAUSE the behaviour diverges from the approved
# design even though the file diff is clean (reasoning) — so a "swept clean" pass drops a token and fails.
assert_all "behavioural-drift: records a deviation on the behaviour axis" "$t" 'deviat' 'approved (design|approach|gate.?2|bullet)|behaviou?r'
assert_contains "behavioural-drift: acknowledges the clean file diff"     "$t" 'subset|diff ⊆|file.?set|change.?list|touched file|clean (file )?diff'
assert_contains "behavioural-drift: surfaces it to review / not clean"    "$t" 'review|not clean|surface|adjudicat'

# vague-requirement (Fix v1.2): Gate-1 falsifiability. A vaguely-worded AC ("loads quickly / feels
# responsive") must be pinned to a measurable or logged as a manual-check exclusion, and may not carry
# a bare ✅.
t="$(run_fixture vague-requirement 'Run the mango analysis skill on this ticket. Apply the Gate-1 falsifiability check in the AC-validation step to each acceptance value. Do not stop for my input; show the artifacts you would produce.')"
assert_contains "vague-requirement: flags AC-1 as not falsifiable" "$t" 'not falsifiable|not measurable|unmeasurable|vague|manual-check'
# Decision-level: it is pinned to a measurable OR logged as a manual-check exclusion (outcome), and it
# may not carry a bare ✅ (the guard) — so a silent ✅ drops a token and fails.
assert_all "vague-requirement: cannot carry a bare ✅"             "$t" 'falsifiable|measurable|manual-check' 'may not|cannot|not carry|flag|pin|Gate[ -]?1 question|exclusion'

# red-baseline (Fix v1.2, hardened v1.3.1): baseline vocabulary against a GENUINELY red command. The
# config.test_command is pointed at the committed pre-existing failing check for THIS fixture only, so
# analysis must DETECT baseline: red by RUNNING it (detect-not-assume). The ticket carries NO fabricated
# command output, so the model cannot pass by narrating "red" — the failing-item detail can only come
# from the command. Restore the green default immediately after this one run.
write_harness "sh tests/baseline/verify.sh"
t="$(run_fixture red-baseline 'Run the mango analysis skill on this ticket, focusing on the baseline-capture step: run config.test_command once on the untouched checkout, record the BASELINE from what you actually observe, state the Definition of Done, and say how any pre-existing failure is handled. Do not stop for my input.')"
write_harness "true"
# Decision-level: the baseline is classified red/flaky. Matches the label-adjacent form
# (`BASELINE: red`), the `is/=` form, and a red/flaky *result* classification (`Result: **red**`,
# `red, exit code 1`) — emphasis-agnostic over phrasing. Still outcome-bound: a green result never
# produces a red/flaky classification (the ticket carries no "red" and verify.sh's output has none).
assert_contains "red-baseline: records baseline red/flaky"  "$t" 'baseline[:*_ ]+(red|flaky)|baseline.*(is|=).*(red|flaky)|result:?[-* ]*(red|flaky)|(red|flaky)[,)* ]+exit'
# Measured, not narrated: a failing-item detail that exists ONLY in the command's output (never in the
# ticket) must appear — so a run that read "red" off the ticket without running the command still fails.
assert_contains "red-baseline: measured (observed failing item, not narrated)" "$t" 'pdf_snapshot_spec|snapshot drift|sub-?pixel|1 failed'
assert_contains "red-baseline: DoD is delta-green"          "$t" 'delta.?green|prove the delta|delta is green'
# Decision-level: the pre-existing failure is a recorded exclusion (outcome) that neither blocks nor
# silently passes (the guard).
assert_all "red-baseline: pre-existing failure is a recorded exclusion" "$t" 'exclusion|excluded|baseline exclusion' 'not a blocker|neither|not.{0,4}silent|does.{0,4}not.{0,4}block|not.{0,4}block|outside the change'

# conditional-LGTM (Fix v1.2): a round-1 CHANGES REQUESTED with a conditional LGTM leads to a
# verify-only re-review (confirm findings 1–N + regression scan), NOT a full re-derivation, and the
# ticket-blind challenger is not re-run unless a fix changed scope.
t="$(run_fixture conditional-LGTM 'Run the mango review re-review on this ticket. Round 1 already returned CHANGES REQUESTED with the two named findings shown, and the author has applied exactly those two fixes (no scope change). State the round-1 verdict form and exactly what round 2 does. Do not stop for my input.')"
assert_contains "conditional-LGTM: conditional LGTM offered"      "$t" 'conditional'
assert_contains "conditional-LGTM: verify-only re-review"         "$t" 'verify-only|verify only'
# Decision-level: round 2 confirms the named fixes + runs a regression scan (outcome) WITHOUT a full
# re-derivation / without re-running the challenger (the guard) — so a full re-review drops a token.
assert_all "conditional-LGTM: verify-only, not a full re-derivation" "$t" 'regression' 'not .*re-?deriv|without a full|challenger.*(once|not repeated|not re-?run)|not repeated'

# ledger-descriptive (v1.3): the Cost ledger is a descriptive, facts-only artifact. A completed run
# records per-phase/per-subagent token usage and finalise surfaces a one-line summary (total + top cost
# driver) WITHOUT the ledger deciding to cut anything.
t="$(run_fixture ledger-descriptive 'Run the mango finalise cost-ledger step for this completed full-tier ticket. Using the recorded per-dispatch token usage shown, produce the Cost ledger block and the one-line finalise summary (total + top cost driver). State plainly whether the ledger itself decides to cut anything. Do not stop for my input.')"
assert_contains "ledger: records a cost ledger"              "$t" 'cost ledger|ledger total'
# Decision-level: it is descriptive/facts-only (outcome) AND does not itself auto-cut a check/critic (guard).
assert_all "ledger: descriptive, does not auto-cut"          "$t" 'descriptive|facts[ -]only|facts only' 'not.*cut|never.*cut|(not|never) *\*{0,2}normative|does *\*{0,2}not\*{0,2}.{0,12}(cut|decide|drop)|human (call|can |decide|decision)|not itself|makes.*visible'
assert_contains "ledger: finalise summary (total + driver)"  "$t" 'top cost driver|cost driver|ledger total'

# rtk-degrade (v1.3): with token_optimizer.rtk: expect but RTK absent, the run completes identically —
# mango never fails, blocks, or changes a decision on RTK absence; only the token saving is lost.
t="$(run_fixture rtk-degrade 'Per the mango budget skill and PRINCIPLES, this project sets token_optimizer.rtk: expect but RTK is not installed. Explain exactly what happens to a mango run: does anything fail, block, or change a gate decision because RTK is absent? Be specific. Do not stop for my input.')"
assert_contains "rtk-degrade: runs identically"             "$t" 'identical|degrade clean|degrade cleanly|unchanged|same|no difference'
# Decision-level: about RTK (subject) AND nothing fails/blocks/changes a decision / only the saving is lost (guard).
assert_all "rtk-degrade: no failure / no changed decision"  "$t" 'rtk' 'not fail|never fail|does not.*(fail|block|chang)|no.*(fail|block|chang)|only the saving|degrade'

# caveman-critic-guard (v1.3): with caveman enabled, critic output (reviewer/challenger) must NOT be
# terse-compressed and must retain path:line evidence detail.
t="$(run_fixture caveman-critic-guard 'Run the mango review phase on this ticket with token_optimizer.caveman.enabled true. Per mango'\''s Caveman critic guardrail, state whether the reviewer/challenger output may be compressed to a terse form, and what evidence critic output must retain. Do not stop for my input.')"
assert_contains "caveman-guard: critic keeps evidence detail" "$t" 'path:line|evidence detail|full evidence'
# Decision-level: names caveman/compression/terse (subject) AND forbids it on critic output (guard).
assert_all "caveman-guard: forbids terse critic output"       "$t" 'caveman|compress|terse' 'never|not|forbid|must not|non-critic-only|retain'

# optimizer-adoption-gated (v1.3): enabling an optimizer is a recorded provisional decision in
# .harness.json token_optimizer — never a silent toggle — and budget installs nothing.
t="$(run_fixture optimizer-adoption-gated 'Run the mango budget skill for this project to consider adopting the detected Headroom optimizer. Per mango, state exactly how the adoption is recorded and where, whether it is silent, and whether budget installs anything. Do not stop for my input.')"
assert_contains "adoption-gated: recorded in token_optimizer" "$t" 'token_optimizer|\.harness\.json'
# Decision-level: recorded (outcome) AND provisional / not silent (guard).
assert_all "adoption-gated: recorded provisional, not silent"  "$t" 'recorded|token_optimizer' 'provisional|not.*silent|not a silent|ratif|human'
assert_contains "adoption-gated: never installs / no depend"   "$t" 'never install|not install|does not install|installs nothing|depend'

# ledger-auto-append (v1.4 Fix 1): the Cost ledger is emitted mechanically — one row per dispatch
# return, as a by-product of dispatching, NOT narrated bookkeeping the model must remember. A run that
# dispatched four subagents ends with four ledger rows.
t="$(run_fixture ledger-auto-append 'Run the mango solve/finalise Cost-ledger step for this run. Per mango, produce the Cost-ledger block the run ends with, state plainly what emits each row (the dispatch return, mechanically — not narrated bookkeeping), and how many rows a four-dispatch run carries. Do not stop for my input.')"
assert_contains "ledger-auto-append: records the ledger"         "$t" 'cost ledger|ledger total|ledger'
# Decision-level: rows are emitted per dispatch return (outcome) mechanically / as a by-product, not narrated (guard).
assert_all "ledger-auto-append: one row emitted per dispatch return" "$t" 'per dispatch|each dispatch|per .*return|row per dispatch' 'mechanical|by-?product|emitted|not narrat|not bookkeep'
assert_contains "ledger-auto-append: N dispatches → N rows"      "$t" '4 rows|four rows|4 ledger rows|four ledger rows|one row per (dispatch|return)'

# ledger-dispatch-only-honesty (v1.4 Fix 2): the ledger measures subagent dispatch ONLY; main-loop
# output noise is NOT measured by mango. The summary must declare dispatch-only, refuse to fabricate a
# dispatch-vs-noise split, and point at the optimizer's own analytics (rtk gain) for the noise side.
t="$(run_fixture ledger-dispatch-only-honesty 'Run the mango finalise Cost-ledger summary for this completed ticket, then answer the operator honestly per mango. Do not stop for my input.')"
assert_contains "dispatch-only: declares dispatch-only"          "$t" 'dispatch[ -]only|subagent dispatch only|dispatch-scoped'
# Decision-level: it does not fabricate a split (guard) over the noise/main-loop side (subject).
assert_all "dispatch-only: no fabricated dispatch-vs-noise split" "$t" 'not[ _*]*measured?|does[ _*]*not[ _*]*(measure|instrument)|not[ _*]*instrument|instrumentation artifact|artifact of only|no .*split|won.?t merge|would be a fiction' 'noise|main[- ]loop|dispatch.?vs.?noise'
assert_contains "dispatch-only: points at optimizer analytics"   "$t" 'rtk gain|optimizer.?s own|its own analytics|own savings|own analytics'

# verify-only-scoped (v1.4 Fix 3): a conditional-LGTM verify-only round must REUSE round-1's verified
# facts and re-run ONLY the proof affected by the named fixes — never blanket-re-run the full suite or
# re-derive requirements (no fix changed scope), so the cheap path is the default not a coin flip.
t="$(run_fixture verify-only-scoped 'Run the mango review re-review on this ticket. Round 1 was a conditional LGTM with the two named findings; the author applied exactly those two fixes, no scope change. State exactly what round 2 re-runs and what it reuses, and why. Do not stop for my input.')"
assert_contains "verify-only-scoped: reuses round-1 facts"       "$t" 'reuse|carr(y|ies).?forward|round.?1 (facts|verified)|already (verified|established)'
# Decision-level: re-runs only the affected proof (outcome) and does NOT blanket-re-run / re-derive (guard).
assert_all "verify-only-scoped: re-runs only the affected proof" "$t" 'only .*(proof|affected|named|fix)|scoped|affected proof' 'not .*(blanket|re-?deriv|full suite|entire suite)|without .*full|not re-?run the (full|entire)|does not re-?run'
assert_contains "verify-only-scoped: challenger not repeated"    "$t" 'challenger.*(not|once)|not repeated|not re-?run|re-?deriv.*(not|once)'

# ledger-label (v1.4 Fix 4): a dispatch return surfaces a single unsplit figure, so the Tokens column
# must be labelled plainly `Tokens` — never `(out)` / `(in / out)` over an unsplit metric (false precision).
t="$(run_fixture ledger-label 'Run the mango Cost-ledger step for this run and produce the ledger block and its column header. Label the token column to match what is actually measured; do not label it (out) or (in / out) over an unsplit metric, and say why. Do not stop for my input.')"
assert_contains "ledger-label: single unsplit figure"           "$t" 'single|unsplit|not split|no in.?/.?out|one figure'
# Decision-level: labelled Tokens (subject) and NOT labelled (out) over an unsplit metric (guard).
assert_all "ledger-label: column not labelled (out)"            "$t" 'tokens' 'not .*\(out\)|no .*\(out\)|without .*\(out\)|not.*in ?/ ?out|plainly|just .?tokens|not split|unsplit'

# budget-rtk-wire-guidance (v1.4 Fix 5): with RTK present-but-unwired, budget prints the exact wiring
# command + a "you run this yourself, not mango" note (it edits the global config), and administers
# nothing — detect + inform usefully, never execute.
t="$(run_fixture budget-rtk-wire-guidance 'Run the mango budget skill for this project: RTK is installed but not wired. Per mango, state exactly what budget outputs and what it does NOT do. Do not stop for my input.')"
assert_contains "rtk-wire: prints the wiring command"            "$t" 'rtk init|wire|wiring|hook setup|register.*hook'
# Decision-level: the user runs it (subject) and mango will not / it edits the global config (guard).
assert_all "rtk-wire: you run it, not mango"                     "$t" 'you (must |would |should )?run|user (must )?run|run (it|this|that) yourself|must run it' 'mango (will not|won.?t|does not|never)|not mango|global.*config'
assert_contains "rtk-wire: administers nothing"                  "$t" 'install(ed|s)?[ _*]*nothing|nothing[ _*]*install|never[ _*]*install|wires?[ _*]*nothing|nothing[ _*]*wired?|global config untouched|administers?[ _*]*nothing|did[ _*]*n.?t[ _*]*(install|wire|run|touch|edit)|does[ _*]*n.?t[ _*]*(install|wire|run|touch|edit)'

# ledger-gate (v1.5 Fix 1): the Cost ledger's teeth. finalise runs a dispatch-count check and REFUSES to
# proceed when the ledger has fewer rows than the run's dispatch count — an incomplete ledger blocks like
# an unfilled matrix column (a COMPLETENESS check, never content, never auto-cuts). A complete ledger proceeds.
t="$(run_fixture ledger-gate 'Run the mango finalise Cost-ledger dispatch-count gate for this run. Apply it: count the run'\''s subagent dispatches, compare to the Cost-ledger row count, and decide proceed-or-block. State your decision and why. Do not stop for my input.')"
assert_contains "ledger-gate: incomplete ledger blocks finalise" "$t" 'block|refuse|not proceed|cannot proceed|does not proceed|incomplete'
# Decision-level: gated on dispatch count (outcome) BECAUSE rows < dispatches (reasoning) — a proceed, or a
# block with no count reasoning, drops a token and fails.
assert_all "ledger-gate: gated on dispatch count, fewer rows than dispatches" "$t" 'dispatch[ -]count|dispatch' 'fewer|less than|2[[:space:]]*(of|/)[[:space:]]*4|missing|incomplete|only 2'
assert_contains "ledger-gate: blocks like an unfilled matrix column"          "$t" 'matrix column|unfilled|like a.*(gate|column)|gate-?block'
# Decision-level: it is a completeness check (subject) that never cuts content (guard).
assert_all "ledger-gate: completeness check, not content (never auto-cuts)"   "$t" 'complete' 'not.*content|never.*cut|not.*cut|descriptive|completeness'
# proceeds variant: a complete ledger (rows == dispatches) proceeds.
t="$(run_prompt ledger-gate-complete 'On the mango finalise dispatch-count gate: a run made 4 subagent dispatches and the Cost ledger has 4 rows (one per dispatch return). Per mango, does finalise proceed or block? Answer and say why.')"
assert_contains "ledger-gate-complete: complete ledger proceeds" "$t" 'proceed|passes|not block|does not block|complete'

# verify-only-main-loop (v1.5 Fix 2): the conditional-LGTM verify-only round is MAIN-LOOP-BY-DEFAULT. An
# in-scope round verifies in the main loop dispatching NO subagent (cost does not swing on operator choice);
# a scope-changing fix is the ONLY trigger for re-dispatching a reviewer/challenger.
t="$(run_fixture verify-only-main-loop 'Run the mango review verify-only re-review on this ticket. Round 1 was a conditional LGTM with two named findings; the author applied exactly those two in-scope fixes, no scope change. State exactly HOW round 2 verifies — in the main loop, or by re-dispatching a reviewer/challenger — and what WOULD trigger a re-dispatch. Do not stop for my input.')"
assert_contains "verify-only-main-loop: verifies in the main loop" "$t" 'main[ -]loop'
# Decision-level: main-loop (outcome) with NO re-dispatch of a subagent (guard) for in-scope fixes.
assert_all "verify-only-main-loop: no re-dispatch for in-scope fixes" "$t" 're-?dispatch|subagent|reviewer|challenger' 'no re-?dispatch|not re-?dispatch|dispatch(ing)? no|without .*(dispatch|subagent)|no subagent'
# Decision-level: a re-dispatch happens (subject) only on a scope change (guard).
assert_all "verify-only-main-loop: scope change is the only re-dispatch trigger" "$t" 're-?dispatch|full re-?review' 'scope chang|changed scope|outside the .*set|new surface|beyond the .*finding'

# uncodified-standard-nudge (v1.5 Fix 3): a standard applied at a gate with NO codified rule must be
# SURFACED as an uncodified-standard item into codify's provisional→ratify flow — never silently enforced
# and never silently ignored.
t="$(run_fixture uncodified-standard-nudge 'Run the mango analysis uncodified-standard check on this ticket. A standard is applied at a gate but the rule book has NO codified rule for it. Per mango, state what mango does — silently enforce it, silently ignore it, or surface it — and how the human ratifies it. Do not stop for my input.')"
assert_contains "uncodified-standard: surfaced, not silently applied" "$t" 'uncodified|surface'
# Decision-level: routed into codify's provisional→ratify flow (outcome) for the human to ratify (guard).
assert_all "uncodified-standard: routed to codify'\''s ratify flow" "$t" 'codify|ratif|provisional' 'ratif|provisional|human'
# Decision-level: NOT silently enforced or ignored (guard) — the human ratifies, mango does not author.
assert_all "uncodified-standard: not silently enforced or ignored" "$t" 'not silent|neither|does not silently|surface|nudge' 'enforc|apply|ignore|ratif|human|never author'

# ledger-content-gate (v1.6 Fix 2): the ledger's teeth become a CONTENT-completeness check. All four
# dispatch rows are PRESENT but one has a BLANK token cell — finalise must BLOCK (a blank token value is
# incomplete, exactly like an unfilled matrix column), not merely count rows. This is the test the vacuous
# row-count field runs could never provide — it INJECTS a short/blank ledger directly.
t="$(run_fixture ledger-content-gate 'Run the mango finalise Cost-ledger completeness gate for this run. All four dispatch rows are present but the first row'\''s token cell is blank. Apply the content-completeness check and decide proceed-or-block. State your decision and why. Do not stop for my input.')"
assert_contains "ledger-content-gate: blank token cell blocks finalise" "$t" 'block|refuse|not proceed|cannot proceed|does not proceed|incomplete'
# Decision-level: blocked BECAUSE a token value is blank/missing (content), not merely a row count.
assert_all "ledger-content-gate: blocks on a blank token value, not just row count" "$t" 'blank|empty|no.{0,6}(token|value)|missing.{0,6}(token|value)|absent' 'token|value|content|cell'
assert_contains "ledger-content-gate: blocks like an unfilled matrix column"        "$t" 'matrix column|unfilled|like a.*(gate|column)|gate-?block'
# Decision-level: still a completeness/descriptive check that never auto-cuts content.
assert_all "ledger-content-gate: completeness check, never auto-cuts"               "$t" 'complete' 'not.*(inspect|judg|rank|cut)|never.*cut|descriptive|completeness|presence'
# proceeds variant: every cell has a number OR the explicit unmeasured marker → proceeds.
t="$(run_prompt ledger-content-gate-marker 'On the mango finalise content-completeness gate: a run made 4 dispatches and the Cost ledger has 4 rows, each with a token count EXCEPT the blocked first dispatch, whose cell reads the explicit marker "unmeasured (blocking retrieval)". Per mango, does finalise proceed or block? Answer and say why.')"
assert_contains "ledger-content-gate-marker: value-or-marker in every cell proceeds" "$t" 'proceed|passes|not block|does not block'

# usage-unmeasured-marker (v1.6 Fix 1): a dispatch retrieved by BLOCKING carries no <usage> block. Its
# ledger row must show a REAL count (recovered via a usage-carrying path) or the explicit
# `unmeasured (blocking retrieval)` marker — NEVER a silent blank and never a fabricated number.
t="$(run_fixture usage-unmeasured-marker 'Run the mango Cost-ledger usage-surfacing step for this run. The first dispatch was retrieved by blocking and its return carried no <usage> block. Produce its ledger row and state what its token cell holds and why it may never be blank or invented. Do not stop for my input.')"
# Decision-level: the cell holds a real recovered count OR the explicit unmeasured marker (outcome)...
assert_contains "usage-marker: real count or explicit unmeasured marker" "$t" 'unmeasured|re-?quer|task-?notification|recover|real (count|number|token)'
# ...and it is never a silent blank / never fabricated (the guard).
assert_all "usage-marker: never a silent blank, never invented"          "$t" 'blank|invent|fabricat|made up|guess' 'never|not|no silent|without'
assert_contains "usage-marker: names the blocking-retrieval reason"       "$t" 'blocking retrieval|blocked dispatch|blocking|no .*usage|without .*usage'

# verify-only-bookkeeping-carveout (v1.6 Fix 3): the verify-only re-dispatch trigger has a docs/bookkeeping
# carve-out reusing finalise's staleness exemption set (working doc, lessons_path, rule-book drift-list). A
# verify-only fix touching ONLY exempt bookkeeping files stays MAIN-LOOP (no re-dispatch).
t="$(run_fixture verify-only-bookkeeping-carveout 'Run the mango review verify-only re-review on this ticket. Round 1 was a conditional LGTM with two named findings; the author applied those two fixes AND touched only exempt bookkeeping files (LESSONS.md + the rule-book drift-list). State whether round 2 stays main-loop or re-dispatches a reviewer/challenger, and why. Do not stop for my input.')"
assert_contains "carveout: stays main-loop" "$t" 'main[ -]loop'
# Decision-level: main-loop / no re-dispatch (outcome) BECAUSE the only extra files are exempt bookkeeping (reasoning).
assert_all "carveout: no re-dispatch for exempt-bookkeeping-only fix" "$t" 'no .{0,40}re-?dispatch|not .{0,40}re-?dispatch|dispatch(ing)? no|no subagent|without .*(dispatch|subagent)|stays[ _*]*main[ -]loop' 'bookkeeping|exempt|lessons|drift-?list|carve-?out|zero runtime'
# non-exempt variant: a fix touching a non-exempt out-of-scope file still triggers a full re-dispatch.
t="$(run_prompt carveout-nonexempt 'On the mango verify-only re-review docs/bookkeeping carve-out: after a conditional LGTM, the author fixes the named findings but ALSO edits a product SOURCE file OUTSIDE the approved change list (not an exempt bookkeeping file). Per mango, does round 2 stay main-loop or re-dispatch a full reviewer/challenger? Answer and say why.')"
assert_all "carveout-nonexempt: non-exempt out-of-scope fix re-dispatches" "$t" 're-?dispatch|full re-?review' 'scope|outside the .*(set|list)|non-exempt|not .*bookkeeping|product|source'

# finalise-lesson-pushed (v1.6 Fix 4): the durable lesson must land on a SHARED/PUSHED ref, not only a
# local branch a merge would delete. finalise folds the lesson into the branch-push OR takes an explicit
# "push bookkeeping" outward action under the same per-action approval.
t="$(run_fixture finalise-lesson-pushed 'Run the mango finalise durable-lesson step on this working doc. The lesson is committed on a local-only feature branch. State where it must end up and how finalise ensures it, and whether the push follows the normal per-action approval. Do not stop for my input.')"
# Decision-level: it must land on a shared/pushed ref (outcome) NOT only a local branch (the guard).
assert_all "lesson-pushed: lands on a shared/pushed ref, not local-only" "$t" 'shared ref|pushed|push' 'not .*local|local-?only|orphan|deleted|reach .*main|not only|shared'
assert_contains "lesson-pushed: via branch-push or a push-bookkeeping action" "$t" 'branch-?push|push bookkeeping|bookkeeping.*(action|commit|push)|fold'
assert_contains "lesson-pushed: under the normal per-action approval"        "$t" 'per-?action|separate approval|each .*approv|approval per'

# artifact-delta-emission (v1.6.1 Fix 2): on a PARTIAL update mid-run, mango emits only the CHANGED
# portion into the response (the new ledger row / the just-filled matrix cell) and REFERENCES the
# unchanged rest ("ledger unchanged except row N") — it does NOT reprint the whole artifact each time.
# The full artifact still lives COMPLETE on disk in the working doc (single source of truth), so the
# v1.6 content-completeness gate still passes. "Emit less into the response" ≠ "store less on disk".
t="$(run_prompt artifact-delta-emission 'In the mango lifecycle, a full-tier run makes several partial updates to the working doc (a new ledger row per dispatch, one matrix cell filled at a time). Per mango, when you report a partial update into the conversation, do you reprint the whole working doc / ledger / matrix each time, or only the changed portion — and what stays on disk? State exactly what goes into the response versus the working doc, and whether the content-completeness gate still passes. Do not stop for my input.')"
assert_contains "delta-emission: emits only the changed portion"        "$t" 'delta|changed portion|only the (new|changed)|unchanged except'
# Decision-level: deltas into the response (outcome) while the full artifact stays COMPLETE on disk (guard).
assert_all "delta-emission: full artifact stays complete on disk"       "$t" 'on disk|working doc|single source' 'complete|full|unchanged|not reprint|content|completeness'
assert_contains "delta-emission: content-completeness gate still passes" "$t" 'content|completeness|complete on disk|gate.{0,6}(still )?pass'

# --- refine phase (v1.7.0) ---------------------------------------------------
echo
echo "== refine phase (v1.7.0) =="

# refine-skip-clear-ticket: a clear, convention-covered ticket (the Nth item following an existing
# repeated pattern) → refine SELF-SKIPS (records "0 unresolved product-decisions") and hands to
# analysis, WITHOUT fabricating a want-decision question (no over-trigger). refine must not be a tax.
t="$(run_fixture refine-skip-clear-ticket 'Run the mango refine phase (Phase 0) on this raw request. Scan the project, TRY to expose the unresolved product-decisions, and act on the count you find. State your REFINE line and what you hand to the next phase. Do not stop for my input.')"
# Decision-level: skips (outcome) BECAUSE 0 unresolved / convention-covered / derivable (reasoning).
assert_all "refine-skip: skips because clear/convention-covered" "$t" 'skip|0 unresolved|0 want-decision' 'convention|derivable|pattern|cite|already|scan|nth|no genuine'
assert_contains "refine-skip: hands to analysis"                 "$t" 'analysis'
# No over-trigger: it does not fabricate a want-decision question.
assert_contains "refine-skip: no fabricated want-decision (no over-trigger)" "$t" 'no want-decision|0 want-decision|want-decision[[:space:]:=*_]*0|no .{0,20}(fabricat|question)|not .{0,6}over-?trigger|no over-?trigger|no genuine .{0,15}(want|want-decision)'

# refine-classify-A-vs-B: a raw ticket carrying BOTH kinds. The how-decision (HOW) is
# resolved-with-citation and NOT asked; the want-decision (WANT) is asked in want-language; the
# self-check catches a convention-answerable question as a how-decision rather than wrongly asking it
# as a want-decision.
t="$(run_fixture refine-classify-A-vs-B 'Run the mango refine phase (Phase 0) on this raw request. Classify EVERY product-decision as a want-decision vs a how-decision BEFORE asking anything, apply the self-check, then produce the refined-ticket artifacts. Do not stop for my input.')"
# Decision-level: how-decision resolved WITH a citation (outcome) and NOT asked (guard).
assert_all "refine-classify: how-decision resolved+cited, not asked" "$t" 'how-decision' 'cite|citation|convention|rulebook|:[0-9]|code' 'not ask|resolve|self-resolve|do ?n.?t ask|don.t ask|without asking'
# Decision-level: want-decision asked (outcome) in want-language (guard).
assert_all "refine-classify: want-decision asked in want-language"   "$t" 'want-decision' 'ask' 'want-language|want language|want|intent'
# The self-check catches a convention-answerable question as a how-decision (not a fabricated want-decision).
assert_all "refine-classify: self-check catches a convention-answerable as a how-decision" "$t" 'self-check|can .{0,25}(convention|code|rule).{0,15}answer' 'how-decision'

# refine-acceptance-bar-is-want (v1.7.1 Fix 1a): a decision about the acceptance BAR itself (what counts
# as a valid source anchor / a sourcing standard) is a WANT-decision by default, even when it looks
# derivable — the user owns the bar. refine files it as want-decision / ASSUMED, NOT a silent cited
# how-decision. Non-vacuous: settling it as an UNCITED how-decision is itself a finding.
t="$(run_fixture refine-acceptance-bar-is-want 'Run the mango refine phase (Phase 0) on this raw request. The load-bearing decision is what counts as a valid "verified source anchor" — a sourcing/acceptance standard. Classify it, apply the tie-breaker, and state how you file it. Then state what happens if refine were to settle that standard as an uncited how-decision. Do not stop for my input.')"
# Decision-level: acceptance-bar filed as a want-decision / ASSUMED (outcome) BECAUSE the user owns the bar (reasoning).
assert_all "refine-acceptance-bar: filed as want-decision/ASSUMED, not a silent how-decision" "$t" 'want-decision|assumed|acceptance[ -]bar|bar' 'user owns|owns the bar|ask|assumed|not .{0,20}how-decision|even .{0,12}derivable|want-decision by default'
# Non-vacuous: an UNCITED how-decision resolution is a finding.
assert_all "refine-acceptance-bar: uncited how-decision resolution is a finding" "$t" 'uncited|no .{0,8}(source|citation)|without .{0,8}(a )?citation|how-decision' 'finding|flag|mis-?classif|blocks?|not .{0,12}(allowed|silent)'

# refine-consistency-is-how (v1.7.1 Fix 1b): a scope/consistency question answerable from a DOCUMENTED
# shared recipe (apply to one consumer or all?) is a how-decision — resolve-by-citation and flag for
# ratify, NOT asked as an open want-decision.
t="$(run_fixture refine-consistency-is-how 'Run the mango refine phase (Phase 0) on this raw request. A documented shared table recipe backs several consumers. Decide whether the "one consumer or all consumers?" scope question is a want-decision or a how-decision, apply the tie-breaker, and state exactly how you handle it. Do not stop for my input.')"
# Decision-level: resolved as a how-decision by citation (outcome) BECAUSE the documented recipe answers it (reasoning).
assert_all "refine-consistency: resolved-by-citation as a how-decision" "$t" 'how-decision|resolve-by-citation|cite|citation' 'recipe|convention|documented|all consumers|shared'
# Guard: NOT asked as an open want-decision.
assert_all "refine-consistency: NOT asked as a want-decision" "$t" 'how-decision|not ask|resolve|cite' 'not .{0,20}(ask|want-decision|open want)|do ?n.?t ask|without asking|rather than .{0,18}ask|not a want-decision'

# refine-assumed-on-handback: user says "your call" on a want-decision → refine picks per recommendation
# but MUST mark ASSUMED (awaiting ratification), require an EXPLICIT next-gate confirm, NEVER silent-adopt
# and NEVER record it as settled prose; the tripwire fires when the recommendation would reverse a prior
# human decision.
t="$(run_fixture refine-assumed-on-handback 'Run the mango refine phase (Phase 0) on this raw request. The requester handed back a want-decision (WANT) ("your call"). State exactly how you record and surface that decision, whether the ASSUMED tag is mandatory, what ratifies it at the next gate, and whether you adopt it silently. Check the tripwire against the prior human decision. Do not stop for my input.')"
assert_contains "refine-assumed: marks ASSUMED (awaiting ratification)" "$t" 'assumed'
# Decision-level: ASSUMED tag is MANDATORY (outcome) — settled prose is a finding (guard).
assert_all "refine-assumed: ASSUMED tag mandatory, not settled prose" "$t" 'assumed|mandat|must' 'mandat|must|required|not .{0,20}(prose|settl)|never .{0,20}(prose|settl)|finding|not optional'
# Decision-level: ratified only by an EXPLICIT next-gate confirm (guard), not an incidental re-mention.
assert_all "refine-assumed: explicit next-gate confirm required" "$t" 'assumed|ratif|confirm' 'explicit|next gate|later gate|gate 1|design|not .{0,20}(re-?mention|happen|incidental|organic)'
# Decision-level: NOT silently adopted (guard).
assert_all "refine-assumed: not silently adopted"                        "$t" 'assumed|recommend' 'not[*_ ]{0,3}.{0,20}(silent|adopt|settl)|never[*_ ]{0,3}.{0,20}(silent|settl|adopt)|nor .{0,12}(silent|settl)|no silent|silent-?settle|rather than .{0,18}settl|0 silently|not automatically'
# Tripwire fires on a prior-decision reversal.
assert_all "refine-assumed: tripwire on prior-decision reversal"         "$t" 'tripwire|prior .{0,15}(human )?decision|revers' 'flag|assumed|surface|loud|never silent|not silent'

# refine-direction-not-tool: refine stops at the solution DIRECTION (wrap vs rebuild) a non-technical
# user can feel, and does NOT pin the specific tool/library — tool selection is analysis's job.
t="$(run_fixture refine-direction-not-tool 'Run the mango refine phase (Phase 0) on this raw request. Expose the solution DIRECTION the user can feel, and state whether you pin the specific tool/library or leave that to a later phase. Do not stop for my input.')"
assert_contains "refine-direction: stops at a direction (wrap vs rebuild)" "$t" 'wrap|rebuild|direction'
# Decision-level: does NOT pin a tool (outcome) — tool selection is analysis's job (reasoning).
assert_all "refine-direction: does not pin a tool"                        "$t" 'tool|library|engine' 'not .{0,14}(pin|pick|choose|select)|analysis.?s job|leave .{0,12}(tool|analysis)|defer .{0,12}tool|not .{0,10}pin.{0,10}tool|stops? at .{0,10}direction'
assert_contains "refine-direction: tool selection is analysis's job"      "$t" 'analysis'

# refine-epic-detect-breakdown: an epic input → refine detects the epic and routes to the epic path;
# breakdown emits a COUNTED ticket list with a per-ticket INVEST self-check, human-approved before any
# ticket executes.
t="$(run_fixture refine-epic-detect-breakdown 'Run the mango refine phase (Phase 0) on this raw request, then describe the path it routes to. If it is an epic, state what breakdown produces and the gate before any ticket executes. Do not stop for my input.')"
# Decision-level: detected an epic (outcome) and takes the epic path (reasoning).
assert_all "refine-epic: detects an epic, takes the epic path" "$t" 'epic' 'epic path|analysis\(epic\)|design\(epic\)|breakdown|multiple .{0,20}(deliverable|ticket)'
# breakdown emits a counted ticket list with a per-ticket INVEST self-check.
assert_all "refine-epic: breakdown emits a counted ticket list + INVEST" "$t" 'invest' 'ticket list|counted|ticket|breakdown'
# Human-approved (the human holds the gate) BEFORE any ticket executes.
assert_all "refine-epic: human-approved before any ticket executes"      "$t" 'human|approv|ratif|gate' 'before .{0,24}(execut|any ticket)|before any ticket|human .{0,10}(hold|ratif|approv)'

# refine-backstop-challenger: the completeness-of-exposure backstop is the ticket-blind challenger used
# as an exposure-checker with exactly 1 dispatch — it can surface an un-exposed decision, and it is NOT
# a multi-advisor Council / debate.
t="$(run_fixture refine-backstop-challenger 'Run the mango refine phase (Phase 0) on this raw request, focusing on the completeness-of-exposure backstop. State what runs it, how many dispatches it uses, what it can surface, and whether it is a multi-advisor debate. Do not stop for my input.')"
# Decision-level: exposure-checker = ticket-blind challenger, 1 dispatch (outcome).
assert_all "refine-backstop: exposure-checker is the ticket-blind challenger, 1 dispatch" "$t" 'exposure-checker|challenger' '1 dispatch|one dispatch|single dispatch|ticket-blind'
assert_contains "refine-backstop: can surface an un-exposed decision" "$t" 'un-?exposed|still .{0,15}expose|missed|surface'
# Decision-level: NOT a multi-advisor debate (guard) over the debate/council subject.
assert_all "refine-backstop: not a multi-advisor debate/council"     "$t" 'debate|council|advisor' 'not[*_ ]{0,4}.{0,16}(debate|council|advisor|panel)|never[*_ ]{0,4}.{0,16}(debate|council|panel)|no[*_ ]{0,4}(panel|vote|council|debate|cross)|one dispatch|1 dispatch|single dispatch|single-shot|not a[*_ ]{0,4}(council|debate)'

# --- v1.7.2 (epic exposure-checker + enumerated INVEST + design blast-radius) ----
echo
echo "== v1.7.2 (epic exposure-checker + enumerated INVEST + design blast-radius) =="

# epic-exposure-checker (v1.7.2 Fix A): on the epic path, refine dispatches the SAME 1-dispatch
# ticket-blind exposure-checker the ticket path uses — BEFORE breakdown — over the epic's exposed set.
# Exactly one dispatch, not a debate; it can surface an un-exposed decision (non-vacuous). The epic path
# is NOT the one path that skips the backstop.
t="$(run_fixture epic-exposure-checker 'Run the mango refine phase (Phase 0) on this raw request. It is an epic. State the path it routes to, and — before breakdown — whether refine dispatches an exposure-checker, how many dispatches, what runs it, and what it can surface. Do not stop for my input.')"
# Decision-level: detected an epic and takes the epic path.
assert_all "epic-exposure: detects an epic, takes the epic path" "$t" 'epic' 'epic path|analysis\(epic\)|design\(epic\)|breakdown|multiple .{0,20}(deliverable|ticket)'
# Exactly one ticket-blind exposure-checker dispatch, BEFORE breakdown.
assert_all "epic-exposure: one exposure-checker dispatch before breakdown" "$t" 'exposure-checker|ticket-blind challenger' '1 dispatch|one dispatch|single[ -].{0,24}dispatch|exactly[ _*]*(one|1)\b' 'before .{0,24}breakdown|before breakdown'
# Not a multi-advisor debate.
assert_contains "epic-exposure: one dispatch, not a debate"     "$t" 'not a.*(debate|council)|one dispatch|single dispatch|1 dispatch'
# Non-vacuous: it can surface an un-exposed decision.
assert_contains "epic-exposure: can surface an un-exposed decision" "$t" 'un-?exposed|still .{0,15}expose|who counts|internal user|surface'

# breakdown-invest-enumerated (v1.7.2 Fix B): each ticket in the breakdown carries a SIX-letter
# ENUMERATED INVEST check (not a one-line label). A ticket that fails a letter (here: not Small) is
# FLAGGED for re-split before ratification (non-vacuous — the failing letter must be caught).
t="$(run_fixture breakdown-invest-enumerated 'Run the mango breakdown phase on this epic (analysis(epic)/design(epic) already cleared). For each proposed ticket, emit the INVEST self-check. Show whether it is a six-letter enumerated check or a one-liner, and state what happens to a ticket that fails a letter. Do not stop for my input.')"
# Decision-level: the INVEST check is enumerated across the six letters, not a one-liner.
assert_all "breakdown-invest: enumerated six-letter INVEST per ticket" "$t" 'invest' 'enumerat|six letters?|all six|each letter|each of the six'
assert_contains "breakdown-invest: names the individual letters"       "$t" 'independent|negotiable|valuable|estimable|testable'
# Non-vacuous: a ticket failing "Small" is flagged for re-split before ratification.
assert_all "breakdown-invest: ticket failing Small is flagged for re-split" "$t" 'small' 'flag|finding|caught|re-?split|not .{0,10}(small|ratif)' 're-?split|split'

# design-blastradius-shared-type (v1.7.2 Fix C): a change touching a shared/generated TYPE with factories
# in a NON-src test root → the design blast-radius step enumerates EVERY test root + the type factories +
# runs typecheck, so the change-list is COMPLETE. A shallow name grep (src only) that misses the factory
# root is a FINDING (non-vacuous).
t="$(run_fixture design-blastradius-shared-type 'Run the mango design skill on this ticket. Assume Gate 1 cleared. Produce the Phase 2 smallest change-list and its mechanical test blast-radius sub-step for this shared-type change. State which test roots and factory/fixture patterns you enumerate, whether you run typecheck, and what happens if a shallow src-only grep missed a factory root. Do not stop for my input.')"
# Decision-level: enumerates every test root + the type factories (not a shallow one-string grep).
assert_all "blastradius-type: enumerates all test roots + factories" "$t" 'test root' 'factor|fixture|makeMoney|MoneyFactory'
assert_contains "blastradius-type: names the non-src roots (e2e/integration)" "$t" 'e2e|integration'
assert_contains "blastradius-type: runs typecheck in the estimate"           "$t" 'typecheck'
# Non-vacuous: a shallow-grep estimate missing the factory root is a finding.
assert_all "blastradius-type: shallow-grep miss is a finding" "$t" 'shallow|grep|miss|src.only|under-?scope' 'finding|flag|incomplete|under-?scope|not .{0,12}complete'

# design-blastradius-value-threading (v1.7.2 Fix C): a VALUE threaded to a downstream builder called from
# MULTIPLE sites → the blast-radius step enumerates EVERY builder call site, not just the surface that
# owns the feature (non-vacuous — it must name the sites beyond the owning page).
t="$(run_fixture design-blastradius-value-threading 'Run the mango design skill on this ticket. Assume Gate 1 cleared. Produce the Phase 2 change-list and its test blast-radius sub-step for this value-threading change. Enumerate every call site where the threaded value originates, and state whether you trace only the owning surface or all builder call sites. Do not stop for my input.')"
# Decision-level: enumerates all builder call sites (outcome).
assert_all "blastradius-value: enumerates all builder call sites" "$t" 'call site' 'all|every|each|multiple' 'builder|summaryBuilder'
# Non-vacuous: names the call sites beyond the owning page (they exist only in the fixture).
assert_contains "blastradius-value: names sites beyond the owning page" "$t" 'emailDigest|pushSummary|email digest|push summary'
# Guard: not just the owning surface/page.
assert_all "blastradius-value: not just the owning surface" "$t" 'not just|beyond|more than|all .{0,14}call site|every .{0,14}call site' 'owning|surface|page|reportPage'

# --- v1.7.3 (breakdown re-ratification + epic scaffold commit + INVEST force-re-split) ----
echo
echo "== v1.7.3 (re-ratification + scaffold-commit + force-re-split) =="

# breakdown-reratify (v1.7.3 Fix A): after the split-gate ratifies, an injected change to the ratified
# ticket list (a ticket ADDED, or a ratified DECISION reversed/re-pointed) must trigger a breakdown-level
# RE-RATIFICATION — surface the DELTA vs the ratified split as a counted artifact and require an explicit
# human RE-APPROVE — never let the change ride in silently on a child ticket's Gate 1 (non-vacuous: the
# silent ride-in is the failure the second assertion catches).
t="$(run_fixture breakdown-reratify 'Run the mango breakdown phase. The split-gate ALREADY ratified the ticket list. Now a 7th ticket is added AND a previously-ratified decision is reversed. State what breakdown does with that change: does it re-ratify at the breakdown level or let it ride in on a child ticket'\''s Gate 1? Show the delta and the gate. Do not stop for my input.')"
# Decision-level: breakdown RE-RATIFIES (outcome) by surfacing the delta for an explicit human re-approve (reasoning).
assert_all "breakdown-reratify: surfaces the delta + re-ratifies" "$t" 're-?ratif|re-?approv|re-?approve' 'delta|changed|added .{0,12}ticket|reversed|vs the ratified'
assert_contains "breakdown-reratify: explicit human re-approval at breakdown level" "$t" 'human|explicit|approve|gate'
# Non-vacuous: it does NOT let the change ride in on a child's Gate 1.
assert_all "breakdown-reratify: change does not ride in on a child Gate 1" "$t" 'gate 1|child ticket|child .{0,10}gate|ride' 'not .{0,20}(ride|silent|slip)|never .{0,20}(ride|silent|slip)|instead|re-?ratif|breakdown level|not on a child'

# invest-force-resplit (v1.7.3 Fix B): the INVEST "flag → re-split" ACT half. An injected oversized
# ticket that bundles four independent deliverables FAILS Small → breakdown must FLAG it AND DRIVE the
# re-split (split it into smaller tickets) BEFORE the split-gate ratifies — not merely note it. A
# right-sized control ticket is NOT split (non-vacuous).
t="$(run_fixture invest-force-resplit 'Run the mango breakdown phase on this epic. One proposed ticket bundles FOUR independent deliverables (fails INVEST Small); another is a single right-sized deliverable. Enumerate the six-letter INVEST self-check per ticket, then state what breakdown DOES with the oversized ticket (only note it, or actually re-split it before ratification) and what it does with the right-sized control. Do not stop for my input.')"
# Size-failure decision, emphasis-agnostic over wording (a run may say "oversized" / "bundles four
# deliverables" / "too big" rather than the literal INVEST letter "Small") — still outcome-bound: a run
# that never identifies the size problem matches none of these.
assert_contains "invest-force-resplit: flags the oversized ticket (fails Small)" "$t" 'small|oversized|too (big|large)|four .{0,16}deliverabl|bundl'
# Decision-level: it is FLAGGED (outcome) AND actually RE-SPLIT before ratification (the ACT half), not just noted.
assert_all "invest-force-resplit: flagged AND re-split before the gate" "$t" 'flag|finding|fails? .{0,8}small|not .{0,4}small' 're-?split|split .{0,20}(into|before)|split it' 'before .{0,16}ratif|before the (split-?)?gate|pre-?ratif'
# Non-vacuous control: the right-sized ticket is NOT split.
assert_all "invest-force-resplit: right-sized control is not split" "$t" 'right-?sized|control|single .{0,12}deliverable|passes .{0,10}(invest|small)' 'not .{0,8}split|no re-?split|kept|left .{0,8}(intact|as-?is)|not re-?split'

# epic-scaffold-committed (v1.7.3 Fix C): on the epic path, after the split ratifies, the epic scaffold
# (child-ticket stubs + BACKLOG/roadmap) must be COMMITTED to a shared ref BEFORE any child ticket starts
# its own branch — so a child editing a stub reads as an EDIT of a committed file, not net-new authorship
# (preserving the ticket-blind challenger's evidence).
t="$(run_fixture epic-scaffold-committed 'Run the mango epic-path breakdown. After the split ratifies, state exactly WHEN the epic scaffold (child-ticket stubs + the epic BACKLOG/roadmap) is committed relative to the first child ticket branching, and WHY that ordering matters for the ticket-blind challenger (net-new vs edit). Do not stop for my input.')"
# Decision-level: the scaffold is committed (outcome) BEFORE any child branches (reasoning).
assert_all "epic-scaffold: committed before any child branch" "$t" 'scaffold|stub|backlog' 'commit' 'before .{0,24}(child|branch)|before any child|prior to .{0,16}(child|branch)'
# Non-vacuous: a child edit of a committed stub reads as an EDIT, not net-new.
assert_all "epic-scaffold: a child edit reads as edit, not net-new" "$t" 'edit|committed file|retarget' 'net-?new|not net-?new|challenger|edit of a committed'

# --- v1.7.4 (review git-isolation + maturity + workdoc guidance) -------------
echo
echo "== v1.7.4 (review git-isolation) =="

# review-git-isolation (v1.7.4 Fix 1): a review subagent inspecting a branch must use read-only,
# ref-based git (git diff/show/log <base>..<branch>) OR an isolated git worktree, and MUST NOT run
# stateful git (checkout/switch/stash) in the SHARED working tree (the live checkout). The shared HEAD
# stays put; an injected shared-cwd `git checkout` is FLAGGED (non-vacuous), never performed, and the
# live checkout stays on the original branch. Same class as the v1.6.1 eval-isolation fix, review surface.
t="$(run_fixture review-git-isolation 'Run the mango review phase on this ticket. State exactly how a review subagent (reviewer/challenger) inspects the feature branch, whether it may run git checkout/switch/stash in the shared working tree, and where it runs the suite if it must. Then say what happens to the shared HEAD and what you would do if a subagent were about to run `git checkout main` in the shared checkout. Do not stop for my input.')"
# Decision-level: inspection is ref-based OR worktree-isolated (outcome + a branch/inspect token).
assert_all "review-git-isolation: ref-based or worktree-isolated inspection" "$t" 'ref-based|git (diff|show|log)|worktree' 'branch|diff|inspect|review'
# Decision-level: stateful git in the shared working tree is FORBIDDEN (guard) — names the ops.
assert_all "review-git-isolation: no stateful git in the shared working tree" "$t" 'checkout|switch|stash' 'not|never|must not|forbid|avoid|would ?n.?t|do ?n.?t'
# The shared HEAD / live checkout stays unchanged after review.
assert_contains "review-git-isolation: shared HEAD unchanged" "$t" 'unchanged|stays|untouched|same branch|still on|remain|not .{0,12}switch|does not .{0,12}(switch|change)'
# Non-vacuous: an injected shared-cwd `git checkout` is flagged/refused (not performed) AND the live
# checkout stays on the original branch.
assert_all "review-git-isolation: injected shared-cwd checkout flagged, checkout stays put (non-vacuous)" "$t" 'flag|refuse|not .{0,14}(run|perform|do)|never .{0,12}(run|checkout)|instead|worktree|isolat' 'stay|remain|original|not switch|still on|feat/'

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
if assert_checkout_clean "$LEAKREPO" >/dev/null 2>&1; then
  echo "  FAIL: eval-isolation-guard: guard is VACUOUS — missed an injected leak"
  fails=$((fails + 1))
else
  echo "  PASS: eval-isolation-guard: catches an injected leak (non-vacuous)"
fi
rm -rf "$LEAKROOT" 2>/dev/null || true

# (2) The whole point: after the full eval, the LIVE checkout is pristine. On a leak this prints the
# recovery commands and FAILS loudly, so a leak can never pass silently.
total=$((total + 1))
if assert_checkout_clean "$REPO_ROOT"; then
  echo "  PASS: eval-isolation-guard: live checkout untouched after full eval (HEAD on main, no stray *PROJ-* branch, no work doc)"
else
  echo "  FAIL: eval-isolation-guard: LIVE CHECKOUT MUTATED — a fixture leaked (recovery printed above)"
  fails=$((fails + 1))
fi

# Persist this run's FRESH transcripts as the new cached GREEN baseline — but only when the WHOLE suite
# passed (never cache a transcript from a red suite) and cache reads are enabled (skipped under
# --no-cache). A cache-hit fixture already holds a valid green entry under the current hash; only fresh
# runs need writing. This never touches the committed tree — the cache dir is git-ignored.
if [ "$CACHE_ENABLED" -eq 1 ] && [ "$fails" -eq 0 ]; then
  for _name in $FRESH_FIXTURES; do
    _h="$(skills_hash "$_name")"
    [ -n "$_h" ] && cp "$TDIR/$_name.log" "$CACHE_DIR/$_name.$_h.green" 2>/dev/null || true
  done
fi

echo
if [ "$CACHE_ENABLED" -eq 1 ]; then
  echo "EVAL cache: $CACHE_HITS cache-hit(s), $FRESH_RUNS fresh run(s)  [--no-cache forces a full fresh run]"
else
  echo "EVAL cache: disabled (--no-cache) — all $FRESH_RUNS fixture(s) ran fresh"
fi
if [ "$fails" -gt 0 ]; then
  echo "EVAL: $((total - fails))/$total assertions pass — $fails assertion(s) failed"
  exit 1
fi
echo "EVAL: all assertions passed — $total/$total assertions pass"
