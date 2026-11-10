# Full-main CodeQL finding review — 2026-11-10 UTC

By Jason Stys. This report supersedes the alert-disposition section of the earlier
[PR-only configuration snapshot](codeql-2026-11-09.md). A completed analysis job
does not mean its findings are empty. The actual full-main scan found three alerts.

## Exact observed baseline

The reviewed default-branch source is
[`ca0d21b086f4918cd9a0464d735f533ef8c44966`](https://github.com/JasonStys/applicant-evidence-studio/tree/ca0d21b086f4918cd9a0464d735f533ef8c44966).
[CodeQL run 42766254840](https://github.com/JasonStys/applicant-evidence-studio/actions/runs/42766254840)
executed CodeQL 2.27.4 with `security-extended`, without PR diff restriction.
The real logs explicitly identify a non-PR scan and absence of precomputed diff
ranges. Supported tracked-source extraction was checked against the complete
committed source tree, rather than inferred from a green check.

| Category              | Extracted tracked sources | Rules | SARIF results | Analysis ID |
| --------------------- | ------------------------: | ----: | ------------: | ----------- |
| Python                |                        35 |    50 |             1 | 2132846543  |
| JavaScript/TypeScript |                        25 |   103 |             2 | 2132845850  |
| Actions               |                         4 |    23 |             0 | 2132845382  |

The original [nine-job validation](https://github.com/JasonStys/applicant-evidence-studio/actions/runs/42766254516)
and [three-OS published-download acceptance](https://github.com/JasonStys/applicant-evidence-studio/actions/runs/42766254536)
also passed at that same main revision. There were no analysis warnings/errors,
but three open default-branch alerts. This is evidence of completed scans, **not
zero-finding security clearance**.

## Alert 1: descriptor-bound source-index reads

[`js/file-system-race`](https://github.com/JasonStys/applicant-evidence-studio/security/code-scanning/1)
identified an `existsSync(report)` check followed by a pathname-based
`readFileSync(report)` in `scripts/ts_index.mjs:97` at the baseline. Another local
process could replace the path between those operations. This is a genuine
developer-tool robustness defect; it is not a private-account HTTP route.

The indexer now opens once and reads through that descriptor. It accepts regular
files, enforces a 2,000,000-byte cap before and during the read, continues partial
reads at explicit offsets, decodes UTF-8 strictly and always closes the handle.
Only an actual `ENOENT` for the generated report is treated as stale/missing;
permission, type, encoding and other I/O failures propagate. Source-file reads
use the same helper. Eight real-filesystem regressions cover path replacement,
growth after `fstat`, partial reads, exact/multibyte limits, BOM preservation, malformed UTF-8,
missing/nonregular/interrupted reads and invalid budgets. No path/query exclusion
or error-to-empty fallback was introduced.

This is not a coherent snapshot of concurrent writes to the same inode, an
atomic index-write transaction, or protection against a hostile developer
workspace. The indexer remains a trusted development tool. Opening and checking
one descriptor removes the demonstrated check/use identity gap.

## Alert 2: dedicated-worker messaging boundary

[`js/missing-origin-check`](https://github.com/JasonStys/applicant-evidence-studio/security/code-scanning/2)
points to `web/private-parser.worker.ts:19` at the baseline. The query's documented
threat is untrusted **Window** messaging. This module runs only as a newly created
dedicated module Worker; its parent holds the private Worker object and terminates
it after completion, error or timeout. It does not register a Window message
handler or a SharedWorker public connection.

The actual shipped CodeQL DOM model recognizes a global `onmessage` assignment;
it does not establish that this particular receiver is a Window. The source now
declares `DedicatedWorkerGlobalScope` explicitly. This is type information, not a
fabricated runtime origin comparison: a valid dedicated-worker message has an
empty origin and null source, so comparing it to a Window origin would reject
legitimate parsing.

A real-browser regression loads the actual compiled parser asset, observes its
legitimate parent-channel event, delivers an unrelated Window message containing
an injected filename/content, then verifies the expected synthetic text is parsed
through the owned Worker channel. Chromium, Firefox, WebKit and mobile Chromium
all observed `origin === ''` and `source === null`. Existing local TXT/DOCX/PDF,
malformed-input, encryption and accessibility workflows remain required.

TypeScript 5.9.3 transpilation before/after the declaration, with ES2022/ESNext
and comments removed, is byte-identical: 3,080 bytes, SHA-256
`ddf60083a8b30227699b4ad230aa03d346fa2fb005050f3eac334964db3a0b77`.
The proposed disposition is a **finding-specific false positive**, subject to
maintainer review of the actual worker boundary. No alert has been dismissed by
this patch and no class of message checks has been suppressed. Compromised
same-origin application code can already hold the Worker reference; this proof
does not claim safety against a malicious host serving replacement code.

## Alert 3: fixed-authority GitHub README request

[`py/partial-ssrf`](https://github.com/JasonStys/applicant-evidence-studio/security/code-scanning/3)
points to the shared HTTP helper at `app/providers.py:109`. The actual SARIF flow
is browser request URL → `github_source` → validated owner/repository segments →
fixed `https://api.github.com/repos/{owner}/{repository}/readme` → HTTPX stream.
It is **not** a flow from `AES_AI_URL` or the custom AI configuration.

The existing full-match grammar permits bounded ASCII owner/repository segments.
It rejects whole `.`/`..` repository segments, delimiters, encoded separators,
credentials, ports, queries, fragments, control characters and Unicode lookalikes.
User input cannot change the authority, protocol or the fixed README resource.
This connector sends no Authorization header, ignores returned download URLs,
disables environment-proxy inheritance and does not follow redirects. Explicit
source consent and the response-size limit remain unchanged.

New tests exercise 60 deterministic accepted segment combinations through the
actual HTTPX URL parser and verify method, scheme, host, port, raw path, query,
fragment, credentials and absence of authorization. Twenty-five malicious URL
forms fail before even the injected transport is called. Three redirects to
local, metadata and lookalike destinations each make exactly one fixed-authority
request and fail; no redirected destination is contacted. All 43 provider cases
pass without external network access.

The proposed disposition is a **finding-specific false positive** for this
already-constrained path flow, pending maintainer review. Fixed-host requests can
still be abused within that service's permitted scope, and README assertions
still require human evidence review. DNS/TLS/host compromise and hostile operator
configuration are not proven safe by these tests. The separate custom AI endpoint
remains a trusted server-only operator setting; private-account mode exposes
neither provider route and never sends account plaintext to it.

## Local verification and release boundary

### Hosted browser setup correction

The initial revised-source [Validate run 42773088851](https://github.com/JasonStys/applicant-evidence-studio/actions/runs/42773088851)
at `06b0d6ef58c02d4396cbafad9c6ce1fbc13ea509` reached its unchanged 15-minute
deadline. Its actual completed log identifies Ubuntu 26.04.1 and repeated HTTP
Azure package-download delays: 139 MB took 11 minutes 9 seconds. The locked
browser binaries then downloaded in about 14 seconds. All 36 developer browser
cases and the first 22 private workflows passed before cancellation; the rest
and the Firefox repeat had not completed. This is an incomplete run, not a
passing matrix and not an observed application assertion failure.

The browser job now pins Ubuntu 24.04, verifies the expected disposable runner,
active mirror-file source and Ubuntu signing key, then uses the official HTTPS
archive/security mirrors with bounded APT acquire retries/timeouts. Source
suites, components and signature verification remain enabled. Dependency setup
and browser download have separate 10/5-minute caps inside the same 15-minute
job; all browser cases, repeats and actual test deadlines remain unchanged.
There is no retry-to-pass policy or fallback to a smaller browser matrix. The
six-OS/Python jobs, audit, container and three-OS published acceptance remain
separate requirements.

A new actual-file BOM fixture also exposed a compatibility regression in the
new descriptor reader: default TextDecoder behavior removes a leading UTF-8 BOM.
The corrected decoder preserves it while retaining fatal encoding checks and
the same byte cap. This prevents an unintended source rewrite; it does not
change any application parser or private-file processing.

### Completed local checks

Observed on Windows, Python 3.14.6 and Node 24.18.1:

- 158 Python tests pass; combined statement/branch coverage 88.70% exceeds the
  unchanged 85% floor. ResourceWarning remains an error. The existing
  Starlette/httpx compatibility deprecation is recorded, not suppressed.
- Eight descriptor-reader tests and three compiled comparison-domain oracles pass.
- Ruff, formatting, generated indexes and strict TypeScript/Vite build pass.
- npm and Python dependency audits report no known vulnerabilities at the check.
- All 32 private-account workflows pass across Chromium, Firefox, WebKit and
  mobile Chromium, including the four new dedicated-worker cases. All 36 legacy
  developer-mode browser cases and 16 repeated Firefox private workflows also
  pass in separate disposable services. Exact revised-source hosted analyses must
  still be checked before merge.

The sandboxed Python invocation produced no collection/result output and was
stopped; the real full suite above was run with normal local process access in
disposable test stores. No assertion was waived or test counted from that launch.
Local Docker was not repaired or used; the existing non-root container CI job
remains mandatory.

This patch changes development tooling, tests, documentation and a type-only
worker declaration. It changes no account/runtime algorithm, application version,
private store or installed binary. Published 0.3.0 assets remain immutable; no
new installer or application-security runtime update is claimed. A later full-main
rescan must verify the genuine defect's resolution and preserve the reviewed
disposition of any remaining finding. PR diff-informed zero results cannot
substitute for that check.

## Final full main result and reviewed dispositions

The exact merged source [`2742474af85014e849fe38796be1cdb8215e140e`](https://github.com/JasonStys/applicant-evidence-studio/tree/2742474af85014e849fe38796be1cdb8215e140e)
passed [Validate](https://github.com/JasonStys/applicant-evidence-studio/actions/runs/42776533593),
[published portable acceptance](https://github.com/JasonStys/applicant-evidence-studio/actions/runs/42776533592)
and [CodeQL](https://github.com/JasonStys/applicant-evidence-studio/actions/runs/42776533596).
All nine validation jobs, three actual downloaded-app OS jobs and three language
analysis jobs completed successfully. Reader/comparison tests, all 36 developer
browser cases, all 32 private workflows, the repeated Firefox regression and the
guarded browser setup were retained and completed. These are actual main-push
results, not PR-diff clearance or a claim that the earlier cancelled run passed.

| Category | Extracted tracked sources | Rules | Raw SARIF results | Analysis ID |
| --- | ---: | ---: | ---: | --- |
| Python | 35 | 50 | 1 | 2133255723 |
| JavaScript/TypeScript | 27 | 103 | 1 | 2133257220 |
| Actions | 4 | 23 | 0 | 2133255020 |

All complete logs explicitly identify non-PR, non-diff-informed scans; extraction
matches every supported committed source path. No analysis error or warning was
reported. The genuine index-read race, alert 1, closed automatically as fixed.
It was not dismissed. Raw SARIF still contains **two results**, not zero.

At the same reviewed source, the maintainer independently examined the actual
source/data flows, real filesystem and HTTPX tests, actual compiled-worker browser
proof, and primary WHATWG/CodeQL documentation. Alerts 2 and 3 were narrowly
classified through GitHub as false positives for this dedicated Worker channel
and this already-constrained fixed-authority GitHub path. Each alert retains its
own review rationale. No path/query exclusion, blanket suppression or fabricated
SARIF was added. The default-branch inventory has **zero open alerts after those
two reviewed dispositions**; that does not mean zero raw results or prove that
every possible input, deployment or future source revision is secure.

Published 0.3.0 binaries, installed accounts and runtime algorithms are unchanged.
This later documentation edition records the accepted source and dispositions;
its own integration PR/main workflows must pass separately.

## Primary references

- [Node file descriptors and open/check/use guidance](https://nodejs.org/docs/latest-v24.x/api/fs.html#fsopenpath-flags-mode-callback).
- [CodeQL filesystem-race query help](https://codeql.github.com/codeql-query-help/javascript/js-file-system-race/).
- [DedicatedWorkerGlobalScope and its implicit port](https://html.spec.whatwg.org/multipage/workers.html#dedicatedworkerglobalscope).
- [MessageEvent origin/source defaults](https://html.spec.whatwg.org/multipage/comms.html#messageevent).
- [CodeQL Window-message threat description](https://codeql.github.com/codeql-query-help/javascript/js-missing-origin-check/).
- [Exact shipped CodeQL DOM message model](https://github.com/github/codeql/blob/1be292a1e54696ca543b4ad0f9b4537b9687caa7/javascript/ql/lib/semmle/javascript/security/dataflow/DOM.qll#L179).
- [CodeQL partial-SSRF threat description](https://codeql.github.com/codeql-query-help/python/py-partial-ssrf/).
- [HTTPX clients and explicit request configuration](https://www.python-httpx.org/advanced/clients/).
- [Official runner APT-source routing](https://github.com/actions/runner-images/blob/main/images/ubuntu/scripts/build/configure-apt-sources.sh)
  and [bounded acquire settings](https://github.com/actions/runner-images/blob/main/images/ubuntu/scripts/build/configure-apt.sh).
