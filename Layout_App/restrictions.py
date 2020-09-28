module_dictionary = {
    'WYS_PUESTOTRABAJO_RECTO2PERSONAS': 0,
    'WYS_PUESTOTRABAJO_RECTO4PERSONAS': 1,
    'WYS_PUESTOTRABAJO_RECTO6PERSONAS': 2,
    'WYS_PUESTOTRABAJO_ESTRELLA3PERSONAS': 3,
    'WYS_PUESTOTRABAJO_ESTRELLA6PERSONAS': 4,
    'WYS_PUESTOTRABAJO_ESTRELLA9PERSONAS': 5,
    'WYS_PUESTOTRABAJO_CELL3PERSONAS': 6,
    'WYS_PUESTOTRABAJO_CELL6PERSONAS': 7,
    'WYS_PUESTOTRABAJO_CELL9PERSONAS': 8,
    'WYS_PUESTOTRABAJO_VOLANTE2PERSONAS': 9,
    'WYS_PUESTOTRABAJO_VOLANTE4PERSONAS': 10,
    'WYS_PUESTOTRABAJO_VOLANTE6PERSONAS': 11,
    'WYS_SALAREUNION_REDONDA4PERSONAS': 12,
    'WYS_SALAREUNION_REDONDA5PERSONAS': 13,
    'WYS_SALAREUNION_RECTA6PERSONAS': 14,
    'WYS_SALAREUNION_MEDIATABLE3PERSONAS': 15,
    'WYS_SALAREUNION_MEDIATABLE5PERSONAS': 16,
    'WYS_SALAREUNION_RECTA8PERSONAS': 17,
    'WYS_SALAREUNION_DIRECTORIO10PERSONAS': 18,
    'WYS_SALAREUNION_DIRECTORIO12PERSONAS': 19,
    'WYS_SALAREUNION_DIRECTORIO14PERSONAS': 20,
    'WYS_SALAREUNION_DIRECTORIO16PERSONAS': 21,
    'WYS_SALAREUNION_DIRECTORIO20PERSONAS': 22,
    'WYS_SALACAPACITACION_12PERSONAS': 23,
    'WYS_SALACAPACITACION_19PERSONAS': 24,
    'WYS_SALACAPACITACION_25PERSONAS': 25,
    'WYS_PRIVADO_1PERSONA': 26,
    'WYS_PRIVADO_1PERSONAGUARDADO': 27,
    'WYS_PRIVADO_1PERSONAESTAR': 28,
    'WYS_PRIVADO_1PERSONAMESA': 29,
    'WYS_COLABORATIVO_MEETINGBOOTH2PERSONAS': 30,
    'WYS_COLABORATIVO_MEETINGBOOTH4PERSONAS': 31,
    'WYS_COLABORATIVO_BARRA6PERSONAS': 32,
    'WYS_COLABORATIVO_BARRA8PERSONAS': 33,
    'WYS_COLABORATIVO_BARRA10PERSONAS': 34,
    'WYS_COLABORATIVO_TARIMA13PERSONAS': 35,
    'WYS_LOUNGE_4PERSONAS': 36,
    'WYS_LOUNGE_8PERSONAS': 37,
    'WYS_LOUNGE_3PERSONAS': 38,
    'WYS_LOUNGE_5PERSONAS': 39,
    'WYS_RECEPCION_1PERSONA': 40,
    'WYS_RECEPCION_2PERSONAS': 41,
    'WYS_TRABAJOINDIVIDUAL_QUIETROOM2PERSONAS': 42,
    'WYS_TRABAJOINDIVIDUAL_PHONEBOOTH1PERSONA': 43,
    'WYS_WORKCOFFEECOMEDOR_20PERSONAS': 44,
    'WYS_WORKCOFFEECOMEDOR_16PERSONAS': 45,
    'WYS_WORKCOFFEECOMEDOR_28PERSONAS': 46,
    'WYS_SOPORTE_SALALACTANCIA1PERSONA': 47,
    'WYS_SOPORTE_SERVIDOR1BASTIDOR': 48,
    'WYS_SOPORTE_SERVIDOR2BASTIDORES': 49,
    'WYS_SOPORTE_SERVIDOR3BASTIDORES': 50,
    'WYS_SOPORTE_BAÑOUNIVERSAL1PERSONA': 51,
    'WYS_SOPORTE_BAÑOINDIVIDUAL1PERSONA': 52,
    'WYS_SOPORTE_KITCHENETTE': 53,
    'WYS_SOPORTE_PRINT1': 54,
    'WYS_SOPORTE_PRINT2': 55,
    'WYS_SOPORTE_GUARDADOBAJO': 56,
    'WYS_SOPORTE_GUARDADOALTO': 57,
    'WYS_SOPORTE_LOCKERS': 58,
    'WYS_SOPORTE_BODEGA': 59,
    'WYS_SOPORTE_BAÑOBATERIAFEMENINO3PERSONAS': 60,
    'WYS_SOPORTE_BAÑOBATERIAMASCULINO3PERSONAS': 61,
    'WYS_ESPECIALES_TALLERLABORATORIO4PERSONAS': 62,
    'WYS_ESPECIALES_MINDBREAKROOM1PERSONA': 63,
    'WYS_ESPECIALES_BRAINSTORMING4PERSONAS': 64,
    'WYS_ESPECIALES_BRAINSTORMING7PERSONAS': 65,
    'WYS_ESPECIALES_BRAINSTORMING11PERSONAS': 66,
    }


