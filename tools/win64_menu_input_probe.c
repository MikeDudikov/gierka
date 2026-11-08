/* Freestanding Win64 diagnostic using actual user32 APIs, no game patches. */
typedef unsigned int DWORD;
typedef unsigned int UINT;
typedef unsigned short WORD;
typedef unsigned long long ULONG_PTR;
typedef void *HANDLE;
typedef void *HWND;
typedef struct { int x, y; } POINT;
typedef struct { int left, top, right, bottom; } RECT;
typedef struct {
    DWORD type, padding;
    struct { int dx, dy; DWORD data, flags, time, padding; ULONG_PTR extra; } mouse;
} INPUT;
_Static_assert(sizeof(INPUT) == 40, "Win64 INPUT ABI must be 40 bytes");
_Static_assert(sizeof(POINT) == 8, "Win32 POINT ABI must be 8 bytes");
#define API __attribute__((ms_abi))
extern API HANDLE GetStdHandle(DWORD);
extern API int WriteFile(HANDLE, const void *, DWORD, DWORD *, void *);
extern API char *GetCommandLineA(void);
extern API DWORD GetLastError(void);
extern API void Sleep(DWORD);
extern API void ExitProcess(UINT);
extern API int GetCursorPos(POINT *);
extern API int SetCursorPos(int, int);
extern API short GetAsyncKeyState(int);
extern API HWND GetForegroundWindow(void);
extern API HWND FindWindowA(const char *, const char *);
extern API int SetForegroundWindow(HWND);
extern API int GetWindowTextA(HWND, char *, int);
extern API DWORD GetWindowThreadProcessId(HWND, DWORD *);
extern API int GetWindowRect(HWND, RECT *);
extern API int GetSystemMetrics(int);
extern API UINT SendInput(UINT, INPUT *, int);

static char line[2048];
static unsigned length;
static void text(const char *s) { while (*s && length + 1 < sizeof line) line[length++] = *s++; }
static void number(long long value) {
    char reversed[24]; unsigned n = 0; unsigned long long magnitude;
    if (value < 0) { text("-"); magnitude = (unsigned long long)(-(value + 1)) + 1; }
    else magnitude = (unsigned long long)value;
    do { reversed[n++] = (char)('0' + magnitude % 10); magnitude /= 10; } while (magnitude);
    while (n) { char s[2] = { reversed[--n], 0 }; text(s); }
}
static void emit(void) {
    DWORD written; text("\n"); WriteFile(GetStdHandle((DWORD)-11), line, length, &written, 0); length = 0;
}
static int equal(const char *a, const char *b) {
    while (*a && *a == *b) { a++; b++; } return *a == *b;
}
static char *argument(char *s) {
    if (*s == '"') { s++; while (*s && *s != '"') s++; if (*s) s++; }
    else while (*s && *s != ' ') s++;
    while (*s == ' ') s++;
    return s;
}
static int integer(char *s) {
    int sign = 1, value = 0; if (*s == '-') { sign = -1; s++; }
    while (*s >= '0' && *s <= '9') value = value * 10 + *s++ - '0';
    return sign * value;
}
static void status(const char *operation) {
    POINT position = {0, 0}; DWORD pid = 0; char title[256] = {0}; RECT rect = {0, 0, 0, 0};
    HWND foreground = GetForegroundWindow();
    GetCursorPos(&position); GetWindowThreadProcessId(foreground, &pid);
    GetWindowTextA(foreground, title, sizeof title); GetWindowRect(foreground, &rect);
    text("operation="); text(operation); text(" cursor="); number(position.x); text(","); number(position.y);
    text(" left="); number((GetAsyncKeyState(1) & 0x8000) != 0);
    text(" foreground_pid="); number(pid); text(" rect="); number(rect.left); text(","); number(rect.top);
    text(","); number(rect.right); text(","); number(rect.bottom); text(" title="); text(title); emit();
}
static void inject(DWORD flags, int x, int y) {
    INPUT input = {0}; input.type = 0; input.mouse.flags = flags;
    if (flags & 0x8000) {
        int width = GetSystemMetrics(0), height = GetSystemMetrics(1);
        input.mouse.dx = x * 65535 / (width - 1); input.mouse.dy = y * 65535 / (height - 1);
    }
    UINT sent = SendInput(1, &input, sizeof input);
    text("SendInput sent="); number(sent); text(" error="); number(sent ? 0 : GetLastError()); emit();
}
void mainCRTStartup(void) {
    char *command = argument(GetCommandLineA());
    char operation[32] = {0}; unsigned n = 0;
    while (command[n] && command[n] != ' ' && n + 1 < sizeof operation) { operation[n] = command[n]; n++; }
    char *xarg = argument(command), *yarg = argument(xarg);
    int x = integer(xarg), y = integer(yarg);
    status("before");
    if (equal(operation, "move")) { SetCursorPos(x, y); Sleep(200); }
    else if (equal(operation, "sendmove")) { inject(0x8001, x, y); Sleep(200); }
    else if (equal(operation, "down")) { inject(0x0002, 0, 0); Sleep(200); }
    else if (equal(operation, "up")) { inject(0x0004, 0, 0); Sleep(200); }
    else if (equal(operation, "click")) {
        inject(0x8001, x, y); Sleep(200); inject(0x0002, 0, 0); Sleep(200); inject(0x0004, 0, 0); Sleep(200);
    }
    else if (equal(operation, "focus")) {
        HWND window = FindWindowA(0, "AncientConquest");
        text("SetForegroundWindow result="); number(SetForegroundWindow(window)); emit(); Sleep(200);
    }
    else if (!equal(operation, "status")) {
        text("Usage: probe.exe status|focus|move x y|sendmove x y|down|up|click x y"); emit(); ExitProcess(2);
    }
    status("after"); ExitProcess(0);
}
