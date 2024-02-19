#include <stdio.h>
#include <lapack.h>

int main() {
  // Matrix dimensions
  const int m = 3;
  const int n = 1;  // Number of right-hand sides

  // Allocate memory for matrices
  double *A = (double *)malloc(m * m * sizeof(double));
  double *B = (double *)malloc(m * n * sizeof(double));

  // Allocate memory for pivot information
  int32_t *ipiv = (int32_t *)malloc(m * sizeof(int32_t));

  // Initialize A with the coefficients from your system of equations
  A[0] = 3; A[1] = 2; A[2] = -1;
  A[3] = 2; A[4] = -2; A[5] = 4;
  A[6] = -1; A[7] = 0.5; A[8] = -1;

  // Initialize B with the constants from your system of equations
  B[0] = 1;
  B[1] = -2;
  B[2] = 0;

  // Solve a system of linear equations: AX = B
  int info;
  dgesv_(&m, &n, A, &m, ipiv, B, &m, &info);

  // Check if the solution was successfully found
  if (info == 0) {
    printf("Solution found!\n");

    // Print the solution
    for (int i = 0; i < m; ++i) {
      printf("X[%d] = %f\n", i, B[i]);
    }
  } else {
    printf("Error: dgesv_ failed with code %d\n", info);
  }

  // Free allocated memory
  free(A);
  free(B);
  free(ipiv);

  return 0;
}
// Testing lapack C / C++ library - Compilation: g++ -L/d/Programs/mingw64/lib -o lapack_test lapack_test.c -llapack
