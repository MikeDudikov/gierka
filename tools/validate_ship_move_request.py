#!/usr/bin/env python3
"""Narrow original-x86 ship action20 request and pending promotion evidence.

No movement, pathfinding, AI, renderer or general order queue is emulated.
"""
from pathlib import Path
import sys, struct, json, hashlib, argparse, subprocess, tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import validate_mission_object_selection as selection
import validate_mission_ship_seed as seeds


def native_dependencies():
    global pefile, UC_HOOK_CODE, UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_ECX
    import pefile
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_ECX

OBJ, APP, SYSTEM, PAYLOAD = seeds.OBJ, seeds.APP, seeds.SYSTEM, seeds.PAYLOAD
MESSAGE, ACTION, DATA = (selection.CONTEXT + v for v in (0x50000, 0x51000, 0x52000))
END = selection.END


class Original:
    def __init__(self, image, size, payload, instance, skip_derived=True):
        native_dependencies()
        self.uc = selection.new_engine(image, size)
        self.calls, self.hooks = [], []
        self.phase = 'ctor'
        self.skip_derived = skip_derived
        self.uc.hook_add(UC_HOOK_CODE, self.hook)
        self.put(0x5d1f90, 0xabcdef01)
        self.invoke(0x4dc3f0)
        for offset, value in ((0x10, APP), (0x4c, instance), (0x68, APP), (0x6c, SYSTEM), (0x70, SYSTEM)):
            self.put(OBJ + offset, value)
        self.uc.mem_write(PAYLOAD, payload)
        self.phase = 'load'
        self.invoke(0x4dfa90, (PAYLOAD,))
        self.phase = 'request'
        self.initial = self.snapshot()
        self.calls.clear()

    def put(self, address, value):
        selection.put(self.uc, address, value)

    def get(self, address):
        return selection.get(self.uc, address)

    def byte(self, offset, value=None):
        if value is not None:
            self.uc.mem_write(OBJ + offset, bytes((value & 255,)))
        return bytes(self.uc.mem_read(OBJ + offset, 1))[0]

    def ret(self, clean=0, eax=0):
        stack = self.uc.reg_read(UC_X86_REG_ESP)
        self.uc.reg_write(UC_X86_REG_EIP, self.get(stack))
        self.uc.reg_write(UC_X86_REG_ESP, stack + 4 + clean)
        self.uc.reg_write(UC_X86_REG_EAX, eax)

    def hook(self, uc, address, size, unused):
        if address == 0x587318:
            self.hooks.append({'phase': self.phase, 'entry': hex(address), 'kind': 'normal setjmp return'})
            self.ret()
        elif address == 0x50e640 and self.phase == 'load':
            self.hooks.append({'phase': self.phase, 'entry': hex(address), 'kind': 'system-message boundary'})
            self.ret(4)
        elif address == 0x4bee60 and self.phase == 'load' and self.skip_derived:
            self.hooks.append({'phase': self.phase, 'entry': hex(address), 'kind': 'derived initialization boundary'})
            self.ret()
        elif address in (0x556610, 0x556880):
            raise AssertionError('Original error path ' + hex(address))
        if address in (0x4dc630, 0x50c970, 0x4e2ba0, 0x4e6700, 0x4a9e30,
                       0x4ab720, 0x4abe50, 0x4abc60, 0x4ab250, 0x4b97d0, 0x4bd0c0):
            stack = uc.reg_read(UC_X86_REG_ESP)
            args = [self.get(stack + 4 + 4 * i) for i in range(2)]
            record = {'entry': hex(address), 'arguments': args}
            if address == 0x4a9e30 and args[0] == 0x80:
                record['copied_bytes'] = bytes(uc.mem_read(args[1], 26)).hex()
            self.calls.append(record)

    def invoke(self, address, args=()):
        top = selection.STACK + selection.STACK_SIZE - 0x1000
        for index, value in enumerate((END, *args)):
            self.put(top + 4 * index, value)
        self.uc.reg_write(UC_X86_REG_ESP, top)
        self.uc.reg_write(UC_X86_REG_ECX, OBJ)
        self.uc.emu_start(address, END, count=1000000)
        assert self.uc.reg_read(UC_X86_REG_EIP) == END, hex(self.uc.reg_read(UC_X86_REG_EIP))
        assert self.get(0x5d1f90) == 0xabcdef01

    def request(self, x, y, metadata=255, action=20):
        self.put(MESSAGE + 0x10, 0x280f)
        self.put(MESSAGE + 0x14, ACTION)
        self.uc.mem_write(ACTION + 0xc, bytes((action,)))
        self.put(ACTION + 0xd, DATA)
        self.uc.mem_write(DATA, struct.pack('<IIB', x & 0xffffffff, y & 0xffffffff, metadata))
        self.invoke(0x4dc630, (MESSAGE,))

    def snapshot(self):
        values = {'pending': self.get(OBJ + 0x7d6), 'ready_mask': self.get(OBJ + 0x7da),
                  'active': self.get(OBJ + 0x25d), 'capabilities': self.get(OBJ + 0x261),
                  'deferred': self.get(OBJ + 0x265), 'life_status': self.byte(0x251),
                  'pending_26_bytes': bytes(self.uc.mem_read(OBJ + 0x858, 26)).hex(),
                  'mode': self.byte(0x54c), 'submode': self.byte(0x54d),
                  'target_x': struct.unpack('<i', self.uc.mem_read(OBJ + 0x54e, 4))[0],
                  'target_y': struct.unpack('<i', self.uc.mem_read(OBJ + 0x552, 4))[0],
                  'first_navigation': self.byte(0x593), 'navigation_byte_591': self.byte(0x591),
                  'byte_5c7': self.byte(0x5c7), 'byte_5c8': self.byte(0x5c8),
                  'clear_33_bytes': bytes(self.uc.mem_read(OBJ + 0x562, 33)).hex(),
                  'word_57b': self.get(OBJ + 0x57b), 'word_57f': self.get(OBJ + 0x57f),
                  'source_queue_count_482': self.byte(0x482), 'source_queue_index_483': self.byte(0x483)}
        return values


