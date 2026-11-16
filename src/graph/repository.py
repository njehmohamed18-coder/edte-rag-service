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

LINK_CYPHER_BY_PREFIX: dict[str, str] = {
    "urn:system:": """
    MATCH (c:DocumentChunk {urn: $chunk_urn})
    MERGE (target:System {urn: $target_urn})
    ON CREATE SET target.name = $target_name
    MERGE (c)-[:REFERENCES]->(target)
    RETURN target.urn AS urn
    """,
    "urn:resource:": """
    MATCH (c:DocumentChunk {urn: $chunk_urn})
    MERGE (target:Resource {urn: $target_urn})
    ON CREATE SET target.name = $target_name, target.type =$resource_type
    MERGE (c)-[:REFERENCES]->(target)
    RETURN target.urn AS urn
    """,
    "urn:role:": """
    MATCH (c:DocumentChunk {urn: $chunk_urn})
    MERGE (target:Role {urn: $target_urn})
    ON CREATE SET target.name = $target_name
    MERGE (c)-[:REFERENCES]->(target)
    RETURN target.urn AS urn
    """,
    "urn:actor:": """
    MATCH (c:DocumentChunk {urn: $chunk_urn})
    MERGE (target:Actor {urn: $target_urn})
    ON CREATE SET target.name = $target_name
    MERGE (c)-[:REFERENCES]->(target)
    RETURN target.urn AS urn
    """,
}


def _parse_urn_metadata(target_urn: str) -> tuple[str, str]:
    parts = target_urn.split(":")
    name = parts[-1] if parts else target_urn
    resource_type = parts[3].capitalize() if len(parts) >= 5 and parts[1] == "resource" else "Unknown"
    return name, resource_type


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

    def link_chunk_references(
        self,
        chunk_urn: str,
        referenced_urns: list[str],
    ) -> int:
        linked_count = 0
        for target_urn in referenced_urns:
            for prefix, cypher in LINK_CYPHER_BY_PREFIX.items():
                if target_urn.startswith(prefix):
                    target_name, resource_type = _parse_urn_metadata(target_urn)
                    self.client.execute_query(
                        cypher,
                        {
                            "chunk_urn": chunk_urn,
                            "target_urn": target_urn,
                            "target_name": target_name,
                            "resource_type": resource_type,
                        },
                    )
                    linked_count += 1
                    break
        return linked_count


graph_repository = GraphRAGRepository()
