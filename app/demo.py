"""Clearly synthetic professional records demonstrate transfers, uncertainty and work quality."""

# Index: Applicant@4, Criterion@4, Education@4, Evidence@4, Job@4, Source@4, samples@7, samples.jobs@9, samples.specifications@50, samples.applicants@106, samples.identifier@107, samples.kind@107, samples.level@107, samples.months@107, samples.name@107, samples.skills@107, samples.summary@107, samples.source@108, samples.evidence@115, samples.index@126, samples.skill@126, samples.education@128, samples.education@130, samples.education@146
from app.models import Applicant, Criterion, Education, Evidence, Job, Source


def samples() -> tuple[list[Job], list[Applicant]]:
    """Build deterministic synthetic examples; no real applicant or contact data is included."""
    jobs = [
        Job(
            id="software",
            title="Software Engineer — Integration Systems",
            description="Python and TypeScript APIs, SQL, reliable automated testing and documented delivery.",
            criteria=[
                Criterion(skill="python", weight=4),
                Criterion(skill="typescript", weight=3),
                Criterion(skill="sql", weight=3),
                Criterion(skill="testing", weight=5),
                Criterion(skill="api_design", weight=4),
                Criterion(skill="documentation", weight=2, required=False),
            ],
        ),
        Job(
            id="embedded",
            title="Embedded / Industrial Software Engineer",
            description="C++ on Linux, embedded protocols, testing and clear engineering documentation.",
            criteria=[
                Criterion(skill="cpp", weight=5),
                Criterion(skill="linux", weight=3),
                Criterion(skill="embedded", weight=4),
                Criterion(skill="protocols", weight=3),
                Criterion(skill="testing", weight=4),
                Criterion(skill="documentation", weight=2, required=False),
            ],
        ),
        Job(
            id="data",
            title="Data Analyst / Applied ML Developer",
            description="Python, SQL, statistics, data analysis, machine learning and testable experiments.",
            criteria=[
                Criterion(skill="python", weight=4),
                Criterion(skill="sql", weight=4),
                Criterion(skill="statistics", weight=4),
                Criterion(skill="data_analysis", weight=5),
                Criterion(skill="machine_learning", weight=3),
                Criterion(skill="testing", weight=3),
            ],
        ),
    ]
    specifications = [
        (
            "A101",
            "Morgan Rivera (synthetic)",
            ["python", "typescript", "sql", "testing", "api_design", "documentation"],
            "demonstrated",
            "project",
            None,
            "Integration console: implemented schema validation, parameterized queries, retry limits, 48 regression tests and a reproducible load script.",
        ),
        (
            "A102",
            "Taylor Chen (synthetic)",
            ["cpp", "linux", "embedded", "protocols", "testing", "documentation"],
            "demonstrated",
            "work_sample",
            18,
            "Controller simulator: implemented bounded buffers, protocol decoding, malformed-frame tests, Linux build instructions and sanitizer checks.",
        ),
        (
            "A103",
            "Jordan Ellis (synthetic)",
            ["python", "sql", "statistics", "data_analysis", "machine_learning", "testing"],
            "practiced",
            "coursework",
            None,
            "Advanced data coursework: wrote reproducible notebooks, leakage checks, a held-out evaluation and a SQL analysis with explicit limitations.",
        ),
        (
            "A104",
            "Casey Stone (synthetic)",
            ["python", "typescript", "sql", "testing", "api_design"],
            "declared",
            "project",
            None,
            "Resume lists technologies; repository ownership, tests and reproducible results have not yet been supplied.",
        ),
        (
            "A105",
            "Riley Park (synthetic)",
            ["python", "testing", "api_design"],
            "demonstrated",
            "project",
            6,
            "Career-change work sample: implemented an HTTP service, request bounds, failing-input tests and documented trade-offs.",
        ),
        (
            "A106",
            "Sam Quinn (synthetic)",
            ["typescript", "sql", "testing"],
            "assessed",
            "work_sample",
            None,
            "Synthetic reviewer-assessed work sample: traced query plans, implemented UI validation and reproduced edge-case tests.",
        ),
    ]
    applicants = []
    for identifier, name, skills, level, kind, months, summary in specifications:
        source = Source(
            id="portfolio",
            label="Synthetic professional evidence",
            kind="work_sample",
            text=summary,
            warnings=["This entire record is synthetic; no real repository or test result is claimed."],
        )
        evidence = [
            Evidence(
                id=f"e{index}",
                skill=skill,
                kind=kind,
                level=level,
                summary=summary,
                source_id=source.id,
                locator="Synthetic work-sample description",
                reviewed=identifier != "A104",
            )
            for index, skill in enumerate(skills)
        ]
        education = []
        if identifier == "A101":
            education = [
                Education(
                    institution="North Valley College (synthetic)",
                    program="Electrical Engineering coursework",
                    status="transferred",
                    transferred_to="Metro University (synthetic)",
                    notes="Changed major; credits transferred. No degree awarded by the first school is claimed.",
                ),
                Education(
                    institution="Metro University (synthetic)",
                    program="BS Computer Science",
                    status="completed",
                    notes="Completion explicitly stated in this synthetic record.",
                ),
            ]
        if identifier == "A104":
            education = [
                Education(
                    institution="Central Institute (synthetic)",
                    program="Computer Science",
                    status="unclear",
                    notes="Dates listed without an explicit degree outcome.",
                )
            ]
        applicants.append(
            Applicant(
                id=identifier,
                display_name=name,
                sources=[source],
                evidence=evidence,
                education=education,
                verified_employment_months=months,
                consent_sources=True,
                consent_ai=False,
                notes="Synthetic portfolio demonstration; replace only with consented real records in private local storage.",
            )
        )
    return jobs, applicants
