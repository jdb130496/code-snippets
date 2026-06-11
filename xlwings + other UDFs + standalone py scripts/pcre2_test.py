import cffi, os

MSYS2_BIN = r"D:\Programs\msys64\ucrt64\bin"
os.add_dll_directory(MSYS2_BIN)

ffi = cffi.FFI()
ffi.cdef("""
    typedef size_t  PCRE2_SIZE;
    typedef uint8_t PCRE2_UCHAR8;

    typedef struct pcre2_real_code_8          pcre2_code_8;
    typedef struct pcre2_real_match_data_8    pcre2_match_data_8;
    typedef struct pcre2_real_match_context_8 pcre2_match_context_8;

    pcre2_code_8 *pcre2_compile_8(
        const uint8_t *pattern, PCRE2_SIZE length, uint32_t options,
        int *errorcode, PCRE2_SIZE *erroroffset, void *ccontext);

    pcre2_match_data_8 *pcre2_match_data_create_8(
        uint32_t ovecsize, void *gcontext);

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

    PCRE2_SIZE *pcre2_get_ovector_pointer_8(pcre2_match_data_8 *match_data);
    void pcre2_match_data_free_8(pcre2_match_data_8 *match_data);
    void pcre2_code_free_8(pcre2_code_8 *code);
""")

lib = ffi.dlopen(r"D:\Programs\pcre2-gcc\bin\libpcre2-8.dll")

PCRE2_UNSET = int(ffi.cast("PCRE2_SIZE", -1))

pattern = rb'\b\w+'
subject = b"the quick brown fox jumps"

err_code   = ffi.new("int *")
err_offset = ffi.new("PCRE2_SIZE *")
re = lib.pcre2_compile_8(pattern, PCRE2_UNSET, 0, err_code, err_offset, ffi.NULL)
assert re != ffi.NULL, f"compile failed at offset {err_offset[0]}"

match_data = lib.pcre2_match_data_create_8(10, ffi.NULL)

print(f"subject: {subject!r}")
print(f"pattern: {pattern!r}")
print("matches:")

start_offset = ffi.new("PCRE2_SIZE *", 0)
options      = ffi.new("uint32_t *", 0)

rc = lib.pcre2_match_8(re, subject, len(subject), start_offset[0], options[0], match_data, ffi.NULL)
while rc > 0:
    ov = lib.pcre2_get_ovector_pointer_8(match_data)
    s, e = ov[0], ov[1]
    print(f"  [{s}:{e}] {subject[s:e].decode()!r}")
    # pcre2_next_match computes start_offset and options for the next call;
    # returns 1 if another attempt should be made, 0 if iteration is complete
    if not lib.pcre2_next_match_8(match_data, start_offset, options):
        break
    rc = lib.pcre2_match_8(re, subject, len(subject), start_offset[0], options[0], match_data, ffi.NULL)

if rc < -1:
    print(f"error rc={rc}")

lib.pcre2_match_data_free_8(match_data)
lib.pcre2_code_free_8(re)
