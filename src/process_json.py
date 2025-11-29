"""
Script principal para procesar JSONs de KoboToolbox
Uso: python -m src.process_json <ruta_al_archivo.json>

Flujo de procesamiento:
1. Guardar JSON en control_envios_boletas
2. Realizar transformaciones y mapeos
3. Generar transacción SQL con SQLAlchemy
4. Ejecutar transacción en la base de datos
5. Mostrar resultados de la ejecución
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .config import config
from .database import db
from .models import ControlEnviosBoletas, EstadoETLEnum, EstadoEnvioEnum
from .mapping_loader import mapping_loader
from .transformer import JSONTransformer
from .executor import TransactionExecutor

console = Console()


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


def save_to_control_table(json_data: Dict[str, Any], allow_duplicates: bool = True) -> int:
    """
    PASO 1: Guarda el JSON completo en la tabla de control
    
    Args:
        json_data: Datos JSON del formulario
        allow_duplicates: Si False, lanza excepción si el _id ya existe
    
    Returns:
        El _id del registro insertado
        
    Raises:
        ValueError: Si allow_duplicates=False y el _id ya existe
    """
    console.print("\n[bold cyan]PASO 1: Guardando en tabla de control[/bold cyan]")
    
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
        estado_etl=EstadoETLEnum.PENDIENTE,
        envio_datos_procesados=EstadoEnvioEnum.PENDIENTE
    )
    
    # Guardar en la base de datos
    with db.get_session() as session:
        # Verificar si ya existe
        existing = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
        
        if existing:
            if not allow_duplicates:
                raise ValueError(f"Registro duplicado: _id={_id} ya existe en la base de datos")
            
            console.print(f"[yellow]⚠️  Ya existe registro con _id={_id}[/yellow]")
            console.print(f"   formhub_uuid: {existing.formhub_uuid}")
            console.print(f"   estado_etl: {existing.estado_etl.value}")
            console.print(f"   Actualizando JSON y reseteando estado...")
            
            # Actualizar el JSON y resetear estado
            existing.json_data = json_data
            existing.estado_etl = EstadoETLEnum.PENDIENTE
            existing.updated_at = datetime.now()
            session.commit()
            console.print(f"[green]✅ Registro actualizado[/green]")
        else:
            session.add(registro)
            session.commit()
            console.print(f"[green]✅ Nuevo registro guardado[/green]")
        
        console.print(f"   _id: {_id}")
        console.print(f"   formhub_uuid: {formhub_uuid}")
    
    return _id


def process_transformations(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    PASO 2: Procesa las transformaciones según los mapeos YAML
    
    Args:
        json_data: Datos JSON del formulario
    
    Returns:
        Diccionario con las transformaciones por entidad y el orden de procesamiento
    """
    console.print("\n[bold cyan]PASO 2: Realizando transformaciones y mapeos[/bold cyan]")
    
    # Cargar todos los mapeos
    console.print("\n📋 Cargando archivos de mapeo YAML...")
    mapping_loader.load_master()
    mapping_loader.load_all_mappings()
    
    # Obtener el orden de procesamiento
    processing_order = mapping_loader.get_processing_order()
    
    console.print(f"[green]✅ Mapeos cargados: {len(mapping_loader.entity_mappings)} entidades[/green]")
    console.print(f"\n📊 Orden de procesamiento en {len(processing_order)} grupos:")
    for i, group in enumerate(processing_order, 1):
        console.print(f"   Grupo {i}: {', '.join(group)}")
    
    # Diccionario para almacenar las transformaciones
    transformations = {}
    
    # Procesar cada grupo en orden
    for group_num, group in enumerate(processing_order, 1):
        console.print(f"\n[bold]Grupo {group_num}:[/bold] {', '.join(group)}")
        
        for entity_name in group:
            if entity_name not in mapping_loader.entity_mappings:
                console.print(f"   [yellow]⚠️  {entity_name}: Sin mapeo[/yellow]")
                continue
            
            entity_mapping = mapping_loader.entity_mappings[entity_name]
            
            # Transformar los datos
            rows = JSONTransformer.transform_entity_with_repeats(
                json_data,
                entity_mapping,
                parent_id=None  # Por ahora sin parent_id
            )
            
            if rows:
                transformations[entity_name] = rows
                console.print(f"   [green]✅ {entity_name}: {len(rows)} registro(s)[/green]")
            else:
                console.print(f"   [dim]⏭️  {entity_name}: Sin datos[/dim]")
    
    return {
        'transformations': transformations,
        'processing_order': processing_order
    }


def execute_transaction(
    transformations: Dict[str, Any],
    processing_order: list,
    debug: bool = False
) -> Dict[str, Any]:
    """
    PASO 3 y 4: Genera y ejecuta la transacción SQL con SQLAlchemy
    
    Args:
        transformations: Diccionario {entity_name: [rows]}
        processing_order: Orden de procesamiento de entidades
        debug: Si True, imprime detalles de ejecución
        
    Returns:
        Resultados de la ejecución
    """
    console.print("\n[bold cyan]PASO 3 y 4: Ejecutando transacción en la base de datos[/bold cyan]")
    
    results = TransactionExecutor.execute_inserts(
        transformations=transformations,
        processing_order=processing_order,
        debug=debug
    )
    
    return results


