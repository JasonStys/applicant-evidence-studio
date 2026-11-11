# Native application ownership and packaging

Created by Jason Stys. This guide describes the 0.3.1 native source contract.
Published 0.3.0 downloads remain immutable and retain their separate acceptance
contract in [published-acceptance.md](published-acceptance.md).

## Start, use and stop

Verify and extract the official OS/architecture archive into a folder you own.
Launch ApplicantEvidenceStudio. Its small native window opens the existing
private-account browser application on an OS-assigned `127.0.0.1` port. Open
workspace reopens that address; an unavailable default browser leaves the address
visible. Help explains login, the separate vault phrase, backups and advisory
review. Runtime notices displays the actual bundled license texts.

Closing a browser tab does not quit the service. Use Quit application or close
the native owner window. Both stop admission of further service work and wait
for active requests to complete. The window and profile ownership remain until
the service thread finishes. There is no HTTP quit endpoint and no forced-exit
deadline. A stuck request therefore requires investigation instead of silently
discarding its write. A second instance using the same account directory is
refused while the first instance owns it.

The browser retains real registration, password recovery, WebCrypto vault unlock,
authorized document import, evidence review, coaching, two-record comparison,
encrypted saves/backups and account deletion. The native shell does not receive
the vault phrase or replace the browser's encryption. A comparison remains an
advisory review of evidence, with original sources and explicit unknowns.

## Existing accounts and files

The data paths are unchanged: `%LOCALAPPDATA%\ApplicantEvidenceStudio` on Windows,
`~/Library/Application Support/ApplicantEvidenceStudio` on macOS, and
`${XDG_DATA_HOME:-~/.local/share}/ApplicantEvidenceStudio` on Linux. There is no
account-schema or ciphertext-format migration in 0.3.1. Keep encrypted exports
and a stopped-service backup of the account directory before an upgrade. Retain
the old executable until the new version can sign in and unlock a test account.

The owner lock and fixed SQLite database, journal, WAL and SHM names must be
ordinary single-link files when present. Linked/junction/reparse ancestors and
the frozen program/extraction trees are refused as data locations before account
initialization. Ordinary recovery files are retained for SQLite. The app does
not delete or recreate a database to work around a failure. These checks prevent
accidental aliases; they do not isolate a user from another malicious process
with the same operating-system privileges.

## Source and runtime identity

The archive contains exactly the executable, LICENSE, INSTALL.md,
NATIVE_SOURCE.json and NATIVE_NOTICES.txt. Its SHA-256 sidecar identifies the
archive and executable. NATIVE_SOURCE records the exact Git source, dirty state,
product version, actual Python/Tcl/Tk patch levels, platform, machine and bounded
UI/license resource hashes. Startup checks the embedded manifest and actual
extracted resources before opening an account store. Public native health reports
only whitelisted product/version/runtime/source fields, with no data paths,
environment variables, account aliases, passwords or vault contents.

Windows CPython 3.14.10's DLL is independently pinned to the verified official
SDK. On macOS, PyInstaller repairs library load paths and ad-hoc signs collected
libraries; this changes the original SDK bytes. The builder retains the SDK
digest separately, measures the actual processed library in the frozen archive,
binds that digest on a second build pass and requires stable bytes plus an exact
embedded/sidecar manifest match. Startup checks the actual processed payload.
This does not turn an unsigned portable package into a signed/notarized app.

All build outputs are fresh directories. Dirty local development candidates are
explicitly labeled and cannot pass CI release acceptance. Runtime notices include
the actual loaded Tcl/Tk notice sources, Python and the installed runtime
dependency graph; packaging fails when a required notice cannot be resolved.

## Validation and releases

The original six Python platform/version lanes, full browser/accessibility/private
account matrix, dependency audits, benchmark and non-root container checks remain.
Real owner-window tests require a native display; Linux CI uses mandatory Xvfb.
The new read-only current-native workflow builds and extracts actual apps on
Windows AMD64, Linux x86-64 and macOS ARM64 and exercises their real encrypted UI.
Linux builds use Ubuntu 24.04; older Linux distribution compatibility is not
claimed. No native binary is replaced by a source server when a check fails.

The release workflow requires exact-main source, original published-package,
current-native and CodeQL workflows, plus processed CodeQL results for all three
configured languages and no open default-branch alerts. All three new platform
packages must pass actual embedded identity and normal-exit acceptance. Uploads
are draft-only, reject different existing bytes and require provider digests.
The workflow verifies the complete six-asset draft and leaves it unpublished for
independent download and installed-app testing. It has no publish operation.

Acceptance uses only synthetic applicants and disposable account stores. The
stdin quit command is available only with an explicit temporary data directory,
no-browser mode and a random 64-hex test nonce. It invokes the same native Quit
handler; no public listener exposes this command.
