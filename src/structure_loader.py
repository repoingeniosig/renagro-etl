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
    """Configuración de datos a enviar"""
    mapping: str  # Nombre de carpeta con YAMLs (ej: "mappings-envio-mag")
    control_table: str  # Tabla de control (ej: "control_envios_boletas")
    id_column: str  # Columna con IDs a empatar con database_id del main.yml (ej: "_id")
    control_table_filters: List[ControlTableFilter]  # Filtros para la tabla de control


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
        required_fields = ['mapping', 'control_table', 'id_column']
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
            id_column=target_config['id_column'],
            control_table_filters=filters
        )
        
        if config.DEBUG_CLI:
            etl_logger.debug(
                f"[StructureLoader] Target configurado: "
                f"mapping={self._target_data.mapping}, "
                f"control_table={self._target_data.control_table}, "
                f"id_column={self._target_data.id_column}, "
                f"filters={len(self._target_data.control_table_filters)}"
            )
        
        return self._target_data


# Instancia global
structure_loader = StructureLoader()
