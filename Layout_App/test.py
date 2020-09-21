import data_in
import SmartLayout

def main():
    pop_size = 1
    generations = 2
    matrix = SmartLayout.restrictions.mod2area_matrix
    for row in matrix:
        print(row)
    output = SmartLayout.Smart_Layout(data_in.dict_ex, pop_size, generations)
    for o in output:
        print(o)
main()