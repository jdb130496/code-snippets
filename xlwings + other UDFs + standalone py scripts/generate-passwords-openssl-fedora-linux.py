import string
import struct
import subprocess
import time
import os
import openpyxl
from openpyxl.utils import get_column_letter


# ── OPENSSL PATH ──────────────────────────────────────────────────────────────

OPENSSL_BIN = '/opt/openssl/bin/openssl'
OPENSSL_LIB = '/opt/openssl/lib64'
OPENSSL_ENV = {**os.environ, 'LD_LIBRARY_PATH': OPENSSL_LIB}

# Output workbook path
OUTPUT_XLSX = '/tmp/passwords-output.xlsx'


# ── OPENSSL-BACKED RNG CLASS ──────────────────────────────────────────────────

class OpensslRandom:
    """
    Drop-in RNG backed by /opt/openssl/bin/openssl rand.
    Entropy chain: Linux kernel entropy pool (RDSEED/RDRAND/hardware events)
    → OpenSSL DRBG → raw bytes → this class → password characters.

    Bytes are pre-fetched in a buffer to avoid per-character subprocess
    overhead — same principle as the original HwRngRandom batching.

    Buffer size: 8192 bytes (~1000 u64 values) per refill call.
    """

    _BUFFER_SIZE = 8192     # bytes fetched per subprocess call

    def __init__(self):
        self._buf = b''
        self._pos = 0

    def _refill(self):
        result = subprocess.run(
            [OPENSSL_BIN, 'rand', str(self._BUFFER_SIZE)],
            capture_output=True, check=True, env=OPENSSL_ENV
        )
        self._buf = result.stdout
        self._pos = 0

    def _raw_bytes(self, n: int) -> bytes:
        """Return exactly n raw bytes, refilling buffer as needed."""
        out = bytearray()
        while len(out) < n:
            if self._pos >= len(self._buf):
                self._refill()
            chunk     = self._buf[self._pos:self._pos + n - len(out)]
            out      += chunk
            self._pos += len(chunk)
        return bytes(out)

    def _raw_u64(self) -> int:
        return struct.unpack('<Q', self._raw_bytes(8))[0]

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
        n    = len(pool)
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
            j          = self.randbelow(i + 1)
            lst[i], lst[j] = lst[j], lst[i]

    def token_hex(self, nbytes: int = 32) -> str:
        """Raw hex string of nbytes from OpenSSL rand."""
        return self._raw_bytes(nbytes).hex()


# ── CONSTANTS ─────────────────────────────────────────────────────────────────

_SPECIAL_CHARS      = '?@$#^&*'
_LETTERS_AND_DIGITS = string.ascii_uppercase + string.ascii_lowercase + string.digits
_FULL_CHARSET       = string.ascii_letters + string.digits + _SPECIAL_CHARS


# ── CORE GENERATORS ───────────────────────────────────────────────────────────

