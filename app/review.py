"""Explainable advisory scoring and factual coaching; no identity or raw text inputs.

Scoring is O(E+C) per applicant, sorting O(N log N). Best evidence per skill
prevents duplicate claims from boosting scores. Unknown evidence is not a failure.
"""

# Index: hashlib@8, html@9, json@10, Applicant@12, Criterion@12, Job@12, Level@12, SKILLS@12, POINTS@14, NOTICE@15, assess@18, assess.applicant@18, assess.job@18, assess.best@20, assess.evidence@21, assess.rows@26, assess.criterion@27, assess.evidence@28, assess.attainment@29, assess.score@43, assess.row@44, assess.flags@46, assess.evidence@47, assess.record@49, assess.record@51, assess.source@53, assess.gaps@55, assess.row@55, assess.status@60, assess.fingerprint@61, assess.criterion@62, rank@77, rank.applicants@77, rank.job@77, rank.results@79, rank.applicant@80, rank.row@81, rank.last_score@83, rank.position@84, rank.index@85, rank.result@85, rank.position@87, rank.last_score@88, recommend@93, recommend.description@93, recommend.re@95, recommend.aliases@97, recommend.text@107, recommend.selected@108, recommend.label@109, recommend.skill@109, recommend.terms@110, recommend.term@111, coach@116, coach.applicant@116, coach.job@116, coach.evidence@118, coach.reviewed@118, coach.scores@119, coach.gaps@120, coach.row@120, coach.advice@121, coach.projects@134, coach.skill@135, resume_html@164, resume_html.applicant@164, resume_html.job@164, resume_html.ordered@166, resume_html.evidence@167, resume_html.evidence@168, resume_html.criterion@169, resume_html.items@173, resume_html.evidence@175, resume_html.education@177, resume_html.record@181, resume_html.duration@183
import hashlib
import html
import json

from app.models import SKILLS, Applicant, Criterion, Job, Level

POINTS = {Level.DECLARED: 1, Level.PRACTICED: 2, Level.DEMONSTRATED: 3, Level.ASSESSED: 4}
NOTICE = "Advisory evidence ranking only. Read the original application and cited work before making a hiring decision."


def assess(applicant: Applicant, job: Job) -> dict:
    """Compute a rubric score from reviewed claims; return gaps and uncertainty separately."""
    best = {}
    for evidence in applicant.evidence:
        if evidence.reviewed and (
            evidence.skill not in best or POINTS[evidence.level] > POINTS[best[evidence.skill].level]
        ):
            best[evidence.skill] = evidence
    rows = []
    for criterion in job.criteria:
        evidence = best.get(criterion.skill)
        attainment = min(1.0, POINTS[evidence.level] / POINTS[criterion.target]) if evidence else 0
        rows.append(
            {
                "skill": criterion.skill,
                "label": SKILLS[criterion.skill],
                "weight": criterion.weight,
                "required": criterion.required,
                "target": criterion.target,
                "attainment": round(attainment, 4),
                "evidence_id": evidence.id if evidence else None,
                "source_id": evidence.source_id if evidence else None,
                "level": evidence.level if evidence else "not_evidenced",
            }
        )
    score = round(
        100 * sum(row["weight"] * row["attainment"] for row in rows) / sum(row["weight"] for row in rows), 1
    )
    flags = []
    if any(not evidence.reviewed for evidence in applicant.evidence):
        flags.append("Unreviewed claims are excluded from scoring; inspect their sources.")
    if any(record.status == "unclear" for record in applicant.education):
        flags.append("Education outcome unclear: ask the applicant rather than assuming a degree or failure.")
    if any(record.status == "transferred" and not record.transferred_to for record in applicant.education):
        flags.append("Transfer destination missing: clarify the chronology; no degree is inferred.")
    if any(source.warnings for source in applicant.sources):
        flags.append("A source has extraction or access warnings; check the original document.")
    gaps = [row["skill"] for row in rows if row["required"] and row["attainment"] < 1]
    if gaps:
        flags.append(
            "Required evidence gaps need clarification or a relevant work sample, not automatic rejection."
        )
    status = "needs_review" if flags else ("strong_evidence" if score >= 80 else "partial_evidence")
    fingerprint = hashlib.sha256(
        json.dumps([criterion.model_dump(mode="json") for criterion in job.criteria], sort_keys=True).encode()
    ).hexdigest()[:16]
    return {
        "applicant_id": applicant.id,
        "score": score,
        "status": status,
        "criteria": rows,
        "flags": flags,
        "required_gaps": gaps,
        "rubric_hash": fingerprint,
        "notice": NOTICE,
        "method": "reviewed-evidence-rubric-v1",
    }


def rank(applicants: list[Applicant], job: Job) -> list[dict]:
    """Order high-to-low scores; equal scores share rank, IDs only stabilize display order."""
    results = sorted(
        [assess(applicant, job) for applicant in applicants],
        key=lambda row: (-row["score"], row["applicant_id"]),
    )
    last_score = None
    position = 0
    for index, result in enumerate(results):
        if result["score"] != last_score:
            position = index + 1
            last_score = result["score"]
        result["rank"] = position
    return results


