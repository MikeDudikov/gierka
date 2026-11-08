/* Owned-window foreground test. No mouse injection, game patch or forged message. */
typedef unsigned int DWORD;
typedef unsigned int UINT;
typedef void *HWND;
typedef void *HANDLE;
#define API __attribute__((ms_abi))
extern API HWND FindWindowA(const char *, const char *);
extern API HWND GetForegroundWindow(void);
extern API int GetWindowTextA(HWND, char *, int);
extern API DWORD GetWindowThreadProcessId(HWND, DWORD *);
extern API DWORD GetCurrentThreadId(void);
extern API int AttachThreadInput(DWORD, DWORD, int);
extern API int PeekMessageA(void *, HWND, UINT, UINT, UINT);
extern API int SetForegroundWindow(HWND);
extern API int BringWindowToTop(HWND);
extern API int ShowWindow(HWND, int);
extern API HANDLE GetStdHandle(DWORD);
extern API int WriteFile(HANDLE, const void *, DWORD, DWORD *, void *);
extern API void Sleep(DWORD);
extern API void ExitProcess(UINT);

static char line[1024];
static unsigned length;
static HWND player, sink;
static void text(const char *s) { while (*s && length + 1 < sizeof line) line[length++] = *s++; }
static void number(unsigned long long value) {
    char digits[24]; unsigned n = 0;
    do { digits[n++] = (char)('0' + value % 10); value /= 10; } while (value);
    while (n) { char s[2] = {digits[--n], 0}; text(s); }
}
static void emit(void) { DWORD written; text("\n"); WriteFile(GetStdHandle((DWORD)-11), line, length, &written, 0); length = 0; }
static void quoted(const char *s) {
    text("\"");
    while (*s) {
        if (*s == '\\' || *s == '"') text("\\");
        char c[2] = {*s++, 0}; text(c);
    }
    text("\"");
}
static int status(const char *phase, HWND expected, int set_result, int top_result) {
    HWND foreground = GetForegroundWindow(); DWORD pid = 0; char title[256] = {0};
    GetWindowThreadProcessId(foreground, &pid); GetWindowTextA(foreground, title, sizeof title);
    quoted(phase); text(":{\"foreground\":"); number((unsigned long long)foreground);
    text(",\"pid\":"); number(pid); text(",\"matched\":"); text(foreground == expected ? "true" : "false");
    text(",\"set_foreground_result\":"); number((unsigned)set_result);
    text(",\"bring_to_top_result\":"); number((unsigned)top_result);
    text(",\"title\":"); quoted(title); text("}");
    return foreground == expected;
}
static int activate(HWND window, int *top_result) {
    ShowWindow(window, 5); *top_result = BringWindowToTop(window); return SetForegroundWindow(window);
}
void mainCRTStartup(void) {
    player = FindWindowA(0, "AncientConquest"); sink = FindWindowA("Notepad", 0);
    if (!sink) sink = FindWindowA(0, "Untitled - Notepad");
    if (!player || !sink || player == sink) { text("{\"passed\":false,\"error\":\"owned-window-not-found\"}"); emit(); ExitProcess(2); }
    /* A fresh GUI worker needs a message queue before attaching. Share only
       these owned windows' input queues to request a genuine foreground change. */
    unsigned long long message[8] = {0};
    PeekMessageA(message, 0, 0, 0, 0);
    DWORD current_thread = GetCurrentThreadId();
    DWORD player_thread = GetWindowThreadProcessId(player, 0);
    DWORD sink_thread = GetWindowThreadProcessId(sink, 0);
    int player_attached = current_thread != player_thread && AttachThreadInput(current_thread, player_thread, 1);
    int sink_attached = current_thread != sink_thread && AttachThreadInput(current_thread, sink_thread, 1);
    text("{\"player_hwnd\":"); number((unsigned long long)player);
    text(",\"sink_hwnd\":"); number((unsigned long long)sink); text(",");
    int top_result = 0, set_result = activate(player, &top_result);
    Sleep(40); int before = status("before", player, set_result, top_result);
    text(","); set_result = activate(sink, &top_result);
    Sleep(160); int changed = status("sink", sink, set_result, top_result);
    text(","); set_result = activate(player, &top_result);
    Sleep(40); int restored = status("restored", player, set_result, top_result);
    text(",\"passed\":"); text(before && changed && restored ? "true" : "false"); text("}"); emit();
    if (sink_attached) AttachThreadInput(current_thread, sink_thread, 0);
    if (player_attached) AttachThreadInput(current_thread, player_thread, 0);
    ExitProcess(before && changed && restored ? 0 : 3);
}
