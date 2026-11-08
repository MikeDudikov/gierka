"""Original100/2 in40ms clock/mail/registry with real movement-generated310.

Extends the existing WorldOracle. ShipLife remains its documented original
Promote/Work trampoline;graphics marker construction/CRT remain boundaries.
Actual4a1700 now executes. Per-actor signed wave[-1] words are explicit inputs,
not a default Windows allocator assumption. No C#or UI integration claim.
"""
from pathlib import Path
import argparse,itertools,json,struct
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EBP,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_ESP
from tools import probe_ship_world_step as world
from tools import probe_ship_fleet_queued as fleet

ROOT=world.ROOT


class QueuedWorldOracle(world.WorldOracle):
    def __init__(self,order,warm,prefixes,patches=()):
        assert set(prefixes)==set(world.live.LOCAL)
        assert all(-32768<=v<=32767 for v in prefixes.values())
        self.prefixes=dict(prefixes);self.markers={};self.arrivals=[];self.wave_reads=[]
        self.group_visits=[];self.queued_ready=False;self.allocations={}
        super().__init__(tuple(order),warm)
        # Original MoveShip calls global fleet5c7504. Previously4a1700 was a
        # boundary,so it was not needed. This is explicit world startup wiring.
        self.w(0x5c7504,world.FLEET);self.queued_ready=True
        for address,before,after in patches:
            assert bytes(self.u.mem_read(address,len(before)))==before
            assert len(before)==len(after);self.u.mem_write(address,after)

    def hook(self,u,address,size,unused):
        if self.queued_ready:
            sp=u.reg_read(UC_X86_REG_ESP);this=u.reg_read(UC_X86_REG_ECX)
            if address==0x4ced80:
                marker=self.heap;self.heap+=0xa0;assert self.heap<0x72000000
                u.mem_write(marker,bytes(0x91));self.w(marker+0x41,-1)
                self.markers[marker]=True;self.ret(4,marker);return
            if address==0x546050 and this in self.markers:self.ret();return
            if address==0x587393 and self.r(sp+4)in self.markers:self.ret();return
            if address==0x4a1700:
                actor=self.r(sp+12);cell=self.r(sp+16)
                self.arrivals.append(dict(counter=self.r(world.original.SYSTEM+0xde),
                    id=self.r(actor+0x4c),member_index=self.r(actor+0x60),
                    group=self.r(sp+8),cell=cell,actual_cell=self.r(actor+0x5a7)*24+self.r(actor+0x5a3),
                    return_address=hex(self.r(sp)),trace=list(self.trace)))
                assert this==world.FLEET
                return #Execute source310 construction;do not call the inherited ret boundary.
            if address==0x557700:self.allocations[self.heap]=self.r(sp+4)
            if address==0x4cf550:
                group=self.r(sp+12)
                self.group_visits.append(dict(counter=self.r(world.original.SYSTEM+0xde),
                    age=self.r(group+8),event_count=self.r(self.r(group+0x2d)+12),trace=list(self.trace)))
            if address==0x4cebc7:
                base=u.reg_read(UC_X86_REG_EAX);index=u.reg_read(UC_X86_REG_EDX)
                assert index==0xffffffff and self.allocations[base]==1152
                actor=self.r(u.reg_read(UC_X86_REG_EBP)+8);identifier=self.r(actor+0x4c)
                word=self.prefixes[identifier];before=struct.unpack('<h',u.mem_read(base-2,2))[0]
                u.mem_write(base-2,struct.pack('<h',word))
                candidate=struct.unpack('<h',struct.pack('<H',u.reg_read(UC_X86_REG_ESI)&65535))[0]
                self.wave_reads.append(dict(counter=self.r(world.original.SYSTEM+0xde),id=identifier,index=-1,word=word,
                    allocation_bytes=1152,offset_bytes=-2,adjacent_before=before,candidate=candidate))
            if address==0x4cebce:self.wave_reads[-1]['result']=u.reg_read(UC_X86_REG_EBX)
        super().hook(u,address,size,unused)

    # Matches49ca60 then4cf2c0(single point,non-patrol);no substitute dispatch.
    def request_queued(self,members,points):
        self.w(world.SELECTED+12,len(members))
        for i,identifier in enumerate(members):self.w(world.SELECTED_DATA+4*i,world.live.motion.ACTORS[identifier])
        self.call_this(0x49ca60,world.FLEET,(5,))
        for point in points:self.append_point(*point)

    # Original4cf2c0 six-DWORD request;point vector input belongs to the caller.
    def append_point(self,x,y):
        group=self.r(world.GROUPS+28);request=world.W+0x51000;point=request+0x40
        self.u.mem_write(point,struct.pack('<ii',x,y))
        self.u.mem_write(request,struct.pack('<6I',x,y,1,0,1,point))
        self.call_this(0x4cf2c0,world.FLEET,(5,0,group,request,0,0))

    # Source logical fields only;opaque task/marker pointer identity is excluded.
    def group_state(self):
        group=self.r(world.GROUPS+28);task=self.r(group+0x25);slots=self.r(group+0x31);events=self.r(group+0x2d)
        if self.r(task+4)==1:return super().group_state()
        route=self.r(task+0x61);pv=self.r(route+4);mv=self.r(route+8)
        return dict(age=self.r(group+8),task=list(struct.unpack('<7I',self.u.mem_read(task,28))),
            members=[self.r(self.r(slots+28)+4*i)for i in range(self.r(slots+12))],
            events=[bytes(self.u.mem_read(self.r(events+28)+32*i,32)).hex()for i in range(self.r(events+12))]if events else[],
            route=dict(registered=self.r(route),
                points=[[self.signed(self.r(pv+28)+12*i),self.signed(self.r(pv+28)+12*i+4)]for i in range(self.r(pv+12))],
                members=[dict(id=self.r(self.r(mv+28)+17*i+4),mode=struct.unpack('<b',self.u.mem_read(self.r(mv+28)+17*i+8,1))[0],
                    target=[self.signed(self.r(mv+28)+17*i+9),self.signed(self.r(mv+28)+17*i+13)])for i in range(self.r(mv+12))]))

    def frame(self,captured):
        self.arrivals=[];self.wave_reads=[];self.group_visits=[]
        result=super().frame(captured)
        result.update(arrivals=list(self.arrivals),wave_reads=list(self.wave_reads),group_visits=list(self.group_visits))
        return result


