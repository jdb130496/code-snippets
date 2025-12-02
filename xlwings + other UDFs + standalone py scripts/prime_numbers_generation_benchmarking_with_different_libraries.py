import numpy as np
import time

def primes_numpy_optimized(n):
    if n < 2:
        return np.array([])
    n_odds = (n - 1) // 2
    sieve = np.ones(n_odds, dtype=bool)
    sqrt_n = int(np.sqrt(n))
    for i in range((sqrt_n - 1) // 2):
        if sieve[i]:
            p = 2 * i + 3
            sieve[(p * p - 3) // 2::p] = False
    return np.concatenate([[2], 2 * np.flatnonzero(sieve) + 3])

try:
    from numba import jit
    
    @jit(nopython=True)
    def primes_numba(n):
        if n < 2:
            return np.empty(0, dtype=np.int64)
        n_odds = (n - 1) // 2
        sieve = np.ones(n_odds, dtype=np.bool_)
        sqrt_n = int(np.sqrt(n))
        for i in range((sqrt_n - 1) // 2):
            if sieve[i]:
                p = 2 * i + 3
                start = (p * p - 3) // 2
                for j in range(start, n_odds, p):
                    sieve[j] = False
        primes = np.empty(np.sum(sieve) + 1, dtype=np.int64)
        primes[0] = 2
        idx = 1
        for i in range(n_odds):
            if sieve[i]:
                primes[idx] = 2 * i + 3
                idx += 1
        return primes
    
    has_numba = True
except ImportError:
    has_numba = False

try:
    from sympy import sieve as sympy_sieve
    def primes_sympy(n):
        sympy_sieve.extend_to_no(n)
        return np.array(list(sympy_sieve.primerange(2, n + 1)))
    has_sympy = True
except ImportError:
    has_sympy = False

try:
    import primesieve
    def primes_primesieve(n):
        return np.array(primesieve.primes(n))
    has_primesieve = True
except ImportError:
    has_primesieve = False

def primes_list_comp(n):
    return np.array([x for x in range(2, n+1) 
                     if all(x % i != 0 for i in range(2, int(x**0.5) + 1))])

def run_comparison(n):
    print("=" * 75)
    print(f"PRIME GENERATION COMPARISON (n = {n:,})")
    print("=" * 75)
    
    results = []
    
    print(f"\n[1] NumPy Optimized Sieve:")
    t_start = time.time()
    p1 = primes_numpy_optimized(n)
    t1 = time.time() - t_start
    print(f"    Time: {t1:.4f}s | Primes found: {len(p1):,}")
    results.append(("NumPy", t1, len(p1)))
    
    if has_numba:
        primes_numba(100)
        print(f"\n[2] Numba JIT:")
        t_start = time.time()
        p2 = primes_numba(n)
        t2 = time.time() - t_start
        print(f"    Time: {t2:.4f}s | Primes found: {len(p2):,}")
        results.append(("Numba", t2, len(p2)))
    
    if has_sympy:
        print(f"\n[3] SymPy:")
        t_start = time.time()
        p3 = primes_sympy(n)
        t3 = time.time() - t_start
        print(f"    Time: {t3:.4f}s | Primes found: {len(p3):,}")
        results.append(("SymPy", t3, len(p3)))
    
    if has_primesieve:
        print(f"\n[4] Primesieve:")
        t_start = time.time()
        p4 = primes_primesieve(n)
        t4 = time.time() - t_start
        print(f"    Time: {t4:.4f}s | Primes found: {len(p4):,}")
        results.append(("Primesieve", t4, len(p4)))
    
    if n <= 10000:
        print(f"\n[5] List Comprehension:")
        t_start = time.time()
        p5 = primes_list_comp(n)
        t5 = time.time() - t_start
        print(f"    Time: {t5:.4f}s | Primes found: {len(p5):,}")
        results.append(("List Comp", t5, len(p5)))
    
    print("\n" + "=" * 75)
    print("RANKINGS (fastest to slowest):")
    print("=" * 75)
    results.sort(key=lambda x: x[1])
    baseline_time = results[0][1]
    
    for i, (method, time_taken, count) in enumerate(results, 1):
        if i == 1:
            print(f"{i}. {method:15s}: {time_taken:.4f}s (baseline)")
        else:
            speedup = time_taken / baseline_time
            print(f"{i}. {method:15s}: {time_taken:.4f}s ({speedup:.1f}x slower)")
    print("=" * 75)

run_comparison(10000)
run_comparison(100000)
run_comparison(1000000)
run_comparison(10000000)