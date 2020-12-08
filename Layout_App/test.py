#import example_data_piso1
import example_data_v3
import example_data_v4
#import example_data_piso2
#import example_data_piso3
import SmartLayout


def main():
    pop_size = 10
    generations = 700
    output = SmartLayout.Smart_Layout(example_data_v3.dict_ex, pop_size, generations, viz= False, viz_period=100)
main()