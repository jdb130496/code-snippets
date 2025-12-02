.code

; RDRAND 64-bit function
public rdrand64_asm
rdrand64_asm proc
retry_rdrand:
    rdrand rax
    jnc retry_rdrand
    ret
rdrand64_asm endp

; RDSEED 64-bit function
public rdseed64_asm
rdseed64_asm proc
retry_rdseed:
    rdseed rax
    jnc retry_rdseed
    ret
rdseed64_asm endp

end
