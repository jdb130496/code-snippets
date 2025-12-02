echo 'int main(){return 0;}' > test.cpp
cl /nologo test.cpp

echo '#include <windows.h>' > test.c; echo 'int main(){MessageBoxA(0,"Hi","",0);return 0;}' >> test.c
cl /nologo test.c user32.lib

@'
.code
main proc
xor eax,eax
ret
main endp
end
'@ > test.asm
ml64 /nologo test.asm /link /entry:main /subsystem:console
Remove-Item test.cpp, test.c, test.asm, test.obj

