# To generate integers using new library (custom) hwrng
import struct
import hwrng
N = 1000
print('\n'.join(f"[{i:4}] {w}" for i, w in enumerate(struct.unpack(f'<{N}Q', hwrng.rdseed_raw_bytes(N * 8)), start=1)))
