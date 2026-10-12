# Install Applicant Evidence Studio — Jason Stys

## Website and installed web app

Use the operator's **verified HTTPS URL**, not an unofficial clone. Create a
non-identifying account alias and a unique login password. Save the once-shown
login recovery code privately. Choose a **different** vault phrase: at least 20
characters, preferably six randomly generated words kept in a password manager.

On desktop/Android browsers that support installation, use the browser's Install
app command. On iPhone/iPad, use Safari's Share → Add to Home Screen. Browser
support varies; ordinary browser use remains available. Installed web apps use
the same account service and require connectivity. Private responses are never
cached by a service worker. This is not an offline sync application.

## One-file local desktop application

Download the matching OS/architecture archive and `.sha256` from the official
[releases](https://github.com/JasonStys/applicant-evidence-studio/releases).
Verify its checksum **before launching**. Extract the archive, place it in a
folder you control and launch `ApplicantEvidenceStudio` (Windows: `.exe`). It
includes Python, the account service and UI; no Python/Node/npm setup is needed.
On macOS/Linux the archive contains a command-line executable; it is not a
notarized `.app` bundle or a distribution-specific package. These builds are
**unsigned**. Checksums verify integrity, not independent publisher identity.
Do not defeat your operating system's warnings blindly.

Windows checksum: `Get-FileHash -Algorithm SHA256 .\download.zip`.
Linux: `sha256sum download.tar.gz`. macOS: `shasum -a 256 download.tar.gz`.
Compare the complete value with the official release's manifest.

The application launches your default browser and listens only on `127.0.0.1`
at an OS-assigned port. A small server/console process remains running; closing
it stops the local service. No telemetry, automatic updates, browser extensions,
ads, source lookups or external AI calls are installed. A restart may choose a
different port; sign in again and unlock with your original vault phrase.

Local accounts are independent from hosted accounts. To transfer documents,
export an encrypted backup, create/unlock an account on the destination using
the same vault phrase, then explicitly restore the backup. There is no automatic
cross-service account migration or hidden sharing.

Runtime data is outside the installation: `%LOCALAPPDATA%\ApplicantEvidenceStudio`
on Windows, `~/Library/Application Support/ApplicantEvidenceStudio` on macOS,
and `${XDG_DATA_HOME:-~/.local/share}/ApplicantEvidenceStudio` on Linux. It
contains aliases, password hashes, session/recovery digests and ciphertext, not
the vault phrase or plaintext resumes. Other processes under your OS account
and administrators still have filesystem access. Protect your device.

## Recovery, backups and removal

Login recovery rotates your login password and recovery code and revokes all
sessions. It **does not** recover your vault phrase. Jason cannot decrypt a
forgotten vault phrase; there is intentionally no recovery backdoor. Keep both
the phrase and encrypted backup safely. Plaintext resume/report downloads are
not encrypted and must be protected separately.

Use Account & backups to export or restore an encrypted backup or permanently
delete your live account. Deletion does not securely erase filesystem sectors
or operator backups. The operator must publish and enforce backup retention.
To uninstall the portable desktop app, stop it and remove its executable. Data
is retained separately unless you explicitly delete your account/data. Do not
delete your data directory without a usable backup.

## Help and authorship

The sign-in/unlock screens and Account & backups include Help, privacy &
installation. The review UI includes Method & privacy, an evidence-strength
guide, job criteria and factual coaching. Read originals before hiring decisions.
Contact [Jason Stys on LinkedIn](https://www.linkedin.com/in/jason-stys-31b30b351/)
or view [his GitHub profile](https://github.com/JasonStys). Never send private
resumes, credentials, vault phrases or recovery codes in a GitHub issue.