area_dictionary = {
    'WYS_ENTRANCE': 0,
    'WYS_FACADE_CRYSTAL': 1,
    'WYS_FACADE_OPAQUE': 2,
    'WYS_SHAFT': 3,
    'WYS_CORE': 4,
}

# create weight matrix for modules in areas
mod2area_matrix = []
# create weight matrix for modules near other modules
mod2mod_matrix = []

for m in range(len(module_dictionary)):
    mod2area_matrix.append([0] * len(area_dictionary))

for m in range(len(module_dictionary)):
    mod2mod_matrix.append([0] * len(module_dictionary))


def set_mod2area_matrix_value(mod_dic, area_dic, matrix, module_name, area_name, value):
    row, col = mod_dic[module_name], area_dic[area_name]
    if row is None or col is None:
        pass
    else:
        matrix[row][col] = value


def set_mod2mod_matrix_value(mod_dic, matrix, mod1, mod2, value):
    row, col = mod_dic[mod1], mod_dic[mod2]
    if row is None or col is None:
        pass
    else:
        matrix[row][col] = value


def mod2mod(mod_dic, matrix, mod1, mod2):
    row, col = mod_dic[mod1], mod_dic[mod2]
    return matrix[row][col]


def mod2area(mod_dic, area_dic, matrix, module_name, area_name):
    row, col = mod_dic[module_name], area_dic[area_name]
    return matrix[row][col]


def set_mod2area_val(Modulo, valores):
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, Modulo,
                              'WYS_ENTRANCE', valores[0])
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, Modulo,
                              'WYS_FACADE_CRYSTAL', valores[1])
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, Modulo,
                              'WYS_FACADE_OPAQUE', valores[2])
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, Modulo,
                              'WYS_SHAFT', valores[3])
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, Modulo,
                              'WYS_CORE', valores[4])


set_mod2area_val('WYS_PUESTOTRABAJO_RECTO2PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PUESTOTRABAJO_RECTO4PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PUESTOTRABAJO_RECTO6PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PUESTOTRABAJO_ESTRELLA3PERSONAS', [0, 1, 0, 0, -1])
set_mod2area_val('WYS_PUESTOTRABAJO_ESTRELLA6PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PUESTOTRABAJO_ESTRELLA9PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PUESTOTRABAJO_CELL3PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PUESTOTRABAJO_CELL6PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PUESTOTRABAJO_CELL9PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PUESTOTRABAJO_VOLANTE2PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PUESTOTRABAJO_VOLANTE4PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PUESTOTRABAJO_VOLANTE6PERSONAS', [0, 1, 0, 0, 0])

set_mod2area_val('WYS_SALAREUNION_REDONDA4PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SALAREUNION_REDONDA5PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SALAREUNION_RECTA6PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SALAREUNION_MEDIATABLE3PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SALAREUNION_MEDIATABLE5PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SALAREUNION_RECTA8PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SALAREUNION_DIRECTORIO10PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SALAREUNION_DIRECTORIO12PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SALAREUNION_DIRECTORIO14PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SALAREUNION_DIRECTORIO16PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SALAREUNION_DIRECTORIO20PERSONAS', [0, 1, 0, 0, 0])

set_mod2area_val('WYS_SALACAPACITACION_12PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SALACAPACITACION_19PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SALACAPACITACION_25PERSONAS', [0, 1, 0, 0, 0])

