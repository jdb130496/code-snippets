import string
import struct
import subprocess
import time
import hwrng
import xlwings as xw


# ── HARDWARE RNG CLASS ────────────────────────────────────────────────────────

class HwRngRandom:
    """
    Drop-in RNG backed by Intel RDSEED via the custom hwrng C extension.
    Entropy chain: Intel RDSEED (thermal noise) → hwrng.rdseed_raw_bytes()
    → this class → password characters.
    No OS pool, no DRBG stretching — raw hardware entropy every call.
    """

    def _raw_u64(self) -> int:
        return struct.unpack('<Q', hwrng.rdseed_raw_bytes(8))[0]

    def randbelow(self, n: int) -> int:
        """Rejection-sampling — no modulo bias."""
        if n <= 0:
            raise ValueError("n must be positive")
        if n == 1:
            return 0
        mask = (1 << (n - 1).bit_length()) - 1
        while True:
            val = self._raw_u64() & mask
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
        """Partial Fisher-Yates — no replacement, no bias."""
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
        """Raw hex string of nbytes from RDSEED — for keys/tokens."""
        return hwrng.rdseed_raw_bytes(nbytes).hex()


# ── CONSTANTS ─────────────────────────────────────────────────────────────────

_SPECIAL_CHARS      = '?@$#^&*'
_LETTERS_AND_DIGITS = string.ascii_uppercase + string.ascii_lowercase + string.digits
_FULL_CHARSET       = string.ascii_letters + string.digits + _SPECIAL_CHARS


# ── CORE GENERATORS ───────────────────────────────────────────────────────────

def _generate_password_more_rules(num_passwords, length=12):
    """
    Bulk: ≥1 upper, ≥1 lower, ≥1 digit, ≥1 special, ≤2 specials,
    must start with uppercase. length=12 default.
    HwRngRandom instantiated once per batch — not once per password.
    """
    try:
        num_passwords = int(num_passwords)
    except (ValueError, TypeError):
        return []
    if num_passwords <= 0:
        return []

    r = HwRngRandom()                           # ← once per batch

    def one_password():
        first = r.choice(string.ascii_uppercase)
        password = [
            r.choice(string.ascii_lowercase),
            r.choice(string.digits),
            r.choice(_SPECIAL_CHARS),
        ]
        while len(password) < length - 1:
            char = r.choice(_FULL_CHARSET)
            if char in _SPECIAL_CHARS and \
               sum(c in _SPECIAL_CHARS for c in password) >= 2:
                continue
            password.append(char)
        r.shuffle(password)
        return first + ''.join(password)

    return [one_password() for _ in range(num_passwords)]


def _generate_passwords_less_rules(num_passwords, length=12):
    """
    Bulk: ≥1 upper, ≥1 lower, exactly 1 digit, exactly 2 unique specials,
    no start with special. length=12 default.
    HwRngRandom instantiated once per batch — not once per password.
    """
    try:
        num_passwords = int(num_passwords)
    except (ValueError, TypeError):
        return []
    if num_passwords <= 0:
        return []

    r = HwRngRandom()                           # ← once per batch

    def one_password():
        while True:
            upper    = r.choice(string.ascii_uppercase)
            lower    = r.choice(string.ascii_lowercase)
            digit    = r.choice(string.digits)
            specials = r.sample(_SPECIAL_CHARS, 2)
            others   = r.sample(_LETTERS_AND_DIGITS, length - 5)
            password = [upper, lower, digit] + specials + others
            r.shuffle(password)
            if password[0] not in _SPECIAL_CHARS:
                return ''.join(password)

    return [one_password() for _ in range(num_passwords)]


def _generate_pins(num_pins, length=6):
    """Cryptographically secure numeric PINs via RDSEED."""
    try:
        num_pins = int(num_pins)
    except (ValueError, TypeError):
        return []
    if num_pins <= 0:
        return []

    r = HwRngRandom()
    return [''.join(str(r.randbelow(10)) for _ in range(length))
            for _ in range(num_pins)]


