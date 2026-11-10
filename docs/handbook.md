# Applicant Evidence Studio handbook

By Jason Stys.

Compare authorized evidence against one rubric with exact citations, unknowns and private exports. Actual published 0.3.0 archives now undergo encrypted UI, record-hash, assessment-parity, locking and access-isolation acceptance on three operating systems.

Compare authorized evidence against one rubric with exact citations, unknowns and private exports. Actual published 0.3.0 archives now undergo encrypted UI, record-hash, assessment-parity, locking and access-isolation acceptance on three operating systems.

Checks the downloadable application's real privacy and review workflow, rather than inferring its behavior from source tests or bundled text.

## Read the documentation

| Edition | Audience and contents |
| --- | --- |
| [project-guide.docx](reports/project-guide.docx) | User and developer guide: purpose, current usage, design, boundaries and source references. |
| [validation-review.docx](reports/validation-review.docx) | Reviewer edition: exact tested baseline, observed workflows, dated local results and remaining limits. |
| [validation-evidence.xlsx](reports/validation-evidence.xlsx) | Two filterable Excel Tables for observed workflows and test-source inventory, with recalculating outcome formulas. |

The editable Markdown remains the maintenance source. The Word files are readable editions. The workbook is an evidence index rather than a test runner. See [publication identities and review](reports/publications.json) and the [documentation refresh record](reports/documentation-refresh-2026-11-09.md).

## Current usage and help

[README quick start](../README.md) is the entry point. Use the project-specific guides below before changing inputs, operating modes or deployment assumptions.

### Usage and operations

- [operations](operations.md)
- [release](release.md)
- [releases/v0.2.0](releases/v0.2.0.md)
- [releases/v0.3.0](releases/v0.3.0.md)
- [user guide](user-guide.md)

### Design and contracts

- [architecture](architecture.md)
- [research](research.md)

### Security and validation

- [validation](validation.md)

## Historical results and reproduction

The reviewed source is [`2742474af85014e849fe38796be1cdb8215e140e`](https://github.com/JasonStys/applicant-evidence-studio/tree/2742474af85014e849fe38796be1cdb8215e140e). The observed functional workflow baseline is `2742474af85014e849fe38796be1cdb8215e140e`; those observations are recorded at `2026-11-10T07:44:17.263414+00:00`. They do not certify an unrun later revision.

- [Detailed recorded validation](reports/codeql-findings-2026-11-10.md)
- [Current Actions](https://github.com/JasonStys/applicant-evidence-studio/actions) records later integration checks separately.
- Preserve dated measurements and follow the existing testing guide to reproduce them; a test-source inventory alone does not establish execution.

## Practical boundaries

- Evidence coverage is advisory, not applicant suitability, a hiring decision, fairness certification or legal-compliance assurance; original applications require human review.
- Comparison captures are unencrypted identifying files. Observations are transient and prior downloads cannot be revoked.
- The accepted public application remains 0.3.0 at its original release source; newer source adds acceptance and release guards without replacing those bytes.
- Unsigned portable applications trust the local OS and retained recovery material; extraction/UI tests do not certify signed installation, a clean-machine lifecycle or public hosting.

## Maintaining these editions

Update the editable usage/design/test documents first. Rebuild and visually review every Word page and workbook tab before replacing an edition; verify the exact binary digests and evidence source in publications.json. Keep account data, logs with secrets, installed-app state and private test stores out of documentation. Source and release assets retain their existing security and licensing boundaries.
