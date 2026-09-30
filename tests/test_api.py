"""API integration, persistence, authorization, bulk atomicity and private-error tests."""

# Index: base64@4, pytest@6, TestClient@7, create_app@9, samples@10, TOKEN@12, HEADERS@13, client@17, client.tmp_path@17, client.app@19, client.jobs@20, client.people@20, client.job@22, client.connection@24, test_authorization_host_origin_and_cache@28, test_authorization_host_origin_and_cache.client@28, test_authorization_host_origin_and_cache.response@34, test_validation_does_not_echo_private_inputs@40, test_validation_does_not_echo_private_inputs.client@40, test_validation_does_not_echo_private_inputs.data@42, test_validation_does_not_echo_private_inputs.response@43, test_validation_does_not_echo_private_inputs.oversized@45, test_queue_rank_filters_pagination@49, test_queue_rank_filters_pagination.client@49, test_queue_rank_filters_pagination.all_rows@51, test_queue_rank_filters_pagination.page@53, test_queue_rank_filters_pagination.subset@55, test_atomic_bulk_and_explicit_replace@62, test_atomic_bulk_and_explicit_replace.client@62, test_atomic_bulk_and_explicit_replace._@64, test_atomic_bulk_and_explicit_replace.people@64, test_atomic_bulk_and_explicit_replace.fresh@65, test_atomic_bulk_and_explicit_replace.duplicate@66, test_edit_concurrency_export_delete_and_restart@83, test_edit_concurrency_export_delete_and_restart.client@83, test_edit_concurrency_export_delete_and_restart.tmp_path@83, test_edit_concurrency_export_delete_and_restart.data@85, test_edit_concurrency_export_delete_and_restart.restarted@91, test_edit_concurrency_export_delete_and_restart.export@93, test_intake_coaching_download_and_job_draft@100, test_intake_coaching_download_and_job_draft.client@100, test_intake_coaching_download_and_job_draft.content@102, test_intake_coaching_download_and_job_draft.response@103, test_intake_coaching_download_and_job_draft.draft@107, test_intake_coaching_download_and_job_draft.report@110, test_intake_coaching_download_and_job_draft.result@113, test_intake_coaching_download_and_job_draft.job@115, test_no_external_request_without_consent@119, test_no_external_request_without_consent.client@119, test_no_external_request_without_consent.monkeypatch@119, test_no_external_request_without_consent.result@122, test_token_minimum@142, test_token_minimum.tmp_path@142
import base64

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.demo import samples

TOKEN = "synthetic_test_session_0123456789_abcdef"
HEADERS = {"Authorization": "Bearer " + TOKEN}


@pytest.fixture
def client(tmp_path):
    """Seed isolated synthetic test storage; never share the user's preview database."""
    app = create_app(tmp_path, TOKEN, "http://testserver")
    jobs, people = samples()
    app.state.store.import_applicants(people)
    for job in jobs:
        app.state.store.save_job(job)
    with TestClient(app) as connection:
        yield connection


def test_authorization_host_origin_and_cache(client):
    """Private endpoints reject missing secrets, cross-origin requests and DNS rebinding."""
    assert client.get("/health").json()["ready"]
    assert client.get("/api/jobs").status_code == 401
    assert client.get("/api/jobs", headers={**HEADERS, "Origin": "https://evil.example"}).status_code == 403
    assert client.get("/api/jobs", headers={**HEADERS, "Host": "evil.example"}).status_code == 403
    response = client.get("/api/config", headers=HEADERS)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    assert response.headers["x-frame-options"] == "DENY"
    assert "key" not in response.json()


def test_validation_does_not_echo_private_inputs(client):
    """Invalid records return error paths, not contact details or complete resume text."""
    data = {"applicants": [{"private": "SECRET_CONTACT_123"}]}
    response = client.post("/api/import", headers=HEADERS, json=data)
    assert response.status_code == 422 and "SECRET_CONTACT_123" not in response.text
    oversized = client.post("/api/import", headers=HEADERS, content=b"x" * 3_000_001)
    assert oversized.status_code == 413


def test_queue_rank_filters_pagination(client):
    """Filtering narrows the view without recomputing ranks within the filtered subset."""
    all_rows = client.get("/api/queue?job_id=software", headers=HEADERS).json()
    assert all_rows["total"] == 6 and all_rows["items"][0]["applicant_id"] == "A101"
    page = client.get("/api/queue?job_id=software&offset=2&limit=2", headers=HEADERS).json()
    assert len(page["items"]) == 2 and page["items"][0]["rank"] == 3
    subset = client.get("/api/queue?job_id=software&q=taylor&skill=cpp", headers=HEADERS).json()
    assert subset["total"] == 1 and subset["items"][0]["rank"] == 5
    assert client.get("/api/queue?job_id=software&skill=gender", headers=HEADERS).status_code == 422
    assert client.get("/api/queue?job_id=software&limit=101", headers=HEADERS).status_code == 422
    assert client.get("/api/queue?job_id=missing", headers=HEADERS).status_code == 404


