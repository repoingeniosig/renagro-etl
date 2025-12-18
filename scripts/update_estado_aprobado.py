#!/usr/bin/env python3
"""
Script para actualizar el estado_etl de registros PROCESADOS a APROBADO
en la tabla control_envios_boletas

Este script permite aprobar manualmente los registros procesados para que
puedan ser enviados a la API remota del MAG.

Uso:
    python3 scripts/update_estado_aprobado.py [--all | --id ID1,ID2,ID3 | --uuid UUID1,UUID2]

Opciones:
    --all          Actualizar TODOS los registros con estado_etl='PROCESADO'
    --id           Lista de IDs separados por coma (ej: --id 1,2,3)
    --uuid         Lista de UUIDs separados por coma (ej: --uuid abc-123,def-456)
    --dry-run      Mostrar lo que se haría sin ejecutar cambios
    --verbose      Mostrar información detallada

Ejemplos:
    # Aprobar todos los registros procesados
    python3 scripts/update_estado_aprobado.py --all

    # Aprobar registros específicos por ID
    python3 scripts/update_estado_aprobado.py --id 1,5,10

    # Aprobar por UUID
    python3 scripts/update_estado_aprobado.py --uuid abc-123-def,xyz-789-ghi

    # Dry-run para ver qué se actualizaría
    python3 scripts/update_estado_aprobado.py --all --dry-run
"""
import sys
import argparse
from pathlib import Path
from sqlalchemy import text, func
from datetime import datetime

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database import db
from config import config
from logger import etl_logger


