"""Actual40ms clock branch,mail and registry dispatch with fleet and3real bodies.

Ship::Life is a documented boundary:its normal Promote/ProcShipsWork subset
runs original4ab720/4ab930 through an owned caller trampoline. Other Life,
visibility,audio/render construction and complete app initialization excluded.
"""
from pathlib import Path
import argparse,itertools,json,struct
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EBP,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDI,UC_X86_REG_EIP,UC_X86_REG_ESI,UC_X86_REG_ESP
from tools import probe_ship_live_fleet as live

ROOT=live.ROOT;original=live.original;W=0x73000000
FLEET=W+0x1000;GROUPS=W+0x2000;GROUP_DATA=W+0x3000;SELECTED=W+0x5000;SELECTED_DATA=W+0x6000
REGISTRY=W+0x7000;REGISTRY_DATA=W+0x8000;OBJECTS=W+0x9000;OBJECT_DATA=W+0xa000
MAIL=W+0x10000;GAME=W+0x30000;Q1=W+0x40000;Q2=W+0x41000;TRAMP=W+0x50000


class WorldOracle(live.LiveFleetOracle):
    def __init__(self,order=(-1,11,12,13),warm=2):
        self.world_ready=False;self.in_frame=False;self.trace=[];self.emitted=[];self.received=[];self.registration=order;self.frame_publications=[]
        super().__init__(0);self.u.mem_map(W,0x100000)
        self.u.mem_map(0,0x1000) #Same isolated SEH/TIB boundary as PointerOracle.
        self.call_this(0x49ab10,FLEET)
        for a,v in((FLEET+0xc,original.SYSTEM),(FLEET+0x10,original.APP),(FLEET+0x22+20,GROUPS),
                    (FLEET+0x72+20,SELECTED),(FLEET+0xc2+20,-1),(original.PLAYERS+5*0xba0+3000,REGISTRY),
                    (original.SYSTEM,0x59b828),(original.SYSTEM+0x18,original.APP),(original.APP+0x15b5,GAME),
                    (original.APP+0xd7c,1),(original.APP+0x3219,FLEET),(original.SYSTEM+4,Q1),(original.SYSTEM+8,Q2),
                    (original.SYSTEM+0x10,OBJECTS),(original.SYSTEM+0x36,MAIL),(original.SYSTEM+0x3a,0x10000),
                    (original.SYSTEM+0xde,0),(original.SYSTEM+0xe2,0),(original.SYSTEM+0xe6,0),(0x5ca556,5),(0x5c74a0,0)):
            self.w(a,v)
        self.u.mem_write(FLEET+0x21,b'\x05');self.u.mem_write(original.APP+0x3212,b'\x01\x01')
        self.u.mem_write(original.SYSTEM+0x3e,bytes([warm]))
        self.vector(GROUPS,61,0,GROUP_DATA);self.vector(SELECTED,4,0,SELECTED_DATA)
        self.vector(REGISTRY,4,3,REGISTRY_DATA);self.vector(OBJECTS,8,len(order),OBJECT_DATA)
        self.vector(Q1,32,0,Q1+0x100);self.vector(Q2,32,0,Q2+0x100)
        for i,identifier in enumerate(live.LOCAL):
            actor=live.motion.ACTORS[identifier];self.w(REGISTRY_DATA+4*i,actor);self.w(actor+0x58,i)
            self.w(actor+0xc,original.SYSTEM);self.u.mem_write(actor+0x5c,struct.pack('<hh',-1,-1))
        for i,identifier in enumerate(order):
            self.w(OBJECT_DATA+8*i,0x100 if identifier==-1 else identifier)
            self.w(OBJECT_DATA+8*i+4,FLEET if identifier==-1 else live.motion.ACTORS[identifier])
        code=bytearray(b'\x56\x8b\xf1')
        for target in(0x4ab720,0x4ab930):
            code+=b'\x8b\xce\xe8'+struct.pack('<i',target-(TRAMP+len(code)+7))
        code+=b'\x5e\xc3';self.u.mem_write(TRAMP,bytes(code));self.tramp_end=TRAMP+len(code)-2
        self.mutations={i:[]for i in live.LOCAL};self.world_ready=True

    #Source registry/vector inputs;not replacements for any tick/queue procedure.
    def vector(self,p,stride,count,data):
        for off,value in((8,stride),(12,count),(16,64),(20,64),(28,data)):self.w(p+off,value)

    def call_this(self,address,this,args=()):
        top=original.S.STACK+original.S.STACK_SIZE-0x1000
        for i,v in enumerate((original.S.END,*args)):self.w(top+4*i,v)
        self.u.reg_write(UC_X86_REG_ESP,top);self.u.reg_write(UC_X86_REG_ECX,this)
        try:self.u.emu_start(address,original.S.END,count=3000000)
        except Exception as e:raise AssertionError(f'{e};EIP={self.u.reg_read(UC_X86_REG_EIP):x};trace={self.trace[-8:]}')from e
        assert self.u.reg_read(UC_X86_REG_EIP)==original.S.END
        return self.u.reg_read(UC_X86_REG_EAX)

    def hook(self,u,a,size,unused):
        if self.world_ready:
            sp=u.reg_read(UC_X86_REG_ESP);this=u.reg_read(UC_X86_REG_ECX)
            if a in(0x521500,0x522850,0x542320):self.trace.append(hex(a))
            if a==0x521500:
                self.publications_by_id={i:[]for i in live.LOCAL};self.tail_by_id={i:False for i in live.LOCAL};self.mutations={i:[]for i in live.LOCAL}
            if a==0x520c50:
                action=self.r(sp+12)&255;assert action in(20,35,41)
                self.emitted.append({'actor':self.r(sp+4),'action':action,'counter':self.r(original.SYSTEM+0xde),
                    'payload_hex':bytes(u.mem_read(self.r(sp+16),{20:9,35:22,41:6}[action])).hex()})
            if a==0x49ab30 and self.in_frame:
                self.trace.append('fleet:'+str(self.r(self.r(sp+4)+16)))
            if a==0x4dc630 and this in self.pointer_ids and self.pointer_ids[this]in live.LOCAL:
                self.current_id=self.pointer_ids[this]
                message=self.r(sp+4)
                if self.r(message+16)==0x280f:
                    packet=self.r(message+20);action=self.b(packet+12)
                    self.received.append({'actor':self.current_id,'action':action,'counter':self.r(original.SYSTEM+0xde),
                        'queued_at':self.r(packet+4),
                        'payload_hex':bytes(u.mem_read(self.r(packet+13),{20:9,35:22,41:6}[action])).hex()})
            if a==0x4dec40:
                self.current_id=self.pointer_ids[this];self.tick=self.r(original.SYSTEM+0xde);self.grid_writes.clear()
                self.trace.append('ship:'+str(self.current_id));u.reg_write(UC_X86_REG_EIP,TRAMP);return
            if a==self.tramp_end:self.mutations[self.current_id]=list(self.grid_writes)
            if a==0x50d5f0:
                self.frame_publications.append([self.current_id,self.r(sp+8),self.r(sp+12),self.r(sp+16),self.depth_by_id[self.current_id]])
            if a==0x50d400:self.ret(4);return
            if self.in_frame and a==0x5209e2:u.emu_stop();return
        super().hook(u,a,size,unused)

    def request(self,members=(11,12,13),goal=(18,5)):
        self.w(SELECTED+12,len(members))
        for i,identifier in enumerate(members):self.w(SELECTED_DATA+4*i,live.motion.ACTORS[identifier])
        self.call_this(0x49ca60,FLEET,(5,))
        group=self.r(GROUPS+28);request=W+0x51000;self.u.mem_write(request,struct.pack('<4i',*goal,1,0))
        self.call_this(0x4ccc30,FLEET,(5,0,group,request))

    def queued(self):
        rows=[];p=self.r(original.SYSTEM+0x2e)
        while p:
            action=self.b(p+12);rows.append({'actor':self.r(p+8),'action':action,'counter':self.r(p+4),
                'payload_hex':bytes(self.u.mem_read(self.r(p+13),{20:9,35:22,41:6}[action])).hex()});p=self.r(p)
        return rows

    #Actual0x83 fleet message:already-member49bd60 no-op,then independent300.
    def notify(self,identifier=11):
        msg=W+0x52000;self.u.mem_write(msg,bytes(32));self.w(msg+16,0x83)
        self.w(msg+20,live.motion.ACTORS[identifier]);self.w(msg+24,0);self.w(msg+28,5)
        self.call_this(0x49ab30,FLEET,(msg,))

    def group_state(self):
        group=self.r(GROUPS+28);t=self.r(group+0x25);v=self.r(group+0x31);a=self.r(t+0x24);e=self.r(group+0x2d)
        return {'age':self.r(group+8),'task':list(struct.unpack('<7I',self.u.mem_read(t,28))),
            'members':[self.r(self.r(v+28)+4*i)for i in range(self.r(v+12))],
            'assignments':[[self.r(self.r(a+28)+20*i),self.signed(self.r(a+28)+20*i+8),self.signed(self.r(a+28)+20*i+12)]for i in range(self.r(a+12))]if a else[],
            'events':[bytes(self.u.mem_read(self.r(e+28)+32*i,32)).hex()for i in range(self.r(e+12))]}

    def frame(self,captured):
        self.trace.clear();self.received.clear();self.emitted.clear();self.frame_publications=[];self.in_frame=True
        top=original.S.STACK+original.S.STACK_SIZE-0x1000
        self.w(top-0x20,captured);self.u.reg_write(UC_X86_REG_EBP,top);self.u.reg_write(UC_X86_REG_ESP,top-0x100)
        self.u.reg_write(UC_X86_REG_ESI,original.SYSTEM);self.u.reg_write(UC_X86_REG_EBX,original.APP)
        self.u.reg_write(UC_X86_REG_EDI,0)
        try:self.u.emu_start(0x520352,0x5209e2,count=5000000)
        except Exception as e:raise AssertionError(f'{e};EIP={self.u.reg_read(UC_X86_REG_EIP):x};trace={self.trace[-12:]}')from e
        assert self.u.reg_read(UC_X86_REG_EIP)==0x5209e2;self.in_frame=False
        actors=[]
        for i in live.LOCAL:
            self.grid_writes=self.mutations[i];actors.append(self.live_snapshot(i))
        return {'captured':captured,'counter':self.r(original.SYSTEM+0xde),'phase':self.signed(original.SYSTEM+0xe6),
                'pending':self.r(original.SYSTEM+0xe2),'mail_gate':self.b(original.SYSTEM+0x3e),
                'trace':list(self.trace),'received':list(self.received),'emitted':list(self.emitted),'outgoing':self.queued(),'actors':actors,
                'group':self.group_state(),'publications':self.frame_publications}


