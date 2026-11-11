"""Jason Stys: actual Tk owner-window controls with real owned loopback requests.

Linux validation runs these mandatory tests under Xvfb. Windows/macOS use their
native runner display. No account directory or browser belonging to a user is
opened. All app windows and listeners are owned by this test.
"""

# Index: annotations@10, asyncio@12, io@13, threading@14, time@15, tk@16, Path@17, httpx@19, pytest@20, FastAPI@21, LocalService@23, OwnerWindow@23, DesktopOwnership@24, pump@27, pump.predicate@27, pump.root@27, pump.seconds@27, pump.until@29, test_real_owner_help_and_all_normal_close_controls@38, test_real_owner_help_and_all_normal_close_controls.close_control@38, test_real_owner_help_and_all_normal_close_controls.monkeypatch@38, test_real_owner_help_and_all_normal_close_controls.tmp_path@38, test_real_owner_help_and_all_normal_close_controls._args@40, test_real_owner_help_and_all_normal_close_controls.service@40, test_real_owner_help_and_all_normal_close_controls.root@41, test_real_owner_help_and_all_normal_close_controls.window@42, test_real_owner_help_and_all_normal_close_controls._url@49, test_real_owner_help_and_all_normal_close_controls.first_help@54, test_real_owner_help_and_all_normal_close_controls.texts@58, test_real_owner_help_and_all_normal_close_controls.frame@60, test_real_owner_help_and_all_normal_close_controls.child@61, test_real_owner_help_and_all_normal_close_controls.nonce@73, test_actual_quit_retains_window_and_profile_until_request_commits@89, test_actual_quit_retains_window_and_profile_until_request_commits.tmp_path@89, test_actual_quit_retains_window_and_profile_until_request_commits._@91, test_actual_quit_retains_window_and_profile_until_request_commits.entered@91, test_actual_quit_retains_window_and_profile_until_request_commits.release@91, test_actual_quit_retains_window_and_profile_until_request_commits.returned@91, test_actual_quit_retains_window_and_profile_until_request_commits.results@92, test_actual_quit_retains_window_and_profile_until_request_commits.factory@94, test_actual_quit_retains_window_and_profile_until_request_commits.factory._args@94, test_actual_quit_retains_window_and_profile_until_request_commits.factory.app@95, test_actual_quit_retains_window_and_profile_until_request_commits.factory.pending@98, test_actual_quit_retains_window_and_profile_until_request_commits.owner@107, test_actual_quit_retains_window_and_profile_until_request_commits.service@108, test_actual_quit_retains_window_and_profile_until_request_commits.root@109, test_actual_quit_retains_window_and_profile_until_request_commits.window@110, test_actual_quit_retains_window_and_profile_until_request_commits.request@113, test_actual_quit_retains_window_and_profile_until_request_commits.request.client@114, test_actual_quit_retains_window_and_profile_until_request_commits.request.result@115, test_actual_quit_retains_window_and_profile_until_request_commits.worker@119, test_invalid_acceptance_nonce_does_not_close_real_window@150, test_invalid_acceptance_nonce_does_not_close_real_window.tmp_path@150, test_invalid_acceptance_nonce_does_not_close_real_window._args@152, test_invalid_acceptance_nonce_does_not_close_real_window.service@152, test_invalid_acceptance_nonce_does_not_close_real_window.root@153, test_invalid_acceptance_nonce_does_not_close_real_window.window@154

from __future__ import annotations

import asyncio
import io
import threading
import time
import tkinter as tk
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from app.native_host import LocalService, OwnerWindow
from app.native_profile import DesktopOwnership


def pump(root: tk.Tk, predicate, seconds=8):
    """Dispatch real Tk events until observed completion; a timeout fails rather than skips."""
    until = time.monotonic() + seconds
    while not predicate():
        if time.monotonic() > until:
            raise AssertionError("Native control did not reach its observed state")
        root.update()
        time.sleep(0.01)


