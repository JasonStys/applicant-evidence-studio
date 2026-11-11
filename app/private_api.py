"""Jason Stys: same-origin private accounts and ciphertext-only synchronization.

This public-capable service does NOT mount plaintext review, parser or AI routes.
TLS must terminate at a configured reverse proxy for non-loopback deployments.
"""

# Index: mimetypes@8, sqlite3@9, Path@10, urlsplit@11, FastAPI@13, HTTPException@13, Request@13, RequestValidationError@14, JSONResponse@15, StaticFiles@16, BaseModel@17, ConfigDict@17, Field@17, model_validator@17, VERSION@19, Accounts@20, SESSION_SECONDS@20, decode_field@20, CSP@22, Credentials@25, Credentials.model_config@28, Credentials.username@29, Credentials.password@30, Reset@33, Reset.recovery@36, Confirmation@39, Confirmation.model_config@42, Confirmation.password@43, Envelope@46, Envelope.model_config@49, Envelope.version@50, Envelope.salt@51, Envelope.iv@52, Envelope.ciphertext@53, Envelope.validate_encoding@56, Envelope.validate_encoding.self@56, Save@64, Save.model_config@67, Save.envelope@68, Save.revision@69, PrivateBoundary@72, PrivateBoundary.__init__@75, PrivateBoundary.__init__.app@75, PrivateBoundary.__init__.origin@75, PrivateBoundary.__init__.self@75, PrivateBoundary.__call__@79, PrivateBoundary.__call__.receive@79, PrivateBoundary.__call__.scope@79, PrivateBoundary.__call__.self@79, PrivateBoundary.__call__.send@79, PrivateBoundary.__call__.protected@84, PrivateBoundary.__call__.protected.message@84, PrivateBoundary.__call__.reject@101, PrivateBoundary.__call__.reject.code@101, PrivateBoundary.__call__.reject.detail@101, PrivateBoundary.__call__.headers@105, PrivateBoundary.__call__.body@118, PrivateBoundary.__call__.message@120, PrivateBoundary.__call__.consumed@128, PrivateBoundary.__call__.replay@130, PrivateBoundary.__call__.replay.consumed@134, create_private_app@141, create_private_app.data@141, create_private_app.native_identity@141, create_private_app.origin@141, create_private_app.ui@141, create_private_app.address@145, create_private_app.accounts@159, create_private_app.app@160, create_private_app.secure@165, create_private_app.cookie@166, create_private_app.invalid@169, create_private_app.invalid.error@169, create_private_app.invalid.request@169, create_private_app.limit@175, create_private_app.limit.auth@175, create_private_app.limit.request@175, create_private_app.limit.username@175, create_private_app.limit.ip@177, create_private_app.identify@183, create_private_app.identify.request@183, create_private_app.identify.owner@186, create_private_app.signed_in@191, create_private_app.signed_in.owner@191, create_private_app.signed_in.recovery@191, create_private_app.signed_in.response@193, create_private_app.health@206, create_private_app.health.value@208, create_private_app.health.key@214, create_private_app.register@228, create_private_app.register.body@228, create_private_app.register.request@228, create_private_app.register.owner@232, create_private_app.register.recovery@232, create_private_app.login@240, create_private_app.login.body@240, create_private_app.login.request@240, create_private_app.login.owner@243, create_private_app.account@249, create_private_app.account.request@249, create_private_app.account.owner@251, create_private_app.logout@255, create_private_app.logout.request@255, create_private_app.logout.response@259, create_private_app.reset@264, create_private_app.reset.body@264, create_private_app.reset.request@264, create_private_app.reset.fresh@267, create_private_app.delete@273, create_private_app.delete.body@273, create_private_app.delete.request@273, create_private_app.delete.owner@275, create_private_app.delete.response@279, create_private_app.workspace@284, create_private_app.workspace.request@284, create_private_app.save@289, create_private_app.save.body@289, create_private_app.save.request@289, create_private_app.save.owner@291
import mimetypes
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app import VERSION
from app.accounts import SESSION_SECONDS, Accounts, decode_field

CSP = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; worker-src 'self' blob:; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"


class Credentials(BaseModel):
    """Closed login contract; identifiers are aliases, not emails or real names."""

    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=40, pattern=r"^[a-z0-9][a-z0-9_-]+$")
    password: str = Field(min_length=15, max_length=128)


class Reset(Credentials):
    """A random once-shown recovery secret authorizes password rotation."""

    recovery: str = Field(min_length=40, max_length=64)


class Confirmation(BaseModel):
    """Account deletion requires password reauthentication, not just a stolen session."""

    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=15, max_length=128)


