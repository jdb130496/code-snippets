#include <windows.h>
extern "C" int add_asm(int a, int b);
int main() {
    int result = add_asm(30, 12);
    char buf[32];
    wsprintfA(buf, "Result: %d", result);
    MessageBoxA(0, buf, "Test", 0);
    return 0;
}
