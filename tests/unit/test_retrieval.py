from typing import Any
from src.models.domain import QueryRequest
from src.services.retrieval import RetrievalService
from src.services.embeddings import EmbeddingService

class MockNeo4jClient:
    def execute_query(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        # Simulating a Neo4j vector search hit that also expanded to two graph entities
        return [
            {
                "chunk_urn": "urn:chunk:sec_policy:0",
                "score": 0.92,
                "text_snippet": "Interns must never modify invoice tables.",
                "related_entities": ["urn:resource:billing_db:table:invoices", "urn:role:intern"]
            }
        ]

def test_retrieval_service_hybrid_search() -> None:
    fake_client = MockNeo4jClient()
    embedder = EmbeddingService(provider="mock", dimensions=64)
    service = RetrievalService(client=fake_client, embedder=embedder)  # type: ignore[arg-type]
    
    request = QueryRequest(question="Can interns edit billing?", top_k=3, expand_graph_hops=1)
    response = service.execute_query(request)
    
    # 1. Verify text context is retrieved
    assert len(response.sources) == 1
    assert response.sources[0].chunk_urn == "urn:chunk:sec_policy:0"
    assert response.sources[0].score == 0.92
    
    # 2. Verify graph context is expanded and formatted
    assert len(response.graph_context) == 2
    entity_urns = [item.entity_urn for item in response.graph_context]
    assert "urn:resource:billing_db:table:invoices" in entity_urns
    assert "urn:role:intern" in entity_urns
