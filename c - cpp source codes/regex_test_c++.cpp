#include <iostream>
#include <regex>

int main() {
    std::string s = "test_string";
    std::regex e ("^[a-zA-Z0-9_]*$");

    bool match = std::regex_match(s, e);
    if (match)
        std::cout << "Match\n";
    else
        std::cout << "No match\n";

    return 0;
}

