"""Jason Stys: disposable ciphertext account service for private-mode browser tests."""

# Index: os@4, tempfile@5, Path@6, uvicorn@8, create_private_app@10, main@13, main.folder@15, main.port@16
import os
import tempfile
from pathlib import Path

import uvicorn

from app.private_api import create_private_app


def main():
    """Never use existing user accounts or real applicant runtime data in tests."""
    with tempfile.TemporaryDirectory(prefix="aes-private-test-") as folder:
        port = int(os.environ.get("AES_PRIVATE_TEST_PORT", "8025"))
        uvicorn.run(
            create_private_app(Path(folder), f"http://127.0.0.1:{port}", Path("dist")),
            host="127.0.0.1",
            port=port,
            access_log=False,
        )


if __name__ == "__main__":
    main()
