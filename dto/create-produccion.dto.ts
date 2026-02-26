import { ApiProperty } from '@nestjs/swagger';
import {
    IsBoolean,
    IsNumber,
    MaxLength,
    IsOptional,
    IsString,
    Max,
    Min,
} from 'class-validator';
import { IsCatalogo } from 'src/anotaciones/isCatalogo';
import { IsNumero } from 'src/anotaciones/isNumero';
import { IsTexto } from 'src/anotaciones/isTexto';

export class CreateProduccionDto {
    produccionId: number;

    @ApiProperty({ title: 'Provincia ', description: ' catalogo:PROV ' })
    @IsString()
    @IsCatalogo('PROV')
    @IsOptional()
    provincia: string;

    @ApiProperty({ title: 'Cantón ', description: ' catalogo:CANT ' })
    @IsString()
    @IsCatalogo('CANT')
    @IsOptional()
    canton: string;

    @ApiProperty({ title: 'Parroquia ', description: ' catalogo:PARR ' })
    @IsString()
    @IsCatalogo('PARR')
    @IsOptional()
    parroquia: string;

    @ApiProperty({
        title: 'Polígono',
        description: 'string',
        maximum: 255,
    })
    @MaxLength(255)
    @IsString()
    @IsTexto()
    @IsOptional()
    poligono: string;

    @ApiProperty({
        title: 'Estado del polígono',
        description: 'string',
        maximum: 100,
    })
    @MaxLength(100)
    @IsString()
    @IsTexto()
    @IsOptional()
    poligonoEstado: string;

    @ApiProperty({
        title: 'UPA planificada',
        description: 'number',
        minimum: 0,
        maximum: 9999999,
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    upaPlanificada: number;

    @ApiProperty({
        title: 'UPA levantada',
        description: 'number',
        minimum: 0,
        maximum: 9999999,
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    upaLevantada: number;

    @ApiProperty({
        title: 'Persona productora planificada',
        description: 'number',
        minimum: 0,
        maximum: 9999999,
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    personaProductoraPlanificada: number;
    @ApiProperty({
        title: 'Persona productora levantada',
        description: 'number',
        minimum: 0,
        maximum: 9999999,
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    personaProductoraLevantada: number;

    @ApiProperty({
        title: 'Área del polígono planificada',
        description: 'number',
        minimum: 0,
        maximum: 9999999,
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    poligonoAreaPlanificada: number;

    @ApiProperty({
        title: 'Área del polígono levantada',
        description: 'number',
        minimum: 0,
        maximum: 9999999,
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    poligonoAreaLevantada: number;

    @ApiProperty({
        title: 'Control de calidad del polígono',
        description: 'string',
        maximum: 100,
    })
    @MaxLength(100)
    @IsString()
    @IsTexto()
    @IsOptional()
    poligonoControlCalidad: string;
    @ApiProperty({
        title: 'Muestra planificada',
        description: 'number',
        minimum: 0,
        maximum: 9999999,
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    muestraPlanificada: number;
    @ApiProperty({
        title: 'Muestra ejecutada',
        description: 'number',
        minimum: 0,
        maximum: 9999999,
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    muestraEjecutada: number;

    @ApiProperty({
        title: 'Boleta UPA planificada',
        description: 'boolean',
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    boletaUpaPlanificada: number;

    @ApiProperty({
        title: 'Boleta UPA ejecutada',
        description: 'boolean',
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    boletaUpaEjecutada: number;

    @ApiProperty({
        title: 'Control de calidad',
        description: ''
    })
    @IsString()
    @IsOptional()
    controlCalidad: string;

    @ApiProperty({
        title: 'Boleta control de calidad',
        description: ''
    })
    @IsString()
    @IsOptional()
    boletaControlCalidad: string;

    @ApiProperty({
        title: 'Previo fase 1',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    previoFase1: number;

    @ApiProperty({
        title: 'Previo fase 2',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    previoFase2: number;

    @ApiProperty({
        title: 'Proceso total',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    procesoTotal: number;

    @ApiProperty({
        title: 'Prelevanta planificado',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    prelevantaPlanificado: number;

    @ApiProperty({
        title: 'Prelevanta levantado',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    prelevantaLevantado: number;

    @ApiProperty({
        title: 'Polígono planificado',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    poligonoPlanificado: number;

    @ApiProperty({
        title: 'Polígono ejecutado',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    poligonoEjecutado: number;

    @ApiProperty({
        title: 'Área agropecuaria planificada',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    poligonoAreaAgropecuariaPlanificada: number;

    @ApiProperty({
        title: 'Área agropecuaria ejecutada',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    poligonoAreaAgropecuariapEjecutada: number;

    @ApiProperty({
        title: 'Área forestal planificada',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    poligonoAreaForestalPlanificada: number;

    @ApiProperty({
        title: 'Área forestal ejecutada',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    poligonoAreaForestalEjecutada: number;

    @ApiProperty({
        title: 'Boleta noupa planificada',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    boletaNoupaPlanificada: number;

    @ApiProperty({
        title: 'Boleta noupa ejecutada',
        description: ''
    })
    @IsNumber()
    @IsNumero(0)
    @Min(0)
    @Max(9999999)
    @IsOptional()
    boletaNoupaEjecutada: number;

    @ApiProperty({
        title: 'Equipo',
        description: ''
    })
    @IsString()
    @IsOptional()
    equipo: string;

    @ApiProperty({
        title: 'Encuestador',
        description: ''
    })
    @IsString()
    @IsOptional()
    encuestador: string;

    @ApiProperty({
        title: 'Unidad de numeración',
        description: ''
    })
    @IsString()
    @IsOptional()
    unidadNumeracion: string;

    @ApiProperty({
        title: 'Unidad estándar',
        description: ''
    })
    @IsString()
    @IsOptional()
    unidadEstandar: string;
    

}