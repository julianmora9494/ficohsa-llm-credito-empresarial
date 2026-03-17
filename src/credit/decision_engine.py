"""
Motor de decisión crediticia.
Genera un dictamen razonado: Aprobar / Aprobar con condiciones / Rechazar.
Basado exclusivamente en el contexto recuperado y los indicadores financieros.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from src.config.prompts.system import GROUNDING_RULES, SYSTEM_PROMPT_CREDIT_ANALYST
from src.credit.financial_analyzer import FinancialProfile
from src.llm.llm_manager import LLMManager
from src.retrieval.retriever import CombinedContext
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class CreditDecision(str, Enum):
    """Posibles dictámenes del análisis crediticio."""

    APROBAR = "APROBAR"
    APROBAR_CON_CONDICIONES = "APROBAR CON CONDICIONES"
    RECHAZAR = "RECHAZAR"
    INSUFICIENTE_INFORMACION = "INFORMACIÓN INSUFICIENTE"


@dataclass
class CreditAnalysisResult:
    """Resultado completo del análisis crediticio."""

    empresa: str
    decision: CreditDecision
    resumen_ejecutivo: str
    analisis_financiero: str
    contexto_sectorial: str
    seniales_riesgo: List[str]
    seniales_positivas: List[str]
    condiciones: List[str]        # Solo si decision = APROBAR_CON_CONDICIONES
    justificacion: str
    fuentes_consultadas: List[str]
    confianza: str                # alta / media / baja
    disclaimer: str = field(
        default=(
            "Este dictamen es una recomendación de apoyo al oficial de crédito "
            "y no constituye una decisión final del banco."
        )
    )


CREDIT_ANALYSIS_PROMPT = """{system_prompt}

{grounding_rules}

---

## DATOS DE LA EMPRESA A EVALUAR
**Empresa**: {empresa}
**Sector**: {sector}
**País**: {pais}
**Año de análisis**: {anio}

## INDICADORES FINANCIEROS
{financial_summary}

## CONTEXTO RECUPERADO
{retrieved_context}

---

## TAREA
Con base en la información anterior, realiza un análisis crediticio completo y entrega:

1. **Resumen ejecutivo** (máximo 3 líneas)
2. **Análisis financiero** (comenta los indicadores clave)
3. **Contexto sectorial** (situación del sector según los documentos recuperados)
4. **Señales de riesgo** (lista)
5. **Señales positivas / capacidad de pago** (lista)
6. **Dictamen** (APROBAR / APROBAR CON CONDICIONES / RECHAZAR / INFORMACIÓN INSUFICIENTE)
7. **Condiciones** (si aplica, lista de condiciones para aprobación)
8. **Justificación del dictamen** (cita fuentes específicas)
9. **Nivel de confianza** (alta/media/baja) con explicación
10. **Fuentes consultadas** (nombres de documentos y secciones usadas)

