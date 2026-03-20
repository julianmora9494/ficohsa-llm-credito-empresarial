"""
Configuración centralizada del sistema usando Pydantic BaseSettings.
Todas las variables se cargan desde .env o variables de entorno del sistema.
"""
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración global del asistente de crédito empresarial."""

    # ─── Azure OpenAI (LLM) ─────────────────────────────────────────────────
    azure_openai_key: str = Field(..., env="AZURE_OPENAI_KEY")
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment_name: str = Field(
        default="gpt-4o", env="AZURE_OPENAI_DEPLOYMENT_NAME"
    )
    azure_openai_api_version: str = Field(
        default="2024-02-01", env="AZURE_OPENAI_API_VERSION"
    )

    # ─── Azure OpenAI (Embeddings) ──────────────────────────────────────────
    azure_openai_embedding_deployment: str = Field(
        default="text-embedding-3-small", env="AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )
    azure_openai_embedding_dimension: int = Field(
        default=1536, env="AZURE_OPENAI_EMBEDDING_DIMENSION"
    )

    # ─── Azure AI Search (opcional) ─────────────────────────────────────────
    azure_search_key: Optional[str] = Field(default=None, env="AZURE_SEARCH_KEY")
    azure_search_endpoint: Optional[str] = Field(
        default=None, env="AZURE_SEARCH_ENDPOINT"
    )
    azure_search_index_sector: str = Field(
        default="credito-sector-index", env="AZURE_SEARCH_INDEX_SECTOR"
    )
    azure_search_index_financial: str = Field(
        default="credito-financial-index", env="AZURE_SEARCH_INDEX_FINANCIAL"
    )

    # ─── Configuración LLM ──────────────────────────────────────────────────
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=4000, ge=500, le=8000, env="LLM_MAX_TOKENS")
    llm_top_p: float = Field(default=0.95, ge=0.0, le=1.0, env="LLM_TOP_P")

    # ─── Configuración RAG ──────────────────────────────────────────────────
    chunk_size: int = Field(default=800, ge=200, le=2000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, ge=0, le=500, env="CHUNK_OVERLAP")
    top_k_sector: int = Field(default=8, ge=1, le=20, env="TOP_K_SECTOR")
    top_k_financial: int = Field(default=6, ge=1, le=20, env="TOP_K_FINANCIAL")
    reranker_top_n: int = Field(default=5, ge=1, le=15, env="RERANKER_TOP_N")

    # ─── Vectorstore ────────────────────────────────────────────────────────
    vector_store_type: Literal["faiss", "azure_search"] = Field(
        default="faiss", env="VECTOR_STORE_TYPE"
    )
    vector_store_path: Path = Field(
        default=Path("./data/vectorstore/faiss_index"), env="VECTOR_STORE_PATH"
    )
    sector_index_name: str = Field(default="sector_index", env="SECTOR_INDEX_NAME")
    financial_index_name: str = Field(
        default="financial_index", env="FINANCIAL_INDEX_NAME"
    )

    # ─── Rutas de datos ─────────────────────────────────────────────────────
    data_raw_path: Path = Field(default=Path("./data/raw"), env="DATA_RAW_PATH")
    data_processed_path: Path = Field(
        default=Path("./data/processed"), env="DATA_PROCESSED_PATH"
    )
    informes_gestion_path: Path = Field(
        default=Path("./data/raw/informes_gestion"), env="INFORMES_GESTION_PATH"
    )
    estados_financieros_path: Path = Field(
        default=Path("./data/raw/estados_financieros"), env="ESTADOS_FINANCIEROS_PATH"
    )

    # ─── Logging ────────────────────────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", env="LOG_LEVEL"
    )
    log_file: Path = Field(default=Path("./logs/app.log"), env="LOG_FILE")
    log_max_bytes: int = Field(default=10_485_760, env="LOG_MAX_BYTES")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")

    # ─── Evaluación RAGAS ───────────────────────────────────────────────────
    enable_ragas: bool = Field(default=True, env="ENABLE_RAGAS")
    ragas_metrics: str = Field(
        default="faithfulness,answer_relevancy,context_precision,context_recall",
        env="RAGAS_METRICS",
    )
    evaluation_dataset_path: Path = Field(
        default=Path("./data/evaluation"), env="EVALUATION_DATASET_PATH"
    )

    # ─── Nombre del Asistente ───────────────────────────────────────────────
    assistant_name: str = Field(default="CréditoAI", env="ASSISTANT_NAME")

    @validator("chunk_overlap")
    def validate_chunk_overlap(cls, v: int, values: dict) -> int:
        """El overlap no debe superar la mitad del chunk_size."""
        chunk_size = values.get("chunk_size", 800)
        if v >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({v}) debe ser menor que chunk_size ({chunk_size})"
            )
        return v

    @validator("azure_openai_endpoint")
    def validate_endpoint(cls, v: str) -> str:
        """El endpoint debe terminar con '/'."""
        if not v.endswith("/"):
            return v + "/"
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton para reutilizar la instancia de settings
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Retorna la instancia singleton de Settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
