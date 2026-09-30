"""Loopback-only API and browser application with authentication and bounded private storage.

All private routes need a per-process bearer token; no public multi-tenant hosting
is claimed. Body limits apply before JSON parsing and error responses omit inputs.
"""

# Index: secrets@8, Path@9, FastAPI@11, HTTPException@11, Query@11, Request@11, RequestValidationError@12, HTMLResponse@13, JSONResponse@13, Response@13, StaticFiles@14, Field@15, extract_isolated@17, proposed_claims@17, AIRequest@18, Applicant@18, BulkImport@18, Ingest@18, Job@18, Model@18, RepositoryImport@18, SKILLS@18, ai_review@19, github_source@19, NOTICE@20, assess@20, coach@20, rank@20, recommend@20, resume_html@20, Store@21, Edit@24, Edit.applicant@27, Edit.revision@28, Recommendation@31, Recommendation.description@34, Boundary@37, Boundary.__init__@40, Boundary.__init__.app@40, Boundary.__init__.origin@40, Boundary.__init__.self@40, Boundary.__init__.token@40, Boundary.__call__@44, Boundary.__call__.receive@44, Boundary.__call__.scope@44, Boundary.__call__.self@44, Boundary.__call__.send@44, Boundary.__call__.headers@48, Boundary.__call__.expected_host@49, Boundary.__call__.origin@50, Boundary.__call__.authorization@56, Boundary.__call__.body@61, Boundary.__call__.more@62, Boundary.__call__.message@64, Boundary.__call__.more@72, Boundary.__call__.consumed@73, Boundary.__call__.replay@75, Boundary.__call__.replay.consumed@79, Boundary.__call__.protected_send@83, Boundary.__call__.protected_send.message@83, create_app@101, create_app.data@102, create_app.origin@102, create_app.token@102, create_app.ui@102, create_app.app@107, create_app.store@108, create_app.invalid_request@113, create_app.invalid_request.error@113, create_app.invalid_request.request@113, create_app.invalid_request.item@118, create_app.invalid_value@124, create_app.invalid_value.error@124, create_app.invalid_value.request@124, create_app.missing_record@129, create_app.missing_record.error@129, create_app.missing_record.request@129, create_app.health@134, create_app.config@139, create_app.config.os@141, create_app.jobs@152, create_app.save_job@157, create_app.save_job.job@157, create_app.recommend_job@163, create_app.recommend_job.request@163, create_app.import_batch@171, create_app.import_batch.batch@171, create_app.queue@177, create_app.queue.job_id@178, create_app.queue.q@179, create_app.queue.skill@180, create_app.queue.status@181, create_app.queue.offset@182, create_app.queue.limit@183, create_app.queue.job@186, create_app.queue.applicants@187, create_app.queue.applicant@188, create_app.queue.records@188, create_app.queue.rows@189, create_app.queue.rows@192, create_app.queue.row@194, create_app.queue.evidence@200, create_app.applicant@217, create_app.applicant.identifier@217, create_app.applicant.record@219, create_app.applicant.revision@219, create_app.update_applicant@223, create_app.update_applicant.edit@223, create_app.update_applicant.identifier@223, create_app.delete_applicant@231, create_app.delete_applicant.identifier@231, create_app.ingest@240, create_app.ingest.upload@240, create_app.ingest.result@242, create_app.import_github@246, create_app.import_github.request@246, create_app.coaching@259, create_app.coaching.identifier@259, create_app.coaching.job_id@259, create_app.coaching._@261, create_app.coaching.record@261, create_app.draft@265, create_app.draft.identifier@265, create_app.draft.job_id@265, create_app.draft._@267, create_app.draft.record@267, create_app.export@274, create_app.export.identifier@274, create_app.export._@276, create_app.export.record@276, create_app.report@284, create_app.report.identifier@284, create_app.report.job_id@284, create_app.report.json@286, create_app.report._@288, create_app.report.record@288, create_app.ai@296, create_app.ai.request@296, create_app.ai._@298, create_app.ai.record@298
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import Field

from app.ingest import extract_isolated, proposed_claims
from app.models import SKILLS, AIRequest, Applicant, BulkImport, Ingest, Job, Model, RepositoryImport
from app.providers import ai_review, github_source
from app.review import NOTICE, assess, coach, rank, recommend, resume_html
from app.store import Store


class Edit(Model):
    """An optimistic-lock edit contains the full record and the revision it replaced."""

    applicant: Applicant
    revision: int = Field(ge=1)