def native_evidence(source_root=selection.SOURCE_ROOT):
    native_dependencies()
    sources = selection.checked_sources(source_root)
    pe = pefile.PE(data=sources['installed/ancient.exe'])
    image, size = pe.get_memory_mapped_image(), pe.OPTIONAL_HEADER.SizeOfImage
    records = seeds.source_records(sources)
    report = {'original_hashes': selection.SOURCE_HASHES, 'cases': [], 'scope': 'request+idle promotion only; no navigation/pathfinding/AI/world'}
    def new(index=0):
        entry, payload = records[index]
        return Original(image, size, payload, int(entry['name'][4:], 16))
    def add(label, obj, before=None):
        report['cases'].append({'label': label, 'initial': obj.initial, 'before': before,
                                'after': obj.snapshot(), 'calls': obj.calls, 'hooks': obj.hooks})

    for index, (entry, payload) in enumerate(records):
        obj = new(index)
        x, y = struct.unpack_from('<ii', payload, 36)
        obj.request(x - 1, y + 1)
        requested = obj.snapshot()
        assert requested['pending'] & 0x80 and requested['active'] == 0
        assert requested['pending_26_bytes'] == (b'\0'*4 + struct.pack('<ii', x-1, y+1) + b'\0'*13 + b'\xff').hex()
        obj.uc.mem_write(DATA, b'\xaa' * 9)  # subsequent mutation cannot change copied request
        assert obj.snapshot()['pending_26_bytes'] == requested['pending_26_bytes']
        obj.invoke(0x4ab720)
        result = obj.snapshot()
        assert result['target_x'] == x-1 and result['target_y'] == y+1
        assert result['pending'] == 0 and result['active'] == 0x80
        assert result['first_navigation'] == 1 and result['byte_5c8'] == 5
        assert result['source_queue_count_482'] == result['source_queue_index_483'] == 0
        assert not any(c['entry'] in ('0x4b97d0', '0x4bd0c0') for c in obj.calls)
        add('source:' + entry['name'], obj, requested)

    obj = new(); obj.request(15, 3, 4); obj.request(17, 2, 9)
    requested = obj.snapshot(); obj.invoke(0x4ab720)
    assert (obj.snapshot()['target_x'], obj.snapshot()['target_y'], obj.byte(0x5c7)) == (17, 2, 9)
    add('newest-pending-overwrites', obj, requested)

    for cap in (0, 0x3ff, 0x400, 0x401, 0xffffffff):
        obj = new(); obj.put(OBJ + 0x261, cap); before = obj.snapshot(); obj.request(15,3)
        assert bool(obj.snapshot()['pending'] & 0x80) == bool(cap & 0x400)
        add('request-capabilities:' + hex(cap), obj, before)
    for status in (0,1,2,4):
        obj = new(); obj.request(15,3); obj.byte(0x251,status); before=obj.snapshot(); obj.invoke(0x4ab720)
        assert bool(obj.snapshot()['active'] & 0x80) == (status == 0)
        add('consumer-status:' + str(status), obj, before)
    for ready in (0,0x7f,0x80,0xffffffff):
        obj = new(); obj.request(15,3); obj.put(OBJ+0x7da,ready); before=obj.snapshot(); obj.invoke(0x4ab720)
        assert bool(obj.snapshot()['active'] & 0x80) == bool(ready & 0x80)
        add('consumer-ready:' + hex(ready), obj, before)
    for metadata in (0,1,50,127,128,254,255):
        obj = new(); obj.byte(0x5c7,88); obj.request(15,3,metadata); before=obj.snapshot(); obj.invoke(0x4ab720)
        assert obj.byte(0x5c7) == (88 if metadata==255 else metadata)
        add('metadata-sentinel:' + str(metadata),obj,before)
    for x,y in ((0,0),(-1,24),(24,-1),(-2147483648,2147483647),(2147483647,-2147483648)):
        obj=new();obj.request(x,y);before=obj.snapshot();obj.invoke(0x4ab720)
        assert (obj.snapshot()['target_x'],obj.snapshot()['target_y'])==(x,y)
        add('unvalidated-coordinate-bits:'+str((x,y)),obj,before)
    obj=new();obj.request(15,3);obj.put(OBJ+0x261,0);before=obj.snapshot();obj.invoke(0x4ab250)
    assert obj.snapshot()['pending']==0 and obj.snapshot()['active']==0
    add('promotion-capability-removed',obj,before)

    obj=new();obj.request(15,3);obj.invoke(0x4ab720);obj.request(17,2,7);before=obj.snapshot();obj.invoke(0x4ab720)
    assert (obj.snapshot()['target_x'],obj.snapshot()['target_y'],obj.snapshot()['active'])==(17,2,0x80)
    add('replace-active-idle-order',obj,before)
    obj=new();obj.request(15,3);obj.put(OBJ+0x7da,0);obj.invoke(0x4ab720);before=obj.snapshot();obj.put(OBJ+0x7da,0x80);obj.invoke(0x4ab720)
    assert before['pending']==0x80 and obj.snapshot()['target_x']==15
    add('ready-mask-eventually-permits',obj,before)
    obj=new();obj.request(15,3);obj.byte(0x251,1);obj.invoke(0x4ab720);before=obj.snapshot();obj.byte(0x251,0);obj.invoke(0x4ab720)
    assert before['pending']==0x80 and obj.snapshot()['target_x']==15
    add('status-eventually-permits',obj,before)
    obj=new();before=obj.snapshot();obj.request(15,3,action=11)
    assert obj.snapshot()==before
    add('unsupported-action-11-noop',obj,before)
    for pattern in (bytes(26),bytes(range(26)),bytes((0xaa,0x55))*13,b'\xff'*26):
        obj=new();obj.uc.mem_write(DATA,pattern);obj.uc.mem_write(OBJ+0x857,b'\xcc');obj.uc.mem_write(OBJ+0x872,b'\xdd')
        obj.invoke(0x4a9e30,(0x80,DATA));obj.uc.mem_write(DATA,b'\xee'*26)
        assert bytes(obj.uc.mem_read(OBJ+0x858,26))==pattern
        assert bytes(obj.uc.mem_read(OBJ+0x857,1))==b'\xcc' and bytes(obj.uc.mem_read(OBJ+0x872,1))==b'\xdd'
        add('internal-exact-copy-guards:'+pattern.hex(),obj)
    for caps in (0x400,0x410,0x480,0x500):
        obj=new();obj.put(OBJ+0x261,caps);obj.request(15,3);before=obj.snapshot();obj.invoke(0x4ab720)
        assert bool(obj.snapshot()['active']&0x80)==bool(caps&0x1f0)
        add('consumer-capability-families:'+hex(caps),obj,before)

    report['priority_prefix_cases']=[]
    for combination in range(1,32):
        mask=sum(bit for index,bit in enumerate((0x20,0x40,0x10,0x100,0x80)) if combination&(1<<index))
        obj=new();obj.put(OBJ+0x25d,0x80);obj.byte(0x58b,1);obj.put(OBJ+0x7d6,mask)
        top=selection.STACK+selection.STACK_SIZE-0x1000
        obj.put(top,END);obj.uc.reg_write(UC_X86_REG_ESP,top);obj.uc.reg_write(UC_X86_REG_ECX,OBJ)
        # Stop before the cancellation call. This proves only candidate priority;
        # it deliberately makes no claim that cancellation retains that candidate.
        obj.uc.emu_start(0x4abe50,0x4abef9,count=1000)
        assert obj.uc.reg_read(UC_X86_REG_EIP)==0x4abef9
        expected=next(bit for bit in (0x20,0x40,0x10,0x100,0x80) if mask&bit)
        assert obj.get(OBJ+0x265)==expected
        report['priority_prefix_cases'].append({'pending':mask,'candidate':obj.get(OBJ+0x265),'stop':'0x4abef9 before cancellation'})
    report['case_count']=len(report['cases'])
    report['source_cases']=8
    report['stress_cases']=len(report['cases'])-8
    report['priority_prefix_case_count']=len(report['priority_prefix_cases'])
    return report


