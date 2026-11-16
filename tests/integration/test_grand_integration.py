import pytest
from typing import Any
from fastapi.testclient import TestClient
from src.main import app
from src.graph.client import Neo4jClient

client = TestClient(app)

def mock_execute_query(
    self: Any, 
    query: str, 
    parameters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Mock Neo4j queries to allow the integration test to run without a live database."""
    params = parameters or {}
    
    # Mock Ingestion Queries
    if "MERGE (d:Document" in query:
        return [{"urn": params.get("urn")}]
    if "MERGE (c:DocumentChunk" in query:
        return [{"urn": params.get("chunk_urn")}]
    if "[:REFERENCES]" in query:
        return [{"urn": params.get("target_urn")}]
        
    # Mock Retrieval Query
    if "CALL db.index.vector.queryNodes" in query:
        return [
            {
                "chunk_urn": "urn:chunk:grand_test:0",
                "score": 0.98,
                "text_snippet": "Interns must never modify invoice tables.",
                "related_entities": ["urn:resource:billing_db:table:invoices", "urn:role:intern"]
            }
        ]
    return []

def test_end_to_end_rag_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    # 1. Patch the Neo4j client
    monkeypatch.setattr(Neo4jClient, "execute_query", mock_execute_query)
    
    # 2. Simulate User Ingesting a Document via API
    ingest_payload = {
        "doc_id": "grand_test",
        "title": "Grand Integration Test Policy",
        "uri": "docs/grand_test.md",
        "content": "The billing_db is critical. Interns must never modify invoice tables."
    }
    ingest_response = client.post("/api/v1/rag/ingest/text", json=ingest_payload)
    assert ingest_response.status_code == 200
    ingest_data = ingest_response.json()
    assert ingest_data["document_urn"] == "urn:doc:grand_test"
    assert ingest_data["chunks_created"] >= 1
    assert ingest_data["references_linked"] > 0

    # 3. Simulate User Querying the Engine via API
    query_payload = {
        "question": "Can interns modify the billing invoices?",
        "top_k": 3,
        "expand_graph_hops": 1
    }
    query_response = client.post("/api/v1/rag/query", json=query_payload)
    assert query_response.status_code == 200
    query_data = query_response.json()
    
    # 4. Verify the final synthesized RAG response and graph context
    assert "answer" in query_data
    assert "Mock synthesis successful" in query_data["answer"]
    
    assert len(query_data["sources"]) == 1
    assert query_data["sources"][0]["text_snippet"] == "Interns must never modify invoice tables."
    
    entity_urns = [item["entity_urn"] for item in query_data["graph_context"]]
    assert "urn:resource:billing_db:table:invoices" in entity_urns
    assert "urn:role:intern" in entity_urns
