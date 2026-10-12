"""Cross-platform local launcher and explicit synthetic-data seed command."""

# Index: argparse@4, os@5, secrets@6, Path@7, uvicorn@9, create_app@11, samples@12, create_private_app@13, Store@14, main@17, main.parser@19, main.args@26, main.applicants@28, main.jobs@28, main.store@29, main.job@31, main.origin@38, main.token@52, main.origin@53
import argparse
import os
import secrets
from pathlib import Path

import uvicorn

from app.api import create_app
from app.demo import samples
from app.private_api import create_private_app
from app.store import Store


def main():
    """Serve loopback-only or seed synthetic records; never overwrite data implicitly."""
    parser = argparse.ArgumentParser(description="Applicant Evidence Studio — local advisory review")
    parser.add_argument("command", choices=["serve", "seed", "accounts"])
    parser.add_argument("--port", type=int, default=8014)
    parser.add_argument("--data", type=Path, default=Path("runtime/local"))
    parser.add_argument("--ui", type=Path, default=Path("dist"))
    parser.add_argument("--origin", default="")
    parser.add_argument("--host", choices=["127.0.0.1", "0.0.0.0"], default="127.0.0.1")  # noqa: S104 -- explicit HTTPS-only server deployment opt-in
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
    if args.command == "accounts":
        origin = args.origin or f"http://127.0.0.1:{args.port}"
        if args.host != "127.0.0.1" and not origin.startswith("https://"):
            parser.error("Network accounts require an HTTPS origin and TLS reverse proxy")
        print(f"Applicant Evidence Studio by Jason Stys: {origin}", flush=True)
        uvicorn.run(
            create_private_app(args.data, origin, args.ui),
            host=args.host,
            port=args.port,
            access_log=False,
            proxy_headers=False,
        )
        return
    if args.host != "127.0.0.1" or args.origin:
        parser.error("Legacy developer mode stays on loopback; use accounts for private users")
    token = os.environ.get("AES_SESSION_TOKEN") or secrets.token_urlsafe(32)
    origin = f"http://127.0.0.1:{args.port}"
    print(f"Open {origin}/#token={token}", flush=True)
    uvicorn.run(
        create_app(args.data, token, origin, args.ui), host="127.0.0.1", port=args.port, access_log=False
    )


if __name__ == "__main__":
    main()
