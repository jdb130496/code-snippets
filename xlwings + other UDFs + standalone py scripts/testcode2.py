import time
import numpy as np
import pandas as pd
import dask.dataframe as dd

def benchmark_simple(size=1_000_000):
    """
    Simple benchmark comparing different methods
    """
    # Generate test data
    print(f"\nTesting with {size:,} elements")
    data = np.random.randint(1, 1000, size=size)
    results = {}
    
    # List comprehension
    start = time.perf_counter()
    _ = [x for x in data if x > 500]
    results['list_comp'] = time.perf_counter() - start
    print(f"List comprehension: {results['list_comp']:.4f} seconds")
    
    # For loop
    start = time.perf_counter()
    result = []
    for x in data:
        if x > 500:
            result.append(x)
    results['for_loop'] = time.perf_counter() - start
    print(f"For loop: {results['for_loop']:.4f} seconds")
    
    # NumPy
    start = time.perf_counter()
    _ = data[data > 500]
    results['numpy'] = time.perf_counter() - start
    print(f"NumPy: {results['numpy']:.4f} seconds")
    
    # Pandas
    pd_data = pd.Series(data)
    start = time.perf_counter()
    _ = pd_data[pd_data > 500]
    results['pandas'] = time.perf_counter() - start
    print(f"Pandas: {results['pandas']:.4f} seconds")
    
    # Dask
    dask_data = dd.from_pandas(pd.Series(data), npartitions=4)
    start = time.perf_counter()
    _ = dask_data[dask_data > 500].compute()
    results['dask'] = time.perf_counter() - start
    print(f"Dask: {results['dask']:.4f} seconds")
    
    return results

# Test with different sizes
sizes = [100_000, 1_000_000, 10_000_000]
all_results = {}

for size in sizes:
    all_results[size] = benchmark_simple(size)

# Print comparison summary
print("\nComparison Summary:")
print("=" * 50)
for size in sizes:
    print(f"\nSize: {size:,}")
    pandas_time = all_results[size]['pandas']
    for method, time_taken in all_results[size].items():
        speedup = pandas_time / time_taken
        print(f"{method:12} : {time_taken:.4f} seconds ({speedup:.2f}x vs Pandas)")

