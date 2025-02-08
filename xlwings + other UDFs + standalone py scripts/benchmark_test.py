import pandas as pd
import numpy as np
import re
import time

def benchmark_string_ops(df, pattern, replacement):
    # Original method
    start = time.time()
    df1 = df.stack().str.replace(pattern, replacement, regex=True).unstack()
    t1 = time.time() - start
    
    # Optimized vectorized method
    start = time.time()
    df2 = df.replace(pattern, replacement, regex=True)
    t2 = time.time() - start
    
    return t1, t2

def generate_test_data(rows=100000, cols=50):
    # Create random strings with patterns to replace
    patterns = [
        "ABC-123",
        "XYZ-789",
        "Test-Case",
        "Sample-Text",
        "Data-Point"
    ]
    
    # Generate random data with NaN values
    data = np.random.choice(patterns + [np.nan], size=(rows, cols), p=[0.15, 0.15, 0.15, 0.15, 0.15, 0.25])
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=[f'col_{i}' for i in range(cols)])
    return df

def run_benchmark():
    # Generate test data
    df = generate_test_data()
    
    # Define pattern and replacement
    pattern = r'-'
    replacement = ' '
    
    # Run benchmark
    t1, t2 = benchmark_string_ops(df, pattern, replacement)
    
    # Print results
    print(f"DataFrame shape: {df.shape}")
    print(f"Original method time: {t1:.2f} seconds")
    print(f"Optimized vectorized method time: {t2:.2f} seconds")
    print(f"Speed improvement: {(t1/t2):.2f}x")

if __name__ == "__main__":
    run_benchmark()
