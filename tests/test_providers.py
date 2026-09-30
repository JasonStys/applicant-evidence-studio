"""Mocked provider contract tests; no live model charges or personal data transmission."""

# Index: base64@4, json@5, httpx@7, pytest@8, samples@10, ai_review@11, bounded_json@11, github_source@11, provider_config@11, test_provider_protocol_and_privacy@15, test_provider_protocol_and_privacy.kind@15, test_provider_protocol_and_privacy.monkeypatch@15, test_provider_protocol_and_privacy.jobs@17, test_provider_protocol_and_privacy.people@17, test_provider_protocol_and_privacy.person@18, test_provider_protocol_and_privacy.respond@25, test_provider_protocol_and_privacy.respond.request@25, test_provider_protocol_and_privacy.respond.value@27, test_provider_protocol_and_privacy.respond.data@28, test_provider_protocol_and_privacy.respond.raw@31, test_provider_protocol_and_privacy.respond.result@32, test_provider_protocol_and_privacy.result@39, test_bad_provider_endpoints@53, test_bad_provider_endpoints.monkeypatch@53, test_bad_provider_endpoints.url@53, test_missing_model_and_consent@61, test_missing_model_and_consent.monkeypatch@61, test_missing_model_and_consent.jobs@66, test_missing_model_and_consent.people@66, test_github_only_selected_public_readme@71, test_github_only_selected_public_readme.content@73, test_github_only_selected_public_readme.respond@75, test_github_only_selected_public_readme.respond.request@75, test_github_only_selected_public_readme.result@88, test_profile_ssrf_urls@102, test_profile_ssrf_urls.url@102, test_remote_size_limit_and_redirect@108, test_remote_size_limit_and_redirect.request@110, test_remote_size_limit_and_redirect.transport@110, test_remote_size_limit_and_redirect.client@111, test_remote_size_limit_and_redirect.transport@113, test_remote_size_limit_and_redirect.request@114
import base64
import json

import httpx
import pytest

from app.demo import samples
from app.providers import ai_review, bounded_json, github_source, provider_config


@pytest.mark.parametrize("kind", ["ollama", "compatible"])
def test_provider_protocol_and_privacy(kind, monkeypatch):
    """Supported provider protocols get only canonical, non-sensitive structured facts."""
    jobs, people = samples()
    person = people[0]
    person.consent_ai = True
    monkeypatch.setenv("AES_AI_KIND", kind)
    monkeypatch.setenv("AES_AI_MODEL", "synthetic-test-model")
    monkeypatch.setenv("AES_AI_URL", "https://model.example/chat")
    monkeypatch.setenv("AES_AI_KEY", "test-only-key")

    def respond(request):
        """Validate outbound input before returning a protocol-specific mock response."""
        value = json.loads(request.content)
        data = json.loads(value["messages"][1]["content"])
        assert set(data) == {"rubric", "evidence"}
        assert "Morgan" not in request.content.decode() and "Metro" not in request.content.decode()
        raw = '{"suggestions":[{"skill":"python","evidence_ids":["e0"],"action":"test"}]}'
        result = (
            {"message": {"content": raw}}
            if kind == "ollama"
            else {"choices": [{"message": {"content": raw}}]}
        )
        return httpx.Response(200, json=result)

    result = ai_review(person, jobs[0], True, httpx.MockTransport(respond))
    assert result["assessment"]["score"] == 100
    assert result["suggestions"][0]["text"].startswith("Add meaningful")


@pytest.mark.parametrize(
    "url",
    [
        "http://remote.example/chat",
        "https://key:secret@remote.example/chat",
        "file:///private",
        "https://remote.example/?key=secret",
    ],
)
def test_bad_provider_endpoints(url, monkeypatch):
    """Remote cleartext or credential-bearing URLs are rejected before I/O."""
    monkeypatch.setenv("AES_AI_MODEL", "test")
    monkeypatch.setenv("AES_AI_URL", url)
    with pytest.raises(ValueError):
        provider_config()


def test_missing_model_and_consent(monkeypatch):
    """No model or consent results in an explicit setup/authorization error."""
    monkeypatch.delenv("AES_AI_MODEL", raising=False)
    with pytest.raises(ValueError):
        provider_config()
    jobs, people = samples()
    with pytest.raises(ValueError, match="consent"):
        ai_review(people[0], jobs[0], True)


def test_github_only_selected_public_readme():
    """Selected repository fetch never follows a README download URL or executes content."""
    content = base64.b64encode(b"Synthetic README: tests and limitations").decode()

    def respond(request):
        """Assert the fixed API destination and return one synthetic professional source."""
        assert str(request.url) == "https://api.github.com/repos/example/project/readme"
        return httpx.Response(
            200,
            json={
                "encoding": "base64",
                "size": 40,
                "content": content,
                "download_url": "http://private/ignored",
            },
        )

    result = github_source("https://github.com/example/project", True, httpx.MockTransport(respond))
    assert result["text"].startswith("Synthetic") and result["warnings"]


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com.evil/example/project",
        "https://github.com/example/..",
        "https://github.com/example/project?token=x",
        "http://github.com/example/project",
        "https://github.com/example",
    ],
)
def test_profile_ssrf_urls(url):
    """GitHub connector cannot be redirected into arbitrary domains, paths or local services."""
    with pytest.raises(ValueError):
        github_source(url, True)


def test_remote_size_limit_and_redirect():
    """Oversized responses and redirections fail before becoming evidence."""
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b"x" * 250001))
    with httpx.Client(transport=transport) as client, pytest.raises(ValueError, match="limit"):
        bounded_json(client, "GET", "https://example.test")
    transport = httpx.MockTransport(
        lambda request: httpx.Response(302, headers={"Location": "http://private"})
    )
    with pytest.raises(httpx.HTTPStatusError):
        github_source("https://github.com/example/project", True, transport)
