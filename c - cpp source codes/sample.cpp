#include <random>
#include <Eigen/Dense>
#include <iostream>
int main() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(-10000, 10000);

    Eigen::Matrix3i mat3i;
    for(int i=0; i<mat3i.rows(); ++i)
        for(int j=0; j<mat3i.cols(); ++j)
            mat3i(i,j) = dis(gen);

    std::cout << "Here is mat3i:\n" << mat3i << std::endl;
    std::cout << "The sum of its coefficients is " << mat3i.sum() << std::endl;

    return 0;
}

