"""Jason Stys: every original real native-owner contract remains mandatory in a fresh Tcl interpreter."""

# Index: Path@5, coverage@7, pytest@8, EXPECTED@10, run_case@10, test_actual_native_owner_case_in_fresh_interpreter@14, test_actual_native_owner_case_in_fresh_interpreter.case@14, test_actual_native_owner_case_in_fresh_interpreter.tmp_path@14, test_actual_native_owner_case_in_fresh_interpreter.active@16, test_actual_native_owner_case_in_fresh_interpreter.output@17, test_actual_native_owner_case_in_fresh_interpreter.receipt@18, test_actual_native_owner_case_in_fresh_interpreter.child@21, test_actual_native_owner_case_in_fresh_interpreter.data@23, test_actual_native_owner_case_in_fresh_interpreter.name@25

from pathlib import Path

import coverage
import pytest

from scripts.owner_contract import EXPECTED, run_case


@pytest.mark.parametrize("case", EXPECTED)
def test_actual_native_owner_case_in_fresh_interpreter(case: str, tmp_path: Path):
    """No skips/retries; actual child coverage joins the original unchanged app branch-coverage floor."""
    active = coverage.Coverage.current()
    output = tmp_path / "actual-native-owner"
    receipt = run_case(case, output, coverage_branch=active.config.branch if active else None)
    assert receipt["passed"] and receipt["actual_case"] == case
    if active:
        child = coverage.Coverage(data_file=str(output / "coverage"))
        child.load()
        data = child.get_data()
        assert data.has_arcs() == active.config.branch
        assert any(Path(name).name == "native_host.py" for name in data.measured_files())
        active.get_data().update(data)
