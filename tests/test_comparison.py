"""Jason Stys: verify two-record authorization, atomic capture, exact order/revisions and no mutations."""

# Index: json@4, sqlite3@5, threading@6, tomllib@7, contextmanager@8, Path@9, TestClient@11, VERSION@13, create_app@14, samples@15, create_private_app@16, TOKEN@18, HEADERS@19, test_release_version_is_coherent_without_changing_vault_formats@22, test_release_version_is_coherent_without_changing_vault_formats.tmp_path@22, test_release_version_is_coherent_without_changing_vault_formats.root@24, test_release_version_is_coherent_without_changing_vault_formats.workflow@30, test_release_version_is_coherent_without_changing_vault_formats.client@35, test_release_version_is_coherent_without_changing_vault_formats.client@40, seeded@44, seeded.tmp_path@44, seeded.application@46, seeded.jobs@47, seeded.people@47, seeded.job@49, test_capture_preserves_selection_revisions_and_privacy_boundary@54, test_capture_preserves_selection_revisions_and_privacy_boundary.tmp_path@54, test_capture_preserves_selection_revisions_and_privacy_boundary.application@56, test_capture_preserves_selection_revisions_and_privacy_boundary.jobs@56, test_capture_preserves_selection_revisions_and_privacy_boundary.people@56, test_capture_preserves_selection_revisions_and_privacy_boundary.store@57, test_capture_preserves_selection_revisions_and_privacy_boundary.connection@58, test_capture_preserves_selection_revisions_and_privacy_boundary.before@59, test_capture_preserves_selection_revisions_and_privacy_boundary.client@60, test_capture_preserves_selection_revisions_and_privacy_boundary.path@61, test_capture_preserves_selection_revisions_and_privacy_boundary.response@64, test_capture_preserves_selection_revisions_and_privacy_boundary.captured@66, test_capture_preserves_selection_revisions_and_privacy_boundary.row@67, test_capture_preserves_selection_revisions_and_privacy_boundary.row@68, test_capture_preserves_selection_revisions_and_privacy_boundary.query@71, test_capture_preserves_selection_revisions_and_privacy_boundary.result@77, test_capture_preserves_selection_revisions_and_privacy_boundary.connection@81, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit@85, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.monkeypatch@85, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.tmp_path@85, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.application@87, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.jobs@87, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.people@87, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.store@88, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.original@89, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.ready@90, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.errors@91, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.changed@92, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.writer@94, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.writer.connection@97, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.thread@109, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.started@110, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.observed_connection@113, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.observed_connection.connection@116, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.observed_connection.trace@118, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.observed_connection.trace.statement@118, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.observed_connection.trace.started@122, test_capture_keeps_one_database_snapshot_during_a_concurrent_edit.captured@130
import json
import sqlite3
import threading
import tomllib
from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient

from app import VERSION
from app.api import create_app
from app.demo import samples
from app.private_api import create_private_app

TOKEN = "synthetic_comparison_session_0123456789_abcdef"
HEADERS = {"Authorization": "Bearer " + TOKEN}


def test_release_version_is_coherent_without_changing_vault_formats(tmp_path):
    """Current software metadata and real health responses agree; prior release assets stay separate."""
    root = Path(__file__).resolve().parents[1]
    assert VERSION == "0.3.1"
    assert json.loads((root / "package.json").read_text(encoding="utf-8"))["version"] == VERSION
    assert (
        tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"] == VERSION
    )
    workflow = (root / ".github/workflows/desktop-release.yml").read_text(encoding="utf-8")
    assert (
        "group: desktop-release-v0.3.1" in workflow and "scripts/desktop_release_guard.py prepare" in workflow
    )
    assert "v0.2.0" not in workflow
    with TestClient(create_app(tmp_path / "developer", TOKEN, "http://testserver")) as client:
        assert client.get("/health").json()["version"] == VERSION
    with TestClient(
        create_private_app(tmp_path / "accounts", "https://studio.example", tmp_path / "no-ui"),
        base_url="https://studio.example",
    ) as client:
        assert client.get("/health").json()["version"] == VERSION


