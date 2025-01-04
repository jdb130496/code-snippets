# Define the coefficients matrix
A = [[3, 2], [2, 3]]

# Define the constants matrix
B = [500, 420]

# Calculate the determinant of the coefficients matrix
det_A = A[0][0] * A[1][1] - A[0][1] * A[1][0]

# Check if the determinant is not zero
if det_A != 0:
# Calculate the solution using Cramer's rule
    X = [(B[0] * A[1][1] - B[1] * A[0][1]) / det_A, (A[0][0] * B[1] - A[1][0] * B[0]) / det_A]
    print(f'X = {X[0]}, Y = {X[1]}')
else:
    print('The system has no unique solution')
