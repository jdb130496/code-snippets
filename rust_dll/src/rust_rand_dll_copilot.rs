#![feature(core_intrinsics)] // Enable core intrinsics for _rdrand64_step

use std::alloc::{alloc, dealloc, Layout};
use core::arch::x86_64::_rdrand64_step;

extern crate rand; // Import the rand crate
use rand::Rng;

#[no_mangle]
pub extern "C" fn rdrand64_step(rand: &mut u64) -> i32 {
    unsafe {
        if _rdrand64_step(rand) == 1 {
            // Check if the number has exactly 15 digits
            if *rand >= 100_000_000_000_000 && *rand <= 999_999_999_999_999 {
                return 1; // Success
            }
        }
        // Fallback to software RNG if hardware RNG fails or does not produce a 15-digit number
        *rand = rand::thread_rng().gen_range(100_000_000_000_000..=999_999_999_999_999);
        return 0; // Indicate fallback
    }
}

#[no_mangle]
pub extern "C" fn generate_random_numbers(num_threads: i32, num_numbers: i32) {
    unsafe {
        let mut rand: u64 = 0;
        for thread_num in 0..num_threads {
            for i in 0..num_numbers / num_threads {
                rdrand64_step(&mut rand);
                *NUMBERS.offset((thread_num * num_numbers / num_threads + i) as isize) = rand;
            }
        }
    }
}

static mut NUMBERS: *mut u64 = std::ptr::null_mut();

#[no_mangle]
pub extern "C" fn get_numbers() -> *mut u64 {
    unsafe { NUMBERS }
}

#[no_mangle]
pub extern "C" fn allocate_memory(num_numbers: i32) {
    unsafe {
        let layout = Layout::from_size_align(num_numbers as usize * std::mem::size_of::<u64>(), std::mem::align_of::<u64>()).unwrap();
        NUMBERS = alloc(layout) as *mut u64;
    }
}

#[no_mangle]
pub extern "C" fn free_memory() {
    unsafe {
        let layout = Layout::from_size_align(std::mem::size_of_val(&*NUMBERS), std::mem::align_of_val(&*NUMBERS)).unwrap();
        dealloc(NUMBERS as *mut u8, layout);
    }
}

