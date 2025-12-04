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
    
    def get_cached_mappings(self, cache_prefix: str = "etl") -> Optional[Dict[str, Any]]:
        """
        Obtiene los mapeos cacheados desde Redis
        
        Args:
            cache_prefix: Prefijo para la clave de cache (etl o envio_mag)
        
        Returns:
            Diccionario con los mapeos o None si no existen/falló
        """
        if not self._enabled or not self._redis_client:
            if config.DEBUG_CLI:
                console.print("Redis no está habilitado, omitiendo cache")
            return None
        
        try:
            key = f"renagro:mappings:{cache_prefix}"
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
    
    def set_cached_mappings(self, mappings: Dict[str, Any], cache_prefix: str = "etl") -> bool:
        """
        Guarda los mapeos en Redis cache
        
        Args:
            mappings: Diccionario con los mapeos a cachear
            cache_prefix: Prefijo para la clave de cache (etl o envio_mag)
        
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        if not self._enabled or not self._redis_client:
            return False
        
        try:
            key = f"renagro:mappings:{cache_prefix}"
            
            # Serializar con pickle
            cached_data = pickle.dumps(mappings)
            
            # Guardar con TTL
            self._redis_client.setex(
                name=key,
                time=config.REDIS_TTL,
                value=cached_data
            )
            
            etl_logger.debug(f"Mapeos guardados en Redis cache ({len(mappings)} entidades, TTL={config.REDIS_TTL}s)")
            
            if config.DEBUG_CLI:
                console.print(f"✅ Mapeos guardados en Redis cache ({len(mappings)} entidades, TTL={config.REDIS_TTL}s)")
            
            return True
            
        except (RedisError, ConnectionError) as e:
            etl_logger.warning(f"Error guardando cache en Redis: {e}")
            
            if config.DEBUG_CLI:
                console.print(f"⚠️  Error guardando cache en Redis: {e}")
            
            return False
        except Exception as e:
            etl_logger.error(f"Error inesperado guardando cache: {e}", exc_info=True)
            
            if config.DEBUG_CLI:
                console.print(f"❌ Error inesperado guardando cache: {e}")
            
            return False
    
    def invalidate_cache(self, cache_prefix: str = None) -> bool:
        """
        Invalida el cache de mapeos en Redis
        
        Args:
            cache_prefix: Prefijo específico a invalidar (etl, envio_mag) o None para todos
        
        Returns:
            True si se invalidó exitosamente
        """
        if not self.is_enabled():
            etl_logger.debug("Redis no disponible")
            return False
        
        try:
            deleted = 0
            
            if cache_prefix:
                # Invalidar solo el cache específico
                key = f"renagro:mappings:{cache_prefix}"
                deleted = self._redis_client.delete(key)
            else:
                # Invalidar todos los caches de mapeos
                for prefix in ['etl', 'envio_mag']:
                    key = f"renagro:mappings:{prefix}"
                    deleted += self._redis_client.delete(key)
            
            if deleted > 0:
                etl_logger.info(f"Cache de mapeos invalidado ({deleted} claves eliminadas)")
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
    
    def get_stats(self, cache_prefix: str = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas del cache
        
        Args:
            cache_prefix: Prefijo específico (etl, envio_mag) o None para todos
        
        Returns:
            Diccionario con información sobre el cache
        """
        stats = {
            'enabled': self.is_enabled(),
            'connected': False,
            'caches': {}
        }
        
        if not self.is_enabled():
            return stats
        
        try:
            # Verificar conexión
            self._redis_client.ping()
            stats['connected'] = True
            
            # Obtener stats para cada prefijo
            prefixes = [cache_prefix] if cache_prefix else ['etl', 'envio_mag']
            
            for prefix in prefixes:
                key = f"renagro:mappings:{prefix}"
                exists = self._redis_client.exists(key) > 0
                
                stats['caches'][prefix] = {
                    'has_cache': exists,
                    'ttl': self._redis_client.ttl(key) if exists else None
                }
            
            # Compatibilidad con código antiguo
            if 'etl' in stats['caches']:
                stats['has_cache'] = stats['caches']['etl']['has_cache']
                stats['ttl'] = stats['caches']['etl']['ttl']
            
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
