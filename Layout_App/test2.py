import example_data_piso1
import example_data_v3
import example_data_v4
import example_data_piso2
import example_data_piso3
import SmartLayout2

def main():
    pop_size = 20
    generations = 100
    '''mod2area_matrix = SmartLayout.restrictions.mod2area_matrix
    mod2mod_matrix = SmartLayout.restrictions.mod2mod_matrix

    if 0:
        print('MOD2AREA MATRIX:')

        for row in mod2area_matrix:
            print(row)

        print('MOD2MOD MATRIX:')

        for row in mod2mod_matrix:
            print(row)'''

    output = SmartLayout2.Smart_Layout(example_data_v3.dict_ex, pop_size, generations, viz= False, viz_period=10)
main()