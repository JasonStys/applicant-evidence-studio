# Test strategy and observed validation

## Scope and acceptance criteria

Risk-driven tests emphasize job-relevant evidence boundaries, unknowns, truthful downloads, parser isolation, persistence and human review. A passing suite is engineering evidence, not validation that this tool predicts job success or produces unbiased hiring outcomes.

Acceptance: ranking must ignore identity/raw personal text, duplicate claims must not multiply scores, custom sensitive/proxy criteria must fail schema validation, source references must resolve, transfers must remain explicit, unsupported parsing/model output must fail safely, authorization/private error boundaries must hold, edits must be atomic/revision-checked, and key reviewer/applicant workflows must work in real browsers.

## Traceability

| Requirement / risk | Evidence |
| --- | --- |
| Weighted coverage, caps, ties, duplicate invariance | `test_review.py`, `test_operations.py` expected values/property tests. |
| Personal-text/identity invariance and protected criteria | 100-example Hypothesis test plus schema-negative cases and opaque-ID payload test. |
| Coursework/project quality without fictional employment years | Domain tests and explicit separated employment duration. |
| Transfers/uncertain degree outcome | Domain/download/API tests and browser source review. |
| TXT/DOCX/PDF, unknowns, malformed input | `test_ingest.py`: extraction fixtures, UTF-8, blank/encrypted PDF, page limits, XML entities, macros, ZIP ratios, binary/oversized input. |
| Private API authentication, Host/Origin, XSS and size | `test_api.py` boundaries and `test_review.py` escaping tests. |
| Atomic batch, stale edits, persistence/restart | Transaction and compare-and-swap integration tests; resource warnings promoted to errors. |
| Provider consent/privacy/citations/output bounds | Mocked Ollama/compatible protocol and malicious URL/output tests; no paid calls. |
| Reviewer/coaching/intake/rubric/download/session flows | Seven Playwright scenarios across Chromium, Firefox, WebKit and mobile Chromium. |
| Worker portability | `test_platform.py` verifies Linux-only resource caps and Windows/macOS parent-timeout behavior; the Actions OS matrix exercises real extraction. |
| Accessibility/responsiveness | axe WCAG 2 A/AA and 2.1 AA tags on queue/record/coaching plus overflow checks. Not a complete accessibility certification. |
| Algorithmic performance | Three timing repeats and traced Python allocation peak for 100/1,000/10,000 synthetic records. |
| Dependencies/code/docs drift | Ruff, strict TypeScript, build, npm audit, pip-audit, exact source-map checks. |

The supplied broad testing taxonomy informs selection: unit/component, integration/API, functional/system/browser, regression, static analysis, CLI, property-based, input-security, interoperability, portability, performance and automated accessibility checks are implemented where relevant. This repository does **not** claim all possible test categories, a professional penetration test, HIL, mutation testing, long-duration soak tests, real applicant outcome validation or real user research.

## Development observations (2026-09-29 local date)

Windows 11 / Python 3.14.6 / Node 24; local Python suite: **69 passed**, combined line/branch coverage **95.06%**, 85% CI floor. The suite promotes SQLite `ResourceWarning` to errors. A remaining Starlette test-client deprecation warning about its httpx compatibility is recorded, not hidden; tests still pass.

Final local four-browser suite: **28 scenarios passed** (36.5 seconds) outside the restricted process context, including the transfer editor, renewed session links and latest UI build. Initial restricted Firefox launches failed before creating a browser page, not from an application assertion. Final publication results and CI links are recorded in [release.md](release.md).

Local dependency checks after updates: npm audit reports no vulnerabilities; pip-audit reports no known vulnerabilities; pip check reports no broken requirements. Audits are time-specific advisories, not guarantees of security. The initially installed pip/pytest development-tool vulnerabilities were corrected by updating to pip 26.2 / pytest 9.0.3; no findings were waived.

## Benchmark snapshot

| Synthetic records | Median scoring/sorting time | Approx. records/s | Peak traced allocations |
| --- | --- | --- | --- |
| 100 | 0.00314 s | 31,844 | 228,372 bytes |
| 1,000 | 0.03747 s | 26,691 | 2,398,616 bytes |
| 10,000 | 0.35615 s | 28,078 | 24,724,448 bytes |

Three repeats, fixed six-case synthetic distribution, no production data. Tracing is a separate run; it measures Python allocations, not full-process RSS. Excludes database load, large source records, parsing, network/AI and concurrent users. The 30-second CI regression ceiling is deliberately generous and is not an SLA. See `docs/reports/benchmark-windows.json` and generated Actions artifacts.

## Defects found and prevented

Database transaction contexts initially committed/rolled back without closing connections; a closing context manager and resource-warning gate now prevent recurrence. AI payloads originally retained caller-chosen evidence IDs; temporary aliases and a regression test prevent identity leakage. Mobile intrinsic widths caused controls to overlap; compact fixed-layout tables and bounded navigation now pass real touch/mobile scenarios. Cross-browser tests originally assumed imports from earlier scenarios did not exist; tests now filter the fixed synthetic baseline instead of depending on test order. These fixes were made before publication.

The initial published Actions run exposed a macOS extraction-worker failure: address-space limits were being applied on every non-Windows platform despite differing resource-limit semantics. Hard CPU/address-space limits now apply only on Linux; macOS/Windows retain bounded input and the parent-enforced timeout. Platform regression tests accompany the fix. Opening a renewed authorization fragment in an existing browser tab also exposed a stale-session issue; the UI now reloads on a new session link, tested in all four browser profiles.

## Remaining validation gaps

Live AI quality is not measured without an explicitly configured model; adapters are contract-tested with mocks. Arbitrary resume interpretation, OCR/images/equations, automatic code-portfolio execution/review and sensitive-trait inference are not implemented. Native mobile hardware, assistive technologies, long-term/high-concurrency production load, formal security review, bias/outcome studies, legal compliance and actual organizational access controls remain outside this prototype's validation. No real applicant data was used in published tests or CI.
