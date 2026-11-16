from pathlib import Path
from typing import Any
from src.graph.repository import GraphRAGRepository
from src.services.embeddings import EmbeddingService
from src.services.ingestion import IngestionService


class RecordingNeo4jClient:
    def __init__(self) -> None:
        self.executed: list[tuple[str, dict[str, Any]]] = []

    def execute_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        self.executed.append((query, parameters or {}))
        return []


def test_ingestion_service_links_chunks_to_system_resource_and_role() -> None:
    fake_client = RecordingNeo4jClient()
    repo = GraphRAGRepository(client=fake_client)  # type: ignore[arg-type]
    embedder = EmbeddingService(provider="mock", dimensions=64)
    service = IngestionService(repository=repo, embedder=embedder)

    response = service.ingest_text(
        doc_id="sec_policy",
        title="Security Policy",
        uri="docs/sec_policy.md",
        raw_text=(
            "System urn:system:billing_db contains urn:resource:billing_db:table:invoices. "
            "Only urn:role:finance_operator can write; interns must never modify invoice tables."
        ),
        chunk_size=500,
        chunk_overlap=50,
    )

    assert response.document_urn == "urn:doc:sec_policy"
    assert response.chunks_created == 1
    assert response.references_linked >= 3

    reference_queries = [
        (q, params) for q, params in fake_client.executed if "[:REFERENCES]" in q
    ]
    linked_targets = {params["target_urn"] for _, params in reference_queries}
    assert "urn:system:billing_db" in linked_targets
    assert "urn:resource:billing_db:table:invoices" in linked_targets
    assert "urn:role:finance_operator" in linked_targets


def test_ingest_markdown_fixture_file() -> None:
    fake_client = RecordingNeo4jClient()
    repo = GraphRAGRepository(client=fake_client)  # type: ignore[arg-type]
    embedder = EmbeddingService(provider="mock", dimensions=64)
    service = IngestionService(repository=repo, embedder=embedder)

    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "sec_arch_guide.md"
    result = service.ingest_file(fixture_path)
    assert result.document_urn == "urn:doc:sec_arch_guide"
    assert result.chunks_created >= 1
    assert result.references_linked >= 3
