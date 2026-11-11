# Actual native-owner fixture isolation

The Windows Python 3.12 source-validation job failed while constructing a later
`Tk()` interpreter: Tcl could not read its bundled `init.tcl`. The first attempt
failed the stdin-close parameter; a later attempt failed the button-close parameter.
The other 224 checks passed in those attempts. Neither result establishes a missing
application resource, an installer fault or a specific Tcl/GC root cause. The
published Python 3.14 native application and its prior actual consumer acceptance
are separate evidence.

The repair changes test infrastructure only. The five original real owner-window
cases now each run in a fresh interpreter, with unchanged actual Open/Help/Quit,
window-close, stdin-close, invalid-nonce and pending-request/profile-retention
assertions. All 20 original assertion ASTs are identical. The original event-pump
deadlines remain unchanged. There are no retries, skips, synthetic pass receipts,
product changes, version changes or replacement release assets.

`tests/native_owner_cases.py` creates its actual Tk root before binding a service
socket. Its context manager closes the exact service and root after later fixture
errors. An independent constructor-failure regression verifies that a rejected Tk
constructor never creates a service. This also fixes the leaked test socket that
the original setup ordering could leave after a constructor error.

`scripts/owner_contract.py` admits only five literal case identities and requires
one matching completed JUnit record, successful process exit and no skipped/error/
failure records. Every child retains its own source-bound receipt. Missing,
different, extra, skipped, failed and oversized result fixtures must fail. Child
process setup/exit has a finite 45-second bound; this is not a wider deadline for
the unchanged actual GUI interaction assertions.

When the parent has app coverage enabled, the child runs the pinned coverage tool
from interpreter startup. Its actual data is loaded through the public coverage
API, checked for matching line/branch mode and merged into the parent's data.
No artificial covered lines or exclusions are added, and the original 85% app
coverage floor remains in every hosted Python matrix job.

Observed local Windows source validation passed 237 parent checks, including all
five wrappers, all five genuine owner children and the separate existing 13-case
notice child. The measured app aggregate was 91.21% under the unchanged line/branch
calculation. An independent saved-data comparison confirmed that every actual
owner child's executed `app/native_host.py` line set is present in the final parent
coverage data, including its actual branch arcs. The local source-test interpreter was Python 3.14.6; this does not describe
the patched runtime distributed in the native application. Exact hosted Python
3.12/3.14 matrix results remain a separate required acceptance gate.

The first new local negative-fixture run exposed an oversized pytest-generated
parameter ID on Windows. Explicit short IDs fix that test-only environment-size
error; its original failure is retained. The corrected focused run passed all 17
checks. Full validation retained one existing Starlette/httpx deprecation warning;
`ResourceWarning` remains an error.

Primary references: [Tkinter interpreter/threading model](https://docs.python.org/3.12/library/tkinter.html#threading-model),
[coverage process measurement](https://coverage.readthedocs.io/en/latest/subprocess.html),
[public CoverageData merge API](https://coverage.readthedocs.io/en/latest/api_coveragedata.html#coverage.CoverageData.update).
