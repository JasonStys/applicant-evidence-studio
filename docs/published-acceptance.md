# Published portable application acceptance

The 0.3.0 downloads already contain the evidence-comparison feature. This update
tests the actual downloadable bytes more thoroughly without replacing that
published version. ZIP/tar packages are portable applications, not registered
system installers. They remain unsigned.

`Published portable acceptance` runs on Windows AMD64, Linux x86-64 and macOS
ARM64. It resolves the fixed 0.3.0 tag to source
`71d51b1fcd228f89d3ff81ee166bee2ce37d7a60`, selects only the current platform's
archive and checksum file, and verifies their length and SHA-256 against both
GitHub asset metadata and the independently reviewed immutable byte identities.
No caller-provided repository, URL, tag or executable is downloaded.

The archive must contain exactly the executable, license and installation guide.
Duplicate names, extra files, traversal, links, special permissions, missing
POSIX executable bits, incomplete manifests and changed hashes fail acceptance.
Tests do not repair a broken archive to make it launch. The binary is extracted
into an owned temporary directory and its own checksum is checked before launch.

The native process runs from a separate empty working directory and uses a new
temporary account store. It announces an OS-assigned loopback port before the
test sends any HTTP request. There is no source-server or host-package fallback.
The actual embedded UI must complete registration, WebCrypto unlock, fictional
example loading, record editing, comparison and JSON download. Record hashes,
criterion results and rubric identity are checked against independent inputs and
Python reference assessments. Capture must not write plaintext or increment the
encrypted store revision; hostile source labels remain literal text. Lock/reopen
must clear capture state, and a separate unauthenticated context receives 401.
Outside resource requests and automated comparison-card accessibility violations
fail the journey. All owned browser/process resources are stopped afterward.

For a local developer acceptance run after installing the locked QA dependencies
and Playwright Chromium:

```text
python scripts/portable_acceptance.py --published
```

Future release builds additionally run:

```text
python scripts/portable_acceptance.py --built-directory release
```

The source release workflow must be on main, with successful main-push source
validation and published-package acceptance for that exact commit. Every upload
rechecks the draft's source and version. Existing equal bytes can be resumed;
different bytes are rejected, with no clobber operation. Publication requires all
six platform assets and provider digests. A published version is never reused.

The current release recipe and published acceptance pins intentionally describe
0.3.0. A future product release needs coherent product/version/notes updates and
a reviewed acceptance contract for its published UI and reference fixtures; do
not weaken an old contract to accommodate changed behavior. Preserve older
published assets. Hashes identify bytes, not a publisher signature or proof that
a compromised device is safe. This is an isolated synthetic QA journey, not
clean-machine certification, physical mobile-device testing or public hosting.
