from pathlib import Path
import pytest
from pydantic import ValidationError
from src.models.domain import (
    DocumentNode,
    DocumentChunkNode,
    build_document_urn,
    build_chunk_urn,
    validate_canonical_urn,
)


def test_build_document_and_chunk_urns() -> None:
    doc_urn = build_document_urn("sec_arch_guide")
    chunk_urn = build_chunk_urn("sec_arch_guide", 3)
    assert doc_urn == "urn:doc:sec_arch_guide"
    assert chunk_urn == "urn:chunk:sec_arch_guide:3"


def test_sanitize_filename_into_canonical_urn() -> None:
    doc_urn = build_document_urn("Security Architecture Guide.pdf")
    assert doc_urn == "urn:doc:Security_Architecture_Guide_pdf"


def test_reject_negative_chunk_index() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        build_chunk_urn("sec_policy", -1)


def test_validate_all_global_canonical_urn_types() -> None:
    valid_samples = [
        "urn:system:billing_db",
        "urn:resource:billing_db:table:invoices",
        "urn:actor:usr_1024",
        "urn:role:finance_operator",
        "urn:step:tx_9801:0",
        "urn:doc:sec_arch_guide",
        "urn:chunk:sec_arch_guide:3",
    ]
    for sample in valid_samples:
        assert validate_canonical_urn(sample) == sample


def test_reject_arbitrary_id_formats() -> None:
    invalid_samples = [
        "12345",
        "doc:sec_arch_guide",
        "urn:unknown:123",
        "urn:chunk:sec_arch_guide:not_an_int",
        "urn:resource:billing_db:invoices",
    ]
    for sample in invalid_samples:
        with pytest.raises(ValueError, match="Invalid canonical URN"):
            validate_canonical_urn(sample)


def test_pydantic_models_enforce_canonical_urns() -> None:
    doc = DocumentNode(
        urn="urn:doc:sec_policy",
        title="Security Policy",
        uri="docs/sec_policy.md",
    )
    assert doc.urn == "urn:doc:sec_policy"

    with pytest.raises(ValidationError):
        DocumentNode(urn="invalid_id", title="Bad", uri="bad.md")

    chunk = DocumentChunkNode(
        urn="urn:chunk:sec_policy:0",
        text="Interns must never modify invoice tables.",
        chunk_index=0,
        referenced_urns=["urn:resource:billing_db:table:invoices"],
    )
    assert len(chunk.referenced_urns) == 1


def test_constraints_cypher_file_contains_all_required_constraints() -> None:
    cypher_file = Path(__file__).resolve().parents[2] / "schema" / "constraints.cypher"
    content = cypher_file.read_text(encoding="utf-8")
    assert "unique_doc_urn" in content
    assert "unique_chunk_urn" in content
    assert "unique_resource_urn" in content
