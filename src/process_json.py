"""
Script principal para procesar JSONs de KoboToolbox
Uso: python -m src.process_json <ruta_al_archivo.json>
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from .config import config
from .database import db
from .models import ControlEnviosBoletas, EstadoETLEnum, EstadoEnvioEnum
from .mapping_loader import mapping_loader
from .transformer import JSONTransformer, SQLGenerator


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Carga un archivo JSON
    
    Args:
        file_path: Ruta al archivo JSON
    
    Returns:
        Diccionario con los datos JSON
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_to_control_table(json_data: Dict[str, Any]) -> int:
    """
    Guarda el JSON completo en la tabla de control
    
    Args:
        json_data: Datos JSON del formulario
    
    Returns:
        El _id del registro insertado
    """
    # Extraer campos requeridos del JSON
    _id = json_data.get('_id')
    formhub_uuid = json_data.get('formhub/uuid') or json_data.get('formhub', {}).get('uuid')
    
    if not _id:
        raise ValueError("El JSON no contiene el campo '_id'")
    
    if not formhub_uuid:
        raise ValueError("El JSON no contiene el campo 'formhub/uuid'")
    
    # Crear el registro
    registro = ControlEnviosBoletas(
        _id=_id,
        formhub_uuid=formhub_uuid,
        json_data=json_data,
        fecha_recepcion=datetime.now(),
        estado_etl=EstadoETLEnum.PENDIENTE,
        envio_datos_procesados=EstadoEnvioEnum.PENDIENTE
    )
    
    # Guardar en la base de datos
    with db.get_session() as session:
        # Verificar si ya existe
        existing = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
        
        if existing:
            print(f"⚠️  Advertencia: Ya existe un registro con _id={_id}")
            print(f"   formhub_uuid: {existing.formhub_uuid}")
            print(f"   fecha_recepcion: {existing.fecha_recepcion}")
            print(f"   estado_etl: {existing.estado_etl}")
            return _id
        
        session.add(registro)
        session.commit()
        
        print(f"✅ JSON guardado en control_envios_boletas")
        print(f"   _id: {_id}")
        print(f"   formhub_uuid: {formhub_uuid}")
        print(f"   estado_etl: {registro.estado_etl.value}")
    
    return _id


def process_transformations(json_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Procesa las transformaciones según los mapeos YAML
    
    Args:
        json_data: Datos JSON del formulario
    
    Returns:
        Diccionario con las sentencias SQL por tabla
    """
    print("\n" + "="*80)
    print("INICIANDO PROCESO DE TRANSFORMACIÓN")
    print("="*80)
    
    # Cargar todos los mapeos
    print("\n📋 Cargando archivos de mapeo YAML...")
    mapping_loader.load_master()
    mapping_loader.load_all_mappings()
    
    # Obtener el orden de procesamiento
    processing_order = mapping_loader.get_processing_order()
    
    print(f"✅ Mapeos cargados: {len(mapping_loader.entity_mappings)} entidades")
    print(f"\n📊 Orden de procesamiento en {len(processing_order)} grupos:")
    for i, group in enumerate(processing_order, 1):
        print(f"   Grupo {i}: {', '.join(group)}")
    
    # Diccionario para almacenar las sentencias SQL
    sql_statements = {}
    # Diccionario para almacenar los IDs generados (simulados)
    generated_ids = {}
    
    # Procesar cada grupo en orden
    for group_num, group in enumerate(processing_order, 1):
        print(f"\n{'='*80}")
        print(f"PROCESANDO GRUPO {group_num}: {', '.join(group)}")
        print(f"{'='*80}")
        
        for entity_name in group:
            if entity_name not in mapping_loader.entity_mappings:
                print(f"⚠️  Advertencia: No se encontró mapeo para '{entity_name}'")
                continue
            
            entity_mapping = mapping_loader.entity_mappings[entity_name]
            
            print(f"\n🔄 Procesando entidad: {entity_name}")
            print(f"   Tabla destino: {entity_mapping.table}")
            print(f"   Campos a mapear: {len(entity_mapping.fields)}")
            
            # Determinar el parent_id si es necesario
            parent_id = None
            if entity_mapping.parent_key:
                parent_field = entity_mapping.parent_key.get('field')
                # El parent_id se obtendría de generated_ids, por ahora usamos NULL
                # En una implementación real con BD, aquí iría el ID retornado por el INSERT anterior
                print(f"   ⚠️  Requiere FK: {parent_field} (se usará NULL en esta versión)")
            
            # Verificar si tiene repeat
            has_repeat = entity_mapping.repeat is not None
            if has_repeat:
                print(f"   📦 Tiene grupo repetido: {entity_mapping.repeat}")
            
            # Transformar los datos
            rows = JSONTransformer.transform_entity_with_repeats(
                json_data,
                entity_mapping,
                parent_id=parent_id
            )
            
            if rows:
                print(f"   ✅ Registros generados: {len(rows)}")
                
                # Generar la sentencia INSERT
                insert_stmt = SQLGenerator.generate_insert(
                    table_name=entity_mapping.table,
                    rows=rows,
                    schema=config.DB_SCHEMA
                )
                
                if insert_stmt:
                    sql_statements[entity_name] = insert_stmt
                    print(f"   ✅ Sentencia SQL generada ({len(insert_stmt)} caracteres)")
                    
                    # Simular generación de ID para esta entidad
                    # En una implementación real, esto vendría del RETURNING del INSERT
                    generated_ids[entity_name] = len(rows)  # Simulado
            else:
                print(f"   ℹ️  No se generaron registros para esta entidad")
    
    return sql_statements


