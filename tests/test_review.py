"""Domain regression/property tests for evidence scoring, privacy and factual coaching."""

# Index: json@4, pytest@6, given@7, settings@7, st@8, ValidationError@9, samples@11, Applicant@12, Criterion@12, Education@12, Evidence@12, Job@12, Source@12, payload@13, validate_plan@13, assess@14, coach@14, rank@14, recommend@14, resume_html@14, candidate@17, candidate.level@17, candidate.reviewed@17, role@37, test_levels@47, test_levels.level@47, test_levels.score@47, test_unknown_not_failure_and_required_review@52, test_unknown_not_failure_and_required_review.result@54, test_duplicate_claims_never_boost@60, test_duplicate_claims_never_boost.person@62, test_duplicate_claims_never_boost.first@63, test_duplicate_claims_never_boost.index@64, test_identity_raw_text_invariance@70, test_identity_raw_text_invariance.name@70, test_identity_raw_text_invariance.text@70, test_identity_raw_text_invariance.person@72, test_identity_raw_text_invariance.original@73, test_identity_raw_text_invariance.provider@74, test_sensitive_arbitrary_criteria_rejected@88, test_sensitive_arbitrary_criteria_rejected.skill@88, test_education_transfer_not_degree_inference@94, test_education_transfer_not_degree_inference.person@96, test_education_transfer_not_degree_inference.result@101, test_education_transfer_not_degree_inference.draft@103, test_education_transfer_not_degree_inference.flag@107, test_score_bound_and_tie_rank@110, test_score_bound_and_tie_rank.first@112, test_score_bound_and_tie_rank.second@112, test_score_bound_and_tie_rank.results@115, test_score_bound_and_tie_rank.result@116, test_score_bound_and_tie_rank.result@117, test_demo_different_strengths@120, test_demo_different_strengths.jobs@122, test_demo_different_strengths.people@122, test_ai_payload_opaque_ids_and_no_raw_fields@128, test_ai_payload_opaque_ids_and_no_raw_fields.person@130, test_ai_payload_opaque_ids_and_no_raw_fields.data@131, test_ai_payload_opaque_ids_and_no_raw_fields.serialized@132, test_ai_payload_opaque_ids_and_no_raw_fields.result@139, test_hallucinated_ai_outputs_fail_closed@155, test_hallucinated_ai_outputs_fail_closed.raw@155, test_cross_skill_citation_rejected@161, test_cross_skill_citation_rejected.job@163, test_factual_download_escapes_and_unreviewed_omission@171, test_factual_download_escapes_and_unreviewed_omission.person@173, test_factual_download_escapes_and_unreviewed_omission.draft@176, test_coaching_general_and_gap_projects@183, test_coaching_general_and_gap_projects.person@185, test_coaching_general_and_gap_projects.tailored@187, test_job_drafts_and_unique_criteria@192, test_job_drafts_and_unique_criteria.criterion@194, test_unique_citations_and_extra_fields@204, test_unique_citations_and_extra_fields.data@206, test_unique_citations_and_extra_fields.data@210, test_unique_citations_and_extra_fields.index@211, test_unique_citations_and_extra_fields.data@215
import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.demo import samples
from app.models import Applicant, Criterion, Education, Evidence, Job, Source
from app.providers import payload, validate_plan
from app.review import assess, coach, rank, recommend, resume_html


def candidate(level="demonstrated", reviewed=True):
    """Build a minimal valid record with one cited Python claim."""
    return Applicant(
        id="test",
        display_name="Test",
        sources=[Source(id="s", label="work", kind="work_sample", text="private")],
        evidence=[
            Evidence(
                id="custom_sensitive_id",
                skill="python",
                kind="coursework",
                level=level,
                summary="Own implementation",
                source_id="s",
                reviewed=reviewed,
            )
        ],
    )


def role():
    """One target makes expected fractions explicit rather than duplicating production logic."""
    return Job(
        id="j", title="Engineer", criteria=[Criterion(skill="python", target="demonstrated", weight=5)]
    )


@pytest.mark.parametrize(
    ("level", "score"), [("declared", 33.3), ("practiced", 66.7), ("demonstrated", 100), ("assessed", 100)]
)
def test_levels(level, score):
    """Evidence quality earns capped rubric coverage, not years of employment."""
    assert assess(candidate(level), role())["score"] == score


def test_unknown_not_failure_and_required_review():
    """No reviewed evidence yields a clarification flag and no hiring verdict."""
    result = assess(candidate(reviewed=False), role())
    assert result["score"] == 0 and result["status"] == "needs_review"
    assert result["criteria"][0]["level"] == "not_evidenced"
    assert "reject" not in result and "hire" not in result


def test_duplicate_claims_never_boost():
    """Repeated portfolio claims and keywords cannot inflate skill attainment."""
    person = candidate("practiced")
    first = assess(person, role())["score"]
    person.evidence.extend([person.evidence[0].model_copy(update={"id": f"d{index}"}) for index in range(50)])
    assert assess(person, role())["score"] == first


@given(st.text(max_size=240), st.text(max_size=1000))
@settings(max_examples=100)
def test_identity_raw_text_invariance(name, text):
    """Changing personal/irrelevant source text cannot change scores or provider inputs."""
    person = candidate()
    original = assess(person, role())
    provider = payload(person, role())
    person.display_name = name
    person.notes = text
    person.sources[0].text = text
    person.evidence[0].summary = text
    person.education = [Education(institution=name[:240], program="Unrelated", status="unclear")]
    assert assess(person, role())["score"] == original["score"]
    assert payload(person, role()) == provider


