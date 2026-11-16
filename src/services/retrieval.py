from typing import Any
from src.graph.client import Neo4jClient, neo4j_client
from src.services.embeddings import EmbeddingService, embedding_service
from src.models.domain import QueryRequest, QueryResponse, SourceCitation, GraphContextItem

# 1. Vector similarity search on the Neo4j index
# 2. Graph expansion matching 1 to 2 hops out from the text chunk
HYBRID_SEARCH_CYPHER = """
CALL db.index.vector.queryNodes('chunk_embedding_index', $top_k,$question_embedding)
YIELD node AS chunk, score
OPTIONAL MATCH (chunk)-[:REFERENCES*1..2]-(entity)
RETURN chunk.urn AS chunk_urn,
       chunk.text AS text_snippet,
       score,
       collect(DISTINCT entity.urn) AS related_entities
ORDER BY score DESC
"""

class RetrievalService:
    def __init__(
        self,
        client: Neo4jClient | None = None,
        embedder: EmbeddingService | None = None,
    ) -> None:
        self.client = client or neo4j_client
        self.embedder = embedder or embedding_service

    def execute_query(self, request: QueryRequest) -> QueryResponse:
        # Embed the incoming question
        question_embedding = self.embedder.embed_text(request.question)
        
        # Execute the hybrid search in Neo4j
        records = self.client.execute_query(
            HYBRID_SEARCH_CYPHER,
            {
                "question_embedding": question_embedding,
                "top_k": request.top_k,
            }
        )
        
        sources: list[SourceCitation] = []
        graph_items: list[GraphContextItem] = []
        seen_entities: set[str] = set()
        
        for record in records:
            sources.append(
                SourceCitation(
                    chunk_urn=record.get("chunk_urn", ""),
                    score=float(record.get("score", 0.0)),
                    text_snippet=record.get("text_snippet", "")
                )
            )
            
            # Extract the 1-to-2 hop graph context
            for entity_urn in record.get("related_entities", []):
                if entity_urn and entity_urn not in seen_entities:
                    seen_entities.add(entity_urn)
                    graph_items.append(
                        GraphContextItem(
                            entity_urn=entity_urn,
                            related_actors=[],
                            connection_type="REFERENCES"
                        )
                    )
                    
        return QueryResponse(
            answer="LLM Synthesis will be integrated in Week 10. Raw text and graph context retrieved successfully.",
            sources=sources,
            graph_context=graph_items
        )

retrieval_service = RetrievalService()
