"""
Cargador de archivos YAML de mapeo
Soporta cache en Redis para optimizar el rendimiento
"""
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from rich.console import Console

from .config import config
from .logger import etl_logger

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class FieldMapping:
    """Mapeo de un campo individual"""
    source: str  # Ruta en el JSON (dot notation)
    type: str  # integer, decimal, boolean, string
    default: Any = None
    convert: Optional[Dict[str, Any]] = None
    repeat_filter: Optional[Dict[str, Any]] = None  # Filtro para repeat groups
    extract: Optional[str] = None  # Campo a extraer del repeat filtrado
    parent_key: Optional[str] = None  # Clave del padre para FKs
    

@dataclass
class EntityMapping:
    """Mapeo de una entidad completa"""
    version: str
    entity: str
    table: str
    fields: Dict[str, FieldMapping]
    conversions: Optional[Dict[str, Dict[str, Any]]] = None
    repeat: Optional[str] = None  # Ruta al grupo repetido
    parent_key: Optional[str] = None  # Nombre del campo FK al padre
    repeat: Optional[Dict[str, str]] = None  # {source: "ruta.al.array"}
    parent_key: Optional[Dict[str, str]] = None  # {field: "nombre_campo_fk"}
    raw_data: Optional[Dict[str, Any]] = None  # Diccionario raw del YAML para parent_keys