@pytest.mark.parametrize(
    "skill",
    ["race", "gender", "religion", "age", "disability", "address", "school_prestige", "female_python"],
)
def test_sensitive_arbitrary_criteria_rejected(skill):
    """Custom criteria must not add protected traits or proxies to the ranking schema."""
    with pytest.raises(ValidationError):
        Criterion(skill=skill)


def test_education_transfer_not_degree_inference():
    """Transfer and career-change context is preserved without changing a skill score."""
    person = candidate()
    person.education = [
        Education(institution="First", program="Physics", status="transferred", transferred_to="Second"),
        Education(institution="Second", program="CS", status="in_progress"),
    ]
    result = assess(person, role())
    assert result["score"] == 100
    draft = resume_html(person, role())
    assert "transferred to Second" in draft and "in progress" in draft
    assert "verified months" not in draft and "not converted into employment years" in draft
    person.education[0].transferred_to = ""
    assert any("Transfer destination" in flag for flag in assess(person, role())["flags"])


def test_score_bound_and_tie_rank():
    """Ties share ranks regardless of names; low evidence remains reviewable."""
    first, second = candidate(), candidate()
    first.id, second.id = "z", "a"
    first.display_name, second.display_name = "AAA", "ZZZ"
    results = rank([first, second], role())
    assert [result["rank"] for result in results] == [1, 1]
    assert [result["applicant_id"] for result in results] == ["a", "z"]


def test_demo_different_strengths():
    """Synthetic portfolio and industrial samples rank differently by the selected role."""
    jobs, people = samples()
    assert rank(people, jobs[0])[0]["applicant_id"] == "A101"
    assert rank(people, jobs[1])[0]["applicant_id"] == "A102"
    assert rank(people, jobs[2])[0]["applicant_id"] == "A103"


def test_ai_payload_opaque_ids_and_no_raw_fields():
    """Even caller-controlled evidence IDs cannot leak identity to a model."""
    person = candidate()
    data = payload(person, role())
    serialized = json.dumps(data)
    assert (
        "custom_sensitive_id" not in serialized
        and "private" not in serialized
        and "Own implementation" not in serialized
    )
    assert data["evidence"][0]["id"] == "e0"
    result = validate_plan(
        '{"suggestions":[{"skill":"python","evidence_ids":["e0"],"action":"test"}]}', person, role()
    )
    assert result["suggestions"][0]["evidence_ids"] == ["custom_sensitive_id"]


@pytest.mark.parametrize(
    "raw",
    [
        '{"suggestions":[{"skill":"gender","evidence_ids":[],"action":"test"}]}',
        '{"suggestions":[{"skill":"python","evidence_ids":["fake"],"action":"test"}]}',
        '{"suggestions":[{"skill":"python","evidence_ids":[],"action":"hire"}]}',
        '{"suggestions":[],"score":99}',
        "not json",
    ],
)
def test_hallucinated_ai_outputs_fail_closed(raw):
    """Unrecognized skills, citations, decisions or JSON must never become advice."""
    with pytest.raises(ValueError):
        validate_plan(raw, candidate(), role())


def test_cross_skill_citation_rejected():
    """A real citation for an unrelated skill cannot justify a recommendation."""
    job = role()
    job.criteria.append(Criterion(skill="sql"))
    with pytest.raises(ValueError):
        validate_plan(
            '{"suggestions":[{"skill":"sql","evidence_ids":["e0"],"action":"test"}]}', candidate(), job
        )


def test_factual_download_escapes_and_unreviewed_omission():
    """Downloaded HTML cannot run source markup and excludes unapproved accomplishments."""
    person = candidate()
    person.display_name = "<script>alert(1)</script>"
    person.evidence[0].summary = "<img src=x onerror=alert(1)>"
    draft = resume_html(person)
    assert "<script>" not in draft and "<img src=x" not in draft and "&lt;script&gt;" in draft
    person.evidence[0].reviewed = False
    assert "Own implementation" not in resume_html(person)
    assert "No reviewed claims supplied" in resume_html(person)


def test_coaching_general_and_gap_projects():
    """General coaching and tailored portfolio recommendations remain distinct."""
    person = candidate("practiced")
    assert coach(person)["general"] is True
    tailored = coach(person, role())
    assert tailored["projects"][0]["skill"] == "python"
    assert "CI workflow" in tailored["projects"][0]["steps"][1]


def test_job_drafts_and_unique_criteria():
    """Job recommendation is a transparent taxonomy draft, not arbitrary keyword ranking."""
    assert {criterion.skill for criterion in recommend("C++ Python SQL tests and gender")} == {
        "cpp",
        "python",
        "sql",
        "testing",
    }
    with pytest.raises(ValidationError):
        Job(id="j", title="j", criteria=[Criterion(skill="python"), Criterion(skill="python")])


def test_unique_citations_and_extra_fields():
    """Malformed source relationships and unexpected personal fields are rejected."""
    data = candidate().model_dump()
    data["race"] = "irrelevant"
    with pytest.raises(ValidationError):
        Applicant.model_validate(data)
    data = candidate().model_dump()
    data["sources"] = [{**data["sources"][0], "id": f"s{index}", "text": "x" * 80000} for index in range(3)]
    data["evidence"] = []
    with pytest.raises(ValidationError, match="Combined source"):
        Applicant.model_validate(data)
    data = candidate().model_dump()
    data["evidence"][0]["source_id"] = "missing"
    with pytest.raises(ValidationError):
        Applicant.model_validate(data)
