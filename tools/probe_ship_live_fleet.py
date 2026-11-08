"""Original20 receipt -> idle promotion -> live planning/work/motion for3actors."""
from pathlib import Path
import argparse
import json
import struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_EAX

from tools import probe_ship_prepared_fleet_motion as motion

ROOT = motion.ROOT
original = motion.original
LOCAL = motion.LOCAL


def planning_fixture():
    """Controlled live-planner inputs, distinct from the coupled work traces."""
    cases=[]
    inputs=[]
    for group in(-1,0,1):
        for state in range(7):
            for retry in(0,51,79):
                for cached in(False,True):
                    inputs.append({'peer':13,'group':group,'state':state,'class':207,'retry':retry,
                                   'cache':[115]if cached else[]})
    inputs +=[{'peer':13,'group':-1,'state':0,'class':207,'retry':0,'cache':[64]},
              {'peer':13,'group':-1,'state':0,'class':207,'retry':0,'cache':[0]},
              {'peer':12,'group':-1,'state':4,'class':200,'retry':0,'cache':[141]},
              {'peer':13,'group':-1,'state':4,'class':400,'retry':0,'cache':[115]}]
    for case in inputs:
        o=LiveFleetOracle(0);o.current_id=11;actor=motion.ACTORS[11];peer=motion.ACTORS[case['peer']]
        o.u.mem_write(actor+0x5e,struct.pack('<h',0))
        o.u.mem_write(peer+0x5e,struct.pack('<h',case['group']))
        o.u.mem_write(peer+0x58c,bytes([case['state']]))
        o.w(peer+0x50,case['class']);o.w(actor+0x18,0xffffffff)
        for cell in case['cache']:o.call_actor(0x4a7230,(cell,))
        count_pointer=motion.BASE+0x1f000;reached_pointer=count_pointer+4
        o.w(count_pointer,0);o.w(reached_pointer,0);paths=[]
        def capture(engine,address,size,unused):
            if address in(0x55c9a0,0x55b9e0):
                sp=engine.reg_read(UC_X86_REG_ESP);pointer=o.r(sp+4)
                paths.append(bytes(engine.mem_read(pointer,1152)).hex())
        o.u.hook_add(UC_HOOK_CODE,capture,begin=0x55b9e0,end=0x55c9a0)
        nearest=case['retry']!=0
        args=(actor,16,2,20,4,0,reached_pointer,0,count_pointer,case['retry'],1)if nearest else(actor,16,2,20,4,count_pointer,0)
        pointer=o.call_actor(0x4a51b0 if nearest else 0x4a5740,args)
        count=o.r(count_pointer);assert count<=577 and bool(pointer)==bool(count)
        cache=o.r(actor+0x5cd)
        cached=[o.r(o.r(cache+28)+4*i)for i in range(o.r(cache+12))]if cache else[]
        working=o.r(0x5c93c0)
        cases.append(dict(case,path_hex=bytes(o.u.mem_read(pointer,count*5)).hex()if count else'',
                          planning_hex=paths[0]if paths else bytes(o.u.mem_read(working,1152)).hex(),
                          working_hex=bytes(o.u.mem_read(working,1152)).hex(),cache_after=cached,
                          rng=o.r(actor+0x18),count=count,nearest=int(nearest),
                          reached=int(bool(o.r(reached_pointer)))if nearest else int(bool(count))))
    return cases


class LiveFleetOracle(motion.FleetOracle):
    def __init__(self, seed=0):
        super().__init__([[], [], []], seed)
        # The five controlled stationary foreign peers are explicitly ungrouped.
        # Their minimal WorkOracle records otherwise contain zero-filled groups.
        for pointer,identifier in self.pointer_ids.items():
            self.u.mem_write(pointer+0x5c,struct.pack('<hh',7,-1))

    def call_actor(self,address,arguments=()):
        # ProcShipsWork has source early-return branches that leave its custom
        # global error-chain head at the source stack frame. Keep those actual
        # writes,as the established WorkOracle does;do not repair source state.
        top=original.S.STACK+original.S.STACK_SIZE-0x1000
        for i,value in enumerate((original.S.END,*arguments)):self.w(top+4*i,value)
        self.u.reg_write(UC_X86_REG_ESP,top);self.u.reg_write(UC_X86_REG_ECX,motion.ACTORS[self.current_id])
        self.u.emu_start(address,original.S.END,count=500000)
        assert self.u.reg_read(UC_X86_REG_EIP)==original.S.END
        return self.u.reg_read(UC_X86_REG_EAX)

    def receive(self, identifier, x, y, argument=0, action=20):
        self.current_id=identifier
        self.publications_by_id[identifier]=[]
        self.tail_by_id[identifier]=False
        self.grid_writes.clear()
        self.w(original.MESSAGE+16,0x280f)
        self.w(original.MESSAGE+20,original.ACTION)
        self.u.mem_write(original.ACTION+12,bytes([action]))
        self.w(original.ACTION+13,original.DATA)
        payload=struct.pack('<iiB',x,y,argument) if action==20 else struct.pack('<BiB',1,x,0)
        self.u.mem_write(original.DATA,payload)
        self.call_actor(0x4dc630,(original.MESSAGE,))
        return self.live_snapshot(identifier)

    def live_snapshot(self, identifier):
        result=self.snapshot(identifier)
        actor=motion.ACTORS[identifier]
        count=self.r(actor+0x5ba);pointer=self.r(actor+0x5c2)
        cache=self.r(actor+0x5cd)
        cached=[self.r(self.r(cache+28)+4*i)for i in range(self.r(cache+12))]if cache else[]
        result.update(pending=self.r(actor+0x7d6),active=self.r(actor+0x25d),deferred=self.r(actor+0x265),
                      stop=self.r(actor+0x818),ready=self.r(actor+0x7da),caps=self.r(actor+0x261),
                      requested=[self.signed(actor+0x85c),self.signed(actor+0x860)],
                      target=[self.signed(actor+0x54e),self.signed(actor+0x552)],first=self.b(actor+0x593),
                      last_plan=self.r(actor+0x57b),retry_interval=self.r(actor+0x57f),radius=self.r(actor+0x5c9),
                      retry_snapshot=self.r(actor+0x562),target_snapshot=[self.signed(actor+0x56b),self.signed(actor+0x56f)],
                      cell_snapshot=[self.signed(actor+0x573),self.signed(actor+0x577)],
                      route_hex=bytes(self.u.mem_read(pointer,count*5)).hex()if count else'',cache=cached,
                      pending_record=bytes(self.u.mem_read(actor+0x858,26)).hex(),
                      simulation_group=struct.unpack('<h',self.u.mem_read(actor+0x5e,2))[0],
                      grid=[[row['cell_index'],self.pointer_ids.get(int(row['after'],16),0)]for row in self.grid_writes],
                      claims=[[i,self.pointer_ids[self.r(original.GRID+8+i*24+4)]]for i in range(576)if self.r(original.GRID+8+i*24+4)])
        return result

    def tick_actor(self,identifier,counter,pending):
        self.current_id=identifier;self.tick=counter
        self.w(original.SYSTEM+0xde,counter);self.w(original.APP+0xe2,pending)
        self.publications_by_id[identifier]=[];self.tail_by_id[identifier]=False;self.grid_writes.clear()
        self.call_actor(0x4ab720)
        self.call_actor(0x4ab930)
        return self.live_snapshot(identifier)


