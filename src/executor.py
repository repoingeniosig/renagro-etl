"""
Ejecutor de transacciones SQL con SQLAlchemy
Maneja la inserción de datos en el orden correcto respetando dependencias
"""
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from rich.console import Console

from .database import db
from .config import config
from .logger import etl_logger

console = Console()


class TransactionExecutor:
    """Ejecuta transacciones SQL en el orden correcto"""
    
    @staticmethod
    def execute_inserts(
        transformations: Dict[str, List[Dict[str, Any]]],
        processing_order: List[List[str]],
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Ejecuta las inserciones en el orden correcto dentro de una transacción
        
        Args:
            transformations: Diccionario {entity_name: [rows]}
            processing_order: Lista de grupos ordenados por dependencias
            debug: Si True, imprime los SQL generados
            
        Returns:
            Diccionario con estadísticas de la ejecución
        """
        results = {
            'success': False,
            'groups_processed': 0,
            'entities_processed': 0,
            'total_rows_inserted': 0,
            'entity_details': {},
            'errors': [],
            'execution_time': 0
        }
        
        start_time = datetime.now()
        
        try:
            with db.get_session() as session:
                # Diccionario para almacenar IDs generados (entity_name -> list of IDs)
                generated_ids = {}
                
                # Procesar cada grupo en orden
                for group_num, group in enumerate(processing_order, 1):
                    if config.DEBUG_CLI:
                        console.print(f"\n{'='*80}")
                        console.print(f"EJECUTANDO GRUPO {group_num}: {', '.join(group)}")
                        console.print(f"{'='*80}")
                    
                    for entity_name in group:
                        if entity_name not in transformations:
                            if config.DEBUG_CLI:
                                console.print(f"⏭️  {entity_name}: Sin datos para insertar")
                            continue
                        
                        rows = transformations[entity_name]
                        if not rows:
                            if config.DEBUG_CLI:
                                console.print(f"⏭️  {entity_name}: Lista vacía")
                            continue
                        
                        # Ejecutar INSERT y obtener IDs generados
                        try:
                            inserted_ids = TransactionExecutor._execute_entity_insert(
                                session=session,
                                entity_name=entity_name,
                                rows=rows,
                                debug=debug
                            )
                            
                            # Guardar IDs generados
                            generated_ids[entity_name] = inserted_ids
                            
                            # Actualizar estadísticas
                            results['entities_processed'] += 1
                            results['total_rows_inserted'] += len(rows)
                            results['entity_details'][entity_name] = {
                                'rows_inserted': len(rows),
                                'ids_generated': inserted_ids
                            }
                            
                            etl_logger.debug(f"{entity_name}: {len(rows)} filas insertadas")
                            
                            if config.DEBUG_CLI:
                                console.print(f"✅ {entity_name}: {len(rows)} filas insertadas")
                                if inserted_ids:
                                    console.print(f"   IDs generados: {inserted_ids[:5]}{'...' if len(inserted_ids) > 5 else ''}")
                        
                        except Exception as e:
                            error_msg = f"Error insertando {entity_name}: {str(e)}"
                            results['errors'].append(error_msg)
                            etl_logger.error(error_msg, exc_info=True)
                            
                            if config.DEBUG_CLI:
                                console.print(f"❌ {error_msg}")
                            raise
                    
                    results['groups_processed'] += 1
                
                # Commit de la transacción completa
                session.commit()
                results['success'] = True
                
                etl_logger.info(f"Transacción completada: {results['total_rows_inserted']} filas insertadas")
                
                if config.DEBUG_CLI:
                    console.print(f"\n{'='*80}")
                    console.print("✅ TRANSACCIÓN COMPLETADA EXITOSAMENTE")
                    console.print(f"{'='*80}")
        
        except SQLAlchemyError as e:
            results['errors'].append(f"Error de SQLAlchemy: {str(e)}")
            etl_logger.error(f"Error de SQLAlchemy: {str(e)}", exc_info=True)
            
            if config.DEBUG_CLI:
                console.print(f"\n{'='*80}")
                console.print(f"❌ ERROR EN LA TRANSACCIÓN: {str(e)}")
                console.print(f"{'='*80}")
            raise
        
        except Exception as e:
            results['errors'].append(f"Error inesperado: {str(e)}")
            etl_logger.error(f"Error inesperado en transacción: {str(e)}", exc_info=True)
            
            if config.DEBUG_CLI:
                console.print(f"\n{'='*80}")
                console.print(f"❌ ERROR INESPERADO: {str(e)}")
                console.print(f"{'='*80}")
            raise
        
        finally:
            end_time = datetime.now()
            results['execution_time'] = (end_time - start_time).total_seconds()
        
        return results
    
    @staticmethod
    def _execute_entity_insert(
        session,
        entity_name: str,
        rows: List[Dict[str, Any]],
        debug: bool = False
    ) -> List[int]:
        """
        Ejecuta el INSERT para una entidad específica
        
        Args:
            session: Sesión de SQLAlchemy
            entity_name: Nombre de la entidad
            rows: Lista de diccionarios con los datos a insertar
            debug: Si True, imprime el SQL generado
            
        Returns:
            Lista de IDs generados
        """
        if not rows:
            return []
        
        # Obtener tabla y schema
        from .mapping_loader import mapping_loader
        entity_mapping = mapping_loader.entity_mappings.get(entity_name)
        
        if not entity_mapping:
            raise ValueError(f"No se encontró mapeo para entidad: {entity_name}")
        
        table_name = entity_mapping.table
        schema = config.DB_SCHEMA
        
        # Construir la sentencia INSERT con RETURNING
        columns = list(rows[0].keys())
        columns_str = ', '.join([f'"{col}"' for col in columns])
        
        # Preparar valores para batch insert
        values_placeholders = []
        all_params = {}
        
        for idx, row in enumerate(rows):
            row_placeholders = []
            for col in columns:
                param_name = f"{col}_{idx}"
                row_placeholders.append(f":{param_name}")
                all_params[param_name] = row[col]
            values_placeholders.append(f"({', '.join(row_placeholders)})")
        
        values_str = ',\n    '.join(values_placeholders)
        
        # Determinar la columna ID para el RETURNING
        # Asumimos que la primera columna numérica con 'id' en el nombre es el ID
        id_column = None
        for col in columns:
            if 'id' in col.lower() and col.endswith('_id'):
                id_column = col
                break
        
        # Si no hay columna ID explícita, no usar RETURNING
        returning_clause = f' RETURNING "{id_column}"' if id_column else ''
        
        sql = f'''
INSERT INTO "{schema}"."{table_name}" ({columns_str})
VALUES
    {values_str}{returning_clause};
        '''.strip()
        
        if config.DEBUG_CLI:
            console.print(f"\n--- SQL para {entity_name} ---")
            console.print(sql[:500] + "..." if len(sql) > 500 else sql)
            console.print(f"Parámetros: {len(all_params)} valores")
        
        # Ejecutar el INSERT
        result = session.execute(text(sql), all_params)
        
        # Obtener IDs generados si hay RETURNING
        inserted_ids = []
        if id_column:
            inserted_ids = [row[0] for row in result.fetchall()]
        
        return inserted_ids
    
    @staticmethod
    def print_execution_summary(results: Dict[str, Any]):
        """
        Imprime un resumen de la ejecución
        
        Args:
            results: Diccionario con los resultados de la ejecución
        """
        if not config.DEBUG_CLI:
            return
        
        console.print(f"\n{'='*80}")
        console.print("RESUMEN DE EJECUCIÓN")
        console.print(f"{'='*80}")
        
        if results['success']:
            console.print(f"✅ Estado: EXITOSO")
        else:
            console.print(f"❌ Estado: FALLIDO")
        
        console.print(f"\n📊 Estadísticas:")
        console.print(f"   Grupos procesados: {results['groups_processed']}")
        console.print(f"   Entidades procesadas: {results['entities_processed']}")
        console.print(f"   Total filas insertadas: {results['total_rows_inserted']}")
        console.print(f"   Tiempo de ejecución: {results['execution_time']:.2f}s")
        
        if results['entity_details']:
            console.print(f"\n📋 Detalle por entidad:")
            for entity_name, details in results['entity_details'].items():
                console.print(f"   {entity_name}: {details['rows_inserted']} filas")
        
        if results['errors']:
            console.print(f"\n❌ Errores ({len(results['errors'])}):")
            for error in results['errors']:
                console.print(f"   - {error}")
        
        console.print(f"{'='*80}\n")
