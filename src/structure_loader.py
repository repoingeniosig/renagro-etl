"""
Cargador del archivo structure.yaml
Define la configuración genérica para envío de datos
"""
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .config import config
from .logger import etl_logger


@dataclass
class ControlTableFilter:
    """Filtro para la tabla de control"""
    column: str
    value: Any
    type: str  # 'enum', 'string', 'integer', 'boolean', etc.


@dataclass
class TargetDataToSend:
    """
    Configuración de datos a enviar
    
    Attributes:
        mapping: Nombre de carpeta con YAMLs (ej: "mappings-envio-mag")
        control_table: Tabla de control (ej: "control_envios_boletas")
        control_table_id: Columna en control_table con IDs a extraer (ej: "uuid_boleta")
                         Estos valores se usarán para buscar en source_reference_field
        control_table_filters: Filtros para consultar registros pendientes
        source_reference_file: Archivo YAML de referencia en mapping (ej: "main.yml")
        source_reference_field: Campo en la tabla principal para hacer match con control_table_id
                               (ej: "bol_id_levanta" que contiene UUIDs)
    """
    mapping: str
    control_table: str
    control_table_id: str
    control_table_filters: List[ControlTableFilter]
    source_reference_file: str
    source_reference_field: str


class StructureLoader:
    """Cargador del archivo structure.yaml"""
    
    def __init__(self, structure_file: Path = None):
        self.structure_file = structure_file or config.BASE_DIR / 'structure.yaml'
        self._target_data: Optional[TargetDataToSend] = None
    
    def load_structure(self) -> Dict[str, Any]:
        """
        Carga el archivo structure.yaml
        
        Returns:
            Diccionario con la configuración completa
        """
        if not self.structure_file.exists():
            raise FileNotFoundError(f"Archivo structure.yaml no encontrado: {self.structure_file}")
        
        if config.DEBUG_CLI:
            etl_logger.debug(f"[StructureLoader] Cargando {self.structure_file}")
        
        with open(self.structure_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return data
    
    def get_target_data_to_send(self) -> TargetDataToSend:
        """
        Obtiene la configuración de target_data_to_send
        
        Returns:
            TargetDataToSend con la configuración
        """
        if self._target_data:
            return self._target_data
        
        structure = self.load_structure()
        
        target_config = structure.get('target_data_to_send')
        if not target_config:
            raise ValueError("No se encontró 'target_data_to_send' en structure.yaml")
        
        # Validar campos requeridos
        required_fields = ['mapping', 'control_table', 'control_table_id', 'source_reference_file', 'source_reference_field']
        for field in required_fields:
            if field not in target_config:
                raise ValueError(f"Campo requerido '{field}' no encontrado en target_data_to_send")
        
        # Parsear filtros
        filters = []
        filters_config = target_config.get('control_table_filters', [])
        
        for filter_config in filters_config:
            if 'column' not in filter_config or 'value' not in filter_config:
                raise ValueError("Cada filtro debe tener 'column' y 'value'")
            
            filters.append(ControlTableFilter(
                column=filter_config['column'],
                value=filter_config['value'],
                type=filter_config.get('type', 'string')
            ))
        
        self._target_data = TargetDataToSend(
            mapping=target_config['mapping'],
            control_table=target_config['control_table'],
            control_table_id=target_config['control_table_id'],
            control_table_filters=filters,
            source_reference_file=target_config['source_reference_file'],
            source_reference_field=target_config['source_reference_field']
        )
        
        if config.DEBUG_CLI:
            etl_logger.debug(
                f"[StructureLoader] Target configurado: "
                f"mapping={self._target_data.mapping}, "
                f"control_table={self._target_data.control_table}, "
                f"control_table_id={self._target_data.control_table_id}, "
                f"filters={len(self._target_data.control_table_filters)}"
            )
        
        return self._target_data


# Instancia global
structure_loader = StructureLoader()
