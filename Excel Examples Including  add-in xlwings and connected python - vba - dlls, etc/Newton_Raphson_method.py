from scipy.optimize import newton
def interest_rate(pv, fv, n, tol=0.00000000000001):
    f = lambda r: pv * (1 + r) ** n - fv
    f_prime = lambda r: n * pv * (1 + r) ** (n - 1)
    r = newton(f, 0.1, f_prime, tol=tol)
    return r
pv = float(input("Enter the present value: "))
fv = float(input("Enter the future value: "))
n = int(input("Enter the number of periods: "))
r = interest_rate(pv, fv, n)
print(f"The interest rate is {r:.12%}")
