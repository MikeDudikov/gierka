/* Drive only observed, explicitly queued controls of the supplied original installer.
 * Offline private guest;commands come from Z:\\probe\\actions.txt. No images. */
#include <windows.h>
#include <stdint.h>
static HANDLE output;
static DWORD installer_pid;
static DWORD applied,sequence,control_id;
static char action_kind,action_text[512];
static void zero(void *p,DWORD n){BYTE *b=p;while(n--)*b++=0;}
static void text(const char *s){DWORD n=0,w;while(s[n])n++;WriteFile(output,s,n,&w,0);}
static void number(DWORD n){char b[16];DWORD i=0,w;do{b[i++]=(char)('0'+n%10);n/=10;}while(n);while(i)WriteFile(output,b+--i,1,&w,0);}
static void escaped(const char *s){text("\"");while(*s){char b[2];b[0]=*s++;b[1]=0;if(b[0]=='"'||b[0]=='\\')text("\\");if((BYTE)b[0]>=32)text(b);}text("\"");}
static int same(const char *a,const char *b){while(*a&&*a==*b){a++;b++;}return *a==*b;}
static void read_action(void){
 HANDLE file;DWORD got=0;char data[1024],*p=data;sequence=0;
 file=CreateFileA("Z:\\probe\\actions.txt",GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,0,OPEN_EXISTING,0,0);
 if(file==INVALID_HANDLE_VALUE)return;
 if(!ReadFile(file,data,sizeof(data)-1,&got,0)){CloseHandle(file);return;}CloseHandle(file);data[got]=0;
 while(*p>='0'&&*p<='9')sequence=sequence*10+(DWORD)(*p++-'0');
 if(sequence<=applied||*p++!='\t'){sequence=0;return;}action_kind=*p++;
 if(*p++!='\t'){sequence=0;return;}control_id=0;
 while(*p>='0'&&*p<='9')control_id=control_id*10+(DWORD)(*p++-'0');
 if(*p++!='\t'){sequence=0;return;}
 {DWORD i=0;while(*p&&*p!='\r'&&*p!='\n'&&i+1<sizeof(action_text))action_text[i++]=*p++;action_text[i]=0;}
}
static void perform(HWND window,DWORD id,const char *klass,const char *title){
 int ok=0;DWORD_PTR result=0;
 if(!sequence||sequence<=applied||id!=control_id||!IsWindowVisible(window)||!IsWindowEnabled(window))return;
 if(action_kind=='C'&&same(klass,"Button")&&same(title,action_text))ok=PostMessageA(window,BM_CLICK,0,0);
 else if(action_kind=='T'&&same(klass,"Edit"))ok=SendMessageTimeoutA(window,WM_SETTEXT,0,(LPARAM)action_text,SMTO_ABORTIFHUNG|SMTO_BLOCK,500,&result)!=0;
 if(ok){applied=sequence;text("{\"event\":\"action\",\"sequence\":");number(sequence);text(",\"id\":");number(id);text(",\"text\":");escaped(action_text);text("}\n");}
}
static BOOL CALLBACK record(HWND window,LPARAM arg){
 DWORD pid;char title[1024],klass[128];(void)arg;GetWindowThreadProcessId(window,&pid);
 if(pid!=installer_pid)return TRUE;
 title[0]=0;klass[0]=0;GetWindowTextA(window,title,sizeof(title));GetClassNameA(window,klass,sizeof(klass));
 text("{\"event\":\"control\",\"id\":");number((DWORD)GetDlgCtrlID(window));text(",\"visible\":");number(IsWindowVisible(window));
 text(",\"enabled\":");number(IsWindowEnabled(window));text(",\"class\":");escaped(klass);text(",\"title\":");escaped(title);text("}\n");perform(window,(DWORD)GetDlgCtrlID(window),klass,title);return TRUE;
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
 while(GetTickCount()-started<240000){
  if(WaitForSingleObject(child.hProcess,2000)==WAIT_OBJECT_0)break;
  read_action();text("{\"event\":\"snapshot\",\"round\":");number(round++);text("}\n");EnumWindows(top_record,0);
 }
 GetExitCodeProcess(child.hProcess,&exit_code);
 text("{\"event\":\"status\",\"child_exit\":");number(exit_code);text(",\"observation_only\":false}\n");
 if(exit_code==STILL_ACTIVE)TerminateProcess(child.hProcess,124);
 CloseHandle(child.hThread);CloseHandle(child.hProcess);ExitProcess(0);
}
