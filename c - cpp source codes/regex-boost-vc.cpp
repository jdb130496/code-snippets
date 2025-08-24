#define BOOST_ALL_NO_LIB
#define BOOST_BIND_GLOBAL_PLACEHOLDERS

#include <iostream>
#include <vector>
#include <boost/regex.hpp>

// Function to match patterns in an array of strings
int match_pattern_in_array(const std::vector<std::string>& input_array, const std::string& pattern, std::vector<std::pair<std::string, size_t>>& output_array) {
    boost::regex regex_pattern(pattern, boost::regex_constants::icase);  // Case insensitive match
    std::cout << "Regex pattern compiled successfully.\n";

    // Single-threaded pattern matching
    for (size_t i = 0; i < input_array.size(); ++i) {
        const auto& str = input_array[i];
        if (boost::regex_match(str, regex_pattern)) {
            output_array.push_back(std::make_pair(str, i));  // Store match and original index
        }
    }
    return output_array.size();
}

extern "C" __declspec(dllexport) int match_patterns(const char** input_array, int array_length, const char* pattern, char*** output_array, size_t** output_indices) {
    std::cout << "match_patterns called with array_length: " << array_length << " and pattern: " << pattern << "\n";
    std::vector<std::pair<std::string, size_t>> matches;

    // Convert input array to vector
    std::vector<std::string> input_vec(input_array, input_array + array_length);
    std::cout << "Input array converted to vector.\n";

    // Match patterns
    int num_matches = match_pattern_in_array(input_vec, pattern, matches);
    std::cout << "Pattern matching completed with " << num_matches << " matches.\n";

    // Allocate memory for output_array and indices
    *output_array = (char**)malloc(num_matches * sizeof(char*));
    *output_indices = (size_t*)malloc(num_matches * sizeof(size_t));
    if (!*output_array || !*output_indices) {
        std::cerr << "Memory allocation failed\n";
        return 0;
    }
    std::cout << "Memory allocated for output.\n";

    // Copy matched strings and their original indices to the output
    for (int i = 0; i < num_matches; i++) {
        (*output_array)[i] = strdup(matches[i].first.c_str());
        (*output_indices)[i] = matches[i].second;  // Keep the original index
    }
    std::cout << "Successfully matched patterns\n";
    return num_matches;
}

extern "C" __declspec(dllexport) void free_matches(char** matches, size_t* indices, int match_count) {
    for (int i = 0; i < match_count; i++) {
        free(matches[i]);
    }
    free(matches);
    free(indices);
    std::cout << "Memory freed\n";
}

