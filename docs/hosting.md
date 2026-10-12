# Host the private account website

The repo includes a functioning Python account service and built browser UI.
**A repository URL or GitHub Pages is not an account backend.** No public account
URL is provisioned by this source change. Select an approved hosting account/domain
with persistent disk, HTTPS, backups, rate-limited ingress and security operations.
Do not give passwords, tokens or private keys to a chat or commit them to GitHub.

## Local verification

After dependency installation and `npm run build`:

```powershell
.\.venv\Scripts\python.exe -m app.cli accounts --data runtime/private --port 8054
```

Visit `http://127.0.0.1:8054/`, register a fictional QA alias, unlock using a
different long phrase, and explicitly load examples from Account & backups.
That loopback URL is **not public hosting**. The portable desktop build bundles
these dependencies and chooses a free loopback port automatically.

## Deployment contract

Run `python -m uvicorn app.server:application --factory --host 0.0.0.0 --port 8000
--no-access-log --no-proxy-headers --workers 1 --limit-concurrency 50
--timeout-keep-alive 5` behind a TLS reverse proxy. This explicit server entrypoint
only exposes account/ciphertext operations; never use legacy `serve` publicly.

Set server-only `AES_PUBLIC_ORIGIN` to the exact canonical HTTPS origin (no path,
trailing slash, query or credentials). Set `AES_PRIVATE_DATA` to a protected
persistent directory and `AES_UI` to the built `dist` directory. The host owns
these deployment settings, not the GitHub client bundle. No user credentials or
encryption keys are required in environment variables. Reject plain HTTP for
public requests and preserve Host and Origin through the reverse proxy. The
application intentionally does not trust arbitrary forwarded headers.

The Dockerfile builds a non-root service with a persistent `/data` mount. Use a
host that supports a long-lived Python/container process and at least 512 MiB
memory (scrypt uses up to two simultaneous ~128 MiB working sets). Select and
verify OS/base-image updates before deploying; version tags are not immutable
digests. Do not repair local Docker Desktop just to deploy this project.

## Operational gates before inviting real users

1. Verify DNS/TLS and canonical Host/Origin, registration, two-user isolation,
   recovery, logout, account deletion, backup restore and service restart on the
   **actual HTTPS host**, not only loopback tests.
2. Apply ingress request/concurrency/IP limits and registration-abuse controls.
   App counters behind a non-trusted proxy see the proxy address; configure
   ingress limits correctly rather than enabling spoofable forwarded-IP trust.
   Single-worker SQLite is intentional; do not scale workers/instances without
   revisiting rate limits, write coordination, key/session storage and persistence.
3. Publish truthful privacy terms, hosting/subprocessor/network metadata, support
   contact, deletion/retention/backup policy and incident reporting process.
   Disable proxy request-body logs, analytics and third-party session replay.
4. Restrict server/admin access, patch dependencies/OS, monitor metadata-only
   health/errors and test encrypted backups/recovery. Prevent public disk access.
   Account deletion removes live rows, not host backup copies or filesystem sectors.
5. Obtain independent security/accessibility and role-specific responsible-use
   review before sensitive organizational recruitment use. No certification,
   legal-compliance guarantee or unbiased-selection claim is made.
6. Provide code-signed/notarized packages if users require trusted publisher
   identity. Current portable downloads are unsigned and checksum-verified only.

No paid plan, new hosting account, domain registration or public sharing change is
performed silently. Hosting credentials must be configured using the provider's
authorized flow. See [private accounts](private-accounts.md) and [install](install.md).
