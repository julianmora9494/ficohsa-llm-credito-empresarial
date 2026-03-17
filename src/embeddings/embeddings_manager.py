"""
Gestión de embeddings usando Azure OpenAI text-embedding-3-small.
Centraliza la vectorización de texto para el sistema RAG.
"""
from typing import List, Optional

from langchain_openai import AzureOpenAIEmbeddings

from src.config.settings import Settings, get_settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class EmbeddingsManager:
    """
    Manager para embeddings de texto via Azure OpenAI.
    Modelo: text-embedding-3-small (1536 dimensiones).
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """
        Inicializa el manager sin crear el cliente todavía.

        Args:
            settings: Configuración del sistema. Si es None, usa el singleton global.
        """
        self._settings = settings or get_settings()
        self._embeddings: Optional[AzureOpenAIEmbeddings] = None
        logger.info("EmbeddingsManager inicializado (cliente en lazy load)")

    @property
    def embeddings(self) -> AzureOpenAIEmbeddings:
        """
        Retorna el cliente de embeddings, inicializándolo si es necesario.
        Patrón lazy loading.
        """
        if self._embeddings is None:
            self._embeddings = self._build_client()
        return self._embeddings

    def _build_client(self) -> AzureOpenAIEmbeddings:
        """Construye el cliente de embeddings Azure OpenAI."""
        logger.info(
            "Inicializando embeddings Azure OpenAI: deployment=%s, dim=%d",
            self._settings.azure_openai_embedding_deployment,
            self._settings.azure_openai_embedding_dimension,
        )
        return AzureOpenAIEmbeddings(
            azure_deployment=self._settings.azure_openai_embedding_deployment,
            azure_endpoint=self._settings.azure_openai_endpoint,
            api_key=self._settings.azure_openai_key,
            api_version=self._settings.azure_openai_api_version,
            dimensions=self._settings.azure_openai_embedding_dimension,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Vectoriza una lista de textos para indexación.

        Args:
            texts: Lista de textos a vectorizar.

        Returns:
            Lista de vectores de embeddings (float lists).
        """
        logger.debug("Generando embeddings para %d documentos", len(texts))
        return self.embeddings.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        """
        Vectoriza un query de búsqueda.

        Args:
            query: Texto del query.

        Returns:
            Vector de embeddings del query.
        """
        return self.embeddings.embed_query(query)

    def get_embeddings_for_langchain(self) -> AzureOpenAIEmbeddings:
        """
        Retorna el cliente de embeddings para usar directamente con LangChain.
        (p.ej. para FAISS.from_documents())

        Returns:
            Instancia de AzureOpenAIEmbeddings.
        """
        return self.embeddings
