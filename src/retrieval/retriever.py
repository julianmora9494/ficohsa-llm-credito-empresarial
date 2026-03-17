"""
Recuperación de contexto desde los índices FAISS.
Realiza búsqueda en índice sectorial e índice financiero para combinar contexto.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from langchain.schema import Document

from src.config.settings import Settings, get_settings
from src.utils.logger import setup_logger
from src.vectorstore.vectorstore_manager import VectorStoreManager

logger = setup_logger(__name__)


@dataclass
class RetrievalResult:
    """Resultado de recuperación de un chunk del vectorstore."""

    chunk_id: str
    text: str
    score: float
    source_category: str
    file_name: str
    country: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


@dataclass
class CombinedContext:
    """Contexto combinado de búsqueda sectorial + financiero para el LLM."""

    sector_results: List[RetrievalResult]
    financial_results: List[RetrievalResult]
    query: str

    @property
    def all_results(self) -> List[RetrievalResult]:
        """Retorna todos los resultados ordenados por score descendente."""
        combined = self.sector_results + self.financial_results
        return sorted(combined, key=lambda r: r.score, reverse=True)

    def format_for_prompt(self) -> str:
        """
        Formatea el contexto recuperado para incluirlo en el prompt del LLM.
        Incluye secciones separadas para contexto sectorial y financiero.
        """
        sections = []

        if self.sector_results:
            sector_text = "\n\n---\n\n".join(
                f"[Fuente: {r.file_name} | País: {r.country} | Score: {r.score:.2f}]\n{r.text}"
                for r in self.sector_results
            )
            sections.append(f"## CONTEXTO SECTORIAL\n\n{sector_text}")

        if self.financial_results:
            financial_text = "\n\n---\n\n".join(
                f"[Fuente: {r.file_name} | Score: {r.score:.2f}]\n{r.text}"
                for r in self.financial_results
            )
            sections.append(f"## ESTADOS FINANCIEROS\n\n{financial_text}")

        return "\n\n" + "\n\n".join(sections) if sections else "Sin contexto disponible."


class Retriever:
    """
    Recupera contexto relevante de los índices sectoriales y financieros.
    """

    def __init__(
        self,
        vectorstore_manager: VectorStoreManager,
        settings: Optional[Settings] = None,
    ) -> None:
        """
        Inicializa el retriever.

        Args:
            vectorstore_manager: Manager de los índices FAISS.
            settings: Configuración del sistema.
        """
        self._vs_manager = vectorstore_manager
        self._settings = settings or get_settings()

    def retrieve(
        self,
        query: str,
        top_k_sector: Optional[int] = None,
        top_k_financial: Optional[int] = None,
        country_filter: Optional[str] = None,
    ) -> CombinedContext:
        """
        Recupera contexto combinado de ambos índices.

        Args:
            query: Pregunta o consulta del analista.
            top_k_sector: Número de resultados del índice sectorial.
            top_k_financial: Número de resultados del índice financiero.
            country_filter: Filtrar resultados sectoriales por país (opcional).

        Returns:
            CombinedContext con resultados de ambos índices.
        """
        top_k_sector = top_k_sector or self._settings.top_k_sector
        top_k_financial = top_k_financial or self._settings.top_k_financial

        logger.info(
            "Retrieving: query='%s...', sector_k=%d, financial_k=%d",
            query[:60], top_k_sector, top_k_financial,
        )

        # Búsqueda en índice sectorial
        sector_raw = self._vs_manager.similarity_search(
            query, index_name="sector", top_k=top_k_sector
        )
        sector_results = self._parse_results(sector_raw, country_filter)

        # Búsqueda en índice financiero
        financial_raw = self._vs_manager.similarity_search(
            query, index_name="financial", top_k=top_k_financial
        )
        financial_results = self._parse_results(financial_raw, country_filter=None)

        logger.info(
            "Retrieved: %d resultados sectoriales, %d financieros",
            len(sector_results), len(financial_results),
        )

        return CombinedContext(
            sector_results=sector_results,
            financial_results=financial_results,
            query=query,
        )

    def _parse_results(
        self,
        raw_results: List[Tuple[Document, float]],
        country_filter: Optional[str],
    ) -> List[RetrievalResult]:
        """Convierte resultados FAISS al formato RetrievalResult."""
        results = []
        for doc, score in raw_results:
            meta = doc.metadata
            country = meta.get("country", "desconocido")

            # Aplicar filtro de país si se especificó
            if country_filter and country != country_filter:
                continue

            results.append(
                RetrievalResult(
                    chunk_id=meta.get("chunk_id", ""),
                    text=doc.page_content,
                    score=score,
                    source_category=meta.get("source_category", ""),
                    file_name=meta.get("file_name", ""),
                    country=country,
                    chunk_index=meta.get("chunk_index", 0),
                    metadata=meta,
                )
            )
        return results
