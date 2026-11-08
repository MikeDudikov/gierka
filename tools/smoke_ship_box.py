"""Bounded real-player box gesture QA with original queries, policy, selector and line pixels.
Only queued InputSystem events; screenshots are internal QA artifacts.
"""
from pathlib import Path
import argparse, json, os, re, subprocess, time
from PIL import Image, ImageChops
from tools import smoke_ship_pointer as pointer, probe_ship_box_selection as native
from tools import probe_ship_move_order as movement, probe_ship_pointer_hover as hover_native
from tools import probe_ship_world_picker as picker
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EAX
menu, terrain, units, order, images, require = pointer.menu, pointer.terrain, pointer.units, pointer.order, pointer.images, pointer.require
ROOT=pointer.ROOT
STAGES=('initial box-down threshold-one-axis activated-zero extent-unpublished visible-forward box-right-down box-right-release selected-box empty-down empty-activate empty-extent empty-preserved reverse-down reverse-activate reverse-extent visible-reverse reverse-selected fleet-down fleet-activate fleet-extent fleet-guarded cancel-down cancel-active device-cancelled recovered one-cell-down one-cell-activate one-cell-extent one-cell-preserved').split()


def fields(line, prefix):
    row={}
    for token in line[len(prefix):].split('; '):
        key,value=token.split('=',1)
        require(key not in row, 'Duplicate box protocol key')
        if value in ('True','False'): value=value=='True'
        elif re.fullmatch(r'-?\d+(,-?\d+)+',value): value=list(map(int,value.split(',')))
        elif re.fullmatch(r'-?\d+',value) and key not in ('members',): value=int(value)
        row[key]=value
    return row


class LineOracle:
    def __init__(self):
        self.n=picker.NativeShipWorldPicker();n=self.n;n.u.mem_map(0,4096)
        self.surface=picker.BASE+0x100000;self.buffer=picker.BASE+0x110000;self.map=picker.BASE+0x200000
        for off,value in ((0x20,8),(0x24,1),(0x70,self.buffer),(0x74,960),(0x80,0),(0x84,0),(0x88,960),(0x8c,540)): n.put(self.surface+off,value)
        def boundary(u,a,size,unused):
            if a in (0x542530,0x567d20,0x567de0):
                sp=u.reg_read(UC_X86_REG_ESP);u.reg_write(UC_X86_REG_EIP,n.get(sp));u.reg_write(UC_X86_REG_ESP,sp+(4 if a==0x542530 else 8));u.reg_write(UC_X86_REG_EAX,0)
        n.u.hook_add(UC_HOOK_CODE,boundary);n.invoke(0x5195c0,(),self.map)
    def overlay(self, baseline, box):
        if not box['visible']: return baseline
        self.n.u.mem_write(self.buffer,b'\x11'*(960*540))
        x,y=box['start'];w,h=box['extent']
        self.n.invoke(0x56ff10,(self.surface,0,box['phase'],x-576,y,w,h,self.map+0x48d))
        raw=bytes(self.n.u.mem_read(self.buffer,960*540));require(set(raw)<={17,201},'Unexpected original outline palette')
        rgba=bytearray(960*540*4)
        for i,v in enumerate(raw):
            if v==201: rgba[4*i:4*i+4]=bytes((0,174,0,255))
        layer=Image.frombytes('RGBA',(960,540),bytes(rgba)).resize((1920,1080),Image.Resampling.NEAREST)
        result=baseline.convert('RGBA');result.alpha_composite(layer);return result.convert('RGB')


