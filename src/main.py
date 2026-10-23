from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.config import settings
from src.graph.client import neo4j_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    neo4j_client.connect()
    yield
    neo4j_client.close()


app = FastAPI(
    title="EDTE Semantic GraphRAG Engine",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
