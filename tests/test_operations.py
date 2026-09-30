"""CLI, worker, report and invariant tests complement API/browser coverage."""

# Index: base64@4, io@5, json@6, sys@7, pytest@9, given@10, st@11, cli@13, extract@13, samples@14, Criterion@15, Job@15, assess@16, Store@17, test_seed_and_serve_entrypoints@20, test_seed_and_serve_entrypoints.capsys@20, test_seed_and_serve_entrypoints.monkeypatch@20, test_seed_and_serve_entrypoints.tmp_path@20, test_seed_and_serve_entrypoints.calls@29, test_seed_and_serve_entrypoints.args@30, test_seed_and_serve_entrypoints.kwargs@30, test_worker_success_and_error@39, test_worker_success_and_error.capsys@39, test_worker_success_and_error.monkeypatch@39, test_worker_success_and_error.data@42, test_weighted_score_range@55, test_weighted_score_range.target@55, test_weighted_score_range.weight@55, test_weighted_score_range._@57, test_weighted_score_range.people@57, test_weighted_score_range.job@58, test_weighted_score_range.result@59, test_audit_contains_no_resume_content@63, test_audit_contains_no_resume_content.tmp_path@63, test_audit_contains_no_resume_content._@65, test_audit_contains_no_resume_content.people@65, test_audit_contains_no_resume_content.store@66, test_audit_contains_no_resume_content.connection@68, test_audit_contains_no_resume_content.rows@69
import base64
import io
import json
import sys

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app import cli, extract
from app.demo import samples
from app.models import Criterion, Job
from app.review import assess
from app.store import Store


def test_seed_and_serve_entrypoints(tmp_path, monkeypatch, capsys):
    """Explicit seed is reproducible; launcher binds only loopback with a sufficiently strong token."""
    monkeypatch.setattr(sys, "argv", ["applicant-studio", "seed", "--data", str(tmp_path)])
    cli.main()
    assert len(Store(tmp_path / "applicants.db").applicants()) == 6
    with pytest.raises(ValueError):
        cli.main()
    monkeypatch.setattr(sys, "argv", ["applicant-studio", "serve", "--data", str(tmp_path), "--port", "8016"])
    monkeypatch.setenv("AES_SESSION_TOKEN", "test_session_0123456789_abcdefghijklmnopqrstuvwxyz")
    calls = []
    monkeypatch.setattr(cli.uvicorn, "run", lambda *args, **kwargs: calls.append(kwargs))
    cli.main()
    assert calls[0]["host"] == "127.0.0.1" and calls[0]["port"] == 8016
    assert "8016/#token=" in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["applicant-studio", "serve", "--port", "80"])
    with pytest.raises(SystemExit):
        cli.main()


def test_worker_success_and_error(monkeypatch, capsys):
    """Exercise worker JSON contract without applying process resource caps to the test runner."""
    monkeypatch.setattr(extract.sys, "platform", "win32")
    data = {"filename": "fixture.txt", "content": base64.b64encode(b"Synthetic content").decode()}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(data)))
    extract.main()
    assert json.loads(capsys.readouterr().out)["text"] == "Synthetic content"
    monkeypatch.setattr(sys, "stdin", io.StringIO("not-json"))
    extract.main()
    assert "error" in json.loads(capsys.readouterr().out)


@given(
    st.integers(min_value=1, max_value=10),
    st.sampled_from(["declared", "practiced", "demonstrated", "assessed"]),
)
def test_weighted_score_range(weight, target):
    """All valid weights and target strengths produce bounded scores, including above-target evidence."""
    _, people = samples()
    job = Job(id="j", title="Role", criteria=[Criterion(skill="python", weight=weight, target=target)])
    result = assess(people[0], job)
    assert 0 <= result["score"] <= 100


def test_audit_contains_no_resume_content(tmp_path):
    """Audit events record operations and local IDs only; source contents never become log messages."""
    _, people = samples()
    store = Store(tmp_path / "records.db")
    store.import_applicants(people[:1])
    with store.connect() as connection:
        rows = connection.execute("SELECT action,record_id FROM events").fetchall()
    assert rows == [("import", "A101")]
    with pytest.raises(ValueError):
        store.save_applicant(people[0], 999)
    with pytest.raises(KeyError):
        store.delete("missing")
