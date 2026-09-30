# Release checklist — v0.1

This is a local portfolio demonstration release, not a production hiring deployment.

## Local gates

- [x] Validated schemas, source citations and explicit unknowns.
- [x] Identity/protected-feature exclusion and opaque provider IDs tested.
- [x] Authorization/Host/Origin/body-size/private-error boundaries tested.
- [x] Atomic imports, stale-write rejection and database reopening tested.
- [x] Factual escaped downloads and transfer qualifiers tested.
- [x] Python suite, strict types, build, formatting and source-map checks.
- [x] Chromium/WebKit/mobile workflows and automated accessibility checks.
- [x] Firefox runtime rerun finalized: seven scenarios passed outside the local sandbox.
- [x] Linux-only worker resource limits and renewed browser session links regression-tested.
- [x] Dependency audit findings corrected; no known findings after rerun.
- [x] Synthetic performance measurements recorded with scope/limits.
- [x] Only independently written code and clearly fictional examples prepared for publication; runtime/secrets/real applicant records excluded.
- [x] Published source revision's GitHub Actions jobs verified successful.

## Published validation

[Actions run 36671509486](https://github.com/JasonStys/applicant-evidence-studio/actions/runs/36671509486) completed successfully for source revision `4d129e330dd4f9a20cabfa1557c4e432861cfdd7`. All eight jobs passed: Python 3.12/3.14 on Linux, Windows and macOS; four-profile browser/accessibility/build checks; and dependency audit/ranking benchmark. The initial run failed on macOS and is retained as diagnostic history; the corrected worker limit policy and platform regression tests resolved that failure without skipping the platform.

The checked-in `docs/reports/ci-validation.json` captures this source-validation baseline. Subsequent documentation-only revisions run the same gates; the live Actions badge shows current branch status. Artifacts contain synthetic records only. No live model or real hiring outcome was evaluated.

## Production gates intentionally unmet

Organizational authentication/authorization/tenant isolation, encryption and retention integration, real accessibility/user studies, independent security review, role-rubric validation, real-world bias/error/outcome evaluation, jurisdiction-specific review and candidate correction/appeal workflow are not completed. Do not infer readiness for real hiring from green engineering CI.

## Rollback / stop-use triggers

Stop using a build if protected/private data enters a score or AI prompt, unknown facts become fabricated credentials, stale updates overwrite newer records, private data is exposed, or core intake/review/download workflows fail. Preserve the last working private data directory, restore a validated backup into a new directory and verify it before resuming. Never erase user data to make tests pass.