class Recommendation(Model):
    """Bounded job description; draft recommendations must be human approved."""

    description: str = Field(max_length=10000)


class Boundary:
    """ASGI security boundary: trusted Host/Origin, authentication, body size and no-cache headers."""

    def __init__(self, app, token: str, origin: str):
        """Bind one explicit origin and one non-persisted session secret."""
        self.app, self.token, self.origin = app, token, origin

    async def __call__(self, scope, receive, send):
        """Reject unauthorized and oversized requests before route processing."""
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        expected_host = self.origin.split("://", 1)[1].encode()
        origin = headers.get(b"origin")
        if headers.get(b"host") != expected_host or (origin and origin.decode() != self.origin):
            return await JSONResponse({"detail": "Untrusted host or origin"}, status_code=403)(
                scope, receive, send
            )
        if scope["path"].startswith("/api/"):
            authorization = headers.get(b"authorization", b"").decode(errors="replace")
            if not secrets.compare_digest(authorization, "Bearer " + self.token):
                return await JSONResponse({"detail": "Session authorization required"}, status_code=401)(
                    scope, receive, send
                )
        body = bytearray()
        more = True
        while more:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 3_000_000:
                return await JSONResponse({"detail": "Request body limit exceeded"}, status_code=413)(
                    scope, receive, send
                )
            more = message.get("more_body", False)
        consumed = False

        async def replay():
            """Replay one bounded body to the downstream parser without repeated reads."""
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        async def protected_send(message):
            """Prevent private response caching, framing and content sniffing."""
            if message["type"] == "http.response.start":
                message["headers"] += [
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"x-frame-options", b"DENY"),
                    (
                        b"content-security-policy",
                        b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'",
                    ),
                ]
            await send(message)

        await self.app(scope, replay, protected_send)


