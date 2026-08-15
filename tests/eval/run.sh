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
# --- How the runner works: PARALLEL DISPATCH over a TWO-PASS suite --------------
# The suite is 100% `claude -p` latency (harness overhead is ~0.03%), so wall-time
# comes from dispatching concurrently — not from cutting fixtures. `suite()` below
# therefore runs TWICE over the SAME code, so a prompt can never drift from the
# assertions that judge it:
#   pass 1  PHASE=collect — every run_fixture/run_prompt REGISTERS a dispatch job
#                           (name, prompt, and the .harness.json test_command in
#                           force at that point); every assert_* is a no-op.
#   dispatch                — the registered jobs run CONCURRENTLY across
#                           --workers N workers, each in its OWN throwaway clone.
#   pass 2  PHASE=assert  — every run_fixture/run_prompt resolves the transcript
#                           the dispatch produced; every assert_* judges it.
# Assertion OUTPUT stays in script order (the assert pass is sequential), so a
# parallel run reads exactly like a sequential one.
#
#   bash tests/eval/run.sh                   # default workers (safe), cache on
#   bash tests/eval/run.sh --workers 8       # milestone speed
#   bash tests/eval/run.sh --workers 1       # sequential — debugging
#   bash tests/eval/run.sh --only refine-    # dev loop: affected fixtures only (PARTIAL, never a milestone run)
#
# PER-WORKER ISOLATION IS MANDATORY, for two reasons that are structural, not
# stylistic: (a) fixtures that let `execute` branch and commit would race inside
# one shared clone, and (b) the red-baseline fixture repoints config.test_command,
# which under concurrency would flip .harness.json under other in-flight
# dispatches. Each worker gets its own clone AND writes its own per-JOB harness,
# so neither can happen; the worker tree is disposed after its last job and the
# disposal is a counted assertion, alongside the existing live-checkout guard.
# Concurrency is a SCHEDULING change only: same fixtures, same assertions, same counts.
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
#   v1.7.5          — validator false-green + worktree env-parity + gathered fixes: validate.py's
#                     zero-jargon grep is proven NON-VACUOUS by a free, dispatch-less self-test — a
#                     banned phrase (`v1 — …` / `enough to run and learn` / `n=1` / `v1-learning`)
#                     injected into a shipped operational file (including the repo-root README, which
#                     v1.7.4's scan scope omitted) makes validate.py FAIL, and removing it restores
#                     green (validator jargon-guard self-test); a review subagent that runs a suite in a
#                     FRESH worktree with no untracked env and sees a NEAR-TOTAL failure classifies it as
#                     an ENV-FAULT — never a finding or a regression — carries the env in (or runs in
#                     place at the reviewed SHA), while a partial targeted failure is still a real
#                     finding (worktree-env-fault); execute COMMITS the change-set before dispatching
#                     review and an empty base..branch range triggers the `git diff HEAD` +
#                     `git status --porcelain -uall` fallback instead of a false "no changes"
#                     (execute-commit-before-review); a committed scaffold stub routes to
#                     work_doc_mode `separate` at solve's auto-path (workdoc-solve-autopath); an epic
#                     ends at breakdown, so BREAKDOWN writes the epic's durable lesson to lessons_path
#                     with an `EPIC LESSON:` counting line (epic-lesson-capture); codify emits its drift
#                     count as the prefixed `DRIFT: <n> entries | <m> tickets` line rather than prose
#                     (codify-drift-count); and a 2-clause ratified want-decision becomes TWO matrix +
#                     proof rows at Gate 1, the injected single-row ✅ certification being flagged
#                     (multi-clause-want).
#   v1.9.0          — the LEARNING LOOP, end to end. One bundled lesson splits into FOUR atomic claims,
#                     each classified by type as a PROPOSAL the human confirms (lesson-claim-split).
#                     Advisory recall fires on the right key and only on it: type 1 on a matching SYMBOL
#                     and not on a non-matching one (recall-symbol-type1), type 5 by AREA while the
#                     symbol-keyed claim stays silent on a ticket naming no symbol (recall-area-type5),
#                     type 6 by the finding about to be re-raised, carrying its expiry and closing
#                     nothing (recall-type6-expiry), and a `retired:` claim is SKIPPED while its
#                     superseder surfaces, the record kept and nothing auto-retired
#                     (recall-retired-skipped). Dedup flags a twice-seen claim and lets a measured claim
#                     REPLACE an inferred one, retiring it without deleting it
#                     (recurrence-supersession). The decisive gate: the MOST-repeated claim is the FALSE
#                     one and is BLOCKED from promotion, as is a claim with no cheap check, with the
#                     gate sitting IN FRONT of the ratification gate (falsify-blocks-promotion) — and
#                     the same gate PASSES a recurring, still-true, cheaply-checkable claim, which is
#                     still not in effect until the human ratifies it (falsify-true-claim-promotes, the
#                     non-vacuous control). Promotion PROPOSES only: nothing is written before an
#                     explicit per-claim ratify, a type-3 skill-gap is a project SIGNAL that edits no
#                     mango skill, and a PROCESS heuristic goes to the project agent brief rather than
#                     the code rule book (promotion-human-gated). A ratified rule lands in
#                     rulebook_path, is never copied into CLAUDE.md, and is not done until doctor is
#                     green on the pointer init already wrote (promotion-rulebook-wiring). Every
#                     destination is inside the PROJECT repo, an unset key is surfaced rather than
#                     redirected, and nothing is carried home (loop-project-local).
#   v1.8.0          — PREMISE-FALSIFIED preflight + the runner's own parallel/assertion guards: a ticket
#                     whose referenced-as-EXISTING sources do not resolve in the checkout makes refine
#                     emit `PREMISE FALSIFIED` with the missing refs and STOP for the human BEFORE any
#                     archaeology — no rename hunt, no history reconstruction (premise-falsified); the
#                     same check must NOT fire when every named path is framed as TO BE CREATED, which
#                     would block every net-new ticket (premise-to-be-created, the negative control);
#                     plus two dispatch-free guards on the runner itself — the assertion-convention
#                     self-test (each widened token must match the correct wording that used to fail AND
#                     still miss the wrong behaviour) and the per-worker-isolation guard (every worker
#                     clone disposed, proven non-vacuous against an undisposed tree).
#   v1.7.6          — skills are directive-only: the rationale trim plus its permanent guard, proven
#                     NON-VACUOUS by a free, dispatch-less self-test — a rationale marker (an
#                     `(Observed failure: …)` / `(Field-observed: …)` war-story, an `exists because`
#                     justification, a `Historically …` note) injected into a runtime SKILL.md makes
#                     validate.py FAIL, a SKILL.md referencing RATIONALE.md also FAILS (the "why" may
#                     never return to the runtime path), and removal restores green (validator
#                     no-rationale-guard self-test). Behaviour is unchanged by the trim itself — every
#                     gate, count line, STOP condition and output format is untouched, which is why the
#                     existing fixtures above are the regression net and no new model fixture is needed.
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
skipped=0        # assertions not judged because --only filtered their dispatch out

# --- CLI -----------------------------------------------------------------------
#   --workers N  concurrent dispatch workers (default 4 — a safe value that is kind
#                to API rate limits; 8 is the measured milestone setting). N=1 is a
#                genuinely sequential run, kept for debugging a single transcript.
#   --only RE    dispatch only fixtures/scenarios whose name matches the regex RE,
#                and judge only those. A DEV-LOOP filter: it makes the run PARTIAL
#                (loudly reported, cache writes suppressed) and can never stand in
#                for a milestone run. CI passes no arguments, so CI is always full.
#   --no-cache   full fresh run (the milestone/release bar) — see the cache block.
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

# The fixture→skill map keys the per-fixture skills-hash: a fixture whose mapped
# SKILL.md file(s) are unchanged can cache-hit. An UNMAPPED fixture hashes over ALL
# skills (fail-safe: any skill change invalidates it). PRINCIPLES.md, every agent
# brief, and every template are ALWAYS in the hash, so a change to any of them
# invalidates every cache — only the per-skill selectivity is the acceleration.
# RATIONALE.md is deliberately NOT in the hash: no skill loads it, so it cannot
# change behaviour and must never invalidate a cache. Do not add it.
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
  [worktree-env-fault]="review" [execute-commit-before-review]="execute review"
  [workdoc-solve-autopath]="solve" [epic-lesson-capture]="breakdown"
  [codify-drift-count]="codify" [multi-clause-want]="analysis"
  [premise-falsified]="refine" [premise-to-be-created]="refine"
  [lesson-claim-split]="finalise" [recurrence-supersession]="finalise"
  [falsify-blocks-promotion]="finalise" [falsify-true-claim-promotes]="finalise"
  [promotion-human-gated]="finalise" [loop-project-local]="finalise"
  [promotion-rulebook-wiring]="finalise codify"
  [recall-symbol-type1]="refine" [recall-area-type5]="refine"
  [recall-type6-expiry]="refine" [recall-retired-skipped]="refine"
  [host-context-file-default]="init doctor" [host-context-file-agents]="init doctor"
  [recall-type2-handle]="refine" [recall-zero-no-busywork]="refine"
  [handle-unanswered-blocks]="design" [handle-does-not-apply-closes]="design"
  [recurring-t2-leaves-lessons]="finalise" [type5-stays-in-lessons]="finalise"
  [template-resolve-no-plugin-root]="finalise"
  [promote-two-lessons-one-rule]="promote" [promote-single-lesson-noop]="promote"
  [promote-idempotent]="promote"
  [ondemand-companion-read]="design" [ondemand-read-no-plugin-root]="review"
  [rule-section-by-handle]="analysis" [rule-section-handle-unanswered]="analysis"
  [rule-section-handle-na-closes]="analysis" [rule-section-provisional-no-block]="analysis"
  [quick-direct-recall]="quick" [claim-retired-promoted]="refine"
  [promote-offers-retirement]="promote" [plugin-root-newest-version]="finalise"
  [challenger-pr-body-refused]="review"
  [greenfield-full-run]="refine analysis" [greenfield-quick-direct]="quick"
  [greenfield-promote-zeros]="promote" [greenfield-recall-handles-none-match]="analysis"
)

# hash_files <file...> — sha256 over the concatenated files. Guards against a zero-arg call (which would
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
# $SANDBOX is the TEMPLATE/reference clone: the two validator self-tests run
# inside it, and every WORKER gets its own independent clone of the same shape
# (see provision_sandbox / the dispatcher) so concurrent dispatches share nothing.
TMPROOT="$(mktemp -d)"
SANDBOX="$TMPROOT/repo"
cleanup() { rm -rf "$TMPROOT" 2>/dev/null || true; }
trap cleanup EXIT
# The cache tally ledgers (see tally_add above) — outside the sandbox, gone with TMPROOT on exit.
CACHE_TALLY_DIR="$TMPROOT/tally"; mkdir -p "$CACHE_TALLY_DIR"

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
# The sandbox harness, parameterized on test_command. Default is `true` (a green baseline). One
# fixture (red-baseline) points it at a committed pre-existing failing check so the baseline is
# GENUINELY red — so the harness JSON stays in one place and only the one field that must vary does.
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
# worker's own clone at dispatch time. So `red-baseline` gets a genuinely red command without any
# shared mid-run mutation, and no "restore the default afterwards" ordering dependency survives.
JOB_TEST_COMMAND="true"
write_harness() { JOB_TEST_COMMAND="$1"; }

# A committed pre-existing failing check, so the red-baseline fixture has a GENUINELY red
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
# repo, the throwaway rule book, the green-default harness, and the committed red-baseline check.
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
}
provision_sandbox "$SANDBOX"
PLUGIN_DIR="$SANDBOX/plugins/mango"

# All fixtures run headless inside a throwaway clone against the SHIPPED skills
# (--plugin-dir), so the eval tests what the repo ships, not whatever the operator
# happens to have installed. Default headless permissions are used (no
# privilege-bypass flag): the assertions read the transcript of artifacts the
# skills produce/describe, and the isolated clone — not a permission flag — is what
# guarantees a fixture can never touch the live checkout.
claude_run() {  # <repo-dir> <prompt...>
  local repo="$1"; shift
  ( cd "$repo" && claude -p --plugin-dir "$repo/plugins/mango" "$@" )
}

# --- Job registry + parallel dispatcher ---------------------------------------
# The collect pass fills this registry; the dispatcher drains it. Every piece of cross-process
# state is a FILE, never a shell variable: workers are background subshells, exactly like the
# command-substitution subshells that once silently lost the cache tallies (v1.7.5 Fix 4).
JOBS_DIR="$TMPROOT/jobs";     mkdir -p "$JOBS_DIR"
CLAIMS_DIR="$TMPROOT/claims"; mkdir -p "$CLAIMS_DIR"
WORKER_LEDGER="$TMPROOT/worker-trees"; : >"$WORKER_LEDGER"
DONE_LEDGER="$TMPROOT/dispatched";     : >"$DONE_LEDGER"
JOB_COUNT=0
PHASE=collect        # collect | assert — see the two-pass note in the header

