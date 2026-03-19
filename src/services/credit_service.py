"""
Servicio de alto nivel para el análisis de crédito empresarial.
Interfaz simplificada para uso desde la UI o API.
"""
import tempfile
from pathlib import Path
from typing import Dict, Optional

from src.credit.decision_engine import CreditAnalysisResult, CreditDecision
from src.pipeline.rag_pipeline import CreditRAGPipeline
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class CreditService:
    """
    Servicio de análisis crediticio empresarial.
    Encapsula el pipeline RAG para uso desde interfaces externas.
    """

    def __init__(self) -> None:
        """Inicializa el servicio y el pipeline RAG."""
        self._pipeline = CreditRAGPipeline()
        self._initialized = False

    def initialize(self, load_existing_indexes: bool = True) -> Dict[str, bool]:
        """
        Inicializa el servicio cargando los índices FAISS.

        Args:
            load_existing_indexes: Si True, carga índices ya existentes en disco.

        Returns:
            Dict indicando qué índices están disponibles.
        """
        if self._initialized:
            return {"sector": True, "financial": True}

        status = {}
        if load_existing_indexes:
            status = self._pipeline.load_indexes()

        self._initialized = True
        logger.info("CreditService inicializado: índices=%s", status)
        return status

    def index_informes_gestion(self) -> Dict[str, int]:
        """
        Indexa todos los informes de gestión disponibles (HN, GT, NI).

        Returns:
            Dict con chunks indexados por país.
        """
        logger.info("Iniciando indexación de informes de gestión...")
        stats = self._pipeline.ingest_informes_gestion()
        logger.info("Indexación completada: %s", stats)
        return stats

    def index_estados_financieros(self, company_name: str) -> int:
        """
        Indexa los estados financieros de una empresa.

        Args:
            company_name: Nombre de la empresa (para filtrar archivos).

        Returns:
            Número de chunks indexados.
        """
        return self._pipeline.ingest_estados_financieros(company_name)

    def analizar_credito(
        self,
        empresa: str,
        sector: str,
        pais: str,
        anio: int,
        financial_data: Optional[Dict] = None,
        query_extra: Optional[str] = None,
        country_filter: Optional[str] = None,
    ) -> Dict:
        """
        Ejecuta el análisis crediticio completo y retorna resultado serializado.

        Args:
            empresa: Nombre de la empresa.
            sector: Sector económico.
            pais: País de operación.
            anio: Año del análisis.
            financial_data: Datos financieros estructurados (opcional).
            query_extra: Consulta adicional para retrieval.
            country_filter: Filtrar contexto sectorial por país.

        Returns:
            Dict con el resultado completo del análisis.
        """
        result: CreditAnalysisResult = self._pipeline.analyze_credit(
            empresa=empresa,
            sector=sector,
            pais=pais,
            anio=anio,
            financial_data=financial_data,
            query_extra=query_extra,
            country_filter=country_filter,
        )
        return self._serialize_result(result)

    def analizar_credito_desde_archivo(
        self,
        file_bytes: bytes,
        file_name: str,
        empresa: str,
        sector: str,
        pais: str,
        anio: int,
        country_filter: Optional[str] = None,
    ) -> Dict:
        """
        Analiza el crédito a partir de un archivo de estados financieros subido.
        El archivo se procesa en memoria sin persistirse en el índice FAISS.

        Args:
            file_bytes: Contenido binario del archivo subido.
            file_name: Nombre original del archivo (para determinar el formato).
            empresa: Nombre de la empresa.
            sector: Sector económico.
            pais: País de operación.
            anio: Año del análisis.
            country_filter: Filtrar contexto sectorial por país.

        Returns:
            Dict con el resultado completo del análisis.
        """
        suffix = Path(file_name).suffix.lower()

        # Guardar el archivo en un directorio temporal
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        try:
            result = self._pipeline.analyze_credit_from_file(
                file_path=tmp_path,
                empresa=empresa,
                sector=sector,
                pais=pais,
                anio=anio,
                country_filter=country_filter,
            )
            return self._serialize_result(result)
        finally:
            tmp_path.unlink(missing_ok=True)

    def _serialize_result(self, result: CreditAnalysisResult) -> Dict:
        """Convierte CreditAnalysisResult a dict serializable."""
        return {
            "empresa": result.empresa,
            "decision": result.decision.value,
            "decision_color": self._decision_color(result.decision),
            "resumen_ejecutivo": result.resumen_ejecutivo,
            "analisis_financiero": result.analisis_financiero,
            "contexto_sectorial": result.contexto_sectorial,
            "seniales_riesgo": result.seniales_riesgo,
            "seniales_positivas": result.seniales_positivas,
            "condiciones": result.condiciones,
            "justificacion": result.justificacion,
            "fuentes_consultadas": result.fuentes_consultadas,
            "confianza": result.confianza,
            "disclaimer": result.disclaimer,
        }

    def _decision_color(self, decision: CreditDecision) -> str:
        """Retorna un color semántico para la decisión (uso en UI)."""
        colors = {
            CreditDecision.APROBAR: "green",
            CreditDecision.APROBAR_CON_CONDICIONES: "orange",
            CreditDecision.RECHAZAR: "red",
            CreditDecision.INSUFICIENTE_INFORMACION: "gray",
        }
        return colors.get(decision, "gray")
