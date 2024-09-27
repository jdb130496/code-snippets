use libloading::{Library, Symbol};
use std::io::{self, Write};

fn main() {
    unsafe {
        // 1. Load the DLL
        let lib = Library::new("D:/Downloads/rust_dll/target/release/rust_rand_dll_copilot.dll").unwrap();

        // 2. Get references to the desired functions
        let rdrand64_step: Symbol<unsafe extern "C" fn(&mut u64) -> i32> = lib.get(b"rdrand64_step").unwrap();
        let generate_random_numbers: Symbol<unsafe extern "C" fn(i32, i32) -> ()> =
            lib.get(b"generate_random_numbers").unwrap();
        let allocate_memory: Symbol<unsafe extern "C" fn(i32) -> ()> = lib.get(b"allocate_memory").unwrap();
        let get_numbers: Symbol<unsafe extern "C" fn() -> *mut u64> = lib.get(b"get_numbers").unwrap();
        let free_memory: Symbol<unsafe extern "C" fn() -> ()> = lib.get(b"free_memory").unwrap();

        // 3. Get user input for testing
        let num_threads = read_input("Enter the number of threads: ");
        let num_numbers = read_input("Enter the number of random numbers: ");

        // 4. Allocate memory for the numbers
        allocate_memory(num_numbers);

        // 5. Generate random numbers
        generate_random_numbers(num_threads, num_numbers);

        // 6. Retrieve the generated numbers
        let numbers = unsafe { std::slice::from_raw_parts(get_numbers(), num_numbers as usize) };

        // 7. Print the generated numbers
        println!("Generated random numbers: {:?}", numbers);

        // 8. Free the allocated memory
        free_memory();
    }
}

fn read_input(prompt: &str) -> i32 {
    loop {
        print!("{}", prompt);
        io::stdout().flush().unwrap(); // Make sure the prompt is immediately displayed

        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();

        match input.trim().parse() {
            Ok(num) => return num,
            Err(_) => println!("Please enter a valid number!"),
        }
    }
}

