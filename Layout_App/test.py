import example_data_piso1
import example_data_v3
import example_data_v4
import example_data_piso2
import example_data_piso3
import SmartLayout

def main():
    pop_size = 8
    generations = 300
    mod2area_matrix = SmartLayout.restrictions.mod2area_matrix
    mod2mod_matrix = SmartLayout.restrictions.mod2mod_matrix

    if 0:
        print('MOD2AREA MATRIX:')

        for row in mod2area_matrix:
            print(row)

        print('MOD2MOD MATRIX:')

        for row in mod2mod_matrix:
            print(row)

    output = SmartLayout.Smart_Layout(example_data_v3.dict_ex, pop_size, generations, viz= True)
main()