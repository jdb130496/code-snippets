extrn printf: PROC

.data
    rand64 QWORD 0
    hex_buffer BYTE 17 DUP(0) ; 16 bytes + null terminator
    dec_buffer BYTE 21 DUP(0) ; 20 bytes + null terminator
    newline BYTE 0Ah, 0

.code
main PROC
    ; Generate a 64-bit random number using rdseed
    rdseed rax
    mov [rand64], rax

    ; Convert the 64-bit random number to a hexadecimal string
    lea rsi, [rand64]
    call hex_to_str

    ; Print the hexadecimal string
    lea rcx, [hex_buffer]
    call printf_internal

    ; Print a newline after the hexadecimal number
    lea rcx, [newline]
    call printf_internal

    ; Convert hexadecimal to decimal
    lea rsi, [rand64]
    call hex_to_dec

    ; Print the decimal value
    lea rcx, [dec_buffer]
    call printf_internal

    ; Print a newline after the decimal number
    lea rcx, [newline]
    call printf_internal

    ; Exit the program
    ret
main ENDP

hex_to_str PROC
    ; Convert the 64-bit number in rsi to a hexadecimal string in hex_buffer
    mov rax, [rsi]
    lea rdi, [hex_buffer + 15]
    mov rcx, 16
    mov rbx, 16
    mov byte ptr [rdi + 1], 0 ; Null-terminate the string
convert_hex_loop:
    xor rdx, rdx
    div rbx
    add dl, '0'
    cmp dl, '9'
    jbe store_hex
    add dl, 7
store_hex:
    mov [rdi], dl
    dec rdi
    loop convert_hex_loop
    ret
hex_to_str ENDP

hex_to_dec PROC
    ; Convert the 64-bit number in rsi to a decimal string in dec_buffer
    mov rax, [rsi]
    lea rdi, [dec_buffer + 20]   ; Point to the end of the buffer (before null terminator)
    mov rcx, 20                  ; Maximum digits for a 64-bit number in decimal
    mov rbx, 10                  ; Base 10 for decimal conversion
    mov byte ptr [rdi], 0        ; Null-terminate the string
    dec rdi

convert_dec_loop:
    xor rdx, rdx                 ; Clear rdx before division
    div rbx                      ; Divide rax by 10, rdx will have remainder
    add dl, '0'                  ; Convert remainder to ASCII
    mov [rdi], dl                ; Store the digit
    dec rdi                      ; Move to the previous byte
    dec rcx                      ; Decrease digit count
    test rax, rax                ; Check if rax is zero
    jnz convert_dec_loop         ; If not, continue loop

    ; Now rdi points to the position just before the first digit.
    ; If rcx > 0, we need to pad with leading zeros.
    mov al, '0'                  ; ASCII for '0'
pad_zeroes:
    cmp rcx, 0                   ; Check if padding is needed
    jz finish_padding            ; If no more padding needed, exit loop
    mov [rdi], al                ; Pad with '0'
    dec rdi                      ; Move to the previous byte
    dec rcx                      ; Decrease digit count
    jmp pad_zeroes               ; Repeat until fully padded

finish_padding:
    lea rdi, [rdi + 1]           ; Adjust rdi to point to the first digit
    ret
hex_to_dec ENDP

printf_internal PROC
    sub rsp, 20h                ; Allocate stack space for alignment
    call printf                 ; Call printf from msvcrt.lib
    add rsp, 20h                ; Clean up stack space
    ret
printf_internal ENDP

END

; Compilation: ml64 /c /Fo test-win-masm-msvcrt.obj test-win-masm-msvcrt.asm
; Linking: link /SUBSYSTEM:CONSOLE /ENTRY:main /OUT:test-win-masm-msvcrt.exe test-win-masm-msvcrt.obj "D:\Programs\masm64\lib64\msvcrt.lib" OR
;link /SUBSYSTEM:CONSOLE /ENTRY:main /OUT:test-win-masm-msvcrt.exe test-win-masm-msvcrt.obj "d:\msvcrt.lib"
