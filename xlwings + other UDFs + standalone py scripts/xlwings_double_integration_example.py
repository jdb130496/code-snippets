import xlwings as xw
import numpy as np
from scipy.integrate import quad
import math

@xw.func
@xw.arg('func', xw.Range)
@xw.arg('a')
@xw.arg('b')
def MidpointRule(func, a, b):
    # Convert a and b to float
    a = float(a)
    b = float(b)

    # Get the formula from the cell
    formula = func.value  # Get the cell value directly as a string

    # Define the function to integrate
    def f(x):
        # Create a dictionary with the current local symbol table
#        namespace = locals()
        namespace = {**locals(), **math.__dict__}
        return eval(formula, namespace)

    # Perform the integration
    result, error = quad(f, a, b)

    # Return the result as a list of lists
    return [[result]]

@xw.arg('cell', xw.Range)
def get_formula(cell):
    # Get the formula from the cell
    formula = cell.formula

    # Return the formula
    return formula

import xlwings as xw
import numpy as np
from scipy.integrate import dblquad
import math

import xlwings as xw
import numpy as np
from scipy.integrate import dblquad
import math

@xw.func
@xw.arg('func', xw.Range)
@xw.arg('a')
@xw.arg('b')
@xw.arg('c')
@xw.arg('d')
def DoubleIntegral(func, a, b, c, d):
    # Convert the limits to float
    a = float(a)
    b = float(b)
    c = float(c)
    d = float(d)

    # Get the formula from the cell
    formula = func.value  # Get the cell value directly as a string

    # Define the function to integrate
    def f(x, y):  # Note the order of the arguments
        # Create a dictionary with the current local symbol table
        namespace = {**locals(), **math.__dict__}
        return eval(formula, namespace)

    # Perform the double integration
    result, error = dblquad(f, a, b, lambda x: c, lambda x: d)

    # Return the result as a list of lists
    return [[result]]