class EstadoAprobadoUpdater:
    """Actualiza registros de PROCESADO a APROBADO"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.schema = config.DB_SCHEMA
        self.table = 'control_envios_boletas'
        self.dry_run = dry_run
        self.verbose = verbose
    
    def update_all(self) -> int:
        """
        Actualiza TODOS los registros con estado_etl='PROCESADO' a 'APROBADO'
        
        Returns:
            Número de registros actualizados
        """
        query_select = f"""
            SELECT _id, uuid_boleta
            FROM "{self.schema}".{self.table}
            WHERE estado_etl = 'PROCESADO'
            ORDER BY _id ASC
        """
        
        query_update = f"""
            UPDATE "{self.schema}".{self.table}
            SET estado_etl = 'APROBADO',
                updated_at = CURRENT_TIMESTAMP
            WHERE estado_etl = 'PROCESADO'
        """
        
        with db.get_session() as session:
            # Obtener registros a actualizar
            result = session.execute(text(query_select))
            records = result.fetchall()
            
            if not records:
                print("✓ No hay registros con estado_etl='PROCESADO' para actualizar")
                return 0
            
            count = len(records)
            
            if self.verbose:
                print(f"\n📋 Registros a actualizar: {count}")
                print("─" * 60)
                for idx, (id_val, uuid_val) in enumerate(records[:10], 1):
                    print(f"  {idx}. _id={id_val}, uuid_boleta={uuid_val}")
                if count > 10:
                    print(f"  ... y {count - 10} más")
                print("─" * 60)
            
            if self.dry_run:
                print(f"\n🔍 [DRY-RUN] Se actualizarían {count} registros a estado_etl='APROBADO'")
                print(f"Query: {query_update}")
                return count
            
            # Ejecutar UPDATE
            session.execute(text(query_update))
            session.commit()
            
            print(f"✅ Actualizados {count} registros a estado_etl='APROBADO'")
            etl_logger.info(f"[update_estado_aprobado] Actualizados {count} registros PROCESADO → APROBADO")
            
            return count
    
    def update_by_ids(self, ids: list) -> int:
        """
        Actualiza registros específicos por _id
        
        Args:
            ids: Lista de IDs a actualizar
        
        Returns:
            Número de registros actualizados
        """
        if not ids:
            print("❌ No se proporcionaron IDs")
            return 0
        
        # Convertir a integers
        try:
            ids = [int(id_val) for id_val in ids]
        except ValueError as e:
            print(f"❌ Error: Los IDs deben ser números enteros - {e}")
            return 0
        
        ids_str = ','.join(str(id_val) for id_val in ids)
        
        query_select = f"""
            SELECT _id, uuid_boleta, estado_etl
            FROM "{self.schema}".{self.table}
            WHERE _id IN ({ids_str})
            ORDER BY _id ASC
        """
        
        query_update = f"""
            UPDATE "{self.schema}".{self.table}
            SET estado_etl = 'APROBADO',
                updated_at = CURRENT_TIMESTAMP
            WHERE _id IN ({ids_str})
              AND estado_etl = 'PROCESADO'
        """
        
        with db.get_session() as session:
            # Verificar registros existentes
            result = session.execute(text(query_select))
            records = result.fetchall()
            
            if not records:
                print(f"❌ No se encontraron registros con los IDs especificados: {ids}")
                return 0
            
            # Verificar cuáles están en estado PROCESADO
            procesados = [(id_val, uuid_val) for id_val, uuid_val, estado in records if estado == 'PROCESADO']
            
            if not procesados:
                estados = {estado for _, _, estado in records}
                print(f"⚠️  Los registros existen pero no están en estado PROCESADO (estados: {estados})")
                return 0
            
            count = len(procesados)
            
            if self.verbose:
                print(f"\n📋 Registros a actualizar: {count}/{len(records)}")
                print("─" * 60)
                for id_val, uuid_val in procesados:
                    print(f"  _id={id_val}, uuid_boleta={uuid_val}")
                print("─" * 60)
            
            if self.dry_run:
                print(f"\n🔍 [DRY-RUN] Se actualizarían {count} registros a estado_etl='APROBADO'")
                print(f"Query: {query_update}")
                return count
            
            # Ejecutar UPDATE
            session.execute(text(query_update))
            session.commit()
            
            print(f"✅ Actualizados {count} registros a estado_etl='APROBADO'")
            etl_logger.info(f"[update_estado_aprobado] Actualizados {count} registros PROCESADO → APROBADO (IDs: {ids})")
            
            return count
    
    def update_by_uuids(self, uuids: list) -> int:
        """
        Actualiza registros específicos por uuid_boleta
        
        Args:
            uuids: Lista de UUIDs a actualizar
        
        Returns:
            Número de registros actualizados
        """
        if not uuids:
            print("❌ No se proporcionaron UUIDs")
            return 0
        
        # Construir placeholders para SQL
        placeholders = ','.join([f":uuid_{i}" for i in range(len(uuids))])
        params = {f"uuid_{i}": uuid for i, uuid in enumerate(uuids)}
        
        query_select = f"""
            SELECT _id, uuid_boleta, estado_etl
            FROM "{self.schema}".{self.table}
            WHERE uuid_boleta IN ({placeholders})
            ORDER BY _id ASC
        """
        
        query_update = f"""
            UPDATE "{self.schema}".{self.table}
            SET estado_etl = 'APROBADO',
                updated_at = CURRENT_TIMESTAMP
            WHERE uuid_boleta IN ({placeholders})
              AND estado_etl = 'PROCESADO'
        """
        
        with db.get_session() as session:
            # Verificar registros existentes
            result = session.execute(text(query_select), params)
            records = result.fetchall()
            
            if not records:
                print(f"❌ No se encontraron registros con los UUIDs especificados")
                return 0
            
            # Verificar cuáles están en estado PROCESADO
            procesados = [(id_val, uuid_val) for id_val, uuid_val, estado in records if estado == 'PROCESADO']
            
            if not procesados:
                estados = {estado for _, _, estado in records}
                print(f"⚠️  Los registros existen pero no están en estado PROCESADO (estados: {estados})")
                return 0
            
            count = len(procesados)
            
            if self.verbose:
                print(f"\n📋 Registros a actualizar: {count}/{len(records)}")
                print("─" * 60)
                for id_val, uuid_val in procesados:
                    print(f"  _id={id_val}, uuid_boleta={uuid_val}")
                print("─" * 60)
            
            if self.dry_run:
                print(f"\n🔍 [DRY-RUN] Se actualizarían {count} registros a estado_etl='APROBADO'")
                print(f"Query: {query_update}")
                return count
            
            # Ejecutar UPDATE
            session.execute(text(query_update), params)
            session.commit()
            
            print(f"✅ Actualizados {count} registros a estado_etl='APROBADO'")
            etl_logger.info(f"[update_estado_aprobado] Actualizados {count} registros PROCESADO → APROBADO (UUIDs)")
            
            return count
    
    def show_stats(self):
        """Muestra estadísticas de registros por estado"""
        query = f"""
            SELECT estado_etl, COUNT(*) as count
            FROM "{self.schema}".{self.table}
            GROUP BY estado_etl
            ORDER BY estado_etl
        """
        
        with db.get_session() as session:
            result = session.execute(text(query))
            records = result.fetchall()
        
        print("\n📊 Estadísticas de registros por estado:")
        print("─" * 40)
        for estado, count in records:
            print(f"  {estado:15} : {count:6} registros")
        print("─" * 40)


def main():
    parser = argparse.ArgumentParser(
        description='Actualiza estado_etl de PROCESADO a APROBADO en control_envios_boletas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Actualizar todos los registros PROCESADOS')
    group.add_argument('--id', type=str, help='Lista de IDs separados por coma (ej: 1,2,3)')
    group.add_argument('--uuid', type=str, help='Lista de UUIDs separados por coma')
    group.add_argument('--stats', action='store_true', help='Mostrar solo estadísticas')
    
    parser.add_argument('--dry-run', action='store_true', help='Mostrar cambios sin ejecutar')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada')
    
    args = parser.parse_args()
    
    updater = EstadoAprobadoUpdater(dry_run=args.dry_run, verbose=args.verbose)
    
    try:
        # Mostrar estadísticas iniciales si verbose
        if args.verbose or args.stats:
            updater.show_stats()
        
        if args.stats:
            return
        
        print("\n" + "="*60)
        print("🔄 ACTUALIZACIÓN DE ESTADO ETL: PROCESADO → APROBADO")
        print("="*60)
        
        if args.dry_run:
            print("⚠️  MODO DRY-RUN: No se ejecutarán cambios reales")
        
        # Ejecutar según opción
        count = 0
        if args.all:
            count = updater.update_all()
        elif args.id:
            ids = [id_val.strip() for id_val in args.id.split(',')]
            count = updater.update_by_ids(ids)
        elif args.uuid:
            uuids = [uuid.strip() for uuid in args.uuid.split(',')]
            count = updater.update_by_uuids(uuids)
        
        # Mostrar estadísticas finales si se hicieron cambios
        if count > 0 and not args.dry_run and args.verbose:
            print()
            updater.show_stats()
        
        print("\n" + "="*60)
        print(f"✅ Proceso completado: {count} registros actualizados")
        print("="*60)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        etl_logger.error(f"[update_estado_aprobado] Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
