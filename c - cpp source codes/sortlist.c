#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <direct.h> // For _getcwd

// Function to convert a string to Proper Case
void toProperCase(char *str) {
    int i = 0;
    int capitalizeNext = 1;

    while (str[i]) {
        if (isspace(str[i])) {
            capitalizeNext = 1;
        } else if (capitalizeNext) {
            str[i] = toupper(str[i]);
            capitalizeNext = 0;
        } else {
            str[i] = tolower(str[i]);
        }
        i++;
    }
}

// Function to sort the list alphabetically
void sort(char **arr, int n) {
    char *temp;
    for (int i = 0; i < n - 1; i++) {
        for (int j = i + 1; j < n; j++) {
            if (strcmp(arr[i], arr[j]) > 0) {
                temp = arr[i];
                arr[i] = arr[j];
                arr[j] = temp;
            }
        }
    }
}

int main() {
    FILE *inputFile, *outputFile;
    char filename[] = "D:\\Programs\\Msys2\\home\\j1304\\Downloads\\usblist.txt";  // input file
    char outputname[] = "D:\\Programs\\Msys2\\home\\j1304\\Downloads\\usblist_output.txt"; // output file
    char **list = NULL;
    char line[256];
    int count = 0, capacity = 10;
    char cwd[1024];

    // Get current working directory and print it
    if (_getcwd(cwd, sizeof(cwd)) != NULL) {
        printf("Current working directory: %s\n", cwd);
    } else {
        perror("_getcwd() error");
        return 1;
    }

    // Debugging: print the file path
    printf("Attempting to open file: %s\n", filename);

    list = (char **)malloc(capacity * sizeof(char *));
    if (list == NULL) {
        printf("Memory allocation failed\n");
        return 1;
    }

    inputFile = fopen(filename, "r");
    if (inputFile == NULL) {
        printf("Error opening file: %s\n", filename);
        free(list);
        return 1;
    }

    while (fgets(line, sizeof(line), inputFile)) {
        if (count >= capacity) {
            capacity *= 2;
            list = (char **)realloc(list, capacity * sizeof(char *));
            if (list == NULL) {
                printf("Memory reallocation failed\n");
                fclose(inputFile);
                return 1;
            }
        }
        list[count] = strdup(line);
        list[count][strcspn(list[count], "\n")] = '\0'; // Remove newline

        // Convert to Proper Case
        toProperCase(list[count]);

        count++;
    }
    fclose(inputFile);

    sort(list, count);

    outputFile = fopen(outputname, "w");
    if (outputFile == NULL) {
        printf("Error opening output file.\n");
        for (int i = 0; i < count; i++) {
            free(list[i]);
        }
        free(list);
        return 1;
    }

    for (int i = 0; i < count; i++) {
        fprintf(outputFile, "%d. %s\n", i + 1, list[i]);
        free(list[i]); // Free each line's memory
    }
    fclose(outputFile);
    free(list); // Free the list's memory

    printf("File sorted and saved as %s\n", outputname);
    return 0;
}

