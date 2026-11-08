/* Freestanding Win32 diagnostic. Launch unchanged ancient.exe in an offline guest;
 * capture the real ECX/vtable at original4eff00. Only a process-memory breakpoint
 * is installed;the on-disk source is never patched. No gameplay result is claimed. */
#include <windows.h>
#include <stdint.h>
static HANDLE output;
static DWORD observed_pid;
static void zero(void *p,DWORD n){BYTE *b=p;while(n--)*b++=0;}
static void text(const char *s){DWORD n=0,w;while(s[n])n++;WriteFile(output,s,n,&w,0);}
static void number(DWORD n){char b[16];DWORD i=0,w;do{b[i++]=(char)('0'+n%10);n/=10;}while(n);while(i)WriteFile(output,b+--i,1,&w,0);}
static void hex(DWORD n){char b[9];DWORD i;const char *digits="0123456789abcdef";for(i=0;i<8;i++)b[i]=digits[(n>>(28-4*i))&15];b[8]=0;text("\"0x");text(b);text("\"");}
static int read_memory(HANDLE p,DWORD address,void *out,DWORD n){SIZE_T got=0;return ReadProcessMemory(p,(void*)(uintptr_t)address,out,n,&got)&&got==n;}
static int patch(HANDLE p,DWORD address,BYTE byte){DWORD old,tmp;SIZE_T put=0;int ok;if(!VirtualProtectEx(p,(void*)(uintptr_t)address,1,PAGE_EXECUTE_READWRITE,&old))return 0;ok=WriteProcessMemory(p,(void*)(uintptr_t)address,&byte,1,&put)&&put==1;FlushInstructionCache(p,(void*)(uintptr_t)address,1);VirtualProtectEx(p,(void*)(uintptr_t)address,1,old,&tmp);return ok;}
static void failure(const char *name){text("{\"event\":\"error\",\"name\":\"");text(name);text("\",\"code\":");number(GetLastError());text("}\n");}
static void escaped(const char *s){text("\"");while(*s){char b[2];b[0]=*s++;b[1]=0;if(b[0]=='"'||b[0]=='\\')text("\\");if((BYTE)b[0]>=32)text(b);}text("\"");}
static BOOL CALLBACK window_record(HWND window,LPARAM arg){DWORD pid;char title[512],klass[128];(void)arg;GetWindowThreadProcessId(window,&pid);if(pid!=observed_pid)return TRUE;title[0]=0;klass[0]=0;GetWindowTextA(window,title,sizeof(title));GetClassNameA(window,klass,sizeof(klass));text("{\"event\":\"window\",\"handle\":");hex((DWORD)(uintptr_t)window);text(",\"visible\":");number(IsWindowVisible(window));text(",\"class\":");escaped(klass);text(",\"title\":");escaped(title);text("}\n");return TRUE;}
static BOOL CALLBACK top_window_record(HWND window,LPARAM arg){window_record(window,arg);EnumChildWindows(window,window_record,arg);return TRUE;}
void mainCRTStartup(void){
 STARTUPINFOA startup;PROCESS_INFORMATION child;DEBUG_EVENT event;DWORD started,code=2,target=0x4eff00;BYTE original=0;BOOL armed=FALSE,hit=FALSE,exited=FALSE;
 char command[]="\"Z:\\tmp\\original-game\\ancient.exe\"";
 output=GetStdHandle(STD_OUTPUT_HANDLE);zero(&startup,sizeof(startup));zero(&child,sizeof(child));startup.cb=sizeof(startup);
 if(!CreateProcessA(0,command,0,0,FALSE,DEBUG_ONLY_THIS_PROCESS|CREATE_DEFAULT_ERROR_MODE,0,"Z:\\tmp\\original-game",&startup,&child)){failure("CreateProcess");ExitProcess(2);}
 started=GetTickCount();observed_pid=child.dwProcessId;text("{\"event\":\"started\",\"pid\":");number(child.dwProcessId);text("}\n");
 while(GetTickCount()-started<90000){
  DWORD continuation=DBG_CONTINUE;
  if(!WaitForDebugEvent(&event,1000)){if(GetLastError()==ERROR_SEM_TIMEOUT)continue;failure("WaitForDebugEvent");break;}
  text("{\"event\":\"debug-event\",\"kind\":");number(event.dwDebugEventCode);text("}\n");
  if(event.dwDebugEventCode==CREATE_PROCESS_DEBUG_EVENT){
   DWORD base=(DWORD)(uintptr_t)event.u.CreateProcessInfo.lpBaseOfImage;
   text("{\"event\":\"image\",\"base\":");hex(base);text("}\n");
   if(base!=0x400000||!read_memory(child.hProcess,target,&original,1)||original!=0x55||!patch(child.hProcess,target,0xcc)){failure("source-breakpoint");TerminateProcess(child.hProcess,3);}
   else {armed=TRUE;text("{\"event\":\"breakpoint-armed\"}\n");}
   if(event.u.CreateProcessInfo.hFile)CloseHandle(event.u.CreateProcessInfo.hFile);
  }else if(event.dwDebugEventCode==LOAD_DLL_DEBUG_EVENT){
   text("{\"event\":\"dll\",\"base\":");hex((DWORD)(uintptr_t)event.u.LoadDll.lpBaseOfDll);text("}\n");
   if(event.u.LoadDll.hFile)CloseHandle(event.u.LoadDll.hFile);
  }else if(event.dwDebugEventCode==CREATE_THREAD_DEBUG_EVENT){
   if(event.u.CreateThread.hThread)CloseHandle(event.u.CreateThread.hThread);
  }else if(event.dwDebugEventCode==EXCEPTION_DEBUG_EVENT){
   DWORD exception=event.u.Exception.ExceptionRecord.ExceptionCode;
   DWORD address=(DWORD)(uintptr_t)event.u.Exception.ExceptionRecord.ExceptionAddress;
   text("{\"event\":\"exception-observed\",\"code\":");hex(exception);text(",\"address\":");hex(address);text("}\n");
   if(armed&&exception==EXCEPTION_BREAKPOINT&&address==target){
    HANDLE thread=OpenThread(THREAD_GET_CONTEXT|THREAD_SET_CONTEXT,FALSE,event.dwThreadId);CONTEXT context;DWORD object[9],table[9],message=0,kind=0;zero(&context,sizeof(context));context.ContextFlags=CONTEXT_FULL;
    if(!thread||!GetThreadContext(thread,&context)||!read_memory(child.hProcess,context.Ecx,object,sizeof(object))||!read_memory(child.hProcess,object[0],table,sizeof(table))||!read_memory(child.hProcess,context.Esp+4,&message,4)||!read_memory(child.hProcess,message+0x10,&kind,4)){failure("source-state");}
    else{
     DWORD i;text("{\"event\":\"source-entry\",\"address\":");hex(target);text(",\"this\":");hex(context.Ecx);text(",\"message\":");number(kind);text(",\"vtable\":");hex(object[0]);text(",\"slot18\":");hex(table[6]);text(",\"slot20\":");hex(table[8]);text(",\"object_words\":[");
     for(i=0;i<9;i++){if(i)text(",");hex(object[i]);}text("],\"vtable_words\":[");for(i=0;i<9;i++){if(i)text(",");hex(table[i]);}text("]}\n");hit=TRUE;code=0;
    }
    if(thread){CloseHandle(thread);}
    patch(child.hProcess,target,original);armed=FALSE;TerminateProcess(child.hProcess,hit?0:4);
   }else if(exception!=EXCEPTION_BREAKPOINT){
    text("{\"event\":\"exception\",\"code\":");hex(exception);text(",\"address\":");hex(address);text(",\"first_chance\":");number(event.u.Exception.dwFirstChance);text("}\n");continuation=DBG_EXCEPTION_NOT_HANDLED;
   }
  }else if(event.dwDebugEventCode==EXIT_PROCESS_DEBUG_EVENT){
   text("{\"event\":\"child-exit\",\"code\":");number(event.u.ExitProcess.dwExitCode);text("}\n");exited=TRUE;
  }
  if(!ContinueDebugEvent(event.dwProcessId,event.dwThreadId,continuation)){failure("ContinueDebugEvent");break;}if(exited)break;
 }
 if(!exited){
  EnumWindows(top_window_record,0);
  CONTEXT last;DWORD stack[24],i;zero(&last,sizeof(last));last.ContextFlags=CONTEXT_FULL;
  if(SuspendThread(child.hThread)!=(DWORD)-1){
   if(GetThreadContext(child.hThread,&last)){
    text("{\"event\":\"last-context\",\"eip\":");hex(last.Eip);text(",\"esp\":");hex(last.Esp);text(",\"stack\":[");
    if(read_memory(child.hProcess,last.Esp,stack,sizeof(stack))){for(i=0;i<24;i++){if(i)text(",");hex(stack[i]);}}text("]}\n");
   }else failure("last-context");
   ResumeThread(child.hThread);
  }else failure("SuspendThread");
  TerminateProcess(child.hProcess,124);text("{\"event\":\"timeout-or-debug-failure\"}\n");}
 CloseHandle(child.hThread);CloseHandle(child.hProcess);text("{\"event\":\"status\",\"source_hit\":");text(hit?"true":"false");text(",\"terminated_after_capture\":");text(hit?"true":"false");text("}\n");ExitProcess(code);
}
