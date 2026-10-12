"""Jason Stys: generate only synthetic PDF and Python/TypeScript parity test vectors."""

# Index: json@4, Path@5, PdfWriter@7, DecodedStreamObject@8, DictionaryObject@8, NameObject@8, samples@10, assess@11, main@14, main.folder@16, main.writer@18, main.page@19, main.stream@20, main.font@23, main.output@33, main.applicants@35, main.jobs@35, main.vectors@36, main.j@38, main.a@39
import json
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.demo import samples
from app.review import assess


def main():
    """No real applicant data: publish deterministic fictional regression fixtures."""
    folder = Path("tests/fixtures")
    folder.mkdir(exist_ok=True)
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 20 200 Td (Project: Python testing) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    with (folder / "synthetic-resume.pdf").open("wb") as output:
        writer.write(output)
    jobs, applicants = samples()
    vectors = [
        {"applicant": a.model_dump(mode="json"), "job": j.model_dump(mode="json"), "assessment": assess(a, j)}
        for j in jobs
        for a in applicants
    ]
    (folder / "parity.json").write_text(json.dumps(vectors, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
