## Subagent git isolation — never mutate shared git state

> **A subagent inspecting a branch works from refs or an isolated worktree; it NEVER mutates the
> shared working tree's git state.**

Branch/diff inspection is **ref-based** — `git diff <base>..<branch>`, `git show <branch>:<path>`,
`git log <base>..<branch>` — or **worktree-isolated** — `git worktree add <scratch> <branch>`, removed
afterward. A subagent — the `reviewer`, the `challenger`, or any review-phase worker — **MUST NOT** run
`git checkout`, `git switch`, `git stash`, or any HEAD/index-mutating git in the **shared working
tree**: that switches the live checkout off the in-progress branch, strips the in-progress source files
from disk, and strands the working doc — a real corruption + recovery detour. If a subagent must
**run** the suite against a branch (not just read it), it does so in an isolated `git worktree` / clone,
never the live checkout.

**Worktree ≠ environment-equivalence — carry the untracked env, or run in place.** A fresh worktree
holds only **tracked** files, so it has none of the project's required **untracked** environment (`.env`
/ local config, local certs, installed deps, built assets) and the app cannot boot. Before running a
suite in one, either **run read-only in place** when the tree is already at the reviewed SHA (preferred),
or **carry the required untracked env into the worktree**. **Sanity rule:** a **near-total** suite
failure inside a fresh worktree is an **env-fault** (missing untracked files) **until proven otherwise**
— it is **never** reported as a review finding or a regression. This reclassifies an environment
artifact only; it never suppresses a real finding — a *partial, targeted* failure inside the change's
blast radius still counts, and once env parity holds the same result is reportable.

This is the **same root cause** the v1.6.1 eval-isolation invariant fixed for the eval path (a process
running stateful git in a shared cwd) — **one principle, two surfaces** (review and eval). Enforced at
`review` and the `reviewer` / `challenger` briefs; guarded by `scripts/validate.py` (the review
git-isolation + env-parity tokens) and, on the eval surface, the `assert_checkout_clean` guard in
`tests/eval/run.sh`.
