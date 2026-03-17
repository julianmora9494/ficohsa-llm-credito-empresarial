"""
Funciones auxiliares de uso general en el sistema.
"""
import re
from pathlib import Path
from typing import Any, Dict, List


def sanitize_company_name(name: str) -> str:
    """
    Normaliza el nombre de una empresa para uso como clave o nombre de archivo.

    Args:
        name: Nombre de la empresa.

    Returns:
        Nombre normalizado sin caracteres especiales.
    """
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s]+", "_", name)
    return name


def format_currency(value: float, currency: str = "L") -> str:
    """
    Formatea un valor monetario con separadores de miles.

    Args:
        value: Valor numérico.
        currency: Símbolo de moneda (L = Lempiras por defecto).

    Returns:
        String formateado (ej. "L 1,250,000.00").
    """
    return f"{currency} {value:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Convierte un ratio decimal a porcentaje formateado.

    Args:
        value: Valor decimal (ej. 0.75).
        decimals: Número de decimales a mostrar.

    Returns:
        String de porcentaje (ej. "75.0%").
    """
    return f"{value * 100:.{decimals}f}%"


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Aplana un diccionario anidado a un nivel.

    Args:
        d: Diccionario a aplanar.
        parent_key: Prefijo para claves anidadas.
        sep: Separador entre niveles.

    Returns:
        Diccionario aplanado.
    """
    items: List = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def truncate_text(text: str, max_chars: int = 500, suffix: str = "...") -> str:
    """
    Trunca un texto a una longitud máxima.

    Args:
        text: Texto a truncar.
        max_chars: Longitud máxima.
        suffix: Sufijo a agregar si se trunca.

    Returns:
        Texto truncado.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars - len(suffix)] + suffix


def ensure_dir(path: Path) -> Path:
    """
    Crea el directorio si no existe.

    Args:
        path: Ruta del directorio.

    Returns:
        La misma ruta de entrada.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
