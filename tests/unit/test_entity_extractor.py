from typing import Any
from src.graph.repository import GraphRAGRepository, MERGE_DOCUMENT_CYPHER, MERGE_CHUNK_CYPHER
from src.models.domain import DocumentNode, DocumentChunkNode
from src.services.entity_extractor import extract_referenced_urns


class FakeNeo4jClient:
    def __init__(self) -> None:
        self.queries: list[tuple[str, dict[str, Any]]] = []

    def execute_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        self.queries.append((query, parameters or {}))
        return [{"urn": (parameters or {}).get("urn", "")}]


def test_extract_explicit_canonical_urns_from_text() -> None:
    text = (
        "The system urn:system:billing_db stores urn:resource:billing_db:table:invoices "
        "managed by urn:role:finance_operator."
    )
    extracted = extract_referenced_urns(text)
    assert "urn:system:billing_db" in extracted
    assert "urn:resource:billing_db:table:invoices" in extracted
    assert "urn:role:finance_operator" in extracted


def test_extract_implicit_policy_aliases_for_grand_integration_test() -> None:
    policy_text = "Interns must never modify invoice tables"
    extracted = extract_referenced_urns(policy_text)
    assert "urn:resource:billing_db:table:invoices" in extracted
    assert "urn:role:intern" in extracted


def test_extract_deduplicates_repeated_mentions() -> None:
    text = (
        "Table urn:resource:billing_db:table:invoices is an invoice tables asset "
        "also referenced as urn:resource:billing_db:table:invoices."
    )
    extracted = extract_referenced_urns(text)
    assert extracted.count("urn:resource:billing_db:table:invoices") == 1


def test_repository_uses_idempotent_merge_statements() -> None:
    assert "MERGE (d:Document {urn: $urn})" in MERGE_DOCUMENT_CYPHER
    assert "MERGE (c:DocumentChunk {urn: $chunk_urn})" in MERGE_CHUNK_CYPHER
    assert "MERGE (d)-[:CONTAINS]->(c)" in MERGE_CHUNK_CYPHER
    assert "CREATE " not in MERGE_DOCUMENT_CYPHER
    assert "CREATE " not in MERGE_CHUNK_CYPHER

    fake_client = FakeNeo4jClient()
    repo = GraphRAGRepository(client=fake_client)  # type: ignore[arg-type]
    doc = DocumentNode(urn="urn:doc:sec_policy", title="Sec Policy", uri="sec_policy.md")
    chunks = [
        DocumentChunkNode(
            urn="urn:chunk:sec_policy:0",
            text="Interns must never modify invoice tables",
            chunk_index=0,
            embedding=[0.1, 0.2],
        )
    ]
    count = repo.upsert_document_and_chunks(doc, chunks)
    assert count == 1
    assert len(fake_client.queries) == 2
