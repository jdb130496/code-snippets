#include <iostream>
#include <vector>
#include <string>
#include <memory>
#include <algorithm>

int main() {
    std::cout << "=== Clang C++ Compiler Test ===" << std::endl;
    std::cout << "Compiler: " << __clang_version__ << std::endl;
    std::cout << "C++ Standard: " << __cplusplus << std::endl;
    
    // Test std::vector (C++ STL)
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    std::cout << "\nVector size: " << numbers.size() << std::endl;
    
    // Test algorithms
    auto sum = 0;
    for(const auto& num : numbers) {
        sum += num;
    }
    std::cout << "Sum of vector: " << sum << std::endl;
    
    // Test std::string
    std::string message = "Hello from Clang++!";
    std::cout << "String: " << message << std::endl;
    
    // Test smart pointers (C++11)
    auto ptr = std::make_unique<int>(42);
    std::cout << "Unique pointer value: " << *ptr << std::endl;
    
    // Test lambda (C++11)
    auto multiply = [](int a, int b) { return a * b; };
    std::cout << "Lambda result (3 * 7): " << multiply(3, 7) << std::endl;
    
    return 0;
}
