def set_mod2area_matrix_value(mod_dic, area_dic, matrix, module_name, area_name, value):
    row, col = mod_dic.get(module_name), area_dic.get(area_name)
    if row is None or col is None:
        pass
    else:
        matrix[row][col] = value


def mod2area(mod_dic, area_dic, matrix, module_name, area_name):
    print(module_name, area_name)
    row, col = mod_dic[module_name], area_dic[area_name]
    return matrix[row][col]


module_dictionary = {
    }
cnt = 0
for i in range(100):
    module_dictionary[i] = cnt
    cnt += 1

area_dictionary = {
    'WYS_ENTRANCE': 0,
    'WYS_FACADE_CRYSTAL': 1,
    'WYS_FACADE_OPAQUE': 2,
    'WYS_SHAFT': 3,
    'WYS_CORE': 4,
}

# create weight matrix
mod2area_matrix = []

for m in range(len(module_dictionary)):
    mod2area_matrix.append([0] * len(area_dictionary))

# Add some prefered areas for some modules:
for i in range(0, 30):  # All the workbenchs
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_ENTRANCE', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_FACADE_CRYSTAL', 1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_FACADE_OPAQUE', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_SHAFT', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_CORE', -1)
for i in range(30, 70):  # All the workbenchs
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_ENTRANCE', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_FACADE_CRYSTAL', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_FACADE_OPAQUE', 1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_SHAFT', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_CORE', -1)
for i in range(70, 80):  # All the workbenchs
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_ENTRANCE', 1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_FACADE_CRYSTAL', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_FACADE_OPAQUE', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_SHAFT', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_CORE', -1)
for i in range(80, 100):  # All the workbenchs
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_ENTRANCE', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_FACADE_CRYSTAL', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_FACADE_OPAQUE', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_SHAFT', -1)
    set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_CORE', 1)