gate = selection.gate
MissingPrerequisite = selection.MissingPrerequisite
SOURCE = ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipMoveRequestInbox.cs'
PROBE = ROOT / 'tests/fixtures/ShipMoveRequestProbe.cs'
FIXTURE = ROOT / 'tests/fixtures/ship_move_request.json'
FIXTURE_SHA256 = 'f8f3b012b0308479ca80322b1a7903b3b217b889a63e2b75c0132faac79ff6b0'
OUTPUT = ROOT / 'artifacts/movement/orders/csharp-validation.json'


def project(obj):
    state = obj.snapshot()
    return [state['pending'], state['active'], int(bool(state['pending'] & 0x80)),
            state['target_x'], state['target_y'], state['byte_5c7'], state['first_navigation'],
            state['pending_26_bytes']]


def differential_cases(sources):
    native_dependencies()
    pe = pefile.PE(data=sources['installed/ancient.exe'])
    image, size = pe.get_memory_mapped_image(), pe.OPTIONAL_HEADER.SizeOfImage
    records = seeds.source_records(sources)
    cases = []

    def add(group, label, operations, index=0, caps=None, ready=0xffffffff, status=0, route=0):
        entry, payload = records[index]
        obj = Original(image, size, payload, int(entry['name'][4:], 16))
        caps = obj.get(OBJ+0x261) if caps is None else caps
        obj.put(OBJ+0x261,caps);obj.put(OBJ+0x7da,ready);obj.byte(0x251,status);obj.byte(0x5c7,route)
        steps = [{'result':-1,'state':project(obj)}]
        for operation in operations:
            if operation[0]=='r':
                calls_before=len(obj.calls)
                obj.request(*operation[1:])
                result=int(any(c['entry']=='0x4a9e30' and c['arguments'][0]==0x80
                               for c in obj.calls[calls_before:]))
            elif operation[0]=='c':
                obj.put(OBJ+0x261,operation[1]);obj.put(OBJ+0x7da,operation[2]);obj.byte(0x251,operation[3]);result=-1
            elif operation[0]=='p':
                before=obj.snapshot();obj.invoke(0x4ab720);after=obj.snapshot()
                result=0 if not(before['pending']&0x80) else 1 if after['pending']&0x80 else 3 if after['active']&0x80 else 2
            else:raise ValueError(operation)
            steps.append({'result':result,'state':project(obj)})
        assert not any(c['entry'] in ('0x4b97d0','0x4bd0c0') for c in obj.calls)
        cases.append({'group':group,'label':label,'resource_name':entry['name'],
                      'payload_sha256':hashlib.sha256(payload).hexdigest(),
                      'context':[caps,ready,status,route],'operations':operations,'steps':steps})

    r=lambda x=15,y=3,b=255:['r',x,y,b]
    p=['p']
    c=lambda caps=0xfffff7ff,ready=0xffffffff,status=0:['c',caps,ready,status]
    for index,(entry,payload) in enumerate(records):
        x,y=struct.unpack_from('<ii',payload,36)
        add('source',entry['name'],[r(x-1,y+1),p],index=index)
    for cap in (0,0x3ff,0x400,0x401,0xffffffff):
        add('request-capability',hex(cap),[r(),p],caps=cap)
    for status in (0,1,2,4):add('consumer-status',str(status),[r(),c(status=status),p])
    for ready in (0,0x7f,0x80,0xffffffff):add('consumer-ready',hex(ready),[r(),c(ready=ready),p])
    for value in (0,1,50,127,128,254,255):add('route-sentinel',str(value),[r(b=value),p],route=88)
    for x,y in ((0,0),(-1,24),(24,-1),(-2147483648,2147483647),(2147483647,-2147483648)):
        add('coordinate-bits',str((x,y)),[r(x,y),p])
    add('replacement','pending',[r(b=4),r(17,2,9),p])
    add('replacement','active-idle',[r(),p,r(17,2,7),p])
    add('deferred','ready-resume',[r(),c(ready=0),p,c(ready=0x80),p])
    add('deferred','status-resume',[r(),c(status=1),p,c(),p])
    for cap in (0,0x80,0x100):add('capability-change',hex(cap),[r(),c(caps=cap),p])
    add('replacement','rejected-after-pending',[r(),c(caps=0),r(17,2),c(),p])
    add('no-pending','empty-and-completed',[p,r(),p,p])
    add('active-before-deferred','ready-clears-active',[r(),p,r(17,2),c(ready=0),p])
    add('active-before-deferred','status-keeps-active',[r(),p,r(17,2),c(status=1),p])
    add('active-before-deferred','cap-family-keeps-active',[r(),p,r(17,2),c(caps=0x400),p])
    return cases


