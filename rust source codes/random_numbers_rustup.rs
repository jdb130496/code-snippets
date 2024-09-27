use std::arch::x86_64::_rdrand64_step;
use std::fs::File;
use std::io::Write;
use std::ptr;

const NUM_NUMBERS: i64 = 45000000;

struct Node {
    value: i64,
    left: *mut Node,
    right: *mut Node,
}

impl Node {
    fn new(value: i64) -> *mut Node {
        let node = Box::into_raw(Box::new(Node {
            value,
            left: ptr::null_mut(),
            right: ptr::null_mut(),
        }));
        node
    }
}

fn insert(node: &mut *mut Node, value: i64) {
    unsafe {
        if (*node).is_null() {
            *node = Node::new(value);
            return;
        }
        if value < (**node).value {
            insert(&mut (**node).left, value);
        } else {
            insert(&mut (**node).right, value);
        }
    }
}

fn contains(node: *mut Node, value: i64) -> bool {
    unsafe {
        if node.is_null() {
            return false;
        }
        if value == (*node).value {
            return true;
        }
        if value < (*node).value {
            return contains((*node).left, value);
        } else {
            return contains((*node).right, value);
        }
    }
}

fn main() -> std::io::Result<()> {
    let mut file = File::create("random_numbers.csv")?;
    let mut root = ptr::null_mut();
    for _ in 0..NUM_NUMBERS {
        let mut rand_u64 = 0;
        let mut rand_i64;
        loop {
            unsafe { _rdrand64_step(&mut rand_u64) };
            rand_i64 = i64::from_be_bytes(rand_u64.to_be_bytes());
            rand_i64 = rand_i64.abs();
            if !contains(root, rand_i64) {
                break;
            }
        }
        insert(&mut root, rand_i64);
        writeln!(file, "{}", rand_i64)?;
    }

    Ok(())
}

