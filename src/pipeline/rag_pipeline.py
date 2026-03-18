"""
Orquestador principal del pipeline RAG de análisis crediticio.
Coordina ingestión, indexación, retrieval, reranking y análisis.
"""
from pathlib import Path
from typing import Dict, List, Optional

from src.config.settings import Settings, get_settings
from src.credit.decision_engine import CreditAnalysisResult, DecisionEngine
from src.credit.financial_analyzer import FinancialAnalyzer, FinancialProfile
from src.embeddings.embeddings_manager import EmbeddingsManager
from src.ingestion.chunker import DocumentChunker
from src.ingestion.document_loader import DocumentLoader, SourceCategory
from src.llm.llm_manager import LLMManager
from src.retrieval.retriever import CombinedContext, Retriever
from src.retrieval.reranker import Reranker
from src.utils.logger import setup_logger
from src.vectorstore.vectorstore_manager import VectorStoreManager

logger = setup_logger(__name__)


class CreditRAGPipeline:
    """
    Pipeline completo para análisis crediticio empresarial con RAG.

    Flujo:
    1. Ingestión y chunking de documentos
    2. Indexación en FAISS (sector + financial)
    3. Retrieval combinado para una consulta
    4. Reranking con LLM
    5. Análisis crediticio + dictamen
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """
        Inicializa todos los componentes del pipeline.

        Args:
            settings: Configuración del sistema. Si es None, usa el singleton global.
        """
        self._settings = settings or get_settings()

        # Componentes de infraestructura
        self.llm_manager = LLMManager(settings=self._settings)
        self.embeddings_manager = EmbeddingsManager(settings=self._settings)
        self.vectorstore_manager = VectorStoreManager(
            embeddings_manager=self.embeddings_manager,
            settings=self._settings,
        )

        # Componentes de ingestión
        self.document_loader = DocumentLoader()
        self.chunker = DocumentChunker(settings=self._settings)

        # Componentes de retrieval
        self.retriever = Retriever(
            vectorstore_manager=self.vectorstore_manager,
            settings=self._settings,
        )
        self.reranker = Reranker(
            llm_manager=self.llm_manager,
            top_n=self._settings.reranker_top_n,
        )

        # Componentes de análisis
        self.financial_analyzer = FinancialAnalyzer()
        self.decision_engine = DecisionEngine(llm_manager=self.llm_manager)

        logger.info("CreditRAGPipeline inicializado correctamente")

    def ingest_informes_gestion(self) -> Dict[str, int]:
        """
        Ingesta todos los informes de gestión de Honduras, Guatemala y Nicaragua.
        Los indexa en el índice sectorial (sector_index).

        Returns:
            Dict con cantidad de chunks indexados por país.
        """
        countries = ["honduras", "guatemala", "nicaragua"]
        stats: Dict[str, int] = {}

        for country in countries:
            country_path = self._settings.informes_gestion_path / country
            if not country_path.exists():
                logger.warning("Directorio no encontrado: %s", country_path)
                stats[country] = 0
                continue

            documents = self.document_loader.load_directory(
                directory=country_path,
                source_category=SourceCategory.INFORME_GESTION,
                country=country,
            )

            if not documents:
                logger.info("Sin documentos en %s", country_path)
                stats[country] = 0
                continue

            chunks = self.chunker.chunk_documents(documents)
            self.vectorstore_manager.add_chunks(chunks, index_name="sector")
            stats[country] = len(chunks)
            logger.info("País %s: %d chunks indexados", country, len(chunks))

        return stats

    def ingest_estados_financieros(self, company_name: str) -> int:
        """
        Ingesta estados financieros de una empresa específica.
        Busca recursivamente en data/raw/estados_financieros/ la carpeta
        cuyo nombre coincida con company_name (ej. 'alutech_sa').
        Los indexa en el índice financiero (financial_index).

        Args:
            company_name: Nombre del directorio de la empresa (ej. 'alutech_sa').

        Returns:
            Número de chunks indexados.
        """
        base_path = self._settings.estados_financieros_path

        # Buscar el directorio de la empresa recursivamente (puede estar bajo [pais]/[empresa])
        company_dir: Optional[Path] = None
        for candidate in base_path.rglob(company_name):
            if candidate.is_dir():
                company_dir = candidate
                break

        if company_dir is None:
            # Fallback: buscar por nombre parcial en subdirectorios
            for candidate in base_path.rglob("*"):
                if candidate.is_dir() and company_name.lower() in candidate.name.lower():
                    company_dir = candidate
                    break

        if company_dir is None:
            logger.warning(
                "No se encontro directorio para la empresa '%s' en %s",
                company_name, base_path,
            )
            return 0

        # Determinar el país a partir del directorio padre
        country = company_dir.parent.name if company_dir.parent != base_path else None
        logger.info("Cargando documentos de %s desde %s", company_name, company_dir)

        documents = self.document_loader.load_directory(
            directory=company_dir,
            source_category=SourceCategory.ESTADO_FINANCIERO,
            country=country,
        )

        if not documents:
            logger.warning("No se encontraron documentos para %s en %s", company_name, company_dir)
            return 0

        chunks = self.chunker.chunk_documents(documents)
        self.vectorstore_manager.add_chunks(chunks, index_name="financial")
        logger.info("Estados financieros de %s: %d chunks indexados", company_name, len(chunks))
        return len(chunks)

    def load_indexes(self) -> Dict[str, bool]:
        """
        Carga los índices FAISS desde disco.

        Returns:
            Dict indicando qué índices se cargaron exitosamente.
        """
        return self.vectorstore_manager.load_stores()

    def analyze_credit(
        self,
        empresa: str,
        sector: str,
        pais: str,
        anio: int,
        financial_data: Optional[Dict] = None,
        query_extra: Optional[str] = None,
        country_filter: Optional[str] = None,
    ) -> CreditAnalysisResult:
        """
        Ejecuta el análisis crediticio completo para una empresa.

        Args:
            empresa: Nombre de la empresa a analizar.
            sector: Sector económico (agrícola, comercio, industria, servicios, etc.).
            pais: País de operación.
            anio: Año del análisis.
            financial_data: Dict con datos financieros estructurados (opcional).
                            Claves: activo_corriente, pasivo_corriente, total_activos,
                                   total_pasivos, patrimonio, utilidad_neta, ventas_netas,
                                   ebit, gastos_financieros.
            query_extra: Consulta adicional para enriquecer el retrieval.
            country_filter: Filtrar contexto sectorial por país específico.

        Returns:
            CreditAnalysisResult con dictamen completo.
        """
        logger.info("Iniciando análisis crediticio: empresa=%s, sector=%s", empresa, sector)

        # Construir query de retrieval
        query = (
            f"análisis crediticio empresa {sector} {pais} situación financiera "
            f"riesgo capacidad pago {empresa}"
        )
        if query_extra:
            query += f" {query_extra}"

        # Retrieval: buscar en ambos índices
        context: CombinedContext = self.retriever.retrieve(
            query=query,
            country_filter=country_filter,
        )

        # Reranking con LLM
        reranked_results = self.reranker.rerank(context)
        # Actualizar el contexto con los resultados rerankeados
        sector_reranked = [r for r in reranked_results if r.source_category == "informe_gestion"]
        financial_reranked = [r for r in reranked_results if r.source_category == "estado_financiero"]

        from src.retrieval.retriever import CombinedContext
        final_context = CombinedContext(
            sector_results=sector_reranked or context.sector_results,
            financial_results=financial_reranked or context.financial_results,
            query=query,
        )

        # Calcular ratios financieros si se proporcionaron datos
        financial_profile: Optional[FinancialProfile] = None
        if financial_data:
            ratios = self.financial_analyzer.calculate_ratios(**financial_data)
            financial_profile = FinancialProfile(
                empresa=empresa,
                sector=sector,
                pais=pais,
                anio=anio,
                ratios=ratios,
            )

        # Generar dictamen con el motor de decisión
        result = self.decision_engine.analyze(
            empresa=empresa,
            sector=sector,
            pais=pais,
            anio=anio,
            financial_profile=financial_profile,
            context=final_context,
        )

        return result

    def analyze_credit_from_file(
        self,
        file_path: Path,
        empresa: str,
        sector: str,
        pais: str,
        anio: int,
        country_filter: Optional[str] = None,
    ) -> CreditAnalysisResult:
        """
        Análisis crediticio a partir de un archivo subido directamente.
        El documento subido se usa como contexto financiero sin pasar por FAISS.
        El contexto sectorial sigue recuperándose del índice sector_index.

        Args:
            file_path: Ruta al archivo de estados financieros (PDF, DOCX, XLSX, TXT).
            empresa: Nombre de la empresa a analizar.
            sector: Sector económico.
            pais: País de operación.
            anio: Año del análisis.
            country_filter: Filtrar contexto sectorial por país.

        Returns:
            CreditAnalysisResult con dictamen completo.
        """
        logger.info(
            "Analizando credito desde archivo: %s para empresa=%s, sector=%s",
            file_path.name, empresa, sector,
        )

        # Cargar y chunkear el documento subido
        doc = self.document_loader.load_file(
            file_path=file_path,
            source_category=SourceCategory.ESTADO_FINANCIERO,
            country=country_filter,
        )

        if doc is None:
            logger.error("No se pudo cargar el archivo: %s", file_path)
            from src.retrieval.retriever import CombinedContext, RetrievalResult
            empty_context = CombinedContext(sector_results=[], financial_results=[], query="")
            return self.decision_engine.analyze(
                empresa=empresa, sector=sector, pais=pais, anio=anio,
                financial_profile=None, context=empty_context,
            )

        chunks = self.chunker.chunk_documents([doc])
        logger.info("Documento cargado: %d chunks extraidos de %s", len(chunks), file_path.name)

        # Convertir chunks del documento a RetrievalResult (sin búsqueda vectorial)
        from src.retrieval.retriever import CombinedContext, RetrievalResult
        financial_results = [
            RetrievalResult(
                chunk_id=f"upload_{i}",
                text=chunk.text,
                score=1.0,
                source_category="estado_financiero",
                file_name=file_path.name,
                country=country_filter or pais.lower(),
                chunk_index=i,
                metadata=chunk.metadata,
            )
            for i, chunk in enumerate(chunks)
        ]

        # Recuperar contexto sectorial del índice FAISS
        query = (
            f"análisis crediticio empresa {sector} {pais} situación financiera "
            f"riesgo capacidad pago {empresa}"
        )
        sector_context = self.retriever.retrieve(
            query=query,
            top_k_sector=self._settings.top_k_sector,
            top_k_financial=0,
            country_filter=country_filter,
        )

        # Aplicar reranking solo al contexto sectorial
        reranked = self.reranker.rerank(sector_context)
        sector_reranked = [r for r in reranked if r.source_category == "informe_gestion"]

        final_context = CombinedContext(
            sector_results=sector_reranked or sector_context.sector_results,
            financial_results=financial_results,
            query=query,
        )

        # Generar dictamen sin financial_profile (el LLM extrae cifras del texto)
        result = self.decision_engine.analyze(
            empresa=empresa,
            sector=sector,
            pais=pais,
            anio=anio,
            financial_profile=None,
            context=final_context,
        )

        return result

    def qa_sectorial(self, query: str, country_filter: Optional[str] = None) -> str:
        """
        Responde preguntas sobre el contexto sectorial usando los informes de gestión.

        Args:
            query: Pregunta sobre el sector o economía.
            country_filter: Filtrar por país específico.

        Returns:
            Respuesta generada por el LLM con contexto recuperado.
        """
        from src.config.prompts.system import GROUNDING_RULES, SYSTEM_PROMPT_QA_SECTORIAL

        context = self.retriever.retrieve(
            query=query,
            top_k_sector=self._settings.top_k_sector,
            top_k_financial=0,
            country_filter=country_filter,
        )

        prompt = f"""{SYSTEM_PROMPT_QA_SECTORIAL}

{GROUNDING_RULES}

## CONSULTA
{query}

## CONTEXTO RECUPERADO
{context.format_for_prompt()}

## RESPUESTA
"""
        return self._llm_invoke(prompt)

    def _llm_invoke(self, prompt: str) -> str:
        """Invoca el LLM con un prompt."""
        return self.llm_manager.invoke(prompt)
