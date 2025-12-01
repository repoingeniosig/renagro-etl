#!/usr/bin/env python3
"""
Script para procesar lotes de registros desde un archivo JSON
Uso: python -m src.batch_processor <ruta_al_archivo.json>

El archivo JSON debe tener estructura:
{
    "count": 38,
    "next": null,
    "previous": null,
    "results": [
        {...},  # Registro 1
        {...},  # Registro 2
        ...
    ]
}

Cada objeto en 'results' será enviado a la cola RabbitMQ para procesamiento ETL.
"""
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .config import config
from .database import db
from .models import ControlEnviosBoletas
from .rabbitmq_client import rabbitmq_client
from .logger import etl_logger

console = Console()


def load_batch_file(file_path: str) -> Dict[str, Any]:
    """
    Carga un archivo JSON con estructura de lote
    
    Args:
        file_path: Ruta al archivo JSON
        
    Returns:
        Diccionario con los datos JSON
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el JSON no tiene estructura correcta
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validar estructura
    if 'results' not in data:
        raise ValueError("El JSON no contiene el campo 'results'")
    
    if not isinstance(data['results'], list):
        raise ValueError("El campo 'results' debe ser una lista")
    
    return data


def validate_record(record: Dict[str, Any], index: int) -> tuple[bool, str]:
    """
    Valida que un registro tenga el campo _id requerido
    
    Args:
        record: Registro a validar
        index: Índice del registro en el lote
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    _id = record.get('_id')
    
    if not _id:
        return False, f"Registro {index}: Falta campo '_id'"
    
    return True, ""


def check_duplicate(session, _id: int) -> bool:
    """
    Verifica si un _id ya existe en la base de datos
    
    Args:
        session: Sesión de SQLAlchemy
        _id: ID a verificar
        
    Returns:
        True si el _id ya existe (duplicado)
    """
    existing = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
    return existing is not None


