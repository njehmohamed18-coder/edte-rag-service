from pathlib import Path
import pytest
from src.services.chunker import (
    split_text_into_chunks,
    parse_document_content,
    parse_document_file,
)


def test_split_text_respects_size_and_overlap_bounds() -> None:
    sample_text = " ".join([f"word_{i}" for i in range(200)])
    chunks = split_text_into_chunks(sample_text, chunk_size=120, chunk_overlap=20)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 120


def test_split_text_invalid_parameters() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        split_text_into_chunks("hello", chunk_size=0, chunk_overlap=0)

    with pytest.raises(ValueError, match="chunk_overlap"):
        split_text_into_chunks("hello", chunk_size=100, chunk_overlap=100)


def test_parse_document_content_creates_canonical_nodes() -> None:
    doc, chunks = parse_document_content(
        doc_id="sec_policy",
        title="Security Policy",
        uri="docs/sec_policy.md",
        raw_text="Interns must never modify invoice tables.",
        chunk_size=200,
        chunk_overlap=20,
    )
    assert doc.urn == "urn:doc:sec_policy"
    assert len(chunks) == 1
    assert chunks[0].urn == "urn:chunk:sec_policy:0"
    assert chunks[0].chunk_index == 0


def test_parse_markdown_fixture_file() -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "sec_arch_guide.md"
    doc, chunks = parse_document_file(fixture_path, chunk_size=180, chunk_overlap=30)
    assert doc.urn == "urn:doc:sec_arch_guide"
    assert len(chunks) >= 2
    assert any("Interns must never modify invoice tables" in c.text for c in chunks)


def test_unsupported_file_extension_raises_error(tmp_path: Path) -> None:
    bad_file = tmp_path / "archive.zip"
    bad_file.write_text("dummy", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported document file format"):
        parse_document_file(bad_file)
