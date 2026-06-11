import cffi, os, subprocess

MSYS2_BIN = r"D:\Programs\msys64\ucrt64\bin"
os.add_dll_directory(MSYS2_BIN)

ffi = cffi.FFI()
ffi.cdef("""
    typedef size_t  PCRE2_SIZE;
    typedef uint8_t PCRE2_UCHAR8;

    typedef struct pcre2_real_code_8          pcre2_code_8;
    typedef struct pcre2_real_match_data_8    pcre2_match_data_8;
    typedef struct pcre2_real_match_context_8 pcre2_match_context_8;
    typedef struct pcre2_real_compile_context_8 pcre2_compile_context_8;

    pcre2_code_8 *pcre2_compile_8(
        const uint8_t *pattern, PCRE2_SIZE length, uint32_t options,
        int *errorcode, PCRE2_SIZE *erroroffset,
        pcre2_compile_context_8 *ccontext);

    pcre2_match_data_8 *pcre2_match_data_create_8(
        uint32_t ovecsize, void *gcontext);

    pcre2_match_data_8 *pcre2_match_data_create_from_pattern_8(
        const pcre2_code_8 *code, void *gcontext);

    int pcre2_match_8(
        const pcre2_code_8 *code,
        const uint8_t *subject, PCRE2_SIZE length,
        PCRE2_SIZE startoffset, uint32_t options,
        pcre2_match_data_8 *match_data,
        pcre2_match_context_8 *mcontext);

    int pcre2_next_match_8(
        pcre2_match_data_8 *match_data,
        PCRE2_SIZE *pstart_offset,
        uint32_t *poptions);

    int pcre2_get_error_message_8(
        int errorcode, uint8_t *buffer, PCRE2_SIZE bufflen);

    PCRE2_SIZE *pcre2_get_ovector_pointer_8(pcre2_match_data_8 *match_data);

    void pcre2_match_data_free_8(pcre2_match_data_8 *match_data);
    void pcre2_code_free_8(pcre2_code_8 *code);
""")

lib = ffi.dlopen(r"D:\Programs\pcre2-gcc\bin\libpcre2-8.dll")

PCRE2_UNSET = int(ffi.cast("PCRE2_SIZE", -1))
PCRE2_UTF   = 0x00080000


# ── Helper: compile a pattern ─────────────────────────────────────────────────
def compile_pattern(pattern: bytes, options: int = 0):
    err_code   = ffi.new("int *")
    err_offset = ffi.new("PCRE2_SIZE *")
    re = lib.pcre2_compile_8(pattern, PCRE2_UNSET, options,
                             err_code, err_offset, ffi.NULL)
    if re == ffi.NULL:
        buf = ffi.new("uint8_t[256]")
        lib.pcre2_get_error_message_8(err_code[0], buf, 256)
        msg = ffi.string(buf).decode()
        raise ValueError(f"Compile error {err_code[0]} at offset {err_offset[0]}: {msg}")
    return re


# ── Helper: extract ovector groups ───────────────────────────────────────────
def get_groups(match_data, subject_bytes, rc):
    ov = lib.pcre2_get_ovector_pointer_8(match_data)
    results = []
    for i in range(rc):
        s, e = ov[i * 2], ov[i * 2 + 1]
        if s == PCRE2_UNSET:
            results.append(None)
        else:
            results.append((s, e, subject_bytes[s:e].decode()))
    return results


print("PCRE2 version: 10.48-DEV")


# ══════════════════════════════════════════════════════════════════════════════
# DEMO 1 — pcre2_next_match()  (new in 10.47)
# pcre2_next_match is a navigation helper: after each pcre2_match call it
# computes the start_offset and options for the next call, handling empty
# matches and \K edge cases automatically.  Returns 1 to continue, 0 to stop.
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("DEMO 1: pcre2_next_match() — iterate all matches safely")
print("=" * 60)

pattern = rb'\b\w+'
subject = b"the quick brown fox jumps"

re         = compile_pattern(pattern)
match_data = lib.pcre2_match_data_create_8(10, ffi.NULL)

