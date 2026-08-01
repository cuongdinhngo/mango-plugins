# PROJ-626 — Add a saved-view selector to the report filters

**Requirement:** The report filter bar offers a saved-view selector.

**Acceptance Criteria:**
- Choosing a saved view applies its filter set, proven by a counted assertion.

## Context — two RECURRING promotion candidates at finalise (INJECTED)

Review was clean and this run reached finalise. The dedup step produced **two promotion candidates** —
each already recorded and seen again:

```
### CLM-061 — the export helper REJECTS an empty filter set, so a caller must always pass at least one filter
- type: 2 generalisable-heuristic
- status: confirmed
- evidence: "stated in the PROJ-333 write-up, repeated in PROJ-370, PROJ-391 and PROJ-455"
- destination: rulebook_path
- seen: PROJ-333, PROJ-370, PROJ-391, PROJ-455

### CLM-062 — a filter set is "reasonable" when the resulting report feels responsive to a real user
- type: 2 generalisable-heuristic
- status: confirmed
- evidence: "agreed in review on PROJ-592 and PROJ-448"
- destination: rulebook_path
- seen: PROJ-592, PROJ-448
```

CLM-061 is the **most-repeated** claim in the file: four sightings. Every one of those sightings **restates
it**; not one of them records a check. This run finally ran the one-line check the claim implies — calling
the export helper with an empty filter set — and it **returned the full unfiltered report without error**.
The claim has been false since it was first written down, and it was on its way to becoming a rule
precisely because it was repeated so often.

CLM-062 has two sightings and no dispute — but there is no grep, command, or test that could disprove it:
"feels responsive to a real user" has no measurable form.

Run the learning loop from the dedup step onward. For each candidate, state what the falsification check
asks, what it finds, and the **outcome for its promotion**. Then state where the falsification check sits
relative to the human ratification gate, and what `FALSIFY:` and `PROMOTION:` report. Say plainly what
recurrence does and does not measure.

Do not stop for my input; show the artifacts you would produce.