def _generate_password_more_rules(num_passwords, length=12):
    """
    Bulk: ≥1 upper, ≥1 lower, ≥1 digit, ≥1 special, ≤2 specials,
    must start with uppercase. length=12 default.
    OpensslRandom instantiated once per batch — not once per password.
    """
    try:
        num_passwords = int(num_passwords)
    except (ValueError, TypeError):
        return []
    if num_passwords <= 0:
        return []

    r = OpensslRandom()                         # ← once per batch

    def one_password():
        first    = r.choice(string.ascii_uppercase)
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
    OpensslRandom instantiated once per batch — not once per password.
    """
    try:
        num_passwords = int(num_passwords)
    except (ValueError, TypeError):
        return []
    if num_passwords <= 0:
        return []

    r = OpensslRandom()                         # ← once per batch

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
    """Cryptographically secure numeric PINs via OpenSSL rand."""
    try:
        num_pins = int(num_pins)
    except (ValueError, TypeError):
        return []
    if num_pins <= 0:
        return []

    r = OpensslRandom()
    return [''.join(str(r.randbelow(10)) for _ in range(length))
            for _ in range(num_pins)]


def _generate_hex_keys(num_keys, bits=256):
    """Raw hex key material from OpenSSL rand — for encryption keys, API tokens."""
    try:
        num_keys = int(num_keys)
    except (ValueError, TypeError):
        return []
    if num_keys <= 0:
        return []

    r = OpensslRandom()
    return [r.token_hex(bits // 8) for _ in range(num_keys)]


def _generate_openssl_passwords(num_passwords, nbytes=32):
    """
    Passwords via /opt/openssl rand — entropy chain:
    Linux kernel pool (hardware-seeded) → OpenSSL DRBG → hex output.
    Bulk-safe: one subprocess call produces all bytes at once, then slices.
    """
    try:
        num_passwords = int(num_passwords)
    except (ValueError, TypeError):
        return []
    if num_passwords <= 0:
        return []

    total_bytes = num_passwords * nbytes
    out = subprocess.run(
        [OPENSSL_BIN, 'rand', '-hex', str(total_bytes)],
        capture_output=True, text=True, check=True, env=OPENSSL_ENV
    )
    hex_str   = out.stdout.strip()
    chars_per = nbytes * 2
    return [hex_str[i * chars_per:(i + 1) * chars_per]
            for i in range(num_passwords)]


# ── NAMED BATCH WRAPPERS ──────────────────────────────────────────────────────

def _batch_more_rules(n): return _generate_password_more_rules(n)
def _batch_less_rules(n): return _generate_passwords_less_rules(n)
def _batch_pins(n):       return _generate_pins(n)
def _batch_hex_keys(n):   return _generate_hex_keys(n)
def _batch_openssl(n):    return _generate_openssl_passwords(n)


# ── CHUNKED BATCH WRITER (openpyxl) ──────────────────────────────────────────

def _chunked_write(generator_func, num_passwords, sheet, col_idx,
                   chunk_size=1000):
    """
    Writes passwords to openpyxl sheet in chunks to avoid memory buildup.
    col_idx : 1-based column index (1=A, 2=B, …)
    Row 1   : reserved for header — data starts at row 2.
    """
    start_time = time.time()

    for i in range(0, num_passwords, chunk_size):
        batch_size = min(chunk_size, num_passwords - i)
        passwords  = generator_func(batch_size)

        for j, pw in enumerate(passwords):
            sheet.cell(row=i + j + 2, column=col_idx, value=pw)  # +2: row 1 = header
        del passwords

        done    = i + batch_size
        elapsed = time.time() - start_time
        rate    = done / elapsed
        eta     = (num_passwords - done) / rate
        print(f"[{generator_func.__name__}] "
              f"{done}/{num_passwords} | "
              f"{rate:.0f} pw/s | "
              f"ETA: {eta/60:.1f} mins")

    col_letter = get_column_letter(col_idx)
    print(f"Done! {num_passwords} entries written to col {col_letter}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    NUM   = 100000
    CHUNK = 500

    wb    = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = 'Sheet1'

    # ── Column headers (row 1) ────────────────────────────────────────────────
    headers = {
        1: 'More Rules',
        2: 'Less Rules',
        3: 'PIN (6-digit)',
        4: 'Hex Key (256-bit)',
        5: 'OpenSSL Raw Hex',
    }
    for col_idx, label in headers.items():
        sheet.cell(row=1, column=col_idx, value=label)

    # ── Col A — more rules:  ≥1 upper, ≥1 lower, ≥1 digit, ≤2 specials, starts uppercase
    _chunked_write(_batch_more_rules, NUM, sheet, 1, CHUNK)

    # ── Col B — less rules:  ≥1 upper, ≥1 lower, exactly 1 digit, exactly 2 specials
    _chunked_write(_batch_less_rules, NUM, sheet, 2, CHUNK)

    # ── Col C — 6-digit numeric PINs
    _chunked_write(_batch_pins, NUM, sheet, 3, CHUNK)

    # ── Col D — 256-bit hex keys (encryption keys / API tokens)
    _chunked_write(_batch_hex_keys, NUM, sheet, 4, CHUNK)

    # ── Col E — OpenSSL hex passwords (direct rand output / entropy comparison)
    _chunked_write(_batch_openssl, NUM, sheet, 5, CHUNK)

    wb.save(OUTPUT_XLSX)
    print(f"\nSaved → {OUTPUT_XLSX}")
