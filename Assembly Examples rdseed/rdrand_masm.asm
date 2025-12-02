.code

; uint64_t rdrand64_masm(void)
rdrand64_masm PROC
    rdrand rax
    jnc rdrand64_masm
    ret
rdrand64_masm ENDP

; uint64_t rdseed64_masm(void)
rdseed64_masm PROC
    rdseed rax
    jnc rdseed64_masm
    ret
rdseed64_masm ENDP

END
