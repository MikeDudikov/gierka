/* Observe only the supplied original installer inside an offline private guest.
 * No buttons are pressed. Window text/control IDs are logged instead of images. */
#include <windows.h>
#include <stdint.h>
static HANDLE output;
static DWORD installer_pid;
static void zero(void *p,DWORD n){BYTE *b=p;while(n--)*b++=0;}
static void text(const char *s){DWORD n=0,w;while(s[n])n++;WriteFile(output,s,n,&w,0);}
static void number(DWORD n){char b[16];DWORD i=0,w;do{b[i++]=(char)('0'+n%10);n/=10;}while(n);while(i)WriteFile(output,b+--i,1,&w,0);}
static void escaped(const char *s){text("\"");while(*s){char b[2];b[0]=*s++;b[1]=0;if(b[0]=='"'||b[0]=='\\')text("\\");if((BYTE)b[0]>=32)text(b);}text("\"");}
static BOOL CALLBACK record(HWND window,LPARAM arg){
 DWORD pid;char title[1024],klass[128];(void)arg;GetWindowThreadProcessId(window,&pid);
 if(pid!=installer_pid)return TRUE;
 title[0]=0;klass[0]=0;GetWindowTextA(window,title,sizeof(title));GetClassNameA(window,klass,sizeof(klass));
 text("{\"event\":\"control\",\"id\":");number((DWORD)GetDlgCtrlID(window));text(",\"visible\":");number(IsWindowVisible(window));
 text(",\"enabled\":");number(IsWindowEnabled(window));text(",\"class\":");escaped(klass);text(",\"title\":");escaped(title);text("}\n");return TRUE;
}
static BOOL CALLBACK top_record(HWND window,LPARAM arg){record(window,arg);EnumChildWindows(window,record,arg);return TRUE;}
void mainCRTStartup(void){
 STARTUPINFOA startup;PROCESS_INFORMATION child;DWORD started,exit_code=0xffffffff,round=0;
 char command[]="\"D:\\SETUP.EXE\"";
 output=GetStdHandle(STD_OUTPUT_HANDLE);zero(&startup,sizeof(startup));zero(&child,sizeof(child));startup.cb=sizeof(startup);
 if(!CreateProcessA(0,command,0,0,FALSE,CREATE_DEFAULT_ERROR_MODE,0,"D:\\",&startup,&child)){
  text("{\"event\":\"create-error\",\"code\":");number(GetLastError());text("}\n");ExitProcess(2);
 }
 installer_pid=child.dwProcessId;started=GetTickCount();
 text("{\"event\":\"started\",\"pid\":");number(installer_pid);text("}\n");
 while(GetTickCount()-started<30000){
  if(WaitForSingleObject(child.hProcess,2000)==WAIT_OBJECT_0)break;
  text("{\"event\":\"snapshot\",\"round\":");number(round++);text("}\n");EnumWindows(top_record,0);
 }
 GetExitCodeProcess(child.hProcess,&exit_code);
 text("{\"event\":\"status\",\"child_exit\":");number(exit_code);text(",\"observation_only\":true}\n");
 if(exit_code==STILL_ACTIVE)TerminateProcess(child.hProcess,124);
 CloseHandle(child.hThread);CloseHandle(child.hProcess);ExitProcess(0);
}
