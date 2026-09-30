"""Consent-gated AI and public GitHub evidence adapters with bounded, non-executing I/O.

AI receives taxonomy IDs and structured evidence strengths only, never identity,
resume text, school, employment dates, source URLs or free-form job instructions.
Model output is a constrained coaching plan, not an unchecked hiring decision.
"""

# Index: base64@9, json@10, os@11, re@12, urlsplit@13, httpx@15, Field@16, Applicant@18, Job@18, Model@18, assess@19, ACTION_TEXT@21, Suggestion@30, Suggestion.skill@33, Suggestion.evidence_ids@34, Suggestion.action@35, Plan@38, Plan.suggestions@41, payload@44, payload.applicant@44, payload.job@44, payload.criterion@47, payload.evidence@50, payload.index@50, payload.item@50, validate_plan@55, validate_plan.applicant@55, validate_plan.job@55, validate_plan.raw@55, validate_plan.plan@57, validate_plan.evidence@58, validate_plan.index@59, validate_plan.item@59, validate_plan.criterion@61, validate_plan.skills@61, validate_plan.suggestion@62, validate_plan.identifier@67, validate_plan.identifier@74, validate_plan.suggestion@77, provider_config@85, provider_config.kind@87, provider_config.endpoint@88, provider_config.model@89, provider_config.parsed@90, provider_config.local@91, bounded_json@107, bounded_json.client@107, bounded_json.kwargs@107, bounded_json.method@107, bounded_json.url@107, bounded_json.response@109, bounded_json.content@111, bounded_json.chunk@112, ai_review@119, ai_review.applicant@119, ai_review.consent@119, ai_review.job@119, ai_review.transport@119, ai_review.endpoint@123, ai_review.key@123, ai_review.kind@123, ai_review.model@123, ai_review.instruction@124, ai_review.messages@129, ai_review.body@133, ai_review.headers@140, ai_review.client@143, ai_review.data@144, ai_review.raw@145, ai_review.result@146, github_source@152, github_source.authorized@152, github_source.transport@152, github_source.url@152, github_source.match@156, github_source.owner@159, github_source.repository@159, github_source.endpoint@160, github_source.headers@161, github_source.client@162, github_source.data@163, github_source.decoded@166
import base64
import json
import os
import re
from urllib.parse import urlsplit

import httpx
from pydantic import Field

from app.models import Applicant, Job, Model
from app.review import assess

ACTION_TEXT = {
    "reproduce": "Add reproducible setup, inputs and expected outputs to the cited work.",
    "test": "Add meaningful automated tests and explain the edge cases they cover.",
    "ownership": "Explain your own contribution and separate it from group work.",
    "measure": "Include a reproducible performance measurement with environment and limitations.",
    "clarify": "Ask for a source-linked example or work sample before treating this qualification as established.",
}


class Suggestion(Model):
    """Only known skill IDs, known evidence IDs and bounded action codes are accepted."""

    skill: str
    evidence_ids: list[str] = Field(max_length=10)
    action: str


class Plan(Model):
    """Strict model response; free-form claims, scores and sensitive attributes are rejected."""

    suggestions: list[Suggestion] = Field(max_length=12)


def payload(applicant: Applicant, job: Job) -> dict:
    """Construct a deliberately narrow privacy boundary, independent of raw source content."""
    return {
        "rubric": [criterion.model_dump(mode="json") for criterion in job.criteria],
        "evidence": [
            {"id": f"e{index}", "skill": evidence.skill, "kind": evidence.kind, "level": evidence.level}
            for index, evidence in enumerate(item for item in applicant.evidence if item.reviewed)
        ],
    }


def validate_plan(raw: str, applicant: Applicant, job: Job) -> dict:
    """Reject hallucinated citations, mismatched skills and unsupported model instructions."""
    plan = Plan.model_validate_json(raw)
    evidence = {
        f"e{index}": item for index, item in enumerate(item for item in applicant.evidence if item.reviewed)
    }
    skills = {criterion.skill for criterion in job.criteria}
    for suggestion in plan.suggestions:
        if suggestion.skill not in skills or suggestion.action not in ACTION_TEXT:
            raise ValueError("AI returned an unsupported skill or action")
        if any(
            identifier not in evidence or evidence[identifier].skill != suggestion.skill
            for identifier in suggestion.evidence_ids
        ):
            raise ValueError("AI returned an invalid evidence citation")
    return {
        "suggestions": [
            {
                **suggestion.model_dump(),
                "evidence_ids": [evidence[identifier].id for identifier in suggestion.evidence_ids],
                "text": ACTION_TEXT[suggestion.action],
            }
            for suggestion in plan.suggestions
        ],
        "assessment": assess(applicant, job),
        "method": "AI-coaching-plus-reviewed-evidence-rubric",
        "unverified_ai": True,
    }