def ui_handoff(metadata,members,points):
    """Independent actual518070/49e230 path,not a synthetic packet builder."""
    n=fleet.QueuedOracle(metadata,'ui');n.run(('select',*members));packets=[]
    for x,y in points:packets.extend(n.run(('shift',x,y,0))['packets'])
    state=n.snapshot_queued()
    return dict(packets=packets,header=state['task']['header'],
        route=dict(registered=state['route']['registered'],points=[p['cell']for p in state['route']['points']],members=state['route']['members']))


def specifications():
    route=((18,6),(16,4),(18,5));local=world.live.LOCAL
    for order in itertools.permutations((-1,*local)):
        yield dict(label='registry-'+','.join(map(str,order)),order=order,warm=2,members=local,points=route,
            prefixes=[117]*3,age_input=None,terrain='mission',times=[0,39]+[40*i for i in range(1,161)])
    for order in((-1,*local),(*local,-1)):
        position=order.index(-1)
        for warm in(0,1):
            yield dict(label=f'mail-{position}-{warm}',order=order,warm=warm,members=local,points=route,
                prefixes=[117]*3,age_input=None,terrain='mission',times=[40*i for i in range(1,161)])
        yield dict(label=f'single-{position}',order=order,warm=2,members=(11,),points=route,
            prefixes=[117]*3,age_input=None,terrain='mission',times=[40*i for i in range(1,321)])
        for prefix in(0,117,32767,-32768):
            yield dict(label=f'periodic-{position}-{prefix}',order=order,warm=0,members=local,points=((16,2),(18,6),(16,4)),
                prefixes=[prefix]*3,age_input=101,terrain='mission',times=[40*i for i in range(1,31)])
            yield dict(label=f'islands-{position}-{prefix}',order=order,warm=0,members=local,points=((16,2),(18,6),(16,4)),
                prefixes=[prefix]*3,age_input=101,terrain='islands',times=[40])


def fixture(specs=None,patches=()):
    cases=[];metadata=fleet.normal.source.membership.hover.source_metadata();handoffs={}
    for spec in list(specifications())if specs is None else specs:
        n=QueuedWorldOracle(spec['order'],spec['warm'],dict(zip(world.live.LOCAL,spec['prefixes'])),patches)
        initial=[n.live_snapshot(i)for i in world.live.LOCAL]
        n.request_queued(spec['members'],spec['points']);queued=n.queued()
        key=repr((tuple(spec['members']),tuple(tuple(p)for p in spec['points'])))
        if key not in handoffs:handoffs[key]=ui_handoff(metadata,spec['members'],spec['points'])
        handoff=handoffs[key];state=n.group_state()
        assert handoff['packets']==[dict(actor=p['actor'],action=p['action'],payload_hex=p['payload_hex'])for p in queued]
        assert state['task']==handoff['header']and state['route']==handoff['route']
        if spec['age_input']is not None:n.w(n.r(world.GROUPS+28)+8,spec['age_input'])
        if spec['terrain']=='islands':
            terrain=[0 if (x,y)in((16,2),(21,5),(19,4),(18,6),(16,4))else-1 for y in range(24)for x in range(24)]
            n.u.mem_write(n.r(0x5c93bc),struct.pack('<576h',*terrain))
        rows=[n.frame(t)for t in spec['times']]
        cases.append(dict(spec,initial=initial,initial_packets=queued,ui_handoff=key,rows=rows))
    return dict(schema_version=1,original_exe_sha256=world.original.EXPECTED,scope=__doc__,cases=cases,
        ui_handoffs=handoffs,seed_payloads={str(i):n.records[i].hex()for i in world.live.LOCAL},
        terrain=fleet.normal.source.formation.mission_terrain(),
        ship_life_boundary='owned trampoline calls original4ab720/4ab930;not full4dec40',
        arrival_entry='4a1700',global_fleet_input='5c7504',source_crt_executed=False)


def pilot():
    cases=[]
    for order in((-1,11,12,13),(11,12,13,-1)):
        n=QueuedWorldOracle(order,2,{11:117,12:117,13:117})
        n.request_queued((11,12,13),((18,6),(16,4),(18,5)))
        packets=n.queued();rows=[n.frame(40*i)for i in range(1,321)]
        cases.append(dict(order=order,initial_packets=packets,rows=rows))
    return dict(schema_version=1,original_exe_sha256=world.original.EXPECTED,scope=__doc__,cases=cases)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--pilot',action='store_true');a=p.parse_args()
    result=pilot()if a.pilot else fixture();a.output.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(dict(cases=len(result['cases']),frames=sum(len(c['rows'])for c in result['cases']),
        arrivals=sum(len(r['arrivals'])for c in result['cases']for r in c['rows']),
        packets=sum(len(r['emitted'])for c in result['cases']for r in c['rows'])))


if __name__=='__main__':main()