def create_app(
    data: Path, token: str, origin: str = "http://127.0.0.1:8014", ui: Path | None = None
) -> FastAPI:
    """Create a private single-user service; caller controls its loopback origin and data directory."""
    if len(token) < 32:
        raise ValueError("Session tokens must be at least 32 characters")
    app = FastAPI(title="Applicant Evidence Studio", docs_url=None, redoc_url=None, openapi_url=None)
    store = Store(data / "applicants.db")
    app.state.store = store
    app.add_middleware(Boundary, token=token, origin=origin)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError):
        """Return locations and error kinds only; never echo private input or provider secrets."""
        return JSONResponse(
            {
                "detail": "Input validation failed",
                "fields": [{"location": list(item["loc"]), "type": item["type"]} for item in error.errors()],
            },
            status_code=422,
        )

    @app.exception_handler(ValueError)
    async def invalid_value(request: Request, error: ValueError):
        """Expose only controlled domain messages, not raw upstream exception payloads."""
        return JSONResponse({"detail": str(error)}, status_code=422)

    @app.exception_handler(KeyError)
    async def missing_record(request: Request, error: KeyError):
        """Missing record responses do not disclose private record contents."""
        return JSONResponse({"detail": "Record not found"}, status_code=404)

    @app.get("/health")
    def health():
        """Minimal non-private readiness check."""
        return {"ready": True, "version": "0.1.0", "mode": "local-single-user"}

    @app.get("/api/config")
    def config():
        """Expose safe taxonomy and capabilities, not keys or server endpoint credentials."""
        import os

        return {
            "skills": SKILLS,
            "notice": NOTICE,
            "ai_configured": bool(os.environ.get("AES_AI_MODEL")),
            "capacity": 10000,
            "file_types": ["txt", "md", "docx", "pdf"],
        }

    @app.get("/api/jobs")
    def jobs():
        """List approved job rubrics."""
        return store.jobs()

    @app.post("/api/jobs")
    def save_job(job: Job):
        """Validate and save job-related skill weights and target evidence levels."""
        store.save_job(job)
        return job

    @app.post("/api/recommend")
    def recommend_job(request: Recommendation):
        """Return editable draft criteria, never silently apply them to applicants."""
        return {
            "criteria": recommend(request.description),
            "notice": "Draft based on recognized professional skills. Review job relevance, weights and evidence levels before saving.",
        }

    @app.post("/api/import")
    def import_batch(batch: BulkImport):
        """Import up to 100 applicants atomically; explicit replacement prevents accidental overwrite."""
        store.import_applicants(batch.applicants, batch.replace)
        return {"imported": len(batch.applicants)}

    @app.get("/api/queue")
    def queue(
        job_id: str,
        q: str = Query(default="", max_length=100),
        skill: str = "",
        status: str = "",
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=25, ge=1, le=100),
    ):
        """Rank a bounded local pool, then filter and paginate without changing shared ranks."""
        job = store.job(job_id)
        applicants = store.applicants()
        records = {applicant.id: applicant for applicant in applicants}
        rows = rank(applicants, job)
        if skill and skill not in SKILLS:
            raise ValueError("Unknown skill filter")
        rows = [
            row
            for row in rows
            if (not status or row["status"] == status)
            and (
                not skill
                or any(
                    evidence.skill == skill and evidence.reviewed
                    for evidence in records[row["applicant_id"]].evidence
                )
            )
            and (
                not q
                or q.casefold()
                in (records[row["applicant_id"]].display_name + " " + row["applicant_id"]).casefold()
            )
        ]
        return {
            "total": len(rows),
            "pool_total": len(applicants),
            "items": rows[offset : offset + limit],
            "notice": NOTICE,
        }

    @app.get("/api/applicants/{identifier}")
    def applicant(identifier: str):
        """Return one standardized private record and its edit revision."""
        record, revision = store.applicant(identifier)
        return {"applicant": record, "revision": revision}

    @app.put("/api/applicants/{identifier}")
    def update_applicant(identifier: str, edit: Edit):
        """Save human evidence review, corrections and consent with a stale-edit guard."""
        if edit.applicant.id != identifier:
            raise ValueError("Path and applicant ID must match")
        store.save_applicant(edit.applicant, edit.revision)
        return {"saved": True, "revision": edit.revision + 1}

    @app.delete("/api/applicants/{identifier}")
    def delete_applicant(identifier: str):
        """Delete exactly one explicitly selected record."""
        store.delete(identifier)
        return {
            "deleted": True,
            "notice": "Deletion is not a secure filesystem wipe; manage backups and retention separately.",
        }

    @app.post("/api/ingest")
    def ingest(upload: Ingest):
        """Extract a supported resume without saving it or assuming qualifications."""
        result = extract_isolated(upload.filename, upload.content)
        return {**result, "proposals": proposed_claims(result["text"], "resume")}

    @app.post("/api/github")
    def import_github(request: RepositoryImport):
        """Fetch one explicitly authorized public professional README; no people search."""
        try:
            return github_source(request.url, request.authorized)
        except ValueError:
            raise
        except Exception as error:
            raise HTTPException(
                502,
                "Public repository unavailable, rate limited or unsupported. Paste an authorized export instead.",
            ) from error

    @app.get("/api/coach/{identifier}")
    def coaching(identifier: str, job_id: str | None = None):
        """Generate general or selected-job advice from the private structured record."""
        record, _ = store.applicant(identifier)
        return coach(record, store.job(job_id) if job_id else None)

    @app.get("/api/resume/{identifier}")
    def draft(identifier: str, job_id: str | None = None):
        """Download an escaped printable HTML draft with only reviewed facts."""
        record, _ = store.applicant(identifier)
        return HTMLResponse(
            resume_html(record, store.job(job_id) if job_id else None),
            headers={"Content-Disposition": 'attachment; filename="resume-draft.html"'},
        )

    @app.get("/api/export/{identifier}")
    def export(identifier: str):
        """Download a consistent source-linked JSON record for the selected applicant."""
        record, _ = store.applicant(identifier)
        return Response(
            record.model_dump_json(indent=2),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="applicant-record.json"'},
        )

    @app.get("/api/report/{identifier}")
    def report(identifier: str, job_id: str):
        """Download a criterion-by-criterion advisory report with rubric fingerprint and citations."""
        import json

        record, _ = store.applicant(identifier)
        return Response(
            json.dumps(assess(record, store.job(job_id)), indent=2),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="advisory-report.json"'},
        )

    @app.post("/api/ai")
    def ai(request: AIRequest):
        """Consent-gated AI coaching; the auditable score never becomes an opaque model verdict."""
        record, _ = store.applicant(request.applicant_id)
        try:
            return ai_review(record, store.job(request.job_id), request.consent)
        except ValueError as error:
            raise HTTPException(
                422,
                "AI request or response failed validation. Verify consent, model settings and valid citations.",
            ) from error
        except Exception as error:
            raise HTTPException(
                502,
                "AI provider unavailable or returned an unsupported response; offline review remains available.",
            ) from error

    if ui and ui.is_dir():
        app.mount("/", StaticFiles(directory=ui, html=True), name="ui")
    return app
