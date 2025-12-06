"""
Cargador de configuración multi-formulario
Lee mappings.yaml y gestiona diferentes tipos de formularios
"""
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from .config import config
from .logger import etl_logger


@dataclass
class FormConfig:
    """Configuración de un formulario específico"""
    uuid: str
    name: str
    description: str
    control_table: str
    mapping_dir: str
    source_form_uuid_field: str
    target_control_table_field: str


@dataclass
class MappingsConfig:
    """Configuración global de mappings"""
    form_uuid_field: str
    reject_unknown_forms: bool
    log_unknown_forms: bool
    forms: List[FormConfig]


class MultiFormLoader:
    """Cargador de configuración multi-formulario desde mappings.yaml"""
    
    def __init__(self, mappings_file: Path = None):
        self.mappings_file = mappings_file or (config.BASE_DIR / 'mappings' / 'mappings.yaml')
        self.config: Optional[MappingsConfig] = None
        self._form_cache: Dict[str, FormConfig] = {}
    
    def load_config(self) -> MappingsConfig:
        """Carga la configuración desde mappings.yaml"""
        if self.config:
            return self.config
        
        if not self.mappings_file.exists():
            raise FileNotFoundError(
                f"Archivo de configuración no encontrado: {self.mappings_file}"
            )
        
        with open(self.mappings_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Validar estructura
        if 'config' not in data or 'forms' not in data:
            raise ValueError(
                "mappings.yaml debe contener 'config' y 'forms'"
            )
        
        config_data = data['config']
        forms_data = data['forms']
        
        # Parsear formularios
        forms = []
        for form_data in forms_data:
            try:
                form = FormConfig(
                    uuid=form_data['uuid'],
                    name=form_data['name'],
                    description=form_data.get('description', ''),
                    control_table=form_data['control_table'],
                    mapping_dir=form_data['mapping_dir'],
                    source_form_uuid_field=form_data['source_form_uuid_field'],
                    target_control_table_field=form_data['target_control_table_field']
                )
                forms.append(form)
                self._form_cache[form.uuid] = form
            except KeyError as e:
                etl_logger.error(
                    f"Error parseando formulario: falta campo {e}. "
                    f"Formulario: {form_data.get('name', 'unknown')}"
                )
                raise
        
        self.config = MappingsConfig(
            form_uuid_field=config_data['form_uuid_field'],
            reject_unknown_forms=config_data.get('reject_unknown_forms', True),
            log_unknown_forms=config_data.get('log_unknown_forms', True),
            forms=forms
        )
        
        etl_logger.info(
            f"Configuración multi-formulario cargada: {len(forms)} formularios registrados"
        )
        
        return self.config
    
    def get_form_by_uuid(self, form_uuid: str) -> Optional[FormConfig]:
        """Obtiene la configuración de un formulario por su UUID"""
        if not self.config:
            self.load_config()
        
        return self._form_cache.get(form_uuid)
    
    def extract_form_uuid_from_json(self, json_data: Dict) -> Optional[str]:
        """Extrae el UUID del formulario desde el JSON"""
        if not self.config:
            self.load_config()
        
        # Navegar por dot notation
        keys = self.config.form_uuid_field.split('/')
        value = json_data
        
        try:
            for key in keys:
                value = value[key]
            return str(value) if value else None
        except (KeyError, TypeError):
            etl_logger.warning(
                f"No se pudo extraer form_uuid_field '{self.config.form_uuid_field}' del JSON"
            )
            return None
    
    def get_mapping_dir_for_form(self, form_uuid: str) -> Optional[Path]:
        """Obtiene la ruta del directorio de mappings para un formulario"""
        form_config = self.get_form_by_uuid(form_uuid)
        if not form_config:
            return None
        
        return config.BASE_DIR / 'mappings' / form_config.mapping_dir


# Instancia global
multi_form_loader = MultiFormLoader()
