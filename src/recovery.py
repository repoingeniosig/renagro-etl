"""
Módulo de recuperación de mensajes fallidos
Procesa registros con estado_etl=ERROR al iniciar el servidor
"""
from typing import List, Dict, Any

from .config import config
from .logger import etl_logger
from .database import db
from .models import ControlEnviosBoletas, EstadoETLEnum
from .rabbitmq_client import rabbitmq_client


async def recover_failed_messages() -> int:
    """
    Recupera y republica mensajes con estado ERROR desde la BD
    
    Solo procesa mensajes que tienen retry_count < MAX_RETRIES
    
    Returns:
        Número de mensajes recuperados y republicados
    """
    recovered_count = 0
    
    try:
        etl_logger.info("=== Iniciando recuperación de mensajes fallidos ===")
        
        with db.get_session() as session:
            # Buscar registros con ERROR y reintentos disponibles
            try:
                failed_records = session.query(ControlEnviosBoletas).filter(
                    ControlEnviosBoletas.estado_etl == EstadoETLEnum.ERROR,
                    ControlEnviosBoletas.retry_count < config.MAX_RETRIES
                ).all()
            except Exception as db_error:
                # Si faltan columnas retry_count/last_error_stage, skip recovery
                if "retry_count" in str(db_error) or "last_error_stage" in str(db_error):
                    etl_logger.warning(
                        "Columnas retry_count/last_error_stage no existen en BD. "
                        "Ejecuta: migrations/001_add_retry_fields.sql"
                    )
                    return 0
                raise
            
            if not failed_records:
                etl_logger.info("No hay mensajes con ERROR pendientes de recuperación")
                return 0
            
            etl_logger.info(f"Encontrados {len(failed_records)} mensajes con ERROR para recuperar")
            
            for record in failed_records:
                try:
                    _id = record._id
                    json_data = record.json_data
                    retry_count = record.retry_count
                    last_stage = record.last_error_stage or 'json_save'
                    
                    # Determinar a qué cola publicar según la última etapa de error
                    target_queue = _get_queue_for_stage(last_stage)
                    
                    # Preparar mensaje según la etapa
                    if last_stage == 'db_insert':
                        # Si falló en db_insert, necesitamos las transformaciones
                        # Por simplicidad, volvemos a empezar desde etl_transform
                        message = json_data
                        target_queue = config.QUEUE_ETL_TRANSFORM
                    else:
                        message = json_data
                    
                    # Publicar a cola de reintentos con delay
                    retry_queue = _get_retry_queue_for_stage(last_stage)
                    success = await rabbitmq_client.publish_to_retry(
                        retry_queue=retry_queue,
                        message=message,
                        retry_count=retry_count,
                        error_msg=record.error_message or "Recovery from ERROR state",
                        priority=3  # Prioridad baja para recovery
                    )
                    
                    if success:
                        # Actualizar estado a PENDIENTE (se va a reintentar)
                        record.estado_etl = EstadoETLEnum.PENDIENTE
                        record.retry_count = retry_count + 1
                        session.commit()
                        
                        recovered_count += 1
                        etl_logger.info(
                            f"Recuperado _id={_id} desde {last_stage} "
                            f"(retry {retry_count + 1}/{config.MAX_RETRIES})"
                        )
                    else:
                        etl_logger.error(f"No se pudo republicar mensaje _id={_id}")
                
                except Exception as e:
                    etl_logger.error(
                        f"Error recuperando mensaje _id={record._id}: {e}",
                        exc_info=True
                    )
                    continue
        
        etl_logger.info(f"=== Recuperación completada: {recovered_count} mensajes republicados ===")
        return recovered_count
    
    except Exception as e:
        etl_logger.error(f"Error en proceso de recuperación: {e}", exc_info=True)
        return recovered_count


def _get_queue_for_stage(stage: str) -> str:
    """Obtiene la cola principal según la etapa"""
    stage_to_queue = {
        'json_save': config.QUEUE_JSON_SAVE,
        'etl_transform': config.QUEUE_ETL_TRANSFORM,
        'db_insert': config.QUEUE_DB_INSERT
    }
    return stage_to_queue.get(stage, config.QUEUE_JSON_SAVE)


def _get_retry_queue_for_stage(stage: str) -> str:
    """Obtiene la cola de reintentos según la etapa"""
    stage_to_retry_queue = {
        'json_save': config.QUEUE_JSON_SAVE_RETRY,
        'etl_transform': config.QUEUE_ETL_TRANSFORM_RETRY,
        'db_insert': config.QUEUE_DB_INSERT_RETRY
    }
    return stage_to_retry_queue.get(stage, config.QUEUE_JSON_SAVE_RETRY)
