"""
Descargador de boletines mensuales de la SIB Guatemala.
Portal: https://www.sib.gob.gt

El Boletín Mensual de Estadísticas del Sistema Financiero contiene:
- Crédito por sector: Consumo 50.8%, Comercio 14.3%, Manufactura 7.1%,
  Construcción 7%, Agro 2.8%, Real estate 2.8%
- Indicadores de mora y calidad de cartera
- Liquidez, solvencia, rentabilidad por institución

Boletín mensual: https://www.sib.gob.gt/web/sib/Boletn-Mensual-de-Estadisticas
Boletín anual: https://www.sib.gob.gt/web/sib/Boletin-Anual-de-Estadisticas
Indicadores: https://www.sib.gob.gt/web/sib/indicadores_financieros
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

SIB_URLS = {
    "boletin_mensual": "https://www.sib.gob.gt/web/sib/Boletn-Mensual-de-Estadisticas",
    "boletin_anual": "https://www.sib.gob.gt/web/sib/Boletin-Anual-de-Estadisticas",
    "indicadores": "https://www.sib.gob.gt/web/sib/indicadores_financieros",
    "estabilidad": "https://www.sib.gob.gt/web/sib/informacion_sistema_financiero/estabilidad",
}


class SIBGuatemalaScraper:
    """
    Descarga boletines de estadísticas de la SIB Guatemala.
    """

    def __init__(self, output_path: Path, request_delay: float = 1.0) -> None:
        """
        Inicializa el scraper SIB Guatemala.

        Args:
            output_path: Directorio donde guardar los boletines descargados.
            request_delay: Segundos de espera entre requests.
        """
        self.output_path = output_path
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.request_delay = request_delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; FicoCreditoAI/1.0; research)",
        })

    def list_available_boletines(self, tipo: str = "boletin_mensual") -> List[Dict[str, str]]:
        """
        Lista los boletines disponibles para descarga.

        Args:
            tipo: Tipo de boletín (ver SIB_URLS).

        Returns:
            Lista de dicts con info de cada boletín disponible.
        """
        url = SIB_URLS.get(tipo, SIB_URLS["boletin_mensual"])

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            boletines = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if ".pdf" in href.lower() or ".xls" in href.lower():
                    boletines.append({
                        "titulo": link.get_text(strip=True),
                        "url": href if href.startswith("http") else f"https://www.sib.gob.gt{href}",
                        "tipo": "pdf" if ".pdf" in href.lower() else "excel",
                    })

            logger.info("SIB Guatemala %s: %d boletines encontrados", tipo, len(boletines))
            return boletines

        except requests.exceptions.RequestException as e:
            logger.error("Error al listar boletines SIB Guatemala: %s", str(e))
            return []

    def download_latest(self, tipo: str = "boletin_mensual", n: int = 3) -> List[Path]:
        """
        Descarga los n boletines más recientes.

        Args:
            tipo: Tipo de boletín a descargar.
            n: Número de boletines a descargar.

        Returns:
            Lista de paths de archivos descargados.
        """
        boletines = self.list_available_boletines(tipo)
        descargados = []

        for boletin in boletines[:n]:
            ext = ".pdf" if boletin["tipo"] == "pdf" else ".xlsx"
            nombre_limpio = re.sub(r"[^\w\-]", "_", boletin["titulo"])[:60]
            filename = f"sib_guatemala_{tipo}_{nombre_limpio}{ext}"
            output_file = self.output_path / filename

            if output_file.exists():
                descargados.append(output_file)
                continue

            try:
                response = self.session.get(boletin["url"], timeout=60, stream=True)
                response.raise_for_status()

                with open(output_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                descargados.append(output_file)
                logger.info("Descargado: %s", filename)
                time.sleep(self.request_delay)

            except requests.exceptions.RequestException as e:
                logger.error("Error al descargar %s: %s", filename, str(e))

        return descargados


def build_sib_metadata(filename: str) -> dict:
    """Metadatos estándar para chunks de documentos SIB Guatemala."""
    return {
        "fuente": "SIB Guatemala",
        "fuente_completa": "Superintendencia de Bancos de Guatemala",
        "pais": "Guatemala",
        "source_category": "informe_gestion",
        "country": "guatemala",
        "fecha_descarga": datetime.now().isoformat(),
        "file_name": filename,
    }