Si no hay suficiente información para algún punto, indícalo explícitamente.
"""


class DecisionEngine:
    """
    Motor que genera el dictamen crediticio final usando el LLM con grounding.
    """

    def __init__(self, llm_manager: LLMManager) -> None:
        """
        Inicializa el motor de decisión.

        Args:
            llm_manager: Manager del LLM Azure OpenAI.
        """
        self._llm = llm_manager

    def analyze(
        self,
        empresa: str,
        sector: str,
        pais: str,
        anio: int,
        financial_profile: Optional[FinancialProfile],
        context: CombinedContext,
    ) -> CreditAnalysisResult:
        """
        Genera el análisis crediticio completo con dictamen razonado.

        Args:
            empresa: Nombre de la empresa a evaluar.
            sector: Sector económico de la empresa.
            pais: País de operación de la empresa.
            anio: Año del análisis.
            financial_profile: Perfil financiero con ratios calculados.
            context: Contexto recuperado de los índices RAG.

        Returns:
            CreditAnalysisResult con dictamen y justificación completa.
        """
        logger.info("Generando análisis crediticio para: %s (%s, %s)", empresa, sector, pais)

        # Preparar resumen de indicadores financieros
        financial_summary = "No se proporcionaron estados financieros estructurados."
        if financial_profile and financial_profile.ratios:
            from src.credit.financial_analyzer import FinancialAnalyzer
            analyzer = FinancialAnalyzer()
            financial_summary = analyzer.build_financial_summary(financial_profile.ratios)

        # Construir el prompt completo
        prompt = CREDIT_ANALYSIS_PROMPT.format(
            system_prompt=SYSTEM_PROMPT_CREDIT_ANALYST,
            grounding_rules=GROUNDING_RULES,
            empresa=empresa,
            sector=sector,
            pais=pais,
            anio=anio,
            financial_summary=financial_summary,
            retrieved_context=context.format_for_prompt(),
        )

        logger.debug("Prompt de análisis: %d caracteres", len(prompt))
        raw_response = self._llm.invoke(prompt)

        # Detectar decisión desde la respuesta del LLM
        decision = self._extract_decision(raw_response)

        # Extraer fuentes consultadas del contexto
        sources = list({r.file_name for r in context.all_results if r.file_name})

        logger.info("Análisis completado para %s: dictamen=%s", empresa, decision.value)

        return CreditAnalysisResult(
            empresa=empresa,
            decision=decision,
            resumen_ejecutivo=self._extract_section(raw_response, "Resumen ejecutivo"),
            analisis_financiero=self._extract_section(raw_response, "Análisis financiero"),
            contexto_sectorial=self._extract_section(raw_response, "Contexto sectorial"),
            seniales_riesgo=self._extract_list_section(raw_response, "Señales de riesgo"),
            seniales_positivas=self._extract_list_section(raw_response, "Señales positivas"),
            condiciones=self._extract_list_section(raw_response, "Condiciones"),
            justificacion=self._extract_section(raw_response, "Justificación"),
            fuentes_consultadas=sources,
            confianza=self._extract_confianza(raw_response),
        )

    def _extract_decision(self, response: str) -> CreditDecision:
        """Extrae el dictamen del texto del LLM."""
        response_upper = response.upper()
        if "RECHAZAR" in response_upper:
            return CreditDecision.RECHAZAR
        elif "APROBAR CON CONDICIONES" in response_upper or "CON CONDICIONES" in response_upper:
            return CreditDecision.APROBAR_CON_CONDICIONES
        elif "APROBAR" in response_upper:
            return CreditDecision.APROBAR
        return CreditDecision.INSUFICIENTE_INFORMACION

    def _extract_section(self, response: str, section_name: str) -> str:
        """Extrae una sección específica de la respuesta del LLM."""
        # Búsqueda simple por palabras clave de sección
        lines = response.split("\n")
        capturing = False
        section_lines = []

        for line in lines:
            if section_name.lower() in line.lower() and ("**" in line or "#" in line):
                capturing = True
                continue
            if capturing:
                # Detener al encontrar la siguiente sección (## o **)
                if (line.startswith("#") or (line.startswith("**") and line.endswith("**"))) and section_lines:
                    break
                section_lines.append(line)

        return "\n".join(section_lines).strip() or "No disponible."

    def _extract_list_section(self, response: str, section_name: str) -> List[str]:
        """Extrae una sección de lista (bullets) de la respuesta."""
        section_text = self._extract_section(response, section_name)
        items = []
        for line in section_text.split("\n"):
            line = line.strip().lstrip("-").lstrip("•").lstrip("*").strip()
            if line:
                items.append(line)
        return items

    def _extract_confianza(self, response: str) -> str:
        """Extrae el nivel de confianza de la respuesta."""
        response_lower = response.lower()
        if "confianza alta" in response_lower or "alta confianza" in response_lower:
            return "alta"
        elif "confianza baja" in response_lower or "baja confianza" in response_lower:
            return "baja"
        return "media"
