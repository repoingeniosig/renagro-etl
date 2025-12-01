"""
Módulo de recuperación de mensajes fallidos
Procesa registros con estado_etl=ERROR al iniciar el servidor
Soporta múltiples tablas de control (multi-formulario)
"""
from typing import List, Dict, Any

from .config import config
from .logger import etl_logger
from .database import db
from .models import ControlEnviosBoletas, EstadoETLEnum, get_control_table_model
from .rabbitmq_client import rabbitmq_client
from .forms_manager import forms_manager


async def recover_failed_messages() -> int:
    """
    Recupera y republica mensajes con estado ERROR desde todas las tablas de control
    
    Solo procesa mensajes que tienen retry_count < MAX_RETRIES
    
    Returns:
        Número de mensajes recuperados y republicados
    """
    recovered_count = 0
    
    try:
        etl_logger.info("=== Iniciando recuperación de mensajes fallidos ===")
        
        # Obtener todos los formularios configurados
        forms = forms_manager.list_active_forms()
        
        for form in forms:
            etl_logger.info(f"Recuperando mensajes de {form.control_table}...")
            
            try:
                # Obtener modelo dinámico para la tabla
                ControlModel = get_control_table_model(form.control_table, db.engine)
                
                with db.get_session() as session:
                    # Buscar registros con ERROR y reintentos disponibles
                    failed_records = session.query(ControlModel).filter_by(
                        estado_etl=EstadoETLEnum.ERROR.value
                    ).filter(
                        ControlModel.retry_count < config.MAX_RETRIES
                    ).all()
                    
                    if not failed_records:
                        etl_logger.info(f"  No hay mensajes con ERROR en {form.control_table}")
                        continue
                    
                    etl_logger.info(f"  Encontrados {len(failed_records)} mensajes en {form.control_table}")
                    
                    for record in failed_records:
                        try:
                            _id = record._id
                            json_data = record.json_data
                            retry_count = record.retry_count
                            last_stage = record.last_error_stage or 'json_save'
                            
                            # Agregar metadato del formulario
                            json_data['__form_uuid__'] = form.uuid
                            
                            # Determinar a qué cola publicar según la última etapa de error
                            target_queue = _get_queue_for_stage(last_stage)
                            
                            # Preparar mensaje según la etapa
                            if last_stage == 'db_insert':
                                # Si falló en db_insert, volver a empezar desde etl_transform
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
                                record.estado_etl = EstadoETLEnum.PENDIENTE.value
                                record.retry_count = retry_count + 1
                                session.commit()
                                
                                recovered_count += 1
                                etl_logger.info(
                                    f"  Recuperado _id={_id} desde {last_stage} "
                                    f"(retry {retry_count + 1}/{config.MAX_RETRIES})"
                                )
                            else:
                                etl_logger.error(f"  No se pudo republicar mensaje _id={_id}")
                        
                        except Exception as e:
                            etl_logger.error(
                                f"  Error recuperando mensaje _id={record._id}: {e}",
                                exc_info=True
                            )
                            continue
            
            except Exception as table_error:
                etl_logger.error(f"Error procesando tabla {form.control_table}: {table_error}")
                continue
        
        etl_logger.info(f"=== Recuperación completada: {recovered_count} mensajes republicados ===")
        return recovered_count
    
    except Exception as e:
        etl_logger.error(
            f"Error en proceso de recuperación: {type(e).__name__} - {e}",
            exc_info=config.DEBUG_MODE
        )
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
