"""Jason Stys: actual main-window/service lifetime and preserved synthetic account identity."""

# Index: annotations@5, sqlite3@7, threading@8, time@9, closing@10, Path@11, httpx@13, VERSION@15, native_desktop@15, OwnerWindow@16, isolated_ui_bundle@19, isolated_ui_bundle.monkeypatch@19, isolated_ui_bundle.tmp_path@19, isolated_ui_bundle.bundle@21, test_legacy_per_user_paths_are_selected_without_creating_data@29, test_legacy_per_user_paths_are_selected_without_creating_data.monkeypatch@29, test_legacy_per_user_paths_are_selected_without_creating_data.tmp_path@29, test_legacy_per_user_paths_are_selected_without_creating_data.chosen@31, test_legacy_per_user_paths_are_selected_without_creating_data._class@35, test_legacy_per_user_paths_are_selected_without_creating_data.expected@38, test_legacy_per_user_paths_are_selected_without_creating_data.system@38, test_real_main_register_reopen_login_and_normal_owned_exit@47, test_real_main_register_reopen_login_and_normal_owned_exit.monkeypatch@47, test_real_main_register_reopen_login_and_normal_owned_exit.tmp_path@47, test_real_main_register_reopen_login_and_normal_owned_exit.profile@49, test_real_main_register_reopen_login_and_normal_owned_exit.errors@54, test_real_main_register_reopen_login_and_normal_owned_exit.observed@54, test_real_main_register_reopen_login_and_normal_owned_exit.threads@54, test_real_main_register_reopen_login_and_normal_owned_exit.current_action@55, test_real_main_register_reopen_login_and_normal_owned_exit.ObservedWindow@57, test_real_main_register_reopen_login_and_normal_owned_exit.ObservedWindow.__init__@60, test_real_main_register_reopen_login_and_normal_owned_exit.ObservedWindow.__init__.args@60, test_real_main_register_reopen_login_and_normal_owned_exit.ObservedWindow.__init__.kwargs@60, test_real_main_register_reopen_login_and_normal_owned_exit.ObservedWindow.__init__.self@60, test_real_main_register_reopen_login_and_normal_owned_exit.ObservedWindow.__init__.action@63, test_real_main_register_reopen_login_and_normal_owned_exit.ObservedWindow.__init__.use_actual_account_service@65, test_real_main_register_reopen_login_and_normal_owned_exit.ObservedWindow.__init__.use_actual_account_service.until@67, test_real_main_register_reopen_login_and_normal_owned_exit.ObservedWindow.__init__.use_actual_account_service.client@72, test_real_main_register_reopen_login_and_normal_owned_exit.ObservedWindow.__init__.use_actual_account_service.result@74, test_real_main_register_reopen_login_and_normal_owned_exit.ObservedWindow.__init__.worker@88, test_real_main_register_reopen_login_and_normal_owned_exit.thread@94, test_real_main_register_reopen_login_and_normal_owned_exit.database@98, test_real_main_register_reopen_login_and_normal_owned_exit.first@99, test_real_main_register_reopen_login_and_normal_owned_exit.current_action@101, test_real_main_register_reopen_login_and_normal_owned_exit.thread@103, test_real_main_register_reopen_login_and_normal_owned_exit.database@107, test_invalid_opt_in_fails_before_any_profile_is_created@111, test_invalid_opt_in_fails_before_any_profile_is_created.monkeypatch@111, test_invalid_opt_in_fails_before_any_profile_is_created.tmp_path@111, test_invalid_opt_in_fails_before_any_profile_is_created.pytest@113, test_startup_diagnostic_has_only_fixed_phase_and_exception_class@124, test_startup_diagnostic_has_only_fixed_phase_and_exception_class.capsys@124, test_startup_diagnostic_has_only_fixed_phase_and_exception_class.monkeypatch@124, test_startup_diagnostic_has_only_fixed_phase_and_exception_class.tmp_path@124, test_startup_diagnostic_has_only_fixed_phase_and_exception_class.profile@127, test_startup_diagnostic_has_only_fixed_phase_and_exception_class.refused@132, test_startup_diagnostic_has_only_fixed_phase_and_exception_class.refused._bundle@132

from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import closing
from pathlib import Path

import httpx

from app import VERSION, native_desktop
from app.native_host import OwnerWindow


def isolated_ui_bundle(tmp_path, monkeypatch):
    """Supply inert static fixture HTML for controller-only tests; full compiled UI has its own mandatory journey."""
    bundle = tmp_path / "ui-bundle"
    (bundle / "dist").mkdir(parents=True)
    (bundle / "dist/index.html").write_text(
        "<!doctype html><html><body>Jason Stys · controller fixture</body></html>"
    )
    monkeypatch.setattr(native_desktop.sys, "_MEIPASS", str(bundle), raising=False)


