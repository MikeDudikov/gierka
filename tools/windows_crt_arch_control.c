/* Freestanding Kernel32-only control;does not map or execute game code. */
#include <windows.h>
void mainCRTStartup(void){
 const char *message=sizeof(void*)==4?"PE32_CONTROL_OK\n":"PE64_CONTROL_OK\n";DWORD written;
 WriteFile(GetStdHandle(STD_OUTPUT_HANDLE),message,15,&written,0);ExitProcess(written==15?0:1);
}
