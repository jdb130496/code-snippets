import hwrng
import struct

N    = 1000
low  = 100_000_000_000_000
high = 999_999_999_999_999
span = high - low + 1          # range size = 900_000_000_000_000

# ── Bias-free rejection sampling ─────────────────────────────────────────────
# Simple modulo (w % span) biases toward lower values when 2^64 % span != 0.
# Rejection sampling fixes this: discard any word >= largest multiple of span
# that fits in uint64, retry with fresh entropy for those positions.

threshold = (2**64 // span) * span   # largest multiple of span <= 2^64

results = []
while len(results) < N:
    # Request a batch — most words will pass, very few retried
    needed = N - len(results)
    data   = hwrng.rdseed_raw_bytes(needed * 8)
    words  = struct.unpack(f'<{needed}Q', data)
    results.extend(
        (w % span) + low
        for w in words
        if w < threshold          # reject biased words
    )

results = results[:N]             # trim any overshoot from last batch

print('\n'.join(
    f"[{i:4}] {v} ({len(str(v))} digits)"
    for i, v in enumerate(results, start=1)
))