def fixture_data(cases):
    return {'original_hashes':selection.SOURCE_HASHES,'scope':'action20 copied pending record and initial idle consumer only',
            'source_case_count':8,'case_count':len(cases),'cases':cases}


def validate(source_root=selection.SOURCE_ROOT,mono_root=None):
    sources=selection.checked_sources(source_root)
    _,unicorn,runtime,compiler=gate.prerequisites(Path(source_root)/'installed/ancient.exe',mono_root)
    original=native_evidence(source_root)
    cases=differential_cases(sources)
    gate.require(gate.digest(FIXTURE)==FIXTURE_SHA256,'Pinned move-request fixture changed')
    gate.require(json.loads(FIXTURE.read_text())==fixture_data(cases),'Original x86 differs from move-request fixture')
    with tempfile.TemporaryDirectory(prefix='ship-move-request-') as temporary:
        exe=Path(temporary)/'ShipMoveRequestProbe.exe'
        build=subprocess.run(compiler+['/nologo','/checked+','/target:exe','/out:'+str(exe),str(SOURCE),str(PROBE)],
                             text=True,capture_output=True,timeout=60)
        if build.returncode:raise RuntimeError('C# move-request compilation failed:\n'+build.stdout+build.stderr)
        lines=[]
        for case in cases:
            operations=';'.join(','.join(map(str,op)) for op in case['operations'])
            lines.append('\t'.join(map(str,case['context']))+'\t'+operations)
        output=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',text=True,capture_output=True,timeout=60,check=True)
    rows=output.stdout.splitlines()
    gate.require(rows and rows[-1].startswith('GUARDS\t'),'C# move-request guards did not complete')
    guards=int(rows.pop().split('\t')[1]);expected=[]
    for case_index,case in enumerate(cases):
        for step_index,step in enumerate(case['steps']):
            expected.append('\t'.join(map(str,[case_index,step_index,step['result'],*step['state']])))
    gate.require(len(rows)==len(expected),'C# returned a different step count')
    for index,(actual,wanted) in enumerate(zip(rows,expected)):
        gate.require(actual==wanted,f'Move-request differential mismatch at step {index}: x86 {wanted} / C# {actual}')
    groups={group:sum(case['group']==group for case in cases) for group in sorted({c['group'] for c in cases})}
    return {'original_hashes':selection.SOURCE_HASHES,'scope':fixture_data(cases)['scope'],
            'native_request_cases':original['case_count'],'native_source_cases':8,'native_stress_cases':original['stress_cases'],
            'native_priority_prefix_cases':original['priority_prefix_case_count'],'case_count':len(cases),
            'source_case_count':8,'passed':len(cases),'step_comparisons':len(rows),'case_groups':groups,
            'csharp_contract_checks':guards,'checked_compilation':True,'fixture_sha256':FIXTURE_SHA256,
            'source_sha256':{str(SOURCE.relative_to(ROOT)):gate.digest(SOURCE)},'validator_sha256':gate.digest(Path(__file__)),
            'probe_sha256':gate.digest(PROBE),'compiler_command':compiler,'mono_runtime':str(runtime),
            'unicorn_version':unicorn.__version__,'native_evidence':original,'differential_cases':cases,
            'hooks':{'request_and_idle_consumer':{'0x587318':'normal setjmp return'},
                     'preparation_only':{'0x587318':'normal setjmp return','0x4bee60':'derived initialization boundary','0x50e640':'system-message boundary'},
                     'priority_prefix':{}},
            'limits':['Busy contexts and statuses outside0/1/2/4 are adapter policy rejections, not source behavior claims',
                      'No general order collection, pathfinder, movement, Life, AI, rendering or input mapping is implemented',
                      'Inputs and source payload field initialization are explicit; this is not full StartGame']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,default=selection.SOURCE_ROOT)
    parser.add_argument('--mono-root',type=Path)
    parser.add_argument('--output',type=Path,default=OUTPUT)
    args=parser.parse_args(argv)
    if args.output.exists():parser.error('Select a fresh output path; previous evidence is preserved')
    try:report=validate(args.source_root,args.mono_root)
    except MissingPrerequisite as error:parser.exit(2,str(error)+'\n')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as stream:stream.write(json.dumps(report,indent=2)+'\n')
    print(f"{report['passed']} original x86 / C# move-request cases; {report['step_comparisons']} steps; {report['csharp_contract_checks']} guards")
    return 0


if __name__=='__main__':raise SystemExit(main())
