-- Migration: Rewrite get_boletas_aprobadas with exact example.json fields
-- Description: La salida JSON tiene exactamente los mismos campos que example.json, ni más ni menos.
-- Date: 2026-02-27

-- ============================================================================
-- 1. ELIMINAR FUNCIÓN ANTERIOR
-- ============================================================================
DROP FUNCTION IF EXISTS api.get_boletas_aprobadas(BIGINT, INT);

-- ============================================================================
-- 2. CREAR FUNCIÓN CON CAMPOS EXACTOS DE example.json
-- ============================================================================
CREATE OR REPLACE FUNCTION api.get_boletas_aprobadas(
  p_after_id BIGINT DEFAULT 0,
  p_limit INT DEFAULT 100
)
RETURNS SETOF JSON
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = sc_renagro_mag, api, public
AS $$
  SELECT (
    -- ======== PARTE 1 (28 campos): identidad, persona, terrenos, miembros, pecuario, des-campos ========
    jsonb_build_object(
      'id', b.bol_id,
      'codigoEncuestador', b.bol_codigo_encuestador,
      'poligono', b.bol_poligono,
      'numeroUPA', b."bol_numero_UPA",
      'NCA', (
        SELECT SUM(pb.pobo_area)
        FROM sc_renagro_mag.poligonos_boleta pb
        WHERE pb.bol_id = b.bol_id
      ),
      'estadoBoleta', b.bol_estado_boleta,
      'provincia', b.bol_provincia,
      'canton', b.bol_canton,
      'parroquia', b.bol_parroquia,
      'sectorMuestreo', b.bol_sector_muestreo,
      'fechaLevantamiento', b.bol_reg_fecha,
      'personaProductora', (
        SELECT jsonb_build_object(
          'primerNombre', p.per_primer_nombre,
          'segundoNombre', p.per_segundo_nombre,
          'primerApellido', p.per_primer_apellido,
          'segundoApellido', p.per_segundo_apellido,
          'identificacion', p.per_identificacion,
          'tipoIdentificacion', p.per_tipo_identificacion,
          'isPersonaJuridica', COALESCE(p.neo_is_persona_juridica, false),
          'isPersonaNatural', COALESCE(p.per_persona_natural, false),
          'isUsoDeSuelo', COALESCE(b.neo_is_uso_suelo_agricola, false)
        )
        FROM sc_renagro_mag.personas p
        WHERE p.per_id = b.per_id
      ),
      'telefonoConvencional', b.bol_telefono_convencional,
      'telefonoCelular', b.bol_telefono_celular,
      'direccionEmail', b.bol_direccion_email,
      'numeroBoleta', b.bol_numero_boleta,
      'terrenos', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'terrenoNo', t.ter_terreno_numero,
          'superficie', t.ter_superficie,
          'superficieUnidad', t.ter_superficie_unidad,
          'isCultivoEnTerrenos', COALESCE(t.ter_is_cultivo_en_terreno, false),
          'accesoTierra', t.ter_acceso_tierra,
          'coberturaTierra', t.ter_cobertura_tierra,
          'tenencia', t.ter_tenencia,
          'isPoseeEspeciesForestales', COALESCE(t.neo_is_especie_forestal, false),
          'isInfraestructura', COALESCE(t.ter_is_infraestructura, false),
          'isManoDeObra', COALESCE(t.ter_is_mano_de_obra, false),
          'isMaquinariaImplementos', COALESCE(t.ter_is_maquinaria_implemento, false)
        ) ORDER BY t.ter_terreno_numero)
        FROM sc_renagro_mag.terrenos t
        WHERE t.bol_id = b.bol_id
          AND COALESCE(t.ter_eliminado, false) = false
      ), '[]'::jsonb),
      'miembroHogar', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'primerNombre', mh.miho_primer_nombre,
          'primerApellido', mh.miho_primer_apellido,
          'autoidentificacion', mh.miho_autoidentificacion,
          'genero', mh.miho_genero
        ) ORDER BY mh.miho_hogar_numero)
        FROM sc_renagro_mag.miembros_hogar mh
        WHERE mh.bol_id = b.bol_id
          AND COALESCE(mh.miho_eliminado, false) = false
      ), '[]'::jsonb),
      'isPecuarioEnTerreno', COALESCE(b.neo_is_pecuario_terreno, false),
      'bovino', (
        SELECT CASE WHEN bov.bov_id IS NOT NULL THEN jsonb_build_object(
          'vacasEnProduccion', bov.bov_vacas_en_produ,
          'principalProduccionGanado', bov.bov_prin_produ_ganado,
          'totalGanado', bov.bov_total_ganado
        ) ELSE NULL END
        FROM sc_renagro_mag.bovinos bov
        WHERE bov.bov_id = b.bov_id
      ),
      'porcino', (
        SELECT CASE WHEN por.por_id IS NOT NULL THEN jsonb_build_object(
          'totalMachoPorcino', por.por_total_macho_por,
          'totalHembraPorcino', por.por_total_hembra_por
        ) ELSE NULL END
        FROM sc_renagro_mag.porcinos por
        WHERE por.por_id = b.por_id
      ),
      'pollo', (
        SELECT CASE WHEN pol.pol_id IS NOT NULL THEN jsonb_build_object(
          'numBroilers', pol.pol_num_broiler,
          'numPonedoras', pol.pol_num_ponedora
        ) ELSE NULL END
        FROM sc_renagro_mag.pollos pol
        WHERE pol.pol_id = b.pol_id
      ),
      'pecuarioOtro', (
        SELECT CASE WHEN peot.peot_id IS NOT NULL THEN jsonb_build_object(
          'isAlpacas', COALESCE(peot.neo_is_alpaca, false),
          'isAsnos', COALESCE(peot.neo_is_asno, false),
          'isAvestruces', COALESCE(peot.neo_is_avestruz, false),
          'isColmenasAbejasMeliferas', COALESCE(peot.neo_is_colmena_mielifera, false),
          'colmenasAbejasMeliferas', peot.peot_colmena_abeja_melifera,
          'isColmenasAbejasMeliponas', COALESCE(peot.neo_is_colmena_melipona, false),
          'isConejos', COALESCE(peot.neo_is_conejo, false),
          'isCodornices', COALESCE(peot.neo_is_codorniz, false),
          'isCuyes', COALESCE(peot.neo_is_cuy, false),
          'cuyes', peot.peot_cuy,
          'isGanadoCaballar', COALESCE(peot.neo_is_caballar, false),
          'isGanadoCaprino', COALESCE(peot.neo_is_caprino, false),
          'isGanadoMular', COALESCE(peot.neo_is_mular, false),
          'isGanadoOvino', COALESCE(peot.neo_is_ovino, false),
          'isLlamas', COALESCE(peot.neo_is_llama, false),
          'isOtrasEspecies', COALESCE(peot.neo_is_otra_especie, false),
          'isPavos', COALESCE(peot.neo_is_pavo, false)
        ) ELSE NULL END
        FROM sc_renagro_mag.pecuarios_otros peot
        WHERE peot.peot_id = b.peot_id
      ),
      'desManejoResiduoAnimal', b.bol_manejo_residuo_animal,
      'desManejoResiduoAgricola', b.bol_manejo_residuo_agricola,
      'desManejoEnvase', b.bol_prin_manejo_envase,
      'desNecesidadConocimientos', b.bol_necesidad_conocimiento,
      'desPrestamoRazonNoGestiono', b.bol_prestamo_razon_no_gestiono
    )

    ||

    -- ======== PARTE 2 (28 campos): des-campos cont., flags, maquinaria, mejoras ========
    jsonb_build_object(
      'desRespuestaNegativaMiembro', b.bol_respuesta_negativa_miembro,
      'desSitioCuyesConejos', b.bol_sitio_cuyes_conejo,
      'desCompradorCuyesConejos', b.bol_comprador_cuyes_conejo,
      'isAccesoRiego', COALESCE(b.bol_is_acc_riego, false),
      'desBombaAgua', b.bol_bomba_agua,
      'desBombaMochila', b.bol_bomba_mochila,
      'desMotosierra', b.bol_motosierra,
      'isBodega', COALESCE(b.bol_is_bodega, false),
      'isSilo', COALESCE(b.bol_is_silo, false),
      'isEmpacador', COALESCE(b.bol_is_empacador, false),
      'isReservorio', COALESCE(b.bol_is_reservorio, false),
      'isCuartoMaquinariaRiego', COALESCE(b.bol_is_cuarto_maquinaria_riego, false),
      'isInvernadero', COALESCE(b.bol_is_invernadero, false),
      'isConstruccionSecado', COALESCE(b.bol_is_construccion_secado, false),
      'tractorForestal', b.bol_tractor_forestal,
      'empacadoraForestal', b.bol_empacadora_forestal,
      'tractorRueda', b.bol_tractor_rueda,
      'tractorJardin', b.bol_tractor_jardin,
      'tractorOruga', b.bol_tractor_oruga,
      'motocultor', b.bol_motocultor,
      'bombaEstacionariaFumiga', b.bol_bomba_estacionaria_fumiga,
      'plantaElectricaTermica', b.bol_planta_electrica_termica,
      'secadora', b.bol_secadora,
      'motoguadania', b.bol_motoguadania,
      'isNoReapzaMejora', COALESCE(b.bol_is_no_realiza_mejora, false),
      'isIncorporaAbono', COALESCE(b.bol_is_incorpora_abono, false),
      'isAsistenciaTecnica', COALESCE(b.bol_is_asistencia_tecnica, false),
      'isCredito', COALESCE(b.bol_is_credito, false)
    )
  )::json
  FROM sc_renagro_mag.boletas b
  INNER JOIN sc_renagro_mag.control_envios_boletas ceb
    ON ceb.uuid_boleta = b.neo_uuid_boleta::TEXT
  WHERE ceb.estado_etl = 'APROBADO'
    AND ceb.envio_datos_procesados = 'ENVIADO'
    AND COALESCE(b.bol_eliminado, false) = false
    AND b.bol_id > p_after_id
  ORDER BY b.bol_id ASC
  LIMIT LEAST(p_limit, 100);
$$;

COMMENT ON FUNCTION api.get_boletas_aprobadas IS 'Retorna boletas aprobadas y enviadas con estructura JSON exacta de example.json. Paginación keyset: usar p_after_id con el último id recibido. Máximo 100 registros por página.';

-- ============================================================================
-- 3. RE-OTORGAR PERMISOS
-- ============================================================================
GRANT EXECUTE ON FUNCTION api.get_boletas_aprobadas(BIGINT, INT) TO api_user;
REVOKE EXECUTE ON FUNCTION api.get_boletas_aprobadas(BIGINT, INT) FROM web_anon;