# Scheduling weights, derived from the fixture→skill map. Longest-first (LPT) ordering keeps a slow
# dispatch from being the last one to start. This is a HINT ONLY: it changes the ORDER jobs are
# claimed in, never which jobs run, what is asserted, or any count. A wrong weight costs seconds.
declare -A SKILL_WEIGHT=(
  [refine]=4 [analysis]=4 [design]=4 [breakdown]=3 [execute]=2
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
job_selected() { [ -z "$ONLY" ] && return 0; printf '%s' "$1" | grep -qE "$ONLY"; }

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

# assert_judgeable <label> <transcript-file> — is there a transcript to judge? Returns 0 when yes.
# Under --only, a filtered-out job has no transcript: its assertions are SKIPPED and counted as
# skipped (never silently passed, and the run is reported PARTIAL). With no --only there is no
# legitimate way for a transcript to be missing — that means a job was asserted but never
# registered, so it FAILS loudly rather than being mistaken for coverage.
assert_judgeable() {
  local label="$1" file="$2"
  [ -s "$file" ] && return 0
  if [ -n "$ONLY" ]; then
    skipped=$((skipped + 1))
    return 1
  fi
  total=$((total + 1)); fails=$((fails + 1))
  echo "  FAIL: $label (NO TRANSCRIPT — this assertion's dispatch was never registered)  [${file#$REPO_ROOT/}]"
  return 1
}

# assert_contains <label> <transcript-file> <regex>
# $2 is the path to the teed transcript file (returned by run_fixture/run_prompt), so every
# PASS/FAIL line can name the exact transcript it judged. A no-op during the collect pass.
assert_contains() {
  local label="$1" file="$2" regex="$3"
  local rel="${file#$REPO_ROOT/}"
  [ "$PHASE" = assert ] || return 0
  assert_judgeable "$label" "$file" || return 0
  total=$((total + 1))
  if grep -qiE "$regex" "$file"; then
    echo "  PASS: $label  [$rel]"
    prof_assert "$(basename "$file" .log)" PASS
  else
    echo "  FAIL: $label (missing /$regex/)  [$rel]"
    fails=$((fails + 1))
    prof_assert "$(basename "$file" .log)" FAIL
  fi
}

# assert_all <label> <transcript-file> <regex...> — passes iff EVERY regex matches the file.
# Use to encode a DECISION-level match (outcome + reasoning must both appear), so a correct
# behaviour passes under any wording while a wrong outcome — which drops one of the tokens —
# still fails.
assert_all() {
  local label="$1" file="$2"; shift 2
  local rel="${file#$REPO_ROOT/}" missing="" re
  [ "$PHASE" = assert ] || return 0
  assert_judgeable "$label" "$file" || return 0
  total=$((total + 1))
  for re in "$@"; do
    grep -qiE "$re" "$file" || missing="$missing /$re/"
  done
  if [ -z "$missing" ]; then
    echo "  PASS: $label  [$rel]"
    prof_assert "$(basename "$file" .log)" PASS
  else
    echo "  FAIL: $label (missing$missing)  [$rel]"
    fails=$((fails + 1))
    prof_assert "$(basename "$file" .log)" FAIL
  fi
}

# assert_absent <label> <transcript-file> <regex> — passes iff the regex does NOT match. For a
# NEGATIVE control, where a match IS the failure (a guard that must stay silent). Keep the regex
# specific to what a real firing emits, so a transcript merely DISCUSSING the guard cannot fail it.
assert_absent() {
  local label="$1" file="$2" regex="$3"
  local rel="${file#$REPO_ROOT/}"
  [ "$PHASE" = assert ] || return 0
  assert_judgeable "$label" "$file" || return 0
  total=$((total + 1))
  if grep -qiE "$regex" "$file"; then
    echo "  FAIL: $label (present, must be absent: /$regex/)  [$rel]"
    fails=$((fails + 1))
    prof_assert "$(basename "$file" .log)" FAIL
  else
    echo "  PASS: $label  [$rel]"
    prof_assert "$(basename "$file" .log)" PASS
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
RE_INVEST_LETTERS='i[*_]{0,2}ndependent|n[*_]{0,2}egotiable|v[*_]{0,2}aluable|e[*_]{0,2}stimable|t[*_]{0,2}estable'
RE_INVEST_SMALL='s[*_]{0,2}mall'
RE_NOT_SPLIT='not[*_ ]{1,6}.{0,8}(re-?)?split|no[*_ ]{1,4}(re-?)?split|kept|left[*_ ]{1,6}.{0,8}(intact|as-?is)|un-?split|untouched|carr(y|ied|ies)[*_ ]{1,6}.{0,14}(through|unchanged)|\bas-?is\b|zero letters? failed|(control|right-?sized)[^.]{0,60}(unchanged|not[*_ ]{1,6}split)|to the gate[*_ ]{1,6}unchanged'
RE_ZERO_WANTS='0[ _*]*want-decisions?|want-decisions?[ _*:=]*0|zero want-decisions?|no want-decisions? (asked|put|surfaced)'
RE_LAYER_SUBJECT='layer[-_* ]{0,4}(mis-?)?match|risk layer|proof layer|verification plan'
RE_LAYER_MISMATCH='❌|✗|layer[-_* ]{0,4}mis-?match|mis-?match(ed)?[-_* ]{0,4}(on|at|for|in|—|:)|layer[^.]{0,40}(mis-?match|does not match|not .{0,6}match|is not met|too low)|(proof|test)[^.]{0,40}below[^.]{0,20}(the )?(risk )?layer|below the .{0,12}(risk )?layer|clears? (none|no)\b|(proof|test)[^.]{0,40}(rejected|insufficient|inadequate|not (a )?(valid|sufficient))'
# `before` + a literal space again — a correct run writes "re-split it **before** the gate" / "*before*
# the split-gate", where the emphasis sits between the words.
RE_BEFORE_GATE='before[*_ ]{1,4}.{0,20}ratif|before[*_ ]{1,4}(the )?(split-?)?gate|pre-?ratif|pre-?gate'
# The verify-only negative is stated as a COST CONTRAST as often as a negation: "round 2 costs zero
# dispatches … one scoped proof re-run", "re-deriving them would re-pay for facts already proven".
RE_NO_BLANKET_RERUN='not[*_ ]{1,4}.*(blanket|re-?deriv|full suite|entire suite)|without[*_ ]{1,4}.*full|not[*_ ]{1,4}re-?run the (full|entire)|does[*_ ]{1,4}not[*_ ]{1,4}re-?run|no[*_ ]{1,4}(full|blanket|whole-?suite|entire)[^.]{0,24}(build|suite|run|re-?review|re-?deriv)|no[*_ ]{1,4}re-?deriv|zero[*_ ]{1,4}(subagent |critic )?dispatch|costs?[*_ ]{1,4}zero|re-?deriv(ing|e|ation)?[^.]{0,30}(would|not|never|no need|re-?pay)'
RE_BEFORE_CHILD='before[*_ ]{1,4}.{0,24}(child|branch)|before any child|prior to[*_ ]{1,4}.{0,20}(child|branch)|only then[^.]{0,40}(child|branch|cut)|(child|branch)[^.]{0,60}uncommitted|(commit|scaffold)[^.]{0,40}too late|last act[^.]{0,40}breakdown'

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

# --- The suite ----------------------------------------------------------------
# Everything below runs TWICE: once with PHASE=collect (registering dispatches) and once with
# PHASE=assert (judging their transcripts) — see the header. The body is intentionally NOT
# re-indented into the function: keeping every fixture line byte-identical to its pre-parallel form
# is what makes "this is a scheduling change, not a coverage change" reviewable in the diff.
suite() {

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
# Emphasis/glyph-agnostic (see RE_LAYER_*): the layer-match FAILURE is the outcome, and the `❌`
# may live in the work-doc verification table rather than the response text. Still outcome-bound —
# the mismatch token is required alongside the layer subject, so a layer-match ✅ matches neither.
assert_all "design: verification-plan layer-match ❌" "$t" "$RE_LAYER_SUBJECT" "$RE_LAYER_MISMATCH"
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
assert_all "frontend-layer: layer-match ❌"                 "$t" "$RE_LAYER_SUBJECT" "$RE_LAYER_MISMATCH"
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
# Widened over WORDING (v1.8.0, separator + word-order class): a correct run writes "what it does
# **not** do: no full requirement re-derivation … **no repeat of the ticket-blind challenger**".
assert_all "conditional-LGTM: verify-only, not a full re-derivation" "$t" 'regression' 'not[*_ ]{1,4}.*re-?deriv|no[*_ ]{1,4}.{0,24}re-?deriv|without a full|challenger.*(once|not repeated|not re-?run)|no[*_ ]{1,4}repeat|not repeated|(repeat|re-?run)[^.]{0,40}challenger'

# ledger-descriptive (v1.3): the Cost ledger is a descriptive, facts-only artifact. A completed run
# records per-phase/per-subagent token usage and finalise surfaces a one-line summary (total + top cost
# driver) WITHOUT the ledger deciding to cut anything.
t="$(run_fixture ledger-descriptive 'Run the mango finalise cost-ledger step for this completed full-tier ticket. Using the recorded per-dispatch token usage shown, produce the Cost ledger block and the one-line finalise summary (total + top cost driver). State plainly whether the ledger itself decides to cut anything. Do not stop for my input.')"
assert_contains "ledger: records a cost ledger"              "$t" 'cost ledger|ledger total'
# Decision-level: it is descriptive/facts-only (outcome) AND does not itself auto-cut a check/critic (guard).
# Widened over WORDING (v1.8.0): a correct run writes "it is descriptive and **cuts nothing**" and
# "only **you** can decide to trim" — the guard, stated positively about who decides.
assert_all "ledger: descriptive, does not auto-cut"          "$t" 'descriptive|facts[ -]only|facts only' 'not.*cut|never.*cut|(not|never) *\*{0,2}normative|does *\*{0,2}not\*{0,2}.{0,12}(cut|decide|drop)|human (call|can |decide|decision)|not itself|makes.*visible|cuts?[*_ ]{1,4}nothing|nothing is cut|only[*_ ]{1,4}you[^.]{0,20}decide|you[*_ ]{1,4}(can[*_ ]{1,4})?decide|surfaced for you'
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
# Widened over WORDING (v1.8.0, literal-word class): a correct run writes "when a subagent dispatch
# returns, **one row is appended** from that return's usage block" — no "per".
assert_all "ledger-auto-append: one row emitted per dispatch return" "$t" 'per dispatch|each dispatch|per .*return|row per dispatch|one row[^.]{0,40}(dispatch|return)|row is appended|appends? one row' 'mechanical|by-?product|emitted|not narrat|not bookkeep'
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
# Widened over WORDING (v1.8.0): a correct run states the negative as "**No** full build, no
# whole-suite run, no re-read" rather than "not …". Every added alternative still names the thing NOT
# done, so a round 2 that DOES re-derive or re-run the suite matches none of them.
assert_all "verify-only-scoped: re-runs only the affected proof" "$t" 'only .*(proof|affected|named|fix)|scoped|affected proof' "$RE_NO_BLANKET_RERUN"
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
# Widened over WORDING (v1.8.0): correct runs write "zero subagents dispatched" and "dispatch**es** no
# reviewer" — the old alternation matched only "dispatch no" / "no subagent". The outcome guard is
# unchanged: a round that re-dispatches a critic matches none of these.
assert_all "verify-only-main-loop: no re-dispatch for in-scope fixes" "$t" 're-?dispatch|subagent|reviewer|challenger' 'no re-?dispatch|not re-?dispatch|dispatch(es|ing|ed)? no|without .*(dispatch|subagent)|no subagent|zero subagents?|zero .{0,14}dispatch'
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
banner "== refine phase (v1.7.0) =="

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
# Widened over WORDING (v1.8.0): a correct run names the mechanism rather than the step — the
# tie-breaker, or refusing to "launder" a convention-answerable question into a want-decision.
assert_all "refine-classify: self-check catches a convention-answerable as a how-decision" "$t" 'self-check|can .{0,25}(convention|code|rule).{0,15}answer|tie-?break|launder' 'how-decision'

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
# The skill states this negative as a COUNT (`0 want-decisions asked`) as readily as a negation
# phrase; RE_ZERO_WANTS accepts either. Outcome-bound: a run that DID ask it emits a non-zero count
# and no negation, so it matches neither alternative.
assert_all "refine-consistency: NOT asked as a want-decision" "$t" 'how-decision|not ask|resolve|cite' "not .{0,20}(ask|want-decision|open want)|do ?n.?t ask|without asking|rather than .{0,18}ask|not a want-decision|$RE_ZERO_WANTS"

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
# Widened over WORDING ONLY (v1.7.5 Fix 4): the old alternation missed correct runs phrased "left to
# analysis" or "analysis’s job" (a typographic apostrophe is multi-byte, so `analysis.?s` could not match
# it). The outcome guard is UNCHANGED — the first regex still requires the tool/library subject, and every
# added alternative still asserts the tool is NOT pinned here. Nothing that pins a tool can now pass.
assert_all "refine-direction: does not pin a tool"                        "$t" 'tool|library|engine' 'not .{0,14}(pin|pick|choose|select)|analysis.{0,3}s job|(job|task|call|decision) (of|for) .{0,10}analysis|le(ave|ft|aving) .{0,16}(to|for) .{0,12}(analysis|a later phase|design)|leave .{0,12}(tool|analysis)|defer(red|s|ring)? .{0,16}(tool|to analysis|to a later|until analysis)|later phase|not .{0,10}pin.{0,10}tool|stops? at .{0,10}direction|out of scope for refine'
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
banner "== v1.7.2 (epic exposure-checker + enumerated INVEST + design blast-radius) =="

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
# The prompt asks for the six-letter check IN THE RESPONSE: a correct run may write the enumeration into
# the working doc and summarise in prose (`4 INVEST self-checks emitted (6 letters each)`), which is
# right behaviour but leaves no per-letter evidence to judge. Asking for the artifact itself keeps the
# letter assertions strict instead of widening them into a duplicate of the "enumerated" assertion.
t="$(run_fixture breakdown-invest-enumerated 'Run the mango breakdown phase on this epic (analysis(epic)/design(epic) already cleared). For each proposed ticket, emit the INVEST self-check IN YOUR RESPONSE — reproduce the per-letter check itself, naming each of the six letters, not only a summary or a count of it. Show whether it is a six-letter enumerated check or a one-liner, and state what happens to a ticket that fails a letter. Do not stop for my input.')"
# Decision-level: the INVEST check is enumerated across the six letters, not a one-liner.
assert_all "breakdown-invest: enumerated six-letter INVEST per ticket" "$t" 'invest' 'enumerat|six letters?|all six|each letter|each of the six'
assert_contains "breakdown-invest: names the individual letters"       "$t" "$RE_INVEST_LETTERS"
# Non-vacuous: a ticket failing "Small" is flagged for re-split before ratification.
assert_all "breakdown-invest: ticket failing Small is flagged for re-split" "$t" "$RE_INVEST_SMALL" 'flag|finding|caught|re-?split|not .{0,10}(small|ratif)' 're-?split|split'

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
banner "== v1.7.3 (re-ratification + scaffold-commit + force-re-split) =="

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
assert_contains "invest-force-resplit: flags the oversized ticket (fails Small)" "$t" "$RE_INVEST_SMALL|oversized|too (big|large)|four .{0,16}deliverabl|bundl"
# Decision-level: it is FLAGGED (outcome) AND actually RE-SPLIT before ratification (the ACT half), not just noted.
assert_all "invest-force-resplit: flagged AND re-split before the gate" "$t" "flag|finding|fails? .{0,8}$RE_INVEST_SMALL|not .{0,4}$RE_INVEST_SMALL" 're-?split|split .{0,20}(into|before)|split it' "$RE_BEFORE_GATE"
# Non-vacuous control: the right-sized ticket is NOT split.
# The control is reported "unsplit" / "untouched" / "carried through" as often as "not split";
# RE_NOT_SPLIT accepts all of them. Outcome-bound: a control that WAS split matches none.
assert_all "invest-force-resplit: right-sized control is not split" "$t" "right-?sized|control|single .{0,12}deliverable|passes .{0,10}(invest|$RE_INVEST_SMALL)" "$RE_NOT_SPLIT"

# epic-scaffold-committed (v1.7.3 Fix C): on the epic path, after the split ratifies, the epic scaffold
# (child-ticket stubs + BACKLOG/roadmap) must be COMMITTED to a shared ref BEFORE any child ticket starts
# its own branch — so a child editing a stub reads as an EDIT of a committed file, not net-new authorship
# (preserving the ticket-blind challenger's evidence).
t="$(run_fixture epic-scaffold-committed 'Run the mango epic-path breakdown. After the split ratifies, state exactly WHEN the epic scaffold (child-ticket stubs + the epic BACKLOG/roadmap) is committed relative to the first child ticket branching, and WHY that ordering matters for the ticket-blind challenger (net-new vs edit). Do not stop for my input.')"
# Decision-level: the scaffold is committed (outcome) BEFORE any child branches (reasoning).
# `before ` + a literal space could not match the correct `**before** the first child ticket`;
# RE_BEFORE_CHILD tolerates the emphasis. The ordering outcome is unchanged.
assert_all "epic-scaffold: committed before any child branch" "$t" 'scaffold|stub|backlog' 'commit' "$RE_BEFORE_CHILD"
# Non-vacuous: a child edit of a committed stub reads as an EDIT, not net-new.
assert_all "epic-scaffold: a child edit reads as edit, not net-new" "$t" 'edit|committed file|retarget' 'net-?new|not net-?new|challenger|edit of a committed'

# --- v1.7.4 (review git-isolation + maturity + workdoc guidance) -------------
banner "== v1.7.4 (review git-isolation) =="

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

# --- v1.7.5 (validator false-green + worktree env-parity + gathered fixes) ----

# worktree-env-fault (v1.7.5 Fix 2): a review subagent ran the suite inside a FRESH worktree with no
# untracked env (.env / local config) and got a NEAR-TOTAL failure (12/12). That is an ENVIRONMENT FAULT,
# not a review finding and not a regression — carry the untracked env in (or run read-only in place at
# the reviewed SHA) and re-run. Non-vacuous: the guard must NOT swallow a partial, targeted failure.
t="$(run_fixture worktree-env-fault 'Run the mango review phase on this branch. Classify the suite result reported below, state whether it becomes a review finding or a regression, and state what you do before re-running. Do not stop for my input.')"
# Decision-level: classified as an ENV fault (outcome) caused by missing untracked files (reasoning).
assert_all "worktree-env-fault: near-total worktree fail is an environment fault" "$t" 'env[a-z]*[ -]?fault|environment(al)? (fault|issue|problem|failure|cause)|not a (code|real) (regression|finding)' 'untracked|\.env|missing .{0,20}(env|config)|environment parity|env[ -]parity'
# NOT reported as a review finding / regression.
assert_all "worktree-env-fault: not reported as a finding or regression" "$t" 'finding|regression' 'not .{0,24}(a )?(review )?(finding|regression)|never .{0,20}(finding|regression)|do(es)? not .{0,20}(report|count|block)|rather than .{0,16}(report|finding)'
# The remedy: carry the untracked env into the worktree, OR run read-only in place at the reviewed SHA.
assert_all "worktree-env-fault: carry the env in, or run in place at the reviewed SHA" "$t" 'copy|carry|bring|provide|populate|in place|already at' '\.env|untracked|local config|reviewed sha|in place'
# Non-vacuous: a PARTIAL, targeted failure inside the blast radius is still a real finding — the
# reclassification must not become a blanket suppressor.
assert_all "worktree-env-fault: a partial targeted failure is STILL a finding (non-vacuous)" "$t" 'partial|targeted|blast radius|specific|individual' 'still .{0,20}(a )?(real )?(finding|regression|counts|report)|would be .{0,16}(a )?finding|genuine|real finding|is .{0,10}reportable'

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

# workdoc-solve-autopath (v1.7.5 Fix 3a): a committed scaffold stub routes to work_doc_mode `separate`
# at solve's auto-path — auto does NOT mean "always embed into the local file".
t="$(run_fixture workdoc-solve-autopath 'Run the mango solve orchestrator preflight on this ticket. State which working-doc placement you select under work_doc_mode auto and why, and where you record it. Do not stop for my input.')"
# Decision-level: chooses `separate` (outcome) because the stub is committed/tracked (reasoning).
assert_all "workdoc-solve-autopath: committed stub → separate working doc" "$t" 'separate|\.work\.md' 'committed|tracked|stub|scaffold'
assert_all "workdoc-solve-autopath: explains the committed-tracked-file fragility" "$t" 'uncommitted|tracked|fragile|git[ -]state|dirty' 'embed|inside .{0,20}(the )?(committed|tracked|stub)|working doc'
assert_contains "workdoc-solve-autopath: records the resolved mode"                "$t" 'session status|record|work_doc_mode'

# epic-lesson-capture (v1.7.5 Fix 3c): an epic ends at breakdown and never reaches finalise, so
# BREAKDOWN owns writing the epic's durable lesson to config.lessons_path at ratification/close-out.
t="$(run_fixture epic-lesson-capture 'Run the mango breakdown phase through its ratification and close-out on this epic. State who captures the epic durable lesson, when, where it is written, and what it contains. Emit the counted artifact. Do not stop for my input.')"
# Decision-level: a durable lesson IS written (outcome) to lessons_path (reasoning).
assert_all "epic-lesson-capture: durable lesson written to lessons_path" "$t" 'lesson' 'lessons_path|LESSONS|durable lesson'
# breakdown owns it because the epic never reaches finalise.
assert_all "epic-lesson-capture: breakdown owns it (the epic never reaches finalise)" "$t" 'breakdown|ratif|close[ -]out' 'never .{0,24}finalise|does not .{0,20}(reach|run) .{0,12}finalise|ends at .{0,16}breakdown|no owner|own(s|er)'
# The counted artifact proving it happened.
assert_contains "epic-lesson-capture: emits the EPIC LESSON counting line" "$t" 'EPIC LESSON:|lesson\(s\) written'
# Content: the split rationale + the overlap/boundary rulings.
assert_all "epic-lesson-capture: records the split rationale + boundary rulings" "$t" 'rationale|why|reason' 'overlap|boundary|ruling|re-?split'

# codify-drift-count (v1.7.5 Fix 3d): the drift count is a PREFIXED COUNTING LINE (`DRIFT: <n> entries |
# <m> tickets`), matching REFINE:/BREAKDOWN:, not fudgeable prose. The list holds 5 entries / 2 tickets.
# The third assertion judges the counted-line-vs-prose CONTRAST, which only exists in the response if the
# prompt asks for it; a correct run otherwise just emits the line (proven by assertions 1 and 2) and says
# nothing about prose. Asking keeps assertion 3 strict and distinct instead of collapsing it into 1 and 2.
t="$(run_fixture codify-drift-count 'Run the mango codify skill on this drift-list step and emit its output exactly as codify specifies, including the counting line. Then state where each number came from, and whether a narrated prose count would be acceptable in its place. Do not stop for my input.')"
assert_contains "codify-drift-count: emits the DRIFT counting line"   "$t" 'DRIFT:'
# Decision-level: the count is taken FROM THE LIST (5 entries, 2 tickets), not narrated.
assert_all "codify-drift-count: counts 5 entries / 2 tickets from the list" "$t" '5[[:space:]*_]*(entries|entr|drift|file)|entries[[:space:]*_|]*5' '2[[:space:]*_]*(tickets|ticket)|tickets[[:space:]*_|]*2'
# Non-vacuous: a prose count is rejected in favour of the counted line (the near-miss this removes).
# Widened over WORDING (v1.8.0): a correct run EMITS the prefixed counted line and says the numbers
# were counted from the list, without also discussing "counting lines" in the abstract. Emitting the
# artifact is stronger evidence than narrating the rule, so the emitted `DRIFT: <n>` line is accepted
# as the subject; the second regex still requires the count to be derived from the list, not narrated.
assert_all "codify-drift-count: a prose count is not acceptable (non-vacuous)" "$t" 'prose|narrat|about six|counted line|counting line|counted artifact|DRIFT:[[:space:]*_]*[0-9]' 'count(ed)? from the (list|table|rows?|above)|not .{0,20}prose|resist|fudg|mechanical|prefixed'

# multi-clause-want (v1.7.5 Fix 3e): a ratified want-decision with TWO clauses ("place the rows under the
# summary" AND "tappable through to detail") must become TWO matrix rows + TWO proof rows at Gate 1 — the
# injected single-row ✅ certification is FLAGGED (non-vacuous), not accepted.
t="$(run_fixture multi-clause-want 'Run the mango analysis skill on this ticket. Decompose the ratified want-decision into the requirements matrix and the verification plan, state how many rows it produces and why, and judge the single-row certification shown in the ticket. Do not stop for my input.')"
# Decision-level: the want-decision has TWO clauses and gets one row PER CLAUSE (outcome + reasoning).
assert_all "multi-clause-want: two clauses → one row per clause" "$t" 'two|2[[:space:]*_]*(rows|clause)|per clause|each clause' 'clause'
assert_all "multi-clause-want: both clauses are named (placement + tappable)" "$t" 'placement|under the summary|position' 'tappable|tap|navigat|detail view'
# Non-vacuous: the injected single-row certification is REJECTED / flagged as a finding.
assert_all "multi-clause-want: the injected 1-row certification is flagged (non-vacuous)" "$t" 'single[ -]row|one row|R-1|certif' 'not acceptable|unacceptable|reject|finding|insufficient|blocks?|must .{0,16}split|cannot .{0,16}(stand|certif)|flag'

# --- v1.8.0 (PREMISE-FALSIFIED preflight) ------------------------------------
banner "== v1.8.0 (PREMISE-FALSIFIED preflight) =="

# premise-falsified (v1.8.0 B1): every source the ticket references AS ALREADY EXISTING is missing from
# the checkout → refine must emit `PREMISE FALSIFIED` with the missing refs and STOP for the human
# BEFORE any archaeology (no hunting for a renamed equivalent, no history reconstruction). The counted
# `PREMISE:` line is emitted either way, so the check cannot silently not-happen.
t="$(run_fixture premise-falsified 'Run the mango refine phase (Phase 0) on this ticket. Scan the project and act on what the scan finds about the sources the ticket references. State what you emit, whether you continue into the rest of Phase 0, and what you do NOT do next. Do not stop for my input; show the artifacts you would produce.')"
assert_contains "premise-falsified: emits PREMISE FALSIFIED"        "$t" 'PREMISE FALSIFIED'
# Decision-level: it names the missing referenced-as-existing source(s) (evidence, not a bare verdict).
assert_all "premise-falsified: names the missing referenced source(s)" "$t" 'exporter\.js|paginate\.js|REPORT_PAGE_SIZE|exporter_spec' 'missing|does not exist|not found|unresolved|absent'
# Decision-level: it HALTS for the human (outcome) rather than proceeding (guard).
assert_all "premise-falsified: halts for the human, does not proceed" "$t" 'stop|halt|refuse|block|wait' 'human|you |confirm|correct the ticket|synthetic|your'
# Non-vacuous the other way: the archaeology is explicitly SKIPPED, not performed.
assert_all "premise-falsified: skips the archaeology (no rename hunt / history reconstruction)" "$t" 'archaeolog|hunt|search|reconstruct|guess|rename|moved|equivalent' 'not|no |never|skip|without|before any|instead'
# The counted artifact.
assert_contains "premise-falsified: emits the PREMISE counting line" "$t" 'PREMISE:'

# premise-to-be-created (v1.8.0 B1, NEGATIVE control): every path the ticket names is framed as
# TO BE CREATED, so its absence is expected — the premise check must NOT fire and refine must carry on.
# This is the non-vacuity in the other direction: a guard that halts on a file the ticket exists to
# create would block every net-new ticket.
t="$(run_fixture premise-to-be-created 'Run the mango refine phase (Phase 0) on this ticket. Scan the project, run the premise check on the sources the ticket references, and state its result and whether it halts the phase. Then continue with the rest of Phase 0. Do not stop for my input; show the artifacts you would produce.')"
# Decision-level: the paths are classified to-be-created (reasoning) so nothing is missing (outcome).
assert_all "premise-new-file: classifies the paths as to-be-created" "$t" 'to.?be.?created|net-?new|will be created|does not exist yet|new (module|file|spec)' 'expected|not .{0,16}missing|0 missing|no .{0,10}missing|create'
assert_contains "premise-new-file: PREMISE line records 0 missing" "$t" 'PREMISE:[^|]*\|[ *_]*0[ *_]*missing|0[ *_]*missing|missing[ *_:=]*0'
# The guard stays SILENT: a real firing emits `PREMISE FALSIFIED: <n≥1> …`. Matching only a non-zero
# count means a transcript that merely DISCUSSES the check cannot fail this assertion.
assert_absent "premise-new-file: no PREMISE FALSIFIED halt (non-vacuous, other direction)" "$t" 'PREMISE FALSIFIED:[ *_]*[1-9]'
# And refine gets on with its actual Phase-0 job.
assert_contains "premise-new-file: refine continues into Phase 0" "$t" 'REFINE:|want-decision|how-decision|skip'

# --- v1.9.0 (the learning loop) -----------------------------------------------
banner "== v1.9.0 (learning loop: claims → recall → recurrence → falsify → human-gated promotion) =="

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

# recall-symbol-type1 (v1.9.0): a type-1 claim is recalled BY SYMBOL — it surfaces when its handle appears
# in the ticket and does NOT surface when it doesn't (the non-vacuity: a recall that fires on everything is
# noise, not recall). And recall is ADVISORY — it injects no requirement and blocks no gate.
t="$(run_fixture recall-symbol-type1 'Run the mango refine phase (Phase 0) on this ticket, including the advisory recall step over the project'"'"'s recorded claims. State what you surface, what you do not, and what recall does to this ticket'"'"'s requirements and gates. Do not stop for my input; show the artifacts you would produce.')"
assert_contains "recall-symbol: emits the RECALL counting line" "$t" 'RECALL:'
assert_all "recall-symbol: the matching-symbol claim IS surfaced" "$t" 'CLM-014|local_store_client' 'surfac|recall'
# The other direction: the non-matching symbol claim is explicitly NOT surfaced.
assert_all "recall-symbol: the non-matching symbol claim is NOT surfaced" "$t" 'CLM-015|layout_grid' 'not[^.]{0,28}(surfac|recall|match)|no[ *_]{1,4}match|does not (match|appear)|skip|exclud|irrelevant'
assert_all "recall-symbol: recall is advisory — injects nothing, blocks nothing" "$t" 'advisory|surfaces only|surface only' 'blocks nothing|never[^.]{0,28}(block|inject)|not[^.]{0,28}(block|inject)|adds no|no new (requirement|acceptance)'

# recall-area-type5 (v1.9.0): a type-5 claim is recalled BY AREA, not by symbol. The ticket names NO symbol
# at all, so the symbol-keyed claim must not surface while the area-keyed one must — which is exactly the
# distinction that makes type 5 its own type rather than a type-1 with a vague handle.
t="$(run_fixture recall-area-type5 'Run the mango refine phase (Phase 0) on this ticket, including the advisory recall step over the project'"'"'s recorded claims. State which claims you surface and what each was matched by. Do not stop for my input; show the artifacts you would produce.')"
assert_contains "recall-area: emits the RECALL counting line" "$t" 'RECALL:'
assert_all "recall-area: the type-5 claim is surfaced BY AREA" "$t" 'CLM-021|loyalty' 'area'
# Non-vacuous: the symbol-keyed claim does NOT surface on a ticket that names no symbol.
assert_all "recall-area: the symbol-keyed claim is NOT surfaced" "$t" 'CLM-023|band_total' 'not[^.]{0,28}(surfac|recall|match)|no[ *_]{1,4}match|does not (match|appear)|skip|exclud'
assert_contains "recall-area: the RECALL line records zero by-symbol matches" "$t" '0[ *_]*by symbol|by symbol[ *_:=|]*0|symbol[ *_:=]*0'

# recall-type6-expiry (v1.9.0): an adjudicated non-defect is recalled by THE FINDING that would otherwise
# be re-raised, and it carries its EXPIRY condition — so an accepted deviation is not a permanent exemption.
# It still only SURFACES: it does not close the ticket or overrule the human raising it again.
t="$(run_fixture recall-type6-expiry 'Run the mango refine phase (Phase 0) on this ticket, including the advisory recall step over the project'"'"'s recorded claims. State what you surface, what it was matched by, and what it does and does not do to this ticket. Do not stop for my input; show the artifacts you would produce.')"
assert_contains "recall-type6: emits the RECALL counting line" "$t" 'RECALL:'
assert_all "recall-type6: recalled by the finding about to be re-raised" "$t" 'CLM-031|sanctioned|adjudicat' 're.rais|the finding|already (examined|accepted)|not be re.litigat'
assert_all "recall-type6: carries its expiry condition" "$t" 'expir' 'token|surface value|accessibility target|revisit|condition'
assert_all "recall-type6: surfaces only — does not close or block the ticket" "$t" 'advisory|surfac' 'blocks nothing|not[^.]{0,32}(block|close|overrul|reject|dismiss)|human (decides|weighs|owns)|for (you|the human)'

# recall-retired-skipped (v1.9.0): two claims share the SAME symbol handle; one is `retired:`. Recall skips
# the retired one and surfaces its superseder — and the retired record is NOT deleted (history stays), with
# no auto-retire anywhere.
t="$(run_fixture recall-retired-skipped 'Run the mango refine phase (Phase 0) on this ticket, including the advisory recall step over the project'"'"'s recorded claims. State which claims you surface and which you skip and why, and what happened to the retired record. Do not stop for my input; show the artifacts you would produce.')"
assert_contains "retired-skip: emits the RECALL counting line" "$t" 'RECALL:'
assert_all "retired-skip: the retired claim is SKIPPED by recall" "$t" 'CLM-041' 'skip|not surfaced|exclud|retired'
# Non-vacuous the other way: recall is not simply silent — the superseding claim IS surfaced.
assert_all "retired-skip: the superseding claim IS surfaced (non-vacuous)" "$t" 'CLM-042' 'surfac|recall'
assert_all "retired-skip: the record stays and nothing auto-retires" "$t" 'not[ *_]{1,4}delet|never[ *_]{1,4}delet|kept|stays|remains|history' 'no auto.retire|human|not automatic|never auto'
assert_contains "retired-skip: the RECALL line counts the retired skip" "$t" 'retired[ *_]*skipped|1[ *_]*retired|retired[ *_:=]*1'

# recurrence-supersession (v1.9.0): dedup across entries. A claim recorded and seen AGAIN is flagged a
# promotion candidate (recording it was not enough); a claim that NARROWS or FALSIFIES an earlier one
# REPLACES it and the old one is marked retired — replaced, never deleted.
t="$(run_fixture recurrence-supersession 'Run the mango finalise phase learning loop on this run'"'"'s claims, deduped against the claims already recorded in the project. State for each whether it recurred or supersedes an earlier claim, and what happens to the earlier record. Do not stop for my input.')"
assert_contains "recurrence: emits the RECURRENCE counting line" "$t" 'RECURRENCE:'
assert_all "recurrence: the twice-seen claim is flagged recurring" "$t" 'CLM-051|idempotency' 'recur|seen again|promotion candidate'
assert_all "supersession: the measured claim REPLACES the inferred one" "$t" 'CLM-052|charge_client' 'supersed|replac'
assert_all "supersession: the old claim is retired, not deleted" "$t" 'retir' 'not[ *_]{1,4}delet|never[ *_]{1,4}delet|stays|kept|history'

# falsify-blocks-promotion (v1.9.0, the decisive case): recurrence measures how often a claim was RESTATED,
# not whether it was CHECKED — so the MOST-repeated claim here is the FALSE one. Both candidates must be
# BLOCKED from promotion (one falsified, one with no cheap check), and the gate must sit IN FRONT of the
# human ratification gate.
t="$(run_fixture falsify-blocks-promotion 'Run the mango finalise phase learning loop from the dedup step onward on the two promotion candidates in this ticket. For each, state what the falsification check asks, what it finds, and the outcome for its promotion, and say where that check sits relative to the human ratification gate. Do not stop for my input.')"
assert_contains "falsify-false: emits the FALSIFY counting line" "$t" 'FALSIFY:'
assert_all "falsify-false: the most-repeated claim is falsified and BLOCKED" "$t" 'CLM-061|empty filter' 'block|not[ *_]{1,4}promot|refus|falsif|fails'
assert_all "falsify-false: the uncheckable claim is BLOCKED too" "$t" 'CLM-062|responsive|feels' 'block|not[ *_]{1,4}promot|no[ *_]{1,4}(measurable|cheap)|not[^.]{0,28}(measur|verifiab|check)'
assert_all "falsify-false: recurrence measures restatement, not truth" "$t" 'restat|repeat' 'not[^.]{0,32}(check|true|truth|quality)|never checked|only repeated|is not (quality|truth|proof)'
assert_all "falsify-false: the check precedes the human ratification gate" "$t" 'before|in front|preced|prior to|first' 'ratif'
assert_contains "falsify-false: emits the PROMOTION counting line" "$t" 'PROMOTION:'

# falsify-true-claim-promotes (v1.9.0, NON-VACUOUS CONTROL): the same gate must PASS a recurring claim that
# is still true, cheaply verifiable, and actually measured — a gate that blocked everything would be a
# promotion pipeline that never promotes. It still ends at the HUMAN, not in effect on its own.
t="$(run_fixture falsify-true-claim-promotes 'Run the mango finalise phase learning loop from the dedup step onward on the promotion candidate in this ticket. State what the falsification check asks, what it finds on each question, and the outcome for its promotion — including whether the rule is now in effect or something must happen first, and who does it. Do not stop for my input.')"
assert_contains "falsify-true: emits the FALSIFY counting line" "$t" 'FALSIFY:'
assert_all "falsify-true: all three falsification questions are answered" "$t" 'still[ *_-]{0,4}true' 'cheap' 'check|measur'
assert_all "falsify-true: the candidate PASSES and reaches the promotion step" "$t" 'CLM-071|transaction' 'propos|promot|candidate|proceed'
# Non-vacuous the other way: passing falsification is not the same as being in effect — the human ratifies.
assert_all "falsify-true: not in effect until the human ratifies" "$t" 'not[^.]{0,32}(in effect|yet|binding|written|applied)|awaiting|PROVISIONAL|propos' 'ratif|human|you '
assert_contains "falsify-true: emits the PROMOTION counting line" "$t" 'PROMOTION:'

# promotion-human-gated (v1.9.0): promotion PROPOSES. Nothing is written before an explicit per-claim
# ratify; a type-3 skill-gap is a project-recorded SIGNAL that never edits a mango skill; and a PROCESS
# heuristic goes to the project agent brief, never into the code rule book.
t="$(run_fixture promotion-human-gated 'Run the mango finalise phase learning loop promotion step on the three claims in this ticket. For each, name the destination file you propose and say whether anything is written now, then answer the four questions in the ticket. Do not stop for my input.')"
assert_all "promotion-gated: the code heuristic is proposed for the project rule book" "$t" 'CLM-081|integration layer' 'rulebook_path|rule[ -]?book|EVAL_RULES'
assert_all "promotion-gated: nothing is written before the explicit ratify" "$t" 'not[^.]{0,32}(writ|edit|creat)|nothing[^.]{0,28}(writ|edit)|no file|propos' 'ratif|human|explicit'
assert_all "promotion-gated: the skill-gap is a project SIGNAL, not a mango edit" "$t" 'CLM-082|skill.gap' 'skill_gap_path|SKILL_GAP|signal'
assert_all "promotion-gated: no mango skill is edited by the loop, ever" "$t" 'mango' 'not[^.]{0,36}(edit|modif|chang|writ)|never[^.]{0,36}(edit|modif|chang|writ)|no mango (skill|file)|maintainer|normal version'
assert_all "promotion-gated: the PROCESS claim goes to the agent brief, not the code rule book" "$t" 'CLM-083|paraphras|PR summary|process' 'agent[ _-]?brief|agent_brief_path'
assert_contains "promotion-gated: the PROMOTION line carries \`mango files written: 0\`" "$t" 'mango files written[ *_:=]*0'

# promotion-rulebook-wiring (v1.9.0): a RATIFIED promotion writes the rule into rulebook_path — never into
# CLAUDE.md, which carries only init's pointer — and is not "done" until doctor is green on that pointer.
# The loop REUSES init/doctor's wiring; it does not rebuild it.
t="$(run_fixture promotion-rulebook-wiring 'Carry out the ratified promotion in this ticket per the mango finalise phase learning loop. State exactly which file the rule text goes into and which files it does not, what makes the promotion done rather than merely written, which existing mango skills own that wiring, and what happens if the project has no rule book. Do not stop for my input.')"
assert_all "wiring: the rule text is written into the project rule book" "$t" 'rulebook_path|rule[ -]?book|EVAL_RULES' 'writ|add|record|land'
assert_all "wiring: the rule is NOT copied into CLAUDE.md (pointer only)" "$t" 'CLAUDE\.md' 'not[^.]{0,32}(cop|writ|past|includ)|never|only[^.]{0,24}point|point(er|s to)'
assert_all "wiring: not done until doctor is green on the pointer" "$t" 'doctor' 'green|pointer'
assert_all "wiring: init/doctor own the wiring — reused, not rebuilt" "$t" 'init' 'reus|already|not[ *_]{1,4}rebuil|own'
assert_all "wiring: a missing rule book is created rather than skipped" "$t" 'creat' 'rule[ -]?book|rulebook_path'

# loop-project-local (v1.9.0): every loop output path is inside the PROJECT repo — nothing lands under a
# mango plugin directory, an unset destination key is SURFACED rather than redirected or dropped, and
# nothing is carried home to the next project.
t="$(run_fixture loop-project-local 'Run the mango finalise phase learning loop promotion step on the six claims in this ticket. Enumerate the destination path for each, then answer the four questions in the ticket and report the PROMOTION line. Do not stop for my input.')"
assert_all "project-local: every destination is inside the project repo" "$t" 'project' 'inside|within|repo|local'
assert_all "project-local: nothing lands under a mango plugin directory" "$t" 'mango' 'mango files written[ *_:=]*0|no mango|not[^.]{0,36}(under|inside|in) (a |the )?mango|never[^.]{0,36}mango'
assert_all "project-local: the type-3 claim is a project-recorded maintainer signal" "$t" 'CLM-103|skill.gap' 'skill_gap_path|SKILL_GAP|signal|maintainer'
assert_all "project-local: an unset destination key is surfaced, not redirected or dropped" "$t" 'unset|not (set|configured)|absent|missing' 'surfac|report|say so|not[^.]{0,28}(drop|silent|elsewhere)'
assert_all "project-local: nothing is carried home to another project" "$t" 'carr|home|another project|different project' 'nothing|none|separate|isolat|project.local|no '
assert_contains "project-local: the PROMOTION line carries \`mango files written: 0\`" "$t" 'mango files written[ *_:=]*0'

# host-context-file-default (v1.9.1): the DEFAULT must be unchanged. On a plain CLAUDE.md project with
# no AGENTS.md and no `context_file` key, init still hoists into CLAUDE.md and doctor still reads it —
# host-awareness must not have moved the Claude-Code case. This is the negative control for the pair:
# a resolver that always answered AGENTS.md would break every existing project.
t="$(run_fixture host-context-file-default 'Run the mango init standing-context hoist (step 6) and then the mango doctor standing-context check against the project state described in this ticket. Answer the four numbered questions. Do not stop for my input.')"
assert_all "ctx-default: the block lands in CLAUDE.md" "$t" 'CLAUDE\.md' 'writ|hoist|land|target|into'
assert_all "ctx-default: it got there by RESOLVING, not assuming" "$t" 'context_file|resolv|detect|default' 'AGENTS\.md|no AGENTS|absent|not (set|present)|unset'
assert_all "ctx-default: the resolved path is recorded in config.context_file" "$t" 'context_file' 'record|writ|set|so doctor|same answer'
assert_all "ctx-default: the block is a POINTER to the rule book, never a copy" "$t" 'point' 'not[^.]{0,24}(a )?cop|never[^.]{0,24}cop|rulebook_path|rule[ -]?book'
assert_all "ctx-default: no secret may appear in the context file" "$t" 'secret|token|credential' 'never|no |not |forbid|\.env'
assert_all "ctx-default: doctor reads the same file and never fails the run" "$t" 'CLAUDE\.md' 'informational|never[^.]{0,20}(fail|block|❌)|not[^.]{0,20}(fail|block)|warn|⚠'

# host-context-file-agents (v1.9.1): the firing case. The host auto-loads AGENTS.md and CLAUDE.md is a
# one-line `@AGENTS.md` import, so the hoist must target AGENTS.md — a block written only into the
# unloaded CLAUDE.md is invisible to the host, which doctor must SURFACE (as a warn, never a ❌).
t="$(run_fixture host-context-file-agents 'Run the mango init standing-context hoist (step 6) and then the mango doctor standing-context check against the project state described in this ticket. Answer the four numbered questions. Do not stop for my input.')"
assert_all "ctx-agents: the block targets AGENTS.md, the file the host loads" "$t" 'AGENTS\.md' 'writ|hoist|land|target|into'
assert_all "ctx-agents: the one-line import is what settled the resolution" "$t" 'import|@AGENTS|stub|one[ -]line' 'AGENTS\.md|resolv|actually load|auto-?load'
assert_all "ctx-agents: the resolved path is recorded in config.context_file" "$t" 'context_file' 'record|writ|set|so doctor|same answer'
assert_all "ctx-agents: a block only in the unloaded CLAUDE.md is surfaced, not passed" "$t" 'CLAUDE\.md' 'warn|⚠|not[^.]{0,28}(load|reach|visib)|invisib|unloaded|does not auto-?load'
assert_all "ctx-agents: doctor warns rather than failing the run" "$t" 'warn|⚠' 'never[^.]{0,20}(fail|block|❌)|not[^.]{0,20}(fail|block)|informational'
assert_all "ctx-agents: the block is still a POINTER, never a copy" "$t" 'point' 'not[^.]{0,24}(a )?cop|never[^.]{0,24}cop|rulebook_path|rule[ -]?book'

# ---- v1.10.0: the learning-loop pipe joined (type-2 recall by handle -> answered at design ->
# ---- recurring claim leaves lessons_path) + cross-ticket `promote` + the on-demand preload split.

# T1 recall-type2-handle: type 2 is keyed by a class HANDLE (neither symbol nor area can key a heuristic).
# It fires on the change SHAPE — a shared vocabulary here — while the type-1 symbol and the type-5 area in
# the same corpus stay silent. Non-vacuity in one fixture: one surfaces, two must not.
t="$(run_fixture recall-type2-handle 'Run the mango refine phase (Phase 0) on this ticket, including the advisory recall step over the project'"'"'s recorded claims. State which claims you surface, what each was matched by, and which you do not surface. Emit the counted RECALL: line. Do not stop for my input.')"
assert_all "t2-handle: the type-2 claim surfaces, matched by its HANDLE" "$t" 'CLM-311|blast-radius-grep' 'handle'
assert_all "t2-handle: the match is on the change SHAPE (shared vocabulary), not a symbol or an area" "$t" 'shared|vocabular|enum|consumer|thread' 'handle|class'
assert_all "t2-handle: the type-1 symbol claim does NOT surface" "$t" 'CLM-312|queue_client' 'not[^.]{0,40}(surfac|match|appear)|no[t]? .{0,20}(present|named)|silent|skip|0 by symbol'
assert_all "t2-handle: the type-5 area claim does NOT surface" "$t" 'CLM-313|billing' 'not[^.]{0,40}(surfac|match|appear)|different area|0 by area|skip'
assert_contains "t2-handle: the RECALL line counts \`by handle\`" "$t" 'by handle'
assert_all "t2-handle: recall stays advisory — it adds no requirement, AC or gate" "$t" 'advisory|surfac' 'not[^.]{0,30}(inject|add|block|requirement|gate)|never|only surfac|blocks nothing'

# T2 handle-unanswered-blocks: a recalled handle with no trace and no `does not apply` BLOCKS Gate 2. This
# is the adequacy half — a filled blast-radius cell naming a surface is not an answer to the handle.
t="$(run_fixture handle-unanswered-blocks 'Run the mango design skill blast-radius step and Gate-2 self-audit on the injected design state in this ticket. State whether Gate 2 passes or is blocked and exactly what is missing, and emit the HANDLES: counting line as it stands. Do not stop for my input.')"
assert_all "unanswered: Gate 2 is BLOCKED" "$t" 'Gate 2' 'block|❌|not[ *_]{1,4}pass|fail|cannot pass|held'
assert_all "unanswered: the unanswered handle is named as the cause" "$t" 'blast-radius-grep|handle' 'unanswered|no trace|not answered|neither|missing'
assert_contains "unanswered: the HANDLES line is emitted" "$t" 'HANDLES:'
assert_all "unanswered: the filled blast-radius cell is not accepted as the answer" "$t" 'blast[ -]radius|cell|callers of the builder' 'not[^.]{0,40}(a trace|an answer|sufficient|enough)|no command|does not answer|names a surface'

# T3 handle-does-not-apply-closes: the negative control that keeps this from becoming a tax. An explicit
# `does not apply because <reason>` is a LEGAL answer and CLOSES the handle — the gate is on accounting.
t="$(run_fixture handle-does-not-apply-closes 'Run the mango design skill blast-radius step and Gate-2 self-audit on the injected design state in this ticket. State whether Gate 2 passes or is blocked, whether the recorded answer to the recalled handle is legal, and emit the HANDLES: counting line. Do not stop for my input.')"
assert_all "does-not-apply: the recorded answer is LEGAL and closes the handle" "$t" 'does not apply' 'legal|valid|acceptable|closes|answered|satisfies|sufficient'
assert_all "does-not-apply: Gate 2 is NOT blocked by the handle" "$t" 'Gate 2' 'pass|clear|not[ *_]{1,4}block|no[ *_]{1,4}block|proceed|closes'
assert_contains "does-not-apply: the HANDLES line is emitted" "$t" 'HANDLES:'
assert_contains "does-not-apply: unanswered is zero" "$t" '0[ *_]*unanswered|unanswered[ *_:=]*0'

# T4 recurring-t2-leaves-lessons: a type-2 claim with seen >= 2 may NOT resolve to `stays in lessons_path`
# — recording it was already the treatment. It routes to the rule book (code) or the agent brief (process).
t="$(run_fixture recurring-t2-leaves-lessons 'Run the mango finalise learning loop from the recurrence step onward on the two claims in this ticket. For each, state the destination you propose and whether stays in lessons_path is acceptable. Emit the RECURRING-T2: counting line and say whether finalise proceeds or blocks. Do not stop for my input.')"
assert_all "recurring-t2: \`stays in lessons_path\` is REJECTED for both recurring type-2 claims" "$t" 'lessons_path' 'reject|not[ *_]{1,4}(accept|allow|permit)|may not|forbid|unacceptable|blocked'
assert_all "recurring-t2: the code heuristic routes to the rule book" "$t" 'CLM-411|blast-radius-grep' 'rulebook_path|rule[ -]?book|EVAL_RULES'
assert_contains "recurring-t2: the RECURRING-T2 line is emitted" "$t" 'RECURRING-T2:'
assert_all "recurring-t2: recurrence, not presence, is what triggered it" "$t" 'seen|recurren|twice|two ticket' 'PROJ-069|PROJ-611|>= 2|≥ 2|2 ticket'

# T5 type5-stays-in-lessons: the NEGATIVE CONTROL. All existing claim records are type-5 project facts;
# sweeping them into a rule book would rot it. A recurring type-5 legitimately stays in lessons_path.
t="$(run_fixture type5-stays-in-lessons 'Run the mango finalise learning loop from the recurrence step onward on the two claims in this ticket. State for each whether stays in lessons_path is accepted or rejected, say whether the recurring-type-2 destination rule applies, and emit the RECURRING-T2: counting line. Do not stop for my input.')"
assert_all "type5-control: \`stays in lessons_path\` is ACCEPTED for the type-5 claims" "$t" 'lessons_path' 'accept|allow|legitimat|stays|remains|correct|valid|unchanged'
assert_all "type5-control: the recurring-type-2 rule does NOT apply to type 5" "$t" 'type 5|type-5' 'not[^.]{0,40}(apply|affect|touch)|does not|only[^.]{0,20}type 2|type 2 only|exempt|untouched'
assert_contains "type5-control: the RECURRING-T2 line is still emitted, with zeros" "$t" 'RECURRING-T2:'
assert_absent "type5-control: finalise is NOT blocked by a type-5 claim staying put" "$t" 'block(s|ed|ing)? finalise|finalise (is )?blocked'

# T6 template-resolve-no-plugin-root: with the plugin-root variable unset, the resolution order continues
# down its steps and the claim record is still produced with its fields — never a hardcoded path, never prose.
t="$(run_fixture template-resolve-no-plugin-root 'Answer the four numbered questions in this ticket, in order, as the mango finalise claim-classification step would on this host. Do not stop for my input.')"
assert_all "no-root: the resolution order is followed, not abandoned" "$t" 'resolv|order|step' 'skill file|plugin root|search|locate|directory'
assert_all "no-root: the unset variable is not the end of the road" "$t" 'CLAUDE_PLUGIN_ROOT|unset|not set|empty' 'else|next|fall ?back|step 2|continue|still'
assert_all "no-root: the claim record is still produced with its fields" "$t" 'type:' 'evidence:|handle:|area:|destination:'
assert_all "no-root: no hardcoded or guessed path is used" "$t" 'hardcod|guess|home director|invent' 'never|not|no |forbid|avoid'
assert_all "no-root: it does not degrade to prose" "$t" 'prose|field' 'not[^.]{0,30}prose|never|inline|field'

# T7 recall-zero-no-busywork: recall that matches nothing closes with zeros and adds NOTHING. Without this
# control the recall step becomes a tax on every ticket it has no claim for.
t="$(run_fixture recall-zero-no-busywork 'Run the mango refine phase advisory recall for this ticket. State which claims you surface, emit the counted RECALL: line, and then say whether this ticket now carries any extra step, question, trace, matrix row or gate because recall ran. Do not stop for my input.')"
assert_contains "recall-zero: the RECALL line is emitted" "$t" 'RECALL:'
assert_contains "recall-zero: zero claims surfaced" "$t" 'RECALL:[ *_]*0|0 claim|no claims|zero claim'
assert_all "recall-zero: nothing is added to the ticket" "$t" 'no[ *_]{1,4}(extra|additional|new)|nothing|none|unchanged|no change' 'step|row|gate|question|trace|work'
assert_absent "recall-zero: no handle is invented to look busy" "$t" 'blast-radius-grep (applies|surfaces|is surfaced)'

# T8 promote-two-lessons-one-rule: recurrence across tickets is the entry condition; two instances of one
# class yield ONE candidate citing both, and nothing is written before a ratify.
t="$(run_fixture promote-two-lessons-one-rule 'Run the mango promote skill on the corpus in this ticket. Emit its counted line and per-class table first, then any candidate rule with its destination and the lesson text behind each clause. State what has been written to disk, then answer the question about CLM-703. Do not stop for my input.')"
assert_contains "promote-two: the PROMOTE counted line is emitted" "$t" 'PROMOTE:'
assert_all "promote-two: exactly one candidate rule for the one recurring class" "$t" 'blast-radius-grep' '1 candidate|one candidate|single candidate|1 class'
assert_all "promote-two: both instances are cited" "$t" 'CLM-701' 'CLM-702'
assert_all "promote-two: nothing is written before the ratify" "$t" 'rules written[ *_:=]*0|nothing[^.]{0,24}(writ|creat)|not[^.]{0,24}writ' 'ratif|human|gate|propos'
assert_all "promote-two: the code heuristic routes to the rule book" "$t" 'rulebook_path|EVAL_RULES|rule[ -]?book' 'destination|route|goes|written to'
assert_all "promote-two: the type-5 claim is out of scope" "$t" 'CLM-703|type 5|type-5' 'out of scope|not[^.]{0,30}(promot|eligib|consider)|skip|excluded|only type 2'

# T9 promote-single-lesson-noop: recurrence 1 proposes NOTHING. The control that stops promote inventing
# rules from a single sighting.
t="$(run_fixture promote-single-lesson-noop 'Run the mango promote skill on the corpus in this ticket. Emit its counted line and per-class table, state how many candidate rules you propose and the verdict per handle, and say whether any rule text was drafted or written. Do not stop for my input.')"
assert_contains "promote-one: the PROMOTE counted line is emitted" "$t" 'PROMOTE:'
assert_all "promote-one: zero candidates proposed" "$t" '0 candidate|no candidate|zero candidate|nothing[^.]{0,20}propos|propose nothing' 'recurrence 1|seen (only )?once|one ticket|single ticket'
assert_all "promote-one: both handles are reported as skipped, not silently dropped" "$t" 'blast-radius-grep' 'empirical-output-in-summary|skip'
assert_absent "promote-one: no rule text is drafted" "$t" 'rules written[ *_:=]*[1-9]'

# T10 promote-idempotent: a class already recorded at its destination proposes nothing NEW, so re-running
# the pass is safe and cannot duplicate a rule.
t="$(run_fixture promote-idempotent 'Run the mango promote skill on the corpus in this ticket again. Emit its counted line and per-class table, give the verdict for the blast-radius-grep class with the evidence you based it on, and state how many NEW candidate rules this run proposes. Do not stop for my input.')"
assert_contains "idempotent: the PROMOTE counted line is emitted" "$t" 'PROMOTE:'
assert_all "idempotent: the class is skipped as already recorded" "$t" 'blast-radius-grep' 'already|skip|exists|present|recorded'
assert_all "idempotent: the existing rule-book entry is the evidence" "$t" 'EVAL_RULES|rule[ -]?book' 'Blast radius|CLM-901|CLM-902|line'
assert_all "idempotent: zero NEW candidates" "$t" '0 (new )?candidate|no (new )?candidate|nothing new|zero' 'propos|new'
assert_absent "idempotent: the rule is not duplicated" "$t" 'rules written[ *_:=]*[1-9]'

# T11 ondemand-companion-read: a phase whose content moved to an on-demand companion must READ it and
# behave exactly as before — the moved block still governs the decision.
t="$(run_fixture ondemand-companion-read 'Run the mango design skill on this ticket. State which files you read and why before producing the Phase-2 artifacts, then produce the verification plan and Gate-2 verdict and answer the four numbered questions. Do not stop for my input.')"
assert_all "ondemand-read: the frontend companion is named and read" "$t" 'frontend\.md' 'read|reading|load|consult|open'
assert_all "ondemand-read: the unit proof is a layer mismatch that blocks Gate 2" "$t" 'Gate 2' "$RE_LAYER_MISMATCH"
assert_all "ondemand-read: DESIGN.md must exist before the plan is named" "$t" 'DESIGN\.md' 'creat|updat|before|must exist'
assert_all "ondemand-read: the plan carries one row per surface against SURFACES: 4" "$t" '4|four' 'surface|per surface|row per'
assert_contains "ondemand-read: the behaviour is unchanged by the relocation" "$t" 'no horizontal scroll|reflow|integration|runtime|computed-style|document'

# T12 ondemand-read-no-plugin-root: the on-demand read resolves with the plugin-root variable unset, and a
# companion it still cannot reach never turns a required check into no check.
t="$(run_fixture ondemand-read-no-plugin-root 'Answer the five numbered questions in this ticket, in order, as the mango review phase would on this host. Score the diff against the rules the companion carries. Do not stop for my input.')"
assert_all "ondemand-noroot: the companion is named and its path resolved" "$t" 'frontend\.md' 'resolv|locate|skill file|plugin root|search'
assert_all "ondemand-noroot: it is read, not skipped because the variable is unset" "$t" 'read' 'not[ *_]{1,4}skip|do not skip|still|unset|regardless'
assert_all "ondemand-noroot: the hover-only affordance is scored" "$t" 'hover' 'M6|M10|pointer|tap|focus|block|fail|finding'
assert_all "ondemand-noroot: the 32px targets are scored against the touch-target gate" "$t" '32|44' 'touch[ -]target|M4|fail|block|finding'
assert_all "ondemand-noroot: an unreachable companion never means no check" "$t" 'never|not|no ' 'no check|without a check|unchecked|drop|skip the rubric|minimum|at minimum'

# ---- v1.10.1: the rule-first recall path (a recalled handle makes its rule section applicable, the
# ---- lite lane reads what it writes, a promoted claim can retire) + the open backlog fixes.

# T1 rule-section-by-handle: the bridge itself. A rule promoted from a handle can never be reached from a
# CHANGE TYPE, so without this source it sits inert while the lesson does the work forever.
t="$(run_fixture rule-section-by-handle 'Run the mango analysis phase advisory recall and then its rule-compliance section-coverage step for this ticket. Emit the counted RECALL: and RULE SECTIONS: lines, name the source that made each applicable section applicable, and answer the closing question. Do not stop for my input.')"
assert_contains "sec-handle: the RULE SECTIONS line is emitted" "$t" 'RULE SECTIONS:'
assert_all "sec-handle: the handle-carrying section is applicable" "$t" '4\.2' 'applicable|applies|in scope|must be (checked|answered)'
assert_all "sec-handle: its source is the recalled handle, not the change type" "$t" 'blast-radius-grep|recalled handle|by handle' '4\.2|source'
assert_all "sec-handle: the change-type derivation is still there (additive, not replaced)" "$t" 'change[ -]type' '2\.1|3\.7|naming|migration|schema'
assert_all "sec-handle: the change type alone could NOT have reached it" "$t" '4\.2|handle' 'no[t]?[^.]{0,40}(change[ -]type|map|derive)|only[^.]{0,30}handle|never[^.]{0,30}change[ -]type'
assert_all "sec-handle: the answer names what in THIS change the rule constrains" "$t" 'enum|dispatch_outcome|consumer|sender|retry scheduler' 'trace|producer|consumer|enumerat|constrain'

# T2 rule-section-handle-unanswered: the teeth. An applicable handle-matched section left neither answered
# nor N/A is a finding — the same accounting the change-type source has always been under.
t="$(run_fixture rule-section-handle-unanswered 'Run the mango analysis rule-compliance section-coverage step and Gate-1 self-audit against the injected state in this ticket. State whether Gate 1 is clear or carries a finding and exactly what is missing, then emit the RULE SECTIONS: line as it should stand. Do not stop for my input.')"
assert_all "sec-unanswered: Gate 1 carries a finding" "$t" 'Gate 1|finding' 'finding|block|not[ *_]{1,4}clear|incomplete|fail'
assert_all "sec-unanswered: the unanswered handle-matched section is named as the cause" "$t" '6\.4|value-threading-callers' 'unanswered|neither|missing|omitted|not (checked|answered|marked)'
assert_contains "sec-unanswered: the RULE SECTIONS line is emitted" "$t" 'RULE SECTIONS:'
assert_all "sec-unanswered: the corrected line counts the handle-matched source" "$t" 'by recalled handle|by handle' '1|one'
assert_absent "sec-unanswered: the recorded zero-handle line is not accepted as it stands" "$t" 'Gate 1 (is )?(clear|clean|passes)( |,|\.|$)'

# T3 rule-section-handle-na-closes: the negative control that stops the new source becoming a tax. An
# explicit `N/A because <reason>` is a LEGAL, CLOSING answer — the gate is on the accounting, not on work.
t="$(run_fixture rule-section-handle-na-closes 'Run the mango analysis rule-compliance section-coverage step and Gate-1 self-audit against the injected state in this ticket. State whether the recorded answer to the handle-matched section is legal, whether Gate 1 is clear or blocked, emit the RULE SECTIONS: line, and say what extra work the handle-matched source caused. Do not stop for my input.')"
assert_all "sec-na: the recorded N/A answer is LEGAL and closes the section" "$t" 'N/A|not applicable' 'legal|valid|acceptable|closes|answered|sufficient|satisfies'
assert_all "sec-na: Gate 1 is NOT blocked by the handle-matched section" "$t" 'Gate 1' 'clear|pass|not[ *_]{1,4}block|no[ *_]{1,4}block|proceed|clean'
assert_contains "sec-na: the RULE SECTIONS line is emitted" "$t" 'RULE SECTIONS:'
assert_all "sec-na: the reason names the property of THIS change" "$t" 'file-local|not exported|no consumer|one file' 'reason|because'
assert_absent "sec-na: no extra investigation is demanded of a closed section" "$t" '(must|need to) (now )?(trace|enumerate) every (consumer|test root)'

# T4 rule-section-provisional-no-block: the greenfield-safety hinge of A1. An UNRATIFIED rule is surfaced
# and accounted for, but its CONTENT may not gate-block as though a human had chosen it.
t="$(run_fixture rule-section-provisional-no-block 'Run the mango analysis rule-compliance section-coverage step and Gate-1 self-audit for this ticket. Emit the RULE SECTIONS: line and answer the three numbered questions. Do not stop for my input.')"
assert_all "provisional: the provisional section IS surfaced in the applicable list" "$t" '9\.3|shared-type-golden-fixture' 'applicable|listed|surfac|appears'
assert_all "provisional: it is tagged as provisional / unratified" "$t" 'PROVISIONAL|provisional|unratified|awaiting ratification' '9\.3|section|rule'
assert_all "provisional: an unmet provisional rule does NOT block Gate 1 as a codified one would" "$t" 'not[ *_]{1,4}block|does not block|no[ *_]{1,4}block|surfac(e|ed) (only|rather)|not a (Gate 1 )?block' 'provisional|unratified|not ratified|codified'
assert_all "provisional: the unsatisfied standard routes to the ratify flow" "$t" 'codify|ratif' 'route|nudge|surfac|human|provisional'
assert_absent "provisional: mango does not enforce a rule nobody chose" "$t" 'Gate 1 is blocked (by|because of) (§?9\.3|the golden fixture)'

# T5 quick-direct-recall: the lite-lane bypass. A directly-invoked quick used to write lessons at finalise
# and never read one — a one-way contributor to a file that only grows.
t="$(run_fixture quick-direct-recall 'Run the mango quick skill on this ticket through its pre-code gate artifacts, and answer the five numbered questions. Do not stop for my input.')"
assert_contains "quick-recall: the RECALL line is emitted on a direct invocation" "$t" 'RECALL:'
assert_contains "quick-recall: the RULE SECTIONS line is emitted on a direct invocation" "$t" 'RULE SECTIONS:'
assert_all "quick-recall: the matching claim surfaces, matched by its handle" "$t" 'CLM-724|value-threading-callers' 'handle|by handle'
assert_all "quick-recall: the handle-carrying rule section becomes applicable" "$t" '6\.4' 'applicable|handle|applies'
assert_all "quick-recall: the lane still reads the corpus, not only writes to it" "$t" 'read' 'recall|lessons|corpus|LESSONS'
assert_all "quick-recall: the lane stays lite — no challenger, matrix, fan-out or baseline" "$t" 'challenger' 'no[^.]{0,30}(challenger|matrix|fan-?out|baseline)|not[^.]{0,30}(challenger|matrix|fan-?out|baseline)|skip'

# T6 claim-retired-promoted: `retired: promoted to <rule-ID>` is a recognised retirement — recall SKIPS the
# claim and the record STAYS. Retirement is not deletion and there is no auto-retire.
t="$(run_fixture claim-retired-promoted 'Run the mango refine phase advisory recall for this ticket, emit the counted RECALL: line, and answer the four numbered questions. Do not stop for my input.')"
assert_contains "retired-promoted: the RECALL line is emitted" "$t" 'RECALL:'
assert_all "retired-promoted: the retired claim is SKIPPED, not surfaced" "$t" 'CLM-730' 'skip|retired|not[^.]{0,30}(surfac|recall)|excluded'
assert_all "retired-promoted: it is counted on the retired-skipped column" "$t" 'retired skipped' '1|one'
assert_all "retired-promoted: the still-live claim DOES surface" "$t" 'CLM-731|shared-type-per-consumer' 'surfac|handle|match'
assert_all "retired-promoted: the record stays in the file — retirement is not deletion" "$t" 'stays|remains|still (in|present)|not deleted|never deleted|history' 'record|LESSONS|file|claim'
assert_all "retired-promoted: \`promoted to\` is a recognised reason a HUMAN applied" "$t" 'promoted to' 'human|ratif|offer|not auto|no auto-?retire'

# T7 promote-offers-retirement: promotion is a COPY, so the claims must be retirable — but the offer is
# never self-applied. This is the one place an auto-retire could creep into the loop; it must not.
t="$(run_fixture promote-offers-retirement 'Continue the mango promote run from the operator ratify recorded in this ticket. Emit the counted PROMOTE: line, state exactly what you write to the rule book, and answer the five numbered questions. Do not stop for my input.')"
assert_all "promote-retire: retirement is OFFERED as a question, not applied" "$t" 'offer|ask|question|answer per claim|would you' 'retire|retirement|promoted to'
assert_all "promote-retire: nothing is retired without the human answer" "$t" 'not[^.]{0,40}(retired|applied|marked)|no[^.]{0,20}auto-?retire|awaiting|until (you|the human) answer' 'retire|human|answer'
assert_all "promote-retire: the retirement reason names the rule that landed" "$t" 'promoted to' '4\.2|rule[ -]ID|<rule-ID>'
assert_all "promote-retire: both claims in the class are offered" "$t" 'CLM-740' 'CLM-741'
assert_all "promote-retire: retirement never deletes the record" "$t" 'not deleted|never delete|stays|remains|history' 'record|claim|LESSONS'
assert_all "promote-retire: the written rule carries the handle so the rule can be recalled" "$t" 'blast-radius-grep|handle' 'writ|carr|cite|record'
assert_all "promote-retire: the ordering rationale — retiring first would remove coverage" "$t" 'before|first|order' 'remove[^.]{0,24}coverage|lose[^.]{0,24}coverage|gap|inert|uncovered|no longer'
assert_absent "promote-retire: no silent auto-retire" "$t" '(I have|I) (now )?marked (CLM-740|both claims) retired'

# T8 plugin-root-newest-version: a host that sets no plugin-root variable returned EIGHT candidates in the
# field and `find` order put the oldest first — silently loading a two-minor-version-old contract.
t="$(run_fixture plugin-root-newest-version 'Answer the five numbered questions in this ticket, in order, as a mango skill resolving a shipped path on this host. Do not stop for my input.')"
assert_all "root-newest: the newest candidate is selected" "$t" '1\.10\.1|mango-c' 'select|use|choose|chosen|pick'
assert_all "root-newest: the candidate count is reported" "$t" '3|three' 'candidate|director|match|found'
assert_all "root-newest: selection is by semver compare, not find order" "$t" 'semver|version' 'not[^.]{0,40}(find|search) order|highest|newest|numeric'
assert_all "root-newest: a plain string sort is explicitly rejected" "$t" 'string|lexicograph|1\.10\.1.*1\.8\.0' 'not|never|wrong|incorrect|would'
assert_all "root-newest: taking the first hit would have loaded the old contract" "$t" '1\.8\.0' 'first|order|would have|stale|old'

# T9 challenger-pr-body-refused: the PR body restates the design and the requirements, so reading it
# launders the authored design back into the review that exists to be independent of it.
t="$(run_fixture challenger-pr-body-refused 'You are mango challenger agent. Apply your agent brief to the input in this ticket and answer the four numbered questions in order. Do not stop for my input.')"
assert_all "chal-pr: the PR body is identified as forbidden input while challenging" "$t" 'pull request|PR body|PR description' 'forbid|not[ *_]{1,4}(read|allow|legitimate)|must not|off[ -]limits|excluded'
assert_all "chal-pr: gh pr view is refused" "$t" 'gh pr view' 'no|not|refuse|will not|must not|decline'
assert_all "chal-pr: independence is reported compromised rather than proceeding quietly" "$t" 'independen' 'compromis|report|say so|declare|flag'
assert_all "chal-pr: the PR's numbered requirement list is not adopted as the requirements" "$t" 'rebuild|derive|my own|independently|from the raw ticket' 'requirement'
assert_all "chal-pr: ref-based git reading is still allowed" "$t" 'git diff|git show|git log' 'allow|still|permitted|may|use'

# ---- GREENFIELD NEGATIVE CONTROLS. A freshly `init`-ed project has no lessons file, a rule book of
# ---- TODOs, zero claims and zero handles. Every mechanism above must CLOSE WITH ZEROS there. If any of
# ---- these four goes red the version is not shippable, whatever else passes.

# G1 greenfield-full-run: the whole lifecycle front half on a project that has learned nothing yet.
t="$(run_fixture greenfield-full-run 'Run the mango refine and analysis phases for this ticket through the Gate-1 self-audit. Emit every counted line both phases emit and answer the four numbered questions. Do not stop for my input.')"
assert_contains "greenfield: the RECALL line is emitted" "$t" 'RECALL:'
assert_contains "greenfield: recall closes with zero claims" "$t" 'RECALL:[ *_]*0|0 claim|no claims|zero claim'
assert_contains "greenfield: the RULE SECTIONS line is emitted" "$t" 'RULE SECTIONS:'
assert_all "greenfield: zero sections come from the recalled-handle source" "$t" 'by recalled handle|by handle' '0|zero|none'
assert_all "greenfield: the missing lessons file neither stops nor warns nor blocks" "$t" 'LESSONS|lessons_path|missing|absent|does not exist' 'not[^.]{0,40}(block|stop|warn|error)|no[ *_]{1,4}(block|warn|error)|continue|proceed|zero'
assert_all "greenfield: no extra step, question, row or gate is added" "$t" 'no[ *_]{1,4}(extra|additional|new)|nothing|none|unchanged' 'step|row|gate|question|trace|work'
assert_all "greenfield: Gate 1 clears" "$t" 'Gate 1' 'clear|pass|proceed|clean|ready'
assert_absent "greenfield: the TODO rule book is not itself a finding" "$t" '(TODO|unfilled rule ?book)[^.]{0,40}(is a finding|blocks Gate)'

# G2 greenfield-quick-direct: the A2 reads must be free on a project with nothing to read.
t="$(run_fixture greenfield-quick-direct 'Run the mango quick skill on this ticket through its pre-code gate, emit every counted line the lane emits, and answer the four numbered questions. Do not stop for my input.')"
assert_contains "greenfield-quick: the RECALL line is emitted with zeros" "$t" 'RECALL:'
assert_contains "greenfield-quick: zero claims surfaced" "$t" 'RECALL:[ *_]*0|0 claim|no claims|zero claim'
assert_contains "greenfield-quick: the RULE SECTIONS line is emitted" "$t" 'RULE SECTIONS:'
assert_all "greenfield-quick: the missing lessons file does not stop or warn the lane" "$t" 'LESSONS|lessons_path|missing|absent|does not exist' 'not[^.]{0,40}(block|stop|warn|error)|no[ *_]{1,4}(block|warn|error)|continue|zero'
assert_all "greenfield-quick: the lane stays lite" "$t" 'challenger|matrix|fan-?out|baseline' 'no|not|skip|without'
assert_all "greenfield-quick: still two human gates" "$t" '2|two' 'gate'

# G3 greenfield-promote-zeros: promote on an empty corpus emits zeros, proposes nothing and stops.
t="$(run_fixture greenfield-promote-zeros 'Run the mango promote skill against the project state described here and answer the five numbered questions, emitting the counted PROMOTE: line and the per-class table first. Do not stop for my input.')"
assert_contains "greenfield-promote: the PROMOTE counted line is emitted" "$t" 'PROMOTE:'
assert_all "greenfield-promote: zero classes and zero candidates" "$t" '0 class|no class|zero class|0 candidate|no candidate|zero candidate' 'propos|class|candidate'
assert_all "greenfield-promote: nothing is drafted and nothing is written" "$t" 'rules written[ *_:=]*0|nothing[^.]{0,24}(writ|draft|creat)|no rule text' 'writ|draft|propos'
assert_all "greenfield-promote: it stops rather than asking a ratification question" "$t" 'stop|halt|end|no candidate' 'no[^.]{0,30}(question|gate|ratif)|nothing to ratify|stops'
assert_all "greenfield-promote: an absent corpus is not an error" "$t" 'not[ *_]{1,4}(an )?error|no[ *_]{1,4}error|neither|not configured|says so' 'corpus|LESSONS|lessons_path|absent|missing'
assert_absent "greenfield-promote: no rule is written" "$t" 'rules written[ *_:=]*[1-9]'

# G4 greenfield-recall-handles-none-match: a corpus FULL of handles, none matching this change shape. A1 must add
# exactly zero sections — the new source may not become an always-on tax once a project has learned things.
t="$(run_fixture greenfield-recall-handles-none-match 'Run the mango analysis phase advisory recall and its rule-compliance section-coverage step for this ticket. Emit the counted RECALL: and RULE SECTIONS: lines and answer the four numbered questions. Do not stop for my input.')"
assert_contains "no-match: the RECALL line is emitted" "$t" 'RECALL:'
assert_all "no-match: zero claims surfaced by handle" "$t" 'by handle' '0|zero|none'
assert_contains "no-match: the RULE SECTIONS line is emitted" "$t" 'RULE SECTIONS:'
assert_all "no-match: the handle-matched source adds zero sections" "$t" 'by recalled handle|by handle' '0|zero|none|add(s|ed)? no'
assert_all "no-match: the handle-carrying sections are NOT applicable here" "$t" '4\.2|7\.3' 'not applicable|no[t]? applicable|out of scope|not[^.]{0,30}(surfac|match|appl)'
assert_all "no-match: no extra trace, row, question or gate is added" "$t" 'no[ *_]{1,4}(extra|additional|new)|nothing|none|unchanged' 'trace|row|gate|question|work'

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
# is handed. A stray `$1` in `write_harness_at` once wrote the repo PATH into `test_command`: the
# `red-baseline` fixture's premise (a genuinely red command) was broken while its assertions still
# passed, because the model found the committed check by itself. Two counted assertions, no dispatch.
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
  echo "  PASS: harness-parameterisation: a per-job override (red-baseline's command) lands in test_command"
else
  echo "  FAIL: harness-parameterisation: a per-job override did not land — $(grep '"test_command"' "$_hp/.harness.json")"
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
  for re in "$@"; do grep -qiE "$re" "$f" || return 1; done
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

cat >"$_ac/zero-wants.correct" <<'AC'
REFINE: 1 unresolved surfaced | 0 want-decisions asked | 1 how-decision resolved+cited | 0 ASSUMED | skip: no
The "one consumer or all consumers?" scope question is a **how-decision**: the documented shared
recipe (docs/recipes/table.md:12) dictates all consumers, so I resolved it by citation and flagged it
for ratification instead of putting it to you.
AC
cat >"$_ac/zero-wants.wrong" <<'AC'
REFINE: 1 unresolved surfaced | 1 want-decision asked | 0 how-decision resolved+cited | 0 ASSUMED | skip: no
I put the scope question to you as an open want: apply the change to one consumer or to all of them?
AC
selftest_assertion "zero-count form of a negative (refine-consistency)" \
  "$_ac/zero-wants.correct" "$_ac/zero-wants.wrong" \
  'how-decision|not ask|resolve|cite' \
  "not .{0,20}(ask|want-decision|open want)|do ?n.?t ask|without asking|rather than .{0,18}ask|not a want-decision|$RE_ZERO_WANTS"

cat >"$_ac/invest.correct" <<'AC'
T-3 INVEST self-check: **I**ndependent ✅ | **N**egotiable ✅ | **V**aluable ✅ | **E**stimable ✅ |
**S**mall ❌ | **T**estable ✅ — T-3 bundles three deliverables, so it is flagged and re-split into
T-3a/T-3b/T-3c before the split-gate ratifies.
AC
cat >"$_ac/invest.wrong" <<'AC'
INVEST: all six tickets look fine (checked as a one-line label). Nothing flagged, nothing re-split;
the ticket list goes to the gate as proposed.
AC
selftest_assertion "emphasis inside a word — INVEST letters (breakdown-invest)" \
  "$_ac/invest.correct" "$_ac/invest.wrong" "$RE_INVEST_LETTERS"
selftest_assertion "emphasis inside a word — failing Small drives a re-split (breakdown-invest)" \
  "$_ac/invest.correct" "$_ac/invest.wrong" \
  "$RE_INVEST_SMALL" 'flag|finding|caught|re-?split|not .{0,10}(small|ratif)' 're-?split|split'

cat >"$_ac/control.correct" <<'AC'
### The right-sized control — untouched
T-2 is a single right-sized deliverable: it passes **6/6** on the enumerated INVEST check and is
carried through **unsplit**.
AC
cat >"$_ac/control.wrong" <<'AC'
### The right-sized control
T-2 is a single deliverable, but I split it into two smaller tickets as well, for consistency with
the re-split above.
AC
selftest_assertion "unsplit/untouched control (invest-force-resplit)" \
  "$_ac/control.correct" "$_ac/control.wrong" \
  "right-?sized|control|single .{0,12}deliverable|passes .{0,10}(invest|$RE_INVEST_SMALL)" "$RE_NOT_SPLIT"

# A third phrasing of the same decision, seen on a later fresh run: "carried unchanged … no split".
cat >"$_ac/control.correct2" <<'AC'
**Right-sized control → carried unchanged.** PROJ-836 "downloadable PDF invoice" passed all six
(Independent under BR-1/BR-3: read-only over 832's record, adds no field). Zero letters failed → no
split. That is the non-vacuity proof — the re-split hit the failing ticket only.
AC
selftest_assertion "control \"carried unchanged / no split\" (invest-force-resplit)" \
  "$_ac/control.correct2" "$_ac/control.wrong" \
  "right-?sized|control|single .{0,12}deliverable|passes .{0,10}(invest|$RE_INVEST_SMALL)" "$RE_NOT_SPLIT"

# Emphasis sitting BETWEEN the two words of the decision — the separator class: a literal space in a
# regex ("not split") cannot match "**not** split", and neither can a literal hyphen match a space.
cat >"$_ac/control.correct3" <<'AC'
### The right-sized control: **not** split
T5 — "add a downloadable PDF invoice" — all six affirmed (S: one render path, one route). Carried to the
gate **unchanged**. That is the non-vacuous proof: breakdown re-split the ticket that failed a letter and
left the one that passed alone.
AC
selftest_assertion "emphasis between the words — \"**not** split\" (invest-force-resplit)" \
  "$_ac/control.correct3" "$_ac/control.wrong" \
  "right-?sized|control|single .{0,12}deliverable|passes .{0,10}(invest|$RE_INVEST_SMALL)" "$RE_NOT_SPLIT"

cat >"$_ac/layer.correct" <<'AC'
Verification plan — the proposed proving test is a unit test asserting layout math against a mocked
DOM. That is a **layer mismatch** on all 9 verification rows: the AC can only fail in a real rendered
DOM at 320 px. Gate 2 is BLOCKED until an automated render@320 proof (or a recorded human-approved
exclusion) replaces it. The table itself is written to the working doc.
AC
cat >"$_ac/layer.wrong" <<'AC'
Verification plan — AC-1 risk layer: computed-style; proof artifact: unit test asserting layout math
against a mocked DOM; layer-match ✅ adequate. Gate 2 passes. The proving test fails before the
change and passes after it.
AC
selftest_assertion "glyph-free layer-match failure (frontend-layer / design-layer)" \
  "$_ac/layer.correct" "$_ac/layer.wrong" "$RE_LAYER_SUBJECT" "$RE_LAYER_MISMATCH"

# A second correct wording, with neither the glyph nor the word "mismatch": the proof is REJECTED and
# clears none of the gates. The wrong transcript is unchanged.
cat >"$_ac/layer.correct2" <<'AC'
**Gate 2: BLOCKED. The proposed proving test is rejected.** AC1 is M2/M3 — risk layer
integration/runtime. A unit test against a mocked DOM sits at logic/unit, and the risk-layer floor says
a mocked-DOM proof clears none of M1–M10: `scrollWidth <= clientWidth` against a mock asserts the mock,
not the layout engine, so it would also pass pre-change. Upgraded to a tier-2 `render@320` against the
real rendered DOM.
AC
selftest_assertion "layer failure as \"rejected / clears none\" (frontend-layer)" \
  "$_ac/layer.correct2" "$_ac/layer.wrong" "$RE_LAYER_SUBJECT" "$RE_LAYER_MISMATCH"

cat >"$_ac/scaffold.correct" <<'AC'
The epic scaffold (child-ticket stubs + the BACKLOG roadmap) is committed to the shared ref **after**
the human ratifies the split and **before** the first child ticket runs `git checkout -b` — so a
child's edit of a stub reads as an edit of a committed file, not net-new authorship.
AC
cat >"$_ac/scaffold.wrong" <<'AC'
Each child ticket branches first and commits its own stub as net-new work; the BACKLOG scaffold is
committed at the end, after all the children merge.
AC
selftest_assertion "bold **before** in an ordering claim (epic-scaffold-committed)" \
  "$_ac/scaffold.correct" "$_ac/scaffold.wrong" \
  'scaffold|stub|backlog' 'commit' "$RE_BEFORE_CHILD"

# Same ordering, stated WITHOUT the word "before" — a numbered sequence plus "only then". The wrong
# transcript is unchanged, so the added alternatives are proven not to admit the wrong ordering.
cat >"$_ac/scaffold.correct2" <<'AC'
The scaffold commit is the **last act of `breakdown`**; the first child branch is the first act of the
first child's lifecycle. 3. breakdown commits the scaffold to the shared ref — 4. only then does
PROJ-833 cut `feat/PROJ-833-…` off that commit. No child branch may be cut from a tree where the
scaffold is uncommitted, and committing after is too late: the branch base is fixed the moment it
branches.
AC
selftest_assertion "ordering stated as a sequence, no \"before\" (epic-scaffold-committed)" \
  "$_ac/scaffold.correct2" "$_ac/scaffold.wrong" \
  'scaffold|stub|backlog' 'commit' "$RE_BEFORE_CHILD"

cat >"$_ac/pregate.correct" <<'AC'
Breakdown re-split the oversized ticket **before** the gate and left the control untouched. P-A does
not appear in the proposed list at all: it was replaced by four tickets *before* the split-gate, per
Step 3 — a ticket that fails a letter is re-split, not carried to the gate as-is.
AC
cat >"$_ac/pregate.wrong" <<'AC'
P-A is carried to the split-gate as proposed, with a note that it bundles four deliverables. If the
human ratifies it anyway, the re-split can happen afterwards, during the child ticket's own lifecycle.
AC
selftest_assertion "emphasis around \"before the gate\" (invest-force-resplit)" \
  "$_ac/pregate.correct" "$_ac/pregate.wrong" "$RE_BEFORE_GATE"

cat >"$_ac/verifyonly.correct" <<'AC'
Round 2 costs zero dispatches, two targeted region reads, one scoped proof re-run and one regression
scan. The full round would cost two subagent dispatches plus a blanket build/lint/test sweep. The
challenger's reconstruction and every layer-match verdict carry forward: re-deriving them would re-pay
for facts already proven at the same commit scope.
AC
cat >"$_ac/verifyonly.wrong" <<'AC'
Round 2 re-dispatches the reviewer and the ticket-blind challenger, re-derives the requirements from
the raw ticket, and re-runs the full suite to be safe.
AC
selftest_assertion "cost-contrast form of the verify-only negative (verify-only-scoped)" \
  "$_ac/verifyonly.correct" "$_ac/verifyonly.wrong" \
  'only .*(proof|affected|named|fix)|scoped|affected proof' "$RE_NO_BLANKET_RERUN"

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

# Persist this run's FRESH transcripts as the new cached GREEN baseline — but only when the WHOLE suite
# passed (never cache a transcript from a red suite) and cache reads are enabled (skipped under
# --no-cache). A cache-hit fixture already holds a valid green entry under the current hash; only fresh
# runs need writing. This never touches the committed tree — the cache dir is git-ignored.
# Read the tallies back out of their ledger files (they were written inside command-substitution
# subshells, so the shell variables never survived — v1.7.5 Fix 4).
# Under --only the run is PARTIAL, so nothing is written to the cache: `fails -eq 0` then means "the
# selected fixtures passed", not "the suite is green", and a cache entry may only ever be minted by a
# run that proved the whole suite green. Fail-safe to run, exactly like every other cache decision.
CACHE_HITS="$(tally_count cache-hits)"; FRESH_RUNS="$(tally_count fresh-runs)"
FRESH_FIXTURES="$(tally_list fresh-runs)"
if [ "$CACHE_ENABLED" -eq 1 ] && [ "$fails" -eq 0 ] && [ -z "$ONLY" ]; then
  for _name in $FRESH_FIXTURES; do
    _h="$(skills_hash "$_name")"
    [ -n "$_h" ] && cp "$(transcript_path "$_name")" "$CACHE_DIR/$_name.$_h.green" 2>/dev/null || true
  done
fi

RUN_SECS=$(( ($(prof_now) - RUN_T0) / 1000000000 ))
echo
echo "EVAL dispatch: $JOB_COUNT job(s) across $WORKERS worker(s) in ${DISPATCH_SECS}s  (total run ${RUN_SECS}s)"
if [ "$CACHE_ENABLED" -eq 1 ]; then
  echo "EVAL cache: $CACHE_HITS cache-hit(s), $FRESH_RUNS fresh run(s)  [--no-cache forces a full fresh run]"
else
  echo "EVAL cache: disabled (--no-cache) — all $FRESH_RUNS fixture(s) ran fresh"
fi
if [ -n "$ONLY" ]; then
  echo "EVAL: PARTIAL RUN (--only '$ONLY') — $skipped assertion(s) skipped, no cache written. NOT a milestone run."
fi
if [ "$fails" -gt 0 ]; then
  echo "EVAL: $((total - fails))/$total assertions pass — $fails assertion(s) failed"
  exit 1
fi
echo "EVAL: all assertions passed — $total/$total assertions pass"