class Model:
    def __init__(self):
        self.reference=images.load_reference();self.motion=movement.WorkOracle(session_seed=0);self.samples=[self.motion.sample()]
        self.samples.extend(self.motion.advance() for _ in range(2))
        self.case={'label':'idle-box','trace':self.samples,'samples':self.samples}
        self.case['_native_queue']=order.native_queue_history(self.case)
        self.hover=hover_native.NativeShipPointerHover();self.h=self.hover.snapshot()
        self.query=native.BoxOracle();self.policy=native.PolicyOracle('none')
        for i in range(576): self.policy.w(native.command.motion.GRID+8+i*24+4,0)
        self.policy.w(native.command.motion.GRID+8+64*24+4,native.command.motion.OBJ)
        self.policy.u.mem_write(native.command.motion.OBJ+0x54,b'\x01\x01');self.policy.w(native.command.motion.OBJ+0x5ab,-1)
        _,image,size=pointer.selection_native.native_image();self.selection=pointer.selection_native.NativeSelection(image,size)
        self.sel=self.selection.op(['A',0,1,1028,132]);self.counter=0;self.selected=False;self.pending=False
        self.line=LineOracle();self.events=[];self.releases=[];self.cancels=[];self.checkpoints=[];self.rows={};self.complete=False;self.cp=None
        self.logical=[0,0];self.drag=None;self.active=False;self.box_visible=False;self.extent=[0,0];self.phase=0;self.box_stamp=0;self.visual_ms=0
    def advance(self,counter,visual_ms=None):
        require(self.counter<=counter<=2,'Unexpected box simulation counter')
        for tick in range(self.counter+1,counter+1):
            sample=self.samples[tick]
            for p in sample['publications']: self.sel=self.selection.op(['A',tick,1,*p['world']])
            if self.sel['frame']<10 or self.sel['selection']==2: self.sel=self.selection.op(['A',tick,1,*sample['render_world']])
            a=self.hover.metadata[11];self.hover.n.set_actor(11,sample['render_world'],sample['frame'],sample['heading'],self.hover.families[a['family']],a['record']['runtime_class_tag'])
            self.h=self.hover.refresh(self.selected,self.pending)
        self.counter=counter
    def consume(self,line):
        p=pointer.PREFIX
        if line.startswith(p+'packet:'): raise AssertionError('Box gesture issued an actor command')
        if line.startswith('[ShipBoxReference] release: '):
            row=fields(line,'[ShipBoxReference] release: ');require(self.active and self.drag is not None,'Box release without drag')
            x,y=self.logical[0]+576,self.logical[1]
            bounds=[min(self.drag[0]//64,x//64),min(self.drag[1]//64,y//64),abs(self.drag[0]//64-x//64)+1,abs(self.drag[1]//64-y//64)+1]
            require(row['bounds']==bounds,'Release used wrong source cell rectangle')
            members=self.query.query(bounds)['members'];require(row['members']==(','.join(f'{i:08x}'for i in members)or'none'),'Box members differ from original')
            supported=members in ([],[11]);calls=[]
            if supported:
                self.policy.observe(self.h['cursor_type'],self.h['hovered_id']==11,*self.h['cell'])
                before=len(self.policy.selection_calls);self.policy.invoke_cursor(0x517b90,(0,*bounds));state=self.policy.snapshot();calls=self.policy.selection_calls[before:]
                self.selected,self.pending=state['selected'],state['pending']
                for call in calls:self.sel=self.selection.op(['S',1028,132]if call else['D'])
            outcome='unsupported-fleet-set'if not supported else 'selected-source0b'if 1 in calls else'preserved'
            require(row['outcome']==outcome,'Box release policy differs from original/scope guard')
            self.releases.append(row);self.drag=None;self.active=self.box_visible=False;self.extent=[0,0];self.phase=0;self.box_stamp=0
        elif line.startswith(p+'event: '):
            row=pointer.tokens(line,'event');require(row['index']==len(self.events),'Skipped/duplicate box event');self.advance(row['counter']);self.visual_ms=row['visual_ms']
            raw=row['raw'];logical=[v//2 for v in raw];world=[576+logical[0],logical[1]]
            if row['message']==96 and logical!=self.logical:
                self.logical=logical;self.h=self.hover.move(logical,world,self.selected,self.pending)
                if self.drag is not None:
                    extent=[world[i]-self.drag[i]+1 for i in (0,1)]
                    if not self.active and all(abs(v)>9 for v in extent): self.active=True;self.extent=[0,0];self.box_stamp=self.visual_ms;self.phase=0;self.box_visible=False
                    elif self.active:self.extent=extent
            elif row['message']==97:self.drag=world;self.active=self.box_visible=False;self.extent=[0,0];self.phase=0;self.box_stamp=0
            require(row['cursor']==self.h['cursor_type']and row['picked']==self.h['hovered_id']and row['has_map']==self.h['has_map'],'Runtime hover differs from original')
            require(row['selected']==self.selected and row['pending']==self.pending and row['ui_group']==row['simulation_group']==-1,'Box selection mutated membership')
            require(row['rng']==self.samples[self.counter]['random_state'],'Box mutated idle RNG')
            self.events.append(row)
        elif line.startswith(p+'motion: '):
            row=pointer.tokens(line,'motion');self.advance(row['counter']);require(row==pointer.expected_motion(self.samples[self.counter]),'Box idle motion differs from original')
        elif line.startswith(p+'cancel: '):
            row=pointer.tokens(line,'cancel');require(row['counter']==self.counter and row['selected']==self.selected and not row['synthesized_up'],'Device cancel manufactured release')
            self.cancels.append(row);self.drag=None;self.active=self.box_visible=False;self.extent=[0,0];self.phase=0;self.box_stamp=0
            self.hover=hover_native.NativeShipPointerHover();self.h=self.hover.refresh(self.selected,self.pending)
        elif line.startswith(p+'checkpoint: '):
            require(self.cp is None,'Incomplete box checkpoint');self.cp=pointer.tokens(line,'checkpoint');self.visuals=[];self.queue=[];self.box=None
        elif line.startswith('[ShipBoxReference] checkpoint: '): self.box=fields(line,'[ShipBoxReference] checkpoint: ')
        elif line.startswith(p+'visual: '): self.visuals.append(pointer.tokens(line,'visual'))
        elif line.startswith(p+'queue: '): self.queue.append(pointer.tokens(line,'queue'))
        elif line.startswith('[ShipBoxReplay] stage: '):
            stage=line.split('stage: ',1)[1].split(';',1)[0];self.checkpoint(stage)
        elif line.startswith('[ShipBoxReplay] complete:'): self.complete=True
    def checkpoint(self,stage):
        require(stage==STAGES[len(self.checkpoints)] and self.cp and self.cp['stage']==stage,'Box stages missing/reordered')
        h=self.cp;self.advance(h['counter']);s=self.sel;b=self.box
        if self.active and h['visual_ms']-self.box_stamp>49:self.phase=(self.phase+1)&31;self.box_visible=True;self.box_stamp=h['visual_ms']
        require(b['candidate']==(self.drag is not None)and b['active']==self.active and b['visible']==self.box_visible and b['extent']==self.extent and b['phase']==self.phase and b['last_ms']==self.box_stamp,'Drag latch/extent/50ms phase differs')
        if self.drag is not None:require(b['start']==self.drag,'Wrong drag anchor')
        require(h['held']and h['selected']==self.selected and h['pending']==self.pending and not h['confirm']and not h['confirm_visible']and h['group_count']==0,'Box checkpoint selection/group/confirm differs')
        for key,value in {'selector_state':s['selection'],'selector_exists':s['exists'],'selector_frame':s['frame'],'selector_drawn':s['drawn_frame'],'selector_visible':s['visible'],'selector_last_counter':s['last_counter'],'health_visible':s['health_visible'],'health_exists':s['health_exists']}.items(): require(h[key]==value,'Native selector checkpoint differs: '+key)
        require(len(self.visuals)==4 and [v['kind']for v in self.visuals]==['selector','health','confirm','cursor'],'Missing box pointer visual')
        sc,hp,co,cu=self.visuals
        require(sc['exists']==s['exists']and sc['visible']==s['visible']and sc['position']==s['world']and sc['sprite']==('none'if s['drawn_frame']<0 else f"RAM_056X056{s['drawn_frame']:02d}"),'Selector pixels/position differ from native')
        require(hp['exists']==s['health_exists']and hp['visible']==s['health_visible']and hp['position']==s['health_world'],'Native health differs')
        require(not co['exists']and not co['visible']and co['order']==(47 if self.active else 46),'Unexpected box confirmation')
        typ=h['cursor'];require(typ==self.h['cursor_type'] and cu['order']==32767 and cu['exists']==cu['visible']==h['cursor_visible'],'Box cursor kind/visibility differs')
        require(h['cursor_frame']in(range(4)if typ==7 else(0,))and h['cursor_interval']==(150 if typ==7 else 10000),'Invalid source cursor phase/interval')
        require(cu['sprite']==f"CUR_{ {0:'STD',5:'OWN',6:'SELECT',7:'SEA'}[typ]}_N{h['cursor_frame']:02d}"and cu['position']==[self.logical[0]+(-18 if typ==7 else 0),self.logical[1]+(-17 if typ==7 else 0)],'Wrong box cursor plane/hotspot')
        base=order.checkpoint_reference(self.reference,self.case,stage,self.samples[self.counter]);require(self.queue==base['expected_queue_rows'],'Box changed base renderer queue')
        world_rows=[sc,hp,dict(co,order=46)]
        pixels=images.compose_overlay(base['expected_image'],world_rows,visual_reference=self.reference['pointer_visuals'])
        pixels=self.line.overlay(pixels,b);pixels=images.compose_overlay(pixels,[cu],visual_reference=self.reference['pointer_visuals'])
        self.rows[stage]={'expected_image':pixels,'header':h,'box':b,'regions':base['regions']};self.checkpoints.append(stage);self.cp=None


def run(output):
    output=Path(output).resolve();require(not output.exists(),'Choose fresh box QA directory');output.mkdir(parents=True)
    model=Model();baseline=pointer.provenance();baseline['box_sources']={str(p.relative_to(ROOT)):menu.file_sha256(p)for p in [Path(__file__),ROOT/'tools/probe_ship_box_selection.py',*sorted((ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime').rglob('*Box*.cs'))]}
    env=os.environ.copy();env['DISPLAY']=menu.DISPLAY;env['LD_LIBRARY_PATH']=str(menu.TOOLCHAIN/'usr/lib/x86_64-linux-gnu')
    log=output/'player.log';launch=['bash',str(terrain.LAUNCHER),str(terrain.EXECUTABLE),'-logFile',str(log),'--ship-pointer-reference','--ship-pointer-box-replay','--terrain-origin-x','9','--terrain-origin-y','0']
    metadata={'launch':launch,'provenance':baseline,'scope':'single controllable0b; multi/other sets guarded; synthetic InputSystem events; no nativeWin11/OSmouse/focus-loss/performance claims; source art, not2026 assets'}
    menu.write_json(output/'launch.json',metadata);player=xvfb=wl=xl=None;failure=None;captures={};started=time.monotonic();processed=0
    try:
        require(not menu.DISPLAY_SOCKET.exists(),'Display79 is owned')
        xl=(output/'xvfb.log').open('w');xvfb=subprocess.Popen([str(menu.TOOLCHAIN/'usr/bin/Xvfb'),menu.DISPLAY,'-screen','0','1920x1080x24','-nolisten','tcp','-ac'],env=env,stdout=xl,stderr=subprocess.STDOUT);menu.wait_for_display(xvfb)
        wl=(output/'wine-launch.log').open('w');player=subprocess.Popen(launch,cwd=terrain.EXECUTABLE.parent,env=env,stdout=wl,stderr=subprocess.STDOUT)
        window=units.wait_for_ready(player,env,log);geometry=menu.xdotool(env,'getwindowgeometry','--shell',window);(output/'geometry.txt').write_text(geometry)
        g=dict(x.split('=',1)for x in geometry.splitlines()if'='in x);require(tuple(int(g[x])for x in('X','Y','WIDTH','HEIGHT'))==(0,0,1920,1080),'Box player not fullscreen1920x1080')
        while True:
            text=terrain.read_log(log);lines=text.splitlines(keepends=True)
            if lines and not lines[-1].endswith('\n'):lines.pop()
            for line in lines[processed:]:model.consume(line.rstrip('\r\n'))
            processed=len(lines)
            if model.checkpoints:
                stage=model.checkpoints[-1]
                require(all(s in captures for s in model.checkpoints[:-1]),'Missed box QA frame')
                if stage not in captures:
                    cp=model.rows[stage];began=time.monotonic();attempts=[]
                    while True:
                        path=menu.capture(env,output,f'{stage}-attempt-{len(attempts)+1:02d}')
                        with Image.open(path)as im:
                            diff=ImageChops.difference(im.convert('RGB'),cp['expected_image']);extrema=diff.getextrema();maximum=max(v[1]for v in extrema)
                        attempts.append({'screenshot':path.name,'maximum_channel_error':maximum})
                        require(time.monotonic()-began<1.0,'Box presentation exceeded held fence')
                        if maximum==0:break
                        require(player.poll()is None,'Player exited before box presentation');time.sleep(.02)
                    after_lines=terrain.read_log(log).splitlines(keepends=True)
                    if after_lines and not after_lines[-1].endswith('\n'):after_lines.pop()
                    relevant=lambda rows:[line for line in rows if line.startswith((pointer.PREFIX,'[ShipBoxReference]','[ShipBoxReplay] stage:'))]
                    require(relevant(lines)==relevant(after_lines),'Box state changed during capture')
                    cp['expected_image'].save(output/(stage+'-expected.png'),compress_level=0)
                    captures[stage]={'attempts':attempts,'maximum_channel_error':maximum,'counter':cp['header']['counter'],'box':cp['box']};menu.write_json(output/'captures.json',captures)
            if player.poll()is not None:break
            require(time.monotonic()-started<145,'Box QA timeout');time.sleep(.01)
        require(player.wait(timeout=10)==0 and model.complete and model.checkpoints==STAGES,'Box replay incomplete')
        final=terrain.read_log(log);require('Exception'not in final,'Runtime box exception; see player.log');require('Mission unit reference cleanup: claimed_released=8; visual_refs_cleared=True'in final and pointer.PREFIX+'cleanup: input_unsubscribed=True; visual_refs_cleared=True'in final,'Box claims/resources leaked')
        require(pointer.provenance()=={k:v for k,v in baseline.items()if k!='box_sources'},'Pointer build/source changed during box QA')
        require(all(menu.file_sha256(ROOT/p)==sha for p,sha in baseline['box_sources'].items()),'Box source changed during QA')
    except Exception as error:failure=error
    finally:
        issues=[]
        for process,label in ((player,'box player'),(xvfb,'box Xvfb')):
            issue=menu.stop_owned_process(process,label)
            if issue:issues.append(issue)
        for stream in (wl,xl):
            if stream is not None:stream.close()
        if issues and failure is None:failure=RuntimeError(str(issues))
    if failure:
        menu.write_json(output/'failure.json',dict(metadata,passed=False,error=str(failure)));raise failure
    report=dict(metadata,passed=True,captures=captures,events=model.events,releases=model.releases,cancels=model.cancels,exit_code=0,elapsed_seconds=time.monotonic()-started,screenshots={p.name:menu.file_sha256(p)for p in sorted(output.glob('*.png'))})
    menu.write_json(output/'report.json',report);return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();result=run(args.output);print(json.dumps({'passed':result['passed'],'frames':len(result['captures']),'releases':len(result['releases']),'events':len(result['events'])}))
if __name__=='__main__':main()
