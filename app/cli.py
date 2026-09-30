"""Cross-platform local launcher and explicit synthetic-data seed command."""

# Index: argparse@4, os@5, secrets@6, Path@7, uvicorn@9, create_app@11, samples@12, Store@13, main@16, main.parser@18, main.args@23, main.applicants@25, main.jobs@25, main.store@26, main.job@28, main.token@34, main.origin@35
import argparse
import os
import secrets
from pathlib import Path

import uvicorn

from app.api import create_app
from app.demo import samples
from app.store import Store


def main():
    """Serve loopback-only or seed synthetic records; never overwrite data implicitly."""
    parser = argparse.ArgumentParser(description="Applicant Evidence Studio — local advisory review")
    parser.add_argument("command", choices=["serve", "seed"])
    parser.add_argument("--port", type=int, default=8014)
    parser.add_argument("--data", type=Path, default=Path("runtime/local"))
    parser.add_argument("--ui", type=Path, default=Path("dist"))
    args = parser.parse_args()
    if args.command == "seed":
        jobs, applicants = samples()
        store = Store(args.data / "applicants.db")
        store.import_applicants(applicants)
        for job in jobs:
            store.save_job(job)
        print("Imported 6 clearly synthetic records and 3 job rubrics.")
        return
    if not 1024 <= args.port <= 65535:
        parser.error("Choose an unprivileged port from 1024 to 65535")
    token = os.environ.get("AES_SESSION_TOKEN") or secrets.token_urlsafe(32)
    origin = f"http://127.0.0.1:{args.port}"
    print(f"Open {origin}/#token={token}", flush=True)
    uvicorn.run(
        create_app(args.data, token, origin, args.ui), host="127.0.0.1", port=args.port, access_log=False
    )


if __name__ == "__main__":
    main()
