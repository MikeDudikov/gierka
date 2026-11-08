"""Actual Shift UI/100-2 point registration,append,dispatch and route queries.

Two source engines per case compare UI and fleet entries. Cells/state/counter are explicit inputs;
no world mail delivery or ship Work. Original helpers execute;only graphics
marker creation/destruction,CRT and inherited services are boundaries.
"""
from pathlib import Path
import argparse,json,struct
import itertools
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_ESP
from tools import probe_ship_fleet_normal_task as normal
ROOT=normal.ROOT;pointer=normal.pointer;LOCAL=normal.LOCAL


class QueuedOracle(normal.TaskOracle):
    def __init__(self,metadata=None,entry='ui',patches=()):
        self.markers={};self.marker_destroyed=[];self.task_tokens={};self.calls=[]
        self.entry=entry
        super().__init__(normal.source.membership.hover.source_metadata()if metadata is None else metadata)
        for address,before,after in patches:
            assert bytes(self.u.mem_read(address,len(before)))==before
            self.u.mem_write(address,after) #Isolated negative control;original file remains unchanged.

    def hook(self,u,address,size,unused):
        if self.pointer_ready:
            sp=u.reg_read(UC_X86_REG_ESP)
            if address in(0x49de70,0x4cf2c0,0x4cef80,0x4ce6c0,0x4ce7c0,0x4ce8a0,0x4cf550,0x4cf0b0,0x4a1700):
                self.calls.append(hex(address))
            if address==0x4a1700:return #Execute source310 construction,not the parent arrival boundary.
            if address==0x4ced80:
                #Graphics-only WPMOVE construction boundary. Original4ced10 still writes coordinates.
                marker=self.heap;self.heap+=0xa0;assert self.heap<0x72000000
                self.u.mem_write(marker,b'\x00'*0x91);self.w(marker+0x41,-1)
                self.markers[marker]=dict(argument=self.r(sp+4)&255,token=len(self.markers)+1)
                self.ret(4,marker);return
            if address==0x546050 and u.reg_read(UC_X86_REG_ECX)in self.markers:
                self.marker_destroyed.append(self.markers[u.reg_read(UC_X86_REG_ECX)]['token']);self.ret();return
            if address==0x587393 and self.r(sp+4)in self.markers:
                self.ret();return #CRT delete of the owned graphical stand-in only.
        super().hook(u,address,size,unused)

    def snapshot_queued(self):
        group=self.group();task=self.r(group+0x25)if self.r(pointer.GROUPS+12)else 0
        state=self.snapshot_membership();result=dict(age=self.r(group+8),task=None,route=None,
            membership=state,packets=[dict(p)for p in self.commands],calls=list(self.calls),marker_destroyed=list(self.marker_destroyed))
        if not task:return result
        if task not in self.task_tokens:self.task_tokens[task]=len(self.task_tokens)+1
        header=list(struct.unpack('<7I',self.u.mem_read(task,28)))
        result['task']=dict(header=header,token=self.task_tokens[task])
        e=self.r(group+0x2d)
        result['events']=[bytes(self.u.mem_read(self.r(e+28)+32*i,32)).hex()for i in range(self.r(e+12))]if e else[]
        route=self.r(task+0x61)
        if not route:return result
        pv=self.r(route+4);mv=self.r(route+8);points=[];members=[]
        if pv:
            assert self.r(pv+8)==12 and self.r(pv+12)<=128
            for i in range(self.r(pv+12)):
                p=self.r(pv+28)+12*i;marker=self.r(p+8)
                points.append(dict(cell=[self.signed(p),self.signed(p+4)],marker=None if not marker else
                    dict(self.markers[marker],world=[self.signed(marker+0x59),self.signed(marker+0x5d)])))
        if mv:
            assert self.r(mv+8)==17 and self.r(mv+12)<=3
            for i in range(self.r(mv+12)):
                p=self.r(mv+28)+17*i;actor=self.r(p)
                assert self.r(actor+0x4c)==self.r(p+4)
                members.append(dict(id=self.r(p+4),mode=struct.unpack('<b',self.u.mem_read(p+8,1))[0],target=[self.signed(p+9),self.signed(p+13)]))
        result['route']=dict(registered=self.r(route),points=points,members=members)
        return result

    def run(self,op):
        #Each operation is an actual source call or explicitly labeled input memory setup.
        self.commands.clear();self.calls.clear();value=None
        if op[0]=='select':
            for index,identifier in enumerate(op[1:]):
                self.selection_events.clear();self.release(5,identifier,flags=0 if index==0 else 4)
        elif op[0]in('click','shift'):
            _,x,y,counter=op;self.w(pointer.motion.SYSTEM+0xde,counter)
            flags=4 if op[0]=='shift'else 0
            if self.entry=='ui':
                self.observe(7,False,x,y);self.w(pointer.CUR+0xd9,0)
                self.invoke_cursor(0x518070,(0x62,flags))
            else:
                request=pointer.BASE+0x58000;self.u.mem_write(request,struct.pack('<iiB',x,y,0))
                self.invoke_fleet(0x49e230,(20,request,5,0,flags))
        elif op[0]=='work':
            _,pending,counter=op;self.w(pointer.motion.SYSTEM+0xde,counter);self.w(pointer.motion.SYSTEM+0xe2,pending)
            self.invoke_fleet(0x4c4f40,(5,0,self.group()))
        elif op[0]=='age':self.w(self.group()+8,op[1])
        elif op[0]=='pose':
            _,identifier,x,y,state=op;actor=self.actors[identifier]
            self.w(actor+0x5a3,x);self.w(actor+0x5a7,y);self.u.mem_write(actor+0x58c,bytes([state]))
        elif op[0]=='next':
            _,x,y,mode=op;out=pointer.BASE+0x5b000;self.w(out,0xdeadbeef)
            self.invoke_fleet(0x4ce7c0,(self.r(self.r(self.group()+0x25)+0x61),x,y,out,mode))
            value=dict(cell=struct.unpack('<i',struct.pack('<I',self.u.reg_read(UC_X86_REG_EAX)))[0],end=self.r(out))
        elif op[0]=='clear':self.invoke_fleet(0x4a1c60,(5,self.group()))
        elif op[0]=='arrival':
            _,identifier,x,y,counter=op;self.w(pointer.motion.SYSTEM+0xde,counter)
            self.invoke_fleet(0x4a1700,(5,0,self.actors[identifier],y*24+x))
        elif op[0]=='notify':
            _,identifier,counter=op;self.w(pointer.motion.SYSTEM+0xde,counter)
            self.invoke_fleet(0x4a1340,(5,0,self.actors[identifier]))
        else:raise AssertionError(op)
        result=self.snapshot_queued();result['value']=value;return result


