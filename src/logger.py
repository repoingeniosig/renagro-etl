"""
Configuración del sistema de logging con rotación semanal
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from .config import config


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
    
    # Determinar nombre de archivo según el logger
    if name == 'worker_envio_mag_geometria':
        log_file = log_dir / 'worker_envio_mag_geometria.log'
        error_log_file = log_dir / 'worker_envio_mag_geometria_errors.log'
    elif name == 'worker_envio_mag_adicional':
        log_file = log_dir / 'worker_envio_mag_adicional.log'
        error_log_file = log_dir / 'worker_envio_mag_adicional_errors.log'
    elif name.startswith('worker_envio_mag'):
        log_file = log_dir / f'{name}.log'
        error_log_file = log_dir / f'{name}_errors.log'
    else:
        log_file = log_dir / 'etl_process.log'
        error_log_file = log_dir / 'etl_errors.log'
    
    # Handler para archivo con rotación semanal (cada lunes)
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='W0',  # W0 = cada lunes
        interval=1,
        backupCount=12,  # Mantener 12 semanas de logs (3 meses)
        encoding='utf-8'
    )
    file_handler.suffix = '%Y-%m-%d'  # Sufijo con fecha
    file_handler.setLevel(logging.DEBUG)
    
    # Handler para archivo de errores con rotación semanal
    error_handler = TimedRotatingFileHandler(
        filename=error_log_file,
        when='W0',
        interval=1,
        backupCount=12,
        encoding='utf-8'
    )
    error_handler.suffix = '%Y-%m-%d'
    error_handler.setLevel(logging.ERROR)
    
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

# Logger para worker de envío a MAG
envio_mag_logger = setup_logger(os.getenv('ENVIO_MAG_LOGGER_NAME', 'worker_envio_mag'))
