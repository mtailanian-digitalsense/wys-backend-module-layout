#import example_data_piso1
import example_data_v3
import example_data_v4
#import example_data_piso2
#import example_data_piso3
import SmartLayout
import SmartLayout_2


def main():
    pop_size = 5
    generations = 10
    output = SmartLayout.Smart_Layout(example_data_v3.dict_ex, pop_size, generations, viz=True, viz_period=10)
main()