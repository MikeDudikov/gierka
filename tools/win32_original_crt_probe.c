/* Win32 diagnostic: map original CRT/data pages580000..5ddfff without relocations;execute original
 * heap_init58ec07(0),malloc589bf5/free589bc6. No game entry/App/Life runs.
 * Kernel32 imports use the host Wine APIs;the source CRT instructions are intact.
 */
#include <windows.h>
#include <stdint.h>

/* Reserve original addresses with the probe image before Wine maps its data. */
__attribute__((section(".origcrt"),used)) static BYTE original_crt_pages[0x5e000];
static HANDLE output;
static void bytes_copy(void *to,const void *from,DWORD n){BYTE*d=to;const BYTE*s=from;while(n--)*d++=*s++;}
static DWORD text_len(const char*s){DWORD n=0;while(s[n])n++;return n;}
static void text(const char*s){DWORD n=0;WriteFile(output,s,text_len(s),&n,0);}
static void number(DWORD n){char b[16];DWORD count=0;do{b[count++]=(char)('0'+n%10);n/=10;}while(n);while(count){DWORD written;WriteFile(output,b+--count,1,&written,0);}}
static void signed_number(LONG n){if(n<0){text("-");number(0u-(DWORD)n);}else number((DWORD)n);}
static void fail(const char*s,DWORD code){text("{\"error\":\"");text(s);text("\",\"code\":");number(code);text("}\n");ExitProcess(code?code:99);}
static int same_kernel(const char*s){const char*k="kernel32.dll";while(*s&&*k){char c=*s++;if(c>='A'&&c<='Z')c=(char)(c+'a'-'A');if(c!=*k++)return 0;}return !*s&&!*k;}
static const char *argument(const char*p,char*out,DWORD cap){DWORD n=0;int quote=0;while(*p==' ')p++;if(*p=='\"'){quote=1;p++;}while(*p&&((quote&&*p!='\"')||(!quote&&*p!=' '))){if(n+1>=cap)fail("argument",2);out[n++]=*p++;}out[n]=0;if(quote&&*p=='\"')p++;return p;}
static LONG WINAPI exception(EXCEPTION_POINTERS*p){text("{\"exception\":");number(p->ExceptionRecord->ExceptionCode);text(",\"eip\":");number(p->ContextRecord->Eip);text("}\n");ExitProcess(90);return EXCEPTION_EXECUTE_HANDLER;}

static BYTE *map_original(const char*path){
 HANDLE f=CreateFileA(path,GENERIC_READ,FILE_SHARE_READ,0,OPEN_EXISTING,0,0);if(f==INVALID_HANDLE_VALUE)fail("open",GetLastError());
 DWORD length=GetFileSize(f,0),read=0;if(length<4096||length>16777216)fail("file-size",3);
 BYTE *raw=VirtualAlloc(0,length,MEM_COMMIT|MEM_RESERVE|MEM_TOP_DOWN,PAGE_READWRITE);if(!raw)fail("read-buffer",4);
 if(!ReadFile(f,raw,length,&read,0)||read!=length)fail("read",5);
 CloseHandle(f);
 IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER*)raw;if(dos->e_magic!=IMAGE_DOS_SIGNATURE||(DWORD)dos->e_lfanew>length-sizeof(IMAGE_NT_HEADERS32))fail("dos-header",6);
 IMAGE_NT_HEADERS32 *nt=(IMAGE_NT_HEADERS32*)(raw+dos->e_lfanew);
 if(nt->Signature!=IMAGE_NT_SIGNATURE||nt->FileHeader.Machine!=IMAGE_FILE_MACHINE_I386||nt->OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR32_MAGIC||nt->OptionalHeader.ImageBase!=0x400000||nt->OptionalHeader.SizeOfImage!=0x1de000)fail("pe-profile",7);
 /* The probe needs only the original CRT/data/import pages. Mapping unused
  * game text at400000 can collide with the probe process heap. Addresses of
  * all executed source instructions/globals remain unchanged;no relocations. */
 BYTE *image=(BYTE*)0x400000;
 DWORD previous_protection=0;BYTE *mapped=original_crt_pages;
 if(mapped!=(BYTE*)0x580000||!VirtualProtect(mapped,0x5e000,PAGE_EXECUTE_READWRITE,&previous_protection))fail("owned-crt-pages",GetLastError());
 if(mapped!=(BYTE*)0x580000){
  DWORD error=GetLastError();MEMORY_BASIC_INFORMATION info;VirtualQuery((void*)0x580000,&info,sizeof(info));
  text("{\"kind\":\"mapping-failure\",\"raw_address\":");number((DWORD)(uintptr_t)raw);text(",\"region_base\":");number((DWORD)(uintptr_t)info.BaseAddress);text(",\"region_size\":");number((DWORD)info.RegionSize);text(",\"region_state\":");number(info.State);text("}\n");fail("crt-pages",error);
 }
 if(nt->OptionalHeader.SizeOfHeaders>length)fail("headers",8);
 /* Original header remains in raw;only original CRT/data pages are copied. */
 IMAGE_SECTION_HEADER *section=IMAGE_FIRST_SECTION(nt);
 for(WORD i=0;i<nt->FileHeader.NumberOfSections;i++){
  if(section[i].PointerToRawData>length||section[i].SizeOfRawData>length-section[i].PointerToRawData||section[i].VirtualAddress>nt->OptionalHeader.SizeOfImage||section[i].SizeOfRawData>nt->OptionalHeader.SizeOfImage-section[i].VirtualAddress)fail("section",9);
  DWORD start=section[i].VirtualAddress,finish=start+section[i].SizeOfRawData;
  if(start<0x180000)start=0x180000;
  if(finish>0x1de000)finish=0x1de000;
  if(start<finish)bytes_copy(image+start,raw+section[i].PointerToRawData+start-section[i].VirtualAddress,finish-start);
 }
 IMAGE_IMPORT_DESCRIPTOR *import=(IMAGE_IMPORT_DESCRIPTOR*)(image+nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress);DWORD fixed=0;
 for(;import->Name;import++){
  const char *name=(char*)(image+import->Name);if(!same_kernel(name))continue;
  HMODULE module=GetModuleHandleA("kernel32.dll");if(!module)fail("kernel32",10);
  IMAGE_THUNK_DATA32 *lookup=(IMAGE_THUNK_DATA32*)(image+(import->OriginalFirstThunk?import->OriginalFirstThunk:import->FirstThunk));
  IMAGE_THUNK_DATA32 *iat=(IMAGE_THUNK_DATA32*)(image+import->FirstThunk);
  for(;lookup->u1.AddressOfData;lookup++,iat++){
   const char *symbol=IMAGE_SNAP_BY_ORDINAL32(lookup->u1.Ordinal)?(const char*)(uintptr_t)IMAGE_ORDINAL32(lookup->u1.Ordinal):(const char*)((IMAGE_IMPORT_BY_NAME*)(image+lookup->u1.AddressOfData))->Name;
   FARPROC proc=GetProcAddress(module,symbol);if(!proc)fail("kernel-import",11);iat->u1.Function=(DWORD)(uintptr_t)proc;fixed++;
  }
 }
 if(fixed<20)fail("import-count",12);
 VirtualFree(raw,0,MEM_RELEASE);return image;
}

