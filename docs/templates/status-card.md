<!-- TEMPLATE: Working-doc status card · Planned (phase 2) · PRINTED by `mango_state.py card <doc>` (read-only; it never
     writes the doc). Finalise pastes it at the top of the PR body; a human may paste it anywhere.
     12 rows maximum. A row whose data the doc does not carry prints `not-checkable`, never a guess,
     never "⏳" and never "none". Omit a row only when it does not apply (UI rows on a backend track).
     attended/unattended = whether the doc carries a run contract. Not verified = the waived,
     could-not-run, pending and unknown items of the doc's Disclosure and other sections — not status lines. -->
## Status card
<!-- mango:card (printed <ISO-8601 UTC> from <doc path> at sha256:<digest>; protocol <v0.2|undeclared>) -->
| | |
|---|---|
| **Ticket** | <KEY> — <title> |
| **Lane · track · profile** | <full\|lite\|epic> <attended\|unattended> · <backend\|frontend\|fullstack> · <standard\|strict\|legacy> |
| **Phase** | <phase> — waiting on <you \| autorun \| nothing> |
| **Gates** | G0 … · G1 <✅ human \| ✅ autorun \| ↩ sent back \| — open> · G2 … · G3 <✅ passed> · G4 <✅ passed \| ✅ human> · GC/GB … · GF <n> action(s) |
| **Requirements** | challenger: <n> rebuilt · <m> met · <x> not met · <u> can't tell — matrix: <rows> rows |
| **Proof** | <p>/<n> proven · <r> regression guards · <z> green@base · <e> env-fault · <f> flaky · <c> could-not-run |
| **UI** (frontend) | universal surfaces <k>/<N> · states <p>/<n> |
| **Evidence** | <a> on tree · <b> other tree · <c> unknown · <d> pre-change on base |
| **Not verified** | <from DISCLOSURE and the doc: every waived, could-not-run, flaky, pending or unknown item, by name — source named> |
| **Next action** | <one concrete action> |
