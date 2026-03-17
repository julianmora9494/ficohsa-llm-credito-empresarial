"""
Script CLI para ingestión e indexación inicial de documentos.

Uso:
    python scripts/ingest_documents.py --tipo sector
    python scripts/ingest_documents.py --tipo financiero --empresa AgroExportadora
    python scripts/ingest_documents.py --tipo todos
"""
import argparse
import sys
from pathlib import Path

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.credit_service import CreditService
from src.utils.logger import setup_logger

logger = setup_logger("ingest_script", log_file=Path("./logs/ingest.log"))


def ingest_sector() -> None:
    """Indexa todos los informes de gestión sectoriales."""
    logger.info("Iniciando ingestión de informes de gestión...")
    service = CreditService()
    service.initialize(load_existing_indexes=False)

    stats = service.index_informes_gestion()
    print("\n=== Ingestión Sectorial Completada ===")
    for country, chunks in stats.items():
        print(f"  {country.capitalize()}: {chunks} chunks indexados")
    print(f"  Total: {sum(stats.values())} chunks\n")


def ingest_financiero(empresa: str) -> None:
    """Indexa estados financieros de una empresa."""
    logger.info("Iniciando ingestión de estados financieros: %s", empresa)
    service = CreditService()
    service.initialize(load_existing_indexes=True)

    chunks = service.index_estados_financieros(empresa)
    print(f"\n=== Estados Financieros Indexados ===")
    print(f"  Empresa: {empresa}")
    print(f"  Chunks indexados: {chunks}\n")


def main() -> None:
    """Punto de entrada del script de ingestión."""
    parser = argparse.ArgumentParser(
        description="Ingestión e indexación de documentos para FicoCrédito AI"
    )
    parser.add_argument(
        "--tipo",
        choices=["sector", "financiero", "todos"],
        required=True,
        help="Tipo de documentos a ingestar",
    )
    parser.add_argument(
        "--empresa",
        type=str,
        default="",
        help="Nombre de la empresa (requerido para --tipo financiero)",
    )
    args = parser.parse_args()

    if args.tipo == "sector":
        ingest_sector()
    elif args.tipo == "financiero":
        if not args.empresa:
            print("Error: --empresa es requerido para --tipo financiero")
            sys.exit(1)
        ingest_financiero(args.empresa)
    elif args.tipo == "todos":
        ingest_sector()
        if args.empresa:
            ingest_financiero(args.empresa)


if __name__ == "__main__":
    main()
