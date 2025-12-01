"""
Configuración del sistema de logging con rotación semanal
Separa logs de proceso (INFO/DEBUG) de logs de error (ERROR/CRITICAL)
"""
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime

from .config import config


class InfoFilter(logging.Filter):
    """Filtro que solo permite mensajes de nivel INFO, DEBUG y WARNING"""
    def filter(self, record):
        return record.levelno < logging.ERROR


class ErrorFilter(logging.Filter):
    """Filtro que solo permite mensajes de nivel ERROR y CRITICAL"""
    def filter(self, record):
        return record.levelno >= logging.ERROR


def setup_logger(name: str = 'renagro_etl') -> logging.Logger:
    """
    Configura el logger con rotación semanal de archivos
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    # Crear directorio de logs si no existe
    log_dir = Path(config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
    
    # Evitar duplicar handlers si ya existe
    if logger.handlers:
        return logger
    
    # Handler para archivo de proceso (solo INFO, DEBUG, WARNING)
    log_file = log_dir / 'etl_process.log'
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='W0',  # W0 = cada lunes
        interval=1,
        backupCount=12,  # Mantener 12 semanas de logs (3 meses)
        encoding='utf-8'
    )
    file_handler.suffix = '%Y-%m-%d'  # Sufijo con fecha
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(InfoFilter())  # Solo INFO, DEBUG, WARNING
    
    # Handler para archivo de errores (solo ERROR y CRITICAL)
    error_log_file = log_dir / 'etl_errors.log'
    error_handler = TimedRotatingFileHandler(
        filename=error_log_file,
        when='W0',
        interval=1,
        backupCount=12,
        encoding='utf-8'
    )
    error_handler.suffix = '%Y-%m-%d'
    error_handler.setLevel(logging.ERROR)
    error_handler.addFilter(ErrorFilter())  # Solo ERROR y CRITICAL
    
    # Formato de logs
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    
    # Agregar handlers
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger


# Logger global
etl_logger = setup_logger('renagro_etl')
