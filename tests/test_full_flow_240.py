#!/usr/bin/env python3
"""Test completo del flujo JSON builder con _id=240"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import db
from src.mapping_loader_envio_mag import mapping_loader_envio_mag
from src.data_fetcher_envio_mag import DataFetcherEnvioMAG
from src.json_builder_envio_mag import JSONBuilderEnvioMAG
from sqlalchemy import text
from src import config
import json

# Habilitar debug
config.DEBUG_CLI = True

print("=== TEST: Flujo completo con _id=240 ===\n")

with db.get_session() as session:
    # 1. Simular lo que hace batch_processor
    test_control_id = 240
    
    print(f"Control ID: {test_control_id}")
    
    # 2. Cargar mapeo principal
    main_mapping = mapping_loader_envio_mag.load_main_mapping()
    print(f"Mapeo principal: {main_mapping.entity}\n")
    
    # 3. Obtener datos de boleta usando bol_id_levanta=240
    fetcher = DataFetcherEnvioMAG(session)
    boleta_data = fetcher.fetch_table_data(
        main_mapping.table,
        [str(test_control_id)],  # Convertir a string
        'bol_id_levanta',
        use_cache=False
    )
    
    if not boleta_data:
        print("❌ No se encontró boleta")
        sys.exit(1)
    
    boleta_row = boleta_data[0]
    bol_id = boleta_row.get('bol_id')
    print(f"✅ Boleta encontrada: bol_id={bol_id}, bol_id_levanta={boleta_row.get('bol_id_levanta')}\n")
    
    # 4. Obtener todos los datos relacionados
    all_mappings = mapping_loader_envio_mag.load_all_mappings_recursive('main.yml', use_redis_cache=False)
    all_related_data = fetcher.fetch_all_related_tables(
        all_mappings,
        [bol_id],  # Usar bol_id como root_ids
        main_mapping,
        boleta_data,
        'bol_id_levanta'
    )
    
    print("\n=== Datos relacionados obtenidos ===")
    for table_name, rows in all_related_data.items():
        print(f"  - {table_name}: {len(rows)} registros")
    
    # 5. Mostrar detalles de terrenos
    if 'terrenos' in all_related_data:
        print(f"\n=== TERRENOS ({len(all_related_data['terrenos'])} registros) ===")
        for idx, terreno in enumerate(all_related_data['terrenos']):
            print(f"  [{idx}] ter_id={terreno.get('ter_id')}, bol_id={terreno.get('bol_id')}, terrenoNo={terreno.get('ter_terreno_numero')}")
    
    # 6. Mostrar detalles de cultivos
    if 'cultivos' in all_related_data:
        print(f"\n=== CULTIVOS ({len(all_related_data['cultivos'])} registros) ===")
        for idx, cultivo in enumerate(all_related_data['cultivos']):
            print(f"  [{idx}] cul_id={cultivo.get('cul_id')}, ter_id={cultivo.get('ter_id')}, nombre={cultivo.get('cul_nombre_cultivo')}")
    
    # 7. Mostrar detalles de miembros_hogar
    if 'miembros_hogar' in all_related_data:
        print(f"\n=== MIEMBROS_HOGAR ({len(all_related_data['miembros_hogar'])} registros) ===")
        for idx, miembro in enumerate(all_related_data['miembros_hogar']):
            print(f"  [{idx}] miho_id={miembro.get('miho_id')}, bol_id={miembro.get('bol_id')}, nombre={miembro.get('miho_primer_nombre')} {miembro.get('miho_primer_apellido')}")
    
    # 8. Construir JSON
    print("\n=== CONSTRUYENDO JSON ===\n")
    json_result = JSONBuilderEnvioMAG.build_nested_structure(
        boleta_row,
        main_mapping,
        all_related_data
    )
    
    # 9. Verificar resultado
    print("\n=== RESULTADO JSON ===")
    print(f"boletaIdLevanta: {json_result.get('boletaIdLevanta')}")
    print(f"terrenos: {len(json_result.get('terrenos', []))} elementos")
    
    if json_result.get('terrenos'):
        for idx, terreno in enumerate(json_result['terrenos']):
            print(f"  [{idx}] terrenoNo={terreno.get('terrenoNo')}, superficie={terreno.get('superficie')}, cultivos={len(terreno.get('cultivos', []))}, cultivosForestales={len(terreno.get('cultivosForestales', []))}")
    
    # Verificar miembros del hogar
    # El mapeo usa personaProductora (object) no miembrosHogar (array)
    if json_result.get('personaProductora'):
        print(f"\npersonaProductora: {json_result['personaProductora'].get('primerNombre')} {json_result['personaProductora'].get('primerApellido')}")
    
    # 10. Guardar JSON completo
    with open('./tmp/boleta_240.json', 'w', encoding='utf-8') as f:
        json.dump(json_result, f, indent=2, ensure_ascii=False)
    print(f"\n✅ JSON completo guardado en ./tmp/boleta_240.json")
    
    # Mostrar resumen
    print(f"\n=== RESUMEN ===")
    if len(json_result.get('terrenos', [])) == 2:
        print("✅ Array terrenos tiene 2 elementos (CORRECTO)")
    else:
        print(f"❌ Array terrenos tiene {len(json_result.get('terrenos', []))} elementos (esperado: 2)")
    
    if json_result.get('personaProductora'):
        print("✅ personaProductora está presente (CORRECTO)")
    else:
        print("❌ personaProductora está ausente")
