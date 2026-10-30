class HwRngRandom:
    """
    RNG backed by Intel RDSEED via the hwrng C extension.

    Optimized: pulls a 4 KB block of RDSEED output per refill and hands out
    only as many bytes as each call needs (1 byte for a 62-char alphabet)
    instead of calling into C and discarding 7 of 8 bytes every time.
    """

    _BUF = 4096                      # multiple of 8, well under the 1 MB limit

    def __init__(self):
        self._buf = b''
        self._pos = 0

    def _take(self, k: int) -> int:
        """Return k fresh hardware-random bytes as a little-endian int."""
        if k > self._BUF:            # huge request: bypass the buffer
            return int.from_bytes(hwrng.rdseed_raw_bytes((k + 7) & ~7)[:k],
                                  'little')
        if self._pos + k > len(self._buf):
            self._buf = hwrng.rdseed_raw_bytes(self._BUF)
            self._pos = 0
        out = self._buf[self._pos:self._pos + k]
        self._pos += k
        return int.from_bytes(out, 'little')

    def randbelow(self, n: int) -> int:
        """Rejection sampling on only the bytes needed: no modulo bias."""
        if n <= 0:
            raise ValueError("n must be positive")
        if n == 1:
            return 0
        bits = (n - 1).bit_length()
        k    = (bits + 7) >> 3
        mask = (1 << bits) - 1
        while True:
            val = self._take(k) & mask
            if val < n:
                return val

    def choice(self, seq):
        n = len(seq)
        if n == 0:
            raise IndexError("Cannot choose from an empty sequence")
        return seq[self.randbelow(n)]

    def randint(self, a: int, b: int) -> int:
        if a > b:
            raise ValueError("a must be <= b")
        return a + self.randbelow(b - a + 1)

    def randrange(self, start: int, stop: int) -> int:
        if stop <= start:
            raise ValueError("stop must be greater than start")
        return start + self.randbelow(stop - start)

    def sample(self, population, k: int) -> list:
        """Partial Fisher-Yates: no replacement, no bias."""
        pool = list(population)
        n = len(pool)
        if k < 0 or k > n:
            raise ValueError("sample larger than population or negative")
        result = []
        for i in range(k):
            j = self.randbelow(n - i)
            result.append(pool[j])
            pool[j] = pool[n - i - 1]
        return result

    def shuffle(self, lst: list) -> None:
        """In-place Fisher-Yates shuffle."""
        for i in range(len(lst) - 1, 0, -1):
            j = self.randbelow(i + 1)
            lst[i], lst[j] = lst[j], lst[i]

    def token_hex(self, nbytes: int = 32) -> str:
        """Raw hex of nbytes from RDSEED (nbytes must be a multiple of 8)."""
        return hwrng.rdseed_raw_bytes(nbytes).hex()
