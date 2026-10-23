from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "edte-rag-service"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "edte_password"
    neo4j_database: str = "neo4j"

    llm_provider: str = "mock"
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3"
    embedding_model: str = "nomic-embed-text"
    embedding_dimensions: int = 768
    openai_api_key: str = ""


settings = Settings()
