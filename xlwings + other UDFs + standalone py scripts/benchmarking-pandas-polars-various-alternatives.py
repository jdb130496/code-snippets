import pandas as pd
import polars as pl
import numpy as np
import time
from pathlib import Path

print("=" * 75)
print("GENERATING TEST DATA (10 MILLION ROWS)")
print("=" * 75)

n_rows = 10_000_000
np.random.seed(42)

df_source = pd.DataFrame({
    'id': np.arange(n_rows, dtype=np.int32),
    'date': pd.date_range('2020-01-01', periods=n_rows, freq='1min'),
    'value1': np.random.randn(n_rows).astype(np.float32),
    'value2': np.random.randint(0, 1000, n_rows, dtype=np.int16),
    'category': np.random.choice(['A', 'B', 'C', 'D'], n_rows),
})

print(f"Generated: {len(df_source):,} rows, {df_source.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

print("\nSaving to disk formats...")
print("  Saving CSV...")
df_source.to_csv('test_data.csv', index=False)
print("  Saving Parquet...")
df_source.to_parquet('test_data.parquet')
print("Files saved!")

del df_source
import gc
gc.collect()

print("\n" + "=" * 75)
print("BENCHMARKING: CSV → POLARS")
print("=" * 75)

t0 = time.time()
df_pl1 = pl.read_csv('test_data.csv', try_parse_dates=True)
t1 = time.time() - t0
print(f"Time: {t1:.4f}s | Rows: {len(df_pl1):,}")
del df_pl1
gc.collect()

print("\n" + "=" * 75)
print("BENCHMARKING: PARQUET → POLARS (FIRST READ)")
print("=" * 75)

t0 = time.time()
df_pl2 = pl.read_parquet('test_data.parquet')
t2 = time.time() - t0
print(f"Time: {t2:.4f}s | Rows: {len(df_pl2):,}")
del df_pl2
gc.collect()

print("\n" + "=" * 75)
print("BENCHMARKING: PARQUET → POLARS (SECOND READ - CACHED)")
print("=" * 75)

t0 = time.time()
df_pl3 = pl.read_parquet('test_data.parquet')
t3 = time.time() - t0
print(f"Time: {t3:.4f}s | Rows: {len(df_pl3):,}")

print("\n" + "=" * 75)
print("BENCHMARKING: CSV → PANDAS → POLARS")
print("=" * 75)

t0 = time.time()
df_pd = pd.read_csv('test_data.csv', parse_dates=['date'])
df_pl4 = pl.from_pandas(df_pd)
t4 = time.time() - t0
print(f"Time: {t4:.4f}s | Rows: {len(df_pl4):,}")

print("\n" + "=" * 75)
print("RANKINGS (fastest to slowest):")
print("=" * 75)

results = [
    ("Parquet→Polars (cached)", t3),
    ("Parquet→Polars (first)", t2),
    ("CSV→Polars", t1),
    ("CSV→Pandas→Polars", t4),
]
results.sort(key=lambda x: x[1])

for i, (method, time_taken) in enumerate(results, 1):
    if i == 1:
        print(f"{i}. {method:30s}: {time_taken:.4f}s (baseline)")
    else:
        speedup = time_taken / results[0][1]
        print(f"{i}. {method:30s}: {time_taken:.4f}s ({speedup:.1f}x slower)")

print("=" * 75)

# Cleanup
Path('test_data.csv').unlink()
Path('test_data.parquet').unlink()
print("\nCleanup complete - test files deleted.")