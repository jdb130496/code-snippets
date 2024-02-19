#include <stdio.h>
#include <lapacke.h>

int main (int argc, const char * argv[]) {
   double a[4] = {2.0, 3.0, 5.0, -4.0};  // The data in the matrix A in column-major order
   int n = 2;  // The order of matrix A
   int nrhs = 1;  // The number of right hand sides, i.e., the number of columns in the matrix B
   int lda = 2;  // The leading dimension of the array A
   int ipiv[2];  // The pivot indices that define the permutation matrix P
   double b[2] = {13.0, 6.0};  // The data in matrix B
   int ldb = 1;  // The leading dimension of the array B
   int info;  // Output parameter, if info=0, the execution is successful.

   // Solve the equations A*X = B
   info = LAPACKE_dgesv(LAPACK_ROW_MAJOR, n, nrhs, a, lda, ipiv, b, ldb);

   if(info > 0) {
       printf("The diagonal element of the triangular factor of A,\n");
       printf("U(%i,%i) is zero, so that A is singular;\n", info, info);
       printf("the solution could not be computed.\n");
       exit(1);
   }

   // Print solution
   printf("Solution: \n%lf\n%lf\n", b[0], b[1]);

   exit(0);
}
// Compilation: g++ -o lapacke_test_new_ROW lapacke_test_new_ROW.c -llapacke -lblas -lm Note: ldb = 1
