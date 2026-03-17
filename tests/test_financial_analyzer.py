"""
Tests para el módulo de análisis financiero.
Verifica cálculo de ratios e identificación de alertas.
"""
import pytest

from src.credit.financial_analyzer import AlertLevel, FinancialAnalyzer


@pytest.fixture
def analyzer() -> FinancialAnalyzer:
    """Fixture que retorna una instancia del analizador financiero."""
    return FinancialAnalyzer()


class TestLiquidezCorriente:
    """Tests para el ratio de liquidez corriente."""

    def test_liquidez_ok(self, analyzer: FinancialAnalyzer) -> None:
        """Liquidez entre 1.0 y 3.0 debe ser nivel OK."""
        ratios = analyzer.calculate_ratios(
            activo_corriente=15_000, pasivo_corriente=10_000
        )
        liq = next(r for r in ratios if "Liquidez" in r.name)
        assert liq.value == 1.5
        assert liq.alert_level == AlertLevel.OK

    def test_liquidez_critica(self, analyzer: FinancialAnalyzer) -> None:
        """Liquidez < 0.7 debe ser nivel CRITICO."""
        ratios = analyzer.calculate_ratios(
            activo_corriente=5_000, pasivo_corriente=10_000
        )
        liq = next(r for r in ratios if "Liquidez" in r.name)
        assert liq.value == 0.5
        assert liq.alert_level == AlertLevel.CRITICO

    def test_liquidez_advertencia(self, analyzer: FinancialAnalyzer) -> None:
        """Liquidez entre 0.7 y 1.0 debe ser nivel ADVERTENCIA."""
        ratios = analyzer.calculate_ratios(
            activo_corriente=8_500, pasivo_corriente=10_000
        )
        liq = next(r for r in ratios if "Liquidez" in r.name)
        assert liq.alert_level == AlertLevel.ADVERTENCIA


class TestEndeudamiento:
    """Tests para el ratio de endeudamiento."""

    def test_endeudamiento_aceptable(self, analyzer: FinancialAnalyzer) -> None:
        """Endeudamiento < 70% debe ser nivel OK."""
        ratios = analyzer.calculate_ratios(
            total_pasivos=30_000, total_activos=60_000
        )
        end = next(r for r in ratios if "Endeudamiento" in r.name)
        assert end.value == 0.5
        assert end.alert_level == AlertLevel.OK

    def test_endeudamiento_critico(self, analyzer: FinancialAnalyzer) -> None:
        """Endeudamiento > 80.5% (70% * 1.15) debe ser CRITICO."""
        ratios = analyzer.calculate_ratios(
            total_pasivos=90_000, total_activos=100_000
        )
        end = next(r for r in ratios if "Endeudamiento" in r.name)
        assert end.alert_level == AlertLevel.CRITICO


class TestCoberturaIntereses:
    """Tests para el ratio de cobertura de intereses."""

    def test_cobertura_ok(self, analyzer: FinancialAnalyzer) -> None:
        """Cobertura > 1.5 debe ser nivel OK."""
        ratios = analyzer.calculate_ratios(ebit=5_000, gastos_financieros=2_000)
        cob = next(r for r in ratios if "Cobertura" in r.name)
        assert cob.value == 2.5
        assert cob.alert_level == AlertLevel.OK

    def test_cobertura_critica(self, analyzer: FinancialAnalyzer) -> None:
        """Cobertura < 1.05 (1.5 * 0.7) debe ser CRITICO."""
        ratios = analyzer.calculate_ratios(ebit=1_000, gastos_financieros=2_000)
        cob = next(r for r in ratios if "Cobertura" in r.name)
        assert cob.alert_level == AlertLevel.CRITICO


class TestFinancialProfile:
    """Tests del perfil financiero completo."""

    def test_tiene_alertas_criticas(self, analyzer: FinancialAnalyzer) -> None:
        """El perfil detecta correctamente alertas críticas."""
        from src.credit.financial_analyzer import FinancialProfile

        ratios = analyzer.calculate_ratios(
            activo_corriente=5_000,
            pasivo_corriente=10_000,
        )
        profile = FinancialProfile(
            empresa="TestEmpresa",
            sector="comercio",
            pais="Honduras",
            anio=2024,
            ratios=ratios,
        )
        assert profile.tiene_alertas_criticas is True

    def test_sin_alertas_criticas(self, analyzer: FinancialAnalyzer) -> None:
        """El perfil sin alertas críticas retorna False."""
        from src.credit.financial_analyzer import FinancialProfile

        ratios = analyzer.calculate_ratios(
            activo_corriente=20_000,
            pasivo_corriente=10_000,
        )
        profile = FinancialProfile(
            empresa="TestEmpresa",
            sector="comercio",
            pais="Honduras",
            anio=2024,
            ratios=ratios,
        )
        assert profile.tiene_alertas_criticas is False
