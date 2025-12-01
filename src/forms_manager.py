"""
Gestor de configuración de formularios multi-ETL
Carga y valida formularios desde forms_config.yml
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass

from .logger import etl_logger


@dataclass
class FormConfig:
    """Configuración de un formulario"""
    uuid: str
    name: str
    description: str
    control_table: str
    mapping_dir: str
    enabled: bool


class FormsManager:
    """Gestor de formularios multi-ETL"""
    
    def __init__(self, config_file: str = "forms_config.yml"):
        """
        Inicializa el gestor de formularios
        
        Args:
            config_file: Ruta al archivo de configuración YAML
        """
        self.config_file = config_file
        self.forms: Dict[str, FormConfig] = {}
        self.mappings_base_dir = "mappings"
        self.uuid_field = "formhub/uuid"
        self.reject_unknown_forms = True
        self.log_unknown_forms = True
        
        self._load_config()
    
    def _load_config(self):
        """Carga la configuración desde el archivo YAML"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            etl_logger.warning(f"Archivo de configuración no encontrado: {config_path}")
            etl_logger.warning("Usando configuración por defecto (solo formulario 'boletas')")
            self._load_default_config()
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Cargar configuración global
            if 'config' in config_data:
                global_config = config_data['config']
                self.mappings_base_dir = global_config.get('mappings_base_dir', 'mappings')
                self.uuid_field = global_config.get('uuid_field', 'formhub/uuid')
                self.reject_unknown_forms = global_config.get('reject_unknown_forms', True)
                self.log_unknown_forms = global_config.get('log_unknown_forms', True)
            
            # Cargar formularios
            if 'forms' in config_data:
                for form_data in config_data['forms']:
                    form = FormConfig(
                        uuid=form_data['uuid'],
                        name=form_data['name'],
                        description=form_data.get('description', ''),
                        control_table=form_data['control_table'],
                        mapping_dir=form_data['mapping_dir'],
                        enabled=form_data.get('enabled', True)
                    )
                    
                    if form.enabled:
                        self.forms[form.uuid] = form
                        etl_logger.info(
                            f"Formulario registrado: {form.uuid} → {form.name} "
                            f"(tabla: {form.control_table}, mapeo: {form.mapping_dir})"
                        )
            
            etl_logger.info(f"Configuración cargada: {len(self.forms)} formularios activos")
            
        except Exception as e:
            etl_logger.error(f"Error cargando configuración de formularios: {e}", exc_info=True)
            self._load_default_config()
    
    def _load_default_config(self):
        """Carga configuración por defecto (retrocompatibilidad)"""
        default_form = FormConfig(
            uuid="default",
            name="boletas",
            description="Formulario por defecto (retrocompatibilidad)",
            control_table="control_envios_boletas",
            mapping_dir="mapping",  # Directorio original
            enabled=True
        )
        
        self.forms["default"] = default_form
        self.mappings_base_dir = "."
        etl_logger.info("Usando configuración por defecto para retrocompatibilidad")
    
    def get_form_uuid_from_json(self, json_data: Dict) -> Optional[str]:
        """
        Extrae el UUID del formulario desde el JSON
        
        Args:
            json_data: Datos JSON del formulario
            
        Returns:
            UUID del formulario o None si no se encuentra
        """
        # Navegar por el path (ej: "formhub/uuid")
        keys = self.uuid_field.split('/')
        value = json_data
        
        try:
            for key in keys:
                value = value.get(key)
                if value is None:
                    return None
            
            return str(value) if value else None
            
        except (AttributeError, TypeError):
            return None
    
    def get_form_config(self, form_uuid: str) -> Optional[FormConfig]:
        """
        Obtiene la configuración de un formulario por su UUID
        
        Args:
            form_uuid: UUID del formulario
            
        Returns:
            FormConfig o None si no existe
        """
        return self.forms.get(form_uuid)
    
    def validate_json(self, json_data: Dict) -> tuple[bool, Optional[FormConfig], Optional[str]]:
        """
        Valida si un JSON puede ser procesado
        
        Args:
            json_data: Datos JSON a validar
            
        Returns:
            Tupla (es_válido, FormConfig, mensaje_error)
        """
        # Extraer UUID del formulario
        form_uuid = self.get_form_uuid_from_json(json_data)
        
        if not form_uuid:
            error_msg = f"JSON no contiene campo '{self.uuid_field}'"
            
            if self.log_unknown_forms:
                etl_logger.warning(error_msg)
            
            # Si no hay UUID, usar configuración por defecto si existe
            if "default" in self.forms:
                return True, self.forms["default"], None
            
            return False, None, error_msg
        
        # Buscar configuración del formulario
        form_config = self.get_form_config(form_uuid)
        
        if not form_config:
            error_msg = f"Formulario no reconocido: UUID={form_uuid}"
            
            if self.log_unknown_forms:
                etl_logger.warning(error_msg)
            
            if self.reject_unknown_forms:
                return False, None, error_msg
            
            # Si no rechaza desconocidos, usar default
            if "default" in self.forms:
                return True, self.forms["default"], None
            
            return False, None, error_msg
        
        return True, form_config, None
    
    def get_mapping_path(self, form_config: FormConfig) -> Path:
        """
        Obtiene la ruta al directorio de mapeos de un formulario
        
        Args:
            form_config: Configuración del formulario
            
        Returns:
            Path al directorio de mapeos
        """
        return Path(self.mappings_base_dir) / form_config.mapping_dir
    
    def list_active_forms(self) -> List[FormConfig]:
        """
        Lista todos los formularios activos
        
        Returns:
            Lista de FormConfig activos
        """
        return list(self.forms.values())
    
    def get_control_table_name(self, form_uuid: str) -> Optional[str]:
        """
        Obtiene el nombre de la tabla de control para un formulario
        
        Args:
            form_uuid: UUID del formulario
            
        Returns:
            Nombre de la tabla de control o None
        """
        form_config = self.get_form_config(form_uuid)
        return form_config.control_table if form_config else None


# Instancia global
forms_manager = FormsManager()
