"""Jason Stys: one-file local application launcher, no package-manager commands needed.

Uses the same ciphertext account service as the website, bound to loopback only.
Data lives outside the installation in the current OS user's application folder.
"""

# Index: os@8, socket@9, sys@10, threading@11, time@12, webbrowser@13, Path@14, httpx@16, uvicorn@17, create_private_app@19, private_directory@22, private_directory.path@25, private_directory.parent@29, private_directory.parent@31, private_directory.parent@33, private_directory.path@34, main@41, main.bundle@43, main.ui@44, main.listener@47, main.port@49, main.origin@50, main.application@51, main.open_when_ready@53, main.open_when_ready.client@55, main.open_when_ready._@56
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

import httpx
import uvicorn

from app.private_api import create_private_app


def private_directory() -> Path:
    """Resolve OS-specific per-user runtime directory, never the repo or executable folder."""
    if os.environ.get("AES_DESKTOP_DATA"):
        path = Path(os.environ["AES_DESKTOP_DATA"])
        path.mkdir(parents=True, exist_ok=True)
        return path
    if sys.platform == "win32":
        parent = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    elif sys.platform == "darwin":
        parent = Path.home() / "Library/Application Support"
    else:
        parent = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    path = parent / "ApplicantEvidenceStudio"
    path.mkdir(parents=True, exist_ok=True)
    if sys.platform != "win32":
        path.chmod(0o700)
    return path


def main():
    """Bind an OS-assigned port before opening browser; never print credentials or secrets."""
    bundle = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    ui = bundle / "dist"
    if not (ui / "index.html").is_file():
        raise SystemExit("Application UI missing. Use a complete release or build the UI first.")
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    application = create_private_app(private_directory(), origin, ui)

    def open_when_ready():
        """Wait for our health endpoint, then open the default browser exactly once."""
        with httpx.Client(trust_env=False) as client:
            for _ in range(100):
                try:
                    if client.get(origin + "/health", timeout=0.2).status_code == 200:
                        if os.environ.get("AES_NO_BROWSER") != "1":
                            webbrowser.open(origin)
                        print(f"Applicant Evidence Studio by Jason Stys is running at {origin}", flush=True)
                        return
                except httpx.HTTPError:
                    pass
                time.sleep(0.1)

    threading.Thread(target=open_when_ready, daemon=True).start()
    try:
        uvicorn.Server(
            uvicorn.Config(application, host="127.0.0.1", port=port, access_log=False, proxy_headers=False)
        ).run(sockets=[listener])
    finally:
        listener.close()


if __name__ == "__main__":
    main()
