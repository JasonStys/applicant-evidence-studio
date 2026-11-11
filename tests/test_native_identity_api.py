"""Jason Stys: public packaged identity never reflects account paths, secrets or arbitrary metadata."""

# Index: TestClient@5, VERSION@7, create_private_app@8, test_public_native_health_is_closed_to_verified_package_fields@11, test_public_native_health_is_closed_to_verified_package_fields.tmp_path@11, test_public_native_health_is_closed_to_verified_package_fields.ui@13, test_public_native_health_is_closed_to_verified_package_fields.metadata@16, test_public_native_health_is_closed_to_verified_package_fields.client@31, test_public_native_health_is_closed_to_verified_package_fields.response@32, test_public_native_health_is_closed_to_verified_package_fields.value@33, test_public_native_health_is_closed_to_verified_package_fields.key@37

from fastapi.testclient import TestClient

from app import VERSION
from app.private_api import create_private_app


def test_public_native_health_is_closed_to_verified_package_fields(tmp_path):
    """Actual HTTP health carries only the explicitly public source/runtime fields; extras never leak."""
    ui = tmp_path / "ui"
    ui.mkdir()
    (ui / "index.html").write_text("<html>synthetic</html>")
    metadata = {
        "product": "applicant-evidence-studio",
        "version": VERSION,
        "source": "a" * 40,
        "source_dirty": False,
        "python": "3.14.10",
        "tcl_version": "9.0.4",
        "tk_version": "9.0.4",
        "runtime_library": {"sha256": "b" * 64},
        "unexpected_private_value": "never-reflect-this",
        "profile_path": str(tmp_path / "accounts"),
    }
    with TestClient(
        create_private_app(tmp_path / "accounts", "http://127.0.0.1:8014", ui, native_identity=metadata),
        base_url="http://127.0.0.1:8014",
    ) as client:
        response = client.get("/health")
        value = response.json()
        assert response.status_code == 200
        assert value["native"] == {
            key: metadata[key]
            for key in ("product", "version", "source", "source_dirty", "python", "tcl_version", "tk_version")
        } | {"runtime_library_sha256": "b" * 64}
        assert "never-reflect-this" not in response.text and str(tmp_path) not in response.text
