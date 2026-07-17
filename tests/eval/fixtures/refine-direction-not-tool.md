# PROJ-713 — Improve the slow legacy search

**Requirement:** The legacy search is slow; make it better.

## Context

refine exposes a solution **DIRECTION** whose trade-offs a non-technical user can feel — e.g. **wrap**
the existing legacy search (cheaper, keeps behaviour) vs **rebuild** it (costlier, changes behaviour).
That is a loại-A WANT the user can answer immediately.

refine must **stop at that direction** and **NOT pin the specific TOOL / library / search engine** that
implements it — tool selection is **analysis's** job. The test: if the user can answer immediately it
is a direction (refine); if they would say *"I don't know, help me decide"* it is a tool/how (analysis,
or refine self-resolves it if derivable). This fixture asserts refine stops at direction (wrap vs
rebuild) and does not pin a tool.
