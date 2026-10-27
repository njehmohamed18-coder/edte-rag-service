from pathlib import Path
from src.config import settings
from src.graph.client import Neo4jClient, neo4j_client

VECTOR_INDEX_NAME = "chunk_embedding_index"


def apply_constraints(
    client: Neo4jClient | None = None,
    cypher_path: Path | None = None,
) -> int:
    target_client = client or neo4j_client
    path = cypher_path or Path(__file__).resolve().parents[2] / "schema" / "constraints.cypher"
    content = path.read_text(encoding="utf-8")
    statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]
    for statement in statements:
        target_client.execute_query(statement)
    return len(statements)


def ensure_vector_index(
    client: Neo4jClient | None = None,
    dimensions: int | None = None,
) -> None:
    target_client = client or neo4j_client
    dims = dimensions or settings.embedding_dimensions
    query = f"""
    CREATE VECTOR INDEX {VECTOR_INDEX_NAME} IF NOT EXISTS
    FOR (c:DocumentChunk) ON (c.embedding)
    OPTIONS {{
        indexConfig: {{
            `vector.dimensions`: {dims},
            `vector.similarity_function`: 'cosine'
        }}
    }}
    """
    target_client.execute_query(query)
