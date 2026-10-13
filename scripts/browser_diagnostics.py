"""Jason Stys: bounded HTTP/navigation trace metadata from synthetic CI failures only."""

# Index: json@4, zipfile@5, Path@6, main@9, main.path@11, main.trace@13, main.rows@14, main.name@15, main.source@18, main.line@19, main.record@20, main.snapshot@23
import json
import zipfile
from pathlib import Path


def main():
    """Print no headers, credentials, bodies, snapshots or applicant text; never execute a trace."""
    for path in sorted(Path("test-results").glob("*/trace.zip"))[:10]:
        print("Synthetic trace metadata:", path.parent.name)
        with zipfile.ZipFile(path) as trace:
            rows = []
            for name in trace.namelist():
                if not name.endswith(".network"):
                    continue
                with trace.open(name) as source:
                    for line in source:
                        record = json.loads(line)
                        if record.get("type") != "resource-snapshot":
                            continue
                        snapshot = record["snapshot"]
                        rows.append(
                            {
                                "method": snapshot.get("request", {}).get("method"),
                                "url": snapshot.get("request", {}).get("url"),
                                "status": snapshot.get("response", {}).get("status"),
                            }
                        )
            print(json.dumps(rows[-20:], indent=2))


if __name__ == "__main__":
    main()
