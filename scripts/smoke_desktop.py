"""Jason Stys: exercise the real packaged binary with disposable accounts, never user data."""

# Index: json@4, os@5, queue@6, re@7, secrets@8, stat@9, subprocess@10, sys@11, tempfile@12, threading@13, Path@14, httpx@16, VERSION@18, main@21, main.binary@23, main.folder@26, main.nonce@27, main.environment@28, main.original_folder@37, main.canonical_folder@38, main.alias_checked@39, main.path@44, main.refused@50, main.process@62, main.output@71, main.startup@72, main.collect@74, main.collect.line@76, main.collector@81, main.origin@84, main._@85, main.line@87, main.match@94, main.origin@96, main.headers@100, main.client@101, main.script@105, main.credentials@108, main.envelope@111, main.client@134, main.killer@160
import json
import os
import queue
import re
import secrets
import stat
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
        alias_checked = any(
            path.is_symlink()
            or path.is_junction()
            or getattr(path.lstat(), "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            for path in (original_folder, *original_folder.parents)
        )
        if alias_checked:
            # Real compiled negative control for an actual OS temp alias. It
            # must fail at admission, before creating a marker/account/lock;
            # the positive journey then uses the same directory's real path.
            refused = subprocess.run(  # noqa: S603 -- exact owned candidate; synthetic directory only
                [str(binary)],
                input=f"quit {nonce}\n",
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
