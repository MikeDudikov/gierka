"""Coupled original membership/task ownership,without actor Work or a world clock.

Actual49ca60/49bd60/49bef0,300/311 construction,100/1 Work and41 receipt run
in ONE source engine. Registry cell/state and phase/counter/pending inputs are
explicit. No Unity input/Shift selection policy,busy20 receipt or rendering.
"""
from pathlib import Path
import argparse,base64,itertools,json,struct,sys
from unicorn.x86_const import UC_X86_REG_EAX
from tools import probe_ship_fleet_normal_task as task

ROOT=task.ROOT;pointer=task.pointer;LOCAL=task.LOCAL


class GroupOracle(task.TaskOracle):
    def __init__(self,metadata):
        super().__init__(metadata)
        self.slot_extents=[];self.membership_packets=[];self.delivered=0

    #Source49c020 packed61-byte group address,not the actor instance ID.
    def group_at(self,index):
        assert 0<=index<self.r(pointer.GROUPS+12)
        return self.r(pointer.GROUPS+28)+61*index

    #Observe source group+8/+25/+2d/+31 and task+24,normalizing only pointers.
    def snapshot_groups(self,result=None):
        groups=[]
        for index in range(self.r(pointer.GROUPS+12)):
            group=self.group_at(index);members=self.r(group+0x31);count=self.r(members+12)
            if len(self.slot_extents)<=index:self.slot_extents.append(0)
            self.slot_extents[index]=max(self.slot_extents[index],count)
            slots=[self.r(self.r(members+28)+4*i)for i in range(self.slot_extents[index])]
            assert all(i<len(LOCAL)for i in slots)
            state={'mode':self.r(group),'serial':self.r(group+12),'age':self.r(group+8),
                   'members':slots[:count],'slots':slots,'task':None,'assignments':[],'events':[]}
            t=self.r(group+0x25)
            if t:
                state['task']=list(struct.unpack('<7I',self.u.mem_read(t,28)))
                a=self.r(t+0x24)
                if a:
                    assert self.r(a+8)==20
                    for n in range(self.r(a+12)):
                        identifier,actor,x,y,reserved=struct.unpack('<IIiiI',self.u.mem_read(self.r(a+28)+20*n,20))
                        assert self.r(actor+0x4c)==identifier and reserved==0
                        state['assignments'].append([identifier,x,y])
                e=self.r(group+0x2d);assert e and self.r(e+8)==32
                state['events']=[bytes(self.u.mem_read(self.r(e+28)+32*n,32)).hex()for n in range(self.r(e+12))]
            groups.append(state)
        membership=self.snapshot_membership()
        return {'result':result,'current_group':self.signed(pointer.FLEET+0xc2+20),
                'groups':groups,'actors':membership['actors'],'consumed':self.delivered,
                'membership_commands':[dict(p)for p in self.membership_packets],
                'commands':[dict(p)for p in self.commands]}

    #Source entry calls only;no fleet behavior is intercepted or substituted.
    def perform_owned(self,op):
        self.commands.clear();result=None
        if op[0]=='C':
            self.w(pointer.motion.SYSTEM+0xde,op[1])
            self.commit(op[2:]);result=self.r(pointer.FLEET+0xc2+20)if len(op)>2 else 0
            #49ca60's return is0 for empty input,even after older groups exist.
            if len(op)==2:result=0
        elif op[0]in('B','N','D'):
            counter=op[-1];self.w(pointer.motion.SYSTEM+0xde,counter)
            if op[0]=='B':
                self.invoke_fleet(0x49bd60,(self.actors[op[2]],op[1]));result=self.u.reg_read(UC_X86_REG_EAX)
            elif op[0]=='N':self.invoke_fleet(0x4a1340,(5,op[1],self.actors[op[2]]))
            else:
                actor=self.actors[op[1]];group=struct.unpack('<h',self.u.mem_read(actor+0x5c,2))[0]
                if group<0:result=0
                else:
                    self.invoke_fleet(0x49bef0,(5,group,self.r(actor+0x60),actor));result=self.u.reg_read(UC_X86_REG_EAX)
        elif op[0]=='R':
            _,group,x,y,counter=op;self.w(pointer.motion.SYSTEM+0xde,counter)
            request=pointer.BASE+0x58000;self.u.mem_write(request,struct.pack('<4i',x,y,1,0))
            self.invoke_fleet(0x4ccc30,(5,group,self.group_at(group),request))
        elif op[0]=='T':
            _,group,pending,counter=op;self.w(pointer.motion.SYSTEM+0xde,counter);self.w(pointer.motion.SYSTEM+0xe2,pending)
            self.invoke_fleet(0x4c4f40,(5,group,self.group_at(group)))
        elif op[0]=='X':self.invoke_fleet(0x4a1c60,(5,self.group_at(op[1])))
        elif op[0]=='P':
            _,identifier,x,y,state=op;actor=self.actors[identifier];self.w(actor+0x5a3,x);self.w(actor+0x5a7,y)
            self.u.mem_write(actor+0x58c,bytes([state]))
        elif op[0]=='M':
            cells=task.source.formation.mission_terrain()if op[1]=='mission'else[-1]*576
            self.u.mem_write(self.r(0x5c93bc),struct.pack('<576h',*cells))
        elif op[0]=='Q':
            packet=self.membership_packets[self.delivered]
            self.consume_packet(packet);self.delivered+=1
        else:raise AssertionError(op)
        self.membership_packets.extend(dict(p)for p in self.commands if p['action']==41)
        return self.snapshot_groups(result)


