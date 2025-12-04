"""
Worker para procesamiento y envío de datos a MAG
Orquesta el proceso completo: consulta, transformación y preparación para envío
"""
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import config
from src.logger import envio_mag_logger
from src.batch_processor_envio_mag import batch_processor_envio_mag


def main():
    """
    Función principal del worker de envío a MAG
    Procesa todos los registros pendientes en lotes
    """
    try:
        envio_mag_logger.info("=" * 80)
        envio_mag_logger.info("WORKER ENVIO MAG - INICIANDO")
        envio_mag_logger.info("=" * 80)
        envio_mag_logger.info(f"Tamaño de lote: {config.BATCH_SIZE_SEND_MAG}")
        envio_mag_logger.info(f"Debug JSON Output: {config.DEBUG_JSON_OUTPUT}")
        envio_mag_logger.info(f"Schema BD: {config.DB_SCHEMA}")
        
        # Procesar todos los registros pendientes
        total_processed = batch_processor_envio_mag.process_all_pending()
        
        envio_mag_logger.info("=" * 80)
        envio_mag_logger.info(f"WORKER ENVIO MAG - FINALIZADO")
        envio_mag_logger.info(f"Total de registros procesados: {total_processed}")
        envio_mag_logger.info("=" * 80)
        
        return 0
    
    except KeyboardInterrupt:
        envio_mag_logger.warning("Worker interrumpido por el usuario")
        return 1
    
    except Exception as e:
        envio_mag_logger.error(f"Error fatal en worker: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
