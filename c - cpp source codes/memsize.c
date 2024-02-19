#include <windows.h>

BOOL SetWorkingSetSizeExample()
{
    DWORD minSize = 1 * 1024 * 1024; // 1 MB
    DWORD maxSize = 10 * 1024 * 1024; // 10 MB

    HANDLE hProcess = GetCurrentProcess();
    BOOL result = SetProcessWorkingSetSize(hProcess, minSize, maxSize);

    if (!result) {
        // Handle error
        return FALSE;
    }

    return TRUE;
}

int main() {
    SetWorkingSetSizeExample();
    return 0;
}

