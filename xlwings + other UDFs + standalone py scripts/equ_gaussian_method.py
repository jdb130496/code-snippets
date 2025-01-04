def gauss_elimination(A, B):
    n = len(B)
    for i in range(n):
        max_el = abs(A[i][i])
        max_row = i
        for k in range(i + 1, n):
            if abs(A[k][i]) > max_el:
                max_el = abs(A[k][i])
                max_row = k
        if max_row != i:
            A[i], A[max_row] = A[max_row], A[i]
            B[i], B[max_row] = B[max_row], B[i]
        for k in range(i+1, n):
            c = -A[k][i] / A[i][i]
            A[k][i] = 0
            for j in range(i + 1, n):
                A[k][j] += c * A[i][j]
            B[k] += c * B[i]
    x = [0 for i in range(n)]
    for i in range(n - 1, -1, -1):
        x[i] = B[i] / A[i][i]
        for k in range(i - 1, -1, -1):
            B[k] -= A[k][i] * x[i]
    return (x)
A = [[1, 0.15], [0.40, 1]]
B = [700, 1900]
X, Y = gauss_elimination(A, B)
print(f"X = {X:.4f}, Y = {Y:.4f}")

