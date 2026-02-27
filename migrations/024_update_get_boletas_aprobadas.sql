-- Migration: Update get_boletas_aprobadas function
-- Description: Agrega campos NCA (poligonos_boleta.pobo_area), fechaLevantamiento (bol_reg_fecha),
--              y renombra campos con prefijo 'des' para coincidir con la estructura requerida.
-- Date: 2026-02-27

-- ============================================================================
-- 1. ELIMINAR FUNCIÓN ANTERIOR
-- ============================================================================
DROP FUNCTION IF EXISTS api.get_boletas_aprobadas(BIGINT, INT);

-- ============================================================================
-- 2. CREAR FUNCIÓN ACTUALIZADA
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
    -- ======== PARTE 1: Identidad, NCA, fechaLevantamiento, persona, ubicación, contacto, servicios, beneficios, asociación ========
    jsonb_build_object(
      'id', b.bol_id,
      'boletaIdLevanta', b.bol_id_levanta,
      'estadoBoleta', b.bol_estado_boleta,
      'provincia', b.bol_provincia,
      'canton', b.bol_canton,
      'parroquia', b.bol_parroquia,
      'sectorMuestreo', b.bol_sector_muestreo,
      'poligono', b.bol_poligono,
      'numeroUPA', b."bol_numero_UPA",
      'codigoEncuestador', b.bol_codigo_encuestador,
      'numeroBoleta', b.bol_numero_boleta,
      'codigoUPA', b."bol_codigo_UPA",
      'NCA', (
        SELECT SUM(pb.pobo_area)
        FROM sc_renagro_mag.poligonos_boleta pb
        WHERE pb.bol_id = b.bol_id
      ),
      'fechaLevantamiento', b.bol_reg_fecha,
      'isUsoDeSuelo', COALESCE(b.neo_is_uso_suelo_agricola, false),
      'personaProductora', (
        SELECT jsonb_build_object(
          'isPersonaNatural', COALESCE(p.per_persona_natural, false),
          'primerNombre', p.per_primer_nombre,
          'segundoNombre', p.per_segundo_nombre,
          'primerApellido', p.per_primer_apellido,
          'segundoApellido', p.per_segundo_apellido,
          'isPersonaJuridica', COALESCE(p.neo_is_persona_juridica, false),
          'razonSocial', p.per_razon_social,
          'tipoIdentificacion', p.per_tipo_identificacion,
          'identificacion', p.per_identificacion
        )
        FROM sc_renagro_mag.personas p
        WHERE p.per_id = b.per_id
      ),
      'isViveTerrenoEntrevista', COALESCE(b.neo_is_vive_terreno_entrevista, false),
      'provinciaVive', b.bol_provincia_vive,
      'cantonVive', b.bol_canton_vive,
      'parroquiaVive', b.bol_parroquia_vive,
      'distanciaAlDomicilio', b.bol_distancia_al_domicilio,
      'isTelefonoConvencional', COALESCE(b.neo_is_telefono_convencional, false),
      'telefonoConvencional', b.bol_telefono_convencional,
      'isTelefonoCelular', COALESCE(b.neo_is_telefono_celular, false),
      'telefonoCelular', b.bol_telefono_celular,
      'isDireccionEmail', COALESCE(b.neo_is_direccion_email, false),
      'direccionEmail', b.bol_direccion_email,
      'isInternet', COALESCE(b.bol_is_internet, false),
      'isComputadora', COALESCE(b.bol_is_computadora, false),
      'isServicioHigienico', COALESCE(b.bol_is_servicio_higienico, false),
      'isAguaPorTuberia', COALESCE(b.bol_is_agua_por_tuberia, false),
      'isAguaOtroMedio', COALESCE(b.bol_is_agua_otro_medio, false),
      'isEnergiaElectrica', COALESCE(b.bol_is_energia_electrica, false),
      'isAsistenciaTecnica', COALESCE(b.bol_is_asistencia_tecnica, false),
      'isLegalizacionTierra', COALESCE(b.bol_is_legalizacion_tierra, false),
      'isAsesoramientoTecnico', COALESCE(b.bol_is_asesoramiento_tecnico, false),
      'isKitAgricola', COALESCE(b.bol_is_kit_agricola, false),
      'isVacunaAgrocalidad', COALESCE(b.bol_is_vacuna_agrocalidad, false),
      'isAccesoRiego', COALESCE(b.bol_is_acc_riego, false),
      'isAgriculturaFamiliarCamp', COALESCE(b.bol_is_agri_familiar_camp, false),
      'isMaquinaria', COALESCE(b.bol_is_maquinaria, false),
      'isInfraestructura', COALESCE(b.bol_is_infraestructura, false),
      'isEspacioComercio', COALESCE(b.bol_is_espacio_comercio, false),
      'isCredito', COALESCE(b.bol_is_credito, false),
      'isOtroBeneficioEstado', COALESCE(b.neo_is_otro_beneficio, false),
      'otroBeneficioEstado', b.bol_otro_beneficio_estado,
      'isNinguno', COALESCE(b.bol_is_ninguno, false),
      'isPerteneceAsociacionCoop', COALESCE(b.bol_is_pert_asociacion_coop, false),
      'tipoDeMiembro', b.bol_tipo_de_miembro,
      'nombreAsociacionCoop', b.bol_nombre_asociacion_coop
    )

    ||

    -- ======== PARTE 2: Asociación cont., maquinaria forestal, pecuario + subobjetos, suelos, residuos, infraestructura, riego, maquinaria ========
    jsonb_build_object(
      'desRespuestaNegativaMiembro', b.bol_respuesta_negativa_miembro,
      'desMotosierra', b.bol_motosierra,
      'tractorForestal', b.bol_tractor_forestal,
      'empacadoraForestal', b.bol_empacadora_forestal,
      'otroMaquinariaEquipoAcceso', b.bol_otro_maquinaria_equipo_acc,
      'otroMaquinariaEquipo', b.bol_otro_maquinaria_equipo,
      'isPecuarioEnTerreno', COALESCE(b.neo_is_pecuario_terreno, false),
      'isBovinoEnTerreno', COALESCE(b.neo_is_bovino_terreno, false),
      'bovino', (
        SELECT CASE WHEN bov.bov_id IS NOT NULL THEN jsonb_build_object(
          'isBovinoRegistroProduccion', COALESCE(bov.neo_is_registro_produccion, false),
          'terneros', bov.bov_ternero,
          'toretes', bov.bov_torete,
          'toros', bov.bov_toro,
          'subtotalMachos', bov.bov_subtotal_macho,
          'terneras', bov.bov_ternera,
          'vaconas', bov.bov_vacona,
          'vacasEnProduccion', bov.bov_vacas_en_produ,
          'vacasSecas', bov.bov_vacas_seca,
          'subtotalHembras', bov.bov_subtotal_hembra,
          'totalGanado', bov.bov_total_ganado,
          'propositoParaLechePropio', bov.bov_prop_para_leche_propio,
          'propositoParaCarnePropio', bov.bov_prop_para_carne_propio,
          'doblePropositoPropio', bov.bov_doble_prop_propio,
          'subtotalPropio', bov.bov_subtotal_propio,
          'propositoParaLecheAjeno', bov.bov_prop_para_leche_ajeno,
          'propositoParaCarneAjeno', bov.bov_prop_para_carne_ajeno,
          'doblePropositoAjeno', bov.bov_doble_prop_ajeno,
          'subtotalAjenos', bov.bov_subtotal_ajeno,
          'noSabeProposito', bov.bov_no_sabe_prop,
          'totalGanadoProposito', bov.bov_total_ganado_prop,
          'isVacaOrdeniadaAyer', COALESCE(bov.bov_is_vaca_ordeniada_ayer, false),
          'litrosLecheObtenido', bov.bov_litros_leche_obtenido,
          'principalFormaReproduccion', bov.bov_prin_forma_reproduccion,
          'isVacunaBrucelosis', COALESCE(bov.bov_is_vacuna_brucelosi, false),
          'isVacunaCarbunco', COALESCE(bov.bov_is_vacuna_carbunco, false),
          'isVacunaFiebreAftosa', COALESCE(bov.bov_is_vacuna_fiebre_aftosa, false),
          'isVacunaIBR', COALESCE(bov.bov_is_vacuna_ibr, false),
          'isVacunaPapilomatosisBovina', COALESCE(bov.bov_is_vacuna_papilomatosis, false),
          'isNingunaVacuna', COALESCE(bov.bov_is_ninguna_vacuna, false),
          'isNoSabeVacuna', COALESCE(bov.bov_is_no_sabe_vacuna, false),
          'isOtraVacuna', COALESCE(bov.bov_otra_vacuna IS NOT NULL AND bov.bov_otra_vacuna != '', false),
          'otraVacuna', bov.bov_otra_vacuna,
          'principalProduccionGanado', bov.bov_prin_produ_ganado,
          'ordeniadora', bov.bov_ordeniadora,
          'tanqueEnfriamiento', bov.bov_tanque_enfriamiento,
          'isDescansoAlimentoBovino', COALESCE(bov.neo_is_infraestructura_descanso, false),
          'numeroGalpones', bov.bov_galpones_numero,
          'capacidadTotalExplotacion', bov.bov_capacidad_total_explo
        ) ELSE NULL END
        FROM sc_renagro_mag.bovinos bov
        WHERE bov.bov_id = b.bov_id
      ),
      'isExisteGanadoPorcino', COALESCE(b.neo_is_porcino_terreno, false),
      'porcino', (
        SELECT CASE WHEN por.por_id IS NOT NULL THEN jsonb_build_object(
          'isLlevaRegistroPorcino', COALESCE(por.neo_is_registro_produccion, false),
          'menos2MesMachoPorcino', por.por_menos_dos_mes_macho_por,
          'mas2MesMachoPorcino', por.por_mas_dos_mes_macho_por,
          'totalMachoPorcino', por.por_total_macho_por,
          'reproductorMachoPorcino', por.por_reproductor_macho_por,
          'propioMachoPorcino', por.por_propio_macho_por,
          'menos2MesesHembrasPorcino', por.por_menos_dos_mes_hembra_por,
          'mas2MesHembraPorcino', por.por_mas_dos_mes_hembra_por,
          'totalHembraPorcino', por.por_total_hembra_por,
          'reproductorHembraPorcino', por.por_reproductor_hembra_por,
          'propioHembraPorcino', por.por_propio_hembra_por,
          'fuenteReprodruccionPorcina', por.por_fuente_reprodruccion_por,
          'isPestePorcinaClasica', COALESCE(por.por_is_peste_por_clasica, false),
          'isColibacilosisDiarrea', COALESCE(por.por_is_colibacilosis_diarrea, false),
          'isPasteurellaNeumonia', COALESCE(por.por_is_pasteurella_neumonia, false),
          'isNeumoniaPorcinaEnzootica', COALESCE(por.por_is_neumonia_por_enzootica, false),
          'isParvovirusMoquera', COALESCE(por.por_is_parvovirus_moquera, false),
          'isFiebreAftosa', COALESCE(por.por_is_fiebre_aftosa, false),
          'isOtra', COALESCE(por.por_is_otra, false),
          'isNinguna', COALESCE(por.por_is_ninguna, false),
          'isNoSabeNoResponde', COALESCE(por.por_is_no_sabe_no_responde, false),
          'isDescansoAlimentoPorcino', COALESCE(por.neo_is_infraestructura_descanso, false),
          'galponExistentePorcino', por.por_galpon_existente_por,
          'capacidadExplotacionCerdos', por.por_capaci_explot_cerdo
        ) ELSE NULL END
        FROM sc_renagro_mag.porcinos por
        WHERE por.por_id = b.por_id
      ),
      'isPoseePollo', COALESCE(b.neo_is_pollo_terreno, false),
      'pollo', (
        SELECT CASE WHEN pol.pol_id IS NOT NULL THEN jsonb_build_object(
          'isLlevaRegistroPollo', COALESCE(pol.neo_is_registro_produccion, false),
          'isNewcastleEnfermedad', COALESCE(pol.pol_is_newcastle_enfer, false),
          'isSalmonellaEnfermedad', COALESCE(pol.pol_is_salmonella_enfer, false),
          'isGumboroEnfermedad', COALESCE(pol.pol_is_gumboro_enfer, false),
          'isTRTEnfermedad', COALESCE(pol.pol_is_trt_enfer, false),
          'isBronquitisEnfermedad', COALESCE(pol.pol_is_bronquitis_enfer, false),
          'isMycoplasmaEnfermedad', COALESCE(pol.pol_is_mycoplasma_enfer, false),
          'isLlaringotraqueitisEnfermedad', COALESCE(pol.pol_is_llaringotraqueitis_enf, false),
          'isNingunaEnfermedad', COALESCE(pol.pol_is_ninguna_enfer, false),
          'isOtrasEnfermedad', COALESCE(pol.neo_is_otra_enfer, false),
          'otraEnfermedad', pol.pol_otra_enfermedad,
          'isPollosCorresponde', COALESCE(pol.pol_is_pollos_corresponde, false),
          'numAvesTraspatio', pol.pol_num_aves_traspatio,
          'numBroilers', pol.pol_num_broiler,
          'numReproLivianos', pol.pol_num_repro_liviano,
          'numReproPesados', pol.pol_num_repro_pesado,
          'numPonedoras', pol.pol_num_ponedora,
          'numCiclosBroilers', pol.pol_num_ciclos_broiler,
          'numCiclosReproPesados', pol.pol_num_ciclos_repro_pesado,
          'numCiclosReproLivianos', pol.pol_num_ciclos_repro_liviano,
          'numCiclosPonedoras', pol.pol_num_ciclos_ponedora,
          'razonNoRegistro', pol.pol_razon_no_registro,
          'otraRazonNoRegistro', pol.pol_otra_razon_no_registro,
          'galponesPollos', pol.pol_galpones_pollo,
          'explotacionPollos', pol.pol_explotacion_pollo
        ) ELSE NULL END
        FROM sc_renagro_mag.pollos pol
        WHERE pol.pol_id = b.pol_id
      ),
      'pecuarioOtro', (
        SELECT CASE WHEN peot.peot_id IS NOT NULL THEN jsonb_build_object(
          'isGanadoOvino', COALESCE(peot.neo_is_ovino, false),
          'ganadoOvino', peot.peot_ganado_ovino,
          'isGanadoCaprino', COALESCE(peot.neo_is_caprino, false),
          'ganadoCaprino', peot.peot_ganado_caprino,
          'isGanadoCaballar', COALESCE(peot.neo_is_caballar, false),
          'ganadoCaballar', peot.peot_ganado_caballar,
          'isGanadoMular', COALESCE(peot.neo_is_mular, false),
          'ganadoMular', peot.peot_ganado_mular,
          'isAsnos', COALESCE(peot.neo_is_asno, false),
          'ganadoAsnos', peot.peot_ganado_asno,
          'isColmenasAbejasMeliferas', COALESCE(peot.neo_is_colmena_mielifera, false),
          'colmenasAbejasMeliferas', peot.peot_colmena_abeja_melifera,
          'isColmenasAbejasMeliponas', COALESCE(peot.neo_is_colmena_melipona, false),
          'colmenasAbejasMeliponas', peot.peot_colmena_abeja_melipona,
          'isAlpacas', COALESCE(peot.neo_is_alpaca, false),
          'alpacas', peot.peot_alpaca,
          'isLlamas', COALESCE(peot.neo_is_llama, false),
          'llamas', peot.peot_llama,
          'isCuyes', COALESCE(peot.neo_is_cuy, false),
          'cuyes', peot.peot_cuy,
          'isConejos', COALESCE(peot.neo_is_conejo, false),
          'conejos', peot.peot_conejo,
          'isPavos', COALESCE(peot.neo_is_pavo, false),
          'pavos', peot.peot_pavo,
          'isAvestruces', COALESCE(peot.neo_is_avestruz, false),
          'avestruces', peot.peot_avestruce,
          'isCodornices', COALESCE(peot.neo_is_codorniz, false),
          'codornices', peot.peot_codornice,
          'isPatos', COALESCE(peot.neo_is_pato, false),
          'patos', peot.peot_pato,
          'isOtrasEspecies', COALESCE(peot.neo_is_otra_especie, false),
          'otraEspecieNombre', peot.peot_otra_especie_nombre,
          'otrasEspecies', peot.peot_otra_especie
        ) ELSE NULL END
        FROM sc_renagro_mag.pecuarios_otros peot
        WHERE peot.peot_id = b.peot_id
      ),
      'isIncorporaAbono', COALESCE(b.bol_is_incorpora_abono, false),
      'isEvitaErosion', COALESCE(b.bol_is_evita_erosion, false),
      'isRotaCultivo', COALESCE(b.bol_is_rota_cultivo, false),
      'isPastoreoRotativo', COALESCE(b.bol_is_pastoreo_rotativo, false),
      'isNoRealizaMejora', COALESCE(b.bol_is_no_realiza_mejora, false),
      'isOtraPracticaMejora', COALESCE(b.bol_is_otra_practica_mejora, false),
      'otraPracticaMejora', b.bol_otra_practica_mejora,
      'desManejoResiduoAnimal', b.bol_manejo_residuo_animal,
      'otroManejoResiduoAnimal', b.bol_manejo_res_animal_otro,
      'desManejoResiduoAgricola', b.bol_manejo_residuo_agricola,
      'otroManejoResiduoAgricola', b.bol_manejo_res_agricola_otro,
      'isTratamientoAgua', COALESCE(b.bol_is_tratamiento_de_agua, false),
      'desManejoEnvase', b.bol_prin_manejo_envase,
      'manejoEnvaseOtro', b.bol_manejo_envase_otro,
      'isBodega', COALESCE(b.bol_is_bodega, false),
      'isSilo', COALESCE(b.bol_is_silo, false),
      'isEmpacador', COALESCE(b.bol_is_empacador, false),
      'isReservorio', COALESCE(b.bol_is_reservorio, false),
      'isCuartoMaquinariaRiego', COALESCE(b.bol_is_cuarto_maquinaria_riego, false),
      'isInvernadero', COALESCE(b.bol_is_invernadero, false),
      'isConstruccionSecado', COALESCE(b.bol_is_construccion_secado, false),
      'isInfraestructuraNinguno', COALESCE(b.bol_is_infraestructura_ninguno, false),
      'isInfraestructuraOtra', COALESCE(b.neo_is_infraestructura_otra, false),
      'infraestructuraOtra', b.bol_infraestructura_otra,
      'isTerrenoAccedeRiego', COALESCE(b.bol_is_terreno_accede_riego, false),
      'fuenteAguaRiego', b.bol_fuente_agua_riego,
      'sistemaAguaRiego', b.bol_sistema_agua_riego,
      'tractorRueda', b.bol_tractor_rueda,
      'tractorJardin', b.bol_tractor_jardin,
      'tractorOruga', b.bol_tractor_oruga,
      'motocultor', b.bol_motocultor,
      'bombaEstacionariaFumiga', b.bol_bomba_estacionaria_fumiga,
      'plantaElectricaTermica', b.bol_planta_electrica_termica,
      'secadora', b.bol_secadora
    )

    ||

    -- ======== PARTE 3: Más maquinaria, autoconsumo, comprador, sitio ========
    jsonb_build_object(
      'motoguadania', b.bol_motoguadania,
      'arado', b.bol_arado,
      'cosechadora', b.bol_cosechadora,
      'carreton', b.bol_carreton,
      'desgranadora', b.bol_desgranadora,
      'empacadora', b.bol_empacadora,
      'ensiladora', b.bol_ensiladora,
      'enfardadora', b.bol_enfardadora,
      'fangueadora', b.bol_fangueadora,
      'fertilizadora', b.bol_fertilizadora,
      'fumigadora', b.bol_fumigadora,
      'romplow', b.bol_romplow,
      'rastra', b.bol_rastra,
      'rotocultor', b.bol_rotocultor,
      'sembradora', b.bol_sembradora,
      'segadora', b.bol_segadora,
      'subsoladora', b.bol_subsoladora,
      'surcadora', b.bol_surcadora,
      'trilladora', b.bol_trilladora,
      'desBombaAgua', b.bol_bomba_agua,
      'desBombaMochila', b.bol_bomba_mochila,
      'bombaMochilaMotor', b.bol_bomba_mochila_motor,
      'autoconsumoAgricola', b.bol_autoconsumo_agricola,
      'autoconsumoBovina', b.bol_autoconsumo_bovina,
      'autoconsumoPorcicola', b.bol_autoconsumo_porcicola,
      'autoconsumoAvicola', b.bol_autoconsumo_avicola,
      'autoconsumoOtrasAves', b.bol_autoconsumo_otras_ave,
      'autoconsumoOvinoCaprino', b.bol_autoconsumo_ovino_caprino,
      'autoconsumoCuyesConejos', b.bol_autoconsumo_cuyes_conejo,
      'autoconsumoApicola', b.bol_autoconsumo_apicola,
      'autoconsumoForestal', b.bol_autoconsumo_forestal,
      'compradorAgricola', b.bol_comprador_agricola,
      'compradorBovina', b.bol_comprador_bovina,
      'compradorPorcicola', b.bol_comprador_porcicola,
      'compradorAvicola', b.bol_comprador_avicola,
      'compradorOtrasAves', b.bol_comprador_otras_ave,
      'compradorOvinoCaprino', b.bol_comprador_ovino_caprino,
      'desCompradorCuyesConejos', b.bol_comprador_cuyes_conejo,
      'compradorApicola', b.bol_comprador_apicola,
      'compradorForestal', b.bol_comprador_forestal,
      'sitioAgricola', b.bol_sitio_agricola,
      'sitioBovina', b.bol_sitio_bovina,
      'sitioPorcicola', b.bol_sitio_porcicola,
      'sitioAvicola', b.bol_sitio_avicola,
      'sitioOtrasAves', b.bol_sitio_otras_ave,
      'sitioOvinoCaprino', b.bol_sitio_ovino_caprino,
      'desSitioCuyesConejos', b.bol_sitio_cuyes_conejo,
      'sitioApicola', b.bol_sitio_apicola
    )

    ||

    -- ======== PARTE 4: Sitio cont., extensión, préstamos, mano de obra, miembros hogar, informante, coordenadas, terrenos ========
    jsonb_build_object(
      'sitioForestal', b.bol_sitio_forestal,
      'isExtensionAgropecuaria', COALESCE(b.neo_is_extension_agricola, false),
      'extencionAgricolaRecibida', b.bol_exten_agricola_recibida,
      'extencionAgricolaInstitucion', b.bol_exten_agricola_institu,
      'otraExtencionAgricolaInstitucion', b.bol_otra_exten_agri_inst,
      'desNecesidadConocimientos', b.bol_necesidad_conocimiento,
      'otraNecesidadConocimientos', b.bol_otra_nece_conoci,
      'isGestionFinanciamiento', COALESCE(b.bol_is_gestion_financiamiento, false),
      'isPrestamoGestiono', COALESCE(b.neo_is_obtuvo_prestamo, false),
      'prestamoPersona', b.bol_prestamo_persona,
      'prestamoFuente', b.bol_prestamo_fuente,
      'otroPrestamoFuente', b.bol_otro_prest_fuen,
      'prestamoDestino', b.bol_prestamo_destino,
      'otroPrestamoDestino', b.bol_otro_prest_dest,
      'prestamoNegacion', b.bol_prestamo_negacion,
      'otroPrestamoNegacion', b.bol_otro_prest_nega,
      'desPrestamoRazonNoGestiono', b.bol_prestamo_razon_no_gestiono,
      'otraRazonNoGestionoPrestamo', b.bol_otra_razon_no_ges_presta,
      'permanenteHombreNumero', b.bol_permanente_hombre_numero,
      'permanenteHombreSalario', b.bol_permanente_hombre_salario,
      'permanenteMujerNumero', b.bol_permanente_mujer_numero,
      'permanenteMujerSalario', b.bol_permanente_mujer_salario,
      'ocasionalHombreNumero', b.bol_ocasional_hombre_numero,
      'isHombrePagoEfectivo', COALESCE(b.neo_is_pago_efectivo_hombre, false),
      'ocacionalHombreSalario', b.bol_ocasional_hombre_salario,
      'ocasionalMujerNumero', b.bol_ocasional_mujer_numero,
      'isMujerPagoEfectivo', COALESCE(b.neo_is_pago_efectivo_mujer, false),
      'ocacionalMujerSalario', b.bol_ocasional_mujer_salario,
      'miembroHogar', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'noHogar', mh.miho_hogar_numero,
          'primerNombre', mh.miho_primer_nombre,
          'primerApellido', mh.miho_primer_apellido,
          'tipoIdentificacion', mh.miho_tipo_identificacion,
          'identificacion', mh.miho_identificacion,
          'relacionPersonaProd', mh.miho_relacion_persona_prod,
          'manejoTerrenos', mh.miho_manejo_terrenos,
          'edad', mh.miho_edad,
          'genero', mh.miho_genero,
          'autoidentificacion', mh.miho_autoidentificacion,
          'nivelInstruccion', mh.miho_nivel_instruccion,
          'anioMasAltoAprobado', mh.miho_anio_mas_alto_aprob,
          'numeroHorasSemanales', mh.miho_numero_horas_semanales,
          'isFueRemunerado', COALESCE(mh.miho_is_fue_remunerado, false),
          'horasOtrasResponsabilidades', mh.miho_horas_otras_resp
        ) ORDER BY mh.miho_hogar_numero)
        FROM sc_renagro_mag.miembros_hogar mh
        WHERE mh.bol_id = b.bol_id
          AND COALESCE(mh.miho_eliminado, false) = false
      ), '[]'::jsonb),
      'isInformanteProductor', COALESCE(b.neo_is_informante_productor, false),
      'personaInformante', (
        SELECT jsonb_build_object(
          'primerNombre', pi.per_primer_nombre,
          'segundoNombre', pi.per_segundo_nombre,
          'primerApellido', pi.per_primer_apellido,
          'segundoApellido', pi.per_segundo_apellido
        )
        FROM sc_renagro_mag.personas pi
        WHERE pi.per_id = b.bol_persona_info_id
      ),
      'informanteTelefono', b.bol_informante_telefono,
      'informanteRelacion', b.bol_informante_relacion,
      'longitud', b.bol_longitud,
      'latitud', b.bol_latitud,
      'altitud', b.bol_altitud,
      'terrenos', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'terrenoNo', t.ter_terreno_numero,
          'tenencia', t.ter_tenencia,
          'accesoTierra', t.ter_acceso_tierra,
          'coberturaTierra', t.ter_cobertura_tierra,
          'superficieUnidad', t.ter_superficie_unidad,
          'superficie', t.ter_superficie,
          'isInfraestructura', COALESCE(t.ter_is_infraestructura, false),
          'isManoDeObra', COALESCE(t.ter_is_mano_de_obra, false),
          'isMaquinariaImplementos', COALESCE(t.ter_is_maquinaria_implemento, false),
          'isTerrenoPrincipal', COALESCE(t.ter_is_terreno_principal, false),
          'isCultivoEnTerrenos', COALESCE(t.ter_is_cultivo_en_terreno, false),
          'isPoseeEspeciesForestales', COALESCE(t.neo_is_especie_forestal, false),
          'cultivos', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
              'nombreCultivo', c.cul_nombre_cultivo,
              'otroNombreCultivo', c.cul_otro_nombre_cultivo,
              'superficiePlantada', c.cul_superficie_plantada,
              'superficiePlantadaUnidad', c.cul_superficie_plantada_unidad,
              'superficieRiego', c.cul_superficie_riego,
              'superficieRiegoUnidad', c.cul_superficie_riego_unidad,
              'metodoDeRiego', c.cul_metodo_de_riego,
              'cultivoAsociado', c.cul_cultivo_asociado,
              'formaCultivar', c.cul_forma_cultivar,
              'isControlPlagasQuimico', COALESCE(c.cul_is_control_plagas_quimico, false),
              'isControlPlagasOrganico', COALESCE(c.cul_is_control_plagas_organico, false),
              'sacosDeUreaUsado', c.cul_sacos_de_urea_usado,
              'isUsoFertilizanteQuimico', COALESCE(c.cul_is_uso_fert_quimico, false),
              'isUsoFertilizanteOrganico', COALESCE(c.cul_is_uso_fert_organico, false),
              'isUsoSemillaNativaCampesina', COALESCE(c.cul_is_uso_semilla_nativa_camp, false),
              'isUsoMaterialVegetativo', COALESCE(c.cul_is_uso_material_vegetativo, false),
              'isCertificacionOrganica', COALESCE(c.cul_is_certificacion_organica, false),
              'isSeguroAgricola', COALESCE(c.cul_is_seguro_agricola, false),
              'isLlevaRegistroProduccion', COALESCE(c.cul_is_lleva_registro_prod, false)
            ))
            FROM sc_renagro_mag.cultivos c
            WHERE c.ter_id = t.ter_id
              AND COALESCE(c.cul_eliminado, false) = false
          ), '[]'::jsonb),
          'cultivosForestales', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
              'nombreEspecieForestal', f.for_nombre_especie,
              'otroNombreEspecieForestal', f.for_otro_nombre_especie,
              'edadEspecieForestal', f.for_edad_especie,
              'superficiePlantada', f.for_superficie_plantada,
              'superficiePlantadaUnidad', f.for_superficie_plantada_unidad,
              'principalDestinoDeUso', f.for_principal_destino_uso
            ))
            FROM sc_renagro_mag.forestales f
            WHERE f.ter_id = t.ter_id
              AND COALESCE(f.for_eliminado, false) = false
          ), '[]'::jsonb)
        ) ORDER BY t.ter_terreno_numero)
        FROM sc_renagro_mag.terrenos t
        WHERE t.bol_id = b.bol_id
          AND COALESCE(t.ter_eliminado, false) = false
      ), '[]'::jsonb)
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

COMMENT ON FUNCTION api.get_boletas_aprobadas IS 'Retorna boletas aprobadas y enviadas con estructura JSON anidada completa. Incluye NCA (suma de áreas de polígonos) y fechaLevantamiento. Paginación keyset: usar p_after_id con el último id recibido. Máximo 100 registros por página.';

-- ============================================================================
-- 3. RE-OTORGAR PERMISOS SOBRE LA FUNCIÓN
-- ============================================================================
GRANT EXECUTE ON FUNCTION api.get_boletas_aprobadas(BIGINT, INT) TO api_user;
REVOKE EXECUTE ON FUNCTION api.get_boletas_aprobadas(BIGINT, INT) FROM web_anon;
