"""
Workers/Consumidores para las colas de RabbitMQ
Cada worker procesa mensajes de una cola específica del pipeline ETL
"""
import asyncio
import sys
from typing import Dict, Any
from sqlalchemy import text

from .config import config
from .logger import etl_logger
from .database import db
from .models import ControlEnviosBoletas, EstadoETLEnum, EstadoEnvioEnum, get_control_table_model
from .rabbitmq_client import rabbitmq_client
from .mapping_loader import mapping_loader
from .transformer import JSONTransformer
from .executor import TransactionExecutor
from .forms_manager import forms_manager
from datetime import datetime
from sqlalchemy import inspect


class JsonSaveWorker:
    """
    Worker para cola json_save
    Recibe JSON, lo guarda en control_envios_boletas y pasa a siguiente cola
    """
    
    @staticmethod
    async def process_message(data: Dict[str, Any]):
        """
        Procesa un mensaje de la cola json_save
        
        Args:
            data: Mensaje con el JSON completo del formulario
        """
        _id = data.get('_id')
        uuid_boleta = data.get('_uuid')
        form_uuid = data.get('__form_uuid__', 'default')
        
        try:
            etl_logger.info(f"[json_save] Procesando _id={_id} uuid={uuid_boleta} form={form_uuid}")
            
            # Validar campos requeridos
            if not _id:
                raise ValueError("El JSON no contiene el campo '_id'")
            
            # Obtener configuración del formulario
            form_config = forms_manager.get_form_config(form_uuid)
            if not form_config:
                raise ValueError(f"Formulario no configurado: {form_uuid}")
            
            # Obtener modelo dinámico de la tabla de control
            ControlModel = get_control_table_model(form_config.control_table, db.engine)
            
            # Guardar en tabla de control correspondiente
            with db.get_session() as session:
                control = ControlModel(
                    _id=_id,
                    uuid_boleta=uuid_boleta,
                    json_data=data,
                    estado_etl=EstadoETLEnum.PENDIENTE.value,
                    envio_datos_procesados=EstadoEnvioEnum.PENDIENTE.value
                )
                session.add(control)
                session.commit()
                
                etl_logger.info(f"[json_save] Guardado en {form_config.control_table} _id={_id}")
            
            # Publicar a siguiente cola: etl_transform
            success = await rabbitmq_client.publish_message(
                queue_name=config.QUEUE_ETL_TRANSFORM,
                message=data,
                priority=5
            )
            
            if success:
                etl_logger.info(f"[json_save] Mensaje enviado a etl_transform _id={_id}")
            else:
                raise Exception("No se pudo publicar a etl_transform")
        
        except Exception as e:
            error_msg = f"Error en json_save: {str(e)}"
            etl_logger.error(f"[json_save] _id={_id} - {error_msg}", exc_info=True)
            
            # Actualizar retry_count y estado en BD
            retry_count = 0
            try:
                form_config = forms_manager.get_form_config(form_uuid)
                ControlModel = get_control_table_model(form_config.control_table, db.engine)
                
                with db.get_session() as session:
                    control = session.query(ControlModel).filter_by(_id=_id).first()
                    if control:
                        control.retry_count += 1
                        retry_count = control.retry_count
                        control.last_error_stage = 'json_save'
                        control.error_message = error_msg
                        
                        if retry_count >= config.MAX_RETRIES:
                            control.estado_etl = EstadoETLEnum.ERROR.value
                            etl_logger.error(
                                f"[json_save] _id={_id} alcanzó MAX_RETRIES={config.MAX_RETRIES}"
                            )
                        else:
                            control.estado_etl = EstadoETLEnum.PENDIENTE.value
                        
                        session.commit()
            except Exception as db_error:
                etl_logger.error(f"[json_save] Error actualizando BD: {db_error}")
            
            # Decidir si reintentar o enviar a DLQ
            if retry_count >= config.MAX_RETRIES:
                # Enviar a Dead Letter Queue
                await rabbitmq_client.publish_to_dlq(
                    dlq_queue=config.QUEUE_JSON_SAVE_DLQ,
                    _id=_id,
                    error_msg=error_msg,
                    original_queue=config.QUEUE_JSON_SAVE,
                    retry_count=retry_count
                )
            else:
                # Publicar a cola de reintentos con delay
                await rabbitmq_client.publish_to_retry(
                    retry_queue=config.QUEUE_JSON_SAVE_RETRY,
                    message=data,
                    retry_count=retry_count,
                    error_msg=error_msg,
                    priority=5
                )
            
            # NO re-raise - el mensaje ya se manejó (retry o DLQ)


