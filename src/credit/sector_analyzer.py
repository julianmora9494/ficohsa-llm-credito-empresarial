"""
Análisis del contexto sectorial usando el contexto recuperado de los informes de gestión.
Identifica señales del sector relevantes para la evaluación crediticia.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from src.retrieval.retriever import RetrievalResult
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Sectores económicos reconocidos por el sistema
SECTORES_CONOCIDOS = [
    "agrícola", "agricultura", "café", "palma africana", "granos básicos",
    "comercio", "retail", "distribución",
    "industria", "manufactura", "procesamiento",
    "servicios", "transporte", "logística",
    "construcción", "inmobiliario",
    "financiero", "banca",
    "turismo", "hospitalidad",
]

# Palabras clave que indican riesgo sectorial
PALABRAS_RIESGO_SECTORIAL = [
    "contracción", "caída", "disminución", "baja", "reducción",
    "crisis", "desaceleración", "deterioro", "incertidumbre",
    "sequía", "fenómeno climático", "desempleo", "inflación",
]

# Palabras clave que indican oportunidad sectorial
PALABRAS_OPORTUNIDAD_SECTORIAL = [
    "crecimiento", "expansión", "aumento", "mejora", "dinamismo",
    "recuperación", "fortalecimiento", "oportunidad", "demanda",
    "exportación", "inversión", "estabilidad",
]


@dataclass
class SectorSignal:
    """Señal identificada en el contexto sectorial."""

    text: str
    type: str   # "riesgo" o "oportunidad"
    source: str
    country: str


@dataclass
class SectorContext:
    """Contexto sectorial consolidado para el análisis crediticio."""

    sector: str
    countries_covered: List[str]
    signals: List[SectorSignal] = field(default_factory=list)
    summary: str = ""

    @property
    def risk_signals(self) -> List[SectorSignal]:
        """Solo las señales de riesgo."""
        return [s for s in self.signals if s.type == "riesgo"]

    @property
    def opportunity_signals(self) -> List[SectorSignal]:
        """Solo las señales de oportunidad."""
        return [s for s in self.signals if s.type == "oportunidad"]

    @property
    def sector_outlook(self) -> str:
        """
        Evaluación rápida del panorama sectorial.
        Retorna: 'favorable', 'neutro', 'desfavorable'.
        """
        n_risk = len(self.risk_signals)
        n_opp = len(self.opportunity_signals)
        if n_risk > n_opp * 2:
            return "desfavorable"
        elif n_opp > n_risk * 2:
            return "favorable"
        return "neutro"


class SectorAnalyzer:
    """
    Analiza el contexto sectorial a partir de los chunks recuperados.
    Detecta señales de riesgo y oportunidad por sector y país.
    """

    def analyze(
        self,
        sector: str,
        sector_results: List[RetrievalResult],
    ) -> SectorContext:
        """
        Analiza los resultados sectoriales recuperados para identificar señales.

        Args:
            sector: Sector económico de la empresa a evaluar.
            sector_results: Chunks recuperados del índice sectorial.

        Returns:
            SectorContext con señales identificadas y panorama sectorial.
        """
        if not sector_results:
            logger.warning("Sin resultados sectoriales para analizar")
            return SectorContext(
                sector=sector,
                countries_covered=[],
                summary="No se encontró información sectorial en los documentos disponibles.",
            )

        signals: List[SectorSignal] = []
        countries = list({r.country for r in sector_results if r.country})

        for result in sector_results:
            text_lower = result.text.lower()

            # Detectar si el chunk menciona el sector relevante
            sector_relevante = any(
                s in text_lower for s in [sector.lower()] + self._get_sector_aliases(sector)
            )

            if not sector_relevante and result.score < 0.7:
                continue

            # Identificar señales de riesgo
            for keyword in PALABRAS_RIESGO_SECTORIAL:
                if keyword in text_lower:
                    signals.append(SectorSignal(
                        text=self._extract_sentence_with_keyword(result.text, keyword),
                        type="riesgo",
                        source=result.file_name,
                        country=result.country,
                    ))
                    break

            # Identificar señales de oportunidad
            for keyword in PALABRAS_OPORTUNIDAD_SECTORIAL:
                if keyword in text_lower:
                    signals.append(SectorSignal(
                        text=self._extract_sentence_with_keyword(result.text, keyword),
                        type="oportunidad",
                        source=result.file_name,
                        country=result.country,
                    ))
                    break

        context = SectorContext(
            sector=sector,
            countries_covered=countries,
            signals=signals[:10],  # Limitar a 10 señales más relevantes
        )

        context.summary = self._build_summary(context)
        logger.info(
            "Sector %s: %d señales (%d riesgo, %d oportunidad), outlook=%s",
            sector,
            len(signals),
            len(context.risk_signals),
            len(context.opportunity_signals),
            context.sector_outlook,
        )
        return context

    def _get_sector_aliases(self, sector: str) -> List[str]:
        """Retorna aliases del sector para búsqueda en texto."""
        aliases = {
            "agrícola": ["agricultura", "campo", "agro", "café", "palma"],
            "comercio": ["comercial", "retail", "tienda", "distribución"],
            "industria": ["industrial", "manufactura", "fábrica", "procesamiento"],
            "servicios": ["servicio", "logística", "transporte"],
            "construcción": ["constructora", "inmobiliario", "obras"],
        }
        return aliases.get(sector.lower(), [])

    def _extract_sentence_with_keyword(self, text: str, keyword: str) -> str:
        """Extrae la oración que contiene una palabra clave."""
        sentences = text.split(".")
        for sentence in sentences:
            if keyword.lower() in sentence.lower():
                return sentence.strip()[:300]
        return text[:200]

    def _build_summary(self, context: SectorContext) -> str:
        """Genera un resumen textual del análisis sectorial."""
        parts = [
            f"Sector {context.sector} — Panorama: {context.sector_outlook.upper()}.",
            f"Países cubiertos: {', '.join(context.countries_covered) or 'No especificado'}.",
            f"Señales de riesgo identificadas: {len(context.risk_signals)}.",
            f"Señales de oportunidad: {len(context.opportunity_signals)}.",
        ]
        return " ".join(parts)
