"""
Workers/Consumidores para las colas de RabbitMQ
Cada worker procesa mensajes de una cola específica del pipeline ETL
"""
import asyncio
import sys
from typing import Dict, Any

from .config import config
from .logger import etl_logger
from .database import db
from .models import ControlEnviosBoletas, EstadoETLEnum, EstadoEnvioEnum, get_control_table_model
from .rabbitmq_client import rabbitmq_client
from .mapping_loader import mapping_loader
from .multi_form_loader import multi_form_loader
from .transformer import JSONTransformer
from .executor import TransactionExecutor
from datetime import datetime


def get_control_model_from_json(data: Dict[str, Any]):
    """
    Obtiene el modelo de control dinámicamente desde el JSON del formulario
    
    Args:
        data: JSON del formulario
    
    Returns:
        Modelo SQLAlchemy de la tabla de control correspondiente
    """
    try:
        form_uuid = multi_form_loader.extract_form_uuid_from_json(data)
        if form_uuid:
            form_config = multi_form_loader.get_form_by_uuid(form_uuid)
            if form_config:
                return get_control_table_model(form_config.control_table)
    except Exception as e:
        etl_logger.warning(f"Error obteniendo modelo de control desde JSON: {e}")
    
    # Fallback a la tabla por defecto
    return ControlEnviosBoletas


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
        uuid_boleta = data.get('_uuid')  # Extraer UUID de la boleta
        
        try:
            etl_logger.info(f"[json_save] Procesando _id={_id} uuid={uuid_boleta}")
            
            # Validar campos requeridos
            if not _id:
                raise ValueError("El JSON no contiene el campo '_id'")
            
            # Extraer UUID del formulario para determinar la tabla de control
            form_uuid = multi_form_loader.extract_form_uuid_from_json(data)
            if not form_uuid:
                raise ValueError("No se pudo extraer el UUID del formulario del JSON")
            
            # Obtener configuración del formulario
            form_config = multi_form_loader.get_form_by_uuid(form_uuid)
            if not form_config:
                raise ValueError(f"Formulario no registrado: {form_uuid}")
            
            etl_logger.info(
                f"[json_save] _id={_id} - Formulario: {form_config.name}, "
                f"Tabla de control: {form_config.control_table}"
            )
            
            # Obtener el modelo de control dinámicamente
            ControlModel = get_control_table_model(form_config.control_table)
            
            # Guardar en tabla de control
            with db.get_session() as session:
                # Nota: La validación de duplicados se hace en el endpoint FastAPI
                # Si llegó aquí, es porque pasó la validación

                # En caso de leer desde la api de kobo, igualente cada registro se deberia verificar en el script
                # que orignalmente lee la api de kobo y hacer un proceso parecido al que hace la api actual de /boletas para evitar duplicados.
                
                # Crear nuevo registro
                registro = ControlModel(
                    _id=_id,
                    uuid_boleta=uuid_boleta,
                    json_data=data,
                    estado_etl=EstadoETLEnum.PENDIENTE,
                    envio_datos_procesados=EstadoEnvioEnum.PENDIENTE
                )
                
                session.add(registro)
                session.commit()
                
                etl_logger.info(
                    f"[json_save] JSON guardado _id={_id} en tabla {form_config.control_table}"
                )
            
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
                # Intentar obtener el modelo de control (puede fallar si el error fue antes de detectar el formulario)
                try:
                    form_uuid = multi_form_loader.extract_form_uuid_from_json(data)
                    form_config = multi_form_loader.get_form_by_uuid(form_uuid) if form_uuid else None
                    ControlModel = get_control_table_model(form_config.control_table) if form_config else ControlEnviosBoletas
                except:
                    # Fallback a la tabla de control por defecto
                    ControlModel = ControlEnviosBoletas
                
                with db.get_session() as session:
                    control = session.query(ControlModel).filter_by(_id=_id).first()
                    if control:
                        control.retry_count += 1
                        retry_count = control.retry_count
                        control.last_error_stage = 'json_save'
                        control.error_message = error_msg
                        
                        if retry_count >= config.MAX_RETRIES:
                            control.estado_etl = EstadoETLEnum.ERROR
                            etl_logger.error(
                                f"[json_save] _id={_id} alcanzó MAX_RETRIES={config.MAX_RETRIES}"
                            )
                        else:
                            control.estado_etl = EstadoETLEnum.PENDIENTE
                        
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
        
        try:
            etl_logger.info(f"[etl_transform] Procesando _id={_id}")
            
            # Extraer UUID del formulario del JSON
            form_uuid = multi_form_loader.extract_form_uuid_from_json(data)
            if not form_uuid:
                error_msg = "No se pudo extraer el UUID del formulario del JSON"
                etl_logger.error(f"[etl_transform] _id={_id} - {error_msg}")
                raise ValueError(error_msg)
            
            etl_logger.info(f"[etl_transform] _id={_id} - Formulario detectado: {form_uuid}")
            
            # Obtener configuración del formulario
            form_config = multi_form_loader.get_form_by_uuid(form_uuid)
            if not form_config:
                error_msg = f"Formulario no registrado: {form_uuid}"
                etl_logger.error(f"[etl_transform] _id={_id} - {error_msg}")
                
                if multi_form_loader.config.reject_unknown_forms:
                    raise ValueError(error_msg)
                else:
                    etl_logger.warning(f"[etl_transform] _id={_id} - Formulario no registrado, pero reject_unknown_forms=False")
                    return
            
            etl_logger.info(
                f"[etl_transform] _id={_id} - Formulario: {form_config.name} ({form_config.description})"
            )
            
            # Obtener directorio de mappings para este formulario
            mapping_dir = multi_form_loader.get_mapping_dir_for_form(form_uuid)
            if not mapping_dir or not mapping_dir.exists():
                error_msg = f"Directorio de mappings no encontrado: {mapping_dir}"
                etl_logger.error(f"[etl_transform] _id={_id} - {error_msg}")
                raise FileNotFoundError(error_msg)
            
            etl_logger.info(f"[etl_transform] _id={_id} - Directorio de mappings: {mapping_dir}")
            
            # Cargar mappings desde el directorio específico del formulario
            mapping_loader.load_master(mapping_dir=mapping_dir)
            mapping_loader.load_all_mappings(force_reload=True, mapping_dir=mapping_dir)
            
            # Log de mapeos cargados
            etl_logger.info(f"[etl_transform] _id={_id} - Mapeos disponibles: {list(mapping_loader.entity_mappings.keys())}")
            
            processing_order = mapping_loader.get_processing_order()
            etl_logger.info(f"[etl_transform] _id={_id} - Orden de procesamiento: {processing_order}")
            
            # Transformar datos según mapeos
            transformations = {}
            
            for group in processing_order:
                for entity_name in group:
                    if entity_name not in mapping_loader.entity_mappings:
                        etl_logger.debug(f"[etl_transform] _id={_id} - Entidad '{entity_name}' no está en mapeos cargados, saltando...")
                        continue
                    
                    etl_logger.info(f"[etl_transform] _id={_id} - Transformando entidad '{entity_name}'...")
                    entity_mapping = mapping_loader.entity_mappings[entity_name]
                    
                    rows = JSONTransformer.transform_entity_with_repeats(
                        data,
                        entity_mapping,
                        parent_id=None
                    )
                    
                    if rows:
                        transformations[entity_name] = rows
                        etl_logger.info(f"[etl_transform] _id={_id} - ✅ {entity_name}: {len(rows)} registros generados")
                    else:
                        etl_logger.warning(f"[etl_transform] _id={_id} - ⚠️  {entity_name}: 0 registros (posible array vacío o datos faltantes)")
            
            if not transformations:
                # IMPORTANTE: Si NO hay transformaciones, puede ser por dos razones:
                # 1. Los mapeos no están cargados correctamente (ERROR)
                # 2. El formulario tiene arrays vacíos pero es válido (PROCESADO sin datos)
                
                # Verificar si hay mapeos cargados
                if not mapping_loader.entity_mappings:
                    error_msg = "No hay mapeos cargados - revisar master.yml y archivos YAML"
                    etl_logger.error(f"[etl_transform] _id={_id} - {error_msg}")
                    
                    ControlModel = get_control_model_from_json(data)
                    with db.get_session() as session:
                        control = session.query(ControlModel).filter_by(_id=_id).first()
                        if control:
                            control.estado_etl = EstadoETLEnum.ERROR
                            control.error_message = error_msg
                            control.last_error_stage = 'etl_transform'
                            session.commit()
                    
                    raise Exception(error_msg)
                
                # Caso válido: formulario procesado pero sin datos en arrays repetidos
                etl_logger.warning(f"[etl_transform] _id={_id} - Sin datos para insertar (arrays vacíos o campos opcionales sin valores)")
                
                # Actualizar estado a PROCESADO (sin datos)
                ControlModel = get_control_model_from_json(data)
                with db.get_session() as session:
                    control = session.query(ControlModel).filter_by(_id=_id).first()
                    if control:
                        control.estado_etl = EstadoETLEnum.PROCESADO
                        control.procesado_at = datetime.now()
                        control.error_message = "Procesado sin datos: arrays vacíos o campos opcionales"
                        session.commit()
                
                return  # No continuar pipeline
            
            etl_logger.info(f"[etl_transform] _id={_id} - {len(transformations)} entidades transformadas")
            
            # Preparar mensaje para siguiente cola
            transform_message = {
                '_id': _id,
                'transformations': transformations,
                'processing_order': processing_order,
                'mapping_dir': mapping_dir  # Incluir mapping_dir para db_insert
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
            
            # Actualizar retry_count y estado en BD
            retry_count = 0
            try:
                ControlModel = get_control_model_from_json(data)
                with db.get_session() as session:
                    control = session.query(ControlModel).filter_by(_id=_id).first()
                    if control:
                        control.retry_count += 1
                        retry_count = control.retry_count
                        control.last_error_stage = 'etl_transform'
                        control.error_message = error_msg
                        
                        if retry_count >= config.MAX_RETRIES:
                            control.estado_etl = EstadoETLEnum.ERROR
                            etl_logger.error(
                                f"[etl_transform] _id={_id} alcanzó MAX_RETRIES={config.MAX_RETRIES}"
                            )
                        else:
                            control.estado_etl = EstadoETLEnum.PENDIENTE
                        
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
            data: Mensaje con transformations, processing_order y mapping_dir
        """
        _id = data.get('_id')
        transformations = data.get('transformations', {})
        processing_order = data.get('processing_order', [])
        mapping_dir = data.get('mapping_dir')  # Directorio de mappings del formulario
        
        try:
            etl_logger.info(f"[db_insert] Procesando _id={_id}")
            
            # Validar que tenemos mapping_dir
            if not mapping_dir:
                raise ValueError("No se recibió 'mapping_dir' en el mensaje de db_insert")
            
            # Cargar mapeos si no están en memoria (workers son procesos separados)
            from .mapping_loader import mapping_loader
            if not mapping_loader.entity_mappings:
                etl_logger.warning(f"[db_insert] Cargando mapeos desde {mapping_dir}...")
                mapping_loader.set_mapping_dir(mapping_dir)
                mapping_loader.load_master(mapping_dir=mapping_dir)
                mapping_loader.load_all_mappings(force_reload=False)
            
            # Crear instancia de executor con los mapeos
            executor = TransactionExecutor(entity_mappings=mapping_loader.entity_mappings)
            
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
                
                # Actualizar estado a PROCESADO
                with db.get_session() as session:
                    control = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
                    if control:
                        control.estado_etl = EstadoETLEnum.PROCESADO
                        control.procesado_at = datetime.now()
                        control.error_message = None
                        session.commit()
            else:
                error_msg = '; '.join(results['errors']) if results['errors'] else 'Error desconocido'
                etl_logger.error(f"[db_insert] _id={_id} - Transacción fallida: {error_msg}")
                
                # Actualizar estado a ERROR
                with db.get_session() as session:
                    control = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
                    if control:
                        control.estado_etl = EstadoETLEnum.ERROR
                        control.error_message = error_msg
                        session.commit()
                
                raise Exception(f"Transacción fallida: {error_msg}")
        
        except Exception as e:
            error_msg = f"Error en db_insert: {str(e)}"
            etl_logger.error(f"[db_insert] _id={_id} - {error_msg}", exc_info=True)
            
            # Actualizar retry_count y estado en BD
            retry_count = 0
            try:
                # Obtener modelo dinámico desde data original (debería estar en el mensaje)
                ControlModel = ControlEnviosBoletas  # Usar por defecto ya que no tenemos el JSON original aquí
                with db.get_session() as session:
                    control = session.query(ControlModel).filter_by(_id=_id).first()
                    if control:
                        control.retry_count += 1
                        retry_count = control.retry_count
                        control.last_error_stage = 'db_insert'
                        control.error_message = error_msg
                        
                        if retry_count >= config.MAX_RETRIES:
                            control.estado_etl = EstadoETLEnum.ERROR
                            etl_logger.error(
                                f"[db_insert] _id={_id} alcanzó MAX_RETRIES={config.MAX_RETRIES}"
                            )
                        else:
                            control.estado_etl = EstadoETLEnum.PENDIENTE
                        
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


class EnvioMagWorker:
    """
    Worker para procesamiento de envío a MAG
    Construye JSONs desde BD y los prepara para envío
    """
    
    @staticmethod
    async def process_message(data: Dict[str, Any]):
        """
        Procesa registros pendientes y construye JSONs
        Este worker NO usa colas, procesa directamente desde BD
        """
        from .logger import envio_mag_logger
        from .batch_processor_envio_mag import batch_processor_envio_mag
        
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
            
        except Exception as e:
            envio_mag_logger.error(f"Error en worker envio_mag: {e}", exc_info=True)
            raise


# Función principal para ejecutar un worker específico
async def run_worker(worker_type: str):
    """
    Ejecuta un worker específico
    
    Args:
        worker_type: Tipo de worker (json_save, etl_transform, db_insert, envio_mag)
    """
    etl_logger.info(f"Iniciando worker: {worker_type}")
    
    # Worker especial envio_mag (no usa colas)
    if worker_type == 'envio_mag':
        try:
            await EnvioMagWorker.process_message({})
        except KeyboardInterrupt:
            from .logger import envio_mag_logger
            envio_mag_logger.info("Worker envio_mag detenido por usuario")
        except Exception as e:
            from .logger import envio_mag_logger
            envio_mag_logger.error(f"Error en worker envio_mag: {e}", exc_info=True)
            raise
        return
    
    # Mapeo de workers normales (basados en colas)
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
        print("Worker types: json_save, etl_transform, db_insert, envio_mag")
        sys.exit(1)
    
    worker_type = sys.argv[1]
    asyncio.run(run_worker(worker_type))
