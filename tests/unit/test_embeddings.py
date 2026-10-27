import math
from src.services.embeddings import EmbeddingService


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def test_embedding_dimensions_and_normalization() -> None:
    service = EmbeddingService(provider="mock", dimensions=128)
    vector = service.embed_text("Interns must never modify invoice tables.")
    assert len(vector) == 128
    norm = math.sqrt(sum(v * v for v in vector))
    assert math.isclose(norm, 1.0, rel_tol=1e-3)


def test_similar_texts_score_higher_than_unrelated_texts() -> None:
    service = EmbeddingService(provider="mock", dimensions=256)
    policy_vec = service.embed_text("Interns must never modify invoice tables in billing_db")
    query_vec = service.embed_text("Did any intern modify invoice records or tables?")
    unrelated_vec = service.embed_text("Kubernetes cluster ingress controller TLS certificates")

    sim_related = _cosine_similarity(policy_vec, query_vec)
    sim_unrelated = _cosine_similarity(policy_vec, unrelated_vec)
    assert sim_related > sim_unrelated


def test_embed_batch_returns_matching_count() -> None:
    service = EmbeddingService(provider="mock", dimensions=64)
    batch = service.embed_batch(["First chunk", "Second chunk", "Third chunk"])
    assert len(batch) == 3
    assert all(len(v) == 64 for v in batch)
