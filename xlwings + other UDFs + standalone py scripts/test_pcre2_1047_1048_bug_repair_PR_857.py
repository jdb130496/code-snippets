import cffi, os

MSYS2_BIN = r"D:\Programs\msys64\ucrt64\bin"
os.add_dll_directory(MSYS2_BIN)

ffi = cffi.FFI()
ffi.cdef("""
    typedef size_t PCRE2_SIZE;
    typedef uint8_t PCRE2_UCHAR8;
    typedef struct pcre2_real_code_8 pcre2_code_8;
    typedef struct pcre2_real_match_data_8 pcre2_match_data_8;
    typedef struct pcre2_real_match_context_8 pcre2_match_context_8;
    typedef struct pcre2_real_general_context_8 pcre2_general_context_8;

    pcre2_code_8 *pcre2_compile_8(
        const uint8_t *pattern, PCRE2_SIZE length, uint32_t options,
        int *errorcode, PCRE2_SIZE *erroroffset, void *ccontext);
    pcre2_match_data_8 *pcre2_match_data_create_from_pattern_8(
        const pcre2_code_8 *code, void *gcontext);
    int pcre2_substitute_8(
        const pcre2_code_8 *code,
        const uint8_t *subject, PCRE2_SIZE length,
        PCRE2_SIZE startoffset, uint32_t options,
        pcre2_match_data_8 *match_data,
        pcre2_match_context_8 *mcontext,
        const uint8_t *replacement, PCRE2_SIZE rlength,
        uint8_t *outputbuffer, PCRE2_SIZE *outlengthptr);
    int pcre2_get_error_message_8(
        int errorcode, uint8_t *buffer, PCRE2_SIZE bufflen);
    void pcre2_match_data_free_8(pcre2_match_data_8 *match_data);
    void pcre2_code_free_8(pcre2_code_8 *code);
""")

PCRE2_UNSET              = int(ffi.cast("PCRE2_SIZE", -1))
PCRE2_SUBSTITUTE_GLOBAL   = 0x00000100
PCRE2_SUBSTITUTE_EXTENDED = 0x00000200

def test_substitute(dll_path, label):
    lib = ffi.dlopen(dll_path)

    pattern     = rb'foo(?<Bar>BAR)?'
    replacement = rb'X${Bar:+\:\:text}Y'
    subjects    = [b'foo', b'fooBAR']

    err_code   = ffi.new("int *")
    err_offset = ffi.new("PCRE2_SIZE *")
    re = lib.pcre2_compile_8(pattern, PCRE2_UNSET, 0, err_code, err_offset, ffi.NULL)
    assert re != ffi.NULL, f"compile failed"

    match_data = lib.pcre2_match_data_create_from_pattern_8(re, ffi.NULL)

    print(f"\n{label}")
    print(f"  pattern:     {pattern!r}")
    print(f"  replacement: {replacement!r}")
    for subject in subjects:
        outlen  = ffi.new("PCRE2_SIZE *", 1024)
        outbuf  = ffi.new("uint8_t[1024]")
        rc = lib.pcre2_substitute_8(
            re, subject, PCRE2_UNSET, 0,
            PCRE2_SUBSTITUTE_GLOBAL | PCRE2_SUBSTITUTE_EXTENDED,
            match_data, ffi.NULL,
            replacement, PCRE2_UNSET,
            outbuf, outlen)
        if rc >= 0:
            result = ffi.string(outbuf, outlen[0]).decode()
            print(f"  {subject!r} → {result!r}")
        else:
            buf = ffi.new("uint8_t[256]")
            lib.pcre2_get_error_message_8(rc, buf, 256)
            print(f"  {subject!r} → ERROR: {ffi.string(buf).decode()}")

    lib.pcre2_match_data_free_8(match_data)
    lib.pcre2_code_free_8(re)

test_substitute(r"D:\Downloads\pcre2\build-gcc-1047\libpcre2-8.dll", "10.47 (buggy)")
test_substitute(r"D:\Programs\pcre2-gcc\bin\libpcre2-8.dll",         "10.48-DEV (fixed)")
