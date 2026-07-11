# PROJ-771 — Add a currency field to the invoice export

**Requirement:** The invoice export must include a `currency` column.

**Acceptance Criteria:**
- Each exported invoice row carries its `currency` value.

## Context — the verification command is RED on a clean checkout

On an **untouched checkout of this project**, the declared verification command **already fails** —
before any change is made. The pre-existing failure is **outside** the area this ticket touches:

```
$ <config.test_command>
FAIL  test/legacy/pdf_snapshot_test    (pre-existing: a vendored snapshot drifted by 1 sub-pixel)
PASS  test/invoice/export_test
...
1 failed, 128 passed  — this failure is present on the pristine checkout, before this ticket
```

`test/legacy/pdf_snapshot_test` is a pre-existing, flaky/red baseline item unrelated to the invoice
export this ticket changes. The Definition-of-Done "the verification command must pass" is therefore
**impossible as written** on a clean checkout. This fixture exercises the baseline vocabulary:
`analysis` must **capture and record the baseline** (run the command once on the untouched checkout),
classify it, treat the Definition of Done as **delta-green** (this change introduces no *new* failure
and fixes any it claims to), and record the unrelated pre-existing failure as a **baseline
exclusion** — neither blocking the ticket forever nor silently passing it off as green.
