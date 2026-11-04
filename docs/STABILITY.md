# Stability and release cadence

What a user can rely on between versions. This policy applies from **1.19.1** onward; the record before
it — including the one API removal, in 1.14.0 — is in [`MATURITY.md`](./MATURITY.md).

## Versioning

mango follows [Semantic Versioning](https://semver.org/) for its **public API**: the skill names and
their arguments, the `.harness.json` keys, and the counted-line grammars a project or script parses
(`RUN CONTRACT`, `CLAIMS:`, `SECTIONS:`, and the rest checked by `check_lines.py`).

- **Patch** — fixes and docs; no key, argument or grammar changes meaning.
- **Minor** — adds a skill, argument, key or line; everything that worked before still works.
- **Major** — removes or changes the meaning of anything above.

## Deprecation

A key, argument or grammar field is removed only after it has been **deprecated for at least one minor
version**: the CHANGELOG names it and its replacement, and the removal lands in a later release. A
removal without that notice is a defect in the release, not a policy exception.

## Release cadence

`main` stays the release channel (see [`CONTRIBUTING.md`](../CONTRIBUTING.md) → *`main` is the release
channel*), so the community-marketplace pin advances on every push. To keep releases readable:

- **Batch related changes into one version.** A series of fixes found in one review ships as one
  release, not one release per fix.
- **Hotfixes ship as soon as they are ready**, as a patch.
- **Pin a tag to opt out of the cadence entirely** — see *Update and pin* in the
  [root README](../README.md#update-and-pin). Every version bump is tagged `v<version>`.
