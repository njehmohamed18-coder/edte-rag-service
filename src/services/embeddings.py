import hashlib
import math
import httpx
from src.config import settings


def _deterministic_embedding(text: str, dimensions: int) -> list[float]:
    """Generates a normalized, deterministic embedding vector for offline/CI testing."""
    tokens = [tok.lower().strip(".,:;!?()[]\"'`") for tok in text.split() if tok.strip()]
    vec = [0.0] * dimensions
    if not tokens:
        return vec

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for i in range(0, len(digest), 2):
            idx = ((digest[i] << 8) | digest[i + 1]) % dimensions
            sign = 1.0 if (digest[i] % 2 == 0) else -1.0
            vec[idx] += sign

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0.0:
        vec = [round(v / norm, 6) for v in vec]
    return vec


class EmbeddingService:
    def __init__(
        self,
        provider: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        self.provider = (provider or settings.llm_provider).lower()
        self.dimensions = dimensions or settings.embedding_dimensions

    def embed_text(self, text: str) -> list[float]:
        if self.provider == "ollama":
            return self._embed_ollama(text)
        if self.provider == "openai":
            return self._embed_openai(text)
        return _deterministic_embedding(text, self.dimensions)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]

    def _embed_ollama(self, text: str) -> list[float]:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/embeddings"
        response = httpx.post(
            url,
            json={"model": settings.embedding_model, "prompt": text},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        embedding: list[float] = [float(x) for x in data["embedding"]]
        return embedding

    def _embed_openai(self, text: str) -> list[float]:
        response = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": settings.embedding_model, "input": text},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        embedding: list[float] = [float(x) for x in data["data"][0]["embedding"]]
        return embedding


embedding_service = EmbeddingService()
