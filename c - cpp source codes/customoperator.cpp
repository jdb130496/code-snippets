// CustomClass.cpp
#include <iostream>

extern "C" {
    __declspec(dllexport) void compare_custom(double* arr1, double* arr2, int length, bool* result);
}

class CustomClass {
public:
    double value;

    CustomClass(double v) : value(v) {}

    // Overloaded operator==
    bool operator==(const CustomClass& other) const {
        return value == other.value;
    }

    // Custom operator for demonstration
    bool operator%(const CustomClass& other) const {
        return static_cast<int>(value) % static_cast<int>(other.value) == 0;
    }
};

void compare_custom(double* arr1, double* arr2, int length, bool* result) {
    for (int i = 0; i < length; ++i) {
        CustomClass obj1(arr1[i]);
        CustomClass obj2(arr2[i]);
        result[i] = (obj1 % obj2);  // Using custom operator%
    }
}

