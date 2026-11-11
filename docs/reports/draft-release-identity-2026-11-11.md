# Draft release identity correction — 11 November 2026

By Jason Stys. Native update main `8f4a0fa7b8aae02de8e69ba1eed7bf67e47408e4`
passed all original source/privacy/audit/container checks, current native
Windows/Linux/macOS workflows, immutable 0.3.0 acceptance and processed CodeQL.
The subsequent [draft release run](https://github.com/JasonStys/applicant-evidence-studio/actions/runs/42998692973)
passed the exact-source/security gate and created an unpublished 0.3.1 draft,
then stopped before every build/upload job.

The release guard requested `releases/tags/v0.3.1`. GitHub returned 404, including
in a separate authenticated maintainer read. The authenticated release listing
returned the correct empty draft, ID 441495787, target `8f4a0fa`. This is a release
lookup defect, not evidence that the three tested applications failed. The
original failed run and empty draft are retained; zero assets were uploaded.

The corrected guard selects exactly one matching version from a bounded
authenticated release listing, then rereads and verifies its numeric release ID,
draft/stable state, exact version and source before every operation. It creates a
missing draft with structured JSON and uploads only fixed accepted filenames to
GitHub's fixed official upload host using that verified ID. It does not use a
published-tag lookup for an unpublished draft, overwrite assets, retarget an
existing release or publish automatically. The final read-only verifier also
receives the push-level release visibility GitHub requires to list unpublished
drafts; it has no publication operation. The broader workflow's default remains
read-only, and checkout never persists credentials.

Regression controls cover the real-shaped unpublished draft, malformed or
incomplete lists, duplicate versions, invalid numeric IDs, identity changes,
published/prerelease/different-source rejection, read-only resume and literal
multiline notes in a structured create request. The full Windows Python suite
passed 223 tests with 92.81% branch-inclusive coverage against the unchanged
85% minimum. Ruff checks, formatting and the generated code index passed.
All existing source/asset/native security gates remain required.
Fresh hosted validation is pending for this
correction. An existing empty draft with the earlier source must be explicitly
reviewed before any source retarget; the workflow refuses that mismatch.

No installed application or existing user account was opened or changed while
diagnosing this failure. Docker and published 0.3.0 assets were unchanged.

API contracts: [GitHub release listing and draft visibility](https://docs.github.com/en/rest/releases/releases#list-releases)
and [release asset uploads](https://docs.github.com/en/rest/releases/assets#upload-a-release-asset).