void mainCRTStartup(void){
 output=GetStdHandle(STD_OUTPUT_HANDLE);SetUnhandledExceptionFilter(exception);
 char own[512],path[1024],modeText[32];const char*command=GetCommandLineA();command=argument(command,own,sizeof(own));command=argument(command,path,sizeof(path));argument(command,modeText,sizeof(modeText));
 if(!path[0])fail("source-path-required",1);
 DWORD mode=modeText[0]=='1'?1:0;map_original(path);
 typedef int (__cdecl *Init)(int);typedef void* (__cdecl *Malloc)(unsigned int);typedef void (__cdecl *Free)(void*);
 Init init=(Init)(uintptr_t)0x58ec07;Malloc alloc=(Malloc)(uintptr_t)0x589bf5;Free release=(Free)(uintptr_t)0x589bc6;
 if(!init((int)mode))fail("source-heap-init",13);
 HANDLE heap=*(HANDLE*)(uintptr_t)0x5d2fc4;DWORD threshold=*(DWORD*)(uintptr_t)0x5c63b8;
 text("{\"kind\":\"conditions\",\"pointer_bits\":32,\"heap_init_arg\":");number(mode);text(",\"source_threshold\":");number(threshold);text(",\"wave_request\":1152,\"heap_compatibility\":");
 ULONG compatibility=0;SIZE_T returned=0;if(!HeapQueryInformation(heap,HeapCompatibilityInformation,&compatibility,sizeof(compatibility),&returned))fail("heap-info",14);number(compatibility);text("}\n");
 /* Vary small-block and native-heap history with the actual source malloc/free. */
 static const DWORD sizes[]={1,8,16,31,128,511,1016,1017,1152,2048,4096};
 void *held[96];for(DWORD i=0;i<96;i++){held[i]=alloc(sizes[i%11]);if(!held[i])fail("history-alloc",15);}
 for(DWORD i=0;i<96;i+=2){release(held[i]);held[i]=0;}
 for(DWORD i=0;i<256;i++){
  void *p=alloc(1152);if(!p)fail("wave-alloc",16);SIZE_T usable=HeapSize(heap,0,p);if(usable==(SIZE_T)-1)fail("source-native-heap",17);
  WORD before=*(volatile WORD*)((BYTE*)p-2);short value=(short)before;
  text("{\"kind\":\"wave\",\"sample\":");number(i);text(",\"usable\":");number((DWORD)usable);text(",\"prefix_u16\":");number(before);text(",\"prefix_i16\":");signed_number(value);text(",\"suppresses_candidate29985\":");number((short)29985<value);text("}\n");
  release(p);
  if(i%8==0){void*q=alloc(sizes[(i/8)%11]);if(!q)fail("churn",18);release(q);}
 }
 for(DWORD i=0;i<96;i++)if(held[i])release(held[i]);
 if(!HeapDestroy(heap))fail("heap-destroy",19);
 text("{\"kind\":\"complete\",\"samples\":256,\"game_entry_called\":false}\n");ExitProcess(0);
}
