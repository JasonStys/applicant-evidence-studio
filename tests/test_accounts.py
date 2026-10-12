"""Jason Stys: real-auth, ciphertext isolation, CSRF, recovery, deletion and concurrency tests."""

# Index: base64@4, sqlite3@5, ThreadPoolExecutor@6, pytest@8, TestClient@9, decode_field@11, password_hash@11, password_matches@11, create_private_app@12, ORIGIN@14, HEADERS@15, PASSWORD@16, ENVELOPE@17, service@26, service.tmp_path@26, service.app@28, service.client@29, register@33, register.client@33, register.username@33, register.response@35, test_auth_cookie_and_no_plaintext_endpoints@42, test_auth_cookie_and_no_plaintext_endpoints.service@42, test_auth_cookie_and_no_plaintext_endpoints.client@44, test_auth_cookie_and_no_plaintext_endpoints.store@44, test_auth_cookie_and_no_plaintext_endpoints.code@46, test_auth_cookie_and_no_plaintext_endpoints.cookie@47, test_auth_cookie_and_no_plaintext_endpoints.response@49, test_auth_cookie_and_no_plaintext_endpoints.header@52, test_auth_cookie_and_no_plaintext_endpoints.db@57, test_auth_cookie_and_no_plaintext_endpoints.row@58, test_auth_cookie_and_no_plaintext_endpoints.result@65, test_isolation_cas_and_persistence@75, test_isolation_cas_and_persistence.service@75, test_isolation_cas_and_persistence.tmp_path@75, test_isolation_cas_and_persistence.first@77, test_isolation_cas_and_persistence.store@77, test_isolation_cas_and_persistence.second@87, test_isolation_cas_and_persistence.restarted@101, test_isolation_cas_and_persistence.db@104, test_isolation_cas_and_persistence.owner@105, test_isolation_cas_and_persistence.pool@106, test_isolation_cas_and_persistence._@107, test_isolation_cas_and_persistence.results@107, test_csrf_headers_hosts_body_and_private_errors@111, test_csrf_headers_hosts_body_and_private_errors.service@111, test_csrf_headers_hosts_body_and_private_errors._@113, test_csrf_headers_hosts_body_and_private_errors.client@113, test_csrf_headers_hosts_body_and_private_errors.credentials@114, test_csrf_headers_hosts_body_and_private_errors.headers@115, test_csrf_headers_hosts_body_and_private_errors.result@121, test_csrf_headers_hosts_body_and_private_errors.result@128, test_csrf_headers_hosts_body_and_private_errors.result@130, test_csrf_headers_hosts_body_and_private_errors.result@134, test_csrf_headers_hosts_body_and_private_errors.header@135, test_envelope_validation_and_no_input_leak@146, test_envelope_validation_and_no_input_leak.service@146, test_envelope_validation_and_no_input_leak._@148, test_envelope_validation_and_no_input_leak.client@148, test_envelope_validation_and_no_input_leak.envelope@150, test_envelope_validation_and_no_input_leak.result@157, test_recovery_revocation_expiry_and_deletion@164, test_recovery_revocation_expiry_and_deletion.service@164, test_recovery_revocation_expiry_and_deletion.client@166, test_recovery_revocation_expiry_and_deletion.store@166, test_recovery_revocation_expiry_and_deletion.code@167, test_recovery_revocation_expiry_and_deletion.token@168, test_recovery_revocation_expiry_and_deletion.new_password@170, test_recovery_revocation_expiry_and_deletion.bad@171, test_recovery_revocation_expiry_and_deletion.result@177, test_recovery_revocation_expiry_and_deletion.owner@186, test_recovery_revocation_expiry_and_deletion.expired@188, test_recovery_revocation_expiry_and_deletion.db@189, test_recovery_revocation_expiry_and_deletion.db@203, test_hash_rate_limits_and_configuration@209, test_hash_rate_limits_and_configuration.service@209, test_hash_rate_limits_and_configuration.tmp_path@209, test_hash_rate_limits_and_configuration.client@211, test_hash_rate_limits_and_configuration.store@211, test_hash_rate_limits_and_configuration.hashed@212, test_hash_rate_limits_and_configuration._@217, test_hash_rate_limits_and_configuration.db@218, test_hash_rate_limits_and_configuration.origin@221, test_hash_rate_limits_and_configuration.local@233, test_hash_rate_limits_and_configuration.response@234, test_hash_rate_limits_and_configuration._@240, test_hash_rate_limits_and_configuration.result@241, test_session_bound_and_capacity_guard@247, test_session_bound_and_capacity_guard.service@247, test_session_bound_and_capacity_guard.client@249, test_session_bound_and_capacity_guard.store@249, test_session_bound_and_capacity_guard.owner@251, test_session_bound_and_capacity_guard._@252, test_session_bound_and_capacity_guard.db@254, test_session_bound_and_capacity_guard.i@258, test_session_bound_and_capacity_guard.db@263
import base64
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.accounts import decode_field, password_hash, password_matches
from app.private_api import create_private_app

