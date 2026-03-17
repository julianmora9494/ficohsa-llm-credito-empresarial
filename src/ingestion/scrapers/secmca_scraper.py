"""
Descargador de reportes mensuales de SECMCA.
Portal: https://www.secmca.org

SECMCA publica reportes PDF/Excel con indicadores bancarios y de actividad
económica para 7 países de Centroamérica, con metodología armonizada.

Los reportes se descargan manualmente o via scraping desde:
- Actividad Económica: https://www.secmca.org/informe/reporte-mensual-de-actividad-economica/
- Indicadores Bancarios: https://www.secmca.org/informe/reporte-mensual-de-indicadores-bancarios/
"""
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

SECMCA_REPORTES = {
    "actividad_economica": "https://www.secmca.org/informe/reporte-mensual-de-actividad-economica/",
    "indicadores_bancarios": "https://www.secmca.org/informe/reporte-mensual-de-indicadores-bancarios/",
    "tipo_cambio": "https://www.secmca.org/informe/reporte-mensual-tipo-cambio-real/",
}


class SECMCAScraper:
    """
    Descarga reportes mensuales de SECMCA (PDF y Excel).
    Soporta listado de reportes disponibles y descarga selectiva por mes.
    """

    def __init__(self, output_path: Path, request_delay: float = 1.0) -> None:
        """
        Inicializa el scraper de SECMCA.

        Args:
            output_path: Directorio donde guardar los reportes descargados.
            request_delay: Segundos de espera entre requests.
        """
        self.output_path = output_path
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.request_delay = request_delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; FicoCreditoAI/1.0; research)",
            "Accept": "text/html,application/xhtml+xml",
        })

    def list_available_reports(self, reporte_type: str) -> List[Dict[str, str]]:
        """
        Lista los reportes disponibles para descarga en una página de SECMCA.

        Args:
            reporte_type: Clave del reporte (ver SECMCA_REPORTES).

        Returns:
            Lista de dicts con {"titulo": ..., "url": ..., "periodo": ...}.
        """
        url = SECMCA_REPORTES.get(reporte_type)
        if not url:
            logger.error("Tipo de reporte desconocido: %s", reporte_type)
            return []

        try:
            logger.info("Listando reportes disponibles: %s", reporte_type)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Buscar links a PDFs y archivos Excel en la página
            reports = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if any(ext in href.lower() for ext in [".pdf", ".xlsx", ".xls"]):
                    reports.append({
                        "titulo": link.get_text(strip=True),
                        "url": href if href.startswith("http") else f"https://www.secmca.org{href}",
                        "tipo": "pdf" if ".pdf" in href.lower() else "excel",
                    })

            logger.info("Encontrados %d reportes disponibles", len(reports))
            return reports

        except requests.exceptions.RequestException as e:
            logger.error("Error al listar reportes SECMCA: %s", str(e))
            return []

    def download_report(self, url: str, filename: str) -> Optional[Path]:
        """
        Descarga un reporte individual de SECMCA.

        Args:
            url: URL del reporte a descargar.
            filename: Nombre del archivo de destino.

        Returns:
            Path del archivo descargado, o None si falla.
        """
        output_file = self.output_path / filename

        if output_file.exists():
            logger.info("Reporte ya existe, omitiendo: %s", filename)
            return output_file

        try:
            logger.info("Descargando: %s", filename)
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()

            with open(output_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info("Descargado: %s (%d KB)", filename, output_file.stat().st_size // 1024)
            time.sleep(self.request_delay)
            return output_file

        except requests.exceptions.RequestException as e:
            logger.error("Error al descargar %s: %s", filename, str(e))
            return None

    def download_latest_reports(self, max_reports: int = 3) -> Dict[str, List[Path]]:
        """
        Descarga los reportes más recientes de cada tipo.

        Args:
            max_reports: Número máximo de reportes por tipo a descargar.

        Returns:
            Dict con tipo de reporte → lista de archivos descargados.
        """
        results: Dict[str, List[Path]] = {}

        for reporte_type in SECMCA_REPORTES:
            available = self.list_available_reports(reporte_type)
            descargados = []

            for report in available[:max_reports]:
                ext = ".pdf" if report["tipo"] == "pdf" else ".xlsx"
                # Generar nombre de archivo limpio con fecha de descarga
                nombre_limpio = re.sub(r"[^\w\-]", "_", report["titulo"])[:60]
                filename = f"secmca_{reporte_type}_{nombre_limpio}{ext}"

                path = self.download_report(report["url"], filename)
                if path:
                    descargados.append(path)

            results[reporte_type] = descargados
            logger.info("SECMCA %s: %d archivos descargados", reporte_type, len(descargados))

        return results


def build_secmca_metadata(filename: str, reporte_type: str) -> dict:
    """
    Construye los metadatos estándar para un documento SECMCA.
    Estos metadatos se incluyen en los chunks para grounding.

    Args:
        filename: Nombre del archivo descargado.
        reporte_type: Tipo de reporte SECMCA.

    Returns:
        Dict con metadatos para incluir en el chunk.
    """
    return {
        "fuente": "SECMCA",
        "fuente_completa": "Secretaría Ejecutiva del Consejo Monetario Centroamericano",
        "tipo_reporte": reporte_type,
        "cobertura": "regional_centroamerica",
        "paises": ["Honduras", "Guatemala", "Nicaragua", "El Salvador", "Costa Rica", "Panamá"],
        "source_category": "informe_gestion",
        "fecha_descarga": datetime.now().isoformat(),
        "file_name": filename,
    }
