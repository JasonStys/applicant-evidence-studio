"""Start isolated seeded browser-test storage in a temporary directory."""

# Index: os@4, tempfile@5, Path@6, uvicorn@8, create_app@10, samples@11, Store@12, main@15, main.directory@17, main.data@18, main.store@19, main.jobs@20, main.people@20, main.job@22, main.port@24, main.application@25
import os
import tempfile
from pathlib import Path

import uvicorn

from app.api import create_app
from app.demo import samples
from app.store import Store


def main():
    """Keep a disposable synthetic server alive only for the browser test session."""
    with tempfile.TemporaryDirectory(prefix="applicant-evidence-test-") as directory:
        data = Path(directory)
        store = Store(data / "applicants.db")
        jobs, people = samples()
        store.import_applicants(people)
        for job in jobs:
            store.save_job(job)
        port = int(os.environ.get("AES_TEST_PORT", "8015"))
        application = create_app(
            data, "synthetic_browser_session_0123456789_abcdef", f"http://127.0.0.1:{port}", Path("dist")
        )
        uvicorn.run(application, host="127.0.0.1", port=port, access_log=False)


if __name__ == "__main__":
    main()
