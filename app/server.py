"""Jason Stys: explicit deployment factory for the ciphertext-only account service."""

# Index: os@4, Path@5, create_private_app@7, application@10, application.origin@12
import os
from pathlib import Path

from app.private_api import create_private_app


def application():
    """Fail closed when hosting origin is missing; runtime data must use a persistent volume."""
    origin = os.environ.get("AES_PUBLIC_ORIGIN")
    if not origin or not origin.startswith("https://"):
        raise ValueError("Set AES_PUBLIC_ORIGIN to your exact HTTPS origin before deploying")
    return create_private_app(
        Path(os.environ.get("AES_PRIVATE_DATA", "/data")), origin, Path(os.environ.get("AES_UI", "dist"))
    )
