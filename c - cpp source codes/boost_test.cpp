#include <boost/lexical_cast.hpp>
#include <iostream>
#include <string>

int main() {
    std::string input;
    std::cout << "Enter a number: ";
    std::getline(std::cin, input);

    try {
        int num = boost::lexical_cast<int>(input);
        num += 10;
        std::cout << "Your number plus 10 is: " << num << std::endl;
    } catch(boost::bad_lexical_cast &) {
        std::cout << "You did not enter a valid number." << std::endl;
    }

    return 0;
}

