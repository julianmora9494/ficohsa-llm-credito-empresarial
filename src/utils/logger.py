"""
Configuración centralizada de logging con rotación de archivos.
Todos los módulos del sistema deben usar este logger.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    max_bytes: int = 10_485_760,
    backup_count: int = 5,
) -> logging.Logger:
    """
    Crea y configura un logger con salida a consola y archivo.

    Args:
        name: Nombre del logger (generalmente __name__ del módulo).
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR).
        log_file: Ruta del archivo de log. Si es None, solo usa consola.
        max_bytes: Tamaño máximo del archivo antes de rotar (10MB por defecto).
        backup_count: Número de archivos de backup a conservar.

    Returns:
        Logger configurado listo para usar.
    """
    logger = logging.getLogger(name)

    # Evitar duplicar handlers si el logger ya fue configurado
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler de archivo con rotación
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
