// Apply the requested 85% opacity only to Simplicity's HTA window.
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <wchar.h>

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR command, int show) {
    (void)instance; (void)previous; (void)command; (void)show;
    for (int attempt = 0; attempt < 100; ++attempt) {
        HWND window = FindWindowW(NULL, L"SimplicityBRS");
        if (window) {
            wchar_t class_name[128] = {0};
            GetClassNameW(window, class_name, 128);
            if (wcscmp(class_name, L"HTML Application Host Window Class") == 0) {
                SetLastError(0);
                LONG_PTR style = GetWindowLongPtrW(window, GWL_EXSTYLE);
                if (!SetWindowLongPtrW(window, GWL_EXSTYLE, style | WS_EX_LAYERED) && GetLastError()) return 2;
                return SetLayeredWindowAttributes(window, 0, 217, LWA_ALPHA) ? 0 : 3;
            }
        }
        Sleep(100);
    }
    return 1;
}
