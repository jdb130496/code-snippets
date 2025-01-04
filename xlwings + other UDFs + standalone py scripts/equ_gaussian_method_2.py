def gauss_elimination(A, B):
    n = len(B)
    for i in range(n):
        pivot = a[i][i]
        for j in range(i+1, n):
            ratio = a[j][i]/pivot
            for k in range(n):
                a[j][k] = a[j][k] - ratio*a[i][k]
            b[j] = b[j] - ratio*b[i]
    x = [0]*n
    for i in range(n-1, -1, -1):
        s = sum(a[i][j]*x[j] for j in range(i+1, n))
        x[i] = (b[i]-s)/a[i][i]
    return x
a = [[3, 2], [2, 3]]
b = [500, 420]
x = gauss_elimination(a,b)
print("X=",x[0], "Y=", x[1])    