def test_atomic_bulk_and_explicit_replace(client):
    """A conflict rolls the entire batch back; replacement is deliberate."""
    _, people = samples()
    fresh = people[0].model_copy(update={"id": "NEW"}).model_dump(mode="json")
    duplicate = people[0].model_dump(mode="json")
    assert (
        client.post("/api/import", headers=HEADERS, json={"applicants": [fresh, duplicate]}).status_code
        == 422
    )
    assert client.get("/api/applicants/NEW", headers=HEADERS).status_code == 404
    assert client.post("/api/import", headers=HEADERS, json={"applicants": [fresh, fresh]}).status_code == 422
    assert client.post("/api/import", headers=HEADERS, json={"applicants": [fresh]}).json()["imported"] == 1
    assert (
        client.post(
            "/api/import", headers=HEADERS, json={"applicants": [duplicate], "replace": True}
        ).status_code
        == 200
    )
    assert client.get("/api/applicants/A101", headers=HEADERS).json()["revision"] == 2


def test_edit_concurrency_export_delete_and_restart(client, tmp_path):
    """Stale edits fail; updates survive reopening SQLite; export/deletion is scoped."""
    data = client.get("/api/applicants/A101", headers=HEADERS).json()
    data["applicant"]["notes"] = "Corrected context"
    assert client.put("/api/applicants/A101", headers=HEADERS, json=data).status_code == 200
    assert client.put("/api/applicants/A101", headers=HEADERS, json=data).status_code == 422
    data["applicant"]["id"] = "BAD"
    assert client.put("/api/applicants/A101", headers=HEADERS, json=data).status_code == 422
    restarted = create_app(tmp_path, TOKEN, "http://testserver")
    assert restarted.state.store.applicant("A101")[0].notes == "Corrected context"
    export = client.get("/api/export/A101", headers=HEADERS)
    assert export.json()["education"][0]["status"] == "transferred"
    assert "attachment" in export.headers["content-disposition"]
    assert client.delete("/api/applicants/A101", headers=HEADERS).status_code == 200
    assert client.get("/api/applicants/A101", headers=HEADERS).status_code == 404


def test_intake_coaching_download_and_job_draft(client):
    """Real API intake and factual downloads preserve unknowns and proposed review status."""
    content = base64.b64encode(b"Synthetic\nProject: Python implementation").decode()
    response = client.post(
        "/api/ingest", headers=HEADERS, json={"filename": "source.txt", "content": content}
    )
    assert response.status_code == 200 and response.json()["proposals"][0]["reviewed"] is False
    draft = client.get("/api/resume/A101?job_id=software", headers=HEADERS)
    assert "transferred" in draft.text and "completed" in draft.text
    assert "attachment" in draft.headers["content-disposition"]
    report = client.get("/api/report/A101?job_id=software", headers=HEADERS)
    assert report.json()["score"] == 100 and len(report.json()["rubric_hash"]) == 16
    assert client.get("/api/coach/A101", headers=HEADERS).json()["general"]
    result = client.post("/api/recommend", headers=HEADERS, json={"description": "Python SQL testing"}).json()
    assert len(result["criteria"]) == 3
    job = {"id": "custom", "title": "Tester", "criteria": result["criteria"]}
    assert client.post("/api/jobs", headers=HEADERS, json=job).status_code == 200


def test_no_external_request_without_consent(client, monkeypatch):
    """Missing consent fails before provider I/O; profile lookup accepts only authorized repo URLs."""
    monkeypatch.delenv("AES_AI_MODEL", raising=False)
    result = client.post(
        "/api/ai", headers=HEADERS, json={"job_id": "software", "applicant_id": "A101", "consent": True}
    )
    assert result.status_code == 422
    assert (
        client.post(
            "/api/github", headers=HEADERS, json={"url": "http://127.0.0.1/private", "authorized": True}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/github",
            headers=HEADERS,
            json={"url": "https://github.com/example/project", "authorized": False},
        ).status_code
        == 422
    )


def test_token_minimum(tmp_path):
    """Launcher cannot accidentally create a weak service session."""
    with pytest.raises(ValueError):
        create_app(tmp_path, "short")