def update_control_status(
    _id: int,
    success: bool,
    error_message: str = None
):
    """
    Actualiza el estado del registro en control_envios_boletas
    
    Args:
        _id: ID del registro
        success: Si el procesamiento fue exitoso
        error_message: Mensaje de error si falló
    """
    try:
        with db.get_session() as session:
            control = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
            if control:
                if success:
                    control.estado_etl = EstadoETLEnum.PROCESADO
                    control.procesado_at = datetime.now()
                    control.error_message = None
                else:
                    control.estado_etl = EstadoETLEnum.ERROR
                    control.error_message = error_message
                
                session.commit()
                console.print(f"\n[green]✅ Estado actualizado en control_envios_boletas[/green]")
    except Exception as e:
        console.print(f"[yellow]⚠️  No se pudo actualizar el estado: {e}[/yellow]")


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description='Procesa un archivo JSON de KoboToolbox y ejecuta la transacción en la base de datos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python -m src.process_json archivo.json
  python -m src.process_json --skip-db archivo.json
  python -m src.process_json --debug archivo.json
        """
    )
    parser.add_argument(
        'json_file',
        type=str,
        help='Ruta al archivo JSON a procesar'
    )
    parser.add_argument(
        '--skip-db',
        action='store_true',
        help='Omitir guardado en base de datos (solo mostrar transformaciones)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Modo debug: mostrar SQL generado y detalles de ejecución'
    )
    
    args = parser.parse_args()
    
    # Usar DEBUG del .env si no se especifica en argumentos
    debug = args.debug or config.DEBUG
    
    try:
        # Banner inicial
        console.print(Panel.fit(
            "[bold cyan]RENAGRO ETL PROCESS[/bold cyan]\n"
            "Procesador de formularios KoboToolbox",
            border_style="cyan"
        ))
        
        # Cargar el archivo JSON
        console.print(f"\n📂 Cargando archivo: [bold]{args.json_file}[/bold]")
        json_data = load_json_file(args.json_file)
        
        file_size = Path(args.json_file).stat().st_size
        console.print(f"[green]✅ Archivo cargado exitosamente[/green]")
        console.print(f"   Tamaño: {file_size:,} bytes ({file_size/1024:.2f} KB)")
        
        _id = None
        
        # PASO 1: Guardar en la tabla de control
        if not args.skip_db:
            _id = save_to_control_table(json_data)
        else:
            console.print("\n[yellow]⏭️  Omitiendo guardado en base de datos (--skip-db)[/yellow]")
            _id = json_data.get('_id')
        
        # PASO 2: Procesar transformaciones
        transformation_result = process_transformations(json_data)
        transformations = transformation_result['transformations']
        processing_order = transformation_result['processing_order']
        
        # Mostrar resumen de transformaciones
        total_rows = sum(len(rows) for rows in transformations.values())
        console.print(f"\n[bold green]✅ Transformaciones completadas:[/bold green]")
        console.print(f"   Entidades con datos: {len(transformations)}")
        console.print(f"   Total registros a insertar: {total_rows}")
        
        # PASO 3 y 4: Ejecutar transacción
        if not args.skip_db and transformations:
            try:
                results = execute_transaction(
                    transformations=transformations,
                    processing_order=processing_order,
                    debug=debug
                )
                
                # PASO 5: Mostrar resultados
                console.print("\n[bold cyan]PASO 5: Resultados de la ejecución[/bold cyan]")
                TransactionExecutor.print_execution_summary(results)
                
                # Actualizar estado a PROCESADO
                if results['success']:
                    update_control_status(_id, success=True)
                    console.print("\n[bold green]🎉 ¡Proceso completado exitosamente![/bold green]")
                else:
                    error_msg = '; '.join(results['errors']) if results['errors'] else 'Error desconocido'
                    update_control_status(_id, success=False, error_message=error_msg)
                    console.print("\n[bold red]❌ El proceso finalizó con errores[/bold red]")
                    sys.exit(1)
                    
            except Exception as e:
                error_msg = str(e)
                console.print(f"\n[bold red]❌ Error ejecutando transacción: {error_msg}[/bold red]")
                
                # Actualizar estado a ERROR
                if _id:
                    update_control_status(_id, success=False, error_message=error_msg)
                
                if debug:
                    import traceback
                    traceback.print_exc()
                
                sys.exit(1)
        
        elif args.skip_db:
            console.print("\n[yellow]⏭️  Omitiendo ejecución en base de datos (--skip-db)[/yellow]")
            console.print("[dim]Para ejecutar en BD, ejecute sin --skip-db[/dim]")
        
        elif not transformations:
            console.print("\n[yellow]⚠️  No hay datos para insertar[/yellow]")
        
    except FileNotFoundError as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        sys.exit(1)
    except ValueError as e:
        console.print(f"\n[bold red]❌ Error de validación: {e}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error inesperado: {e}[/bold red]")
        if debug or config.DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
