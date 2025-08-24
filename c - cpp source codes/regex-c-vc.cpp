#include <iostream>
#include <vector>
#include <regex>
#include <windows.h>

typedef struct {
    const char** input_array;
    int array_length;
    const char* pattern;
    char*** output_array;
    int* num_matches;
} thread_data_t;

DWORD WINAPI match_patterns_thread(LPVOID arg) {
    thread_data_t* data = (thread_data_t*)arg;
    std::regex regex_pattern(data->pattern, std::regex_constants::icase);

    int match_count = 0;
    char** matches = (char**)malloc(data->array_length * sizeof(char*));
    if (matches == NULL) {
        return 1;
    }

    for (int i = 0; i < data->array_length; i++) {
        if (std::regex_match(data->input_array[i], regex_pattern)) {
            matches[match_count] = _strdup(data->input_array[i]);
            if (matches[match_count] == NULL) {
                for (int j = 0; j < match_count; j++) {
                    free(matches[j]);
                }
                free(matches);
                return 1;
            }
            match_count++;
        }
    }

    *data->output_array = matches;
    *data->num_matches = match_count;
    return 0;
}

extern "C" __declspec(dllexport) int match_patterns(const char** input_array, int array_length, const char* pattern, char*** output_array) {
    HANDLE thread;
    DWORD thread_id;
    thread_data_t data = {input_array, array_length, pattern, output_array, 0};
    int num_matches = 0;
    data.num_matches = &num_matches;

    thread = CreateThread(NULL, 0, match_patterns_thread, &data, 0, &thread_id);
    if (thread == NULL) {
        return 0;
    }

    WaitForSingleObject(thread, INFINITE);
    CloseHandle(thread);
    return num_matches;
}

extern "C" __declspec(dllexport) void free_matches(char** matches, int match_count) {
    for (int i = 0; i < match_count; i++) {
        free(matches[i]);
    }
    free(matches);
}

int main() {
    const char* input_array[] = {"example1", "test2", "sample3"};
    int array_length = 3;
    const char* pattern = "test";
    char** output_array;
    int num_matches = match_patterns(input_array, array_length, pattern, &output_array);

    std::cout << "Number of matches: " << num_matches << std::endl;
    for (int i = 0; i < num_matches; i++) {
        std::cout << "Match: " << output_array[i] << std::endl;
        free(output_array[i]);
    }
    free(output_array);

    return 0;
}

