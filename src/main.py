from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from src.config import settings
from src.graph.client import neo4j_client
from src.models.domain import (
    IngestTextRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from src.services.ingestion import ingestion_service
from src.services.retrieval import retrieval_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    neo4j_client.connect()
    yield
    neo4j_client.close()


app = FastAPI(
    title="EDTE Semantic GraphRAG Engine",
    description="Team 4: Semantic GraphRAG Engine API for the Enterprise Digital Twin Engine",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.post("/api/v1/rag/ingest/text", response_model=IngestResponse, tags=["Ingestion"])
def ingest_text_payload(request: IngestTextRequest) -> IngestResponse:
    try:
        return ingestion_service.ingest_text(
            doc_id=request.doc_id,
            title=request.title,
            uri=request.uri,
            raw_text=request.content,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/rag/ingest/file", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_multipart_file(file: UploadFile = File(...)) -> IngestResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")
    try:
        content = await file.read()
        return ingestion_service.ingest_uploaded_bytes(
            filename=file.filename,
            file_bytes=content,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/rag/query", response_model=QueryResponse, tags=["Retrieval"])
def execute_rag_query(request: QueryRequest) -> QueryResponse:
    """Execute a hybrid GraphRAG query to retrieve semantic text and graph topology context."""
    try:
        return retrieval_service.execute_query(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
