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


export class CreateCapacitacionDto {
    capacitacionId: number;

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
        title: 'Nombre del evento (capacitación)',
        description: 'string',
        maximum: 255,
    })
    @MaxLength(255)
    @IsString()
    @IsTexto()
    @IsOptional()
    evento: string;

    @ApiProperty({
        title: 'Primer nombre de persona capacitada. ',
        description: 'string',
        maximum: 20,
    })
    @MaxLength(20)
    @IsString()
    @IsTexto()
    @IsOptional()
    primerNombre: string;

    @ApiProperty({
        title: 'Primer apellido de persona capacitada. ',
        description: 'string',
        maximum: 20,
    })
    @MaxLength(20)
    @IsString()
    @IsTexto()
    @IsOptional()
    primerApellido: string;

    @ApiProperty({
        title: 'Tipo de capacitación. ',
        description: 'string',
    })
    @MaxLength(50)
    @IsString()
    @IsTexto()
    @IsOptional()
    tipoCapacitacion: string;

    @ApiProperty({
        title:
            'Se recapacita a la persona.',
        description: 'boolean',
    })
    @IsBoolean()
    @IsOptional()
    isRecapacitacion: boolean;

    @ApiProperty({
        title:
            'Tipo de estado de capacitación. ',
        description: 'string',
    })
    @MaxLength(50)
    @IsString()
    @IsTexto()
    @IsOptional()
    estadoCapacitacion: string;

    @ApiProperty({
        title:
            'Tipo de función de la persona. ',
        description: 'string',
    })
    @MaxLength(50)
    @IsString()
    @IsTexto()
    @IsOptional()
    tipoFuncion: string;
}