class EtlTransformWorker:
    """
    Worker para cola etl_transform
    Realiza transformaciones y genera SQL para inserción
    """
    
    @staticmethod
    async def process_message(data: Dict[str, Any]):
        """
        Procesa un mensaje de la cola etl_transform
        
        Args:
            data: Mensaje con el JSON completo del formulario
        """
        _id = data.get('_id')
        form_uuid = data.get('__form_uuid__', 'default')
        
        try:
            etl_logger.info(f"[etl_transform] Procesando _id={_id} form={form_uuid}")
            
            # Obtener mapeos del formulario
            entity_mappings = mapping_loader.get_form_mappings(form_uuid)
            
            if not entity_mappings:
                raise ValueError(f"No hay mapeos cargados para formulario {form_uuid}")
            
            # Establecer como activo para retrocompatibilidad
            mapping_loader.set_active_form(form_uuid)
            
            processing_order = mapping_loader.get_processing_order(form_uuid)
            
            # Transformar datos según mapeos
            transformations = {}
            
            for group in processing_order:
                for entity_name in group:
                    if entity_name not in entity_mappings:
                        continue
                    
                    entity_mapping = entity_mappings[entity_name]
                    
                    rows = JSONTransformer.transform_entity_with_repeats(
                        data,
                        entity_mapping,
                        parent_id=None
                    )
                    
                    if rows:
                        transformations[entity_name] = rows
                        etl_logger.debug(f"[etl_transform] _id={_id} - {entity_name}: {len(rows)} registros")
            
            if not transformations:
                etl_logger.warning(f"[etl_transform] _id={_id} - Sin datos para insertar")
                
                # Actualizar estado a PROCESADO (sin datos) en tabla específica
                form_config = forms_manager.get_form_config(form_uuid)
                ControlModel = get_control_table_model(form_config.control_table, db.engine)
                
                with db.get_session() as session:
                    control = session.query(ControlModel).filter_by(_id=_id).first()
                    if control:
                        control.estado_etl = EstadoETLEnum.PROCESADO.value
                        control.procesado_at = datetime.now()
                        session.commit()
                
                return  # No continuar pipeline
            
            etl_logger.info(f"[etl_transform] _id={_id} - {len(transformations)} entidades transformadas")
            
            # Preparar mensaje para siguiente cola
            transform_message = {
                '_id': _id,
                '__form_uuid__': form_uuid,
                'transformations': transformations,
                'processing_order': processing_order
            }
            
            # Publicar a siguiente cola: db_insert
            success = await rabbitmq_client.publish_message(
                queue_name=config.QUEUE_DB_INSERT,
                message=transform_message,
                priority=5
            )
            
            if success:
                etl_logger.info(f"[etl_transform] Mensaje enviado a db_insert _id={_id}")
            else:
                raise Exception("No se pudo publicar a db_insert")
        
        except Exception as e:
            error_msg = f"Error en etl_transform: {str(e)}"
            etl_logger.error(f"[etl_transform] _id={_id} - {error_msg}", exc_info=True)
            
            # Actualizar retry_count y estado en BD (tabla específica)
            retry_count = 0
            try:
                form_config = forms_manager.get_form_config(form_uuid)
                ControlModel = get_control_table_model(form_config.control_table, db.engine)
                
                with db.get_session() as session:
                    control = session.query(ControlModel).filter_by(_id=_id).first()
                    if control:
                        control.retry_count += 1
                        control.last_error_stage = 'etl_transform'
                        control.error_message = error_msg
                        retry_count = control.retry_count
                        
                        if retry_count >= config.MAX_RETRIES:
                            control.estado_etl = EstadoETLEnum.ERROR.value
                            etl_logger.error(
                                f"[etl_transform] _id={_id} alcanzó MAX_RETRIES={config.MAX_RETRIES}"
                            )
                        else:
                            control.estado_etl = EstadoETLEnum.PENDIENTE.value
                        
                        session.commit()
            except Exception as db_error:
                etl_logger.error(f"[etl_transform] Error actualizando BD: {db_error}")
            
            # Decidir si reintentar o enviar a DLQ
            if retry_count >= config.MAX_RETRIES:
                # Enviar a Dead Letter Queue
                await rabbitmq_client.publish_to_dlq(
                    dlq_queue=config.QUEUE_ETL_TRANSFORM_DLQ,
                    _id=_id,
                    error_msg=error_msg,
                    original_queue=config.QUEUE_ETL_TRANSFORM,
                    retry_count=retry_count
                )
            else:
                # Publicar a cola de reintentos con delay
                await rabbitmq_client.publish_to_retry(
                    retry_queue=config.QUEUE_ETL_TRANSFORM_RETRY,
                    message=data,
                    retry_count=retry_count,
                    error_msg=error_msg,
                    priority=5
                )
            
            # NO re-raise - el mensaje ya se manejó (retry o DLQ)
            raise


