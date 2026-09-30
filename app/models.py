"""Validated domain contracts; only vetted professional skills can influence ranking.

Free-text identity, sources and education remain available to human reviewers, but
are deliberately excluded from scoring and AI payloads. Variable maps are generated.
"""

# Index: StrEnum@8, Annotated@9, Literal@9, BaseModel@11, ConfigDict@11, Field@11, field_validator@11, model_validator@11, SKILLS@13, Id@51, Short@52, Model@55, Model.model_config@58, Level@61, Level.DECLARED@64, Level.PRACTICED@65, Level.DEMONSTRATED@66, Level.ASSESSED@67, Evidence@70, Evidence.id@73, Evidence.skill@74, Evidence.kind@75, Evidence.level@76, Evidence.summary@77, Evidence.source_id@78, Evidence.locator@79, Evidence.reviewed@80, Evidence.valid_skill@84, Evidence.valid_skill.cls@84, Evidence.valid_skill.value@84, Source@91, Source.id@94, Source.label@95, Source.kind@96, Source.text@97, Source.url@98, Source.warnings@99, Education@102, Education.institution@105, Education.program@106, Education.status@107, Education.transferred_to@108, Education.notes@109, Applicant@112, Applicant.id@115, Applicant.display_name@116, Applicant.consent_sources@117, Applicant.consent_ai@118, Applicant.sources@119, Applicant.evidence@120, Applicant.education@121, Applicant.verified_employment_months@122, Applicant.notes@123, Applicant.review_status@124, Applicant.references@127, Applicant.references.self@127, Applicant.references.source@129, Applicant.references.source_ids@129, Applicant.references.source@130, Applicant.references.evidence@132, Applicant.references.evidence_ids@132, Applicant.references.evidence@135, Criterion@140, Criterion.skill@143, Criterion.weight@144, Criterion.target@145, Criterion.required@146, Criterion._skill@147, Job@150, Job.id@153, Job.title@154, Job.description@155, Job.criteria@156, Job.unique_criteria@159, Job.unique_criteria.self@159, Job.unique_criteria.criterion@161, BulkImport@166, BulkImport.applicants@169, BulkImport.replace@170, Ingest@173, Ingest.filename@176, Ingest.content@177, RepositoryImport@180, RepositoryImport.url@183, RepositoryImport.authorized@184, AIRequest@187, AIRequest.job_id@190, AIRequest.applicant_id@191, AIRequest.consent@192
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SKILLS = {
    "python": "Python",
    "cpp": "C++",
    "csharp": "C#",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "rust": "Rust",
    "assembly": "Assembly",
    "php": "PHP",
    "bash": "Bash",
    "sql": "SQL",
    "html_css": "HTML / CSS",
    "testing": "Automated testing",
    "api_design": "API design",
    "security": "Application security",
    "accessibility": "Accessibility",
    "documentation": "Documentation",
    "git_ci": "Git / CI",
    "cloud": "Cloud deployment",
    "containers": "Containers",
    "data_analysis": "Data analysis",
    "statistics": "Statistics",
    "machine_learning": "Machine learning",
    "deep_learning": "Deep learning",
    "embedded": "Embedded software",
    "protocols": "Industrial protocols",
    "linux": "Linux",
    "game_engine": "Game engines",
    "graphics": "Graphics programming",
    "frontend": "Frontend development",
    "backend": "Backend development",
    "mobile": "Mobile development",
    "requirements": "Requirements analysis",
    "customer_support": "Customer support",
    "sales_analysis": "Sales analysis",
    "technical_writing": "Technical writing",
}
Id = Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")]
Short = Annotated[str, Field(max_length=240)]


