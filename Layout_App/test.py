import example_data_piso1
import example_data_piso2
import example_data_piso3
import SmartLayout

def main():
    pop_size = 50
    generations = 100
    matrix = SmartLayout.restrictions.mod2area_matrix
    #for row in matrix:
        #print(row)
    output = SmartLayout.Smart_Layout(example_data_piso1.dict_ex, pop_size, generations)
    #for o in output:
    #    print(o)
main()