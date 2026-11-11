# Installed Windows 0.3.1 validation · 11 November 2026

By Jason Stys. These observations refer to the actual independently downloaded, published **0.3.1** application built from `c3d44882ee39209b3a9fbbe884e1177cc78359e5`. Historical Office editions, failed-run evidence and published assets remain unchanged.

## Observed validation

**Installed encrypted UI: Passed.** Real WebCrypto, exact record hashes, Python parity, read-only comparison, accessibility, lock/reopen and unauthenticated refusal passed; zero outside requests and normal exit 0.

**Old-to-new vault: Passed.** An immutable 0.3.0 compatibility binary created and edited a synthetic encrypted vault. Installed 0.3.1 used the same login and phrase and retained its exact edited record hash.

**Source and packages: Passed.** Exact-main CI and processed three-language CodeQL passed. All three real native builds and final draft verification passed; all six independent asset downloads matched provider SHA-256.

**Installation and icons: Passed.** A fresh per-version Windows folder and individual Desktop/Start-menu targets were verified. Normal accounts and Docker were unchanged; default-profile shortcut activation remains separately untested.

## Illustrated workflow and implementation

The [four-page application guide](windows-application-guide-0.3.1.docx) contains two actual installed-app screenshots, a worked user journey, an important immutable-source code excerpt and detailed results/operating limits. Every final page content was inspected and the OOXML schema passed. The [manifest](windows-application-guide-0.3.1.json) binds document, screenshot, source and reviewed-page identities. Prepared examples are inputs inside the actual application, never separate demo apps.

## Installation, data and limits

Download the matching archive and checksum from official Releases, extract it and launch the included application. Retain old versions and stopped-profile backups.

Open the individual Desktop icon, read Help and runtime notices, and use the application's own Quit controls. Prepared examples are inputs inside the actual app, never separate demo applications.

Advisory evidence comparison requires human source review; absent evidence is unknown ability, and education is not converted into paid employment. This app does not make a hiring decision.

Browser-side encryption protects stored workspace content; the trusted OS owner can still inspect the local machine. Exported comparison JSON is plaintext. Downloads are unsigned, with no notarized macOS bundle or public host provisioned.

The legacy 0.3.0 compatibility test required its explicitly recorded historical process cleanup; normal owned exit is proven for 0.3.1. No previously located user installation is claimed for that separately downloaded baseline.

Individual Desktop and Start-menu targets were read-back verified. Actual installed-executable testing is distinct from normal default-profile shortcut activation, which was not independently exercised. Normal profiles, account data and Docker were not changed. This documentation revision must pass its own current hosted workflows and processed security analysis; historical runtime evidence does not certify later source changes.
