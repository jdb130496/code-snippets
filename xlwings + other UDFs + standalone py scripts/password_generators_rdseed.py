import string
import struct
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

def _generate_password_single(length=12):
    """Single password: ≥1 upper, ≥1 lower, ≥1 special, ≤2 specials,
    no start with special. No guaranteed digit."""
    r = HwRngRandom()
    char_set = string.ascii_letters + string.digits + '?@$#^&*'
    special_chars = '?@$#^&*'
    password = [
        r.choice(string.ascii_uppercase),
        r.choice(string.ascii_lowercase),
        r.choice(special_chars)
    ]
    while len(password) < length:
        char = r.choice(char_set)
        if char in special_chars and sum(c in special_chars for c in password) >= 2:
            continue
        password.append(char)
    for i in range(len(password)):
        j = r.randint(0, len(password) - 1)
        password[i], password[j] = password[j], password[i]
    while password[0] in special_chars:
        for i in range(len(password)):
            j = r.randint(0, len(password) - 1)
            password[i], password[j] = password[j], password[i]  # ← fixed indent
    return ''.join(password)


def _generate_passwords_bulk(num_passwords):
    """Bulk: ≥1 upper, ≥1 lower, exactly 1 digit,
    exactly 2 unique specials, no start with special."""
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
            others   = r.sample(letters_and_digits, 7)
            password = [upper, lower, digit] + specials + others
            for i in range(len(password) - 1, 0, -1):
                j = r.randrange(0, i + 1)
                password[i], password[j] = password[j], password[i]
            if password[0] not in special_chars:
                return ''.join(password)

    return [one_password() for _ in range(num_passwords)]


# ── NAMED BATCH WRAPPERS ──────────────────────────────────────────────────────

def _generate_passwords_single_bulk(num_passwords):
    try:
        num_passwords = int(num_passwords)
    except (ValueError, TypeError):
        return []
    if num_passwords <= 0:
        return []
    return [_generate_password_single() for _ in range(num_passwords)]


# ── UDF WRAPPERS ──────────────────────────────────────────────────────────────

@xw.func
def PASSRDSEED(dummy=None):
    """Single password — =PASSRDSEED() in one cell."""
    return _generate_password_single()

@xw.func
def PASSRDSEED_MULTI(num_passwords):
    """Bulk single-logic — used by VBA GenerateSingle."""
    return [[p] for p in _generate_passwords_single_bulk(num_passwords)]

@xw.func
def RDSEED_MULTIPW(num_passwords):
    """Bulk with guaranteed digit — used by VBA GenerateBulk."""
    return [[p] for p in _generate_passwords_bulk(num_passwords)]
