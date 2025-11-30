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
    """Ejecuta transacciones SQL en el orden correcto con manejo de dependencias de IDs"""
    
    def __init__(self, entity_mappings: Dict[str, Any]):
        """
        Args:
            entity_mappings: Dict con los YAMLs cargados {entity_name: yaml_config}
        """
        self.entity_mappings = entity_mappings
        self._parent_child_map = self._build_parent_child_map()
    
    def _build_parent_child_map(self) -> Dict[str, Any]:
        """
        Construye el mapeo de relaciones padre-hijo desde los YAMLs
        
        Returns:
            Dict con estructura:
            {
                'entity_name': {
                    'generates_for': ['child1', 'child2'],
                    'pk_field': 'entity_id'
                }
            }
        """
        parent_child_map = {}
        
        for entity_name, mapping in self.entity_mappings.items():
            # Verificar si esta entidad tiene parent_key o parent_keys
            parent_key = mapping.get('parent_key')
            parent_keys = mapping.get('parent_keys')
            
            if parent_key:
                # parent_key: {field: bol_id, from_entity: boletas}
                fk_field = parent_key['field']
                parent_entity = parent_key['from_entity']
                
                # Registrar en el mapa
                if parent_entity not in parent_child_map:
                    parent_child_map[parent_entity] = {
                        'generates_for': [],
                        'pk_field': fk_field  # El FK es el mismo que el PK del padre
                    }
                
                if entity_name not in parent_child_map[parent_entity]['generates_for']:
                    parent_child_map[parent_entity]['generates_for'].append(entity_name)
            
            elif parent_keys:
                # parent_keys: lista de {field: bov_id, from_entity: bovinos}
                for pk in parent_keys:
                    fk_field = pk['field']
                    parent_entity = pk['from_entity']
                    
                    # Registrar en el mapa
                    if parent_entity not in parent_child_map:
                        parent_child_map[parent_entity] = {
                            'generates_for': [],
                            'pk_field': fk_field
                        }
                    
                    if entity_name not in parent_child_map[parent_entity]['generates_for']:
                        parent_child_map[parent_entity]['generates_for'].append(entity_name)
        
        if config.DEBUG_CLI:
            console.print(f"[cyan]Parent-Child Map construido desde YAMLs:[/cyan]")
            for parent, info in parent_child_map.items():
                console.print(f"  {parent} → {info['generates_for']} (PK: {info['pk_field']})")
        
        return parent_child_map
    
    def execute_inserts(
        self,
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
                # Diccionario para almacenar IDs generados por entidad
                # Estructura: {entity_name: {index_in_transformations: generated_id}}
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
                        
                        # PASO 1: Inyectar IDs de padres en las filas
                        rows = self._inject_parent_ids(
                            entity_name=entity_name,
                            rows=rows,
                            generated_ids=generated_ids
                        )
                        
                        # PASO 2: Ejecutar INSERT y capturar IDs
                        try:
                            inserted_ids = self._execute_entity_insert(
                                session=session,
                                entity_name=entity_name,
                                rows=rows,
                                debug=debug
                            )
                            
                            # PASO 3: Guardar IDs generados para inyectar en hijos
                            if inserted_ids:
                                generated_ids[entity_name] = {
                                    i: inserted_id 
                                    for i, inserted_id in enumerate(inserted_ids)
                                }
                            
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
    
    def _inject_parent_ids(
        self,
        entity_name: str,
        rows: List[Dict[str, Any]],
        generated_ids: Dict[str, Dict[int, int]]
    ) -> List[Dict[str, Any]]:
        """
        Inyecta IDs de entidades padre en las filas de la entidad hija
        Usa configuración desde YAMLs (parent_key/parent_keys)
        
        Args:
            entity_name: Nombre de la entidad hija
            rows: Filas a las que inyectar IDs
            generated_ids: Dict de IDs generados {entity: {row_index: id}}
        
        Returns:
            Filas con IDs de padres inyectados
        """
        if not rows:
            return rows
        
        # Obtener configuración de parent_key desde YAML
        mapping = self.entity_mappings.get(entity_name, {})
        parent_key = mapping.get('parent_key')
        parent_keys = mapping.get('parent_keys')
        
        # Lista de dependencias padre
        parent_dependencies = []
        
        if parent_key:
            # Caso simple: un solo padre
            parent_dependencies.append({
                'entity': parent_key['from_entity'],
                'fk_field': parent_key['field']
            })
        
        elif parent_keys:
            # Caso múltiple: varios padres
            for pk in parent_keys:
                parent_dependencies.append({
                    'entity': pk['from_entity'],
                    'fk_field': pk['field']
                })
        
        if not parent_dependencies:
            # Esta entidad no tiene padres
            return rows
        
        # Inyectar IDs en cada fila
        updated_rows = []
        for row_index, row in enumerate(rows):
            updated_row = row.copy()
            
            for parent_info in parent_dependencies:
                parent_entity = parent_info['entity']
                fk_field = parent_info['fk_field']
                
                # Obtener el ID generado del padre (mismo índice)
                if parent_entity in generated_ids and row_index in generated_ids[parent_entity]:
                    parent_id = generated_ids[parent_entity][row_index]
                    
                    # Inyectar ID en la fila
                    if fk_field in updated_row:
                        updated_row[fk_field] = parent_id
                        
                        if config.DEBUG_CLI:
                            etl_logger.debug(
                                f"[{entity_name}] Inyectando {fk_field}={parent_id} "
                                f"desde {parent_entity} (índice {row_index})"
                            )
            
            updated_rows.append(updated_row)
        
        return updated_rows
    
    def _execute_entity_insert(
        self,
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
        
        # Determinar la columna ID (PK) para RETURNING
        pk_field = self._get_primary_key_field(entity_name)
        
        # SIEMPRE usar RETURNING para capturar IDs
        returning_clause = f' RETURNING "{pk_field}"' if pk_field else ''
        
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
        if pk_field:
            inserted_ids = [row[0] for row in result.fetchall()]
        
        return inserted_ids
    
    @staticmethod
    def _get_primary_key_field(self, entity_name: str) -> str:
        """
        Obtiene el campo de clave primaria para una entidad
        """
        # Intentar obtener desde el mapa construido
        if entity_name in self._parent_child_map:
            return self._parent_child_map[entity_name]['pk_field']
        
        # Fallback: usar prefijo de la entidad + _id
        # terrenos → ter_id, boletas → bol_id
        if entity_name == 'pecuario_otros':
            return 'peot_id'
        elif entity_name == 'miembros_hogar':
            return 'miho_id'
        
        prefix = entity_name[:3] if len(entity_name) >= 3 else entity_name
        return f"{prefix}_id"
    
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
