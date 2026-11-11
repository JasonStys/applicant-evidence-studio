"""Jason Stys: real service lifecycle checks with controlled in-flight HTTP work."""

# Index: annotations@5, asyncio@7, socket@8, threading@9, time@10, Path@11, httpx@13, pytest@14, FastAPI@15, LocalService@17, wait_for@20, wait_for.predicate@20, wait_for.seconds@20, wait_for.until@22, test_real_active_request_finishes_before_owned_service_close@29, test_real_active_request_finishes_before_owned_service_close.tmp_path@29, test_real_active_request_finishes_before_owned_service_close._@31, test_real_active_request_finishes_before_owned_service_close.closed@31, test_real_active_request_finishes_before_owned_service_close.entered@31, test_real_active_request_finishes_before_owned_service_close.release@31, test_real_active_request_finishes_before_owned_service_close.returned@31, test_real_active_request_finishes_before_owned_service_close.observations@32, test_real_active_request_finishes_before_owned_service_close.factory@34, test_real_active_request_finishes_before_owned_service_close.factory._directory@34, test_real_active_request_finishes_before_owned_service_close.factory._origin@34, test_real_active_request_finishes_before_owned_service_close.factory._ui@34, test_real_active_request_finishes_before_owned_service_close.factory.app@35, test_real_active_request_finishes_before_owned_service_close.factory.held@38, test_real_active_request_finishes_before_owned_service_close.service@47, test_real_active_request_finishes_before_owned_service_close.request@50, test_real_active_request_finishes_before_owned_service_close.request.client@51, test_real_active_request_finishes_before_owned_service_close.request.response@52, test_real_active_request_finishes_before_owned_service_close.stop@56, test_real_active_request_finishes_before_owned_service_close.closer@60, test_real_active_request_finishes_before_owned_service_close.worker@60, test_real_active_request_finishes_before_owned_service_close.worker@63, test_real_active_request_finishes_before_owned_service_close.closer@66, test_real_active_request_finishes_before_owned_service_close.port@77, test_real_active_request_finishes_before_owned_service_close.connection@78, test_factory_failure_releases_bound_socket@90, test_factory_failure_releases_bound_socket.monkeypatch@90, test_factory_failure_releases_bound_socket.tmp_path@90, test_factory_failure_releases_bound_socket.sockets@92, test_factory_failure_releases_bound_socket.original@93, test_factory_failure_releases_bound_socket.record@95, test_factory_failure_releases_bound_socket.record.args@95, test_factory_failure_releases_bound_socket.record.kwargs@95, test_factory_failure_releases_bound_socket.record.result@96, test_factory_failure_releases_bound_socket.unavailable@100, test_factory_failure_releases_bound_socket.unavailable._args@100, test_unstarted_service_close_releases_listener@109, test_unstarted_service_close_releases_listener.tmp_path@109, test_unstarted_service_close_releases_listener._args@111, test_unstarted_service_close_releases_listener.service@111

from __future__ import annotations

import asyncio
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from app.native_host import LocalService


def wait_for(predicate, seconds=5):
    """Bound test waiting by observed state; never assume readiness after a fixed sleep."""
    until = time.monotonic() + seconds
    while not predicate():
        if time.monotonic() > until:
            raise AssertionError("Owned test state did not complete")
        time.sleep(0.01)


def test_real_active_request_finishes_before_owned_service_close(tmp_path: Path):
    """A real request barrier proves normal shutdown waits and preserves the result before listener release."""
    entered, release, returned, closed = (threading.Event() for _ in range(4))
    observations = []

    def factory(_directory, _origin, _ui):
        app = FastAPI()

        @app.get("/held")
        async def held():
            entered.set()
            while not release.is_set():
                await asyncio.sleep(0.01)
            (tmp_path / "committed.txt").write_text("complete")
            return {"completed": True}

        return app

    service = LocalService(factory, tmp_path, tmp_path)
    service.thread.start()

    def request():
        with httpx.Client(trust_env=False, timeout=10) as client:
            response = client.get(service.origin + "/held")
            observations.append((response.status_code, response.json()))
        returned.set()

    def stop():
        service.close()
        closed.set()

    worker = closer = None
    try:
        wait_for(lambda: service.server.started)
        worker = threading.Thread(target=request)
        worker.start()
        assert entered.wait(5)
        closer = threading.Thread(target=stop)
        closer.start()
        wait_for(lambda: service.server.should_exit)
        assert not closed.wait(0.2)
        assert not service.done.is_set()
        assert not (tmp_path / "committed.txt").exists()
        release.set()
        assert returned.wait(5) and closed.wait(5)
        assert observations == [(200, {"completed": True})]
        assert (tmp_path / "committed.txt").read_text() == "complete"
        assert not service.failed
        port = int(service.origin.rsplit(":", 1)[1])
        with socket.socket() as connection:
            assert connection.connect_ex(("127.0.0.1", port)) != 0
    finally:
        release.set()
        service.close()
        if worker is not None:
            worker.join(5)
        if closer is not None:
            closer.join(5)
        assert not service.thread.is_alive()


def test_factory_failure_releases_bound_socket(tmp_path: Path, monkeypatch):
    """An actual listener allocated before a failed application factory must not leak."""
    sockets = []
    original = socket.socket

    def record(*args, **kwargs):
        result = original(*args, **kwargs)
        sockets.append(result)
        return result

    def unavailable(*_args):
        raise ValueError("bad profile")

    monkeypatch.setattr("app.native_host.socket.socket", record)
    with pytest.raises(ValueError, match="bad profile"):
        LocalService(unavailable, tmp_path, tmp_path)
    assert len(sockets) == 1 and sockets[0].fileno() == -1


def test_unstarted_service_close_releases_listener(tmp_path: Path):
    """A failed native window setup may close an unstarted owner without starting a second service."""
    service = LocalService(lambda *_args: FastAPI(), tmp_path, tmp_path)
    service.close()
    assert service.listener.fileno() == -1
    assert service.thread.ident is None
