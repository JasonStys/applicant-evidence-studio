"""Trusted document-worker entrypoint; Linux workers also cap memory and CPU.

Windows/macOS timeout is enforced by the parent; a hard memory cap is not claimed there.
"""

# Index: base64@7, json@8, sys@9, main@12, main.resource@15, main.extract_bytes@20, main.data@22, main.result@23, main.result@25
import base64
import json
import sys


def main():
    """Read one bounded document and emit JSON; hide parser exception details."""
    if sys.platform.startswith("linux"):
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
    try:
        from app.ingest import extract_bytes

        data = json.loads(sys.stdin.read(2_900_000))
        result = extract_bytes(data["filename"], base64.b64decode(data["content"], validate=True))
    except Exception:
        result = {
            "error": "Unsupported, damaged, encrypted or resource-limited document. Use a text export and inspect the original."
        }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
