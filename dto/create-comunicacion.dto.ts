import { ApiProperty } from '@nestjs/swagger';
import {
    IsBoolean,
    IsNumber,
    IsOptional,
    IsString,
    Max,
    Min,
} from 'class-validator';
import { IsCatalogo } from 'src/anotaciones/isCatalogo';
import { IsNumero } from 'src/anotaciones/isNumero';


export class CreateComunicacionDto {
    comunicacionId: number;

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
        title: ' Hubo una sensibilización planificada ',
        description: 'boolean',
    })
    @IsBoolean()
    @IsOptional()
    isSensibilizacionPlanificada: boolean;

    @ApiProperty({
        title: ' Hubo una socialización planificada ',
        description: 'boolean',
    })
    @IsBoolean()
    @IsOptional()
    isSocializacionPlanificada: boolean;

    @ApiProperty({
        title: ' Hubo una avanzada planificada ',
        description: 'boolean',
    })
    @IsBoolean()
    @IsOptional()
    isAvanzadaPlanificada: boolean;

    @ApiProperty({
        title: 'Número de asociaciones involucradas',
        description: 'number decimales:0',
        minimum: 0,
        maximum: 999,
    })
    @Min(0)
    @Max(999)
    @IsNumber()
    @IsNumero(0)
    @IsOptional()
    numeroAsociaciones: number;

    @ApiProperty({
        title: 'Número de actores involucrados',
        description: 'number decimales:0',
        minimum: 0,
        maximum: 999,
    })
    @Min(0)
    @Max(999)
    @IsNumber()
    @IsNumero(0)
    @IsOptional()
    numeroActores: number;

    @ApiProperty({
        title: 'Número de planes de levantamiento',
        description: 'number decimales:0',
        minimum: 0,
        maximum: 999,
    })
    @Min(0)
    @Max(999)
    @IsNumber()
    @IsNumero(0)
    @IsOptional()
    numeroPlanesLevantamiento: number;

    @ApiProperty({
        title: ' Hubo una sensibilización ejecutada ',
        description: 'boolean',
    })
    @IsBoolean()
    @IsOptional()
    isSensibilizacionEjecutada: boolean;
    
    @ApiProperty({
        title: ' Hubo una socialización ejecutada ',
        description: 'boolean',
    })
    @IsBoolean()
    @IsOptional()
    isSocializacionEjecutada: boolean;

    @ApiProperty({
        title: ' Hubo una avanzada ejecutada ',
        description: 'boolean',
    })
    @IsBoolean()
    @IsOptional()
    isAvanzadaEjecutada: boolean;

}