import data_in
import SmartLayout

def main():
    pop_size = 100
    generations = 200
    output = SmartLayout.Smart_Layout(data_in.dict_ex, pop_size, generations)
    for o in output:
        print(o)
main()