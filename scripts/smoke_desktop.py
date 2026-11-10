"""Jason Stys: exercise the real packaged binary with disposable accounts, never user data."""

# Index: json@4, os@5, queue@6, re@7, subprocess@8, sys@9, tempfile@10, threading@11, Path@12, httpx@14, VERSION@16, main@19, main.binary@21, main.folder@24, main.environment@25, main.process@26, main.output@34, main.collect@36, main.collect.line@38, main.origin@43, main._@44, main.line@46, main.match@51, main.origin@53, main.headers@57, main.client@58, main.script@62, main.credentials@65, main.envelope@68, main.killer@97
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import httpx

from app import VERSION


def main():
    """Launch hidden for QA, test real HTTP/login/ciphertext flow, then stop that process tree."""
    binary = Path(sys.argv[1]).resolve()
    if not binary.is_file():
        raise SystemExit("Packaged binary missing")
    with tempfile.TemporaryDirectory(prefix="aes-packaged-qa-") as folder:
        environment = {**os.environ, "AES_NO_BROWSER": "1", "AES_DESKTOP_DATA": folder}
        process = subprocess.Popen(  # noqa: S603 -- explicitly selected locally built binary only
            [str(binary)],
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

        threading.Thread(target=collect, daemon=True).start()
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
            Path("artifacts").mkdir(exist_ok=True)
            Path("artifacts/packaged-smoke.json").write_text(
                json.dumps(
                    {"platform": sys.platform, "result": "passed", "checks": 8, "real_user_data": False},
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
            process.stdout.close()


if __name__ == "__main__":
    main()
