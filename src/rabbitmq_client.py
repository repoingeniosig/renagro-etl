"""
Cliente RabbitMQ para gestión de colas de mensajes
Pipeline asíncrono ETL con 3 colas:
1. json_save - Guardar JSON en BD
2. etl_transform - Transformar y generar SQL
3. db_insert - Ejecutar transacción
"""
import json
import asyncio
from typing import Dict, Any, Optional, Callable
from aio_pika import connect_robust, Message, DeliveryMode, Connection, Channel
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool

from .config import config
from .logger import etl_logger


class RabbitMQClient:
    """Cliente singleton para RabbitMQ con pools de conexión"""
    
    _instance = None
    _connection_pool: Optional[Pool] = None
    _channel_pool: Optional[Pool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RabbitMQClient, cls).__new__(cls)
        return cls._instance
    
    async def get_connection(self) -> AbstractRobustConnection:
        """Obtiene una conexión de RabbitMQ"""
        connection_url = (
            f"amqp://{config.RABBITMQ_USER}:{config.RABBITMQ_PASSWORD}"
            f"@{config.RABBITMQ_HOST}:{config.RABBITMQ_PORT}{config.RABBITMQ_VHOST}"
        )
        
        return await connect_robust(connection_url)
    
    async def get_channel(self) -> Channel:
        """Obtiene un canal del pool"""
        if self._connection_pool is None:
            self._connection_pool = Pool(self.get_connection, max_size=10)
        
        async def get_channel():
            async with self._connection_pool.acquire() as connection:
                return await connection.channel()
        
        if self._channel_pool is None:
            self._channel_pool = Pool(get_channel, max_size=20)
        
        async with self._channel_pool.acquire() as channel:
            return channel
    
    async def declare_queues(self, channel: Channel):
        """
        Declara todas las colas necesarias
        Las colas son durables para persistir mensajes
        """
        queues = [
            config.QUEUE_JSON_SAVE,
            config.QUEUE_ETL_TRANSFORM,
            config.QUEUE_DB_INSERT
        ]
        
        for queue_name in queues:
            queue = await channel.declare_queue(
                queue_name,
                durable=True,  # Cola persiste después de reinicio
                arguments={
                    'x-max-priority': 10,  # Soporte de prioridades
                    'x-message-ttl': 3600000  # TTL de 1 hora (milisegundos)
                }
            )
            etl_logger.info(f"Cola declarada: {queue_name}")
    
    async def publish_message(
        self,
        queue_name: str,
        message: Dict[str, Any],
        priority: int = 5
    ) -> bool:
        """
        Publica un mensaje a una cola
        
        Args:
            queue_name: Nombre de la cola
            message: Diccionario con el mensaje (se serializa a JSON)
            priority: Prioridad del mensaje (0-10, mayor es más prioritario)
            
        Returns:
            True si se publicó exitosamente
        """
        try:
            async with self._connection_pool.acquire() as connection:
                async with connection.channel() as channel:
                    # Serializar mensaje a JSON
                    message_body = json.dumps(message).encode()
                    
                    # Crear mensaje con propiedades
                    msg = Message(
                        message_body,
                        delivery_mode=DeliveryMode.PERSISTENT,  # Persistir mensaje en disco
                        priority=priority,
                        content_type='application/json'
                    )
                    
                    # Publicar a la cola
                    await channel.default_exchange.publish(
                        msg,
                        routing_key=queue_name
                    )
                    
                    etl_logger.debug(f"Mensaje publicado a {queue_name}: _id={message.get('_id', 'unknown')}")
                    return True
        
        except Exception as e:
            etl_logger.error(f"Error publicando mensaje a {queue_name}: {e}", exc_info=True)
            return False
    
    async def consume_queue(
        self,
        queue_name: str,
        callback: Callable,
        prefetch_count: int = 10
    ):
        """
        Consume mensajes de una cola
        
        Args:
            queue_name: Nombre de la cola
            callback: Función async que procesa cada mensaje
            prefetch_count: Cantidad de mensajes a prefetch
        """
        try:
            connection = await self.get_connection()
            channel = await connection.channel()
            
            # Configurar QoS - cuántos mensajes procesar a la vez
            await channel.set_qos(prefetch_count=prefetch_count)
            
            # Declarar cola (idempotente)
            queue = await channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    'x-max-priority': 10,
                    'x-message-ttl': 3600000
                }
            )
            
            etl_logger.info(f"Consumidor iniciado para cola: {queue_name}")
            
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            # Deserializar mensaje
                            data = json.loads(message.body.decode())
                            
                            etl_logger.debug(f"Mensaje recibido de {queue_name}: {data.get('_id', 'unknown')}")
                            
                            # Procesar mensaje
                            await callback(data)
                            
                            # ACK automático al salir del context manager
                        
                        except json.JSONDecodeError as e:
                            etl_logger.error(f"Error decodificando mensaje: {e}", exc_info=True)
                            # NACK - rechazar mensaje (no reencolar si es inválido)
                        
                        except Exception as e:
                            etl_logger.error(f"Error procesando mensaje: {e}", exc_info=True)
                            # El mensaje se reintentará automáticamente
        
        except Exception as e:
            etl_logger.error(f"Error en consumidor de {queue_name}: {e}", exc_info=True)
            raise
    
    async def close(self):
        """Cierra los pools de conexión"""
        if self._channel_pool:
            await self._channel_pool.close()
        if self._connection_pool:
            await self._connection_pool.close()
        
        etl_logger.info("Conexiones RabbitMQ cerradas")


# Instancia global
rabbitmq_client = RabbitMQClient()
