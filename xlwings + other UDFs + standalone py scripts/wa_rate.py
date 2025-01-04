import numpy as np
from scipy.optimize import newton
import xlwings as xw

@xw.func
@xw.arg('x_values', ndim=2)
@xw.arg('z_values', ndim=2)
@xw.arg('target', numbers=float)
def wa_return(x_values, z_values, target):
    # Convert input lists of lists to numpy arrays
    x_values = np.array(x_values)
    z_values = np.array(z_values)

    # Define the function for which we want to find the root
    def func(y):
        return np.sum(x_values * ((1 + y / 4) ** z_values)) - target

    # Use the Newton-Raphson method to find the root
    y_initial_guess = 0.5
    y_solution = newton(func, y_initial_guess)

    return y_solution

