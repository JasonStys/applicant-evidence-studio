# Native application validation — 11 November 2026

Author: Jason Stys. Status: local development candidates validated; clean-source
hosted/release/installed-upgrade verification is recorded separately when it
completes. No existing user account was opened or migrated for these tests.

## Local evidence

The initial full Windows CPython3.14.10 source run passed **207 tests**, including
the isolated parent that requires all **13 actual Tcl/Tk notice cases** to pass
with no retries or skips. Combined line/branch coverage was **93.04%**, above the
unchanged85% floor. Real Tk tests exercised Help and every normal-close control,
duplicate profile ownership, actual hard-link/junction refusal, account reopen
and a real HTTP request barrier that retains the window/lock until its write
completes. The run recorded one upstream Starlette TestClient deprecation warning
and one pytest cache-directory creation race between parent/child tests. Neither
was hidden or counted as a failed assertion. The isolated notice interpreter now
uses its own temporary cache directory. The corrected full run again passed
207 tests at93.04% and recorded only the upstream deprecation warning.

The full browser rerun passed **36 legacy/developer workflows** and **32 private
account workflows** across Chromium, Firefox, WebKit and a mobile Chromium layout.
Independent comparison and source-index-reader suites each passed8 tests. The
first browser run failed8 heading assertions because a version-edit operation
had corrupted their original UTF-8 middle-dot text; the actual application
rendered the correct headings. The original Unicode assertions were restored,
without changing selectors' meaning, product behavior, timeouts or assertions.
Failed traces/logs were retained privately. All68 scenarios then passed.

Three explicitly dirty development freezes were preserved. The third candidate
contained CPython3.14.10 and Tcl/Tk9.0.4, the actual patched Windows DLL, bounded
resource/source metadata and complete notices. Its archive SHA-256 was
`e0fa49a45354965b56c9f9bf6ebcfbae2b740a461734277ccd74057471e9c1f6`;
EXE SHA-256 was
`98b5f1901f1ebccc312bc7a50eb77275b0913b20e4670e406396dfd4e4c3a534`.
These identify a development candidate, not a reviewed release or installed app.

The actual candidate EXE passed the original eight HTTP/account/ciphertext smoke
assertions and normal owned exit0. The five-member archive was safely extracted
and the real embedded UI completed WebCrypto registration/unlock, two fictional
records A101/A102, exact captured-record hashes, independent Python assessment
parity, read-only comparison capture, encrypted-only persistence, lock/reopen and
unauthenticated denial. It made **zero outside resource requests** and had
**zero automated comparison-card accessibility violations**. Embedded native
health identity matched the archive manifest. After normal Quit the process
exited0 and its local listener was unavailable. The UI journey took8,919ms on
this PC; that diagnostic is not a product latency guarantee.

## Gates retained and added

The first hosted draft at`3879be3e076242b085adfa69e56902b1c2712ad2` passed
all six Python lanes, all browser/privacy/audit/container checks, processed
CodeQL, immutable0.3.0 acceptance on three OSes, and current native Windows/Linux.
The [macOS native job](https://github.com/JasonStys/applicant-evidence-studio/actions/runs/42992812670)
built successfully but the EXE exited before readiness. Its log is retained as a
failed run. Startup now emits a fixed nonprivate phase/class code; no private
exception message or path is logged. The synthetic acceptance paths are resolved
to their actual owned temporary directory, preserving production ancestor-alias
refusal. On an OS that supplies a temp alias, the real EXE must first refuse that
alias at profile admission with no files created, then pass the canonical-path
account journey. The original60-second readiness/20-second normal-exit limits,
runtime hashes and all platforms remain required. Fresh hosted proof is pending;
the first failure's precise phase was not captured, so its cause is not assumed.

After diagnostic and canonical-temp regression additions, local source testing
passed209 tests at93.31% with the original85% floor. The separate fresh-service
Firefox repeat passed all16 scenarios. Python/npm dependency audits reported no
known findings in their audited installed/locked graphs. The original10,000-row
synthetic benchmark ran with a274.39ms median; this is a local diagnostic, not a
capacity or response-time guarantee.

The existing source, four-profile browser, privacy, schema, independent comparison,
audit/performance, container and immutable0.3.0 published-download checks remain.
Current native validation builds real apps on all three desktop platforms; Linux
uses an actual Xvfb display. No coverage floor, test assertion or readiness limit
was weakened to accommodate the new shell. Test-only forced termination is a
failure-cleanup path and cannot authorize a current native release.

Release uploads require clean exact-source metadata, actual extracted compiled
UI, normal exit0 and embedded/sidecar identity equality. Source workflow success
alone is insufficient: processed exact-source CodeQL for Python, JavaScript/
TypeScript and Actions plus no open default-branch alert is required. The release
workflow verifies all six immutable draft assets and does not publish them.

## Limits and pending delivery evidence

Local development proof does not establish clean hosted three-OS success,
independently downloaded installation, old-to-new account preservation or normal
desktop-shortcut activation. Those stages are required before delivery and will
receive fresh source/asset/run identities. No real applicant, API provider,
payment service, Docker configuration or existing account store was used. Current
engineering checks do not establish real-world hiring fairness or production
hosting readiness.
