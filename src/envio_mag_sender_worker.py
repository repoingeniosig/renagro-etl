"""
Worker para envío de JSONs a API remota RENAGRO
Consume cola QUEUE_ENVIO_MAG_SEND y envía con paralelismo controlado
"""
import asyncio
from typing import Dict, Any
from sqlalchemy import text

from .config import config
from .logger import envio_mag_logger
from .database import db
from .api_sender_envio_mag import api_sender_envio_mag
from .rabbitmq_client import rabbitmq_client


class EnvioMagSenderWorker:
    """
    Worker para envío paralelo de JSONs a API remota
    
    Arquitectura:
    1. Consume cola QUEUE_ENVIO_MAG_SEND
    2. Envía JSONs en paralelo (hasta PARALLEL_REQUESTS_SEND_MAG simultáneos)
    3. Actualiza estado en control_table según respuesta HTTP
    4. Reintentos automáticos para errores 5xx vía APISenderEnvioMAG
    """
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(config.PARALLEL_REQUESTS_SEND_MAG)
        self.stats = {
            'total_processed': 0,
            'success': 0,
            'error_4xx': 0,
            'error_5xx': 0,
            'error_network': 0
        }
    
    async def update_control_status(
        self,
        control_table: str,
        control_id_column: str,
        control_id: int,
        status: str,
        error_message: str = None
    ):
        """
        Actualiza el estado de un registro en la tabla de control
        
        Args:
            control_table: Nombre de la tabla de control
            control_id_column: Nombre de la columna ID
            control_id: Valor del ID
            status: Estado a establecer ('ENTREGANDO', 'ENVIADO', 'ERROR')
            error_message: Mensaje de error (solo para status='ERROR')
        """
        try:
            # Construir UPDATE dinámico
            if status == 'ERROR' and error_message:
                update_query = f"""
                    UPDATE "{config.DB_SCHEMA}".{control_table}
                    SET 
                        envio_datos_procesados = :status,
                        error_envio_datos = :error_message
                    WHERE {control_id_column} = :control_id
                """
                params = {
                    'status': status,
                    'error_message': error_message[:500],  # Limitar longitud
                    'control_id': control_id
                }
            else:
                update_query = f"""
                    UPDATE "{config.DB_SCHEMA}".{control_table}
                    SET envio_datos_procesados = :status
                    WHERE {control_id_column} = :control_id
                """
                params = {
                    'status': status,
                    'control_id': control_id
                }
            
            with db.get_session() as session:
                session.execute(text(update_query), params)
                session.commit()
            
            if config.DEBUG_CLI:
                envio_mag_logger.debug(
                    f"[EnvioMagSenderWorker] Estado actualizado: "
                    f"{control_table}.{control_id_column}={control_id} -> {status}"
                )
        
        except Exception as e:
            envio_mag_logger.error(
                f"[EnvioMagSenderWorker] Error actualizando estado: {e}",
                exc_info=True
            )
    
    async def send_json_task(self, message: Dict[str, Any]):
        """
        Envía un JSON a la API remota (con control de semáforo)
        
        Args:
            message: Mensaje de la cola con estructura:
                - control_id: ID en tabla de control
                - record_id: ID del registro principal
                - json_data: JSON a enviar
                - control_table: Nombre tabla de control
                - control_id_column: Nombre columna ID
        """
        async with self.semaphore:
            control_id = message.get('control_id')
            record_id = message.get('record_id')
            json_data = message.get('json_data')
            control_table = message.get('control_table')
            control_id_column = message.get('control_id_column')
            
            try:
                # Marcar como ENTREGANDO antes de enviar
                await self.update_control_status(
                    control_table=control_table,
                    control_id_column=control_id_column,
                    control_id=control_id,
                    status='ENTREGANDO'
                )
                
                # Enviar JSON a API remota (con reintentos internos)
                success, status_code, error_msg = await api_sender_envio_mag.send_json(
                    json_data=json_data,
                    control_id=control_id,
                    record_id=record_id
                )
                
                # Actualizar estado según resultado
                if success:
                    # Envío exitoso (201)
                    await self.update_control_status(
                        control_table=control_table,
                        control_id_column=control_id_column,
                        control_id=control_id,
                        status='ENVIADO'
                    )
                    
                    self.stats['success'] += 1
                    
                    envio_mag_logger.info(
                        f"[EnvioMagSenderWorker] ✅ Enviado: control_id={control_id}"
                    )
                
                else:
                    # Error después de reintentos
                    await self.update_control_status(
                        control_table=control_table,
                        control_id_column=control_id_column,
                        control_id=control_id,
                        status='ERROR',
                        error_message=error_msg
                    )
                    
                    # Clasificar tipo de error para estadísticas
                    if status_code and 400 <= status_code < 500:
                        self.stats['error_4xx'] += 1
                    elif status_code and status_code >= 500:
                        self.stats['error_5xx'] += 1
                    else:
                        self.stats['error_network'] += 1
                    
                    envio_mag_logger.error(
                        f"[EnvioMagSenderWorker] ❌ Error enviando: "
                        f"control_id={control_id}, status={status_code}, error={error_msg}"
                    )
            
            except Exception as e:
                # Error inesperado
                envio_mag_logger.error(
                    f"[EnvioMagSenderWorker] Error inesperado: control_id={control_id}, {e}",
                    exc_info=True
                )
                
                # Marcar como ERROR
                await self.update_control_status(
                    control_table=control_table,
                    control_id_column=control_id_column,
                    control_id=control_id,
                    status='ERROR',
                    error_message=f"Error inesperado: {str(e)[:200]}"
                )
                
                self.stats['error_network'] += 1
            
            finally:
                self.stats['total_processed'] += 1
    
    async def process_message(self, data: Dict[str, Any]):
        """
        Callback para procesar mensaje de la cola
        
        Args:
            data: Mensaje de RabbitMQ
        """
        await self.send_json_task(data)
    
    def print_stats(self):
        """Imprime estadísticas de envío"""
        envio_mag_logger.info("=" * 80)
        envio_mag_logger.info("ESTADÍSTICAS DE ENVÍO")
        envio_mag_logger.info("=" * 80)
        envio_mag_logger.info(f"Total procesado: {self.stats['total_processed']}")
        envio_mag_logger.info(f"✅ Enviados exitosamente: {self.stats['success']}")
        envio_mag_logger.info(f"❌ Errores 4xx (cliente): {self.stats['error_4xx']}")
        envio_mag_logger.info(f"❌ Errores 5xx (servidor): {self.stats['error_5xx']}")
        envio_mag_logger.info(f"❌ Errores de red: {self.stats['error_network']}")
        envio_mag_logger.info("=" * 80)


# Instancia global
envio_mag_sender_worker = EnvioMagSenderWorker()
