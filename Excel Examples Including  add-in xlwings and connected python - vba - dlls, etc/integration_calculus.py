from sympy import Symbol, integrate, log, sin, cos
# Define the variable of integration
x = Symbol('x')
# Compute the indefinite integral of log(x)
result = integrate(cos(x), x)
print(f"The result of the integration is: {result}")
