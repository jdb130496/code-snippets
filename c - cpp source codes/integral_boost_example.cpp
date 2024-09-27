#include <boost/math/quadrature/gauss_kronrod.hpp>
#include <cmath>
#include <iostream>

double f(double x) {
    return std::log(x);
}

double F(double x) {
    return x*std::log(x) - x;  // Indefinite integral of log(x)
}

int main() {
    using namespace boost::math::quadrature;

    double a = 1;  // lower limit of integration
    double b = 2;  // upper limit of integration

    gauss_kronrod<double, 15> integrator;
    double Q = integrator.integrate(f, a, b);

    std::cout << "The indefinite integral of log(x) dx is " << "x*log(x) - x + C" << std::endl;
    std::cout << "The definite integral of log(x) dx from " << a << " to " << b << " is " << Q << std::endl;

    return 0;
}

