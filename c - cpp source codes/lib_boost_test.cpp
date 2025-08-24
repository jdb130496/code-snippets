#include <boost/thread.hpp>
#include <iostream>
#include <vector>

class Worker {
public:
    Worker(int id, int start, int end) : id(id), start(start), end(end) {}

    void operator()() {
        for (int i = start; i < end; ++i) {
            std::cout << "Worker " << id << " is handling number " << i << " on thread id " << boost::this_thread::get_id() << std::endl;
        }
    }

private:
    int id;
    int start;
    int end;
};

int main() {
    int num_workers = 5; // replace with the number of workers you want
    int num_numbers = 50; // replace with the number of numbers you want

    boost::thread_group threads;

    int numbers_per_worker = num_numbers / num_workers;
    for (int i = 0; i < num_workers; ++i) {
        int start = i * numbers_per_worker;
        int end = (i == num_workers - 1) ? num_numbers : start + numbers_per_worker;
        Worker worker(i, start, end);
        threads.create_thread(worker);
    }

    threads.join_all();

    return 0;
}

