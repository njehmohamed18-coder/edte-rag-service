from pathlib import Path
from src.graph.client import Neo4jClient, neo4j_client


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
