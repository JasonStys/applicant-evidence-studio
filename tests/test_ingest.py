"""Parser negative-input, resource-bound and source-preservation tests using synthetic bytes."""

# Index: base64@4, io@5, zipfile@6, pytest@8, DefusedXmlException@9, PdfWriter@10, DecodedStreamObject@11, DictionaryObject@11, NameObject@11, extract_bytes@13, extract_isolated@13, proposed_claims@13, docx@16, docx.extra@16, docx.xml@16, docx.buffer@18, docx.archive@19, test_utf8_and_isolated_worker@26, test_utf8_and_isolated_worker.value@28, test_utf8_and_isolated_worker.result@31, test_utf8_and_isolated_worker.claims@33, test_docx_paragraphs_table_text_and_warning@38, test_docx_paragraphs_table_text_and_warning.xml@40, test_docx_paragraphs_table_text_and_warning.result@41, test_bad_text@51, test_bad_text.content@51, test_docx_entities_macros_and_bombs@57, test_docx_entities_macros_and_bombs.content@59, test_pdf_blank_encrypted_page_bound_and_signature@68, test_pdf_blank_encrypted_page_bound_and_signature.writer@70, test_pdf_blank_encrypted_page_bound_and_signature.buffer@72, test_pdf_blank_encrypted_page_bound_and_signature.result@74, test_pdf_blank_encrypted_page_bound_and_signature.warning@76, test_pdf_blank_encrypted_page_bound_and_signature.encrypted@79, test_pdf_blank_encrypted_page_bound_and_signature.many@83, test_pdf_blank_encrypted_page_bound_and_signature._@84, test_pdf_blank_encrypted_page_bound_and_signature.buffer@86, test_unknown_format_and_base64@94, test_text_pdf_content_extraction@102, test_text_pdf_content_extraction.writer@104, test_text_pdf_content_extraction.page@105, test_text_pdf_content_extraction.font@106, test_text_pdf_content_extraction.stream@116, test_text_pdf_content_extraction.buffer@119, test_private_sections_not_proposed_and_claim_limit@124, test_private_sections_not_proposed_and_claim_limit._@127
import base64
import io
import zipfile

import pytest
from defusedxml.common import DefusedXmlException
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.ingest import extract_bytes, extract_isolated, proposed_claims


def docx(xml, extra=None):
    """Make a tiny XML extraction fixture, not a visual document artifact."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", xml)
        if extra:
            archive.writestr(*extra)
    return buffer.getvalue()


def test_utf8_and_isolated_worker():
    """UTF-8 accented names and professional text survive extraction, not scoring."""
    value = (
        "Synthetic Renée\nProject: Python API with tests\nEducation: transferred credits; degree unspecified"
    )
    result = extract_isolated("synthetic.txt", base64.b64encode(value.encode()).decode())
    assert result["text"] == value
    claims = proposed_claims(value, "resume")
    assert len(claims) == 1 and not claims[0]["reviewed"] and claims[0]["level"] == "declared"
    assert claims[0]["skill"] == "python"


def test_docx_paragraphs_table_text_and_warning():
    """Extract paragraph/table text while explicitly warning about visual/other content."""
    xml = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Skills: C++</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Table content</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>'
    result = extract_bytes("source.docx", docx(xml))
    assert "Skills: C++\nTable content" == result["text"]
    assert result["warnings"]


@pytest.mark.parametrize(
    "content",
    [b"", b"\xff", b"binary\x00content", b"x" * 2_000_001],
    ids=["empty", "invalid-utf8", "binary", "oversized"],
)
def test_bad_text(content):
    """Empty, invalid UTF-8, binary or oversized text fails explicitly."""
    with pytest.raises(ValueError):
        extract_bytes("text.txt", content)


def test_docx_entities_macros_and_bombs():
    """DTD entities, embedded macro names and excessive ZIP expansion are refused."""
    for content in [
        docx('<!DOCTYPE x [<!ENTITY z "boom">]><x>&z;</x>'),
        docx("<x/>", ("word/vbaProject.bin", "x")),
        docx("<x/>", ("word/media/bomb", "0" * 200000)),
    ]:
        with pytest.raises((ValueError, DefusedXmlException)):
            extract_bytes("source.docx", content)


def test_pdf_blank_encrypted_page_bound_and_signature():
    """Image-only/blank PDF is unknown; encrypted and excessive-page documents fail."""
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    buffer = io.BytesIO()
    writer.write(buffer)
    result = extract_bytes("blank.pdf", buffer.getvalue())
    assert not result["text"].strip() and any(
        "no extractable text" in warning for warning in result["warnings"]
    )
    writer.encrypt("secret")
    encrypted = io.BytesIO()
    writer.write(encrypted)
    with pytest.raises(ValueError, match="Encrypted"):
        extract_bytes("private.pdf", encrypted.getvalue())
    many = PdfWriter()
    for _ in range(31):
        many.add_blank_page(width=100, height=100)
    buffer = io.BytesIO()
    many.write(buffer)
    with pytest.raises(ValueError, match="page limit"):
        extract_bytes("many.pdf", buffer.getvalue())
    with pytest.raises(ValueError, match="signature"):
        extract_bytes("wrong.pdf", b"not PDF")


def test_unknown_format_and_base64():
    """Unsupported formats are never mislabeled as successful extraction."""
    with pytest.raises(ValueError, match="Supported"):
        extract_bytes("resume.exe", b"abc")
    with pytest.raises(ValueError, match="base64"):
        extract_isolated("resume.txt", "%%%")


def test_text_pdf_content_extraction():
    """A real text-content PDF fixture extracts professional text, not just blank-page warnings."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 20 250 Td (Project: Python validation) Tj ET")
    page[NameObject("/Contents")] = stream
    buffer = io.BytesIO()
    writer.write(buffer)
    assert "Project: Python validation" in extract_bytes("text.pdf", buffer.getvalue())["text"]


def test_private_sections_not_proposed_and_claim_limit():
    """Personal details are not extracted as skill claims; proposals remain bounded."""
    assert proposed_claims("Gender: Python\nReligion: SQL\nName: Java", "s") == []
    assert len(proposed_claims("\n".join("Skills: Python SQL Java" for _ in range(100)), "s")) == 150
