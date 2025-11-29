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
from .models import ControlEnviosBoletas, EstadoETLEnum, EstadoEnvioEnum
from .rabbitmq_client import rabbitmq_client
from .mapping_loader import mapping_loader
from .transformer import JSONTransformer
from .executor import TransactionExecutor
from datetime import datetime


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
        
        try:
            etl_logger.info(f"[json_save] Procesando _id={_id}")
            
            # Validar campos requeridos
            if not _id:
                raise ValueError("El JSON no contiene el campo '_id'")
            
            # Guardar en tabla de control
            with db.get_session() as session:
                # Verificar si ya existe (rechazo de duplicados)
                existing = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
                
                if existing:
                    error_msg = f"Registro duplicado: _id={_id} ya existe"
                    etl_logger.warning(f"[json_save] {error_msg}")
                    
                    # Actualizar estado a ERROR
                    existing.estado_etl = EstadoETLEnum.ERROR
                    existing.error_message = error_msg
                    session.commit()
                    
                    return  # No continuar el pipeline
                
                # Crear nuevo registro
                registro = ControlEnviosBoletas(
                    _id=_id,
                    json_data=data,
                    estado_etl=EstadoETLEnum.PENDIENTE,
                    envio_datos_procesados=EstadoEnvioEnum.PENDIENTE
                )
                
                session.add(registro)
                session.commit()
                
                etl_logger.info(f"[json_save] JSON guardado _id={_id}")
            
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
            
            # Actualizar estado a ERROR en BD
            try:
                with db.get_session() as session:
                    control = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
                    if control:
                        control.estado_etl = EstadoETLEnum.ERROR
                        control.error_message = error_msg
                        session.commit()
            except Exception as db_error:
                etl_logger.error(f"[json_save] Error actualizando estado: {db_error}")
            
            # Re-raise para que RabbitMQ reintente
            raise


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
            
            # Cargar mapeos (deberían estar en cache)
            if not mapping_loader.entity_mappings:
                mapping_loader.load_master()
                mapping_loader.load_all_mappings(force_reload=False)
            
            processing_order = mapping_loader.get_processing_order()
            
            # Transformar datos según mapeos
            transformations = {}
            
            for group in processing_order:
                for entity_name in group:
                    if entity_name not in mapping_loader.entity_mappings:
                        continue
                    
                    entity_mapping = mapping_loader.entity_mappings[entity_name]
                    
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
                
                # Actualizar estado a PROCESADO (sin datos)
                with db.get_session() as session:
                    control = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
                    if control:
                        control.estado_etl = EstadoETLEnum.PROCESADO
                        control.procesado_at = datetime.now()
                        session.commit()
                
                return  # No continuar pipeline
            
            etl_logger.info(f"[etl_transform] _id={_id} - {len(transformations)} entidades transformadas")
            
            # Preparar mensaje para siguiente cola
            transform_message = {
                '_id': _id,
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
            
            # Actualizar estado a ERROR
            try:
                with db.get_session() as session:
                    control = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
                    if control:
                        control.estado_etl = EstadoETLEnum.ERROR
                        control.error_message = error_msg
                        session.commit()
            except Exception as db_error:
                etl_logger.error(f"[etl_transform] Error actualizando estado: {db_error}")
            
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
        transformations = data.get('transformations', {})
        processing_order = data.get('processing_order', [])
        
        try:
            etl_logger.info(f"[db_insert] Procesando _id={_id}")
            
            # Ejecutar transacción
            # Nota: execute_inserts es síncrono, lo ejecutamos en thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                TransactionExecutor.execute_inserts,
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
            
            # Actualizar estado a ERROR
            try:
                with db.get_session() as session:
                    control = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
                    if control:
                        control.estado_etl = EstadoETLEnum.ERROR
                        control.error_message = error_msg
                        session.commit()
            except Exception as db_error:
                etl_logger.error(f"[db_insert] Error actualizando estado: {db_error}")
            
            raise


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
