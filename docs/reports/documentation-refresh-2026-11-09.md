# Documentation refresh — 2026-11-09

By Jason Stys.

This documentation-only edition describes source `2742474af85014e849fe38796be1cdb8215e140e`. It does not change application behavior, accounts, private data, installers or published releases.

## Published editions and completed review

| File | Bytes | SHA-256 | Reviewed scope |
| --- | ---: | --- | --- |
| [project-guide.docx](project-guide.docx) | 154843 | `c50699ff90bb425b89b53f8647ead97dff779d6d5f03935cc623de2f4d04cb5f` | 7 pages, each viewed individually |
| [validation-review.docx](validation-review.docx) | 46802 | `6059864d06a4c95eec4f3394637317a385c0e361225dae8f6413d09c7484eb5e` | 6 pages, each viewed individually |
| [validation-evidence.xlsx](validation-evidence.xlsx) | 7523 | `3329055813782726342abc966c077dbae42071a83f31c7a4197959a6436d9693` | Both tab previews; two actual Excel Tables/autoFilters; four formulas; failure-change/restore recalculation and zero formula errors |

Word review checked plain black titles, readable pagination, whole table rows, source references, practical limits and absence of clipping or overflow. Render receipts were matched to the current DOCX digest before approval. Workbook review inspected both tab previews and actual exported Table/autoFilter elements; recalculated success/failure summaries were compared independently with workflow metadata. Static previews do not draw Excel dropdown arrows; the exported workbook contains the actual filters.

## Evidence and change boundary

- Functional baseline: `2742474af85014e849fe38796be1cdb8215e140e`.
- Workflow observation: `2026-11-10T07:44:17.263414+00:00`; exact run URLs and source identities remain in [publications.json](publications.json).
- Local document-package validation verifies exact copied bytes, Office ZIP integrity, approved page/tab identities and internal documentation links. Repository-specific documentation and source-policy commands are run separately and recorded in the integration handoff.
- Source/index metadata is regenerated using the repository’s existing tools. Existing privacy, security, coverage and workflow gates are retained.
- PR and later main workflows must pass independently. This record does not claim future or unrun integration CI success.

## Interpretation

The Word files document the cited source; dated source reports retain their original execution scope. A passing workflow is distinct from completed analysis with zero findings, and neither establishes production suitability. The Excel source inventory is not a per-test execution report. Checksums identify exact bytes, not a signature or publisher attestation.

Use the [handbook](../handbook.md) to choose usage, design, security and test documentation. Keep editable Markdown and reviewed editions together; do not replace historical measurements with undated claims.
