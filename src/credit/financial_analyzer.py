"""
Análisis de indicadores financieros de una empresa solicitante de crédito.
Calcula ratios clave y detecta señales de alerta según estándares bancarios.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class AlertLevel(str, Enum):
    """Nivel de alerta de un indicador financiero."""

    OK = "ok"
    ADVERTENCIA = "advertencia"
    CRITICO = "critico"


@dataclass
class FinancialRatio:
    """Representa un ratio financiero calculado con su interpretación."""

    name: str
    value: Optional[float]
    benchmark_min: Optional[float]
    benchmark_max: Optional[float]
    alert_level: AlertLevel
    interpretation: str


@dataclass
class FinancialProfile:
    """Perfil financiero completo de una empresa analizada."""

    empresa: str
    sector: str
    pais: str
    anio: int
    ratios: List[FinancialRatio] = field(default_factory=list)
    seniales_riesgo: List[str] = field(default_factory=list)
    seniales_positivas: List[str] = field(default_factory=list)
    observaciones: List[str] = field(default_factory=list)

    @property
    def tiene_alertas_criticas(self) -> bool:
        """Indica si hay al menos un ratio con nivel CRITICO."""
        return any(r.alert_level == AlertLevel.CRITICO for r in self.ratios)


class FinancialAnalyzer:
    """
    Analiza indicadores financieros para evaluación crediticia empresarial.
    Proporciona ratios, benchmarks y señales de alerta.
    """

    # Benchmarks sectoriales por defecto (Centroamérica)
    # En producción estos valores deberían venir de la base de conocimiento sectorial
    DEFAULT_BENCHMARKS: Dict[str, Dict[str, float]] = {
        "liquidez_corriente": {"min": 1.0, "max": 3.0},
        "endeudamiento": {"min": 0.0, "max": 0.70},
        "margen_utilidad_neta": {"min": 0.03, "max": 0.30},
        "roe": {"min": 0.08, "max": 0.35},
        "cobertura_intereses": {"min": 1.5, "max": 10.0},
    }

    def calculate_ratios(
        self,
        activo_corriente: Optional[float] = None,
        pasivo_corriente: Optional[float] = None,
        total_activos: Optional[float] = None,
        total_pasivos: Optional[float] = None,
        patrimonio: Optional[float] = None,
        utilidad_neta: Optional[float] = None,
        ventas_netas: Optional[float] = None,
        ebit: Optional[float] = None,
        gastos_financieros: Optional[float] = None,
    ) -> List[FinancialRatio]:
        """
        Calcula los ratios financieros clave para análisis de crédito.

        Args:
            activo_corriente: Activos circulantes/corrientes.
            pasivo_corriente: Pasivos circulantes/corrientes.
            total_activos: Total de activos.
            total_pasivos: Total de pasivos.
            patrimonio: Patrimonio neto.
            utilidad_neta: Utilidad/beneficio neto.
            ventas_netas: Ventas netas o ingresos totales.
            ebit: Ganancias antes de intereses e impuestos.
            gastos_financieros: Gastos por intereses financieros.

        Returns:
            Lista de FinancialRatio calculados e interpretados.
        """
        ratios = []

        # 1. Liquidez corriente
        if activo_corriente is not None and pasivo_corriente and pasivo_corriente > 0:
            valor = activo_corriente / pasivo_corriente
            bench = self.DEFAULT_BENCHMARKS["liquidez_corriente"]
            ratios.append(FinancialRatio(
                name="Liquidez Corriente",
                value=round(valor, 2),
                benchmark_min=bench["min"],
                benchmark_max=bench["max"],
                alert_level=self._classify_alert(valor, bench["min"], bench["max"], inverse=False),
                interpretation=self._interpret_liquidez(valor),
            ))

        # 2. Endeudamiento sobre activos
        if total_pasivos is not None and total_activos and total_activos > 0:
            valor = total_pasivos / total_activos
            bench = self.DEFAULT_BENCHMARKS["endeudamiento"]
            ratios.append(FinancialRatio(
                name="Ratio de Endeudamiento",
                value=round(valor, 3),
                benchmark_min=bench["min"],
                benchmark_max=bench["max"],
                alert_level=self._classify_alert(valor, bench["min"], bench["max"], inverse=True),
                interpretation=self._interpret_endeudamiento(valor),
            ))

        # 3. Margen de utilidad neta
        if utilidad_neta is not None and ventas_netas and ventas_netas > 0:
            valor = utilidad_neta / ventas_netas
            bench = self.DEFAULT_BENCHMARKS["margen_utilidad_neta"]
            ratios.append(FinancialRatio(
                name="Margen Utilidad Neta",
                value=round(valor, 3),
                benchmark_min=bench["min"],
                benchmark_max=bench["max"],
                alert_level=self._classify_alert(valor, bench["min"], bench["max"], inverse=False),
                interpretation=f"La empresa genera {valor*100:.1f}% de utilidad por cada lempira vendido.",
            ))

        # 4. ROE (Retorno sobre Patrimonio)
        if utilidad_neta is not None and patrimonio and patrimonio > 0:
            valor = utilidad_neta / patrimonio
            bench = self.DEFAULT_BENCHMARKS["roe"]
            ratios.append(FinancialRatio(
                name="ROE",
                value=round(valor, 3),
                benchmark_min=bench["min"],
                benchmark_max=bench["max"],
                alert_level=self._classify_alert(valor, bench["min"], bench["max"], inverse=False),
                interpretation=f"Retorno sobre patrimonio: {valor*100:.1f}%.",
            ))

        # 5. Cobertura de intereses
        if ebit is not None and gastos_financieros and gastos_financieros > 0:
            valor = ebit / gastos_financieros
            bench = self.DEFAULT_BENCHMARKS["cobertura_intereses"]
            ratios.append(FinancialRatio(
                name="Cobertura de Intereses",
                value=round(valor, 2),
                benchmark_min=bench["min"],
                benchmark_max=bench["max"],
                alert_level=self._classify_alert(valor, bench["min"], bench["max"], inverse=False),
                interpretation=self._interpret_cobertura(valor),
            ))

        return ratios

    def build_financial_summary(self, ratios: List[FinancialRatio]) -> str:
        """
        Genera un resumen textual de los indicadores para incluir en el prompt del LLM.

        Args:
            ratios: Lista de ratios calculados.

        Returns:
            Texto formateado con los indicadores y alertas.
        """
        lines = ["## Indicadores Financieros Calculados\n"]
        for r in ratios:
            icon = {"ok": "✓", "advertencia": "⚠", "critico": "✗"}.get(r.alert_level.value, "")
            lines.append(
                f"- **{r.name}**: {r.value} {icon}  \n"
                f"  Benchmark: [{r.benchmark_min} – {r.benchmark_max}]  \n"
                f"  {r.interpretation}"
            )
        return "\n".join(lines)

    def _classify_alert(
        self,
        value: float,
        min_ok: float,
        max_ok: float,
        inverse: bool = False,
    ) -> AlertLevel:
        """
        Clasifica el nivel de alerta de un ratio.
        inverse=True: valores altos son riesgo (ej. endeudamiento).
        """
        if inverse:
            if value > max_ok * 1.15:
                return AlertLevel.CRITICO
            elif value > max_ok:
                return AlertLevel.ADVERTENCIA
            return AlertLevel.OK
        else:
            if value < min_ok * 0.7:
                return AlertLevel.CRITICO
            elif value < min_ok:
                return AlertLevel.ADVERTENCIA
            return AlertLevel.OK

    def _interpret_liquidez(self, value: float) -> str:
        """Interpretación del ratio de liquidez corriente."""
        if value < 1.0:
            return "La empresa no tiene suficientes activos corrientes para cubrir sus pasivos corrientes. Riesgo de iliquidez."
        elif value < 1.5:
            return "Liquidez ajustada. Capacidad de pago corriente limitada."
        return f"Liquidez adecuada ({value:.2f}x). La empresa puede cubrir sus obligaciones corrientes."

    def _interpret_endeudamiento(self, value: float) -> str:
        """Interpretación del ratio de endeudamiento."""
        if value > 0.85:
            return f"Endeudamiento crítico ({value*100:.1f}%). Patrimonio muy comprometido."
        elif value > 0.70:
            return f"Endeudamiento elevado ({value*100:.1f}%). Supera el umbral recomendado del 70%."
        return f"Nivel de endeudamiento aceptable ({value*100:.1f}%)."

    def _interpret_cobertura(self, value: float) -> str:
        """Interpretación del ratio de cobertura de intereses."""
        if value < 1.0:
            return "La empresa no genera suficiente EBIT para cubrir sus intereses. Riesgo de default."
        elif value < 1.5:
            return f"Cobertura de intereses muy ajustada ({value:.2f}x). Margen de seguridad insuficiente."
        return f"Cobertura de intereses razonable ({value:.2f}x)."