start_offset = ffi.new("PCRE2_SIZE *", 0)
options      = ffi.new("uint32_t *", 0)

print(f"Subject: {subject!r}")
print(f"Pattern: {pattern!r}")
print("Matches:")

rc = lib.pcre2_match_8(re, subject, len(subject), start_offset[0], options[0], match_data, ffi.NULL)
while rc > 0:
    ov = lib.pcre2_get_ovector_pointer_8(match_data)
    s, e = ov[0], ov[1]
    print(f"  [{s}:{e}] {subject[s:e].decode()!r}")
    if not lib.pcre2_next_match_8(match_data, start_offset, options):
        break
    rc = lib.pcre2_match_8(re, subject, len(subject), start_offset[0], options[0], match_data, ffi.NULL)

if rc < -1:
    print(f"  Error rc={rc}")

lib.pcre2_match_data_free_8(match_data)
lib.pcre2_code_free_8(re)


# ══════════════════════════════════════════════════════════════════════════════
# DEMO 2 — Subroutine call returning captures to caller  (new in 10.47)
# (?1(2)) calls group 1 as a subroutine and returns group 2 back to the caller.
# ══════════════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("DEMO 2: Subroutine calls that return captures to caller (10.47)")
print("=" * 60)

pattern = rb'((\w+)) (?1(2))'
subject = b"hello world"

re         = compile_pattern(pattern)
match_data = lib.pcre2_match_data_create_from_pattern_8(re, ffi.NULL)

rc = lib.pcre2_match_8(re, subject, len(subject), 0, 0, match_data, ffi.NULL)
if rc > 0:
    groups = get_groups(match_data, subject, rc)
    print(f"Subject: {subject!r}   Pattern: {pattern!r}")
    print(f"  Group 0 (whole match): {groups[0][2]!r}")
    if rc > 1:
        print(f"  Group 1 (first word):  {groups[1][2]!r}")
    if rc > 2:
        print(f"  Group 2 (caller-returned subroutine capture): {groups[2][2]!r}")
    else:
        print(f"  Group 2 not returned (rc={rc}) — requires 10.47+ subroutine-return support")
else:
    print(f"No match (rc={rc})")

lib.pcre2_match_data_free_8(match_data)
lib.pcre2_code_free_8(re)


# ══════════════════════════════════════════════════════════════════════════════
# DEMO 3 — Scan Substring assertion  (*scs:(group)...)  (new in 10.45)
# Captures a group then asserts its entire content matches a subpattern.
# ══════════════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("DEMO 3: Scan Substring (*scs:) — group content assertion (10.45)")
print("=" * 60)

pattern  = rb'(\w++)(*scs:(1)^\d+$)'
subjects = [b"price42", b"abc123", b"99bottles", b"hello", b"12345"]

try:
    re         = compile_pattern(pattern)
    match_data = lib.pcre2_match_data_create_from_pattern_8(re, ffi.NULL)
    print(f"Pattern: {pattern!r}  (word matches only if entirely digits)")
    for subject in subjects:
        rc = lib.pcre2_match_8(re, subject, len(subject), 0, 0, match_data, ffi.NULL)
        if rc > 0:
            ov = lib.pcre2_get_ovector_pointer_8(match_data)
            matched = subject[ov[0]:ov[1]].decode()
            print(f"  {subject!r:14} → MATCH: {matched!r}")
        else:
            print(f"  {subject!r:14} → no match")
    lib.pcre2_match_data_free_8(match_data)
    lib.pcre2_code_free_8(re)
