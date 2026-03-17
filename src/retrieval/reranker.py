"""
Reranking de resultados de retrieval usando el LLM.
Prioriza los chunks más relevantes para el análisis crediticio específico.
"""
from typing import List, Optional

from src.llm.llm_manager import LLMManager
from src.retrieval.retriever import CombinedContext, RetrievalResult
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

RERANKER_PROMPT = """Eres un analista de crédito corporativo especializado.
Dada la siguiente consulta sobre análisis crediticio, ordena los fragmentos de contexto \
del más relevante al menos relevante.

CONSULTA: {query}

FRAGMENTOS DISPONIBLES:
{candidates}

Responde SOLO con los números de los fragmentos en orden de relevancia, separados por coma.
Ejemplo: 3,1,5,2,4
Solo incluye los {top_n} más relevantes.
"""


class Reranker:
    """
    Reordena los chunks recuperados usando el LLM para maximizar relevancia crediticia.
    """

    def __init__(
        self,
        llm_manager: LLMManager,
        top_n: int = 5,
    ) -> None:
        """
        Inicializa el reranker.

        Args:
            llm_manager: Manager del LLM Azure OpenAI.
            top_n: Número de resultados a retornar tras reranking.
        """
        self._llm = llm_manager
        self._top_n = top_n

    def rerank(
        self,
        context: CombinedContext,
        top_n: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """
        Reordena los resultados combinados por relevancia para la consulta.

        Args:
            context: Contexto combinado de búsqueda.
            top_n: Número de resultados a retornar. Usa self._top_n si es None.

        Returns:
            Lista reordenada de RetrievalResult (top_n más relevantes).
        """
        top_n = top_n or self._top_n
        all_results = context.all_results

        if not all_results:
            return []

        # Si hay pocos resultados, no rerankeamos para ahorrar tokens
        if len(all_results) <= top_n:
            logger.debug("Menos resultados que top_n, sin reranking necesario")
            return all_results[:top_n]

        logger.info(
            "Rerankando %d candidatos → top %d para query='%s...'",
            len(all_results), top_n, context.query[:50],
        )

        # Preparar candidatos numerados para el prompt
        candidates_text = "\n\n".join(
            f"[{i+1}] (Fuente: {r.file_name} | País: {r.country})\n{r.text[:400]}..."
            for i, r in enumerate(all_results)
        )

        prompt = RERANKER_PROMPT.format(
            query=context.query,
            candidates=candidates_text,
            top_n=top_n,
        )

        try:
            response = self._llm.invoke(prompt).strip()
            indices = [int(x.strip()) - 1 for x in response.split(",") if x.strip().isdigit()]
            # Filtrar índices válidos
            valid_indices = [i for i in indices if 0 <= i < len(all_results)]
            reranked = [all_results[i] for i in valid_indices[:top_n]]

            # Si el LLM no devolvió suficientes, complementar con los top originales
            if len(reranked) < top_n:
                remaining = [r for r in all_results if r not in reranked]
                reranked.extend(remaining[: top_n - len(reranked)])

            logger.info("Reranking completado: %d resultados seleccionados", len(reranked))
            return reranked

        except Exception as e:
            logger.warning("Error en reranking LLM: %s. Usando orden original.", str(e))
            return all_results[:top_n]