def _generate_hex_keys(num_keys, bits=256):
    """Raw hex key material from RDSEED — for encryption keys, API tokens."""
    try:
        num_keys = int(num_keys)
    except (ValueError, TypeError):
        return []
    if num_keys <= 0:
        return []

    r = HwRngRandom()
    return [r.token_hex(bits // 8) for _ in range(num_keys)]


def _generate_openssl_passwords(num_passwords, nbytes=32):
    """
    Passwords via OpenSSL rand — entropy chain:
    BCryptGenRandom (OS pool, hardware-seeded) → OpenSSL DRBG → base64 output.
    Fallback when hwrng is unavailable (VM, non-Intel CPU).

    Bulk-safe: one subprocess call produces all bytes at once, then slices
    into per-password tokens — avoids per-password subprocess overhead that
    would make bulk generation unusably slow.
    """
    try:
        num_passwords = int(num_passwords)
    except (ValueError, TypeError):
        return []
    if num_passwords <= 0:
        return []

    # Request all bytes in one call: num_passwords × nbytes
    total_bytes = num_passwords * nbytes
    out = subprocess.run(
        ["openssl", "rand", "-hex", str(total_bytes)],
        capture_output=True, text=True, check=True
    )
    hex_str = out.stdout.strip()

    # Slice into num_passwords equal hex tokens (each nbytes × 2 hex chars)
    chars_per = nbytes * 2
    return [hex_str[i * chars_per:(i + 1) * chars_per]
            for i in range(num_passwords)]


# ── NAMED BATCH WRAPPERS (for chunked writer) ─────────────────────────────────

def _batch_more_rules(n):
    return _generate_password_more_rules(n)

def _batch_less_rules(n):
    return _generate_passwords_less_rules(n)

def _batch_pins(n):
    return _generate_pins(n)

def _batch_hex_keys(n):
    return _generate_hex_keys(n)

def _batch_openssl(n):
    return _generate_openssl_passwords(n)


# ── UDF WRAPPERS (xlwings — small on-demand use from Excel cells only) ────────
# For bulk generation use __main__ + _chunked_write instead.
# Pushing thousands of passwords through the OLE automation boundary
# causes COM object accumulation that presents as a memory leak.

@xw.func
def PASSRDSEED_MORE_RULES(num_passwords):
    return [[p] for p in _generate_password_more_rules(num_passwords)]

@xw.func
def PASSRDSEED_LESS_RULES(num_passwords):
    return [[p] for p in _generate_passwords_less_rules(num_passwords)]

@xw.func
def PASSRDSEED_PIN(num_pins, length=6):
    return [[p] for p in _generate_pins(num_pins, length)]

@xw.func
def PASSRDSEED_HEX_KEY(num_keys, bits=256):
    return [[p] for p in _generate_hex_keys(num_keys, bits)]

@xw.func
def PASS_OPENSSL(num_passwords, nbytes=32):
    return [[p] for p in _generate_openssl_passwords(num_passwords, nbytes)]


# ── CHUNKED BATCH WRITER ──────────────────────────────────────────────────────

def _chunked_write(generator_func, num_passwords, sheet_name, start_col,
                   chunk_size=1000):
    """
    Writes passwords to open Excel workbook in chunks to avoid memory buildup.
    Each chunk is written and immediately freed before the next is generated.
    """
    wb    = xw.books.active
    sheet = wb.sheets[sheet_name]
    start_time = time.time()

    for i in range(0, num_passwords, chunk_size):
        batch_size = min(chunk_size, num_passwords - i)
        passwords  = generator_func(batch_size)
        sheet[f'{start_col}{i + 1}'].value = [[p] for p in passwords]
        del passwords

        done    = i + batch_size
        elapsed = time.time() - start_time
        rate    = done / elapsed
        eta     = (num_passwords - done) / rate
        print(f"[{generator_func.__name__}] "
              f"{done}/{num_passwords} | "
              f"{rate:.0f} pw/s | "
              f"ETA: {eta/60:.1f} mins")

    print(f"Done! {num_passwords} passwords written to {sheet_name} col {start_col}")


# ── MAIN (run from Spyder) ────────────────────────────────────────────────────

if __name__ == '__main__':
    SHEET = 'Sheet1'
    NUM   = 100000
    CHUNK = 500

    # Col A — more rules:  ≥1 upper, ≥1 lower, ≥1 digit, ≤2 specials, starts uppercase
    _chunked_write(_batch_more_rules, NUM, SHEET, 'A', CHUNK)

    # Col B — less rules:  ≥1 upper, ≥1 lower, exactly 1 digit, exactly 2 specials
    _chunked_write(_batch_less_rules, NUM, SHEET, 'B', CHUNK)

    # Col C — 6-digit PINs via RDSEED
    _chunked_write(_batch_pins, NUM, SHEET, 'C', CHUNK)

    # Col D — 256-bit hex keys via RDSEED (encryption keys / API tokens)
    _chunked_write(_batch_hex_keys, NUM, SHEET, 'D', CHUNK)

    # Col E — OpenSSL hex passwords (OS entropy pool fallback / comparison)
    _chunked_write(_batch_openssl, NUM, SHEET, 'E', CHUNK)
