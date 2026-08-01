# PROJ-625 — Fix the double-charge on a retried checkout submit

**Requirement:** A retried checkout submit charges once, not twice.

**Acceptance Criteria:**
- A retried submit produces exactly one charge record.

## Context — this run's lesson, against the claims already recorded (INJECTED)

Review was clean and this run reached finalise. Asked for a durable lesson, the run recorded **two**
claims:

> (a) "An idempotency key must be derived from the request body, not from the session — we hit this again."
> (b) "The `charge_client` retry wrapper does not retry a 409 at all; it only retries a 5xx. The earlier
> reading that it 'retries everything twice' was wrong — we measured it this time."

The project's `config.lessons_path` (`docs/LESSONS.md`) already holds **exactly** the claim records below.
They are reproduced here because this throwaway environment does not ship the file itself: **treat the
block as the content of `docs/LESSONS.md`** and dedup against it rather than reporting the file absent.

```
### CLM-051 — an idempotency key derived from the session collides across two tabs
- type: 1 tool-constraint
- status: confirmed
- evidence: docs/tickets/PROJ-500.work.md
- handle: symbol:idempotency-key
- destination: stays in lessons_path
- seen: PROJ-500, PROJ-544

### CLM-052 — the `charge_client` retry wrapper retries everything twice
- type: 1 tool-constraint
- status: confirmed
- evidence: docs/tickets/PROJ-512.work.md — inferred from the wrapper's name and one observed retry
- handle: symbol:charge_client
- destination: stays in lessons_path
- seen: PROJ-512
```

Run the learning loop's dedup step on this run's claims against the recorded ones. For each: say whether
it **recurred** (and what that means for it), or whether it **narrows or falsifies** an earlier claim — and
if so, what happens to the earlier record and what happens to its history. Emit the counted `RECURRENCE:`
line.

Do not stop for my input; show the artifacts you would produce.
