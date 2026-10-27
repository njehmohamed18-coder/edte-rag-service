import re
from typing import Annotated
from pydantic import BaseModel, Field, AfterValidator

URN_PATTERNS: dict[str, re.Pattern[str]] = {
    "System": re.compile(r"^urn:system:[a-zA-Z0-9_\-]+$"),
    "Resource": re.compile(r"^urn:resource:[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-.]+$"),
    "Actor": re.compile(r"^urn:actor:[a-zA-Z0-9_\-]+$"),
    "Role": re.compile(r"^urn:role:[a-zA-Z0-9_\-]+$"),
    "ProcessStep": re.compile(r"^urn:step:[a-zA-Z0-9_\-]+:\d+$"),
    "Document": re.compile(r"^urn:doc:[a-zA-Z0-9_\-]+$"),
    "DocumentChunk": re.compile(r"^urn:chunk:[a-zA-Z0-9_\-]+:\d+$"),
}


def sanitize_identifier(raw_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "_", raw_id.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        raise ValueError("Identifier cannot be empty after sanitization.")
    return cleaned


def build_document_urn(doc_id: str) -> str:
    clean_id = sanitize_identifier(doc_id)
    return f"urn:doc:{clean_id}"


def build_chunk_urn(doc_id: str, chunk_index: int) -> str:
    if chunk_index < 0:
        raise ValueError("chunk_index must be non-negative.")
    clean_id = sanitize_identifier(doc_id)
    return f"urn:chunk:{clean_id}:{chunk_index}"


def validate_canonical_urn(value: str) -> str:
    if any(pattern.match(value) for pattern in URN_PATTERNS.values()):
        return value
    raise ValueError(f"Invalid canonical URN format: '{value}'")


def validate_document_urn(value: str) -> str:
    if URN_PATTERNS["Document"].match(value):
        return value
    raise ValueError(f"Invalid Document URN format: '{value}'")


def validate_chunk_urn(value: str) -> str:
    if URN_PATTERNS["DocumentChunk"].match(value):
        return value
    raise ValueError(f"Invalid DocumentChunk URN format: '{value}'")


CanonicalURN = Annotated[str, AfterValidator(validate_canonical_urn)]
DocumentURN = Annotated[str, AfterValidator(validate_document_urn)]
DocumentChunkURN = Annotated[str, AfterValidator(validate_chunk_urn)]


class DocumentNode(BaseModel):
    urn: DocumentURN
    title: str
    uri: str


class DocumentChunkNode(BaseModel):
    urn: DocumentChunkURN
    text: str
    chunk_index: int = Field(ge=0)
    embedding: list[float] = Field(default_factory=list)
    referenced_urns: list[CanonicalURN] = Field(default_factory=list)


class SourceCitation(BaseModel):
    chunk_urn: DocumentChunkURN
    score: float
    text_snippet: str


class GraphContextItem(BaseModel):
    entity_urn: CanonicalURN
    related_actors: list[str] = Field(default_factory=list)
    connection_type: str


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)
    expand_graph_hops: int = Field(default=1, ge=1, le=3)


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceCitation]
    graph_context: list[GraphContextItem]


class IngestTextRequest(BaseModel):
    doc_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    uri: str = Field(default="inline://document")
    content: str = Field(min_length=1)


class IngestResponse(BaseModel):
    document_urn: DocumentURN
    chunks_created: int
    references_linked: int
    execution_time_ms: float
