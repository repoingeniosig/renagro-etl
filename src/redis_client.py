"""
Cliente Redis para cache de mapeos YAML
Optimiza la carga de mapeos evitando leer del disco en cada procesamiento
"""
import pickle
import logging
from typing import Dict, Optional, Any
import redis
from redis.exceptions import RedisError, ConnectionError
from rich.console import Console

from .config import config
from .logger import etl_logger

console = Console()
logger = logging.getLogger(__name__)


class RedisClient:
    """Cliente singleton para cache de mapeos en Redis"""
    
    _instance = None
    _redis_client = None
    _enabled = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializa la conexión a Redis"""
        if not config.REDIS_ENABLED:
            if config.DEBUG_CLI:
                console.print("Redis cache deshabilitado en configuración")
            etl_logger.info("Redis cache deshabilitado")
            self._enabled = False
            return
        
        try:
            # Crear cliente Redis
            redis_config = {
                'host': config.REDIS_HOST,
                'port': config.REDIS_PORT,
                'db': config.REDIS_DB,
                'decode_responses': False,  # Usamos pickle, necesitamos bytes
                'socket_connect_timeout': 2,
                'socket_timeout': 2,
                'retry_on_timeout': True
            }
            
            if config.REDIS_PASSWORD:
                redis_config['password'] = config.REDIS_PASSWORD
            
            self._redis_client = redis.Redis(**redis_config)
            
            # Verificar conexión
            self._redis_client.ping()
            self._enabled = True
            
            etl_logger.info(f"Redis conectado: {config.REDIS_HOST}:{config.REDIS_PORT}")
            
            if config.DEBUG_CLI:
                console.print(f"✅ Conexión a Redis establecida: {config.REDIS_HOST}:{config.REDIS_PORT}")
            
        except (RedisError, ConnectionError) as e:
            etl_logger.warning(f"No se pudo conectar a Redis: {e}")
            
            if config.DEBUG_CLI:
                console.print(f"⚠️  No se pudo conectar a Redis: {e}")
                console.print("Se usará lectura directa desde disco como fallback")
            
            self._enabled = False
            self._redis_client = None
        except Exception as e:
            etl_logger.error(f"Error inesperado inicializando Redis: {e}", exc_info=True)
            
            if config.DEBUG_CLI:
                console.print(f"❌ Error inesperado inicializando Redis: {e}")
            
            self._enabled = False
            self._redis_client = None
    
    def is_enabled(self) -> bool:
        """Verifica si Redis está habilitado y disponible"""
        return self._enabled and self._redis_client is not None
    
    def get_form_mappings(self, form_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los mapeos de un formulario específico desde Redis
        
        Args:
            form_uuid: UUID del formulario
        
        Returns:
            Diccionario con los mapeos del formulario o None si no existen
        """
        if not self.is_enabled():
            return None
        
        try:
            key = f"renagro:mappings:{form_uuid}"
            cached_data = self._redis_client.get(key)
            
            if cached_data:
                mappings = pickle.loads(cached_data)
                etl_logger.debug(f"Mapeos de {form_uuid} cargados desde Redis ({len(mappings)} entidades)")
                
                if config.DEBUG_CLI:
                    console.print(f"✅ Mapeos de {form_uuid} desde Redis ({len(mappings)} entidades)")
                
                return mappings
            else:
                if config.DEBUG_CLI:
                    console.print(f"ℹ️  No hay mapeos de {form_uuid} en cache")
                return None
        
        except (RedisError, ConnectionError) as e:
            etl_logger.warning(f"Error leyendo cache de {form_uuid}: {e}")
            return None
        except Exception as e:
            etl_logger.error(f"Error inesperado leyendo cache de {form_uuid}: {e}", exc_info=True)
            return None
    
    def set_form_mappings(self, form_uuid: str, mappings: Dict[str, Any]) -> bool:
        """
        Guarda los mapeos de un formulario en cache de Redis
        
        Args:
            form_uuid: UUID del formulario
            mappings: Diccionario con los mapeos
        
        Returns:
            True si se guardó exitosamente
        """
        if not self.is_enabled():
            return False
        
        try:
            key = f"renagro:mappings:{form_uuid}"
            serialized_data = pickle.dumps(mappings)
            
            self._redis_client.setex(
                name=key,
                time=config.REDIS_TTL,
                value=serialized_data
            )
            
            etl_logger.debug(f"Mapeos de {form_uuid} guardados en Redis ({len(mappings)} entidades)")
            
            if config.DEBUG_CLI:
                console.print(f"✅ Mapeos de {form_uuid} guardados en Redis ({len(mappings)} entidades)")
            
            return True
        
        except (RedisError, pickle.PickleError) as e:
            etl_logger.warning(f"Error guardando cache de {form_uuid}: {e}")
            return False
        except Exception as e:
            etl_logger.error(f"Error inesperado guardando cache de {form_uuid}: {e}", exc_info=True)
            return False
    
    def invalidate_form_cache(self, form_uuid: str) -> bool:
        """
        Invalida el cache de un formulario específico
        
        Args:
            form_uuid: UUID del formulario
        
        Returns:
            True si se invalidó exitosamente
        """
        if not self.is_enabled():
            return False
        
        try:
            key = f"renagro:mappings:{form_uuid}"
            result = self._redis_client.delete(key)
            
            etl_logger.info(f"Cache de {form_uuid} invalidado")
            
            if config.DEBUG_CLI:
                console.print(f"✅ Cache de {form_uuid} invalidado")
            
            return result > 0
        
        except (RedisError, ConnectionError) as e:
            etl_logger.warning(f"Error invalidando cache de {form_uuid}: {e}")
            return False
    
    def get_cached_mappings(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene los mapeos cacheados desde Redis
        
        Returns:
            Diccionario con los mapeos o None si no existen/falló
        """
        if not self._enabled or not self._redis_client:
            if config.DEBUG_CLI:
                console.print("Redis no está habilitado, omitiendo cache")
            return None
        
        try:
            key = "renagro:mappings"
            cached_data = self._redis_client.get(key)
            
            if cached_data:
                # Deserializar con pickle
                mappings = pickle.loads(cached_data)
                
                etl_logger.debug(f"Mapeos cargados desde Redis cache ({len(mappings)} entidades)")
                
                if config.DEBUG_CLI:
                    console.print(f"✅ Mapeos cargados desde Redis cache ({len(mappings)} entidades)")
                
                return mappings
            else:
                if config.DEBUG_CLI:
                    console.print("ℹ️  No hay mapeos en cache, se cargarán desde disco")
                return None
        
        except (RedisError, ConnectionError) as e:
            etl_logger.warning(f"Error leyendo cache de Redis: {e}")
            
            if config.DEBUG_CLI:
                console.print(f"⚠️  Error leyendo cache de Redis: {e}")
            
            return None
        except Exception as e:
            etl_logger.error(f"Error inesperado leyendo cache: {e}", exc_info=True)
            
            if config.DEBUG_CLI:
                console.print(f"❌ Error inesperado leyendo cache: {e}")
            
            return None
    
    def set_cached_mappings(self, mappings: Dict[str, Any]) -> bool:
        """
        Guarda los mapeos en cache de Redis
        
        Args:
            mappings: Diccionario con los mapeos a cachear
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        if not self.is_enabled():
            if config.DEBUG_CLI:
                console.print("Redis no disponible, omitiendo guardado en cache")
            return False
        
        try:
            key = "renagro:mappings"
            
            # Serializar con pickle
            serialized_data = pickle.dumps(mappings)
            
            # Guardar en Redis con TTL
            self._redis_client.setex(
                name=key,
                time=config.REDIS_TTL,
                value=serialized_data
            )
            
            etl_logger.debug(f"Mapeos guardados en Redis cache ({len(mappings)} entidades, TTL={config.REDIS_TTL}s)")
            
            if config.DEBUG_CLI:
                console.print(f"✅ Mapeos guardados en Redis cache ({len(mappings)} entidades, TTL={config.REDIS_TTL}s)")
            
            return True
            
        except (RedisError, pickle.PickleError) as e:
            etl_logger.warning(f"Error guardando en cache de Redis: {e}")
            
            if config.DEBUG_CLI:
                console.print(f"⚠️  Error guardando en cache de Redis: {e}")
                console.print("El proceso continuará normalmente usando disco")
            
            return False
        except Exception as e:
            etl_logger.error(f"Error inesperado guardando cache: {e}", exc_info=True)
            
            if config.DEBUG_CLI:
                console.print(f"❌ Error inesperado guardando cache: {e}")
            
            return False
    
    def invalidate_cache(self, form_uuid: Optional[str] = None) -> bool:
        """
        Invalida el cache de mapeos
        
        Args:
            form_uuid: UUID del formulario (None para invalidar todos)
        
        Returns:
            True si se invalidó exitosamente
        """
        if not self.is_enabled():
            etl_logger.debug("Redis no disponible")
            return False
        
        try:
            if form_uuid:
                # Invalidar formulario específico
                return self.invalidate_form_cache(form_uuid)
            else:
                # Invalidar todos los formularios
                pattern = "renagro:mappings:*"
                keys = self._redis_client.keys(pattern)
                
                if keys:
                    result = self._redis_client.delete(*keys)
                    etl_logger.info(f"Cache invalidado: {result} formularios")
                    
                    if config.DEBUG_CLI:
                        console.print(f"✅ Cache invalidado: {result} formularios")
                    
                    return result > 0
                else:
                    etl_logger.info("No hay cache para invalidar")
                    return True
            
            if result > 0:
                etl_logger.info("Cache de mapeos invalidado")
                return True
            else:
                logger.info("ℹ️  No había cache para invalidar")
                return False
                
        except RedisError as e:
            logger.warning(f"⚠️  Error invalidando cache: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado invalidando cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del cache
        
        Returns:
            Diccionario con información sobre el cache
        """
        stats = {
            'enabled': self.is_enabled(),
            'connected': False,
            'has_cache': False,
            'ttl': None
        }
        
        if not self.is_enabled():
            return stats
        
        try:
            # Verificar conexión
            self._redis_client.ping()
            stats['connected'] = True
            
            # Verificar si existe cache
            key = "renagro:mappings"
            stats['has_cache'] = self._redis_client.exists(key) > 0
            
            # Obtener TTL restante
            if stats['has_cache']:
                stats['ttl'] = self._redis_client.ttl(key)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
        
        return stats
    
    def close(self):
        """Cierra la conexión a Redis"""
        if self._redis_client:
            try:
                self._redis_client.close()
                logger.info("Conexión a Redis cerrada")
            except Exception as e:
                logger.error(f"Error cerrando conexión a Redis: {e}")


# Singleton global
redis_client = RedisClient()
