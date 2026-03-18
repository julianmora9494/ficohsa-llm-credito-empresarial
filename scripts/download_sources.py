"""
Script para descarga automática de fuentes de datos públicas centroamericanas.

Fuentes soportadas:
  - BCH API Honduras (requiere API key)
  - SIB Guatemala (boletines PDF)
  - SECMCA (reportes regionales PDF/Excel)

Uso:
  python scripts/download_sources.py --fuente todas
  python scripts/download_sources.py --fuente bch --fecha-inicio 2023-01-01
  python scripts/download_sources.py --fuente sib
  python scripts/download_sources.py --fuente secmca --max-reportes 6
"""
# -*- coding: utf-8 -*-
import argparse
import io
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Forzar UTF-8 en stdout para compatibilidad con Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

from src.ingestion.scrapers.bch_api_scraper import BCHAPIScraper
from src.ingestion.scrapers.secmca_scraper import SECMCAScraper
from src.ingestion.scrapers.sib_guatemala_scraper import SIBGuatemalaScraper
from src.utils.logger import setup_logger

logger = setup_logger("download_sources", log_file=Path("./logs/download.log"))

# Directorio base para documentos descargados
RAW_DATA_PATH = Path("./data/raw/informes_gestion")


def download_bch(fecha_inicio: str = "2023-01-01") -> None:
    """Descarga indicadores sectoriales desde la API BCH Honduras."""
    api_key = os.getenv("BCH_API_KEY", "")
    if not api_key:
        print("⚠  BCH_API_KEY no configurada en .env. Ver docs/fuentes_datos.md para obtenerla.")
        print("   Registro en: https://bchapi-am.developer.azure-api.net/")
        return

    output_path = RAW_DATA_PATH / "honduras" / "bch_api"
    scraper = BCHAPIScraper(api_key=api_key, output_path=output_path)
    status = scraper.download_credit_indicators(fecha_inicio=fecha_inicio)

    ok = sum(1 for v in status.values() if v)
    print(f"\n✓ BCH Honduras: {ok}/{len(status)} series descargadas → {output_path}")


def download_sib(n: int = 3) -> None:
    """Descarga boletines mensuales de la SIB Guatemala."""
    output_path = RAW_DATA_PATH / "guatemala"
    scraper = SIBGuatemalaScraper(output_path=output_path)

    for tipo in ["boletin_mensual", "estabilidad"]:
        files = scraper.download_latest(tipo=tipo, n=n)
        print(f"\n✓ SIB Guatemala ({tipo}): {len(files)} archivos → {output_path}")


def download_secmca(max_reportes: int = 3) -> None:
    """Descarga reportes mensuales de SECMCA."""
    output_path = RAW_DATA_PATH / "regional" / "secmca"
    scraper = SECMCAScraper(output_path=output_path)
    results = scraper.download_latest_reports(max_reports=max_reportes)

    for tipo, files in results.items():
        print(f"\n✓ SECMCA ({tipo}): {len(files)} archivos → {output_path}")


def main() -> None:
    """Punto de entrada del script de descarga."""
    parser = argparse.ArgumentParser(
        description="Descarga fuentes de datos públicas centroamericanas para FicoCrédito AI"
    )
    parser.add_argument(
        "--fuente",
        choices=["bch", "sib", "secmca", "todas"],
        default="todas",
        help="Fuente a descargar",
    )
    parser.add_argument(
        "--fecha-inicio",
        default="2023-01-01",
        help="Fecha inicio para BCH API (formato YYYY-MM-DD)",
    )
    parser.add_argument(
        "--max-reportes",
        type=int,
        default=3,
        help="Número máximo de reportes por tipo (para SIB y SECMCA)",
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  FicoCrédito AI — Descarga de Fuentes de Datos")
    print("=" * 60)

    if args.fuente in ("bch", "todas"):
        print("\n[1/3] Descargando BCH API Honduras...")
        download_bch(fecha_inicio=args.fecha_inicio)

    if args.fuente in ("sib", "todas"):
        print("\n[2/3] Descargando SIB Guatemala...")
        download_sib(n=args.max_reportes)

    if args.fuente in ("secmca", "todas"):
        print("\n[3/3] Descargando SECMCA...")
        download_secmca(max_reportes=args.max_reportes)

    print("\n✓ Descarga completada. Próximo paso:")
    print("  python scripts/ingest_documents.py --tipo sector")


if __name__ == "__main__":
    main()
