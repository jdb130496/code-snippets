import hwrng, struct

N = 1000
low, high = 100_000_000_000_000, 999_999_999_999_999

data = hwrng.rdseed_raw_bytes(N * 8)
words = struct.unpack(f'<{N}Q', data)
results = [(w % (high - low + 1)) + low for w in words]

print('\n'.join(f"[{i:4}] {v} ({len(str(v))} digits)" for i, v in enumerate(results, start=1)))

