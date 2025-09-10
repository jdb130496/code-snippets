use std::arch::asm;

fn main() {
    // Check if RDSEED is supported
    if !is_rdseed_supported() {
        eprintln!("Error: RDSEED instruction not supported on this CPU");
        std::process::exit(1);
    }

    println!("Generating 64 bytes using Intel RDSEED instruction...\n");
    
    let mut random_bytes = [0u8; 64];
    
    // Generate 64 bytes (8 iterations of 8 bytes each)
    for i in 0..8 {
        let random_u64 = rdseed_u64();
        let bytes = random_u64.to_le_bytes();
        
        // Copy 8 bytes into our array
        for j in 0..8 {
            random_bytes[i * 8 + j] = bytes[j];
        }
    }
    
    // Display the results
    println!("Generated 64 random bytes:");
    print_hex_bytes(&random_bytes);
    
    println!("\nAs decimal values:");
    for (i, &byte) in random_bytes.iter().enumerate() {
        if i % 16 == 0 {
            print!("\n{:02}: ", i);
        }
        print!("{:3} ", byte);
    }
    println!();
}

/// Generate a random u64 using RDSEED instruction
fn rdseed_u64() -> u64 {
    let mut result: u64;
    let mut success: u8;
    
    unsafe {
        loop {
            asm!(
                "rdseed {result}",      
                "setc {success}",       
                result = out(reg) result,
                success = out(reg_byte) success,
                options(nomem, nostack)
            );
            
            if success != 0 {
                break;
            }
            
            std::hint::spin_loop();
        }
    }
    
    result
}

/// Check if RDSEED is supported - test the instruction directly
fn is_rdseed_supported() -> bool {
    let mut _test_result: u64;
    let mut success: u8;
    
    unsafe {
        asm!(
            "rdseed {result}",
            "setc {success}",
            result = out(reg) _test_result,
            success = out(reg_byte) success,
            options(nomem, nostack)
        );
    }
    
    // If we get here without crashing and success flag is set, RDSEED works
    success != 0
}

/// Helper function to print bytes in hex format
fn print_hex_bytes(bytes: &[u8]) {
    for (i, &byte) in bytes.iter().enumerate() {
        if i % 16 == 0 {
            print!("\n{:04X}: ", i);
        }
        print!("{:02X} ", byte);
    }
    println!();
}
