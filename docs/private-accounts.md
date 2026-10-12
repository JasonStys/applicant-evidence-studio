# Private accounts and browser-encrypted workspaces

Created by Jason Stys. Version 0.2 adds a **separate ciphertext-only service**;
the earlier `serve` developer mode remains loopback-only and stores plaintext
locally. Never expose that legacy mode publicly. No automatic migration of
legacy resumes occurs: export only authorized data and explicitly import it into
an unlocked private account. Do not upload real records to GitHub.

## Trust and data boundary

| Data | Where it exists | Who can access it |
| --- | --- | --- |
| Alias, creation time | Account database | Host/backup administrators; signed-in user sees own alias |
| Login password | TLS request, briefly server/browser memory | Login verification process; not stored in plaintext |
| Password hash | Account database | Host; scrypt N=131072, r=8, p=1, random 32-byte salt |
| Session/recovery secrets | HttpOnly cookie / once-shown recovery display | User/browser; server stores SHA-256 digests of random 256-bit values |
| Independent vault phrase/key | Unlocked browser memory | User/device, never account service |
| Resumes, job rubrics, sources, reports | Unlocked browser memory and explicitly downloaded exports | User/device; no server parser/scorer sees plaintext |
| Workspace envelope | Account DB, encrypted backup | Owner/host see ciphertext, nonce, salt and byte length; not plaintext |
| Network metadata | Host/reverse proxy | Host/infrastructure; not anonymous browsing |

There is **no administrator document-view route**, no cross-user owner parameter,
no sharing directory, no telemetry, analytics, third-party scripts, ad network,
automatic GitHub/LinkedIn lookup or external AI request in private mode. The
owner is derived exclusively from a verified session. A user may intentionally
download/share a plaintext export outside the service; that is their decision.

Encryption protects stored documents from passive host/database inspection. It
does **not** protect against a host serving malicious future JavaScript, browser
extensions, device malware, stolen unlocked sessions, screenshots, a weak phrase
or coercion. Source review, independent audits and verified local builds help
reduce reliance on a web host. Hosting account metadata is not operator-blind.
No application can guarantee that all attacks or popups are impossible.

## Cryptography and recovery

Web Crypto derives a non-extractable AES-256-GCM key from a separate phrase using
PBKDF2-HMAC-SHA-256, 600,000 iterations and a random 16-byte salt. Each save uses
a fresh random 12-byte nonce, 128-bit authentication tag and protocol/version AAD
`applicant-evidence-studio:workspace:v1`. A backup contains only `version`, `salt`,
`iv`, `ciphertext`. Envelope and decrypted schema validation precede import.
Wrong keys, corrupt ciphertext and unrecognized versions do not replace data.
Phrase length is a minimum input guard, **not a guarantee of entropy**: use six
random words or a password-manager-generated secret. Do not reuse the login
password. JavaScript references are dropped on lock; secure memory erasure is
not promised by a garbage-collected runtime.

Login recovery is a distinct random secret. It rotates login credentials and
revokes every session. It does not recover or change the vault key. There is no
email collection, identity verification, vault reset or host decryption backdoor.
Save the phrase, encrypted backups and login recovery code separately and privately.

## Web/security controls

Cookie sessions are random, hashed at rest, eight-hour absolute / thirty-minute
server idle expiry, ten sessions maximum. HTTPS uses a `__Host-` cookie with
Secure, HttpOnly, SameSite=Strict, Path=/ and no Domain. Literal loopback HTTP
uses a separate non-Secure cookie; it is not accepted as a public deployment.
Browser state locks after ten idle minutes. Logout revokes the presented cookie;
account deletion re-verifies the login password and cascades live credentials,
sessions and ciphertext. Older host backups require separate retention enforcement.

Host/Origin checks, an explicit JSON/custom-header CSRF boundary, cross-site
fetch rejection, body/envelope limits, persistent hashed-identifier rate counters,
bounded scrypt concurrency, schema/citation checks and compare-and-swap revisions
protect input and ownership boundaries. Extra fields are rejected. Errors omit
input/password values. Security headers apply to rejected requests too.

CSP allows only same-origin scripts/connectivity/workers, disables objects,
framing, base URI injection and foreign form targets. Camera, microphone,
geolocation and payment are disabled. No external fonts are loaded. Static assets
use explicit module/manifest MIME types on Windows as well as Unix. Inline styles
remain permitted for the established React UI; inline scripts and eval do not.
Validators are generated at build time so they do not require unsafe-eval.
The installable web app's worker does not cache private responses or credentials.

Parsing stays local: bounded UTF-8 TXT/MD and main-body DOCX in a disposable worker;
PDF.js's dedicated worker for text-based PDF. Input cap 2 MB, text cap 80,000
characters, PDF cap 50 pages, DOCX entry/expansion caps and fifteen-second timeout.
No applicant code, PDF JavaScript, macros or document links are run. OCR, images,
headers/footnotes, equations and layout inference are not claimed. Browser parsing
is not a hard OS memory sandbox; hostile compressed documents still require care.

## Domain behavior and practical limits

The browser uses the existing closed skill taxonomy and schema contracts.
Professional evidence alone influences scores. Names, school prestige, gender,
race, age and personal biography do not. Unreviewed claims score nothing; transfer
ambiguity and required gaps request human clarification. Coursework is not invented
employment. Scores are advisory, not automatic acceptance/rejection or a legally
validated predictor. Organizational evaluation still needs role-specific validity,
fairness/accessibility/correction processes and applicable professional review.

Private coaching is deterministic and offline. Optional external-provider AI and
single-README imports remain in the **separate trusted local developer mode**;
they are disabled in private account mode to avoid disclosure to another provider.
Paste authorized professional exports for private sources. This privacy trade-off
is deliberate, not a claim of hosted AI inference or automated people search.

Capacity is 1,000 records, 100 job rubrics and **8 MiB encrypted plaintext budget**;
real documents may reach the size cap well before the count cap. Mutations serialize,
validate, encrypt and sync before committing memory. A stale remote revision returns
409, never silently overwrites. The encrypted backup includes the latest failed-save
attempt while unlocked; export it before locking, reloading or the idle timeout.
Do not merge conflicting versions by guessing. Export/import and review deliberately.

Scoring is O(E+C) per applicant; ranking O(A(E+C)+A log A), filtering uses a map,
and whole-vault cloning/encryption/transfer is O(S) in workspace bytes. This avoids
per-field metadata disclosure but is unsuitable for huge multi-user HR systems.
No team sharing, E2EE key exchange, multi-tenant organization administration,
offline sync or high-availability cluster is implemented.

## Primary implementation references

- [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html): scrypt work factor and salted storage; browser PBKDF2 iteration guidance.
- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html): random sessions, expiry and cookie protections.
- [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html): Origin checks, custom headers and SameSite defense in depth.
- [MDN Web Crypto deriveKey](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/deriveKey) and [AES-GCM encryption](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/encrypt): non-extractable keys, derivation and authenticated encryption.
- [Ajv standalone generation](https://ajv.js.org/standalone.html): build-time validation compatible with strict CSP.
- [PDF.js](https://mozilla.github.io/pdf.js/): browser API/worker document extraction, not document script execution.
