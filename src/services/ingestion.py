from pathlib import Path
import time
from src.graph.repository import GraphRAGRepository, graph_repository
from src.models.domain import IngestResponse
from src.services.chunker import (
    extract_text_from_pdf_bytes,
    parse_document_content,
    parse_document_file,
)
from src.services.embeddings import EmbeddingService, embedding_service
from src.services.entity_extractor import extract_referenced_urns


class IngestionService:
    def __init__(
        self,
        repository: GraphRAGRepository | None = None,
        embedder: EmbeddingService | None = None,
    ) -> None:
        self.repository = repository or graph_repository
        self.embedder = embedder or embedding_service

    def ingest_text(
        self,
        doc_id: str,
        title: str,
        uri: str,
        raw_text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> IngestResponse:
        start_time = time.perf_counter()
        document, chunks = parse_document_content(
            doc_id=doc_id,
            title=title,
            uri=uri,
            raw_text=raw_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        total_references = 0
        for chunk in chunks:
            chunk.embedding = self.embedder.embed_text(chunk.text)
            chunk.referenced_urns = extract_referenced_urns(chunk.text)

        self.repository.upsert_document_and_chunks(document, chunks)

        for chunk in chunks:
            total_references += self.repository.link_chunk_references(
                chunk.urn, chunk.referenced_urns
            )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return IngestResponse(
            document_urn=document.urn,
            chunks_created=len(chunks),
            references_linked=total_references,
            execution_time_ms=elapsed_ms,
        )

    def ingest_file(self, file_path: Path) -> IngestResponse:
        document, _ = parse_document_file(file_path)
        if file_path.suffix.lower() == ".pdf":
            raw_text = extract_text_from_pdf_bytes(file_path.read_bytes())
        else:
            raw_text = file_path.read_text(encoding="utf-8")

        return self.ingest_text(
            doc_id=file_path.stem,
            title=document.title,
            uri=str(file_path),
            raw_text=raw_text,
        )

    def ingest_uploaded_bytes(
        self,
        filename: str,
        file_bytes: bytes,
    ) -> IngestResponse:
        path_obj = Path(filename)
        suffix = path_obj.suffix.lower()
        if suffix == ".pdf":
            raw_text = extract_text_from_pdf_bytes(file_bytes)
        elif suffix in {".md", ".txt", ".markdown"}:
            raw_text = file_bytes.decode("utf-8")
        else:
            raise ValueError(f"Unsupported upload format: '{suffix}'")

        return self.ingest_text(
            doc_id=path_obj.stem,
            title=path_obj.name,
            uri=f"upload://{path_obj.name}",
            raw_text=raw_text,
        )


ingestion_service = IngestionService()
