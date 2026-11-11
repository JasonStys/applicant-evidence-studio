"""Jason Stys: exercise the real packaged binary with disposable accounts, never user data."""

# Index: json@4, os@5, queue@6, re@7, secrets@8, subprocess@9, sys@10, tempfile@11, threading@12, Path@13, httpx@15, VERSION@17, main@20, main.binary@22, main.folder@25, main.nonce@26, main.environment@27, main.original_folder@36, main.canonical_folder@37, main.alias_checked@38, main.refused@43, main.process@55, main.output@64, main.startup@65, main.collect@67, main.collect.line@69, main.collector@74, main.origin@77, main._@78, main.line@80, main.match@87, main.origin@89, main.headers@93, main.client@94, main.script@98, main.credentials@101, main.envelope@104, main.client@127, main.killer@153
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
            # macOS's system temporary root may use the /var -> /private/var
            # alias. Pass the actual newly-owned directory, preserving the
            # application's intentional ancestor-alias refusal.
            "AES_DESKTOP_DATA": str(Path(folder).resolve()),
            "AES_ACCEPTANCE_NONCE": nonce,
        }
        original_folder = Path(folder)
        canonical_folder = original_folder.resolve()
        alias_checked = original_folder != canonical_folder
        if alias_checked:
            # Real compiled negative control for an actual OS temp alias. It
            # must fail at admission, before creating a marker/account/lock;
            # the positive journey then uses the same directory's real path.
            refused = subprocess.run(  # noqa: S603 -- exact owned candidate; synthetic directory only
                [str(binary)],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=60,
                env={**environment, "AES_DESKTOP_DATA": str(original_folder)},
            )
            assert refused.returncode == 2 and len(refused.stdout) + len(refused.stderr) < 65536
            assert "AES_STARTUP_REFUSED phase=profile-admission type=ValueError" in refused.stderr
            assert not list(canonical_folder.iterdir()), "Refused alias mutated the synthetic profile"
        print(f"Synthetic system-temp alias control: exercised={alias_checked}", flush=True)
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
        startup = []

        def collect():
            """Read startup messages without a blocking UI or unbounded wait."""
            for line in process.stdout:
                if len(startup) < 20:
                    startup.append(line[:512])
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
                        raise RuntimeError(
                            "Packaged application exited before readiness: " + "".join(startup)
                        ) from None
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
                        "actual_system_temp_alias_refusal": alias_checked,
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
