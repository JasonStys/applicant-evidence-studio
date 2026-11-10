# Portable acceptance review — 2026-11-09

## Finding and correction

The prior native smoke tested the compiled service's health, registration and
opaque envelope round-trip, and looked for a comparison label in bundled
JavaScript. Source browser tests separately exercised WebCrypto and comparison.
That did not prove the new user journey through the extracted public application.

The new controller verifies provider and independently pinned hashes, extracts
the public archive, verifies its internal executable, launches it outside the
source tree with disposable accounts, and drives its actual embedded UI.
The normal release recipe now also tests its extracted archive before upload.
Exact-source/status/event checks and draft-only idempotent uploads replace
optimizable release decisions and clobber uploads.

## Executed Windows result

The actual published 0.3.0 Windows AMD64 ZIP passed. Archive SHA-256:
`434065a4e285d2595ec82d6fa6c67894db20c285cf13378c9515a6dbd7102e79`.
Extracted executable SHA-256:
`7bd6865d87463aa5ce24d2ab950c674df23a391993ba53d2571b908d13209f0e`.
Both match the reviewed provider/sidecar evidence; the tag resolves to
`71d51b1fcd228f89d3ff81ee166bee2ce37d7a60`.

The genuine native UI journey took 9.148 seconds before teardown. Registration,
WebCrypto, two-record comparison, exact record hashes, Python assessment parity,
ciphertext-only storage, unchanged capture revision, lock/reopen and 401 for an
unauthenticated context passed. There were zero outside requests and zero
automated accessibility violations in the tested comparison card. These are
observed results, not a performance or universal accessibility guarantee.

Fifty focused independent metadata/archive/release-boundary cases passed locally.
Fixtures include altered public digests, wrong versions/architectures, duplicate
or missing checksums, path escapes, ZIP links, missing executable modes,
incomplete workflow results, wrong sources/events and incomplete platform sets.
These parser fixtures are never executed as application binaries.

## Hosted gates and limits

The added three-OS workflow must pass against the actual fixed public archives;
local Windows success does not stand in for Linux or macOS. Existing source
Python, browser, privacy, container, performance and audit gates remain required.
No existing public assets, user stores, OS security settings or real applicant
records were changed. Results and execution metadata are emitted by the workflow;
full packages and account data are not uploaded as Actions artifacts.

See [the acceptance guide](../published-acceptance.md) for the exact contract and
the distinction between portable extraction, native UI acceptance and a system
installer lifecycle.