class DbInsertWorker:
    """
    Worker para cola db_insert
    Ejecuta la transacción SQL en PostgreSQL
    """
    
    @staticmethod
    async def process_message(data: Dict[str, Any]):
        """
        Procesa un mensaje de la cola db_insert
        
        Args:
            data: Mensaje con transformations y processing_order
        """
        _id = data.get('_id')
        form_uuid = data.get('__form_uuid__', 'default')
        transformations = data.get('transformations', {})
        processing_order = data.get('processing_order', [])
        
        try:
            etl_logger.info(f"[db_insert] Procesando _id={_id} form={form_uuid}")
            
            # Obtener mapeos del formulario
            entity_mappings = mapping_loader.get_form_mappings(form_uuid)
            
            if not entity_mappings:
                raise ValueError(f"No hay mapeos cargados para formulario {form_uuid}")
            
            # Crear instancia de executor con los mapeos del formulario
            executor = TransactionExecutor(entity_mappings=entity_mappings)
            
            # Ejecutar transacción
            # Nota: execute_inserts es síncrono, lo ejecutamos en thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                executor.execute_inserts,
                transformations,
                processing_order,
                config.DEBUG
            )
            
            if results['success']:
                etl_logger.info(
                    f"[db_insert] _id={_id} - Transacción exitosa: "
                    f"{results['total_rows_inserted']} filas insertadas"
                )
                
                # Actualizar estado a PROCESADO en tabla específica
                form_config = forms_manager.get_form_config(form_uuid)
                ControlModel = get_control_table_model(form_config.control_table, db.engine)
                
                with db.get_session() as session:
                    control = session.query(ControlModel).filter_by(_id=_id).first()
                    if control:
                        control.estado_etl = EstadoETLEnum.PROCESADO.value
                        control.procesado_at = datetime.now()
                        control.error_message = None
                        session.commit()
            else:
                error_msg = '; '.join(results['errors']) if results['errors'] else 'Error desconocido'
                etl_logger.error(f"[db_insert] _id={_id} - Transacción fallida: {error_msg}")
                
                # Actualizar estado a ERROR en tabla específica
                form_config = forms_manager.get_form_config(form_uuid)
                ControlModel = get_control_table_model(form_config.control_table, db.engine)
                
                with db.get_session() as session:
                    control = session.query(ControlModel).filter_by(_id=_id).first()
                    if control:
                        control.estado_etl = EstadoETLEnum.ERROR.value
                        control.error_message = error_msg
                        session.commit()
                
                raise Exception(f"Transacción fallida: {error_msg}")
        
        except Exception as e:
            error_msg = f"Error en db_insert: {str(e)}"
            etl_logger.error(f"[db_insert] _id={_id} - {error_msg}", exc_info=True)
            
            # Actualizar retry_count y estado en BD (tabla específica)
            retry_count = 0
            try:
                form_config = forms_manager.get_form_config(form_uuid)
                ControlModel = get_control_table_model(form_config.control_table, db.engine)
                
                with db.get_session() as session:
                    control = session.query(ControlModel).filter_by(_id=_id).first()
                    if control:
                        control.retry_count += 1
                        control.last_error_stage = 'db_insert'
                        control.error_message = error_msg
                        retry_count = control.retry_count
                        
                        if retry_count >= config.MAX_RETRIES:
                            control.estado_etl = EstadoETLEnum.ERROR.value
                            etl_logger.error(
                                f"[db_insert] _id={_id} alcanzó MAX_RETRIES={config.MAX_RETRIES}"
                            )
                        else:
                            control.estado_etl = EstadoETLEnum.PENDIENTE.value
                        
                        session.commit()
            except Exception as db_error:
                etl_logger.error(f"[db_insert] Error actualizando BD: {db_error}")
            
            # Decidir si reintentar o enviar a DLQ
            if retry_count >= config.MAX_RETRIES:
                # Enviar a Dead Letter Queue
                await rabbitmq_client.publish_to_dlq(
                    dlq_queue=config.QUEUE_DB_INSERT_DLQ,
                    _id=_id,
                    error_msg=error_msg,
                    original_queue=config.QUEUE_DB_INSERT,
                    retry_count=retry_count
                )
            else:
                # Publicar a cola de reintentos con delay
                # IMPORTANTE: Re-publicar el mensaje de transformación completo
                await rabbitmq_client.publish_to_retry(
                    retry_queue=config.QUEUE_DB_INSERT_RETRY,
                    message=data,  # Incluye transformations y processing_order
                    retry_count=retry_count,
                    error_msg=error_msg,
                    priority=5
                )
            
            # NO re-raise - el mensaje ya se manejó (retry o DLQ)


