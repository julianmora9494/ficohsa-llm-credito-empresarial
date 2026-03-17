"""
Scraper para la Web API del Banco Central de Honduras (BCH).
API REST documentada: https://bchapi-am.developer.azure-api.net/

Requiere registro gratuito en el portal para obtener API key.
Documentación legal: https://www.bch.hn/marco-legal/terminos-condiciones-uso-web-api
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Series económicas clave para análisis crediticio sectorial
# Códigos de series BCH (verificar en portal bchapi-am.developer.azure-api.net)
BCH_SERIES_CREDIT = {
    # Actividad económica sectorial
    "imae_total": "IMAE_TOTAL",
    "imae_agropecuario": "IMAE_AGROP",
    "imae_industrial": "IMAE_IND",
    "imae_comercio": "IMAE_COM",
    "imae_servicios": "IMAE_SERV",
    # Crédito del sistema financiero
    "credito_total": "CRED_TOTAL",
    "credito_agropecuario": "CRED_AGROP",
    "credito_industria": "CRED_IND",
    "credito_comercio": "CRED_COM",
    "credito_servicios": "CRED_SERV",
    "credito_vivienda": "CRED_VIV",
    "credito_consumo": "CRED_CONS",
    # Tasas de interés
    "tasa_activa_promedio": "TASA_ACTIVA_PROM",
    "tasa_pasiva_promedio": "TASA_PASIVA_PROM",
    # Tipo de cambio
    "tipo_cambio_venta": "TC_VENTA",
    "tipo_cambio_compra": "TC_COMPRA",
}


class BCHAPIScraper:
    """
    Cliente para la API REST del Banco Central de Honduras.
    Descarga series económicas y las guarda como JSON para ingestión.
    """

    BASE_URL = "https://bchapi-am.developer.azure-api.net"

    def __init__(
        self,
        api_key: str,
        output_path: Path,
        request_delay: float = 0.5,
    ) -> None:
        """
        Inicializa el cliente de la API BCH.

        Args:
            api_key: Clave de API obtenida del portal BCH.
            output_path: Directorio donde guardar los datos descargados.
            request_delay: Segundos de espera entre requests (cortesía al servidor).
        """
        self.api_key = api_key
        self.output_path = output_path
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.request_delay = request_delay
        self.session = requests.Session()
        self.session.headers.update({
            "Ocp-Apim-Subscription-Key": api_key,
            "Accept": "application/json",
        })

    def fetch_series(
        self,
        series_code: str,
        fecha_inicio: str,
        fecha_fin: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Descarga una serie económica de la API BCH.

        Args:
            series_code: Código de la serie (ej. "IMAE_AGROP").
            fecha_inicio: Fecha inicio en formato YYYY-MM-DD.
            fecha_fin: Fecha fin. Si es None, usa la fecha actual.

        Returns:
            Dict con la serie descargada, o None si falla.
        """
        if fecha_fin is None:
            fecha_fin = datetime.now().strftime("%Y-%m-%d")

        url = f"{self.BASE_URL}/series/{series_code}"
        params = {
            "fechaInicio": fecha_inicio,
            "fechaFin": fecha_fin,
            "formato": "json",
        }

        try:
            logger.info("Descargando serie %s desde %s", series_code, fecha_inicio)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            logger.info("Serie %s: %d registros descargados", series_code, len(data.get("datos", [])))
            return data
        except requests.exceptions.HTTPError as e:
            logger.error("Error HTTP en serie %s: %s", series_code, str(e))
            return None
        except requests.exceptions.RequestException as e:
            logger.error("Error de red en serie %s: %s", series_code, str(e))
            return None

    def download_credit_indicators(
        self,
        fecha_inicio: str = "2022-01-01",
    ) -> Dict[str, bool]:
        """
        Descarga todos los indicadores de crédito sectorial.

        Args:
            fecha_inicio: Fecha de inicio para la descarga.

        Returns:
            Dict con el estado de descarga de cada serie.
        """
        status: Dict[str, bool] = {}

        for nombre, codigo in BCH_SERIES_CREDIT.items():
            data = self.fetch_series(codigo, fecha_inicio)

            if data is not None:
                output_file = self.output_path / f"bch_{nombre}_{datetime.now().strftime('%Y%m')}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "fuente": "Banco Central de Honduras",
                        "serie": nombre,
                        "codigo": codigo,
                        "fecha_descarga": datetime.now().isoformat(),
                        "url_origen": f"{self.BASE_URL}/series/{codigo}",
                        "datos": data,
                    }, f, ensure_ascii=False, indent=2)
                status[nombre] = True
                logger.info("Guardado: %s", output_file.name)
            else:
                status[nombre] = False

            # Espera entre requests para no saturar el servidor
            time.sleep(self.request_delay)

        exitosas = sum(1 for v in status.values() if v)
        logger.info("BCH API: %d/%d series descargadas", exitosas, len(status))
        return status

    def series_to_text(self, series_data: Dict[str, Any]) -> str:
        """
        Convierte una serie descargada a texto formateado para RAG.
        El texto incluye metadatos para grounding.

        Args:
            series_data: Datos de la serie en formato dict.

        Returns:
            Texto formateado listo para chunking e indexación.
        """
        lines = [
            f"Fuente: {series_data.get('fuente', 'BCH')}",
            f"Serie: {series_data.get('serie', '')}",
            f"Fecha de descarga: {series_data.get('fecha_descarga', '')}",
            "",
        ]

        datos = series_data.get("datos", {}).get("datos", [])
        for registro in datos:
            fecha = registro.get("fecha", "")
            valor = registro.get("valor", "")
            lines.append(f"{fecha}: {valor}")

        return "\n".join(lines)
