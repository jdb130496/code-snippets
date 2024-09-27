#include <stdio.h>
#include <math.h>
#include <lapacke.h>

void print_fraction(double value, double accuracy) {
    if (accuracy <= 0.0 || accuracy >= 1.0) {
        printf("Accuracy out of range");
        return;
    }

    int sign = (value > 0) ? 1 : -1;
    value = fabs(value);

    int n1 = 1, d1 = 0;
    int n2 = 0, d2 = 1;
    double b = value;
    do {
        double a = floor(b);
        double aux = n1;
        n1 = a * n1 + n2;
        n2 = aux;
        aux = d1;
        d1 = a * d1 + d2;
        d2 = aux;
        b = 1 / (b - a);
    } while (fabs((double)n1 / d1 - value) > value * accuracy);

    printf("%d/%d\n", sign * n1, d1);
}

int main (int argc, const char * argv[]) {
   double a[4] = {7.0, 10.0, 3.0, 2.0};  // The data in the matrix A in column-major order
   int n = 2;  // The order of matrix A
   int nrhs = 1;  // The number of right hand sides, i.e., the number of columns in the matrix B
   int lda = 2;  // The leading dimension of the array A
   int ipiv[2];  // The pivot indices that define the permutation matrix P
   double b[2] = {28.0, 34.0};  // The data in matrix B
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
   printf("Solution: \n");
   print_fraction(b[0], 1e-10);
   print_fraction(b[1], 1e-10);

   exit(0);
}
//Compilation: g++ -o lapacke_test_fraction lapacke_test_new_ROW_Fraction_Printing.c -llapacke -lblas
