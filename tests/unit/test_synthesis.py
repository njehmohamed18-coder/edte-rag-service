from src.services.synthesis import SynthesisService
from src.models.domain import SourceCitation, GraphContextItem


def test_mock_synthesis_returns_valid_string_with_context() -> None:
    service = SynthesisService(provider="mock")
    sources = [
        SourceCitation(
            chunk_urn="urn:chunk:sec_policy:0",
            score=0.99,
            text_snippet="Interns must never modify invoice tables."
        )
    ]
    graph_context = [
        GraphContextItem(
            entity_urn="urn:role:intern",
            connection_type="REFERENCES"
        )
    ]
    
    answer = service.generate_answer(
        question="Who is prohibited from modifying invoices?",
        sources=sources,
        graph_context=graph_context
    )
    
    assert isinstance(answer, str)
    assert len(answer) > 0
    assert "Mock synthesis successful" in answer
