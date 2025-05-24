import xlwings as xw
import rdrand

@xw.func
def RDSEED_EXCEL(min_val, max_val, count):
    """Generate random numbers in range [min_val, max_val] using RDSEED."""
    count = int(count)
    min_val = int(min_val)
    max_val = int(max_val)
    
    s = rdrand.RdSeedom()  # Create instance once
    random_numbers = []
    
    for _ in range(count):
        random_number = s.get_bits(64) % (max_val - min_val + 1) + min_val
        random_numbers.append(random_number)
    
    return [[num] for num in random_numbers]
    
@xw.func
def RDRAND_EXCEL(min_val, max_val, count):
    """Generate random numbers in range [min_val, max_val] using RDRAND."""
    count = int(count)
    min_val = int(min_val)
    max_val = int(max_val)
    
    s = rdrand.RdRandom()  # Create instance once
    random_numbers = []
    
    for _ in range(count):
        random_number = s.get_bits(64) % (max_val - min_val + 1) + min_val
        random_numbers.append(random_number)
    
    return [[num] for num in random_numbers]


@xw.func
def RDSEED_FLOAT(min_val, max_val, count):
    """Generate random floating point numbers using RDSEED."""
    count = int(count)
    min_val = float(min_val)
    max_val = float(max_val)
    
    s = rdrand.RdSeedom()  # Create instance once
    random_numbers = []
    
    for _ in range(count):
        # Get 52 bits for float precision, convert to [0,1) range
        random_float = s.get_bits(52) / (2**52)
        # Scale to desired range
        scaled_float = min_val + (max_val - min_val) * random_float
        random_numbers.append(scaled_float)
    
    return [[num] for num in random_numbers]

@xw.func
def RDRAND_FLOAT(min_val, max_val, count):
    """Generate random floating point numbers using RDRAND."""
    count = int(count)
    min_val = float(min_val)
    max_val = float(max_val)
    
    s = rdrand.RdRandom()  # Create instance once
    random_numbers = []
    
    for _ in range(count):
        # Get 52 bits for float precision, convert to [0,1) range
        random_float = s.get_bits(52) / (2**52)
        # Scale to desired range
        scaled_float = min_val + (max_val - min_val) * random_float
        random_numbers.append(scaled_float)
    
    return [[num] for num in random_numbers]

@xw.func
def RDSEED_DICE(num_dice, num_sides):
    """Simulate dice rolls using RDSEED."""
    num_dice = int(num_dice)
    num_sides = int(num_sides)
    
    s = rdrand.RdSeedom()  # Create instance once
    results = []
    total = 0
    
    for i in range(num_dice):
        roll = s.get_bits(32) % num_sides + 1
        results.append([f"Die {i+1}", roll])
        total += roll
    
    results.append(["Total", total])
    return results

@xw.func
def RDSEED_COIN(count):
    """Simulate coin flips using RDSEED."""
    count = int(count)
    
    s = rdrand.RdSeedom()  # Create instance once
    results = []
    heads_count = 0
    
    for i in range(count):
        flip = s.get_bits(1)  # Just 1 bit needed
        result = "Heads" if flip == 1 else "Tails"
        results.append([f"Flip {i+1}", result])
        if flip == 1:
            heads_count += 1
    
    results.append(["Summary", f"{heads_count} Heads, {count - heads_count} Tails"])
    return results

@xw.func
def RDSEED_BYTES(num_bytes):
    """Generate random bytes using RDSEED."""
    num_bytes = int(num_bytes)
    
    s = rdrand.RdSeedom()  # Create instance once
    random_bytes = s.get_bytes(num_bytes)
    
    # Convert bytes to list of integers for Excel display
    result = []
    for i, byte_val in enumerate(random_bytes):
        result.append([f"Byte {i+1}", byte_val])
    
    return result

@xw.func
def RDRAND_BYTES(num_bytes):
    """Generate random bytes using RDRAND."""
    num_bytes = int(num_bytes)
    
    s = rdrand.RdRandom()  # Create instance once
    random_bytes = s.get_bytes(num_bytes)
    
    # Convert bytes to list of integers for Excel display
    result = []
    for i, byte_val in enumerate(random_bytes):
        result.append([f"Byte {i+1}", byte_val])
    
    return result

@xw.func
def RDSEED_M(rows, cols, min_val, max_val):
    """Generate a matrix of random numbers using RDSEED."""
    rows = int(rows)
    cols = int(cols)
    min_val = int(min_val)
    max_val = int(max_val)
    
    s = rdrand.RdSeedom()  # Create instance once
    result = []
    
    for i in range(rows):
        row = []
        for j in range(cols):
            random_number = s.get_bits(64) % (max_val - min_val + 1) + min_val
            row.append(random_number)
        result.append(row)
    
    return result

@xw.func
def RDRAND_M(rows, cols, min_val, max_val):
    """Generate a matrix of random numbers using RDRAND."""
    rows = int(rows)
    cols = int(cols)
    min_val = int(min_val)
    max_val = int(max_val)
    
    s = rdrand.RdRandom()  # Create instance once
    result = []
    
    for i in range(rows):
        row = []
        for j in range(cols):
            random_number = s.get_bits(64) % (max_val - min_val + 1) + min_val
            row.append(random_number)
        result.append(row)
    
    return result
