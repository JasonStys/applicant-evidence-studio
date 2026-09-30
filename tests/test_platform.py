"""Regression tests for platform-specific parser containment, using mocked process resource APIs."""

# Index: base64@4, io@5, json@6, sys@7, SimpleNamespace@8, pytest@10, extract@12, test_parser_resource_policy@16, test_parser_resource_policy.capsys@16, test_parser_resource_policy.monkeypatch@16, test_parser_resource_policy.platform@16, test_parser_resource_policy.calls@18, test_parser_resource_policy.resource@19, test_parser_resource_policy.key@20, test_parser_resource_policy.value@20, test_parser_resource_policy.data@24
import base64
import io
import json
import sys
from types import SimpleNamespace

import pytest

from app import extract


@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
def test_parser_resource_policy(platform, monkeypatch, capsys):
    """Apply Linux caps only where intended; other platforms preserve bounded subprocess operation."""
    calls = []
    resource = SimpleNamespace(
        RLIMIT_AS=1, RLIMIT_CPU=2, setrlimit=lambda key, value: calls.append((key, value))
    )
    monkeypatch.setitem(sys.modules, "resource", resource)
    monkeypatch.setattr(sys, "platform", platform)
    data = {
        "filename": "synthetic.txt",
        "content": base64.b64encode(b"Synthetic professional source").decode(),
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(data)))
    extract.main()
    assert json.loads(capsys.readouterr().out)["text"] == "Synthetic professional source"
    assert len(calls) == (2 if platform == "linux" else 0)
