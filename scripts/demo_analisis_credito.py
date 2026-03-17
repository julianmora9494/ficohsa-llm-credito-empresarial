"""
Script de demostración del análisis crediticio.
Simula la evaluación de una empresa agrícola ficticia.

IMPORTANTE: Los datos usados aquí son completamente ficticios y solo
tienen propósito de prueba/demostración. No contienen datos reales de clientes.

Uso:
    python scripts/demo_analisis_credito.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.credit_service import CreditService
from src.utils.logger import setup_logger

logger = setup_logger("demo_script")


# ─── Datos de ejemplo FICTICIOS ───────────────────────────────────────────────
# Empresa agrícola ficticia para prueba del sistema
EMPRESA_FICTICIA = {
    "empresa": "AgroExportadora Demo S.A.",
    "sector": "agrícola",
    "pais": "Honduras",
    "anio": 2024,
    "financial_data": {
        # Datos financieros completamente ficticios (en miles de lempiras)
        "activo_corriente": 12_500.0,
        "pasivo_corriente": 9_800.0,
        "total_activos": 45_000.0,
        "total_pasivos": 28_000.0,
        "patrimonio": 17_000.0,
        "utilidad_neta": 2_100.0,
        "ventas_netas": 35_000.0,
        "ebit": 3_500.0,
        "gastos_financieros": 1_800.0,
    },
}


def run_demo() -> None:
    """Ejecuta el análisis de crédito con datos ficticios de demostración."""
    print("\n" + "=" * 60)
    print("  FicoCrédito AI — Demostración de Análisis Crediticio")
    print("=" * 60)
    print(f"\nEmpresa: {EMPRESA_FICTICIA['empresa']}")
    print(f"Sector: {EMPRESA_FICTICIA['sector']}")
    print(f"País: {EMPRESA_FICTICIA['pais']}")
    print(f"Año: {EMPRESA_FICTICIA['anio']}")
    print("\n[AVISO] Los datos financieros son ficticios y solo sirven para prueba.\n")

    # Inicializar servicio
    service = CreditService()
    status = service.initialize(load_existing_indexes=True)
    print(f"Índices disponibles: {status}")

    # Ejecutar análisis
    print("\nEjecutando análisis crediticio...\n")
    result = service.analizar_credito(
        empresa=EMPRESA_FICTICIA["empresa"],
        sector=EMPRESA_FICTICIA["sector"],
        pais=EMPRESA_FICTICIA["pais"],
        anio=EMPRESA_FICTICIA["anio"],
        financial_data=EMPRESA_FICTICIA["financial_data"],
        country_filter="honduras",
    )

    # Mostrar resultados
    print("=" * 60)
    print(f"  DICTAMEN: {result['decision']}")
    print("=" * 60)
    print(f"\nConfianza: {result['confianza'].upper()}")
    print(f"\nResumen Ejecutivo:\n{result['resumen_ejecutivo']}")
    print(f"\nSeñales de Riesgo:")
    for s in result['seniales_riesgo']:
        print(f"  - {s}")
    print(f"\nSeñales Positivas:")
    for s in result['seniales_positivas']:
        print(f"  + {s}")
    if result['condiciones']:
        print(f"\nCondiciones:")
        for c in result['condiciones']:
            print(f"  * {c}")
    print(f"\nJustificación:\n{result['justificacion']}")
    print(f"\nFuentes consultadas: {', '.join(result['fuentes_consultadas']) or 'Ninguna'}")
    print(f"\n{result['disclaimer']}\n")


if __name__ == "__main__":
    run_demo()
