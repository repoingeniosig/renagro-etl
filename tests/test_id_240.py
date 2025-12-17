#!/usr/bin/env python3
"""Script para probar con _id=240 específicamente"""

from src.database import db
from sqlalchemy import text

with db.get_session() as session:
    # 1. Verificar control_envios_boletas._id=240
    result = session.execute(text("""
        SELECT _id, uuid_boleta, estado_etl, envio_datos_procesados
        FROM sc_renagro_mag.control_envios_boletas
        WHERE _id = 240
    """)).fetchone()
    
    print("=== CONTROL_ENVIOS_BOLETAS (_id=240) ===")
    if result:
        print(f"_id={result[0]}, uuid_boleta={result[1]}, estado_etl={result[2]}, envio_datos_procesados={result[3]}")
    else:
        print("❌ No existe registro con _id=240")
        exit(1)
    
    # 2. Verificar boletas con bol_id_levanta=240
    result = session.execute(text("""
        SELECT bol_id, bol_id_levanta
        FROM sc_renagro_mag.boletas
        WHERE bol_id_levanta = '240'
    """)).fetchone()
    
    print("\n=== BOLETAS (bol_id_levanta='240') ===")
    if result:
        bol_id = result[0]
        print(f"bol_id={bol_id}, bol_id_levanta={result[1]}")
    else:
        print("❌ No existe boleta con bol_id_levanta='240'")
        exit(1)
    
    # 3. Verificar terrenos de esta boleta
    result = session.execute(text("""
        SELECT ter_id, bol_id, ter_terreno_numero, ter_superficie
        FROM sc_renagro_mag.terrenos
        WHERE bol_id = :bol_id
        ORDER BY ter_id
    """), {"bol_id": bol_id}).fetchall()
    
    print(f"\n=== TERRENOS (bol_id={bol_id}) ===")
    if result:
        print(f"Total: {len(result)} terrenos")
        for row in result:
            print(f"  ter_id={row[0]}, bol_id={row[1]}, terrenoNo={row[2]}, superficie={row[3]}")
            
            # Cultivos de cada terreno
            cultivos = session.execute(text("""
                SELECT cul_id, ter_id, cul_nombre_cultivo
                FROM sc_renagro_mag.cultivos
                WHERE ter_id = :ter_id
            """), {"ter_id": row[0]}).fetchall()
            
            if cultivos:
                print(f"    Cultivos: {len(cultivos)}")
                for c in cultivos:
                    print(f"      cul_id={c[0]}, ter_id={c[1]}, nombre={c[2]}")
            
            # Forestales de cada terreno
            forestales = session.execute(text("""
                SELECT for_id, ter_id, for_nombre_especie
                FROM sc_renagro_mag.forestales
                WHERE ter_id = :ter_id
            """), {"ter_id": row[0]}).fetchall()
            
            if forestales:
                print(f"    Forestales: {len(forestales)}")
                for f in forestales:
                    print(f"      for_id={f[0]}, ter_id={f[1]}, especie={f[2]}")
    else:
        print("❌ No hay terrenos para esta boleta")
    
    # 4. Verificar miembros_hogar
    result = session.execute(text("""
        SELECT miho_id, bol_id, miho_primer_nombre, miho_primer_apellido
        FROM sc_renagro_mag.miembros_hogar
        WHERE bol_id = :bol_id
    """), {"bol_id": bol_id}).fetchall()
    
    print(f"\n=== MIEMBROS_HOGAR (bol_id={bol_id}) ===")
    if result:
        print(f"Total: {len(result)} miembros")
        for row in result:
            print(f"  miho_id={row[0]}, bol_id={row[1]}, nombre={row[2]} {row[3]}")
    else:
        print("No hay miembros del hogar")
