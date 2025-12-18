"""
Script para comparar datos del JSON de entrada con datos en la base de datos
y detectar discrepancias en el proceso ETL.
"""
import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy import text

# Agregar el directorio src al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import db

DB_SCHEMA = os.getenv('DB_SCHEMA', 'sc_renagro_mag')

class ETLComparer:
    def __init__(self, json_file: str, mappings_dir: str):
        self.json_file = json_file
        self.mappings_dir = Path(mappings_dir)
        self.json_data = None
        self.mappings = {}
        self.session = None
        self.differences = []
    
    def load_json(self):
        """Cargar el archivo JSON"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'results' in data:
                    self.json_data = data['results']
                else:
                    self.json_data = data if isinstance(data, list) else [data]
            print(f"✓ JSON cargado: {len(self.json_data)} registros")
        except Exception as e:
            print(f"✗ Error cargando JSON: {e}")
            sys.exit(1)
    
    def load_mappings(self):
        """Cargar todos los archivos de mapeo YAML"""
        try:
            yaml_files = list(self.mappings_dir.glob('*.yaml')) + list(self.mappings_dir.glob('*.yml'))
            
            for yaml_file in yaml_files:
                if yaml_file.name == 'master.yml':
                    continue
                    
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    mapping = yaml.safe_load(f)
                    if mapping and 'entity' in mapping and 'table' in mapping:
                        entity_name = mapping['entity']
                        self.mappings[entity_name] = mapping
                        print(f"  - {entity_name}: {yaml_file.name}")
            
            print(f"✓ Mapeos cargados: {len(self.mappings)} entidades")
        except Exception as e:
            print(f"✗ Error cargando mapeos: {e}")
            sys.exit(1)
    
    def get_nested_value(self, data: Dict, key: str) -> Any:
        """
        Obtener valor anidado del JSON.
        En Kobo, el slash '/' es parte del key, no un separador de jerarquía.
        """
        return data.get(key)
    
    def normalize_value(self, value: Any, field_type: str = None) -> str:
        """Normalizar valor para comparación"""
        if value is None or value == '':
            return None
        
        # Convertir a string y uppercase para comparar
        str_value = str(value).strip()
        
        # Si el campo es de tipo texto, convertir a uppercase
        if field_type == 'string' or field_type is None:
            return str_value.upper()
        
        return str_value
    
    def should_compare_field(self, field_config: Dict) -> bool:
        """Determinar si un campo debe ser comparado"""
        field_type = field_config.get('type', 'string')
        
        # Solo comparar campos de tipo string
        if field_type != 'string':
            return False
        
        # No comparar campos sin source (IDs generados, etc.)
        source = field_config.get('source', '')
        
        # Si source es una lista, no comparar (son campos multi-choice o transformaciones)
        if isinstance(source, list):
            return False
        
        # Si source es un dict, no comparar (son transformaciones complejas)
        if isinstance(source, dict):
            return False
        
        if not source or (isinstance(source, str) and source.strip() == ''):
            return False
        
        # No comparar campos que son repeat (arrays)
        if field_config.get('repeat_filter'):
            return False
        
        # No comparar campos extract (ya que estos vienen de arrays y son más complejos)
        if field_config.get('extract'):
            return False
            
        return True
    
    def get_db_records(self, table: str) -> List[Dict]:
        """Obtener todos los registros de una tabla"""
        try:
            query = text(f"SELECT * FROM {DB_SCHEMA}.{table}")
            result = self.session.execute(query)
            records = result.fetchall()
            # Convertir a dict usando las keys de las columnas
            columns = result.keys()
            return [dict(zip(columns, row)) for row in records]
        except Exception as e:
            print(f"✗ Error consultando tabla {table}: {e}")
            return []
    
    def get_json_record_by_id(self, json_id: int) -> Dict:
        """Buscar un registro JSON por su _id"""
        for record in self.json_data:
            if record.get('_id') == json_id:
                return record
        return None
    
    def compare_entity(self, entity_name: str, mapping: Dict):
        """Comparar una entidad específica"""
        print(f"\n{'='*80}")
        print(f"Comparando entidad: {entity_name}")
        print(f"Tabla: {mapping['table']}")
        print(f"{'='*80}")
        
        fields = mapping.get('fields', {})
        table = mapping['table']
        
        # Obtener registros de la base de datos
        db_records = self.get_db_records(table)
        print(f"Registros en BD: {len(db_records)}")
        print(f"Registros en JSON: {len(self.json_data)}")
        
        if not db_records:
            print(f"⚠ No hay registros en la tabla {table}")
            return
        
        # Contar campos comparables
        comparable_fields = [f for f, cfg in fields.items() if self.should_compare_field(cfg)]
        print(f"Campos de texto comparables: {len(comparable_fields)}")
        
        if not comparable_fields:
            print(f"⚠ No hay campos de texto para comparar en {entity_name}")
            return
        
        # Comparar campos
        fields_compared = 0
        differences_found = 0
        
        # Para tabla boletas, usar bol_id_levanta para relacionar con _id del JSON
        for db_record in db_records:
            # Intentar obtener el ID del levantamiento desde la BD
            json_id = None
            if table == 'boletas':
                json_id = db_record.get('bol_id_levanta')
                if json_id:
                    try:
                        json_id = int(json_id)
                    except:
                        json_id = None
            
            # Si no podemos relacionar, saltar este registro
            if json_id is None:
                continue
            
            # Buscar el registro JSON correspondiente
            json_record = self.get_json_record_by_id(json_id)
            if not json_record:
                continue
            
            # Comparar cada campo
            for field_name, field_config in fields.items():
                if not self.should_compare_field(field_config):
                    continue
                
                fields_compared += 1
                source_key = field_config['source']
                field_type = field_config.get('type', 'string')
                
                # Obtener valores
                json_value = self.get_nested_value(json_record, source_key)
                json_value_normalized = self.normalize_value(json_value, field_type)
                
                db_value = db_record.get(field_name.lower())
                db_value_normalized = self.normalize_value(db_value, field_type)
                
                # Verificar diferencias
                if json_value_normalized != db_value_normalized:
                    differences_found += 1
                    difference = {
                        'entity': entity_name,
                        'table': table,
                        'field': field_name,
                        'source_key': source_key,
                        'json_id': json_id,
                        'json_value': json_value,
                        'json_value_normalized': json_value_normalized,
                        'db_value': db_value,
                        'db_value_normalized': db_value_normalized,
                        'field_type': field_type,
                        'db_record_id': db_record.get(f'{table[:3]}_id')  # Ej: bol_id para boletas
                    }
                    self.differences.append(difference)
                    
                    # Mostrar diferencia
                    print(f"\n⚠ DIFERENCIA ENCONTRADA:")
                    print(f"   Campo: {field_name}")
                    print(f"   Source JSON: {source_key}")
                    print(f"   JSON ID: {json_id}")
                    print(f"   DB Record ID: {db_record.get(f'{table[:3]}_id')}")
                    print(f"   Valor JSON: '{json_value}' → '{json_value_normalized}'")
                    print(f"   Valor BD: '{db_value}' → '{db_value_normalized}'")
        
        print(f"\n📊 Resumen de {entity_name}:")
        print(f"   Campos comparados: {fields_compared}")
        print(f"   Diferencias encontradas: {differences_found}")
    
    def run(self):
        """Ejecutar la comparación completa"""
        print("="*80)
        print("SCRIPT DE COMPARACIÓN JSON vs BASE DE DATOS")
        print("="*80)
        
        # Cargar datos
        print("\n📂 Cargando datos...")
        self.load_json()
        self.load_mappings()
        
        # Usar sesión de base de datos
        with db.get_session() as session:
            self.session = session
            
            print("\n✓ Conectado a la base de datos")
            
            # Comparar cada entidad
            print("\n🔍 Iniciando comparación...")
            for entity_name, mapping in self.mappings.items():
                self.compare_entity(entity_name, mapping)
        
        # Resumen final
        print("\n" + "="*80)
        print("RESUMEN FINAL")
        print("="*80)
        print(f"Total de diferencias encontradas: {len(self.differences)}")
        
        # Agrupar diferencias por campo
        fields_with_diff = {}
        for diff in self.differences:
            key = f"{diff['entity']}.{diff['field']}"
            if key not in fields_with_diff:
                fields_with_diff[key] = []
            fields_with_diff[key].append(diff)
        
        print(f"\nCampos con diferencias: {len(fields_with_diff)}")
        for field, diffs in sorted(fields_with_diff.items()):
            print(f"  - {field}: {len(diffs)} diferencia(s)")
        
        # Mostrar campos sin mapear (valor en JSON pero NULL en BD)
        null_in_db = [d for d in self.differences if d['db_value_normalized'] is None and d['json_value_normalized'] is not None]
        if null_in_db:
            print(f"\n⚠️  Campos con valor en JSON pero NULL en BD: {len(null_in_db)}")
            null_by_field = {}
            for diff in null_in_db:
                key = f"{diff['entity']}.{diff['field']}"
                if key not in null_by_field:
                    null_by_field[key] = 0
                null_by_field[key] += 1
            for field, count in sorted(null_by_field.items()):
                print(f"  - {field}: {count} caso(s)")
        
        return self.differences

def main():
    # Rutas de archivos
    project_root = Path(__file__).parent.parent
    json_file = Path.home() / "Downloads" / "boletas.json"
    mappings_dir = project_root / "mappings" / "boletas"
    
    print(f"JSON file: {json_file}")
    print(f"Mappings dir: {mappings_dir}")
    
    if not json_file.exists():
        print(f"✗ Archivo JSON no encontrado: {json_file}")
        sys.exit(1)
    
    if not mappings_dir.exists():
        print(f"✗ Directorio de mapeos no encontrado: {mappings_dir}")
        sys.exit(1)
    
    # Ejecutar comparación
    comparer = ETLComparer(str(json_file), str(mappings_dir))
    differences = comparer.run()
    
    # Guardar reporte
    report_file = project_root / "tests" / f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(differences, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Reporte guardado en: {report_file}")

if __name__ == "__main__":
    main()