class MappingLoader:
    """Cargador de archivos YAML de mapeo - soporta subdirectorios dinámicos"""
    
    def __init__(self, mapping_dir: Path = None, form_mapping_dir: str = None):
        """
        Args:
            mapping_dir: Directorio base de mappings (por defecto config.BASE_DIR / 'mappings')
            form_mapping_dir: Subdirectorio específico del formulario (ej: 'boletas', 'boletas-procesos')
        """
        if form_mapping_dir:
            # Usar subdirectorio específico del formulario
            self.mapping_dir = config.BASE_DIR / 'mappings' / form_mapping_dir
        else:
            # Fallback al directorio configurado (legacy)
            self.mapping_dir = mapping_dir or config.MAPPING_DIR
        
        self.master_config = None
        self.entity_mappings: Dict[str, EntityMapping] = {}
        self.cache_prefix = f"etl:{form_mapping_dir}" if form_mapping_dir else "etl"
    
    def set_mapping_dir(self, mapping_dir: Path):
        """Actualiza el directorio de mappings dinámicamente"""
        self.mapping_dir = mapping_dir
        # Actualizar cache prefix basado en el nombre del subdirectorio
        subdir_name = mapping_dir.name
        self.cache_prefix = f"etl:{subdir_name}"
        # Limpiar mapeos cargados previamente
        self.master_config = None
        self.entity_mappings = {}
    
    def load_master(self, mapping_dir: Path = None) -> Dict[str, str]:
        """
        Carga el archivo master.yml que contiene las referencias a todos los mapeos
        
        Args:
            mapping_dir: Directorio opcional para cargar el master.yml (sobrescribe self.mapping_dir temporalmente)
        
        Retorna un diccionario con el orden de procesamiento
        """
        if mapping_dir:
            self.set_mapping_dir(mapping_dir)
        
        master_path = self.mapping_dir / 'master.yml'
        
        if not master_path.exists():
            raise FileNotFoundError(f"Archivo master.yml no encontrado en {self.mapping_dir}")
        
        with open(master_path, 'r', encoding='utf-8') as f:
            self.master_config = yaml.safe_load(f)
        
        return self.master_config
    
    def load_entity_mapping(self, yaml_file: str) -> EntityMapping:
        """
        Carga un archivo YAML de mapeo de una entidad específica
        
        Args:
            yaml_file: Ruta relativa del archivo YAML (ej: "mapping/bovinos.yml")
        
        Returns:
            EntityMapping con la configuración cargada
        """
        # Si la ruta es relativa desde mapping/, construir la ruta completa
        if yaml_file.startswith('mapping/'):
            yaml_path = self.mapping_dir.parent / yaml_file
        else:
            yaml_path = self.mapping_dir / yaml_file
        
        if not yaml_path.exists():
            raise FileNotFoundError(f"Archivo de mapeo no encontrado: {yaml_path}")
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Convertir fields a objetos FieldMapping
        fields = {}
        for field_name, field_config in data.get('fields', {}).items():
            fields[field_name] = FieldMapping(
                source=field_config['source'],
                type=field_config['type'],
                default=field_config.get('default'),
                convert=field_config.get('convert'),
                repeat_filter=field_config.get('repeat_filter'),
                extract=field_config.get('extract'),
                parent_key=field_config.get('parent_key')
            )
        
        entity_mapping = EntityMapping(
            version=data.get('version', '1.0'),
            entity=data.get('entity'),
            table=data.get('table'),
            fields=fields,
            conversions=data.get('conversions'),
            repeat=data.get('repeat'),
            parent_key=data.get('parent_key'),
            raw_data=data  # Guardar el diccionario completo para parent_keys
        )
        
        return entity_mapping
    
    def load_all_mappings(self, force_reload: bool = False, mapping_dir: Path = None) -> Dict[str, EntityMapping]:
        """
        Carga todos los mapeos definidos en master.yml
        Intenta primero desde Redis cache, si falla lee desde disco
        
        Args:
            force_reload: Si True, ignora el cache y recarga desde disco
            mapping_dir: Directorio opcional para cargar los mappings (sobrescribe self.mapping_dir temporalmente)
        
        Returns:
            Diccionario con los mapeos por entidad
        """
        if mapping_dir:
            self.set_mapping_dir(mapping_dir)
        
        # Intentar cargar desde Redis cache primero
        if not force_reload:
            try:
                from .redis_client import redis_client
                
                if config.DEBUG_CLI:
                    console.print("🔍 Intentando cargar mapeos desde Redis cache...")
                
                cached_mappings = redis_client.get_cached_mappings(self.cache_prefix)
                if cached_mappings:
                    self.entity_mappings = cached_mappings
                    return self.entity_mappings
                    
            except ImportError as e:
                etl_logger.debug(f"Redis client no disponible: {e}")
                
                if config.DEBUG_CLI:
                    console.print(f"Redis client no disponible: {e}")
            except Exception as e:
                etl_logger.warning(f"Error accediendo a Redis cache: {e}")
                
                if config.DEBUG_CLI:
                    console.print(f"⚠️  Error accediendo a Redis cache: {e}")
                    console.print("Fallback: cargando mapeos desde disco")
        
        # Fallback: Cargar desde disco
        etl_logger.debug("Cargando mapeos desde archivos YAML...")
        
        if config.DEBUG_CLI:
            console.print("📂 Cargando mapeos desde archivos YAML...")
        
        if not self.master_config:
            self.load_master()
        
        for entity_name, yaml_file in self.master_config.items():
            self.entity_mappings[entity_name] = self.load_entity_mapping(yaml_file)
        
        etl_logger.info(f"{len(self.entity_mappings)} mapeos cargados desde disco")
        
        if config.DEBUG_CLI:
            console.print(f"✅ {len(self.entity_mappings)} mapeos cargados desde disco")
        
        # Intentar guardar en Redis cache para futuras ejecuciones
        if not force_reload:
            try:
                from .redis_client import redis_client
                
                if config.DEBUG_CLI:
                    console.print("💾 Guardando mapeos en Redis cache...")
                
                success = redis_client.set_cached_mappings(self.entity_mappings, self.cache_prefix)
                if not success:
                    if config.DEBUG_CLI:
                        console.print("⚠️  No se pudo guardar en cache, pero el proceso continúa")
            except ImportError:
                if config.DEBUG_CLI:
                    console.print("Redis client no disponible para guardar cache")
            except Exception as e:
                etl_logger.warning(f"No se pudo guardar en cache: {e}")
                
                if config.DEBUG_CLI:
                    console.print(f"⚠️  No se pudo guardar en cache: {e}")
                    console.print("El proceso continuará normalmente")
        
        return self.entity_mappings
    
    def invalidate_cache(self):
        """
        Invalida el cache de Redis
        Útil cuando se actualizan los archivos YAML
        """
        try:
            from .redis_client import redis_client
            redis_client.invalidate_cache()
            logger.info("✅ Cache invalidado, próxima carga será desde disco")
        except ImportError:
            logger.warning("Redis client no disponible")
        except Exception as e:
            logger.error(f"Error invalidando cache: {e}")
    
    def get_processing_order(self) -> List[List[str]]:
        """
        Retorna el orden de procesamiento de las entidades en grupos
        según las dependencias de las llaves foráneas
        
        Returns:
            Lista de listas, donde cada lista interna representa un grupo
            que puede ser procesado en paralelo
        """
        # Orden definido según dependencias de FK
        # IMPORTANTE: Asegurarse de que las entidades en master.yml estén incluidas aquí
        return [
            # Grupo 1: Tablas principales sin dependencias (formulario completo)
            ['bovinos', 'pecuario_otros', 'pollos', 'porcinos', 'personas'],
            # Grupo 2: Boletas (depende de los IDs del grupo 1)
            ['boletas'],
            # Grupo 3: Tablas que dependen de boletas (formulario completo)
            ['miembros_hogar', 'terrenos'],
            # Grupo 4: Tablas que dependen de terrenos (formulario completo)
            ['cultivos', 'forestales'],
            # Grupo 5: Formulario simplificado - Tabla principal
            ['boletas-simplificada'],
            # Grupo 6: Formulario simplificado - Tablas dependientes
            ['terrenos_simplificado']
        ]


# Instancia global del cargador
mapping_loader = MappingLoader()
