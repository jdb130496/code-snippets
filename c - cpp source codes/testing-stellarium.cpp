#include <iostream>
#include <iomanip>
#include <sstream>
#include <string>
#include <curl/curl.h>

// Callback function to handle response data
size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

// Function to set time using Stellarium API
bool setTime(double julianDay, int timerate) {
    CURL* curl;
    CURLcode res;
    std::string responseString;
    bool success = false;

    // Initialize libcurl
    curl = curl_easy_init();
    if (curl) {
        // Use stringstream for precise double conversion
        std::ostringstream jsonStream;
        jsonStream << std::fixed << std::setprecision(9)  // Increase precision
                   << "{\"time\": " << julianDay
                   << ", \"timerate\": " << timerate << "}";
        std::string jsonData = jsonStream.str();

        std::cout << "JSON Payload: " << jsonData << std::endl;

        // Set the URL
        curl_easy_setopt(curl, CURLOPT_URL, "http://192.168.1.4:8090/api/main/time");

        // Specify that this is a POST request
        curl_easy_setopt(curl, CURLOPT_POST, 1L);

        // Set the JSON data as the POST data
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, jsonData.c_str());

        // Set the content type to JSON
        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        // Set up response handling
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &responseString);

        // Perform the request
        res = curl_easy_perform(curl);

        // Check for errors
        if (res != CURLE_OK) {
            std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        } else {
            long response_code;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
            std::cout << "Response Code: " << response_code << std::endl;
            std::cout << "Response Body: " << responseString << std::endl;

            if (response_code == 200 && responseString.find("ok") != std::string::npos) {
                success = true;
                std::cout << "Time set successfully." << std::endl;
            } else {
                std::cerr << "Error: HTTP response code " << response_code << std::endl;
                std::cerr << "Failed to set time." << std::endl;
            }
        }

        // Clean up
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }
    return success;
}

int main() {
    double julianDay = 2458387.294818901; // Example Julian Day from status response
    double timerate = 1;

    if (!setTime(julianDay, timerate)) {
        std::cerr << "Failed to set time." << std::endl;
    }

    return 0;
}

//Compilation: g++ testing-stellarium.cpp -lcurl -o testing-stellarium