set_mod2area_val('WYS_PRIVADO_1PERSONA', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PRIVADO_1PERSONAGUARDADO', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PRIVADO_1PERSONAESTAR', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_PRIVADO_1PERSONAMESA', [0, 1, 0, 0, 0])

set_mod2area_val('WYS_COLABORATIVO_MEETINGBOOTH2PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_COLABORATIVO_MEETINGBOOTH4PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_COLABORATIVO_BARRA6PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_COLABORATIVO_BARRA8PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_COLABORATIVO_BARRA10PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_COLABORATIVO_TARIMA13PERSONAS', [0, 1, 0, 0, 0])

set_mod2area_val('WYS_LOUNGE_4PERSONAS', [1, 0, 0, 0, 0])
set_mod2area_val('WYS_LOUNGE_8PERSONAS', [1, 0, 0, 0, 0])
set_mod2area_val('WYS_LOUNGE_3PERSONAS', [1, 0, 0, 0, 0])
set_mod2area_val('WYS_LOUNGE_5PERSONAS', [1, 0, 0, 0, 0])

set_mod2area_val('WYS_RECEPCION_1PERSONA', [1, 0, 0, 0, 0])
set_mod2area_val('WYS_RECEPCION_2PERSONAS', [1, 0, 0, 0, 0])

set_mod2area_val('WYS_TRABAJOINDIVIDUAL_QUIETROOM2PERSONAS', [0, 0, 0, 0, 1])
set_mod2area_val('WYS_TRABAJOINDIVIDUAL_PHONEBOOTH1PERSONA', [0, 0, 0, 0, 1])

set_mod2area_val('WYS_WORKCOFFEECOMEDOR_20PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_WORKCOFFEECOMEDOR_16PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_WORKCOFFEECOMEDOR_28PERSONAS', [0, 1, 0, 0, 0])

set_mod2area_val('WYS_SOPORTE_SALALACTANCIA1PERSONA', [0, 1, 0, 0, 0])

set_mod2area_val('WYS_SOPORTE_SERVIDOR1BASTIDOR', [0, 0, 0, 0, 1])
set_mod2area_val('WYS_SOPORTE_SERVIDOR2BASTIDORES', [0, 0, 0, 0, 1])
set_mod2area_val('WYS_SOPORTE_SERVIDOR3BASTIDORES', [0, 0, 0, 0, 1])

set_mod2area_val('WYS_SOPORTE_BAÑOUNIVERSAL1PERSONA', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SOPORTE_BAÑOINDIVIDUAL1PERSONA', [0, 1, 0, 0, 0])

set_mod2area_val('WYS_SOPORTE_KITCHENETTE', [0, 1, 0, 0, 0])

set_mod2area_val('WYS_SOPORTE_PRINT1', [0, 0, 0, 0, 1])
set_mod2area_val('WYS_SOPORTE_PRINT2', [0, 0, 0, 0, 1])

set_mod2area_val('WYS_SOPORTE_GUARDADOBAJO', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_SOPORTE_GUARDADOALTO', [0, 1, 0, 0, 0])

set_mod2area_val('WYS_SOPORTE_LOCKERS', [0, 0, 0, 0, 1])
set_mod2area_val('WYS_SOPORTE_BODEGA', [0, 0, 0, 0, 1])

set_mod2area_val('WYS_SOPORTE_BAÑOBATERIAFEMENINO3PERSONAS', [0, 0, 0, 1, 0])
set_mod2area_val('WYS_SOPORTE_BAÑOBATERIAMASCULINO3PERSONAS', [0, 0, 0, 1, 0])

set_mod2area_val('WYS_ESPECIALES_TALLERLABORATORIO4PERSONAS', [0, 1, 0, 0, 0])

set_mod2area_val('WYS_ESPECIALES_MINDBREAKROOM1PERSONA', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_ESPECIALES_BRAINSTORMING4PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_ESPECIALES_BRAINSTORMING7PERSONAS', [0, 1, 0, 0, 0])
set_mod2area_val('WYS_ESPECIALES_BRAINSTORMING11PERSONAS', [0, 1, 0, 0, 0])



set_mod2mod_matrix_value(module_dictionary, mod2mod_matrix, 'WYS_PUESTOTRABAJO_CELL3PERSONAS', 'WYS_PUESTOTRABAJO_CELL3PERSONAS', 1)
set_mod2mod_matrix_value(module_dictionary, mod2mod_matrix, 'WYS_SALAREUNION_RECTA6PERSONAS', 'WYS_SALAREUNION_RECTA6PERSONAS', 1)
set_mod2mod_matrix_value(module_dictionary, mod2mod_matrix, 'WYS_SOPORTE_PRINT1', 'WYS_RECEPCION_1PERSONA', 1)
set_mod2mod_matrix_value(module_dictionary, mod2mod_matrix, 'WYS_SOPORTE_BAÑOBATERIAFEMENINO3PERSONAS', 'WYS_SOPORTE_BAÑOBATERIAFEMENINO3PERSONAS', 1)