def provider_config() -> tuple[str, str, str, str]:
    """Read server-only settings; reject cleartext remote endpoints and URL credentials."""
    kind = os.environ.get("AES_AI_KIND", "ollama")
    endpoint = os.environ.get("AES_AI_URL", "http://127.0.0.1:11434/api/chat")
    model = os.environ.get("AES_AI_MODEL", "")
    parsed = urlsplit(endpoint)
    local = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if (
        kind not in {"ollama", "compatible"}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Invalid server AI configuration")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
        raise ValueError("Remote AI endpoints require HTTPS")
    if not model or len(model) > 200:
        raise ValueError("Set AES_AI_MODEL on the server before requesting AI coaching")
    return kind, endpoint, model, os.environ.get("AES_AI_KEY", "")


def bounded_json(client: httpx.Client, method: str, url: str, **kwargs) -> dict:
    """Bound streamed bytes before JSON parsing; redirects and proxy inheritance are disabled by callers."""
    with client.stream(method, url, **kwargs) as response:
        response.raise_for_status()
        content = bytearray()
        for chunk in response.iter_bytes():
            content.extend(chunk)
            if len(content) > 250000:
                raise ValueError("Remote response limit exceeded")
        return json.loads(content)


def ai_review(applicant: Applicant, job: Job, consent: bool, transport=None) -> dict:
    """Call one configured model only after both operator and applicant consent."""
    if not consent or not applicant.consent_ai:
        raise ValueError("Explicit operator approval and applicant AI consent are required")
    kind, endpoint, model, key = provider_config()
    instruction = (
        'Return JSON only: {"suggestions":[{"skill":"taxonomy key from rubric","evidence_ids":["matching evidence ID"],'
        '"action":"reproduce|test|ownership|measure|clarify"}]}. Choose useful evidence-improvement actions for this job. '
        "No personal traits, unsupported claims, hiring decisions or employment-year equivalences. Maximum 12 suggestions."
    )
    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": json.dumps(payload(applicant, job))},
    ]
    body = {"model": model, "messages": messages, "stream": False}
    if kind == "ollama":
        body["format"] = Plan.model_json_schema()
        body["options"] = {"temperature": 0, "num_predict": 1500}
    else:
        body["temperature"] = 0
        body["max_tokens"] = 1500
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    with httpx.Client(
        timeout=httpx.Timeout(30, connect=5), follow_redirects=False, trust_env=False, transport=transport
    ) as client:
        data = bounded_json(client, "POST", endpoint, json=body, headers=headers)
    raw = data["message"]["content"] if kind == "ollama" else data["choices"][0]["message"]["content"]
    result = validate_plan(raw, applicant, job)
    result["provider"] = kind
    result["model"] = model
    return result


def github_source(url: str, authorized: bool, transport=None) -> dict:
    """Fetch one authorized public repo's README, never code execution or broad social lookup."""
    if not authorized:
        raise ValueError("Applicant-authorized professional source required")
    match = re.fullmatch(r"https://github\.com/([A-Za-z0-9-]{1,39})/([A-Za-z0-9_.-]{1,100})/?", url)
    if not match or match[2] in {".", ".."}:
        raise ValueError("Provide an exact https://github.com/owner/repository URL")
    owner, repository = match.groups()
    endpoint = f"https://api.github.com/repos/{owner}/{repository}/readme"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "applicant-evidence-studio"}
    with httpx.Client(timeout=10, follow_redirects=False, trust_env=False, transport=transport) as client:
        data = bounded_json(client, "GET", endpoint, headers=headers)
    if data.get("encoding") != "base64" or data.get("size", 0) > 80000:
        raise ValueError("README unsupported or too large")
    decoded = base64.b64decode(data["content"], validate=False)
    if len(decoded) > 80000:
        raise ValueError("README limit exceeded")
    return {
        "text": decoded.decode("utf-8"),
        "url": url,
        "label": f"{owner}/{repository} README",
        "warnings": [
            "README claims are not proof of code quality or authorship. Review selected source, tests and contributions yourself."
        ],
    }