def print_sql_statements(sql_statements: Dict[str, str]):
    """
    Imprime las sentencias SQL generadas de forma legible
    
    Args:
        sql_statements: Diccionario con las sentencias SQL por entidad
    """
    print("\n" + "="*80)
    print("SENTENCIAS SQL GENERADAS")
    print("="*80)
    
    if not sql_statements:
        print("\n⚠️  No se generaron sentencias SQL")
        return
    
    print(f"\n✅ Total de sentencias generadas: {len(sql_statements)}")
    
    for entity_name, sql in sql_statements.items():
        print(f"\n{'─'*80}")
        print(f"ENTIDAD: {entity_name.upper()}")
        print(f"{'─'*80}")
        print(sql)
    
    print(f"\n{'='*80}")
    print("FIN DE SENTENCIAS SQL")
    print("="*80)


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description='Procesa un archivo JSON de KoboToolbox y genera sentencias SQL'
    )
    parser.add_argument(
        'json_file',
        type=str,
        help='Ruta al archivo JSON a procesar'
    )
    parser.add_argument(
        '--skip-db',
        action='store_true',
        help='Omitir guardado en base de datos (solo generar SQL)'
    )
    
    args = parser.parse_args()
    
    try:
        print("="*80)
        print("RENAGRO ETL PROCESS - Procesador de formularios KoboToolbox")
        print("="*80)
        
        # Cargar el archivo JSON
        print(f"\n📂 Cargando archivo JSON: {args.json_file}")
        json_data = load_json_file(args.json_file)
        
        # Obtener información básica
        file_size = Path(args.json_file).stat().st_size
        print(f"✅ Archivo cargado exitosamente")
        print(f"   Tamaño: {file_size:,} bytes ({file_size/1024:.2f} KB)")
        print(f"   Claves principales: {len(json_data)} campos")
        
        # Guardar en la tabla de control (si no se omite)
        if not args.skip_db:
            print(f"\n💾 Guardando en base de datos...")
            try:
                _id = save_to_control_table(json_data)
            except Exception as e:
                print(f"❌ Error al guardar en base de datos: {e}")
                print("   Continuando con la generación de SQL...")
        else:
            print(f"\n⏭️  Omitiendo guardado en base de datos (--skip-db)")
        
        # Procesar transformaciones
        sql_statements = process_transformations(json_data)
        
        # Imprimir las sentencias SQL
        print_sql_statements(sql_statements)
        
        print(f"\n✅ Proceso completado exitosamente")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Error de validación: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
