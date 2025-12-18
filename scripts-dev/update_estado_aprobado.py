"""
Script para actualizar todos los registros de control_envios_boletas
Cambia estado_etl de 'PROCESADO' a 'APROBADO' para todos los registros
que están listos para envío a la API de MAG

Uso: python3 scripts-dev/update_estado_aprobado.py
"""
import os
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar módulos
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
from sqlalchemy import text
from rich.console import Console
from rich.table import Table

# Cargar variables de entorno
load_dotenv()

from src.database import db
from src.config import config

console = Console()


def update_estado_to_aprobado():
    """
    Actualiza todos los registros con estado_etl='PROCESADO' a 'APROBADO'
    en las tres tablas de control
    """
    tables = [
        'control_envios_boletas',
        'control_envios_boletas_procesos',
        'control_envios_boletas_simplificadas'
    ]
    
    console.print("\n[cyan]═══════════════════════════════════════════════════════════[/cyan]")
    console.print("[cyan]  Script de Actualización: PROCESADO → APROBADO[/cyan]")
    console.print("[cyan]═══════════════════════════════════════════════════════════[/cyan]\n")
    
    total_updated = 0
    
    with db.get_session() as session:
        for table in tables:
            console.print(f"[yellow]Procesando tabla:[/yellow] {table}")
            
            # Consultar cuántos registros hay en PROCESADO
            count_query = f"""
                SELECT COUNT(*) as total
                FROM "{config.DB_SCHEMA}"."{table}"
                WHERE estado_etl = 'PROCESADO'
            """
            
            result = session.execute(text(count_query))
            count = result.scalar()
            
            if count == 0:
                console.print(f"  [dim]No hay registros con estado_etl='PROCESADO'[/dim]\n")
                continue
            
            console.print(f"  [blue]Registros encontrados:[/blue] {count}")
            
            # Actualizar registros
            update_query = f"""
                UPDATE "{config.DB_SCHEMA}"."{table}"
                SET estado_etl = 'APROBADO',
                    updated_at = CURRENT_TIMESTAMP
                WHERE estado_etl = 'PROCESADO'
            """
            
            result = session.execute(text(update_query))
            updated = result.rowcount
            
            console.print(f"  [green]✓ Registros actualizados:[/green] {updated}\n")
            total_updated += updated
        
        # Commit de la transacción
        session.commit()
        console.print("[green]✓ Cambios guardados exitosamente[/green]\n")
    
    # Resumen final
    console.print("[cyan]═══════════════════════════════════════════════════════════[/cyan]")
    console.print(f"[green bold]Total de registros actualizados:[/green bold] {total_updated}")
    console.print("[cyan]═══════════════════════════════════════════════════════════[/cyan]\n")
    
    # Mostrar conteo actual por estado
    console.print("[yellow]Distribución actual de estados en control_envios_boletas:[/yellow]\n")
    
    with db.get_session() as session:
        stats_query = f"""
            SELECT estado_etl, COUNT(*) as total
            FROM "{config.DB_SCHEMA}"."control_envios_boletas"
            GROUP BY estado_etl
            ORDER BY total DESC
        """
        
        result = session.execute(text(stats_query))
        rows = result.fetchall()
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Estado ETL", style="yellow")
        table.add_column("Total Registros", justify="right", style="green")
        
        for row in rows:
            table.add_row(row[0], str(row[1]))
        
        console.print(table)
        console.print()


if __name__ == '__main__':
    try:
        update_estado_to_aprobado()
    except Exception as e:
        console.print(f"\n[red bold]✗ Error:[/red bold] {str(e)}\n")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        sys.exit(1)
