"""Actual source cursor/Fleet/Ship hover for every local pending selection subset."""
import argparse,json
from pathlib import Path
from tools import probe_ship_pointer_hover as original

def fixture():
    n=original.NativeShipPointerHover();actors=original.source_metadata();local=[11,12,13];operations=[]
    for mask in range(8):
        members=[i for k,i in enumerate(local)if mask&(1<<k)]
        n.n.put(original.PENDING+12,len(members))
        for k,i in enumerate(members):n.n.put(original.ABUF+4*k,n.n.actors[i])
        # Grid centres include friendly hull centres and passable/blocked water.
        points=[[1056,160],[1376,352],[1248,288],[1184,352],[1024,128],[800,300],[1000,100],[1110,210],[1500,500]]
        for y in range(24):
            for x in range(24):
                world=[x*64+32,y*64+32];picked=n.n.query(*world,x,y,True)['hit_id']
                if picked is not None and picked not in local:continue
                points.append(world)
        for world in points:
            state=n.move(world,world,bool(members),bool(members));operations.append({'mask':mask,'operation':'MOVE','point':world,'state':state})
            state=n.refresh(bool(members),bool(members));operations.append({'mask':mask,'operation':'REFRESH','state':state})
    return {'schema_version':1,'original_exe_sha256':original.gate.EXPECTED,'actors':actors,'operations':operations,'scope':'All8 local pending subsets;friendly/water;foreign combat excluded;existing source cursor renderer/system boundaries'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();data=fixture();a.output.write_text(json.dumps(data,indent=2)+'\n');print({'states':len(data['operations'])})
if __name__=='__main__':main()
