"""Mocked provider contract tests; no live model charges or personal data transmission."""

# Index: base64@4, json@5, httpx@7, pytest@8, given@9, settings@9, st@10, samples@12, ai_review@13, bounded_json@13, github_source@13, provider_config@13, test_provider_protocol_and_privacy@17, test_provider_protocol_and_privacy.kind@17, test_provider_protocol_and_privacy.monkeypatch@17, test_provider_protocol_and_privacy.jobs@19, test_provider_protocol_and_privacy.people@19, test_provider_protocol_and_privacy.person@20, test_provider_protocol_and_privacy.respond@27, test_provider_protocol_and_privacy.respond.request@27, test_provider_protocol_and_privacy.respond.value@29, test_provider_protocol_and_privacy.respond.data@30, test_provider_protocol_and_privacy.respond.raw@33, test_provider_protocol_and_privacy.respond.result@34, test_provider_protocol_and_privacy.result@41, test_bad_provider_endpoints@55, test_bad_provider_endpoints.monkeypatch@55, test_bad_provider_endpoints.url@55, test_missing_model_and_consent@63, test_missing_model_and_consent.monkeypatch@63, test_missing_model_and_consent.jobs@68, test_missing_model_and_consent.people@68, test_github_only_selected_public_readme@73, test_github_only_selected_public_readme.content@75, test_github_only_selected_public_readme.respond@77, test_github_only_selected_public_readme.respond.request@77, test_github_only_selected_public_readme.result@90, test_profile_ssrf_urls@104, test_profile_ssrf_urls.url@104, test_remote_size_limit_and_redirect@110, test_remote_size_limit_and_redirect.request@112, test_remote_size_limit_and_redirect.transport@112, test_remote_size_limit_and_redirect.client@113, test_remote_size_limit_and_redirect.transport@115, test_remote_size_limit_and_redirect.request@116, test_github_validated_segments_never_change_authority_or_readme_resource.value@128, test_github_validated_segments_never_change_authority_or_readme_resource@131, test_github_validated_segments_never_change_authority_or_readme_resource.owner@131, test_github_validated_segments_never_change_authority_or_readme_resource.repository@131, test_github_validated_segments_never_change_authority_or_readme_resource.requests@133, test_github_validated_segments_never_change_authority_or_readme_resource.respond@135, test_github_validated_segments_never_change_authority_or_readme_resource.respond.request@135, test_github_validated_segments_never_change_authority_or_readme_resource.result@148, test_github_delimiter_and_traversal_vectors_are_rejected_before_any_io@182, test_github_delimiter_and_traversal_vectors_are_rejected_before_any_io.url@182, test_github_delimiter_and_traversal_vectors_are_rejected_before_any_io.requests@184, test_github_delimiter_and_traversal_vectors_are_rejected_before_any_io.unexpected@186, test_github_delimiter_and_traversal_vectors_are_rejected_before_any_io.unexpected.request@186, test_github_redirect_targets_never_receive_a_second_request@204, test_github_redirect_targets_never_receive_a_second_request.target@204, test_github_redirect_targets_never_receive_a_second_request.requests@206, test_github_redirect_targets_never_receive_a_second_request.redirect@208, test_github_redirect_targets_never_receive_a_second_request.redirect.request@208
import base64
import json

import httpx
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

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


@given(
    owner=st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-", min_size=1, max_size=39
    ),
    repository=st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-", min_size=1, max_size=100
    ).filter(lambda value: value not in {".", ".."}),
)
@settings(max_examples=60, derandomize=True, deadline=500)
def test_github_validated_segments_never_change_authority_or_readme_resource(owner, repository):
    """Exercise accepted path components against the actual HTTPX URL parser, never the network."""
    requests = []

    def respond(request):
        """Reject any protocol, authority, query, credential or resource drift in the real request."""
        requests.append(request)
        assert request.method == "GET"
        assert request.url.scheme == "https"
        assert request.url.host == "api.github.com"
        assert request.url.port in {None, 443}
        assert request.url.username == "" and request.url.password == ""
        assert request.url.query == b"" and request.url.fragment == ""
        assert request.url.raw_path == f"/repos/{owner}/{repository}/readme".encode("ascii")
        assert "authorization" not in request.headers
        return httpx.Response(200, json={"encoding": "base64", "size": 9, "content": "U3ludGhldGlj"})

    result = github_source(f"https://github.com/{owner}/{repository}", True, httpx.MockTransport(respond))
    assert len(requests) == 1 and result["text"] == "Synthetic"


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com@127.0.0.1/owner/repo",
        "https://github.com:443/owner/repo",
        "https://github.com/owner/..",
        "https://github.com/owner/.",
        "https://github.com/owner/repo/../../admin",
        "https://github.com/owner/%2e%2e",
        "https://github.com/owner/repo%2f..",
        "https://github.com/owner/repo?next=http://127.0.0.1",
        "https://github.com/owner/repo#http://169.254.169.254",
        "https://github.com/owner/repo\\admin",
        "https://github.com/owner/repo\r\nHost:127.0.0.1",
        "https://github.com/owner/repo\n",
        "https://github.com/owner/repo%00",
        "https://github.com/owner/repo%3fquery",
        "https://github.com./owner/repo",
        "https://github.com.evil.test/owner/repo",
        "https://127.0.0.1/owner/repo",
        "http://169.254.169.254/latest/meta-data",
        "file:///private",
        "gopher://127.0.0.1/",
        "https://github.com/ownér/repo",
        "https://github.com/owner/repο",
        "https://github.com//owner/repo",
        "https://github.com/" + "x" * 40 + "/repo",
        "https://github.com/owner/" + "r" * 101,
    ],
)
def test_github_delimiter_and_traversal_vectors_are_rejected_before_any_io(url):
    """Prove malicious URL forms cannot reach even the injected test transport."""
    requests = []

    def unexpected(request):
        """Record accidental outbound work without contacting a real destination."""
        requests.append(request)
        raise AssertionError("Rejected URL reached HTTP transport")

    with pytest.raises(ValueError):
        github_source(url, True, httpx.MockTransport(unexpected))
    assert requests == []


@pytest.mark.parametrize(
    "target",
    [
        "http://127.0.0.1/private",
        "http://169.254.169.254/latest/meta-data",
        "https://api.github.com.evil.test/admin",
    ],
)
def test_github_redirect_targets_never_receive_a_second_request(target):
    """A fixed-host README request does not become authority to follow an attacker-controlled redirect."""
    requests = []

    def redirect(request):
        """Return an untrusted Location while retaining the count and fixed first authority."""
        requests.append(str(request.url))
        return httpx.Response(302, headers={"Location": target})

    with pytest.raises(httpx.HTTPStatusError):
        github_source("https://github.com/example/project", True, httpx.MockTransport(redirect))
    assert requests == ["https://api.github.com/repos/example/project/readme"]