ORIGIN = "https://studio.example"
HEADERS = {"Origin": ORIGIN, "X-AES-Request": "v1"}
PASSWORD = "synthetic-login-password-only"
ENVELOPE = {
    "version": 1,
    "salt": base64.b64encode(b"s" * 16).decode(),
    "iv": base64.b64encode(b"i" * 12).decode(),
    "ciphertext": base64.b64encode(b"x" * 100).decode(),
}


@pytest.fixture
def service(tmp_path):
    """Each test gets disposable accounts; synthetic credentials never authenticate elsewhere."""
    app = create_private_app(tmp_path, ORIGIN, tmp_path / "no-ui")
    with TestClient(app, base_url=ORIGIN) as client:
        yield client, app.state.accounts


def register(client, username="synthetic_user"):
    """Register a controlled synthetic alias and return its once-shown login recovery code."""
    response = client.post(
        "/vault/register", headers=HEADERS, json={"username": username, "password": PASSWORD}
    )
    assert response.status_code == 200, response.text
    return response.json()["recovery"]


def test_auth_cookie_and_no_plaintext_endpoints(service):
    """Secure cookie flags, generic errors, no plaintext review routes and no raw credentials."""
    client, store = service
    assert client.get("/vault/workspace").status_code == 401
    code = register(client)
    cookie = client.cookies.get("__Host-aes-session")
    assert len(cookie) >= 40 and len(code) >= 40
    response = client.post(
        "/vault/login", headers=HEADERS, json={"username": "synthetic_user", "password": PASSWORD}
    )
    header = response.headers["set-cookie"]
    assert "HttpOnly" in header and "Secure" in header and "SameSite=strict" in header and "Path=/" in header
    assert "Domain=" not in header
    assert client.get("/api/jobs").status_code == 404
    assert client.get("/vault/account").json() == {"username": "synthetic_user"}
    with store.connection() as db:
        row = db.execute("SELECT * FROM accounts").fetchone()
        assert (
            row["password"].startswith("scrypt-v1$")
            and PASSWORD not in row["password"]
            and code not in row["recovery"]
        )
        assert db.execute("SELECT token FROM sessions").fetchone()[0] != cookie
    result = client.post(
        "/vault/register", headers=HEADERS, json={"username": "synthetic_user", "password": PASSWORD}
    )
    assert result.status_code == 409
    client.post("/vault/logout", headers=HEADERS, json={})
    assert client.get("/vault/account").status_code == 401
    client.cookies.set("__Host-aes-session", cookie, domain="studio.example", path="/")
    # This is the older session, not the rotated login session: verify expiry/revocation separately below.


