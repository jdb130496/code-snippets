#include <cblas.h>
#include <iostream>

int main() {
    int i = 0;
    double A[6] = {1.0, 2.0, 1.0, -3.0, 4.0, -1.0};
    double B[6] = {1.0, 2.0, 1.0, -3.0, 4.0, -1.0};
    double C[9] = {.5, .5, .5, .5, .5, .5, .5, .5, .5};

    cblas_dgemm(CblasColMajor, CblasNoTrans, CblasTrans, 3, 3, 2, 1, A, 3, B, 3, 2, C, 3);

    for (i = 0; i < 9; i++)
        std::cout << C[i] << " ";
    std::cout << std::endl;

    return 0;
}
//Compilation - Powershell: g++ -o openblas_test openblas_test.cpp -ID:\Programs\mingw64\include\openblas -LD:\Programs\mingw64\lib -lopenblas
