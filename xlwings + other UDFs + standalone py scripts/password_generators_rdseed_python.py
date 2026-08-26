import string
import struct
import time
import hwrng
import xlwings as xw


# ── HARDWARE RNG CLASS ────────────────────────────────────────────────────────

class HwRngRandom:
    def _raw_u64(self) -> int:
        return struct.unpack('<Q', hwrng.rdseed_raw_bytes(8))[0]

    def randbelow(self, n: int) -> int:
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


# ── CORE GENERATORS ───────────────────────────────────────────────────────────

def _generate_password_more_rules(num_passwords, length=12):
    """Bulk run: ≥1 upper, ≥1 lower, ≥1 digit, ≥1 special, ≤2 specials,
    must start with uppercase, no start with special, 12 chars."""
    try:
        num_passwords = int(num_passwords)
    except (ValueError, TypeError):
        return []
    if num_passwords <= 0:
        return []

    special_chars = '?@$#^&*'
    char_set = string.ascii_letters + string.digits + special_chars

    def one_password():
        r = HwRngRandom()
        first = r.choice(string.ascii_uppercase)
        password = [
            r.choice(string.ascii_lowercase),
            r.choice(string.digits),
            r.choice(special_chars)
        ]
        while len(password) < length - 1:      # ← length respected here
            char = r.choice(char_set)
            if char in special_chars and sum(c in special_chars for c in password) >= 2:
                continue
            password.append(char)
        for i in range(len(password)):
            j = r.randint(0, len(password) - 1)
            password[i], password[j] = password[j], password[i]
        return ''.join([first] + password)     # ← first + 11 chars = 12 total

    return [one_password() for _ in range(num_passwords)]

def _generate_passwords_less_rules(num_passwords, length=12):
    """Bulk: ≥1 upper, ≥1 lower, exactly 1 digit,
    exactly 2 unique specials, no start with special, 12 chars."""
    try:
        num_passwords = int(num_passwords)
    except (ValueError, TypeError):
        return []
    if num_passwords <= 0:
        return []

    special_chars = '?@$#^&*'
    letters_and_digits = string.ascii_uppercase + string.ascii_lowercase + string.digits

    def one_password():
        r = HwRngRandom()
        while True:
            upper    = r.choice(string.ascii_uppercase)
            lower    = r.choice(string.ascii_lowercase)
            digit    = r.choice(string.digits)
            specials = r.sample(special_chars, 2)
            others   = r.sample(letters_and_digits, length - 5)  # ← 12-5=7, dynamic
            password = [upper, lower, digit] + specials + others
            for i in range(len(password) - 1, 0, -1):
                j = r.randrange(0, i + 1)
                password[i], password[j] = password[j], password[i]
            if password[0] not in special_chars:
                return ''.join(password)

    return [one_password() for _ in range(num_passwords)]

# ── NAMED BATCH WRAPPERS (for chunked writer) ─────────────────────────────────

# ── NAMED BATCH WRAPPERS ──────────────────────────────────────────────────────

# ── NAMED BATCH WRAPPERS ──────────────────────────────────────────────────────

def _batch_more_rules(n):
    return _generate_password_more_rules(n)

def _batch_less_rules(n):
    return _generate_passwords_less_rules(n)

# ── UDF WRAPPERS ──────────────────────────────────────────────────────────────


@xw.func
def PASSRDSEED_MORE_RULES(num_passwords):
    return [[p] for p in _generate_password_more_rules(num_passwords)]

@xw.func
def PASSRDSEED_LESS_RULES(num_passwords):
    return [[p] for p in _generate_passwords_less_rules(num_passwords)]

# ── CHUNKED BATCH WRITER ──────────────────────────────────────────────────────
def _chunked_write(generator_func, num_passwords, sheet_name, start_col,
                   chunk_size=1000):
    """Writes passwords to open Excel workbook in chunks to avoid memory buildup."""
    wb = xw.books.active
    sheet = wb.sheets[sheet_name]
    start_time = time.time()
    for i in range(0, num_passwords, chunk_size):
        batch_size = min(chunk_size, num_passwords - i)
        passwords = generator_func(batch_size)
        sheet[f'{start_col}{i + 1}'].value = [[p] for p in passwords]
        del passwords
        done = i + batch_size
        elapsed = time.time() - start_time
        rate = done / elapsed
        eta = (num_passwords - done) / rate
        print(f"[{generator_func.__name__}] "
              f"{done}/{num_passwords} | "
              f"{rate:.0f} pw/s | "
              f"ETA: {eta/60:.1f} mins")
    print(f"Done! {num_passwords} passwords written to {sheet_name} col {start_col}")


# ── MAIN (run from Spyder) ────────────────────────────────────────────────────
if __name__ == '__main__':
    SHEET = 'Sheet1'
    NUM   = 10000
    CHUNK = 500

    # More rules → col A: ≥1 upper, ≥1 lower, ≥1 digit, ≤2 specials, starts uppercase
    _chunked_write(_batch_more_rules, NUM, SHEET, 'A', CHUNK)

    # Less rules → col B: ≥1 upper, ≥1 lower, ≥1 digit, exactly 2 specials
    _chunked_write(_batch_less_rules, NUM, SHEET, 'B', CHUNK)
