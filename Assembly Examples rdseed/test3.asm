section .text
global _start

_start:
    ; Generate a 64-bit random number using rdseed
    rdseed rax
    mov [rand64], rax

    ; Convert the 64-bit random number to a hexadecimal string
    mov rsi, rand64
    call hex_to_str

    ; Print the hexadecimal string
    mov rax, 1
    mov rdi, 1
    mov rsi, hex_buffer
    mov rdx, 17 ; Ensure null terminator is included
    syscall

    ; Print a newline after the hexadecimal number
    mov rax, 1
    mov rdi, 1
    mov rsi, newline
    mov rdx, 1
    syscall

    ; Convert hexadecimal to decimal
    mov rsi, rand64
    call hex_to_dec

    ; Print the decimal value
    mov rax, 1
    mov rdi, 1
    mov rsi, dec_buffer
    mov rdx, 21
    syscall

    ; Print a newline after the decimal number
    mov rax, 1
    mov rdi, 1
    mov rsi, newline
    mov rdx, 1
    syscall

    ; Exit the program
    mov rax, 60
    xor rdi, rdi
    syscall

hex_to_str:
    ; Convert the 64-bit number in rsi to a hexadecimal string in hex_buffer
    mov rax, [rsi]
    mov rdi, hex_buffer + 15
    mov rcx, 16
    mov rbx, 16
    mov byte [rdi + 1], 0 ; Null-terminate the string
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
hex_to_dec:
    ; Convert the 64-bit number in rsi to decimal in dec_buffer
    mov rax, [rsi]            ; Load the 64-bit number into rax
    mov rdi, dec_buffer + 20  ; Point to the end of the buffer
    mov rcx, 20               ; Set the maximum number of digits
    mov rbx, 10               ; Set the divisor to 10 (for decimal conversion)
    mov byte [rdi], 0         ; Null-terminate the string at the end
    dec rdi                   ; Move to the previous position

convert_dec_loop:
    xor rdx, rdx              ; Clear rdx (needed for division)
    div rbx                   ; Divide rax by 10, quotient in rax, remainder in rdx
    add dl, '0'               ; Convert the remainder to its ASCII character
    mov [rdi], dl             ; Store the digit at the current position
    dec rdi                   ; Move to the previous position
    test rax, rax             ; Check if rax is zero
    jnz convert_dec_loop      ; If not zero, repeat the loop

    inc rdi                   ; Adjust rdi to point to the start of the string
    ret


section .bss
rand64: resq 1
hex_buffer: resb 17 ; Increased by 1 for null-termination
dec_buffer: resb 21 ; Increased by 1 for null-termination

section .data
newline: db 0xa

; Compilation in Linux:  "nasm -f elf64 -g -o test3.o test3.asm" followed by "ld -o test3 test3.o"
