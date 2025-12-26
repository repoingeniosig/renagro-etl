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
    source: Any  # Ruta en el JSON (dot notation) - puede ser str o List[str] para concatenación o dict con 'field' y 'when'
    type: str  # integer, decimal, boolean, string, email, uuid, datetime
    default: Any = None
    convert: Optional[Dict[str, Any]] = None
    repeat_filter: Optional[Dict[str, Any]] = None  # Filtro para repeat groups
    extract: Optional[str] = None  # Campo a extraer del repeat filtrado
    parent_key: Optional[str] = None  # Clave del padre para FKs
    func: Optional[str] = None  # Función a aplicar al valor (upper, lower, etc.)
    apply_uppercase: bool = True  # Si True, aplica uppercase a strings (default: True)
    sanitize: bool = True  # Si True, elimina caracteres especiales de strings (default: True)
    when: Optional[Dict[str, Any]] = None  # Condición para extraer el valor (field, convert, equals)
    

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
            mapping_dir: Directorio completo de mappings (ej: /path/to/mappings/boletas)
            form_mapping_dir: Subdirectorio específico del formulario (ej: 'boletas', 'boletas-procesos')
        """
        if form_mapping_dir:
            # Usar subdirectorio específico del formulario
            self.mapping_dir = config.MAPPINGS_BASE_DIR / form_mapping_dir
        elif mapping_dir:
            # Usar directorio explícito proporcionado
            self.mapping_dir = mapping_dir
        else:
            # Sin directorio por defecto - debe especificarse al cargar
            self.mapping_dir = None
        
        self.master_config = None
        self.entity_mappings: Dict[str, EntityMapping] = {}
        self.cache_prefix = f"etl:{form_mapping_dir}" if form_mapping_dir else "etl"
    
    def set_mapping_dir(self, mapping_dir):
        """Actualiza el directorio de mappings dinámicamente"""
        # Convertir a Path si es string
        from pathlib import Path
        if isinstance(mapping_dir, str):
            mapping_dir = Path(mapping_dir)
        
        # Solo actualizar si cambia el directorio
        subdir_name = mapping_dir.name
        new_cache_prefix = f"etl:{subdir_name}"
        
        if self.mapping_dir != mapping_dir or self.cache_prefix != new_cache_prefix:
            self.mapping_dir = mapping_dir
            self.cache_prefix = new_cache_prefix
            # Solo limpiar si cambiamos de formulario
            self.master_config = None
            self.entity_mappings = {}
    
    def load_master(self, mapping_dir: Path = None) -> Dict[str, str]:
        """
        Carga el archivo master.yml que contiene las referencias a todos los mapeos
        
        Args:
            mapping_dir: Directorio para cargar el master.yml (requerido si no se especificó en __init__)
        
        Retorna un diccionario con el orden de procesamiento
        """
        if mapping_dir:
            self.set_mapping_dir(mapping_dir)
        
        if not self.mapping_dir:
            raise ValueError(
                "No se ha especificado un directorio de mappings. "
                "Proporciona 'mapping_dir' al llamar load_master() o al crear la instancia."
            )
        
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
            # Manejar source como dict (con field y func) o como valor directo
            source_config = field_config['source']
            source_value = source_config
            func_value = None
            when_value = None
            
            # Manejar source como dict con diferentes estructuras
            if isinstance(source_config, dict):
                # Caso 1: Dict con 'field' y 'when' (condicional)
                if 'when' in source_config:
                    # Preservar toda la estructura dict para condicionales
                    source_value = source_config
                    when_value = source_config.get('when')
                # Caso 2: Dict con 'field' y 'func' (función aplicada)
                elif 'field' in source_config and 'func' in source_config:
                    source_value = source_config.get('field')
                    func_value = source_config.get('func')
                # Caso 3: Dict con solo 'field'
                elif 'field' in source_config:
                    source_value = source_config.get('field')
                # Caso 4: Otros casos (mantener el dict completo)
                else:
                    source_value = source_config
            
            fields[field_name] = FieldMapping(
                source=source_value,
                type=field_config['type'],
                default=field_config.get('default'),
                convert=field_config.get('convert'),
                repeat_filter=field_config.get('repeat_filter'),
                extract=field_config.get('extract'),
                parent_key=field_config.get('parent_key'),
                func=func_value,
                apply_uppercase=field_config.get('apply_uppercase', True),  # Default: True
                sanitize=field_config.get('sanitize', True),  # Default: True
                when=when_value
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
            ['miembros_hogar', 'terrenos', 'adjuntos', 'poligonos_boleta'],
            # Grupo 4: Tablas que dependen de terrenos (formulario completo)
            ['cultivos', 'forestales'],
            # Grupo 5: Formulario simplificado - Tabla principal
            ['boletas-simplificada'],
            # Grupo 6: Formulario simplificado - Tablas dependientes
            ['terrenos_simplificado']
        ]


# Instancia global del cargador
mapping_loader = MappingLoader()