def test_isolation_cas_and_persistence(service, tmp_path):
    """Two users cannot read/replace each other's ciphertext; revisions survive a restart."""
    first, store = service
    register(first, "first_user")
    assert (
        first.put("/vault/workspace", headers=HEADERS, json={"envelope": ENVELOPE, "revision": 0}).status_code
        == 200
    )
    assert (
        first.put("/vault/workspace", headers=HEADERS, json={"envelope": ENVELOPE, "revision": 0}).status_code
        == 409
    )
    with TestClient(first.app, base_url=ORIGIN) as second:
        register(second, "second_user")
        assert second.get("/vault/workspace").json() == {"envelope": None, "revision": 0}
        assert second.get("/vault/workspace?owner=first_user").json()["envelope"] is None
        assert (
            second.put(
                "/vault/workspace",
                headers=HEADERS,
                json={"owner": "first_user", "envelope": ENVELOPE, "revision": 1},
            ).status_code
            == 422
        )
        second.put("/vault/workspace", headers=HEADERS, json={"envelope": ENVELOPE, "revision": 0})
    assert first.get("/vault/workspace").json()["revision"] == 1
    with TestClient(create_private_app(tmp_path, ORIGIN, tmp_path / "absent"), base_url=ORIGIN) as restarted:
        restarted.cookies.update(first.cookies)
        assert restarted.get("/vault/workspace").json()["envelope"] == ENVELOPE
    with store.connection() as db:
        owner = db.execute("SELECT id FROM accounts WHERE username='first_user'").fetchone()[0]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: store.save(owner, ENVELOPE, 1), range(2)))
    assert sorted(results) == [False, True]


def test_csrf_headers_hosts_body_and_private_errors(service):
    """Reject cross-origin/simple forms, rebinding and unexpected/oversized secret-bearing input."""
    client, _ = service
    credentials = {"username": "synthetic_user", "password": PASSWORD}
    for headers in [
        {},
        {**HEADERS, "Origin": "https://evil.example"},
        {"Origin": ORIGIN},
        {**HEADERS, "Sec-Fetch-Site": "cross-site"},
    ]:
        result = client.post("/vault/login", headers=headers, json=credentials)
        assert (
            result.status_code == 403
            and "frame-ancestors 'none'" in result.headers["content-security-policy"]
        )
    assert client.get("/health", headers={"Host": "evil.example"}).status_code == 403
    assert client.post("/vault/login", headers=HEADERS, data=credentials).status_code == 415
    result = client.post("/vault/login", headers=HEADERS, json={**credentials, "private": "SECRET_RESUME"})
    assert result.status_code == 422 and PASSWORD not in result.text and "SECRET_RESUME" not in result.text
    result = client.post(
        "/vault/login", headers={**HEADERS, "Content-Type": "application/json"}, content=b"x" * 11_300_001
    )
    assert result.status_code == 413
    result = client.get("/health")
    for header in [
        "content-security-policy",
        "x-frame-options",
        "permissions-policy",
        "referrer-policy",
        "cache-control",
        "strict-transport-security",
    ]:
        assert header in result.headers


def test_envelope_validation_and_no_input_leak(service):
    """Only encrypted envelope fields/versions/lengths are accepted, not filenames or documents."""
    client, _ = service
    register(client)
    for envelope in [
        {**ENVELOPE, "version": 2},
        {**ENVELOPE, "iv": "!"},
        {**ENVELOPE, "salt": "eA=="},
        {**ENVELOPE, "plaintext": "SECRET_RESUME"},
        {**ENVELOPE, "ciphertext": "eA=="},
    ]:
        result = client.put("/vault/workspace", headers=HEADERS, json={"envelope": envelope, "revision": 0})
        assert result.status_code == 422 and "SECRET_RESUME" not in result.text
    assert client.get("/vault/workspace").json()["revision"] == 0
    with pytest.raises(ValueError):
        decode_field("!!!", 16, 16)