def seeded(tmp_path):
    """Create only disposable synthetic records and return a seeded application/fixture list."""
    application = create_app(tmp_path, TOKEN, "http://testserver")
    jobs, people = samples()
    application.state.store.import_applicants(people)
    for job in jobs:
        application.state.store.save_job(job)
    return application, jobs, people


def test_capture_preserves_selection_revisions_and_privacy_boundary(tmp_path):
    """A comparison reads an authorized snapshot, never changing the ranking, records or audit trail."""
    application, jobs, people = seeded(tmp_path)
    store = application.state.store
    with store.connect() as connection:
        before = connection.execute("SELECT count(*) FROM events").fetchone()[0]
    with TestClient(application) as client:
        path = f"/api/comparison?job_id={jobs[0].id}&left={people[1].id}&right={people[0].id}"
        assert client.get(path).status_code == 401
        assert client.get(path, headers={**HEADERS, "Origin": "https://evil.example"}).status_code == 403
        response = client.get(path, headers=HEADERS)
        assert response.status_code == 200
        captured = response.json()
        assert [row["applicant"]["id"] for row in captured["applicants"]] == [people[1].id, people[0].id]
        assert [row["revision"] for row in captured["applicants"]] == [1, 1]
        assert captured["job"] == jobs[0].model_dump(mode="json")
        assert response.headers["cache-control"] == "no-store"
        for query in [
            f"job_id={jobs[0].id}&left={people[0].id}&right={people[0].id}",
            f"job_id=missing&left={people[0].id}&right={people[1].id}",
            f"job_id={jobs[0].id}&left=missing&right={people[1].id}",
            f"job_id={jobs[0].id}&left=SQL%27OR1=1&right={people[1].id}",
        ]:
            result = client.get("/api/comparison?" + query, headers=HEADERS)
            assert result.status_code in (404, 422)
        store.save_applicant(people[0].model_copy(update={"consent_sources": False}), 1)
        assert client.get(path, headers=HEADERS).status_code == 422
    with store.connect() as connection:
        assert connection.execute("SELECT count(*) FROM events").fetchone()[0] == before + 1


def test_capture_keeps_one_database_snapshot_during_a_concurrent_edit(tmp_path, monkeypatch):
    """A writer between rubric and record reads cannot create a mixed-revision comparison."""
    application, jobs, people = seeded(tmp_path)
    store = application.state.store
    original = store.connect
    ready = threading.Event()
    errors = []
    changed = people[0].model_copy(update={"notes": "New synthetic revision"})

    def writer():
        """Hold a real transaction until the read snapshot has collected both original records."""
        try:
            with sqlite3.connect(store.path, timeout=5) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "UPDATE applicants SET body=?,revision=2 WHERE id=?",
                    (changed.model_dump_json(), changed.id),
                )
                ready.set()
            connection.close()
        except Exception as error:
            errors.append(error)
            ready.set()

    thread = threading.Thread(target=writer)
    started = False

    @contextmanager
    def observed_connection():
        """Instrument a scheduling boundary without changing any SQL or result."""
        nonlocal started
        with original() as connection:

            def trace(statement):
                """Let an independent SQLite writer update after the read transaction's first SELECT."""
                nonlocal started
                if statement.startswith("SELECT id,body,revision") and not started:
                    started = True
                    thread.start()
                    assert ready.wait(5)

            connection.set_trace_callback(trace)
            yield connection

    monkeypatch.setattr(store, "connect", observed_connection)
    captured = store.comparison_capture(jobs[0].id, people[0].id, people[1].id)
    thread.join(6)
    assert not thread.is_alive() and not errors
    assert captured["applicants"][0]["revision"] == 1
    assert captured["applicants"][0]["applicant"].notes != changed.notes
    assert store.applicant(people[0].id)[1] == 2
