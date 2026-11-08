/* Native Win64 WM_INPUT receiver for compatibility-layer diagnostics only. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

static char line[1024];
static unsigned length;
static unsigned rawCount, mouseCount, bufferedCount;
static BOOL bufferMode;
static void text(const char *s) { while (*s && length + 1 < sizeof line) line[length++] = *s++; }
static void number(long long value) {
    char b[24]; unsigned n = 0; unsigned long long u;
    if (value < 0) { text("-"); u = (unsigned long long)(-(value + 1)) + 1; }
    else u = (unsigned long long)value;
    do { b[n++] = '0' + u % 10; u /= 10; } while (u);
    while (n) { char s[2] = {b[--n], 0}; text(s); }
}
static void emit(void) { DWORD n; text("\n"); WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), line, length, &n, 0); length = 0; }
static void describe(const char *transport, RAWINPUT *data) {
    text(transport); text(" size="); number(data->header.dwSize); text(" alignmentMod8="); number((ULONG_PTR)data & 7);
    text(" type="); number(data->header.dwType); text(" hDevice="); number((ULONG_PTR)data->header.hDevice);
    text(" flags="); number(data->data.mouse.usFlags); text(" buttonFlags="); number(data->data.mouse.usButtonFlags);
    text(" dx="); number(data->data.mouse.lLastX); text(" dy="); number(data->data.mouse.lLastY); emit();
}
static void drainBuffer(void) {
    static union { ULONG_PTR alignment; BYTE bytes[4096]; } storage;
    UINT bytes = sizeof storage.bytes;
    UINT count = GetRawInputBuffer((RAWINPUT *)storage.bytes, &bytes, sizeof(RAWINPUTHEADER));
    if (count == (UINT)-1) {
        text("GetRawInputBuffer error="); number(GetLastError()); text(" bytes="); number(bytes); emit();
        ExitProcess(3);
    }
    if (count) {
        text("GetRawInputBuffer count="); number(count); text(" bytes="); number(bytes); emit();
        RAWINPUT *data = (RAWINPUT *)storage.bytes;
        for (UINT i = 0; i < count; i++) {
            describe("BUFFER", data); bufferedCount++;
            /* x64 RAWINPUT blocks are rounded to the next 8-byte boundary. */
            data = (RAWINPUT *)(((ULONG_PTR)data + data->header.dwSize + 7) & ~(ULONG_PTR)7);
        }
    }
}
static LRESULT CALLBACK receive(HWND window, UINT message, WPARAM wparam, LPARAM lparam) {
    if (message == WM_INPUT) {
        RAWINPUT data = {0}; UINT bytes = sizeof data;
        UINT read = GetRawInputData((HRAWINPUT)lparam, RID_INPUT, &data, &bytes, sizeof(RAWINPUTHEADER));
        rawCount++; text("GetRawInputData bytes="); number(read); emit();
        describe(bufferMode ? "DATA-FALLBACK" : "DATA", &data);
    }
    if (message == WM_MOUSEMOVE || message == WM_LBUTTONDOWN || message == WM_LBUTTONUP) {
        mouseCount++; text("MOUSE message="); number(message); text(" wparam="); number(wparam); emit();
    }
    return DefWindowProcA(window, message, wparam, lparam);
}
static void inject(DWORD flags, LONG x, LONG y) {
    INPUT input = {0}; input.type = INPUT_MOUSE; input.mi.dwFlags = flags;
    if (flags & MOUSEEVENTF_ABSOLUTE) {
        input.mi.dx = x * 65535 / (GetSystemMetrics(SM_CXSCREEN) - 1);
        input.mi.dy = y * 65535 / (GetSystemMetrics(SM_CYSCREEN) - 1);
    }
    text("SendInput count="); number(SendInput(1, &input, sizeof input)); emit();
}
void mainCRTStartup(void) {
    const char *argument = GetCommandLineA();
    if (*argument == '"') { argument++; while (*argument && *argument != '"') argument++; if (*argument) argument++; }
    else while (*argument && *argument != ' ') argument++;
    while (*argument == ' ') argument++;
    bufferMode = argument[0] == 'b' && argument[1] == 'u' && argument[2] == 'f' &&
                 argument[3] == 'f' && argument[4] == 'e' && argument[5] == 'r';
    text("bufferMode="); number(bufferMode); text(" headerSize="); number(sizeof(RAWINPUTHEADER)); emit();
    WNDCLASSA cls = {0}; cls.lpfnWndProc = receive;
    cls.hInstance = GetModuleHandleA(0); cls.lpszClassName = "RawInputProbeClass";
    if (!RegisterClassA(&cls)) ExitProcess(2);
    HWND window = CreateWindowExA(0, cls.lpszClassName, "RawInputProbe", WS_OVERLAPPEDWINDOW,
        100, 100, 500, 400, 0, 0, cls.hInstance, 0);
    ShowWindow(window, SW_SHOW); SetForegroundWindow(window);
    RAWINPUTDEVICE device = {1, 2, 0, window};
    text("RegisterRawInputDevices result="); number(RegisterRawInputDevices(&device, 1, sizeof device)); emit();
    inject(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 200, 200);
    inject(MOUSEEVENTF_LEFTDOWN, 0, 0);
    inject(MOUSEEVENTF_LEFTUP, 0, 0);
    DWORD started = GetTickCount(); MSG message;
    while ((DWORD)(GetTickCount() - started) < 2500) {
        if (bufferMode) drainBuffer();
        while (PeekMessageA(&message, 0, 0, 0, PM_REMOVE)) {
            TranslateMessage(&message); DispatchMessageA(&message);
        }
        Sleep(10);
    }
    text("summary rawCount="); number(rawCount); text(" bufferedCount="); number(bufferedCount);
    text(" legacyMouseCount="); number(mouseCount); emit();
    device.dwFlags = RIDEV_REMOVE; device.hwndTarget = 0;
    RegisterRawInputDevices(&device, 1, sizeof device); DestroyWindow(window);
    ExitProcess(0);
}