except ValueError as exc:
    print(f"  Compile failed: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# DEMO 4 — UTS#18 extended character classes with && intersection  (10.45)
# ══════════════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("DEMO 4: UTS#18 Extended character classes with && intersection (10.45)")
print("=" * 60)

# Probe for the correct flag value by trying to compile a pattern that needs it
PCRE2_ALT_EXTENDED_CLASS = None
re_test2 = compile_pattern(rb'\p{L}+', PCRE2_UTF)
match_data_test = lib.pcre2_match_data_create_from_pattern_8(re_test2, ffi.NULL)
subj = b"Hello"
rc_test = lib.pcre2_match_8(re_test2, subj, len(subj), 0, 0, match_data_test, ffi.NULL)
print(f"sanity \\p{{L}} on b'Hello': rc={rc_test}")
lib.pcre2_match_data_free_8(match_data_test)
lib.pcre2_code_free_8(re_test2)
for flag_val in [0x08000000, 0x02000000, 0x04000000, 0x01000000]:
#for flag_val in [0x02000000, 0x04000000, 0x01000000]:
    try:
        re_test = compile_pattern(rb'[\p{L}&&\p{Ll}]+', PCRE2_UTF | flag_val)
        PCRE2_ALT_EXTENDED_CLASS = flag_val
        lib.pcre2_code_free_8(re_test)
        print(f"PCRE2_ALT_EXTENDED_CLASS = 0x{flag_val:08x}")
        break
    except ValueError:
        continue

if PCRE2_ALT_EXTENDED_CLASS is None:
    print("Could not find working flag value for PCRE2_ALT_EXTENDED_CLASS")
else:
    pattern  = rb'[\p{L}&&\p{Ll}]+'
    subjects = [b"Hello World 123", b"ALLCAPS", b"mixedCase"]

    try:
        re         = compile_pattern(pattern, PCRE2_UTF | PCRE2_ALT_EXTENDED_CLASS)
        match_data = lib.pcre2_match_data_create_from_pattern_8(re, ffi.NULL)
        print(f"Pattern: {pattern!r}  (letters \u2229 lowercase = \\p{{Ll}})")
        for subject in subjects:
            start_offset = ffi.new("PCRE2_SIZE *", 0)
            options      = ffi.new("uint32_t *", 0)
            found        = []
            rc = lib.pcre2_match_8(re, subject, len(subject), start_offset[0], options[0], match_data, ffi.NULL)
            while rc > 0:
                ov = lib.pcre2_get_ovector_pointer_8(match_data)
                found.append(subject[ov[0]:ov[1]].decode())
                if not lib.pcre2_next_match_8(match_data, start_offset, options):
                    break
                rc = lib.pcre2_match_8(re, subject, len(subject), start_offset[0], options[0], match_data, ffi.NULL)
            print(f"  {subject!r:22} → {found}")
        lib.pcre2_match_data_free_8(match_data)
        lib.pcre2_code_free_8(re)
    except ValueError as exc:
        print(f"  Compile failed: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# DEMO 5 — Turkish I casefolding  (10.45)
# In Turkish, uppercase İ (U+0130) lowercases to i, and I lowercases to ı.
# ══════════════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("DEMO 5: Turkish I casefolding — (*TURKISH_CASING) verb (10.45)")
print("=" * 60)
turkish_verb = None
for verb in [b'(*TURKISH_CASING)', b'(*turkish_casing)', b'(*Turkish_Casing)']:
    try:
        re_test = compile_pattern(verb + b'(?i)istanbul', PCRE2_UTF)
        lib.pcre2_code_free_8(re_test)
        turkish_verb = verb   # store just the verb, without (?i)
        print(f"Working verb: {verb!r}")
        break
    except ValueError as exc:
        print(f"  {verb!r} failed: {exc}")

if turkish_verb is None:
    print("No working Turkish casing verb found")
else:
    subject = "İstanbul".encode("utf-8")   # Turkish capital İ (U+0130)
    for label, pat in [
        ("Turkish casing",  turkish_verb + b'(?i)istanbul'),
        ("Standard casing", b'(?i)istanbul'),
    ]:
        try:
            re         = compile_pattern(pat, PCRE2_UTF)
            match_data = lib.pcre2_match_data_create_from_pattern_8(re, ffi.NULL)
            rc = lib.pcre2_match_8(re, subject, len(subject), 0, 0, match_data, ffi.NULL)
            result = "MATCH" if rc > 0 else "no match"
            print(f"  {label:20} pattern={pat!r:45} subject={subject!r} → {result}")
            lib.pcre2_match_data_free_8(match_data)
            lib.pcre2_code_free_8(re)
        except ValueError as exc:
            print(f"  {label}: compile error — {exc}")