def specifications():
    for order in itertools.permutations((-1,11,12,13)):
        yield {'label':'registered-'+','.join(map(str,order)),'order':order,'warm':2,'members':live.LOCAL,
               'times':[0,39]+[40*i for i in range(1,37)],'notify_at':36}
    for warm in(0,1,2):
        yield {'label':'mail-gate-'+str(warm),'order':(-1,11,12,13),'warm':warm,'members':live.LOCAL,
               'times':[0,39,40,41,80,120,121,160,200,240,280,320]}
    for order in((-1,11,12,13),(11,12,13,-1)):
        for warm in(0,2):
            yield {'label':'deferred-group-command-'+str(order[0])+'-'+str(warm),'order':order,'warm':warm,
                   'members':(11,),'times':[i*40 for i in range(1,213)],'notify_at':201}


def fixture():
    cases=[]
    for spec in specifications():
        n=WorldOracle(spec['order'],spec['warm']);n.request(spec['members']);rows=[]
        for t in spec['times']:
            notified=t==spec.get('notify_at',-1)*40
            if notified:n.notify()
            rows.append(dict(n.frame(t),notified=notified))
        assert sum(len(r['received'])for r in rows)>=2*len(spec['members'])
        if spec['label'].startswith('deferred'):
            emission=next(r for r in rows if r['counter']==201);delivery=next(r for r in rows if r['counter']==202)
            assert len(emission['emitted'])==1 and not emission['received']and len(emission['outgoing'])==1
            assert delivery['received'][0]['queued_at']==201 and delivery['actors'][0]['active']&0x80
        cases.append(dict(spec,rows=rows))
    return {'schema_version':1,'original_exe_sha256':original.EXPECTED,'cases':cases,
        'seed_payloads':{str(i):n.records[i].hex()for i in live.LOCAL},
        'terrain':list(live.motion.original.struct.unpack('<576h',bytes(n.u.mem_read(n.r(0x5c93bc),1152)))),'scope':__doc__}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    d=fixture();a.output.write_text(json.dumps(d,separators=(',',':'))+'\n');print({'cases':len(d['cases']),'frames':sum(len(c['rows'])for c in d['cases'])})


if __name__=='__main__':main()