class Model(BaseModel):
    """Reject unexpected fields instead of silently accepting extra personal attributes."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Level(StrEnum):
    """Evidence strength, not years of employment or a personality assessment."""

    DECLARED = "declared"
    PRACTICED = "practiced"
    DEMONSTRATED = "demonstrated"
    ASSESSED = "assessed"


class Evidence(Model):
    """One job-relevant claim; reviewed means a human checked the cited source."""

    id: Id
    skill: str
    kind: Literal["project", "coursework", "employment", "certification", "work_sample"]
    level: Level = Level.DECLARED
    summary: Annotated[str, Field(min_length=1, max_length=1200)]
    source_id: Id
    locator: Short = ""
    reviewed: bool = False

    @field_validator("skill")
    @classmethod
    def valid_skill(cls, value: str) -> str:
        """Validate a taxonomy key; arbitrary criteria cannot smuggle personal traits."""
        if value not in SKILLS:
            raise ValueError("Choose a vetted professional skill from the taxonomy")
        return value


class Source(Model):
    """Preserved, private source text for human verification, never an AI prompt."""

    id: Id
    label: Short
    kind: Literal["resume", "github", "linkedin", "work_sample", "other"]
    text: Annotated[str, Field(max_length=80000)]
    url: Annotated[str, Field(max_length=400)] = ""
    warnings: list[Short] = Field(default_factory=list, max_length=20)


class Education(Model):
    """Explicit chronology prevents assuming that every school awarded a degree."""

    institution: Short
    program: Short
    status: Literal["completed", "in_progress", "transferred", "coursework_only", "unclear"]
    transferred_to: Short = ""
    notes: Annotated[str, Field(max_length=1200)] = ""


class Applicant(Model):
    """Consistent record with provenance, consent, education context and skill claims."""

    id: Id
    display_name: Short
    consent_sources: bool = False
    consent_ai: bool = False
    sources: list[Source] = Field(default_factory=list, max_length=30)
    evidence: list[Evidence] = Field(default_factory=list, max_length=150)
    education: list[Education] = Field(default_factory=list, max_length=20)
    verified_employment_months: Annotated[int | None, Field(ge=0, le=1200)] = None
    notes: Annotated[str, Field(max_length=3000)] = ""
    review_status: Literal["pending", "reviewed", "clarification_requested"] = "pending"

    @model_validator(mode="after")
    def references(self):
        """Ensure unique local IDs and resolvable source citations; do not infer missing facts."""
        source_ids = [source.id for source in self.sources]
        if sum(len(source.text) for source in self.sources) > 200000:
            raise ValueError("Combined source text limit exceeded (200,000 characters)")
        evidence_ids = [evidence.id for evidence in self.evidence]
        if len(set(source_ids)) != len(source_ids) or len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("Duplicate source or evidence IDs")
        if any(evidence.source_id not in source_ids for evidence in self.evidence):
            raise ValueError("Every evidence claim needs a valid source")
        return self


class Criterion(Model):
    """Weighted job-relevant skill, with required gaps surfaced for human review."""

    skill: str
    weight: Annotated[int, Field(ge=1, le=10)] = 3
    target: Level = Level.DEMONSTRATED
    required: bool = True
    _skill = field_validator("skill")(Evidence.valid_skill.__func__)


class Job(Model):
    """Human-approved rubric; description is context, not hidden ranking features."""

    id: Id
    title: Short
    description: Annotated[str, Field(max_length=10000)] = ""
    criteria: list[Criterion] = Field(min_length=1, max_length=36)

    @model_validator(mode="after")
    def unique_criteria(self):
        """Avoid double weighting a skill by repeating it."""
        if len({criterion.skill for criterion in self.criteria}) != len(self.criteria):
            raise ValueError("Each skill can appear once in a rubric")
        return self


class BulkImport(Model):
    """Bounded atomic batch; identities cannot collide within an import."""

    applicants: list[Applicant] = Field(min_length=1, max_length=100)
    replace: bool = False


class Ingest(Model):
    """Bounded base64 upload avoids multipart temp files containing personal data."""

    filename: Short
    content: Annotated[str, Field(max_length=2800000)]


class RepositoryImport(Model):
    """Explicit authorization for one public professional repository, not people lookup."""

    url: Annotated[str, Field(max_length=400)]
    authorized: bool = False


class AIRequest(Model):
    """A deliberate, consented call; no background AI requests or hidden charges."""

    job_id: Id
    applicant_id: Id
    consent: bool = False
