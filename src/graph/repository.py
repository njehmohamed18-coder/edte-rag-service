from typing import Any
from src.graph.client import Neo4jClient, neo4j_client
from src.models.domain import DocumentNode, DocumentChunkNode

MERGE_DOCUMENT_CYPHER = """
MERGE (d:Document {urn: $urn})
SET d.title = $title,
    d.uri = $uri
RETURN d.urn AS urn
"""

MERGE_CHUNK_CYPHER = """
MATCH (d:Document {urn: $doc_urn})
MERGE (c:DocumentChunk {urn: $chunk_urn})
SET c.text = $text,
    c.chunk_index = $chunk_index,
    c.embedding = $embedding
MERGE (d)-[:CONTAINS]->(c)
RETURN c.urn AS urn
"""


class GraphRAGRepository:
    def __init__(self, client: Neo4jClient | None = None) -> None:
        self.client = client or neo4j_client

    def upsert_document_and_chunks(
        self,
        document: DocumentNode,
        chunks: list[DocumentChunkNode],
    ) -> int:
        self.client.execute_query(
            MERGE_DOCUMENT_CYPHER,
            {
                "urn": document.urn,
                "title": document.title,
                "uri": document.uri,
            },
        )
        for chunk in chunks:
            self.client.execute_query(
                MERGE_CHUNK_CYPHER,
                {
                    "doc_urn": document.urn,
                    "chunk_urn": chunk.urn,
                    "text": chunk.text,
                    "chunk_index": chunk.chunk_index,
                    "embedding": chunk.embedding,
                },
            )
        return len(chunks)

    def list_indexed_chunks(self) -> list[dict[str, Any]]:
        query = """
        MATCH (d:Document)-[:CONTAINS]->(c:DocumentChunk)
        OPTIONAL MATCH (c)-[:REFERENCES]->(target)
        RETURN d.urn AS document_urn,
               d.title AS title,
               c.urn AS chunk_urn,
               c.chunk_index AS chunk_index,
               c.text AS text,
               collect(DISTINCT target.urn) AS referenced_urns
        ORDER BY d.urn, c.chunk_index
        """
        return self.client.execute_query(query)