class Envelope(BaseModel):
    """Versioned AES-GCM payload; no plaintext labels, filenames or vault passwords."""

    model_config = ConfigDict(extra="forbid")
    version: int = Field(ge=1, le=1)
    salt: str = Field(max_length=24)
    iv: str = Field(max_length=16)
    ciphertext: str = Field(max_length=11_200_000)

    @model_validator(mode="after")
    def validate_encoding(self):
        """Fix salt/nonce lengths and limit ciphertext to eight MiB plus GCM tag."""
        decode_field(self.salt, 16, 16)
        decode_field(self.iv, 12, 12)
        decode_field(self.ciphertext, 16, 8 * 1024**2 + 16)
        return self


class Save(BaseModel):
    """Require an observed revision to avoid conflicting device overwrites."""

    model_config = ConfigDict(extra="forbid")
    envelope: Envelope
    revision: int = Field(ge=0, le=2**31 - 1)


class PrivateBoundary:
    """Validate Host, Origin, fetch metadata, JSON/body limits and security headers."""

    def __init__(self, app, origin: str):
        """One explicitly configured origin; no permissive CORS or forwarded-header trust."""
        self.app, self.origin = app, origin

    async def __call__(self, scope, receive, send):
        """Apply response protection to successes AND rejected/error paths."""
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def protected(message):
            """Deny framing/third-party scripts, avoid cache/referrer leakage, disable sensors."""
            if message["type"] == "http.response.start":
                message["headers"] += [
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"x-frame-options", b"DENY"),
                    (b"content-security-policy", CSP.encode()),
                    (b"permissions-policy", b"camera=(), microphone=(), geolocation=(), payment=()"),
                    (b"cross-origin-opener-policy", b"same-origin"),
                    (b"cross-origin-resource-policy", b"same-origin"),
                ]
                if self.origin.startswith("https://"):
                    message["headers"].append((b"strict-transport-security", b"max-age=31536000"))
            await send(message)

        async def reject(code, detail):
            """Emit a controlled error without input, credentials or traceback."""
            await JSONResponse({"detail": detail}, status_code=code)(scope, receive, protected)

        headers = dict(scope["headers"])
        if headers.get(b"host", b"").decode(errors="replace") != urlsplit(self.origin).netloc:
            return await reject(403, "Untrusted host")
        if headers.get(b"sec-fetch-site") == b"cross-site":
            return await reject(403, "Cross-site requests are not allowed")
        if scope["method"] not in {"GET", "HEAD"}:
            if (
                headers.get(b"origin", b"").decode(errors="replace") != self.origin
                or headers.get(b"x-aes-request") != b"v1"
            ):
                return await reject(403, "Same-origin request required")
            if headers.get(b"content-type", b"").split(b";", 1)[0] != b"application/json":
                return await reject(415, "JSON required")
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 11_300_000:
                return await reject(413, "Request too large")
            if not message.get("more_body", False):
                break
        consumed = False

        async def replay():
            """Replay one bounded body to framework parsers."""
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, protected)


