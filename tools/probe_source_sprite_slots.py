"""Actual original live/deleted/recycled normal/callback sprite slots."""
import argparse,json,random
from pathlib import Path
from tools import validate_source_sprite_depth_queue as source

def fixture():
    image,size=source.checked_image();cases=[]
    for seed in range(24):
        q=source.NativeQueue(image,size);q.w(source.M,source.M+0x80000);operations=[];rows=[]
        def snap():
            count=q.r(source.M+0x1a0);ids=[q.r(q.r(source.ORDER+4*i)+0x40)for i in range(count)]
            return {'depths':[q.s(q.r(source.IDS+4*i)+0x44)for i in range(count)],'alive':[bool(q.r(q.r(source.IDS+4*i))&0x8000)for i in range(count)],'draw_order':ids[::-1]}
        def op(kind,*args):
            if kind=='R':
                depth,callback=args
                q.call(0x55dc20,(source.M,source.OUT,depth,0,1,1,0))if callback else q.call(0x55d670,(source.M,source.OUT,depth,1,0,0,1,1,0,0))
                result=q.r(source.OUT)
            elif kind=='D':q.call(0x55ed60,(source.M,args[0]));result=None
            else:q.call(0x55d960,(source.M,*args));result=None
            operations.append([kind,*args]);rows.append(dict(snap(),result=result))
        for node in source.cohort_registration():op('R',node['depth'],False)
        # Force a dead depth5 slot to be reused for a selector, and preserve
        # callback ties after both higher and lower intervening nodes.
        for operation in [('R',5,True),('D',21),('R',1020,False),('R',1020,True),('R',1020,False),('R',1020,True),('D',23),('R',1020,False)]:op(*operation)
        rng=random.Random(seed)
        for _ in range(70):
            s=snap();active=[i for i,v in enumerate(s['alive'])if v and i>=21]
            if not active or rng.randrange(3)==0:
                op('R',rng.choice([5,1020,1020,2000,-1]),bool(rng.randrange(2)))
            elif rng.randrange(2):op('D',rng.choice(active))
            else:op('U',rng.choice(active),rng.choice([5,1020,1020,2000,10000,-10]))
        cases.append({'seed':seed,'operations':operations,'rows':rows})
    return {'schema_version':1,'original_exe_sha256':source.EXPECTED,'cases':cases,'scope':'Original55d670/55dc20/55d960/55ed60;unpublished nodes with sufficient fixed64 capacity;no heap/realloc/render callbacks;21 live world barriers plus temporary nodes'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();data=fixture();a.output.write_text(json.dumps(data,indent=2)+'\n');print({'cases':len(data['cases']),'rows':sum(len(c['rows'])for c in data['cases'])})
if __name__=='__main__':main()
