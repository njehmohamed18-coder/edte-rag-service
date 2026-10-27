from io import BytesIO
from pathlib import Path
from pypdf import PdfReader
from src.models.domain import (
    DocumentNode,
    DocumentChunkNode,
    build_document_urn,
    build_chunk_urn,
    sanitize_identifier,
)


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be strictly positive.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and < chunk_size.")

    cleaned = text.strip()
    if not cleaned:
        return []

    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    text_length = len(cleaned)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        if end < text_length:
            # Prefer breaking on newline or space for semantic coherence
            newline_break = cleaned.rfind("\n", start, end)
            space_break = cleaned.rfind(" ", start, end)
            if newline_break > start + (chunk_size // 2):
                end = newline_break
            elif space_break > start + (chunk_size // 2):
                end = space_break

        snippet = cleaned[start:end].strip()
        if snippet:
            chunks.append(snippet)

        if end >= text_length:
            break

        next_start = end - chunk_overlap
        start = next_start if next_start > start else end

    return chunks


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    pages_text: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            pages_text.append(extracted.strip())
    return "\n\n".join(pages_text)


def parse_document_content(
    doc_id: str,
    title: str,
    uri: str,
    raw_text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> tuple[DocumentNode, list[DocumentChunkNode]]:
    clean_doc_id = sanitize_identifier(doc_id)
    doc_node = DocumentNode(
        urn=build_document_urn(clean_doc_id),
        title=title,
        uri=uri,
    )

    text_chunks = split_text_into_chunks(
        raw_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunk_nodes: list[DocumentChunkNode] = []
    for idx, chunk_text in enumerate(text_chunks):
        chunk_nodes.append(
            DocumentChunkNode(
                urn=build_chunk_urn(clean_doc_id, idx),
                text=chunk_text,
                chunk_index=idx,
            )
        )

    return doc_node, chunk_nodes


def parse_document_file(
    file_path: Path,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> tuple[DocumentNode, list[DocumentChunkNode]]:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        raw_text = extract_text_from_pdf_bytes(file_path.read_bytes())
    elif suffix in {".md", ".txt", ".markdown"}:
        raw_text = file_path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported document file format: '{suffix}'")

    doc_id = file_path.stem
    title = file_path.name
    return parse_document_content(
        doc_id=doc_id,
        title=title,
        uri=str(file_path),
        raw_text=raw_text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
