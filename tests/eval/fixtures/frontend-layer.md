# PROJ-301 — Settings panel must fit narrow viewports

**Requirement:** The settings panel renders without horizontal scrolling on small screens.

**Acceptance Criteria:**
- At the 320 px viewport floor, the page has **no horizontal scroll** and all content + function is
  preserved (`scrollWidth ≤ clientWidth` on the document root).
- The panel's controls remain reachable and usable at that width.
