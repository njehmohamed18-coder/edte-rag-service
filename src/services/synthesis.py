import httpx
from src.config import settings
from src.models.domain import SourceCitation, GraphContextItem


class SynthesisService:
    def __init__(self, provider: str | None = None) -> None:
        self.provider = (provider or settings.llm_provider).lower()

    def generate_answer(
        self,
        question: str,
        sources: list[SourceCitation],
        graph_context: list[GraphContextItem],
    ) -> str:
        context_parts: list[str] = []
        for s in sources:
            context_parts.append(f"Text ({s.chunk_urn}): {s.text_snippet}")
        for g in graph_context:
            context_parts.append(f"Entity: {g.entity_urn} (Connected via {g.connection_type})")
        
        context_text = "\n".join(context_parts)
        prompt = (
            f"Answer the question based ONLY on the following context.\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {question}\nAnswer:"
        )

        if self.provider == "ollama":
            return self._generate_ollama(prompt)
        elif self.provider == "openai":
            return self._generate_openai(prompt)
        return self._generate_mock(prompt)

    def _generate_mock(self, prompt: str) -> str:
        return f"Mock synthesis successful. Processed {len(prompt)} prompt characters."

    def _generate_ollama(self, prompt: str) -> str:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        response = httpx.post(
            url,
            json={"model": settings.llm_model, "prompt": prompt, "stream": False},
            timeout=60.0,
        )
        response.raise_for_status()
        return str(response.json().get("response", ""))

    def _generate_openai(self, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60.0,
        )
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"])


synthesis_service = SynthesisService()
