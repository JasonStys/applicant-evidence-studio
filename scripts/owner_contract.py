"""Jason Stys: mandatory fresh-interpreter actual Tk owner contracts with exact-case/coverage receipts."""

# Index: annotations@5, hashlib@7, json@8, os@9, subprocess@10, sys@11, Path@12, ET@14, ROOT@16, CASES@17, EXPECTED@18, verified_case@27, verified_case.exit_code@27, verified_case.expected@27, verified_case.raw@27, verified_case.document@31, verified_case.records@32, verified_case.row@40, verified_case.name@41, run_case@48, run_case.case@48, run_case.coverage_branch@48, run_case.output@48, run_case.result_path@53, run_case.arguments@54, run_case.arguments@56, run_case.arguments@58, run_case.arguments@59, run_case.arguments@60, run_case.environment@73, run_case.name@73, run_case.value@73, run_case.result@74, run_case.stream@81, run_case.raw@82, run_case.receipt@83

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from defusedxml import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests/native_owner_cases.py"
EXPECTED = (
    "test_real_owner_help_and_all_normal_close_controls[button]",
    "test_real_owner_help_and_all_normal_close_controls[window]",
    "test_real_owner_help_and_all_normal_close_controls[stdin]",
    "test_actual_quit_retains_window_and_profile_until_request_commits",
    "test_invalid_acceptance_nonce_does_not_close_real_window",
)


def verified_case(raw: bytes, expected: str, exit_code: int) -> dict:
    """A failed/skipped/missing/extra/wrong actual test cannot become a successful native receipt."""
    if expected not in EXPECTED or exit_code != 0 or len(raw) > 256 * 1024:
        raise AssertionError("Actual native owner child did not pass its exact bounded contract")
    document = ET.fromstring(raw, forbid_dtd=True)
    records = list(document.iter("testcase"))
    if (
        len(records) != 1
        or records[0].attrib.get("name") != expected
        or records[0].attrib.get("classname") != "tests.native_owner_cases"
        or list(records[0])
        or any(
            row.attrib.get(name, "0") != "0"
            for row in document.iter("testsuite")
            for name in ("failures", "errors", "skipped")
        )
    ):
        raise AssertionError("Actual native owner case identity/completion is incomplete")
    return {"passed": True, "actual_case": expected, "skipped": 0, "retries": 0}


def run_case(case: str, output: Path, *, coverage_branch: bool | None = None) -> dict:
    """Run exactly one original actual GUI case; preserve every assertion without repeated-root lifetime."""
    if case not in EXPECTED:
        raise ValueError("Unknown native owner case")
    output.mkdir()
    result_path = output / "result.xml"
    arguments = [sys.executable, "-m"]
    if coverage_branch is not None:
        arguments += ["coverage", "run", "--source=app", "--data-file=" + str(output / "coverage")]
        if coverage_branch:
            arguments += ["--branch"]
        arguments += ["-m"]
    arguments += [
        "pytest",
        "-p",
        "no:cov",
        str(CASES) + "::" + case,
        "--capture=sys",
        "-q",
        "-o",
        "cache_dir=" + str(output / "pytest-cache"),
        "--junitxml=" + str(result_path),
        "-W",
        "error::ResourceWarning",
    ]
    environment = {name: value for name, value in os.environ.items() if name != "PYTEST_ADDOPTS"}
    result = subprocess.run(  # noqa: S603 -- fixed current interpreter/source module and exact closed case whitelist
        arguments, cwd=ROOT, env=environment, text=True, capture_output=True, timeout=45, check=False
    )
    (output / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (output / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    with result_path.open("rb") as stream:
        raw = stream.read(256 * 1024 + 1)
    receipt = verified_case(raw, case, result.returncode)
    receipt.update(
        interpreter=sys.version.split()[0],
        capture="sys; one fresh interpreter and actual Tk root per GUI case",
        case_source_sha256=hashlib.sha256(CASES.read_bytes()).hexdigest(),
        coverage="actual child data merged into active parent measurement"
        if coverage_branch is not None
        else "not collected in this invocation",
    )
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt
