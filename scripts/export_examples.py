"""Generate public synthetic batch/schema examples and an explainable sample report."""

# Index: json@4, Path@5, samples@7, BulkImport@8, Job@8, assess@9, main@12, main.root@14, main.examples@15, main.jobs@17, main.people@17, main.documents@18, main.person@20, main.job@23, main.filename@28, main.value@28
import json
from pathlib import Path

from app.demo import samples
from app.models import BulkImport, Job
from app.review import assess


def main():
    """Export only synthetic built-in data, never runtime applicant databases."""
    root = Path(__file__).resolve().parents[1]
    examples = root / "examples"
    examples.mkdir(exist_ok=True)
    jobs, people = samples()
    documents = {
        "applicants.json": {
            "applicants": [person.model_dump(mode="json") for person in people],
            "replace": False,
        },
        "jobs.json": [job.model_dump(mode="json") for job in jobs],
        "applicant-batch.schema.json": BulkImport.model_json_schema(),
        "job.schema.json": Job.model_json_schema(),
        "advisory-report.json": assess(people[0], jobs[0]),
    }
    for filename, value in documents.items():
        (examples / filename).write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print("Exported 5 synthetic examples and schemas.")


if __name__ == "__main__":
    main()