async def process_batch(file_path: str, skip_duplicates: bool = True):
    """
    Procesa un lote de registros desde un archivo JSON
    
    Args:
        file_path: Ruta al archivo JSON con el lote
        skip_duplicates: Si True, omite duplicados; si False, los actualiza
    """
    try:
        # Banner inicial
        console.print(Panel.fit(
            "[bold cyan]RENAGRO ETL - PROCESAMIENTO POR LOTES[/bold cyan]\n"
            "Envío de registros a cola de procesamiento",
            border_style="cyan"
        ))
        
        # Cargar configuración de formularios
        from .forms_manager import forms_manager
        from .mapping_loader import mapping_loader
        from sqlalchemy import text
        
        console.print("\n⚙️  Cargando configuración de formularios...")
        forms = forms_manager.list_active_forms()
        
        for form in forms:
            mapping_path = forms_manager.get_mapping_path(form)
            if mapping_path.exists():
                mapping_loader.load_form_mappings(form.uuid, mapping_path)
        
        console.print(f"[green]✅ {len(forms)} formularios configurados[/green]")
        
        # Cargar archivo
        console.print(f"\n📂 Cargando archivo: [bold]{file_path}[/bold]")
        batch_data = load_batch_file(file_path)
        
        records = batch_data['results']
        total_records = len(records)
        
        file_size = Path(file_path).stat().st_size
        console.print(f"[green]✅ Archivo cargado exitosamente[/green]")
        console.print(f"   Tamaño: {file_size:,} bytes ({file_size/1024:.2f} KB)")
        console.print(f"   Total de registros: {total_records}")
        
        if total_records == 0:
            console.print("[yellow]⚠️  No hay registros para procesar[/yellow]")
            return
        
        # Estadísticas
        stats = {
            'enviados': 0,
            'duplicados': 0,
            'invalidos': 0,
            'errores': 0,
            'rechazados_uuid': 0
        }
        
        # Procesar registros con barra de progreso
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Procesando registros...", 
                total=total_records
            )
            
            # Procesar cada registro
            for index, record in enumerate(records, start=1):
                progress.update(task, advance=1)
                
                # Validar formulario por UUID
                is_valid_form, form_config, error = forms_manager.validate_json(record)
                
                if not is_valid_form:
                    stats['rechazados_uuid'] += 1
                    etl_logger.error(f"Registro {index}: {error}")
                    continue
                
                # Validar registro
                is_valid, error_msg = validate_record(record, index)
                
                if not is_valid:
                    stats['invalidos'] += 1
                    etl_logger.warning(error_msg)
                    continue
                
                _id = record.get('_id')
                
                # Verificar duplicados en tabla de control correspondiente
                try:
                    from .models import get_control_table_model
                    
                    ControlModel = get_control_table_model(form_config.control_table, db.engine)
                    
                    with db.get_session() as session:
                        existing = session.query(ControlModel).filter_by(_id=_id).first()
                        
                        if existing:
                            if skip_duplicates:
                                stats['duplicados'] += 1
                                etl_logger.info(f"Registro {index} (_id={_id}): Duplicado omitido en {form_config.control_table}")
                                continue
                            else:
                                etl_logger.info(f"Registro {index} (_id={_id}): Duplicado, se actualizará en {form_config.control_table}")
                
                except Exception as db_error:
                    stats['errores'] += 1
                    etl_logger.error(f"Registro {index} (_id={_id}): Error verificando duplicado: {db_error}")
                    continue
                
                # Publicar a cola RabbitMQ
                try:
                    # Agregar metadato del formulario
                    record['__form_uuid__'] = form_config.uuid
                    
                    success = await rabbitmq_client.publish_message(
                        queue_name=config.QUEUE_JSON_SAVE,
                        message=record,
                        priority=5
                    )
                    
                    if success:
                        stats['enviados'] += 1
                        etl_logger.info(f"Registro {index} (_id={_id}): Enviado a cola")
                    else:
                        stats['errores'] += 1
                        etl_logger.error(f"Registro {index} (_id={_id}): Fallo al enviar a cola")
                
                except Exception as queue_error:
                    stats['errores'] += 1
                    etl_logger.error(
                        f"Registro {index} (_id={_id}): Error publicando a cola: {queue_error}"
                    )
        
        # Mostrar resumen final
        console.print("\n" + "="*80)
        console.print("[bold cyan]RESUMEN DE PROCESAMIENTO[/bold cyan]")
        console.print("="*80)
        console.print(f"📊 Total de registros: {total_records}")
        console.print(f"✅ Enviados a cola:    {stats['enviados']}")
        console.print(f"⏭️  Duplicados omitidos: {stats['duplicados']}")
        console.print(f"⚠️  Inválidos:          {stats['invalidos']}")
        console.print(f"🚫 UUID no reconocido: {stats['rechazados_uuid']}")
        console.print(f"❌ Errores:            {stats['errores']}")
        console.print("="*80)
        
        if stats['enviados'] > 0:
            console.print(f"\n[green]✅ {stats['enviados']} registros encolados para procesamiento ETL[/green]")
            console.print("\n💡 Los workers procesarán los registros automáticamente.")
            console.print("   Puedes consultar el estado en la tabla 'control_envios_boletas'")
        
        etl_logger.info(
            f"Batch procesado: {stats['enviados']} enviados, "
            f"{stats['duplicados']} duplicados, {stats['invalidos']} inválidos, "
            f"{stats['errores']} errores"
        )
    
    except FileNotFoundError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        etl_logger.error(str(e))
        sys.exit(1)
    
    except ValueError as e:
        console.print(f"[red]❌ Error de validación: {e}[/red]")
        etl_logger.error(str(e))
        sys.exit(1)
    
    except Exception as e:
        console.print(f"[red]❌ Error inesperado: {e}[/red]")
        etl_logger.error(f"Error procesando batch: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        # Cerrar conexiones de RabbitMQ correctamente
        try:
            console.print("\n🔌 Cerrando conexiones...")
            await rabbitmq_client.close()
            
            # Esperar un momento para que se completen los callbacks pendientes
            await asyncio.sleep(0.5)
            
        except Exception as e:
            etl_logger.warning(f"Error cerrando RabbitMQ: {e}")


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description='Procesa un lote de registros desde un archivo JSON y los envía a la cola ETL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Estructura esperada del JSON:
{
    "count": 38,
    "next": null,
    "previous": null,
    "results": [
        {"_id": 123, ...},
        {"_id": 124, ...},
        ...
    ]
}

Ejemplos de uso:
  python -m src.batch_processor datos.json
  python -m src.batch_processor --allow-duplicates datos.json
        """
    )
    
    parser.add_argument(
        'json_file',
        type=str,
        help='Ruta al archivo JSON con el lote de registros'
    )
    
    parser.add_argument(
        '--allow-duplicates',
        action='store_true',
        help='Procesar duplicados (actualizarlos) en lugar de omitirlos'
    )
    
    args = parser.parse_args()
    
    # Ejecutar procesamiento asíncrono con cleanup correcto
    try:
        asyncio.run(process_batch(
            file_path=args.json_file,
            skip_duplicates=not args.allow_duplicates
        ))
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Procesamiento interrumpido por el usuario[/yellow]")
        sys.exit(0)


if __name__ == '__main__':
    main()