def recommend(description: str) -> list[Criterion]:
    """Draft taxonomy-only criteria from job text; human approval is required before use."""
    import re

    aliases = {
        "cpp": ["c++"],
        "csharp": ["c#"],
        "html_css": ["html", "css"],
        "api_design": ["api", "rest"],
        "git_ci": ["git", "ci/cd"],
        "testing": ["test", "tests", "testing"],
        "machine_learning": ["machine learning"],
        "deep_learning": ["deep learning"],
    }
    text = description.casefold()
    selected = []
    for skill, label in SKILLS.items():
        terms = aliases.get(skill, [skill.replace("_", " "), label.casefold()])
        if any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text) for term in terms):
            selected.append(Criterion(skill=skill))
    return selected or [Criterion(skill="requirements"), Criterion(skill="documentation")]


def coach(applicant: Applicant, job: Job | None = None) -> dict:
    """Offer actionable gap projects and truthful profile advice, without inventing achievements."""
    reviewed = [evidence for evidence in applicant.evidence if evidence.reviewed]
    scores = assess(applicant, job) if job else None
    gaps = [row["skill"] for row in scores["criteria"] if row["attainment"] < 1] if scores else []
    advice = [
        "Show your contribution, design trade-offs, reproducible setup and test results for each project.",
        "Keep employment duration separate from coursework and project practice; never invent years or credentials.",
        "Link relevant portfolio work and explain what you implemented yourself; do not rely on stars or follower counts.",
    ]
    if applicant.education:
        advice.append(
            "State completed degrees explicitly. Label transfers, coursework and current study as such, with their chronology."
        )
    if not reviewed:
        advice.append(
            "Review and approve source-linked professional evidence before generating a factual resume draft."
        )
    projects = []
    for skill in gaps[:8]:
        projects.append(
            {
                "skill": skill,
                "title": f"{SKILLS[skill]} evidence lab",
                "steps": [
                    f"Build a small job-relevant example demonstrating {SKILLS[skill]}; document the problem and your own contribution.",
                    "Include unit, integration, negative-input and regression tests plus a CI workflow.",
                    "Record a reproducible benchmark, limitations, security considerations and a concise architecture explanation.",
                    "Publish only data and code you have permission to share. Report actual outcomes, not promised results.",
                ],
            }
        )
    return {
        "advice": advice,
        "projects": projects,
        "linkedin": [
            "Add a concise projects section with links, your responsibilities, technology choices and measured results you can substantiate.",
            "Describe relevant advanced coursework as coursework, not employment; explicitly label transfers and earned qualifications.",
        ],
        "resume": [
            "Lead with reviewed skills relevant to the selected role; keep evidence-backed outcomes.",
            "Use a simple single-column layout and consistent headings. Verify every fact before submission.",
        ],
        "assessment": scores,
        "general": job is None,
    }


def resume_html(applicant: Applicant, job: Job | None = None) -> str:
    """Return an escaped, printable factual draft; preserve education qualifiers and no invented outcomes."""
    ordered = sorted(
        [evidence for evidence in applicant.evidence if evidence.reviewed],
        key=lambda evidence: (
            0 if job and evidence.skill in {criterion.skill for criterion in job.criteria} else 1,
            evidence.skill,
        ),
    )
    items = "".join(
        f"<li><strong>{html.escape(SKILLS[evidence.skill])}</strong> ({html.escape(evidence.kind)}): {html.escape(evidence.summary)}</li>"
        for evidence in ordered
    )
    education = "".join(
        f"<li>{html.escape(record.institution)} — {html.escape(record.program)}; {record.status.replace('_', ' ')}"
        + (f"; transferred to {html.escape(record.transferred_to)}" if record.transferred_to else "")
        + f". {html.escape(record.notes)}</li>"
        for record in applicant.education
    )
    duration = (
        "Not supplied / not verified"
        if applicant.verified_employment_months is None
        else f"{applicant.verified_employment_months} verified months"
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Resume draft</title>
<style>body{{font:16px Arial,sans-serif;line-height:1.6;max-width:760px;margin:40px auto;padding:24px;color:#162b37}}h1,h2{{line-height:1.2}}li{{margin:10px 0}}.notice{{border:1px solid #789;padding:12px}}@media print{{.notice{{display:none}}body{{margin:0}}}}</style></head>
<body><div class="notice">Draft: verify all facts before use. Only reviewed claims included. Print to PDF if desired.</div>
<h1>{html.escape(applicant.display_name)}</h1><p>{html.escape(job.title) if job else "Professional skills and project evidence"}</p>
<h2>Relevant evidence</h2><ul>{items or "<li>No reviewed claims supplied.</li>"}</ul><h2>Education and transitions</h2><ul>{education or "<li>Not supplied.</li>"}</ul>
<h2>Employment duration</h2><p>{duration}; coursework and projects are not converted into employment years.</p></body></html>"""
