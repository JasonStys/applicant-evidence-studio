"""Jason Stys: independent exact-case negative receipts and actual fixture-construction resource-order regression."""

# Index: runpy@5, Path@6, pytest@8, CASES@10, EXPECTED@10, run_case@10, verified_case@10, report@13, report.child@13, report.name@13, report.suite@13, report.attributes@15, report.key@15, report.value@15, test_exact_success_requires_one_real_named_case@22, test_failure_skip_missing_wrong_extra_and_oversized_records_cannot_pass@56, test_failure_skip_missing_wrong_extra_and_oversized_records_cannot_pass.exit_code@56, test_failure_skip_missing_wrong_extra_and_oversized_records_cannot_pass.raw@56, test_unknown_case_never_starts_an_interpreter_or_creates_output@61, test_unknown_case_never_starts_an_interpreter_or_creates_output.tmp_path@61, test_unknown_case_never_starts_an_interpreter_or_creates_output.output@62, test_tcl_constructor_failure_precedes_any_socket_or_service_binding@68, test_tcl_constructor_failure_precedes_any_socket_or_service_binding.monkeypatch@68, test_tcl_constructor_failure_precedes_any_socket_or_service_binding.tmp_path@68, test_tcl_constructor_failure_precedes_any_socket_or_service_binding.source@69, test_tcl_constructor_failure_precedes_any_socket_or_service_binding.calls@70, test_tcl_constructor_failure_precedes_any_socket_or_service_binding.unavailable@72, test_tcl_constructor_failure_precedes_any_socket_or_service_binding._args@77

import runpy
from pathlib import Path

import pytest

from scripts.owner_contract import CASES, EXPECTED, run_case, verified_case


def report(name=EXPECTED[0], child="", **suite):
    """Author inert JUnit-shaped bytes independently of the validator."""
    attributes = " ".join(f'{key}="{value}"' for key, value in suite.items())
    return (
        f'<testsuites><testsuite {attributes}><testcase classname="tests.native_owner_cases" '
        f'name="{name}">{child}</testcase></testsuite></testsuites>'
    ).encode()


def test_exact_success_requires_one_real_named_case():
    assert verified_case(report(), EXPECTED[0], 0)["passed"] is True


@pytest.mark.parametrize(
    "raw,exit_code",
    [
        (report(), 1),
        (report(EXPECTED[1]), 0),
        (report(child="<skipped/>"), 0),
        (report(child="<failure/>"), 0),
        (report(child="<error/>"), 0),
        (report(failures="1"), 0),
        (b"<testsuites/>", 0),
        (
            report().replace(
                b"</testsuite>", b'<testcase classname="tests.native_owner_cases" name="extra"/></testsuite>'
            ),
            0,
        ),
        (b" " * (256 * 1024 + 1), 0),
    ],
    ids=[
        "child-failed",
        "wrong-case",
        "skipped",
        "failure",
        "error",
        "suite-failure",
        "missing",
        "extra",
        "oversized",
    ],
)
def test_failure_skip_missing_wrong_extra_and_oversized_records_cannot_pass(raw, exit_code):
    with pytest.raises(AssertionError):
        verified_case(raw, EXPECTED[0], exit_code)


def test_unknown_case_never_starts_an_interpreter_or_creates_output(tmp_path: Path):
    output = tmp_path / "untouched"
    with pytest.raises(ValueError, match="Unknown"):
        run_case("not-an-owned-case", output)
    assert not output.exists()


def test_tcl_constructor_failure_precedes_any_socket_or_service_binding(monkeypatch, tmp_path):
    source = runpy.run_path(str(CASES))
    calls = []

    def unavailable():
        raise source["tk"].TclError("inert fixture constructor failure")

    monkeypatch.setattr(source["tk"], "Tk", unavailable)
    monkeypatch.setitem(
        source["native_owner"].__wrapped__.__globals__, "LocalService", lambda *_args: calls.append("service")
    )
    with pytest.raises(source["tk"].TclError, match="fixture"):
        with source["native_owner"](None, tmp_path, tmp_path):
            raise AssertionError("An unavailable Tcl root cannot enter the GUI fixture")
    assert calls == []
