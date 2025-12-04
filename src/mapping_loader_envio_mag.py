"""
Cargador de archivos YAML de mapeo para envío a MAG
Lee los archivos YAML desde mappings-envio-mag que definen cómo extraer datos de BD
"""
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .config import config
from .logger import etl_logger


@dataclass
class FieldMappingEnvioMAG:
    """Mapeo de un campo para envío a MAG"""
    source: str  # Campo en la tabla de BD
    type: str  # integer, float, string, boolean
    default: Any = None
    convert: Optional[Dict[str, Any]] = None
    reference: Optional[str] = None  # Archivo YAML referenciado para objetos/arrays


@dataclass
class EntityMappingEnvioMAG:
    """Mapeo de una entidad para envío a MAG"""
    version: str
    entity: str
    table: str
    fields: Dict[str, FieldMappingEnvioMAG]
    raw_data: Dict[str, Any] = None  # Datos raw del YAML


class MappingLoaderEnvioMAG:
    """Cargador de archivos YAML de mapeo para envío a MAG"""
    
    def __init__(self, mapping_dir: Path = None):
        self.mapping_dir = mapping_dir or config.MAPPING_ENVIO_MAG_DIR
        self.loaded_mappings: Dict[str, EntityMappingEnvioMAG] = {}
    
    def load_yaml_file(self, yaml_file: str) -> EntityMappingEnvioMAG:
        """
        Carga un archivo YAML de mapeo
        
        Args:
            yaml_file: Nombre del archivo YAML (ej: "main.yml", "terreno.yaml")
        
        Returns:
            EntityMappingEnvioMAG con la configuración cargada
        """
        # Verificar si ya está cargado en caché
        if yaml_file in self.loaded_mappings:
            if config.DEBUG_CLI:
                etl_logger.debug(f"[MappingLoaderEnvioMAG] Usando caché para {yaml_file}")
            return self.loaded_mappings[yaml_file]
        
        yaml_path = self.mapping_dir / yaml_file
        
        if not yaml_path.exists():
            raise FileNotFoundError(f"Archivo de mapeo no encontrado: {yaml_path}")
        
        if config.DEBUG_CLI:
            etl_logger.debug(f"[MappingLoaderEnvioMAG] Cargando {yaml_file}")
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Convertir fields a objetos FieldMappingEnvioMAG
        fields = {}
        for field_name, field_config in data.get('fields', {}).items():
            fields[field_name] = FieldMappingEnvioMAG(
                source=field_config.get('source'),
                type=field_config.get('type', 'string'),
                default=field_config.get('default'),
                convert=field_config.get('convert'),
                reference=field_config.get('reference')
            )
        
        entity_mapping = EntityMappingEnvioMAG(
            version=data.get('version', '1.0'),
            entity=data.get('entity', ''),
            table=data.get('table', ''),
            fields=fields,
            raw_data=data
        )
        
        # Guardar en caché
        self.loaded_mappings[yaml_file] = entity_mapping
        
        return entity_mapping
    
    def load_main_mapping(self) -> EntityMappingEnvioMAG:
        """
        Carga el archivo main.yml que es el punto de entrada principal
        
        Returns:
            EntityMappingEnvioMAG del archivo main.yml
        """
        return self.load_yaml_file('main.yml')
    
    def get_referenced_mappings(self, entity_mapping: EntityMappingEnvioMAG) -> List[str]:
        """
        Obtiene la lista de archivos YAML referenciados en un mapeo
        
        Args:
            entity_mapping: Mapeo de entidad a analizar
        
        Returns:
            Lista de nombres de archivos YAML referenciados
        """
        references = []
        for field_name, field_mapping in entity_mapping.fields.items():
            if field_mapping.reference:
                references.append(field_mapping.reference)
        return references
    
    def load_all_mappings_recursive(self, start_file: str = 'main.yml') -> Dict[str, EntityMappingEnvioMAG]:
        """
        Carga todos los mapeos de forma recursiva a partir de un archivo inicial
        
        Args:
            start_file: Archivo YAML inicial (por defecto main.yml)
        
        Returns:
            Diccionario con todos los mapeos cargados {filename: EntityMappingEnvioMAG}
        """
        visited = set()
        to_process = [start_file]
        
        while to_process:
            current_file = to_process.pop(0)
            
            if current_file in visited:
                continue
            
            visited.add(current_file)
            
            # Cargar el archivo actual
            entity_mapping = self.load_yaml_file(current_file)
            
            # Obtener referencias y agregarlas a la cola
            references = self.get_referenced_mappings(entity_mapping)
            for ref in references:
                if ref not in visited:
                    to_process.append(ref)
        
        if config.DEBUG_CLI:
            etl_logger.debug(f"[MappingLoaderEnvioMAG] Cargados {len(self.loaded_mappings)} archivos de mapeo")
        
        return self.loaded_mappings


# Instancia global del cargador
mapping_loader_envio_mag = MappingLoaderEnvioMAG()
