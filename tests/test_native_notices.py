"""Jason Stys: mandatory isolated actual Tcl notice contracts with exact-case receipt. Symbol locations: generated source index."""

# Index: hashlib@5, json@6, subprocess@7, sys@8, tempfile@9, Path@10, ET@12, test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter@15, test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter.root@17, test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter.cases@18, test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter.temporary@19, test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter.result_path@20, test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter.result@21, test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter.records@39, test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter.item@41, test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter.item@42, test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter.receipt@43, test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter.item@45, test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter.target@56

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from defusedxml import ElementTree as ET


def test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter():
    """No retries/skips: preserve every real case, propagate failures and retain its source-bound JUnit identity."""
    root = Path(__file__).resolve().parents[1]
    cases = root / "tests/native_notice_cases.py"
    with tempfile.TemporaryDirectory(prefix="notice-contract-results-") as temporary:
        result_path = Path(temporary) / "results.xml"
        result = subprocess.run(  # noqa: S603 -- fixed owned interpreter and literal test module, no caller-supplied code
            [
                sys.executable,
                "-m",
                "pytest",
                str(cases),
                "--capture=sys",
                "-q",
                "-o",
                "cache_dir=" + str(Path(temporary) / "pytest-cache"),
                "--junitxml=" + str(result_path),
            ],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        records = list(ET.parse(result_path).getroot().iter("testcase"))
        assert len(records) == 13
        assert len({item.attrib["name"] for item in records}) == 13
        assert not any(list(item) for item in records), result.stdout + result.stderr
        receipt = {
            "passed": True,
            "actual_cases": [item.attrib["name"] for item in records],
            "case_count": len(records),
            "interpreter": sys.version.split()[0],
            "capture": "sys; stable native descriptors",
            "retries": 0,
            "skipped": 0,
            "case_source_sha256": hashlib.sha256(cases.read_bytes()).hexdigest(),
            "reader_source_sha256": hashlib.sha256(
                (root / "scripts/native_notices.py").read_bytes()
            ).hexdigest(),
        }
        target = root / ".runtime/notices-contract.json"
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print("All13 actual isolated Tcl/Tk notice cases passed; no retries or skips.")
