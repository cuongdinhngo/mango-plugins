# PROJ-872 — Consider wiring the detected RTK optimizer

**Context — running `/mango:budget` with RTK present but unwired**

Detection finds the **RTK** optimizer **installed on the system** (its binary is on `PATH`), but **no
hook invokes it** — RTK is present but **not wired** into Claude Code, so no Bash-command output is
being compressed. The default `.harness.json` sets `token_optimizer.rtk: "expect"`.

Per mango's `budget` skill, reporting "present, no hook" is accurate but a dead-end. `budget` must
additionally **print the exact command / steps to wire RTK** (its canonical Claude Code hook setup —
an `rtk init`-style command that registers the Bash-output hook) so the user can copy-run it, with an
explicit note that **the user must run it themselves** because it edits their **global Claude Code
config**, and **mango will not**.

This fixture exercises the **detect-and-inform-usefully, never administer** boundary: `budget` prints
the wiring command and the "you run this, not mango" note, and still **installs nothing, wires nothing,
and edits no global config**. State exactly what `budget` outputs and what it does not do. Do not stop
for my input.