# Función principal para ejecutar un worker específico
async def run_worker(worker_type: str):
    """
    Ejecuta un worker específico
    
    Args:
        worker_type: Tipo de worker (json_save, etl_transform, db_insert)
    """
    etl_logger.info(f"Iniciando worker: {worker_type}")
    
    # Mapeo de workers
    workers = {
        'json_save': (config.QUEUE_JSON_SAVE, JsonSaveWorker.process_message),
        'etl_transform': (config.QUEUE_ETL_TRANSFORM, EtlTransformWorker.process_message),
        'db_insert': (config.QUEUE_DB_INSERT, DbInsertWorker.process_message)
    }
    
    if worker_type not in workers:
        raise ValueError(f"Worker desconocido: {worker_type}")
    
    queue_name, callback = workers[worker_type]
    
    try:
        # Consumir cola
        await rabbitmq_client.consume_queue(
            queue_name=queue_name,
            callback=callback,
            prefetch_count=10
        )
    except KeyboardInterrupt:
        etl_logger.info(f"Worker {worker_type} detenido por usuario")
    except Exception as e:
        etl_logger.error(f"Error en worker {worker_type}: {e}", exc_info=True)
        raise
    finally:
        await rabbitmq_client.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python -m src.workers <worker_type>")
        print("Worker types: json_save, etl_transform, db_insert")
        sys.exit(1)
    
    worker_type = sys.argv[1]
    asyncio.run(run_worker(worker_type))
