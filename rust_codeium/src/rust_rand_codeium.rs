use std::sync::{Arc, Mutex};
use std::thread;
use std::io;
use rdrand::RdRand;

fn generate_random_numbers(num_threads: usize, num_rand_nums: usize) -> Vec<u64> {
    let result = Arc::new(Mutex::new(Vec::new()));
    let handles: Vec<_> = (0..num_threads)
        .map(|_| {
            let result = Arc::clone(&result);
            thread::spawn(move || {
                let mut local_result = Vec::new();
                let rng = RdRand::new().unwrap();
                for _ in 0..num_rand_nums / num_threads {
                    let rand_num: u64 = match rng.try_next_u64() {
                        Ok(num) => num,
                        Err(_) => continue,
                    };
                    // Ensure the random number is 15 digits long and within the specified range
                    let rand_num = 100_000_000_000_000 + (rand_num % 900_000_000_000_000);
                    local_result.push(rand_num);
                }
                result.lock().unwrap().extend(local_result);
            })
        })
        .collect();

    for handle in handles {
        handle.join().unwrap();
    }

    Arc::try_unwrap(result).unwrap().into_inner().unwrap()
}

fn main() {
    println!("Enter the number of threads: ");
    let mut num_threads = String::new();
    io::stdin().read_line(&mut num_threads).expect("Failed to read line");
    let num_threads: usize = num_threads.trim().parse().unwrap();

    println!("Enter the number of random numbers to generate: ");
    let mut num_rand_nums = String::new();
    io::stdin().read_line(&mut num_rand_nums).expect("Failed to read line");
    let num_rand_nums: usize = num_rand_nums.trim().parse().unwrap();

    let random_numbers = generate_random_numbers(num_threads, num_rand_nums);
    println!("{:?}", random_numbers);
}