def specifications():
    orders=[list(p)for n in(1,2,3)for p in itertools.permutations(LOCAL,n)]
    #49ca60 out of an active task:all225 ordered old/new local subset pairs.
    for first in orders:
        for second in orders:
            yield {'label':f'active-commit-{first}-{second}','operations':[
                ['C',0,*first],['R',0,18,5,1],['C',2,*second],['R',1,18,5,3],
                ['T',0,101,4],['T',1,101,5],['T',0,1,6],['T',1,1,7]]}
    for count in(1,2,3):
        for members in itertools.permutations(LOCAL,count):
            for map_name in('mission','blocked'):
                ops=[['C',10,*members],['M',map_name],['R',0,18,5,11]]
                ops +=[['Q']for _ in members]
                ops +=[['T',0,100,12],['T',0,1,13],['T',0,1,14]]
                for n,identifier in enumerate(LOCAL):
                    if identifier in members:ops.append(['D',identifier,20+n])
                    else:ops +=[['B',0,identifier,20+n],['N',0,identifier,20+n]]
                ops +=[['T',0,1,30],['T',0,101,31],['T',0,7,32],['X',0],['T',0,7,33],['R',0,18,5,34]]
                yield {'label':f'owned-{members}-{map_name}','operations':ops}
    for map_name in('mission','blocked'):
        yield {'label':'multi-group-reassignment-'+map_name,'operations':[
            ['C',0,11,12],['C',0,13],['M',map_name],['R',0,18,5,1],['R',1,20,4,2],
            ['Q'],['Q'],['Q'],['B',1,11,10],['N',1,11,10],['P',12,8,9,0],
            ['T',0,101,11],['T',1,101,12],['T',0,1,13],['T',1,1,14],
            ['C',15,13,12,11],['R',2,18,5,16],['T',0,1,17],['T',1,1,18],
            ['Q'],['Q'],['Q'],['Q'],['Q'],['Q'],['Q'],['Q'],
            ['B',0,13,20],['N',0,13,20],['B',0,11,21],['N',0,11,21],
            ['D',11,22],['T',0,7,23],['T',2,7,24],['X',1],['R',1,18,5,25],
            ['B',1,12,26],['N',1,12,26],['T',1,7,27]]}
        yield {'label':'retained-tail-not-current-membership-'+map_name,'operations':[
            ['C',0,11],['M',map_name],['R',0,18,5,1],['B',0,12,2],['N',0,12,2],
            ['B',0,13,3],['N',0,13,3],['D',13,4],['T',0,101,5],['T',0,1,6],
            ['D',12,7],['D',11,8],['T',0,1,9],['Q'],['Q'],['Q'],['Q'],['Q'],['Q']]}
    yield {'label':'same-group-add-is-noop-notify-is-separate','operations':[
        ['C',0,11,12,13],['B',0,12,1],['N',0,12,1],['R',0,18,5,2],['B',0,12,3],
        ['N',0,12,3],['B',0,12,4],['N',0,12,4],['T',0,1,5],['D',12,6],['D',12,7],['T',0,1,8]]}
    yield {'label':'clear-preserves-age-and-retained-slots','operations':[
        ['C',0,11,12,13],['R',0,18,5,1],['T',0,100,2],['D',12,3],['X',0],
        ['T',0,100,4],['N',0,11,5],['R',0,18,5,6],['T',0,1,7],['T',0,1,8]]}
    yield {'label':'unsigned-age-and-request-counter-wrap','operations':[
        ['C',0,11],['R',0,18,5,0xffffffff],['T',0,0xffffffff,0],['N',0,11,1],
        ['T',0,1,1],['T',0,100,2],['T',0,1,3],['T',0,0,4]]}


def fixture():
    metadata=task.source.membership.hover.source_metadata();cases=[]
    for case in specifications():
        oracle=GroupOracle(metadata)
        cases.append({'label':case['label'],'states':[{'operation':op,'after':oracle.perform_owned(op)}for op in case['operations']]})
        if len(cases)%64==0:print('Native coupled group cases: '+str(len(cases)),file=sys.stderr,flush=True)
    cells=task.source.formation.mission_terrain()
    return {'schema_version':1,'original_exe_sha256':pointer.gate.EXPECTED,
            'terrain_base64':base64.b64encode(struct.pack('<576h',*cells)).decode(),'cases':cases,
            'scope':__doc__,'boundaries':['TaskOracle constructor/CRT/render/disabled-audio boundaries retained',
            'Raw slot extent is observation-only high-water count;all recorded slots were written by actual source membership',
            'Cells/states,global terrain and explicit phase order are inputs;no whole-world scheduling proof',
            'All41/20/35 payloads and groups/actors/task/events/assignments compared;20/35 are not delivered to actors']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=fixture()
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,separators=(',',':'))+'\n')
    print({'cases':len(d['cases']),'states':sum(len(c['states'])for c in d['cases'])})


if __name__=='__main__':main()
