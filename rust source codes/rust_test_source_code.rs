use libloading::{Library, Symbol};

fn main() {
    unsafe {
        // 1. Load the DLL
        let lib = Library::new("D:/Downloads/target/x86_64-pc-windows-gnu/release/rust_rand_dll_new.dll").unwrap();

        // 2. Get references to the desired functions
        let rdrand64_step: Symbol<unsafe extern "C" fn(&mut u64) -> i32> = lib.get(b"rdrand64_step").unwrap();
        let generate_random_numbers: Symbol<unsafe extern "C" fn(i32, i32) -> ()> =
            lib.get(b"generate_random_numbers").unwrap();
        let allocate_memory: Symbol<unsafe extern "C" fn(i32) -> ()> = lib.get(b"allocate_memory").unwrap();
        let get_numbers: Symbol<unsafe extern "C" fn() -> *mut u64> = lib.get(b"get_numbers").unwrap();
        let free_memory: Symbol<unsafe extern "C" fn() -> ()> = lib.get(b"free_memory").unwrap();

        // 3. Get user input for testing (adjust as needed)
        let num_threads = 4;
        let num_numbers = 100000;

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

