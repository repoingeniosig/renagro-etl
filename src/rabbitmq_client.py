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
        Declara todas las colas necesarias con sistema de reintentos
        
        ARQUITECTURA:
        - Colas principales: procesamiento normal
        - Colas .retry: reintentos con TTL (redirecciona a principal)
        - Colas .dlq: errores permanentes (después de MAX_RETRIES)
        """
        # Mapeo de colas principales
        main_queues = [
            config.QUEUE_JSON_SAVE,
            config.QUEUE_ETL_TRANSFORM,
            config.QUEUE_DB_INSERT
        ]
        
        retry_queues = [
            config.QUEUE_JSON_SAVE_RETRY,
            config.QUEUE_ETL_TRANSFORM_RETRY,
            config.QUEUE_DB_INSERT_RETRY
        ]
        
        dlq_queues = [
            config.QUEUE_JSON_SAVE_DLQ,
            config.QUEUE_ETL_TRANSFORM_DLQ,
            config.QUEUE_DB_INSERT_DLQ
        ]
        
        # 1. Declarar Dead Letter Queues (sin TTL, sin DLX)
        for dlq_name in dlq_queues:
            await channel.declare_queue(
                dlq_name,
                durable=True,
                arguments={'x-max-priority': 10}
            )
            etl_logger.info(f"DLQ declarada: {dlq_name}")
        
        # 2. Declarar colas de reintentos (con TTL dinámico y DLX a cola principal)
        for retry_name, main_name in zip(retry_queues, main_queues):
            await channel.declare_queue(
                retry_name,
                durable=True,
                arguments={
                    'x-max-priority': 10,
                    # Sin TTL aquí - se establece por mensaje
                    # DLX redirige a cola principal cuando expira
                    'x-dead-letter-exchange': '',
                    'x-dead-letter-routing-key': main_name
                }
            )
            etl_logger.info(f"Cola retry declarada: {retry_name} -> {main_name}")
        
        # 3. Declarar colas principales
        for queue_name in main_queues:
            await channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    'x-max-priority': 10,
                    'x-message-ttl': 3600000  # 1 hora timeout general
                }
            )
            etl_logger.info(f"Cola principal declarada: {queue_name}")
    
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
    
    async def publish_to_retry(
        self,
        retry_queue: str,
        message: Dict[str, Any],
        retry_count: int,
        error_msg: str,
        priority: int = 5
    ) -> bool:
        """
        Publica mensaje a cola de reintentos con TTL exponencial
        
        Args:
            retry_queue: Cola .retry destino
            message: Mensaje original
            retry_count: Número de reintentos actual
            error_msg: Mensaje del último error
            priority: Prioridad
            
        Returns:
            True si se publicó exitosamente
        """
        try:
            # Backoff exponencial: 2^retry_count segundos -> milisegundos
            delay_seconds = 2 ** retry_count
            ttl_ms = delay_seconds * 1000
            
            async with self._connection_pool.acquire() as connection:
                async with connection.channel() as channel:
                    message_body = json.dumps(message).encode()
                    
                    msg = Message(
                        message_body,
                        delivery_mode=DeliveryMode.PERSISTENT,
                        priority=priority,
                        content_type='application/json',
                        headers={
                            'x-retry-count': retry_count,
                            'x-last-error': error_msg[:500],  # Limitar tamaño
                            'x-retry-timestamp': asyncio.get_event_loop().time()
                        },
                        expiration=str(ttl_ms)  # TTL en milisegundos (como string)
                    )
                    
                    await channel.default_exchange.publish(
                        msg,
                        routing_key=retry_queue
                    )
                    
                    etl_logger.info(
                        f"Mensaje enviado a retry {retry_queue}: "
                        f"_id={message.get('_id')} retry={retry_count} delay={delay_seconds}s"
                    )
                    return True
        
        except Exception as e:
            etl_logger.error(f"Error publicando a retry {retry_queue}: {e}", exc_info=True)
            return False
    
    async def publish_to_dlq(
        self,
        dlq_queue: str,
        _id: int,
        error_msg: str,
        original_queue: str,
        retry_count: int
    ) -> bool:
        """
        Publica mensaje a Dead Letter Queue con metadata reducida
        Solo guarda _id para ahorrar memoria
        
        Args:
            dlq_queue: Cola DLQ destino
            _id: ID del registro
            error_msg: Mensaje de error final
            original_queue: Cola de origen
            retry_count: Número de reintentos realizados
            
        Returns:
            True si se publicó exitosamente
        """
        try:
            async with self._connection_pool.acquire() as connection:
                async with connection.channel() as channel:
                    # Solo metadata, no JSON completo
                    dlq_message = {
                        '_id': _id,
                        'error': error_msg[:1000],  # Limitar tamaño
                        'original_queue': original_queue,
                        'retry_count': retry_count,
                        'timestamp': asyncio.get_event_loop().time()
                    }
                    
                    message_body = json.dumps(dlq_message).encode()
                    
                    msg = Message(
                        message_body,
                        delivery_mode=DeliveryMode.PERSISTENT,
                        content_type='application/json'
                    )
                    
                    await channel.default_exchange.publish(
                        msg,
                        routing_key=dlq_queue
                    )
                    
                    etl_logger.error(
                        f"Mensaje enviado a DLQ {dlq_queue}: "
                        f"_id={_id} retry_count={retry_count}"
                    )
                    return True
        
        except Exception as e:
            etl_logger.error(f"Error publicando a DLQ {dlq_queue}: {e}", exc_info=True)
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
