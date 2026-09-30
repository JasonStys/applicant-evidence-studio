"""Conservative TXT/PDF/DOCX extraction with explicit uncertainty and no document execution.

Raw text is retained for human review. Proposed taxonomy matches stay unreviewed;
no degree, skill quality or employment duration is inferred from formatting.
"""

# Index: base64@8, io@9, json@10, os@11, re@12, subprocess@13, sys@14, zipfile@15, Path@16, ElementTree@18, SKILLS@20, MAX_FILE@22, MAX_TEXT@23, WORD_NS@24, extract_bytes@27, extract_bytes.content@27, extract_bytes.filename@27, extract_bytes.extension@31, extract_bytes.warnings@32, extract_bytes.text@34, extract_bytes.archive@38, extract_bytes.entries@39, extract_bytes.entry@40, extract_bytes.entry@42, extract_bytes.entry@46, extract_bytes.document@49, extract_bytes.root@52, extract_bytes.lines@53, extract_bytes.paragraph@54, extract_bytes.node@55, extract_bytes.text@56, extract_bytes.PdfReader@63, extract_bytes.reader@65, extract_bytes.texts@70, extract_bytes.page@71, extract_bytes.page_text@72, extract_bytes.value@78, extract_bytes.text@80, extract_isolated@93, extract_isolated.content@93, extract_isolated.filename@93, extract_isolated.decoded@96, extract_isolated.environment@101, extract_isolated.key@103, extract_isolated.value@103, extract_isolated.result@107, extract_isolated.data@120, proposed_claims@126, proposed_claims.source_id@126, proposed_claims.text@126, proposed_claims.proposals@128, proposed_claims.aliases@129, proposed_claims.line@130, proposed_claims.line_number@130, proposed_claims.match@131, proposed_claims.section@134, proposed_claims.summary@134, proposed_claims.kind@135, proposed_claims.skill@142, proposed_claims.term@145
import base64
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from defusedxml import ElementTree

from app.models import SKILLS

MAX_FILE = 2_000_000
MAX_TEXT = 80_000
WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extract_bytes(filename: str, content: bytes) -> dict:
    """Extract supported text and warnings; reject malformed, encrypted or unsafe input."""
    if not content or len(content) > MAX_FILE:
        raise ValueError("File must contain 1 to 2,000,000 bytes")
    extension = Path(filename).suffix.casefold()
    warnings = []
    if extension in {".txt", ".md"}:
        text = content.decode("utf-8-sig", errors="strict")
        if "\x00" in text:
            raise ValueError("Binary data is not a text resume")
    elif extension == ".docx":
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 500 or sum(entry.file_size for entry in entries) > 15_000_000:
                raise ValueError("DOCX expansion limit exceeded")
            if any(entry.file_size / max(1, entry.compress_size) > 100 for entry in entries):
                raise ValueError("Suspicious DOCX compression ratio")
            if any(
                "vbaproject" in entry.filename.casefold() or "embeddings/" in entry.filename.casefold()
                for entry in entries
            ):
                raise ValueError("Embedded objects or macros are not accepted")
            document = archive.getinfo("word/document.xml")
            if document.file_size > 2_000_000:
                raise ValueError("DOCX text XML limit exceeded")
            root = ElementTree.fromstring(archive.read(document))
            lines = []
            for paragraph in root.iter(WORD_NS + "p"):
                lines.append("".join(node.text or "" for node in paragraph.iter(WORD_NS + "t")))
            text = "\n".join(lines)
            warnings.append(
                "DOCX formatting, comments, deleted revisions, images and embedded objects are not interpreted. Verify the original."
            )
    elif extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("PDF signature missing")
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content), strict=True)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDF: provide an authorized decrypted copy")
        if len(reader.pages) > 30:
            raise ValueError("PDF page limit exceeded (30)")
        texts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if not page_text.strip():
                warnings.append(
                    "A PDF page has no extractable text; scanned/image contents need manual review or an authorized OCR export."
                )
            texts.append(page_text)
            if sum(len(value) for value in texts) > MAX_TEXT:
                raise ValueError("Extracted text limit exceeded")
        text = "\n".join(texts)
        warnings.append(
            "PDF reading order, tables, equations and images may not be preserved. Verify the original."
        )
    else:
        raise ValueError("Supported intake: UTF-8 TXT/MD, DOCX and text-based PDF")
    if len(text) > MAX_TEXT:
        raise ValueError("Extracted text limit exceeded")
    if not text.strip():
        warnings.append("No text extracted: manual review required; no qualifications inferred.")
    return {"text": text, "warnings": list(dict.fromkeys(warnings)), "filename": Path(filename).name}


def extract_isolated(filename: str, content: str) -> dict:
    """Run trusted parsing code in a timed child process; uploads are data, never code."""
    try:
        decoded = base64.b64decode(content, validate=True)
    except ValueError as error:
        raise ValueError("Invalid base64 content") from error
    if not decoded or len(decoded) > MAX_FILE:
        raise ValueError("File size limit exceeded")
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in {"PATH", "SYSTEMROOT", "TEMP", "TMP", "LANG", "HOME"}
    }
    try:
        result = subprocess.run(
            [sys.executable, "-m", "app.extract"],
            input=json.dumps({"filename": filename, "content": content}),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env=environment,
        )  # noqa: S603
    except subprocess.TimeoutExpired as error:
        raise ValueError("Document parsing timed out; use a simpler text export") from error
    if result.returncode or len(result.stdout) > 500_000:
        raise ValueError("Document could not be parsed safely; use a text export")
    data = json.loads(result.stdout)
    if "error" in data:
        raise ValueError(data["error"])
    return data


def proposed_claims(text: str, source_id: str) -> list[dict]:
    """Suggest only declared skill mentions for explicit professional-section lines."""
    proposals = []
    aliases = {"cpp": ["c++"], "csharp": ["c#"], "html_css": ["html", "css"], "git_ci": ["git", "ci/cd"]}
    for line_number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^(Skills|Project|Coursework|Experience|Work sample)\s*:\s*(.+)$", line, flags=re.I)
        if not match:
            continue
        section, summary = match.groups()
        kind = {
            "skills": "work_sample",
            "project": "project",
            "coursework": "coursework",
            "experience": "employment",
            "work sample": "work_sample",
        }[section.casefold()]
        for skill in SKILLS:
            if any(
                re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", summary.casefold())
                for term in aliases.get(skill, [skill.replace("_", " ")])
            ):
                proposals.append(
                    {
                        "id": f"claim_{len(proposals) + 1}",
                        "skill": skill,
                        "kind": kind,
                        "level": "declared",
                        "summary": summary[:1200],
                        "source_id": source_id,
                        "locator": f"extracted line {line_number}",
                        "reviewed": False,
                    }
                )
                if len(proposals) == 150:
                    return proposals
    return proposals
