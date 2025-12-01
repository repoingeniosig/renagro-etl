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
    """Cargador de archivos YAML de mapeo con soporte multi-formulario"""
    
    def __init__(self, mapping_dir: Path = None):
        self.mapping_dir = mapping_dir or config.MAPPING_DIR
        self.master_config = None
        self.entity_mappings: Dict[str, EntityMapping] = {}
        
        # Multi-formulario: {form_uuid: {entity: EntityMapping}}
        self.form_mappings: Dict[str, Dict[str, EntityMapping]] = {}
        self.form_processing_orders: Dict[str, List[List[str]]] = {}
    
    def load_master(self) -> Dict[str, str]:
        """
        Carga el archivo master.yml que contiene las referencias a todos los mapeos
        Retorna un diccionario con el orden de procesamiento
        """
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
    
    def load_all_mappings(self, force_reload: bool = False) -> Dict[str, EntityMapping]:
        """
        Carga todos los mapeos definidos en master.yml
        Intenta primero desde Redis cache, si falla lee desde disco
        
        Args:
            force_reload: Si True, ignora el cache y recarga desde disco
        
        Returns:
            Diccionario con los mapeos por entidad
        """
        # Intentar cargar desde Redis cache primero
        if not force_reload:
            try:
                from .redis_client import redis_client
                
                if config.DEBUG_CLI:
                    console.print("🔍 Intentando cargar mapeos desde Redis cache...")
                
                cached_mappings = redis_client.get_cached_mappings()
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
                
                success = redis_client.set_cached_mappings(self.entity_mappings)
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
    
    def get_processing_order(self, form_uuid: str = None) -> List[List[str]]:
        """
        Retorna el orden de procesamiento de las entidades en grupos
        
        Args:
            form_uuid: UUID del formulario (opcional, usa default si no se provee)
        
        Returns:
            Lista de listas de nombres de entidades
        """
        if form_uuid and form_uuid in self.form_processing_orders:
            return self.form_processing_orders[form_uuid]
        
        # Fallback: orden por defecto
        return [
            ['bovinos', 'pecuario_otros', 'pollos', 'porcinos', 'personas'],
            ['boletas'],
            ['miembros_hogar', 'terrenos'],
            ['cultivos', 'forestales']
        ]
    
    def load_form_mappings(self, form_uuid: str, mapping_path: Path, force_reload: bool = False):
        """
        Carga mapeos para un formulario específico
        Primero intenta cargar desde Redis, luego desde disco
        
        Args:
            form_uuid: UUID del formulario
            mapping_path: Ruta al directorio de mapeos
            force_reload: Forzar recarga desde disco ignorando cache
        """
        # Intentar cargar desde Redis si está habilitado
        if not force_reload:
            from .redis_client import redis_client
            
            cached_mappings = redis_client.get_form_mappings(form_uuid)
            if cached_mappings:
                self.form_mappings[form_uuid] = cached_mappings.get('entity_mappings', {})
                self.form_processing_orders[form_uuid] = cached_mappings.get('processing_order', [])
                etl_logger.info(f"Formulario {form_uuid}: {len(self.form_mappings[form_uuid])} entidades desde Redis")
                return
        
        # Cargar desde disco
        etl_logger.info(f"Cargando mapeos para formulario {form_uuid} desde {mapping_path}")
        
        # Cargar master.yml
        master_file = mapping_path / "master.yml"
        if not master_file.exists():
            raise FileNotFoundError(f"master.yml no encontrado en {mapping_path}")
        
        with open(master_file, 'r', encoding='utf-8') as f:
            master_data = yaml.safe_load(f)
        
        # Extraer orden de procesamiento (formato nuevo con processing_order)
        processing_order = []
        if 'processing_order' in master_data:
            for group in master_data.get('processing_order', []):
                entities = group.get('entities', [])
                if entities:
                    processing_order.append(entities)
        else:
            # Formato legacy: el master.yml es un dict simple {entity: file.yaml}
            # No hay orden específico, solo cargar todas las entidades
            processing_order = []
        
        self.form_processing_orders[form_uuid] = processing_order
        
        # Cargar todos los YAMLs de entidades
        entity_mappings = {}
        yaml_files = list(mapping_path.glob("*.yaml"))
        
        for yaml_file in yaml_files:
            if yaml_file.name == 'master.yml':
                continue
            
            try:
                # Cargar directamente desde la ruta absoluta
                if not yaml_file.exists():
                    raise FileNotFoundError(f"Archivo de mapeo no encontrado: {yaml_file}")
                
                with open(yaml_file, 'r', encoding='utf-8') as f:
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
                
                mapping = EntityMapping(
                    version=data.get('version', '1.0'),
                    entity=data.get('entity'),
                    table=data.get('table'),
                    fields=fields,
                    conversions=data.get('conversions'),
                    repeat=data.get('repeat'),
                    parent_key=data.get('parent_key'),
                    raw_data=data
                )
                
                entity_mappings[mapping.entity] = mapping
                etl_logger.debug(f"  - {mapping.entity} cargado")
            except Exception as e:
                etl_logger.error(f"Error cargando {yaml_file.name}: {e}")
        
        self.form_mappings[form_uuid] = entity_mappings
        etl_logger.info(f"Formulario {form_uuid}: {len(entity_mappings)} entidades cargadas desde disco")
        
        # Guardar en Redis (convertir EntityMapping a dict para serialización)
        from .redis_client import redis_client
        cache_data = {
            'entity_mappings': entity_mappings,  # Redis client manejará la serialización
            'processing_order': processing_order
        }
        redis_client.set_form_mappings(form_uuid, cache_data)
    
    def get_form_mappings(self, form_uuid: str) -> Dict[str, EntityMapping]:
        """
        Obtiene los mapeos de un formulario específico
        
        Args:
            form_uuid: UUID del formulario
            
        Returns:
            Diccionario {entity_name: EntityMapping}
        """
        return self.form_mappings.get(form_uuid, {})
    
    def set_active_form(self, form_uuid: str):
        """
        Establece un formulario como activo (para retrocompatibilidad)
        
        Args:
            form_uuid: UUID del formulario
        """
        if form_uuid in self.form_mappings:
            self.entity_mappings = self.form_mappings[form_uuid]
            etl_logger.info(f"Formulario activo: {form_uuid}")


# Instancia global del cargador
mapping_loader = MappingLoader()
