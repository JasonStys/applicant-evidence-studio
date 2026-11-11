"""Jason Stys: exercise the real packaged binary with disposable accounts, never user data."""

# Index: json@4, os@5, queue@6, re@7, secrets@8, subprocess@9, sys@10, tempfile@11, threading@12, Path@13, httpx@15, VERSION@17, main@20, main.binary@22, main.folder@25, main.nonce@26, main.environment@27, main.process@33, main.output@42, main.collect@44, main.collect.line@46, main.collector@49, main.origin@52, main._@53, main.line@55, main.match@60, main.origin@62, main.headers@66, main.client@67, main.script@71, main.credentials@74, main.envelope@77, main.client@100, main.killer@125
import json
import os
import queue
import re
import secrets
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import httpx

from app import VERSION


def main():
    """Test the real HTTP/login/ciphertext flow, then close through the normal owned native handler."""
    binary = Path(sys.argv[1]).resolve()
    if not binary.is_file():
        raise SystemExit("Packaged binary missing")
    with tempfile.TemporaryDirectory(prefix="aes-packaged-qa-") as folder:
        nonce = secrets.token_hex(32)
        environment = {
            **os.environ,
            "AES_NO_BROWSER": "1",
            "AES_DESKTOP_DATA": folder,
            "AES_ACCEPTANCE_NONCE": nonce,
        }
        process = subprocess.Popen(  # noqa: S603 -- explicitly selected locally built binary only
            [str(binary)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=environment,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )  # noqa: S603 -- explicitly selected locally built binary only
        output = queue.Queue()

        def collect():
            """Read startup messages without a blocking UI or unbounded wait."""
            for line in process.stdout:
                output.put(line)

        collector = threading.Thread(target=collect, daemon=True)
        collector.start()
        try:
            origin = None
            for _ in range(60):
                try:
                    line = output.get(timeout=1)
                except queue.Empty:
                    if process.poll() is not None:
                        raise RuntimeError("Packaged application exited before readiness") from None
                    continue
                match = re.search(r"running at (http://127\.0\.0\.1:\d+)", line)
                if match:
                    origin = match[1]
                    break
            if not origin:
                raise RuntimeError("Packaged application did not become ready")
            headers = {"Origin": origin, "X-AES-Request": "v1"}
            with httpx.Client(base_url=origin, headers=headers, trust_env=False, timeout=10) as client:
                assert client.get("/health").json()["mode"] == "private-accounts"
                assert client.get("/health").json()["version"] == VERSION
                assert "Jason Stys" in client.get("/").text
                script = re.search(r'src="(/assets/[A-Za-z0-9_.-]+\.js)"', client.get("/").text)
                assert script, "Packaged UI script missing"
                assert "Criterion evidence comparison" in client.get(script[1]).text
                credentials = {"username": "packaged_qa", "password": "synthetic-only-packaged-password"}
                assert client.post("/vault/register", json=credentials).status_code == 200
                assert client.get("/vault/workspace").json()["revision"] == 0
                envelope = {
                    "version": 1,
                    "salt": "c3Nzc3Nzc3Nzc3Nzc3Nzcw==",
                    "iv": "aWlpaWlpaWlpaWlp",
                    "ciphertext": "eHh4eHh4eHh4eHh4eHh4eA==",
                }
                assert (
                    client.put("/vault/workspace", json={"revision": 0, "envelope": envelope}).status_code
                    == 200
                )
                assert client.get("/vault/workspace").json()["envelope"] == envelope
                assert client.post("/api/import", json={"plaintext": "never-send-real-data"}).status_code in {
                    404,
                    405,
                }
                assert client.post("/vault/logout", json={}).status_code == 200
                assert client.get("/vault/workspace").status_code == 401
            process.stdin.write(f"quit {nonce}\n")
            process.stdin.flush()
            process.stdin.close()
            assert process.wait(timeout=20) == 0
            collector.join(timeout=2)
            try:
                with httpx.Client(trust_env=False, timeout=2) as client:
                    client.get(origin + "/health")
            except httpx.TransportError:
                pass
            else:
                raise AssertionError("Owned listener survived normal native shutdown")
            Path("artifacts").mkdir(exist_ok=True)
            Path("artifacts/packaged-smoke.json").write_text(
                json.dumps(
                    {
                        "platform": sys.platform,
                        "result": "passed",
                        "checks": 8,
                        "real_user_data": False,
                        "normal_owned_exit": True,
                        "normal_exit_code": 0,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            print("Packaged application: 8 smoke checks passed; disposable synthetic data only.")
        finally:
            if sys.platform == "win32" and process.poll() is None:
                killer = Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32/taskkill.exe"
                subprocess.run(  # noqa: S603 -- exact process tree created by this test
                    [str(killer), "/PID", str(process.pid), "/T", "/F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )  # noqa: S603 -- exact process tree created by this test
            elif process.poll() is None:
                process.terminate()
            process.wait(timeout=15)
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
            collector.join(timeout=2)
            process.stdout.close()


if __name__ == "__main__":
    main()