def test_legacy_per_user_paths_are_selected_without_creating_data(tmp_path, monkeypatch):
    """The upgrade retains all three legacy per-user directory names and explicit isolated overrides."""
    chosen = tmp_path / "selected"
    monkeypatch.setenv("AES_DESKTOP_DATA", str(chosen))
    assert native_desktop.private_directory() == chosen and not chosen.exists()
    monkeypatch.delenv("AES_DESKTOP_DATA")
    monkeypatch.setattr(Path, "home", classmethod(lambda _class: tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    for system, expected in [
        ("win32", tmp_path / "local/ApplicantEvidenceStudio"),
        ("darwin", tmp_path / "Library/Application Support/ApplicantEvidenceStudio"),
        ("linux", tmp_path / "xdg/ApplicantEvidenceStudio"),
    ]:
        monkeypatch.setattr(native_desktop.sys, "platform", system)
        assert native_desktop.private_directory() == expected and not expected.exists()


def test_real_main_register_reopen_login_and_normal_owned_exit(tmp_path, monkeypatch):
    """Run the actual entry twice, register then sign in over real HTTP, and retain the exact account row."""
    profile = tmp_path / "synthetic-accounts"
    isolated_ui_bundle(tmp_path, monkeypatch)
    monkeypatch.setenv("AES_DESKTOP_DATA", str(profile))
    monkeypatch.setenv("AES_NO_BROWSER", "1")
    monkeypatch.delenv("AES_ACCEPTANCE_NONCE", raising=False)
    threads, errors, observed = [], [], []
    current_action = "register"

    class ObservedWindow(OwnerWindow):
        """Observe the real window/service without replacing either implementation or its controls."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.root.after(10, self.show_notices)
            action = current_action

            def use_actual_account_service():
                try:
                    until = time.monotonic() + 8
                    while not self.service.server.started:
                        if self.service.done.is_set() or time.monotonic() >= until:
                            raise AssertionError("The actual owned service did not start")
                        time.sleep(0.01)
                    with httpx.Client(base_url=self.service.origin, trust_env=False, timeout=5) as client:
                        assert client.get("/health").json()["version"] == VERSION
                        result = client.post(
                            "/vault/" + action,
                            headers={"Origin": self.service.origin, "X-AES-Request": "v1"},
                            json={"username": "native_fixture", "password": "Synthetic-native-account-2026!"},
                        )
                        assert result.status_code == 200 and result.json()["signed_in"] is True
                        assert client.get("/vault/account").json() == {"username": "native_fixture"}
                        assert client.get("/vault/workspace").status_code == 200
                        observed.append(action)
                except BaseException as error:
                    errors.append(error)
                finally:
                    self.commands.put("quit")

            worker = threading.Thread(target=use_actual_account_service)
            threads.append(worker)
            worker.start()

    monkeypatch.setattr(native_desktop, "OwnerWindow", ObservedWindow)
    assert native_desktop.main() == 0
    for thread in threads:
        thread.join(5)
        assert not thread.is_alive()
    assert not errors and observed == ["register"]
    with closing(sqlite3.connect(profile / "private-accounts.db")) as database:
        first = database.execute("SELECT * FROM accounts ORDER BY username").fetchall()
    assert len(first) == 1 and "Synthetic-native-account-2026!" not in str(first)
    current_action = "login"
    assert native_desktop.main() == 0
    for thread in threads:
        thread.join(5)
        assert not thread.is_alive()
    assert not errors and observed == ["register", "login"]
    with closing(sqlite3.connect(profile / "private-accounts.db")) as database:
        assert database.execute("SELECT * FROM accounts ORDER BY username").fetchall() == first


def test_invalid_opt_in_fails_before_any_profile_is_created(tmp_path, monkeypatch):
    """Acceptance-only stdin control cannot be enabled accidentally on an ordinary launch."""
    import pytest

    isolated_ui_bundle(tmp_path, monkeypatch)

    monkeypatch.setenv("AES_ACCEPTANCE_NONCE", "a" * 64)
    monkeypatch.delenv("AES_DESKTOP_DATA", raising=False)
    monkeypatch.delenv("AES_NO_BROWSER", raising=False)
    with pytest.raises(SystemExit, match="Explicit acceptance"):
        native_desktop.main()


def test_startup_diagnostic_has_only_fixed_phase_and_exception_class(tmp_path, monkeypatch, capsys):
    """Package refusal is actionable without exposing the underlying private error message or data path."""
    isolated_ui_bundle(tmp_path, monkeypatch)
    profile = tmp_path / "private-profile-not-created"
    monkeypatch.setenv("AES_DESKTOP_DATA", str(profile))
    monkeypatch.setenv("AES_NO_BROWSER", "1")
    monkeypatch.delenv("AES_ACCEPTANCE_NONCE", raising=False)

    def refused(_bundle):
        raise ValueError("private diagnostic content must not be logged")

    monkeypatch.setattr(native_desktop, "verify_bundle", refused)
    assert native_desktop.main() == 2
    assert capsys.readouterr().err == "AES_STARTUP_REFUSED phase=bundle-integrity type=ValueError\n"
    assert not profile.exists()