def create_private_app(data: Path, origin: str, ui: Path, *, native_identity: dict | None = None) -> FastAPI:
    """Create account service; fail closed unless origin is HTTPS or literal loopback."""
    mimetypes.add_type("application/javascript", ".mjs")
    mimetypes.add_type("application/manifest+json", ".webmanifest")
    address = urlsplit(origin)
    if (
        address.path
        or address.query
        or address.fragment
        or address.username
        or address.password
        or not address.hostname
    ):
        raise ValueError("Origin must be a bare HTTPS origin or loopback HTTP origin")
    if address.scheme != "https" and not (
        address.scheme == "http" and address.hostname in {"127.0.0.1", "localhost"}
    ):
        raise ValueError("Public accounts require HTTPS")
    accounts = Accounts(data / "private-accounts.db")
    app = FastAPI(
        title="Applicant Evidence Studio by Jason Stys", docs_url=None, redoc_url=None, openapi_url=None
    )
    app.state.accounts = accounts
    app.add_middleware(PrivateBoundary, origin=origin)
    secure = address.scheme == "https"
    cookie = "__Host-aes-session" if secure else "aes-local-session"

    @app.exception_handler(RequestValidationError)
    async def invalid(request: Request, error: RequestValidationError):
        """Never include Pydantic input values (which could be passwords) in responses."""
        return JSONResponse(
            {"detail": "Input validation failed; check field lengths and format."}, status_code=422
        )

    def limit(request: Request, username: str = "", auth: bool = False):
        """Bound work before expensive password hashing; proxy ingress needs additional limits."""
        ip = request.client.host if request.client else "unknown"
        if not accounts.throttle("auth-ip:" + ip if auth else "ip:" + ip, 30 if auth else 300):
            raise HTTPException(429, "Too many requests; wait five minutes.")
        if auth and username and not accounts.throttle("auth-user:" + username, 10):
            raise HTTPException(429, "Too many requests; wait five minutes.")

    def identify(request: Request):
        """Resolve ownership solely from an unexpired server-verified cookie."""
        limit(request)
        owner = accounts.owner(request.cookies.get(cookie, ""))
        if not owner:
            raise HTTPException(401, "Sign in again; your session expired or was revoked.")
        return owner

    def signed_in(owner: str, recovery: str | None = None):
        """Return only safe account state; session secret is HttpOnly, not JavaScript-readable."""
        response = JSONResponse({"signed_in": True, **({"recovery": recovery} if recovery else {})})
        response.set_cookie(
            cookie,
            accounts.session(owner),
            max_age=SESSION_SECONDS,
            httponly=True,
            secure=secure,
            samesite="strict",
            path="/",
        )
        return response

    @app.get("/health")
    def health():
        """Public non-sensitive readiness/mode metadata."""
        value = {"ready": True, "version": VERSION, "mode": "private-accounts", "author": "Jason Stys"}
        if native_identity is not None:
            # Only verified public package identity is exposed. Never reflect
            # arbitrary manifest extras, environment values or account paths.
            value["native"] = {
                key: native_identity[key]
                for key in (
                    "product",
                    "version",
                    "source",
                    "source_dirty",
                    "python",
                    "tcl_version",
                    "tk_version",
                )
            }
            value["native"]["runtime_library_sha256"] = native_identity["runtime_library"]["sha256"]
        return value

    @app.post("/vault/register")
    def register(body: Credentials, request: Request):
        """Register an alias without collecting email, real name or identity traits."""
        limit(request, body.username, True)
        try:
            owner, recovery = accounts.register(body.username, body.password)
        except (sqlite3.IntegrityError, ValueError) as error:
            raise HTTPException(
                409, "Registration unavailable; choose another alias or try later."
            ) from error
        return signed_in(owner, recovery)

    @app.post("/vault/login")
    def login(body: Credentials, request: Request):
        """Password authentication with generic failed-login response."""
        limit(request, body.username, True)
        owner = accounts.login(body.username, body.password)
        if not owner:
            raise HTTPException(401, "Sign-in details not accepted.")
        return signed_in(owner)

    @app.get("/vault/account")
    def account(request: Request):
        """Return the signed-in user's alias, never an administrative user directory."""
        owner = identify(request)
        return {"username": owner["username"]}

    @app.post("/vault/logout")
    def logout(request: Request):
        """Revoke the presented cookie even if it has already expired."""
        limit(request)
        accounts.revoke(request.cookies.get(cookie, ""))
        response = JSONResponse({"signed_in": False})
        response.delete_cookie(cookie, path="/", secure=secure, httponly=True, samesite="strict")
        return response

    @app.post("/vault/reset")
    def reset(body: Reset, request: Request):
        """Recover login only using a random recovery code; revoke all existing sessions."""
        limit(request, body.username, True)
        fresh = accounts.reset(body.username, body.recovery, body.password)
        if not fresh:
            raise HTTPException(401, "Recovery details not accepted.")
        return {"recovery": fresh, "notice": "Login reset. Your independent vault key has not changed."}

    @app.delete("/vault/account")
    def delete(body: Confirmation, request: Request):
        """Password-confirmed account deletion; managed host backups require separate retention."""
        owner = identify(request)
        limit(request, owner["username"], True)
        if not accounts.delete(owner["id"], body.password):
            raise HTTPException(401, "Password not accepted.")
        response = JSONResponse({"deleted": True})
        response.delete_cookie(cookie, path="/", secure=secure, httponly=True, samesite="strict")
        return response

    @app.get("/vault/workspace")
    def workspace(request: Request):
        """No owner parameter: every read is scoped to the authenticated session."""
        return accounts.vault(identify(request)["id"])

    @app.put("/vault/workspace")
    def save(body: Save, request: Request):
        """Accept only versioned ciphertext and an optimistic revision, never raw resumes."""
        owner = identify(request)
        if not accounts.save(owner["id"], body.envelope.model_dump(), body.revision):
            raise HTTPException(
                409,
                "Another device changed this workspace. Export your backup, lock and reopen before editing.",
            )
        return {"revision": body.revision + 1}

    if ui.is_dir():
        app.mount("/", StaticFiles(directory=ui, html=True), name="ui")
    return app