@pytest.mark.parametrize("close_control", ["button", "window", "stdin"])
def test_real_owner_help_and_all_normal_close_controls(tmp_path: Path, monkeypatch, close_control):
    """Real Open/Help controls and each close affordance retain the same service lifecycle."""
    service = LocalService(lambda *_args: FastAPI(), tmp_path, tmp_path)
    root = tk.Tk()
    window = OwnerWindow(root, service, open_browser=False)
    service.thread.start()
    try:
        pump(root, lambda: window.ready)
        assert "Jason Stys" in root.title()
        assert not window.open_button.instate(["disabled"])
        # An unavailable browser leaves the actual local address usable.
        monkeypatch.setattr("app.native_host.webbrowser.open", lambda _url: False)
        window.open_button.invoke()
        assert service.origin in window.status.get()
        window.help()
        root.update()
        first_help = window.help_window
        assert first_help is not None and first_help.winfo_ismapped()
        window.help()
        assert window.help_window is first_help
        texts = [
            child
            for frame in first_help.winfo_children()
            for child in frame.winfo_children()
            if isinstance(child, tk.Text)
        ]
        assert len(texts) == 1
        assert "Rankings are advisory" in texts[0].get("1.0", "end")
        assert "Quit application waits for active requests" in texts[0].get("1.0", "end")
        first_help.destroy()
        if close_control == "button":
            window.quit_button.invoke()
        elif close_control == "window":
            root.tk.call(root.protocol("WM_DELETE_WINDOW"))
        else:
            nonce = "a" * 64
            monkeypatch.setattr("app.native_host.sys.stdin", io.StringIO(f"quit {nonce}\n"))
            window.acceptance_input(nonce)
        pump(root, lambda: service.done.is_set())
        root.update()
        assert window.closing
        assert not service.failed
        assert service.done.is_set()
    finally:
        service.close()
        try:
            root.destroy()
        except tk.TclError:
            pass


def test_actual_quit_retains_window_and_profile_until_request_commits(tmp_path: Path):
    """A real pending HTTP handler blocks Quit completion, then commits before the window/profile close."""
    entered, release, returned = (threading.Event() for _ in range(3))
    results = []

    def factory(*_args):
        app = FastAPI()

        @app.get("/pending")
        async def pending():
            entered.set()
            while not release.is_set():
                await asyncio.sleep(0.01)
            (tmp_path / "request-commit.txt").write_text("retained")
            return {"saved": True}

        return app

    with DesktopOwnership(tmp_path / "profile") as owner:
        service = LocalService(factory, owner.directory, tmp_path)
        root = tk.Tk()
        window = OwnerWindow(root, service, open_browser=False)
        service.thread.start()

        def request():
            with httpx.Client(trust_env=False, timeout=10) as client:
                result = client.get(service.origin + "/pending")
                results.append((result.status_code, result.json()))
            returned.set()

        worker = threading.Thread(target=request)
        try:
            pump(root, lambda: window.ready)
            worker.start()
            pump(root, entered.is_set)
            window.quit_button.invoke()
            root.update()
            assert window.closing and root.winfo_exists()
            assert window.open_button.instate(["disabled"])
            assert window.quit_button.instate(["disabled"])
            assert owner.descriptor >= 0 and not service.done.is_set()
            assert not (tmp_path / "request-commit.txt").exists()
            release.set()
            pump(root, lambda: service.done.is_set() and returned.is_set())
            root.update()
            service.close()
            assert results == [(200, {"saved": True})]
            assert (tmp_path / "request-commit.txt").read_text() == "retained"
        finally:
            release.set()
            service.close()
            if worker.ident is not None:
                worker.join(5)
            try:
                root.destroy()
            except tk.TclError:
                pass
    with DesktopOwnership(tmp_path / "profile"):
        assert (tmp_path / "request-commit.txt").read_text() == "retained"


def test_invalid_acceptance_nonce_does_not_close_real_window(tmp_path: Path):
    """An invalid opt-in channel fails without starting or closing an unrelated service."""
    service = LocalService(lambda *_args: FastAPI(), tmp_path, tmp_path)
    root = tk.Tk()
    window = OwnerWindow(root, service, open_browser=False)
    try:
        with pytest.raises(ValueError, match="acceptance channel"):
            window.acceptance_input("wrong")
        assert root.winfo_exists() and not window.closing
    finally:
        service.close()
        root.destroy()
