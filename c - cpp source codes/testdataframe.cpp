#include <DataFrame/DataFrame.h>
#include <random>
#include <fstream>

int main() {
    // Set the optimum thread level for parallel processing
    hmdf::ThreadGranularity::set_thread_level(4);

    // Create a DataFrame object
    hmdf::StdDataFrame<unsigned long> df;

    // Create vectors to hold data
    std::vector<double> vec1(10000000);
    std::vector<int> vec2(10000000);
    std::vector<std::string> vec3(10000000, "test");

    // Create an index for the DataFrame
    std::vector<unsigned long> index(10000000);
    std::iota(index.begin(), index.end(), 0);  // Fill with consecutive numbers

    // Fill vec1 and vec2 with random numbers
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis1(1.0, 2.0);
    std::uniform_int_distribution<> dis2(1, 10);

    for (auto &x : vec1) {
        x = dis1(gen);
    }

    for (auto &x : vec2) {
        x = dis2(gen);
    }

    // Load index into the DataFrame
    df.load_index(std::move(index));

    // Load data into the DataFrame
    df.load_column("col1", std::move(vec1));
    df.load_column("col2", std::move(vec2));
    df.load_column("col3", std::move(vec3));

    // Save the DataFrame to a CSV file
    std::ofstream outfile("dataframe.csv");
    df.write<std::ostream, int, double, std::string>(outfile);

    return 0;
}
// Compiled using: g++ -std=c++23 -I /opt/cppdataframe/include -L /opt/cppdataframe/lib -l DataFrame testdataframe.cpp -o testdataframe in msys2
