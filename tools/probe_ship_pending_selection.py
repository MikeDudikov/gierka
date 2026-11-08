"""Original normal pending-fleet selection transactions for miss000's three local ships."""
from pathlib import Path
import json,struct,argparse
from tools import probe_ship_box_selection as box
from tools import probe_ship_pointer_commands as pointer
from unicorn.x86_const import UC_X86_REG_ESP
ROOT=box.ROOT
LOCAL=(11,12,13)
class PendingOracle(box.BoxOracle):
    def __init__(self):
        self.selection_events=[];super().__init__()
        self.vector(pointer.ACTORS,4,3,pointer.ACTOR_DATA)
        for i,identifier in enumerate(LOCAL):self.w(pointer.ACTOR_DATA+4*i,self.actors[identifier])
        self.reset(0,False)
    def hook(self,u,a,size,unused):
        if self.pointer_ready and a==0x4dc630:
            message=self.r(u.reg_read(UC_X86_REG_ESP)+4)
            if self.r(message+0x10)==0xc453:
                from unicorn.x86_const import UC_X86_REG_ECX
                actor=u.reg_read(UC_X86_REG_ECX)
                self.selection_events.append([self.r(actor+0x4c),self.r(message+0x14)])
        super().hook(u,a,size,unused)
    def reset(self,mask,pending=None):
        members=[i for n,i in enumerate(LOCAL)if mask&(1<<n)]
        self.w(pointer.SELECTED+12,len(members))
        for n,i in enumerate(members):self.w(pointer.SELECTED_DATA+4*n,self.actors[i])
        self.w(pointer.FLEET+0xc2+20,-1);self.u.mem_write(pointer.FLEET+0x20,bytes([bool(members)if pending is None else pending]));self.w(pointer.motion.APP+0x3221,bool(members))
        for i,actor in self.actors.items():
            self.u.mem_write(actor+0x252,bytes([int(i in members)]));self.u.mem_write(actor+0x57,b'\x01');self.w(actor+0x5c,-1)
        self.commands.clear();self.selection_events.clear()
    def snapshot_pending(self):
        count=self.r(pointer.SELECTED+12);data=self.r(pointer.SELECTED+28)
        return {'members':[self.r(self.r(data+4*i)+0x4c)for i in range(count)],'selected':bool(self.r(pointer.motion.APP+0x3221)),'pending':bool(self.b(pointer.FLEET+0x20)),'current_group':self.signed(pointer.FLEET+0xc2+20),'visuals':[self.b(self.actors[i]+0x252)for i in LOCAL],'events':self.selection_events.copy(),'cursor':struct.unpack('<H',self.u.mem_read(pointer.CUR+0x101,2))[0],'mask':struct.unpack('<H',self.u.mem_read(pointer.CUR+0xe2,2))[0],'bit':struct.unpack('<H',self.u.mem_read(pointer.CUR+0xe4,2))[0],'blocked':bool(self.r(pointer.CUR+0xe6)),'commands':[dict(c)for c in self.commands]}
    def release(self,kind,target,message=0x62,flags=0,blocked=False,enabled=True):
        self.observe(kind,False,18,5,blocked=blocked,enabled=enabled)
        self.w(pointer.CUR+0xd9,self.actors[target]if target is not None else 0)
        self.invoke_cursor(0x518070,(message,flags));return self.snapshot_pending()
    def rectangle(self,kind,rect,flags):
        self.observe(kind,False,18,5);self.invoke_cursor(0x517b90,(flags,*rect));return self.snapshot_pending()

def fixture():
    oracle=PendingOracle();cases=[]
    initial=[(mask,bool(mask))for mask in range(8)]+[(0,True)]
    rects=([0,0,2,2],[15,1,3,3],[18,5,1,1],[20,5,3,3],[15,1,9,7])
    for mask,pending in initial:
        for target in LOCAL:
            for kind in (0,5,6):
                for flags in (0,4,8,12):
                    for blocked,enabled in ((False,True),(True,True),(False,False)):
                        oracle.reset(mask,pending);result=oracle.release(kind,target,flags=flags,blocked=blocked,enabled=enabled)
                        cases.append({'initial_mask':mask,'initial_pending':pending,'operation':'release','kind':kind,'target':target,'message':98,'flags':flags,'blocked':blocked,'enabled':enabled,'after':result})
        for kind in (0,7):
            oracle.reset(mask,pending);result=oracle.release(kind,None,message=100)
            cases.append({'initial_mask':mask,'initial_pending':pending,'operation':'release','kind':kind,'target':None,'message':100,'flags':0,'blocked':False,'enabled':True,'after':result})
        for kind in (0,5,6,7):
            for flags in (0,4,8,12):
                for rect in rects:
                    oracle.reset(mask,pending);members=oracle.query(rect)['members'];oracle.reset(mask,pending)
                    result=oracle.rectangle(kind,rect,flags)
                    cases.append({'initial_mask':mask,'initial_pending':pending,'operation':'box','kind':kind,'rect':rect,'candidates':members,'flags':flags,'after':result})
    assert all(not c['after']['commands']and c['after']['current_group']==-1 for c in cases)
    return {'schema_version':1,'original_exe_sha256':box.pick.gate.EXPECTED,'local_ids':list(LOCAL),'cases':cases,'scope':'Normal local ships0b/0c/0d;pending or empty selection only;no committed group/movement/contextual right cycling/combat','boundaries':'Existing BoxOracle heap/setjmp/disabled audio/renderer/empty UI boundaries;actual cursor/fleet/actor selection and original vectors execute'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();data=fixture();a.output.write_text(json.dumps(data,indent=2)+'\n');print({'cases':len(data['cases'])})
if __name__=='__main__':main()
