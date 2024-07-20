#include <iostream>
#include <vector>

int main() {
    std::vector<int> vec = {1, 2, 3, 4, 5};
    for(int i : vec) {
	  std::cout << i << " ";
    }
//        std::cout << i << "\n";
    std::cout << std::endl;
    return 0;
}


