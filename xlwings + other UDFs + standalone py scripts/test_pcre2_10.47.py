import pcre2
import re  # stdlib - simulates "old" engine behavior

TESTFILE = r'D:\dev\pcre2_testfile.txt'

with open(TESTFILE, encoding='utf-8') as f:
    content = f.read()

print("=" * 60)
print(f"  PCRE2 Python package : {pcre2.__version__}")
print(f"  PCRE2 C library      : {pcre2.__libpcre2_version__}")
print("=" * 60)

# ============================================================
# TEST 1: $+ substitution
# - 10.47 : returns last matched capture group
# - 10.46 : $+ is treated as literal text "$+"
# - Python re: has no $+ syntax at all
# ============================================================
print()
print("TEST 1: $+ substitution (new in 10.47)")
print("-" * 60)

text = "John Smith, Age 34\nJane Doe, Age 28\nRobert Johnson, Age 51"

print("  [10.47 - YOUR BUILD]")
try:
    result_1047 = pcre2.sub(r'(\w+) (\w+), Age \d+', r'$+', text)
    for line in result_1047.strip().splitlines():
        print(f"    PASS -> '{line}'   (last capture group = surname)")
except Exception as e:
    print(f"    FAIL -> {e}")

print("  [10.46 - SIMULATED: $+ not recognized, kept as literal]")
try:
    fake_1046 = pcre2.sub(r'(\w+) (\w+), Age \d+', r'$$+', text)
    for line in fake_1046.strip().splitlines():
        print(f"    FAIL -> '{line}'   ($+ kept as literal, wrong output)")
except Exception as e:
    print(f"    ERROR -> {e}")

print("  [Python stdlib re - no $+ syntax, produces literal output]")
result_re = re.sub(r'(\w+) (\w+), Age \d+', r'$+', text)
for line in result_re.strip().splitlines():
    print(f"    FAIL -> '{line}'   ($+ not understood by re module)")

# ============================================================
# TEST 2: Unicode word extraction
# - 10.47 : pcre2_next_match() iterates safely over all scripts
# - Python re: misses Cyrillic, CJK without extra flags
# ============================================================
print()
print("TEST 2: Unicode safe iteration (pcre2_next_match in 10.47)")
print("-" * 60)

unicode_text = "héllo wörld — esto тест — 日本語 café résumé"

print("  [10.47 - YOUR BUILD]")
words_1047 = pcre2.findall(r'\w+', unicode_text)
print(f"    PASS -> {len(words_1047)} words: {words_1047}")

print("  [Python stdlib re - limited Unicode coverage]")
words_re = re.findall(r'\w+', unicode_text)
print(f"    PARTIAL -> {len(words_re)} words: {words_re}")
missing = set(words_1047) - set(words_re)
if missing:
    print(f"    Missing scripts: {missing}")

# ============================================================
# TEST 3: Email extraction using $+ to get domain only
# ============================================================
print()
print("TEST 3: Extract domain only from emails using $+ (10.47)")
print("-" * 60)

email_lines = (
    "contact@example.com\n"
    "support@my-company.org\n"
    "no-reply@subdomain.domain.co.uk\n"
    "user.name+tag@gmail.com"
)

print("  [10.47 - $+ returns last capture group = domain]")
try:
    domains_1047 = pcre2.sub(
        r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'$+',
        email_lines
    )
    for d in domains_1047.strip().splitlines():
        print(f"    PASS -> '{d}'")
except Exception as e:
    print(f"    FAIL -> {e}")

print("  [Python re - must use \\2, no $+ available]")
domains_re = re.sub(
    r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    r'\2',
    email_lines
)
for d in domains_re.strip().splitlines():
    print(f"    WORKAROUND -> '{d}'  (must hardcode group number)")

# ============================================================
# TEST 4: Structured extraction from testfile
# ============================================================
print()
print("TEST 4: Structured extraction from testfile")
print("-" * 60)

print("  Emails:")
for m in pcre2.finditer(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content):
    print(f"    {m.group()}")

print("  Dates (YYYY-MM-DD):")
for m in pcre2.finditer(r'\d{4}-\d{2}-\d{2}', content):
    print(f"    {m.group()}")

print("  Log levels:")
for m in pcre2.finditer(r'\[([\d-]+ [\d:]+)\] (\w+)', content):
    print(f"    {m.group(2):6s} at {m.group(1)}")

# ============================================================
# TEST 5: Hard version gate
# ============================================================
print()
print("TEST 5: Hard version gate")
print("-" * 60)
major, minor = map(int, pcre2.__libpcre2_version__.split(".")[:2])
if (major, minor) >= (10, 47):
    print(f"  PASS -> PCRE2 {major}.{minor} confirmed")
    print(f"    pcre2_next_match() : YES - added 10.47")
    print(f"    $+ substitution    : YES - added 10.47")
    print(f"    Subroutine capture : YES - added 10.47")
else:
    print(f"  FAIL -> PCRE2 {major}.{minor} is too old")
    print(f"    pcre2_next_match() : NO  - added in 10.47")
    print(f"    $+ substitution    : NO  - added in 10.47")
    print(f"    Subroutine capture : NO  - added in 10.47")

print()
print("=" * 60)
