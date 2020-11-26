import random

def randrange(a: float, b: float, div: int):
    """ Calc a random number between interval [a , b] 
        with 'div' divisions 


    Args:
        a (float): left value
        b (float): right value
        div (int): 

    Raises:
        Exception: Div must be grather than 1
        Exception: b must be grather than a

    Returns:
        float: random number between [a,b] interval
    """
    
    # Verify div less than 2
    if div < 2:
        raise Exception("Div must be grather than 1")

    if a >= b:
        raise Exception("b must be grather than a")

    rand_value = random.randrange(0, div, 1)
    
    float_range = rand_value * ((1.0 / (div))* (b - a) ) + a

    return float_range

