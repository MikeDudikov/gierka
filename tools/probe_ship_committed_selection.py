"""Original Ctrl/plain/right-release selection with cold committed normal groups."""
from pathlib import Path
import argparse,itertools,json
from tools import probe_ship_fleet_membership as membership
from tools import probe_ship_pointer_commands as pointer
ROOT=membership.ROOT


def fixture():
    metadata=membership.hover.source_metadata();cases=[]
    orders=[list(p)for count in(1,2,3)for p in itertools.permutations(membership.LOCAL,count)]
    for members in orders:
        for target in membership.LOCAL:
            for sequence in(('ctrl','clear','ctrl'),('plain','ctrl'),('ctrl','plain','clear')):
                o=membership.MembershipOracle(metadata);o.commit(members)
                rest=[i for i in membership.LOCAL if i not in members]
                if rest:o.commit(rest)
                #Selection entry state:no current visual selection;normal Mode10
                #groups already exist. This is an explicit UI setup boundary.
                o.w(pointer.SELECTED+12,0);o.w(pointer.FLEET+0xc2+20,-1);o.u.mem_write(pointer.FLEET+0x20,b'\0');o.w(pointer.motion.APP+0x3221,0)
                o.commands.clear();o.selection_events.clear();steps=[]
                for action in sequence:
                    o.selection_events.clear()
                    if action=='clear':state=o.release(7,None,message=100)
                    else:state=o.release(5,target,flags=8 if action=='ctrl' else 0)
                    group=state['current_group']
                    effective=state['members']if state['pending']else[]
                    if not state['pending']and group>=0:
                        g=o.r(pointer.GROUPS+28)+group*61;v=o.r(g+0x31)
                        effective=[o.r(o.r(pointer.ACTOR_DATA+4*o.r(o.r(v+28)+4*n))+0x4c)for n in range(o.r(v+12))]
                    steps.append({'action':action,'target':target,'after':state,'effective_members':effective})
                cases.append({'groups':[members]+([rest]if rest else[]),'steps':steps})
    return {'schema_version':1,'original_exe_sha256':pointer.gate.EXPECTED,'cases':cases,
            'scope':'Ctrl/plain/right blank selection;already committed normal Mode10 groups;group UI words only,sim words unchanged;no Shift group editing/taskLife/physical motion',
            'entries':['0x518070','0x49ab30','0x49ecb0','0x49d320','0x49ca60','0x49bd60','0x4dc630']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=fixture();a.output.write_text(json.dumps(d,separators=(',',':'))+'\n');print({'cases':len(d['cases']),'states':sum(len(c['steps'])for c in d['cases'])})


if __name__=='__main__':main()
