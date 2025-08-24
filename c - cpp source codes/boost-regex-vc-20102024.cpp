#define BOOST_ALL_NO_LIB
#define BOOST_BIND_GLOBAL_PLACEHOLDERS
#include <iostream>
#include <vector>
#include <boost/thread.hpp>
#include <boost/regex.hpp>
#include <boost/bind.hpp>

extern "C" {
    // Function to match patterns in an array of strings
    __declspec(dllexport) int __cdecl match_pattern_in_array(const std::vector<std::string>& input_array, const std::string& pattern, std::vector<std::string>& output_array) {
        boost::regex regex_pattern(pattern, boost::regex_constants::icase); // Case insensitive match

        for (const auto& str : input_array) {
            if (boost::regex_match(str, regex_pattern)) {
                output_array.push_back(str);
            }
        }
        return output_array.size();
    }

    // Example usage (removed main function to comply with DLL requirements)
    __declspec(dllexport) int __cdecl match_patterns(const char** input_array, int array_length, const char* pattern, char*** output_array) {
        std::vector<std::string> matches;

        // Convert input array to vector
        std::vector<std::string> input_vec(input_array, input_array + array_length);

        // Match patterns
        int num_matches = match_pattern_in_array(input_vec, pattern, matches);

        // Allocate memory for output_array
        *output_array = (char**)malloc(num_matches * sizeof(char*));

        // Copy matched strings to output array
        for (int i = 0; i < num_matches; i++) {
            (*output_array)[i] = strdup(matches[i].c_str());
        }

        return num_matches;
    }

    // Function to free the allocated memory for matches
    __declspec(dllexport) void __cdecl free_matches(char** matches, int match_count) {
        for (int i = 0; i < match_count; i++) {
            free(matches[i]);
        }
        free(matches);
    }
}

