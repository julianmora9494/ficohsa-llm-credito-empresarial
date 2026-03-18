"""
Gestión de índices FAISS para búsqueda vectorial.
Mantiene índices separados para documentos sectoriales y estados financieros.
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from langchain.schema import Document
from langchain_community.vectorstores import FAISS

from src.config.settings import Settings, get_settings
from src.embeddings.embeddings_manager import EmbeddingsManager
from src.ingestion.chunker import DocumentChunk
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class VectorStoreManager:
    """
    Gestiona índices FAISS separados para:
    - sector_index: Informes de gestión (contexto sectorial)
    - financial_index: Estados financieros de empresas
    """

    def __init__(
        self,
        embeddings_manager: EmbeddingsManager,
        settings: Optional[Settings] = None,
    ) -> None:
        """
        Inicializa el manager de vectorstores.

        Args:
            embeddings_manager: Manager de embeddings para vectorización.
            settings: Configuración del sistema.
        """
        self._settings = settings or get_settings()
        self._embeddings_manager = embeddings_manager
        self._sector_store: Optional[FAISS] = None
        self._financial_store: Optional[FAISS] = None
        logger.info("VectorStoreManager inicializado")

    @property
    def sector_store_path(self) -> Path:
        """Ruta del índice FAISS sectorial."""
        return self._settings.vector_store_path / self._settings.sector_index_name

    @property
    def financial_store_path(self) -> Path:
        """Ruta del índice FAISS de estados financieros."""
        return self._settings.vector_store_path / self._settings.financial_index_name

    def add_chunks(
        self, chunks: List[DocumentChunk], index_name: str
    ) -> None:
        """
        Vectoriza e indexa una lista de chunks en el índice especificado.

        Args:
            chunks: Lista de chunks a indexar.
            index_name: Nombre del índice ('sector' o 'financial').
        """
        if not chunks:
            logger.warning("No hay chunks para indexar en %s", index_name)
            return

        logger.info("Indexando %d chunks en %s...", len(chunks), index_name)

        embeddings = self._embeddings_manager.get_embeddings_for_langchain()
        store: Optional[FAISS] = None

        # Procesar en lotes para respetar el rate limit del tier S0 de Azure OpenAI.
        # S0 permite ~60 req/min para embeddings; lotes de 50 chunks con pausa entre ellos.
        BATCH_SIZE = 50
        BATCH_PAUSE_SECONDS = 12  # pausa entre lotes para evitar 429

        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i: i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            logger.info(
                "Vectorizando lote %d/%d (%d chunks)...",
                batch_num, total_batches, len(batch),
            )
            documents = [
                Document(page_content=c.text, metadata=c.metadata) for c in batch
            ]

            # Reintento con backoff ante rate limit (429)
            for attempt in range(3):
                try:
                    batch_store = FAISS.from_documents(documents, embeddings)
                    break
                except Exception as e:
                    if "429" in str(e) or "RateLimit" in str(e):
                        wait = 65 * (attempt + 1)
                        logger.warning(
                            "Rate limit en lote %d, esperando %ds (intento %d/3)...",
                            batch_num, wait, attempt + 1,
                        )
                        time.sleep(wait)
                    else:
                        raise

            if store is None:
                store = batch_store
            else:
                store.merge_from(batch_store)

            # Pausa entre lotes (excepto el ultimo)
            if i + BATCH_SIZE < len(chunks):
                time.sleep(BATCH_PAUSE_SECONDS)

        if store is None:
            logger.error("No se generaron vectores para indexar en %s", index_name)
            return

        if index_name == "sector":
            if self._sector_store is not None:
                self._sector_store.merge_from(store)
            else:
                self._sector_store = store
            self._save_store(self._sector_store, self.sector_store_path)
        elif index_name == "financial":
            if self._financial_store is not None:
                self._financial_store.merge_from(store)
            else:
                self._financial_store = store
            self._save_store(self._financial_store, self.financial_store_path)
        else:
            raise ValueError(f"Indice desconocido: {index_name}. Usar 'sector' o 'financial'.")

        logger.info("Indexacion completada: %d documentos en %s", len(chunks), index_name)

    def similarity_search(
        self,
        query: str,
        index_name: str,
        top_k: int = 5,
    ) -> List[Tuple[Document, float]]:
        """
        Búsqueda por similitud semántica en un índice.

        Args:
            query: Texto de consulta.
            index_name: Índice a consultar ('sector' o 'financial').
            top_k: Número de resultados a retornar.

        Returns:
            Lista de tuplas (Document, score) ordenadas por relevancia.
        """
        store = self._get_store(index_name)
        if store is None:
            logger.warning("Índice %s no cargado o vacío", index_name)
            return []

        results = store.similarity_search_with_relevance_scores(query, k=top_k)
        logger.debug(
            "Búsqueda en %s: query='%s...', top_%d resultados",
            index_name, query[:50], top_k,
        )
        return results

    def load_stores(self) -> Dict[str, bool]:
        """
        Carga los índices FAISS desde disco si existen.

        Returns:
            Dict indicando qué índices se cargaron exitosamente.
        """
        status = {"sector": False, "financial": False}
        embeddings = self._embeddings_manager.get_embeddings_for_langchain()

        if self.sector_store_path.exists():
            self._sector_store = FAISS.load_local(
                str(self.sector_store_path),
                embeddings,
                allow_dangerous_deserialization=True,
            )
            status["sector"] = True
            logger.info("Índice sectorial cargado desde %s", self.sector_store_path)

        if self.financial_store_path.exists():
            self._financial_store = FAISS.load_local(
                str(self.financial_store_path),
                embeddings,
                allow_dangerous_deserialization=True,
            )
            status["financial"] = True
            logger.info("Índice financiero cargado desde %s", self.financial_store_path)

        return status

    def _get_store(self, index_name: str) -> Optional[FAISS]:
        """Retorna el store correspondiente al nombre del índice."""
        if index_name == "sector":
            return self._sector_store
        elif index_name == "financial":
            return self._financial_store
        raise ValueError(f"Índice desconocido: {index_name}")

    def _save_store(self, store: FAISS, path: Path) -> None:
        """Guarda un índice FAISS en disco."""
        path.mkdir(parents=True, exist_ok=True)
        store.save_local(str(path))
        logger.info("Índice guardado en %s", path)
