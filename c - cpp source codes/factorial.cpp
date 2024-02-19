#include <boost/multiprecision/cpp_int.hpp>
using namespace boost::multiprecision;
using namespace std;

cpp_int factorial(int num) {
    cpp_int fact = 1;
    for (int i = num; i > 1; --i)
        fact *= i;
    return fact;
}

int main() {
    int num = 20;
    cout << "Factorial of " << num << " = " << factorial(num);
    return 0;
}

