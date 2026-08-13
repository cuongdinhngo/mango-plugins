# PROJ-711 — Add a responsive summary panel to the account overview

**Requirement:** The account overview shows a summary panel that reflows at 320 px and has no horizontal
scroll at any declared breakpoint.

**Acceptance Criteria:**
- No horizontal scroll on any reachable surface at 375 px, 768 px and 1280 px, and the panel reflows at the
  320 px floor.

## Project state (INJECTED — treat as given)

- `config.track` is `frontend`. `config.breakpoints` is `[375, 768, 1280]`. `config.design_doc_path` is
  `DESIGN.md`, which does not yet exist.
- Gate 1 has cleared and analysis emitted `TRACK: frontend` and `SURFACES: 4 — overview, detail, settings,
  export`.
- The proposed proving test is a **unit** test that mounts the panel against a mocked DOM and asserts a
  class name.

Run the mango design skill on this ticket. Before producing the Phase-2 artifacts, state which files you
read and why. Then produce the verification plan and the Gate-2 verdict, and answer:

1. Which mango file carries the frontend rules this phase must apply, and did you read it? Name it.
2. What is the risk layer of the no-horizontal-scroll AC, and does the proposed unit test match it?
3. What must exist before the verification plan is named, and what happens if it does not?
4. How many rows does the plan carry for the app-wide AC, and against which denominator?

Do not stop for my input; show the artifacts you would produce.
