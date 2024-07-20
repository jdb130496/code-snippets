#include <boost/filesystem.hpp>
#include <iostream>

int main() {
    boost::filesystem::path p(".");
    boost::filesystem::directory_iterator end_itr;

    for (boost::filesystem::directory_iterator itr(p); itr != end_itr; ++itr) {
        if (boost::filesystem::is_regular_file(itr->path())) {
            std::cout << itr->path().string() << '\n';
        }
    }

    return 0;
}

