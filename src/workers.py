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
            
            # Configurar directorio y cargar mappings (desde Redis cache si existe, sino desde disco)
            # set_mapping_dir limpia entity_mappings cuando cambia el directorio
            mapping_loader.set_mapping_dir(mapping_dir)
            
            # Siempre recargar mapeos después de cambiar directorio para evitar usar mapeos de otro formulario
            mapping_loader.load_master(mapping_dir=mapping_dir)
            mapping_loader.load_all_mappings(force_reload=False, mapping_dir=mapping_dir)
            
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
                'mapping_dir': str(mapping_dir),  # Convertir PosixPath a string para JSON
                'form_uuid': form_uuid,  # Incluir form_uuid para obtener modelo correcto en db_insert
                'control_table': form_config.control_table  # Incluir nombre de tabla de control
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
        mapping_dir = data.get('mapping_dir')  # Directorio de mappings del formulario (string)
        form_uuid = data.get('form_uuid')  # UUID del formulario
        control_table = data.get('control_table')  # Nombre de tabla de control
        
        try:
            etl_logger.info(f"[db_insert] Procesando _id={_id}")
            
            # Validar que tenemos mapping_dir y control_table
            if not mapping_dir:
                raise ValueError("No se recibió 'mapping_dir' en el mensaje de db_insert")
            if not control_table:
                raise ValueError("No se recibió 'control_table' en el mensaje de db_insert")
            
            # Obtener modelo de control dinámico
            ControlModel = get_control_table_model(control_table)
            
            # Cargar mapeos para este formulario específico
            from .mapping_loader import mapping_loader
            from pathlib import Path
            
            mapping_dir_path = Path(mapping_dir) if isinstance(mapping_dir, str) else mapping_dir
            
            # Siempre configurar el directorio correcto y recargar para evitar usar mapeos de otro formulario
            etl_logger.info(f"[db_insert] Configurando mapeos desde {mapping_dir_path}...")
            mapping_loader.set_mapping_dir(mapping_dir_path)
            mapping_loader.load_master(mapping_dir=mapping_dir_path)
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
                    control = session.query(ControlModel).filter_by(_id=_id).first()
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
                    control = session.query(ControlModel).filter_by(_id=_id).first()
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
                # Obtener modelo dinámico desde control_table del mensaje
                try:
                    ControlModel = get_control_table_model(data.get('control_table', 'control_envios_boletas'))
                except:
                    ControlModel = ControlEnviosBoletas  # Fallback
                
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
    
    Comportamiento:
    - Ejecución única (manual)
    - Procesa TODOS los registros pendientes una sola vez
    - Para reprocesar nuevos registros, ejecutar manualmente de nuevo
    """
    
    @staticmethod
    async def process_message(data: Dict[str, Any]):
        """
        Procesa registros pendientes y construye JSONs
        Este worker NO usa colas, procesa directamente desde BD
        Ejecuta UNA SOLA VEZ y termina
        """
        from .logger import envio_mag_logger
        from .batch_processor_envio_mag import batch_processor_envio_mag
        
        try:
            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG - INICIANDO")
            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info(f"Tamaño de lote: {config.BATCH_SIZE_SEND_MAG}")
            envio_mag_logger.info(f"Debug JSON Output: {config.DEBUG_JSON_OUTPUT}")
            envio_mag_logger.info("=" * 80)
            
            # Ejecución única: procesa todos los pendientes y termina
            total_processed = await batch_processor_envio_mag.process_all_pending()
            
            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info(f"WORKER ENVIO MAG - FINALIZADO")
            envio_mag_logger.info(f"Total de registros procesados: {total_processed}")
            envio_mag_logger.info("=" * 80)
            
        except Exception as e:
            envio_mag_logger.error(f"Error en worker envio_mag: {e}", exc_info=True)
            raise


class EnvioMagGeometriaWorker:
    """
    Worker para procesamiento de envío MAG Geometría
    Procesa boleta_geometria y terreno_geometria en ejecución única.
    """

    @staticmethod
    async def process_message(data: Dict[str, Any]):
        from .logger import envio_mag_logger
        from .batch_processor_envio_mag_geometria import process_all_geometry_targets

        try:
            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG GEOMETRÍA - INICIANDO")
            envio_mag_logger.info("=" * 80)

            total_processed = await process_all_geometry_targets()

            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG GEOMETRÍA - FINALIZADO")
            envio_mag_logger.info(f"Total de registros procesados: {total_processed}")
            envio_mag_logger.info("=" * 80)

        except Exception as e:
            envio_mag_logger.error(f"Error en worker envio_mag_geometria: {e}", exc_info=True)
            raise


class EnvioMagGeometriaBoletaWorker:
    """Worker para procesar únicamente boleta_geometria"""

    @staticmethod
    async def process_message(data: Dict[str, Any]):
        from .logger import envio_mag_logger
        from .batch_processor_envio_mag_geometria import process_geometry_target

        try:
            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG GEOMETRÍA BOLETA - INICIANDO")
            envio_mag_logger.info("=" * 80)

            total_processed = await process_geometry_target('boleta_geometria')

            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG GEOMETRÍA BOLETA - FINALIZADO")
            envio_mag_logger.info(f"Total de registros procesados: {total_processed}")
            envio_mag_logger.info("=" * 80)

        except Exception as e:
            envio_mag_logger.error(f"Error en worker envio_mag_geometria_boleta: {e}", exc_info=True)
            raise


class EnvioMagGeometriaTerrenoWorker:
    """Worker para procesar únicamente terreno_geometria"""

    @staticmethod
    async def process_message(data: Dict[str, Any]):
        from .logger import envio_mag_logger
        from .batch_processor_envio_mag_geometria import process_geometry_target

        try:
            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG GEOMETRÍA TERRENO - INICIANDO")
            envio_mag_logger.info("=" * 80)

            total_processed = await process_geometry_target('terreno_geometria')

            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG GEOMETRÍA TERRENO - FINALIZADO")
            envio_mag_logger.info(f"Total de registros procesados: {total_processed}")
            envio_mag_logger.info("=" * 80)

        except Exception as e:
            envio_mag_logger.error(f"Error en worker envio_mag_geometria_terreno: {e}", exc_info=True)
            raise


class EnvioMagAdicionalWorker:
    """
    Worker para procesamiento de envío MAG Adicional.
    Procesa capacitacion, comunicacion y produccion en ejecución única.
    """

    @staticmethod
    async def process_message(data: Dict[str, Any]):
        from .logger import envio_mag_logger
        from .batch_processor_envio_mag_adicional import process_all_additional_targets

        try:
            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG ADICIONAL - INICIANDO")
            envio_mag_logger.info("=" * 80)

            total_processed = await process_all_additional_targets()

            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG ADICIONAL - FINALIZADO")
            envio_mag_logger.info(f"Total de registros procesados: {total_processed}")
            envio_mag_logger.info("=" * 80)

        except Exception as e:
            envio_mag_logger.error(f"Error en worker envio_mag_adicional: {e}", exc_info=True)
            raise


class EnvioMagCapacitacionWorker:
    """Worker para procesar únicamente capacitacion"""

    @staticmethod
    async def process_message(data: Dict[str, Any]):
        from .logger import envio_mag_logger
        from .batch_processor_envio_mag_adicional import process_additional_target

        try:
            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG ADICIONAL CAPACITACIÓN - INICIANDO")
            envio_mag_logger.info("=" * 80)

            total_processed = await process_additional_target('capacitacion')

            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG ADICIONAL CAPACITACIÓN - FINALIZADO")
            envio_mag_logger.info(f"Total de registros procesados: {total_processed}")
            envio_mag_logger.info("=" * 80)

        except Exception as e:
            envio_mag_logger.error(f"Error en worker envio_mag_adicional_capacitacion: {e}", exc_info=True)
            raise


class EnvioMagComunicacionWorker:
    """Worker para procesar únicamente comunicacion"""

    @staticmethod
    async def process_message(data: Dict[str, Any]):
        from .logger import envio_mag_logger
        from .batch_processor_envio_mag_adicional import process_additional_target

        try:
            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG ADICIONAL COMUNICACIÓN - INICIANDO")
            envio_mag_logger.info("=" * 80)

            total_processed = await process_additional_target('comunicacion')

            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG ADICIONAL COMUNICACIÓN - FINALIZADO")
            envio_mag_logger.info(f"Total de registros procesados: {total_processed}")
            envio_mag_logger.info("=" * 80)

        except Exception as e:
            envio_mag_logger.error(f"Error en worker envio_mag_adicional_comunicacion: {e}", exc_info=True)
            raise


class EnvioMagProduccionWorker:
    """Worker para procesar únicamente produccion"""

    @staticmethod
    async def process_message(data: Dict[str, Any]):
        from .logger import envio_mag_logger
        from .batch_processor_envio_mag_adicional import process_additional_target

        try:
            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG ADICIONAL PRODUCCIÓN - INICIANDO")
            envio_mag_logger.info("=" * 80)

            total_processed = await process_additional_target('produccion')

            envio_mag_logger.info("=" * 80)
            envio_mag_logger.info("WORKER ENVIO MAG ADICIONAL PRODUCCIÓN - FINALIZADO")
            envio_mag_logger.info(f"Total de registros procesados: {total_processed}")
            envio_mag_logger.info("=" * 80)

        except Exception as e:
            envio_mag_logger.error(f"Error en worker envio_mag_adicional_produccion: {e}", exc_info=True)
            raise


# Función principal para ejecutar un worker específico
async def run_worker(worker_type: str):
    """
    Ejecuta un worker específico
    
    Args:
        worker_type: Tipo de worker (json_save, etl_transform, db_insert, envio_mag, envio_mag_geometria)
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

    # Worker especial envio_mag_geometria (no usa colas)
    if worker_type == 'envio_mag_geometria':
        try:
            await EnvioMagGeometriaWorker.process_message({})
        except KeyboardInterrupt:
            from .logger import envio_mag_logger
            envio_mag_logger.info("Worker envio_mag_geometria detenido por usuario")
        except Exception as e:
            from .logger import envio_mag_logger
            envio_mag_logger.error(f"Error en worker envio_mag_geometria: {e}", exc_info=True)
            raise
        return

    # Worker especial envio_mag_geometria_boleta (no usa colas)
    if worker_type == 'envio_mag_geometria_boleta':
        try:
            await EnvioMagGeometriaBoletaWorker.process_message({})
        except KeyboardInterrupt:
            from .logger import envio_mag_logger
            envio_mag_logger.info("Worker envio_mag_geometria_boleta detenido por usuario")
        except Exception as e:
            from .logger import envio_mag_logger
            envio_mag_logger.error(f"Error en worker envio_mag_geometria_boleta: {e}", exc_info=True)
            raise
        return

    # Worker especial envio_mag_geometria_terreno (no usa colas)
    if worker_type == 'envio_mag_geometria_terreno':
        try:
            await EnvioMagGeometriaTerrenoWorker.process_message({})
        except KeyboardInterrupt:
            from .logger import envio_mag_logger
            envio_mag_logger.info("Worker envio_mag_geometria_terreno detenido por usuario")
        except Exception as e:
            from .logger import envio_mag_logger
            envio_mag_logger.error(f"Error en worker envio_mag_geometria_terreno: {e}", exc_info=True)
            raise
        return

    # Worker especial envio_mag_adicional (no usa colas) - las 3 entidades
    if worker_type == 'envio_mag_adicional':
        try:
            await EnvioMagAdicionalWorker.process_message({})
        except KeyboardInterrupt:
            from .logger import envio_mag_logger
            envio_mag_logger.info("Worker envio_mag_adicional detenido por usuario")
        except Exception as e:
            from .logger import envio_mag_logger
            envio_mag_logger.error(f"Error en worker envio_mag_adicional: {e}", exc_info=True)
            raise
        return

    # Worker especial envio_mag_adicional_capacitacion (no usa colas)
    if worker_type == 'envio_mag_adicional_capacitacion':
        try:
            await EnvioMagCapacitacionWorker.process_message({})
        except KeyboardInterrupt:
            from .logger import envio_mag_logger
            envio_mag_logger.info("Worker envio_mag_adicional_capacitacion detenido por usuario")
        except Exception as e:
            from .logger import envio_mag_logger
            envio_mag_logger.error(f"Error en worker envio_mag_adicional_capacitacion: {e}", exc_info=True)
            raise
        return

    # Worker especial envio_mag_adicional_comunicacion (no usa colas)
    if worker_type == 'envio_mag_adicional_comunicacion':
        try:
            await EnvioMagComunicacionWorker.process_message({})
        except KeyboardInterrupt:
            from .logger import envio_mag_logger
            envio_mag_logger.info("Worker envio_mag_adicional_comunicacion detenido por usuario")
        except Exception as e:
            from .logger import envio_mag_logger
            envio_mag_logger.error(f"Error en worker envio_mag_adicional_comunicacion: {e}", exc_info=True)
            raise
        return

    # Worker especial envio_mag_adicional_produccion (no usa colas)
    if worker_type == 'envio_mag_adicional_produccion':
        try:
            await EnvioMagProduccionWorker.process_message({})
        except KeyboardInterrupt:
            from .logger import envio_mag_logger
            envio_mag_logger.info("Worker envio_mag_adicional_produccion detenido por usuario")
        except Exception as e:
            from .logger import envio_mag_logger
            envio_mag_logger.error(f"Error en worker envio_mag_adicional_produccion: {e}", exc_info=True)
            raise
        return

    # Mapeo de workers normales (basados en colas)
    workers = {
        'json_save': (config.QUEUE_JSON_SAVE, JsonSaveWorker.process_message),
        'etl_transform': (config.QUEUE_ETL_TRANSFORM, EtlTransformWorker.process_message),
        'db_insert': (config.QUEUE_DB_INSERT, DbInsertWorker.process_message),
        'envio_mag_sender': (config.QUEUE_ENVIO_MAG_SEND, None),  # Configurado abajo
        'envio_mag_geometria_sender': (config.QUEUE_ENVIO_MAG_GEOMETRIA_SEND, None),  # Configurado abajo
        'envio_mag_adicional_sender': (config.QUEUE_ENVIO_MAG_ADICIONAL_SEND, None)  # Configurado abajo
    }
    
    # Configuración especial para envio_mag_sender
    if worker_type == 'envio_mag_sender':
        from .envio_mag_sender_worker import envio_mag_sender_worker
        
        try:
            etl_logger.info(f"Iniciando worker envio_mag_sender (paralelo: {config.PARALLEL_REQUESTS_SEND_MAG})")
            
            # Consumir cola con callback del worker
            await rabbitmq_client.consume_queue(
                queue_name=config.QUEUE_ENVIO_MAG_SEND,
                callback=envio_mag_sender_worker.process_message,
                prefetch_count=config.PARALLEL_REQUESTS_SEND_MAG
            )
        except KeyboardInterrupt:
            etl_logger.info("Worker envio_mag_sender detenido por usuario")
            envio_mag_sender_worker.print_stats()
        except Exception as e:
            etl_logger.error(f"Error en worker envio_mag_sender: {e}", exc_info=True)
            raise
        finally:
            envio_mag_sender_worker.print_stats()
            await rabbitmq_client.close()
        
        return

    # Configuración especial para envio_mag_geometria_sender
    if worker_type == 'envio_mag_geometria_sender':
        from .envio_mag_sender_worker_geometria import envio_mag_sender_worker_geometria

        try:
            etl_logger.info(
                f"Iniciando worker envio_mag_geometria_sender (paralelo: {config.PARALLEL_REQUESTS_SEND_MAG})"
            )

            await rabbitmq_client.consume_queue(
                queue_name=config.QUEUE_ENVIO_MAG_GEOMETRIA_SEND,
                callback=envio_mag_sender_worker_geometria.process_message,
                prefetch_count=config.PARALLEL_REQUESTS_SEND_MAG
            )
        except KeyboardInterrupt:
            etl_logger.info("Worker envio_mag_geometria_sender detenido por usuario")
            envio_mag_sender_worker_geometria.print_stats()
        except Exception as e:
            etl_logger.error(f"Error en worker envio_mag_geometria_sender: {e}", exc_info=True)
            raise
        finally:
            envio_mag_sender_worker_geometria.print_stats()
            await rabbitmq_client.close()

        return

    # Configuración especial para envio_mag_adicional_sender
    if worker_type == 'envio_mag_adicional_sender':
        from .envio_mag_sender_worker_adicional import envio_mag_sender_worker_adicional

        try:
            etl_logger.info(
                f"Iniciando worker envio_mag_adicional_sender (paralelo: {config.PARALLEL_REQUESTS_SEND_MAG})"
            )

            await rabbitmq_client.consume_queue(
                queue_name=config.QUEUE_ENVIO_MAG_ADICIONAL_SEND,
                callback=envio_mag_sender_worker_adicional.process_message,
                prefetch_count=config.PARALLEL_REQUESTS_SEND_MAG
            )
        except KeyboardInterrupt:
            etl_logger.info("Worker envio_mag_adicional_sender detenido por usuario")
            envio_mag_sender_worker_adicional.print_stats()
        except Exception as e:
            etl_logger.error(f"Error en worker envio_mag_adicional_sender: {e}", exc_info=True)
            raise
        finally:
            envio_mag_sender_worker_adicional.print_stats()
            await rabbitmq_client.close()

        return

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
        print(
            "Worker types: json_save, etl_transform, db_insert, "
            "envio_mag, envio_mag_sender, envio_mag_geometria, "
            "envio_mag_geometria_boleta, envio_mag_geometria_terreno, envio_mag_geometria_sender, "
            "envio_mag_adicional, envio_mag_adicional_capacitacion, "
            "envio_mag_adicional_comunicacion, envio_mag_adicional_produccion, "
            "envio_mag_adicional_sender"
        )
        sys.exit(1)
    
    worker_type = sys.argv[1]
    asyncio.run(run_worker(worker_type))