def test_recovery_revocation_expiry_and_deletion(service):
    """Random recovery code rotates once, revokes all sessions and never resets the vault key."""
    client, store = service
    code = register(client)
    token = client.cookies.get("__Host-aes-session")
    client.put("/vault/workspace", headers=HEADERS, json={"envelope": ENVELOPE, "revision": 0})
    new_password = "different-synthetic-password"
    bad = client.post(
        "/vault/reset",
        headers=HEADERS,
        json={"username": "synthetic_user", "password": new_password, "recovery": "x" * 43},
    )
    assert bad.status_code == 401
    result = client.post(
        "/vault/reset",
        headers=HEADERS,
        json={"username": "synthetic_user", "password": new_password, "recovery": code},
    )
    assert result.status_code == 200 and result.json()["recovery"] != code
    assert store.owner(token) is None
    assert store.reset("synthetic_user", code, PASSWORD) is None
    assert store.login("synthetic_user", PASSWORD) is None
    owner = store.login("synthetic_user", new_password)
    assert store.vault(owner)["envelope"] == ENVELOPE
    expired = store.session(owner)
    with store.connection() as db:
        db.execute("UPDATE sessions SET touched=0")
    assert store.owner(expired) is None
    client.cookies.set("__Host-aes-session", store.session(owner), domain="studio.example", path="/")
    assert (
        client.request("DELETE", "/vault/account", headers=HEADERS, json={"password": PASSWORD}).status_code
        == 401
    )
    assert (
        client.request(
            "DELETE", "/vault/account", headers=HEADERS, json={"password": new_password}
        ).status_code
        == 200
    )
    with store.connection() as db:
        assert db.execute("SELECT count(*) FROM accounts").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM sessions").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM vaults").fetchone()[0] == 0


def test_hash_rate_limits_and_configuration(service, tmp_path):
    """Real scrypt comparison, persistent throttling, fail-closed HTTPS and loopback exception."""
    client, store = service
    hashed = password_hash(PASSWORD)
    assert password_matches(PASSWORD, hashed) and not password_matches("wrong", hashed)
    assert not password_matches(PASSWORD, "broken") and not password_matches(
        PASSWORD, hashed.replace("scrypt-v1", "unknown")
    )
    assert [store.throttle("synthetic", 2) for _ in range(3)] == [True, True, False]
    with store.connection() as db:
        db.execute("UPDATE limits SET started=0")
    assert store.throttle("synthetic", 2)
    for origin in [
        "http://public.example",
        "https://studio.example/path",
        "https://user:secret@studio.example",
        "ftp://studio.example",
        "https://studio.example?secret=bad",
    ]:
        with pytest.raises(ValueError):
            create_private_app(tmp_path, origin, tmp_path)
    with TestClient(
        create_private_app(tmp_path / "local", "http://127.0.0.1:8025", tmp_path / "missing"),
        base_url="http://127.0.0.1:8025",
    ) as local:
        response = local.post(
            "/vault/register",
            headers={"Origin": "http://127.0.0.1:8025", "X-AES-Request": "v1"},
            json={"username": "local_user", "password": PASSWORD},
        )
        assert response.status_code == 200 and "Secure;" not in response.headers["set-cookie"]
    for _ in range(11):
        result = client.post(
            "/vault/login", headers=HEADERS, json={"username": "absent_user", "password": PASSWORD}
        )
    assert result.status_code == 429


def test_session_bound_and_capacity_guard(service):
    """Keep a bounded session list and enforce explicit registration capacity."""
    client, store = service
    register(client)
    owner = store.login("synthetic_user", PASSWORD)
    for _ in range(12):
        store.session(owner)
    with store.connection() as db:
        assert db.execute("SELECT count(*) FROM sessions").fetchone()[0] == 10
        db.executemany(
            "INSERT INTO accounts VALUES(?,?,?,?,?)",
            [(f"fake{i}", f"alias{i}", "fakehash", "fakerecovery", 0) for i in range(9999)],
        )
    with pytest.raises(ValueError, match="capacity"):
        store.register("over_capacity", PASSWORD)
    with pytest.raises(sqlite3.IntegrityError):
        with store.connection() as db:
            db.execute(
                "INSERT INTO accounts VALUES(?,?,?,?,?)",
                ("duplicate", "synthetic_user", "fakehash", "fakerecovery", 0),
            )