def pilot():
    engine=QueuedOracle();rows=[]
    for op in(('select',11,12,13),('click',18,5,0),('age',25),('shift',18,6,25),('shift',16,4,25),('shift',18,6,26),('work',1,27)):
        rows.append(dict(operation=op,state=engine.run(op)))
    return dict(rows=rows,scope=__doc__)


def specifications():
    for count in(1,2,3):
        for members in itertools.permutations(LOCAL,count):
            for start in('normal','queued'):
                ops=[['select',*members]]
                if start=='normal':ops.append(['click',18,5,0])
                ops +=[['age',25],['shift',18,6,25],['shift',16,4,26],['shift',18,6,27],['shift',18,5,28],
                        ['work',100,29],['work',1,30]]
                ops +=[['next',x,y,mode]for x,y in((18,6),(16,4),(18,5),(0,0))for mode in(-2,-1,0,1,2)]
                ops +=[['click',18,5,40],['shift',18,6,41],['clear']]
                yield dict(label=f'{start}-{members}',operations=ops)
    for age in(99,100,101,0xffffffff):
        for pending in(0,1,7,0xffffffff):
            yield dict(label=f'age-{age}-{pending}',operations=[['select',11,12,13],['shift',18,6,0],['shift',16,4,1],
                ['age',age],['work',pending,2],['work',1,3]])
    for members in((11,),(11,12,13)):
        for age in(0,101):
            for aligned in(False,True):
                ops=[['select',*members],['shift',18,6,0],['shift',16,4,1],['shift',18,5,2],['age',age]]
                if aligned:ops.append(['pose',11,18,6,0])
                ops +=[['arrival',11,18,6,25],['work',1,26]]
                yield dict(label=f'arrival-{len(members)}-{age}-{aligned}',operations=ops)
    yield dict(label='arrival-lifo',operations=[['select',11,12,13],['shift',18,6,0],['shift',16,4,1],['shift',18,5,2],
        ['pose',11,18,6,0],['pose',12,16,4,0],['pose',13,18,5,0],['arrival',11,18,6,10],
        ['arrival',12,16,4,11],['arrival',13,18,5,12],['work',1,13]])


def fixture(specs=None,patches=()):
    metadata=normal.source.membership.hover.source_metadata();cases=[]
    for spec in list(specifications())if specs is None else specs:
        ui=QueuedOracle(metadata,'ui',patches);direct=QueuedOracle(metadata,'fleet',patches);rows=[]
        for op in spec['operations']:
            actual=ui.run(op);independent=direct.run(op)
            assert actual==independent,(spec['label'],op,actual,independent)
            rows.append(dict(operation=op,state=actual))
        cases.append(dict(label=spec['label'],rows=rows))
    return dict(schema_version=1,original_exe_sha256=normal.source.pointer.gate.EXPECTED,
        independent_entries=['0x518070','0x49e230'],cases=cases,scope=__doc__)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--pilot',action='store_true');a=p.parse_args()
    data=pilot()if a.pilot else fixture();a.output.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print(dict(pilot=True)if a.pilot else dict(cases=len(data['cases']),states=sum(len(c['rows'])for c in data['cases'])))


if __name__=='__main__':main()