def fixture():
    specifications=[]
    goals=([18,5],[20,6],[18,4])
    for pending in(1,2,3,7):
        for order in(LOCAL,LOCAL[::-1]):
            specifications.append({'label':'normal-'+str(pending)+'-'+str(order[0]),'goals':goals,'sequence':[pending],'order':order,'group_at':0,'ticks':250,'seed':0})
    specifications +=[
        {'label':'delayed-membership','goals':goals,'sequence':[1],'order':LOCAL,'group_at':12,'ticks':300,'seed':7},
        {'label':'ungrouped-mixed','goals':goals,'sequence':[1,2,3,7],'order':LOCAL[::-1],'group_at':-1,'ticks':250,'seed':0xffffffff},
        {'label':'ungrouped-blocked-revalidation','goals':([16,1],[20,6],[18,4]),'sequence':[1],'order':LOCAL,'group_at':-1,'ticks':100,'seed':0},
        {'label':'own-cell','goals':([16,2],[21,5],[19,4]),'sequence':[1],'order':LOCAL,'group_at':0,'ticks':80,'seed':0},
        {'label':'blocked-and-foreign','goals':([16,1],[11,18],[18,4]),'sequence':[1],'order':LOCAL,'group_at':0,'ticks':400,'seed':0x12345678},
        {'label':'second-idle-orders','goals':goals,'sequence':[1],'order':LOCAL,'group_at':0,'ticks':450,'seed':7,'second':([16,4],[21,5],[19,4])},
    ]
    cases=[]
    for specification in specifications:
        oracle=LiveFleetOracle(specification['seed']);operations=[]
        def group():
            for identifier in LOCAL:
                state=oracle.receive(identifier,0,0,action=41)
                operations.append({'kind':'G','id':identifier,'group':0,'state':state})
        initial=[oracle.live_snapshot(i)for i in LOCAL]
        if specification['group_at']==0:group()
        for identifier,goal in zip(LOCAL,specification['goals']):
            operations.append({'kind':'R','id':identifier,'goal':list(goal),'argument':0,'state':oracle.receive(identifier,*goal)})
        for counter in range(1,specification['ticks']+1):
            if counter==specification['group_at']:group()
            if counter==201 and'second'in specification:
                for identifier,goal in zip(LOCAL,specification['second']):
                    operations.append({'kind':'R','id':identifier,'goal':list(goal),'argument':255,'state':oracle.receive(identifier,*goal,255)})
            pending=specification['sequence'][(counter-1)%len(specification['sequence'])]
            for identifier in specification['order']:
                operations.append({'kind':'T','id':identifier,'counter':counter,'pending':pending,'state':oracle.tick_actor(identifier,counter,pending)})
        cases.append({'label':specification['label'],'seed':specification['seed'],'initial':initial,'operations':operations})
    return {'schema_version':1,'original_exe_sha256':original.EXPECTED,'cases':cases,'planning_cases':planning_fixture(),
            'seed_payloads':{str(i):oracle.records[i].hex()for i in LOCAL},
            'scope':'Normal idle requests0/255;actual41/20 reception,promotion,live planning/work/motion;3actual local recipes;five stationary ungrouped foreign peers;wind0/5;no fullLife/UI/group-task scheduler'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    data=fixture();args.output.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print({'cases':len(data['cases']),'states':sum(len(c['initial'])+len(c['operations'])for c in data['cases'])})


if __name__=='__main__':main()
