   **Surface inventory — for a universal / app-wide FRONTEND requirement, the denominator N comes
   from the CODE, never the ticket.** When the track includes frontend (confirmed at step 10) and a
   requirement is phrased all/every/no **or is inherently page-wide** (no horizontal scroll, reflow,
   focus-visible, contrast — anything that holds across the UI), enumerate **every reachable surface**
   — each route, full-window overlay, modal, and major mounted state — and set **N = |surfaces|**.
   Source the surface list from the opt-in `sitemap` (`config.docs_dir/sitemap.md`) **if present**;
   if it was never generated, run a lightweight read-only **"enumerate reachable views"** sub-step
   (inspect the routing/entry points). The ticket's examples are a **hint, never the denominator** —
   counting only the surfaces the ticket named is exactly the failure this removes. Emit it as a
   counted, challenger-checkable artifact (like `TRACK`):

   `SURFACES: <N> — <surface>, <surface>, …`

   A surface the change *can* affect that ends up with neither a proof nor a recorded exclusion makes
   the requirement **incomplete** — later phases (design/execute/review) prove against this N.

