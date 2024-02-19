a1 = 3
b1 = 2
c1 = 500

a2 = 2
b2 = 3
c2 = 420

determinant = a1 * b2 - a2 * b1

x = (b2 * c1 - b1 * c2) / determinant
y = (a1 * c2 - a2 * c1) / determinant

print(f"x: {x}, y: {y}")
