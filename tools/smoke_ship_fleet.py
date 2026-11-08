"""Pending-fleet input, selector/slot lifecycle and exact source-art framebuffer QA."""
from pathlib import Path
import argparse,json,os,re,subprocess,time,struct
from PIL import Image,ImageChops
from tools import smoke_ship_box as box,stage_ship_fleet_visuals as art,probe_ship_pending_selection as policy_native
from tools import probe_ship_fleet_visuals as visual_native,probe_ship_pointer_hover as hover_native
pointer=box.pointer;menu,terrain,units,order,images,require=box.menu,box.terrain,box.units,box.order,box.images,box.require
ROOT=box.ROOT;PREFIX='[ShipFleetSelection] ';REPLAY='[ShipFleetReplay] '
STAGES='initial b-down b-up add-c-down add-c-up bc-phase0 toggle-b-down toggle-b-up b-reversing add-d-down add-d-up b-removed cd-healthy all-down all-activate all-extent all-up all-phase0 all-healthy empty-down empty-activate empty-extent empty-up remove-d-down remove-d-up add-d-box-down add-d-box-activate add-d-box-extent add-d-box-up guard-move-down guard-move-up cancel-down cancel-active device-cancelled recovered clear-right-down clear-right-up bars-removed selectors-removed d-again-down d-again-up d-recreated d-healthy ctrl-b-down ctrl-b-up ctrl-b-phase0'.split()
fields=box.fields
class Model:
    def __init__(self):
        self.reference=images.load_reference();motion=box.movement.WorkOracle(session_seed=0);self.samples=[motion.sample()]+[motion.advance()for _ in range(43)]
        self.case={'label':'idle-fleet','trace':self.samples,'samples':self.samples};self.case['_native_queue']=order.native_queue_history(self.case)
        self.policy=policy_native.PendingOracle();self.state=self.policy.snapshot_pending();self.hover=hover_native.NativeShipPointerHover();self.h=self.hover.snapshot()
        _,image,size=visual_native.original.native_image();self.context={};self.sel={};self.nodes={};self.node_kinds={}
        self.slot=visual_native.original.queue.NativeQueue(image,size);self.slot.w(visual_native.original.queue.M,visual_native.original.queue.M+0x80000)
        for node in visual_native.original.queue.cohort_registration():self.register(node['depth'],False)
        self.actor_metadata={a["id"]:a for a in hover_native.source_metadata()}
        for actor in self.actor_metadata.values():
            if actor['id']not in (11,12,13):continue
            logical={'A1':56,'H1':72}[actor['family']];ctx=visual_native.NativeSizedSelection(image,size,logical);self.context[actor['id']]=ctx
            self.sel[actor['id']]=ctx.op(['A',0,1,*actor['world']]);self.nodes[actor['id']]={'selector':-1,'health':-1}
        payloads,manifest=art.compose();directory=ROOT/'Unity/AncientConquest/Assets/Resources/ShipFleetVisualsGenerated'
        require((directory/'ShipFleetVisualsRgba.bytes').read_bytes()==payloads['ShipFleetVisualsRgba.bytes'],'Staged fleet atlas differs')
        rgba=Image.frombytes('RGBA',(640,400),payloads['ShipFleetVisualsRgba.bytes']).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        self.frames={f['name']:rgba.crop((f['atlas_x'],400-f['atlas_y']-f['height'],f['atlas_x']+f['width'],400-f['atlas_y']))for f in manifest['frames']}
        self.logical=[0,0];self.counter=0;self.box_node=-1;self.drag=None;self.active=False;self.visible=False;self.extent=[0,0];self.phase=0;self.box_stamp=0
        self.events=[];self.releases=[];self.cancels=[];self.checkpoints=[];self.rows={};self.expected_events=[];self.complete=False;self.cp=None;self.box=None;self.box_consumed=False;self.guard_count=0
        self.line=box.LineOracle();self.query=box.native.BoxOracle()
    def register(self,depth,callback):
        q=self.slot;s=visual_native.original.queue
        q.call(0x55dc20,(s.M,s.OUT,depth,0,1,1,0))if callback else q.call(0x55d670,(s.M,s.OUT,depth,1,0,0,1,1,0,0))
        return q.r(s.OUT)
    def release_node(self,node):
        q=self.slot;q.call(0x55ed60,(visual_native.original.queue.M,node));self.node_kinds.pop(node,None)
    def sync_hover_selection(self):
        members=self.state['members'];n=self.hover.n;n.put(hover_native.PENDING+12,len(members))
        for i,identifier in enumerate(members):n.put(hover_native.ABUF+4*i,n.actors[identifier])
    def source_cursor(self):
        n=self.hover.n;u=self.hover.u;c=hover_native.CUR
        u.mem_write(c+0x101,struct.pack('<H',self.state['cursor']));u.mem_write(c+0xe2,struct.pack('<HH',self.state['mask'],self.state['bit']));n.put(c+0xe6,int(self.state['blocked']));self.h=self.hover.snapshot()
    def source_events(self):
        self.state=self.policy.snapshot_pending();self.expected_events.extend(self.state['events']);self.policy.selection_events.clear()
        for identifier,value in self.state['events']:
            ctx=self.context[identifier];before=self.sel[identifier];actor=self.actor_metadata[identifier]
            self.sel[identifier]=ctx.op(['S',*actor['world']]if value else['D'])
            if value and not before['exists']:
                for kind,callback in (('selector',False),('health',True)):
                    node=self.register(1020,callback);self.nodes[identifier][kind]=node;self.node_kinds[node]=(identifier,kind)
    def advance_selection(self,identifier,tick,world):
        state=self.context[identifier].op(['A',tick,1,*world]);self.sel[identifier]=state
        for key,deleted in (('health',state['hides_health']),('selector',state['deletes'])):
            if deleted:self.release_node(self.nodes[identifier][key]);self.nodes[identifier][key]=-1
    def advance(self,counter):
        require(self.counter<=counter<=43,'Fleet counter moved backwards/out of scope')
        for tick in range(self.counter+1,counter+1):
            sample=self.samples[tick]
            for publication in sample['publications']:self.advance_selection(11,tick,publication['world'])
            for identifier in (11,12,13):
                s=self.sel[identifier]
                if s['frame']<10 or s['selection']==2:
                    world=sample['render_world']if identifier==11 else self.actor_metadata[identifier]['world']
                    self.advance_selection(identifier,tick,world)
            row=self.hover.metadata[11];self.hover.n.set_actor(11,sample['render_world'],sample['frame'],sample['heading'],self.hover.families[row['family']],row['record']['runtime_class_tag'])
            self.sync_hover_selection();self.h=self.hover.refresh(self.state['selected'],self.state['pending'])
        self.counter=counter
    def cancel_box(self):
        if self.box_node>=0:self.release_node(self.box_node);self.box_node=-1
        self.drag=None;self.active=self.visible=False;self.extent=[0,0];self.phase=0;self.box_stamp=0
    def consume(self,line):
        p=pointer.PREFIX
        if line.startswith(p+'packet:'):raise AssertionError('Selection-only mode issued an actor command')
        if line.startswith(PREFIX+'release: '):
            r=fields(line,PREFIX+'release: ');require((r['kind'],r['mask'],r['bit'],r['blocked'])==(self.h['cursor_type'],self.h['action_mask'],self.h['action_bit'],self.h['blocked']),'Fleet release did not use cached source hover')
            o=self.policy;o.observe(r['kind'],False,*self.h['cell'],mask=r['mask'],bit=r['bit'],blocked=r['blocked'],enabled=self.h['has_map']);o.w(policy_native.pointer.CUR+0xd9,o.actors[self.h['hovered_id']]if self.h['hovered_id']else 0)
            o.invoke_cursor(0x518070,(r['message'],r['flags']));self.source_events();self.source_cursor();self.releases.append(r)
        elif line.startswith(PREFIX+'box: '):
            r=fields(line,PREFIX+'box: ');require(self.active and self.drag is not None,'Fleet box release without an active rectangle')
            x,y=self.logical[0]+576,self.logical[1];bounds=[min(self.drag[0]//64,x//64),min(self.drag[1]//64,y//64),abs(self.drag[0]//64-x//64)+1,abs(self.drag[1]//64-y//64)+1]
            require(r['bounds']==bounds,'Fleet box used wrong source cells')
            # Query the actual source grid on a separate oracle: collection must
            # not clear this policy instance's live temporary vector.
            query=self.query.query(bounds)['members'];require(r['candidates']==(','.join(f'{i:08x}'for i in query)or'none'),'Fleet candidates differ from original')
            self.cancel_box();self.policy.observe(r['kind'],False,*self.h['cell'],mask=self.h['action_mask'],bit=self.h['action_bit'],blocked=self.h['blocked'],enabled=self.h['has_map'])
            self.policy.invoke_cursor(0x517b90,(r['flags'],*bounds));self.source_events();self.box_consumed=True;self.releases.append(r)
        elif line.startswith(PREFIX+'selection: '):
            r=fields(line,PREFIX+'selection: ');require(self.expected_events,'Unexpected fleet selection callback');require(self.expected_events.pop(0)==[int(r['id'],16),int(r['selected'])],'Fleet callback order/target differs')
        elif line.startswith(PREFIX+'guard: '):
            require(self.h['cursor_type']==7 and self.state['selected'],'Unexpected command guard context');self.guard_count+=1
        elif line.startswith(p+'event: '):
            r=pointer.tokens(line,'event');require(r['index']==len(self.events),'Fleet event index missing/reordered');self.advance(r['counter'])
            logical=[v//2 for v in r['raw']];world=[logical[0]+576,logical[1]]
            if r['message']==96 and logical!=self.logical:
                self.logical=logical;self.sync_hover_selection();self.h=self.hover.move(logical,world,self.state['selected'],self.state['pending'])
                if self.drag is not None:
                    extent=[world[i]-self.drag[i]+1 for i in(0,1)]
                    if not self.active and all(abs(v)>9 for v in extent):
                        self.active=True;self.extent=[0,0];self.visible=False;self.phase=0;self.box_stamp=r['visual_ms'];self.box_node=self.register(5,True)
                    elif self.active:self.extent=extent
            elif r['message']==97:self.drag=world
            elif r['message']==98:
                self.drag=None;self.box_consumed=False
            require(not self.expected_events,'Missing fleet callback before event fence')
            require(r['cursor']==self.h['cursor_type']and r['picked']==self.h['hovered_id']and r['has_map']==self.h['has_map'],'Fleet hover differs from original')
            require(r['selected']==self.state['selected']and r['pending']==self.state['pending']and r['ui_group']==r['simulation_group']==-1,'Fleet selection committed an unsupported group')
            require(r['rng']==self.samples[self.counter]['random_state'],'Selection mutated idle RNG');self.events.append(r)
        elif line.startswith(p+'motion: '):
            r=pointer.tokens(line,'motion');self.advance(r['counter']);require(r==pointer.expected_motion(self.samples[self.counter]),'Fleet idle motion differs from original')
        elif line.startswith(p+'cancel: '):
            r=pointer.tokens(line,'cancel');require(not r['synthesized_up']and r['selected']==self.state['selected'],'Fleet cancellation synthesized a release');self.cancel_box();self.cancels.append(r)
            from unicorn.x86_const import UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EIP
            from unicorn import UC_HOOK_CODE
            n=self.hover
            stop=n.u.hook_add(UC_HOOK_CODE,lambda u,a,z,d:u.emu_stop(),begin=0x518f39,end=0x518f39)
            n.u.reg_write(UC_X86_REG_ESI,hover_native.CUR);n.u.reg_write(UC_X86_REG_EDI,0);n.u.emu_start(0x518f2d,hover_native.picking.END,count=4);n.u.hook_del(stop)
            require(n.u.reg_read(UC_X86_REG_EIP)==0x518f39,'Native cursor invalidation did not finish')
            self.sync_hover_selection();self.h=self.hover.refresh(self.state['selected'],self.state['pending'])
        elif line.startswith(p+'checkpoint: '):
            require(self.cp is None,'Fleet checkpoint block incomplete');self.cp=pointer.tokens(line,'checkpoint');self.advance(self.cp['counter']);self.visuals=[];self.queue=[];self.fleet_rows=[];self.fleet_header=None;self.slot_row=None
        elif line.startswith('[ShipBoxReference] checkpoint: '):self.box=fields(line,'[ShipBoxReference] checkpoint: ')
        elif line.startswith(PREFIX+'checkpoint: '):self.fleet_header=fields(line,PREFIX+'checkpoint: ')
        elif line.startswith(PREFIX+'visual: '):self.fleet_rows.append(fields(line,PREFIX+'visual: '))
        elif line.startswith(PREFIX+'slots: '):self.slot_row=fields(line,PREFIX+'slots: ')
        elif line.startswith(p+'visual: '):self.visuals.append(pointer.tokens(line,'visual'))
        elif line.startswith(p+'queue: '):self.queue.append(pointer.tokens(line,'queue'))
        elif line.startswith(REPLAY+'stage: '):self.checkpoint(line.split('stage: ',1)[1].split(';',1)[0])
        elif line.startswith(REPLAY+'complete:'):self.complete=True
    def checkpoint(self,stage):
        require(stage==STAGES[len(self.checkpoints)]and self.cp and self.cp['stage']==stage,'Fleet checkpoints missing/reordered');h=self.cp;b=self.box
        if self.active and h['visual_ms']-self.box_stamp>49:self.phase=(self.phase+1)&31;self.visible=True;self.box_stamp=h['visual_ms']
        require(b['active']==self.active and b['visible']==self.visible and b['extent']==self.extent and b['phase']==self.phase and b['last_ms']==self.box_stamp,'Fleet drag phase/extent differs')
        members=','.join(f'{i:08x}'for i in self.state['members'])or'none';require(self.fleet_header=={'stage':stage,'members':members,'pending':self.state['pending'],'selected':self.state['selected'],'counter':self.counter},'Fleet checkpoint membership differs')
        require(len(self.fleet_rows)==3 and len(self.visuals)==4,'Missing fleet/pointer renderer rows');require(h['held']and not h['confirm']and not h['selector_exists'],'Legacy overlay leaked into fleet mode')
        q=self.slot;s=visual_native.original.queue;count=q.r(s.M+0x1a0);draw=[q.r(q.r(s.ORDER+4*i)+0x40)for i in range(count)][::-1];live=[i for i in draw if q.r(q.r(s.IDS+4*i))&0x8000];overlays=[i for i in live if i>=21];ranks={node:44+i for i,node in enumerate(overlays)}
        slot=self.slot_row;require(slot['allocated']==count and slot['live']==len(live)and slot['box_node']==self.box_node,'Retained source sprite slot lifecycle differs')
        if self.box_node>=0:require(slot['box_order']==ranks[self.box_node],'Box order differs from original')
        by_id={int(r['id'],16):r for r in self.fleet_rows};layers={}
        for identifier in (11,12,13):
            r=by_id[identifier];v=self.sel[identifier];logical=56 if identifier!=13 else 72;ns=self.nodes[identifier]
            expected={'size':logical,'flag':v['selection'],'exists':v['exists'],'frame':v['frame'],'drawn':v['drawn_frame'],'last':v['last_counter'],'visible':v['visible'],'position':v['world'],'sprite':'none'if v['drawn_frame']<0 else f'RAM_{logical:03d}X{logical:03d}{v["drawn_frame"]:02d}','node':ns['selector'],'health_exists':v['health_exists'],'health_visible':v['health_visible'],'health_position':v['health_world'],'health_sprite':f'HEALTH_100_{logical+4}','health_node':ns['health']}
            require(all(r[k]==value for k,value in expected.items()),'Fleet selector/native health differs: '+stage+'/'+str(identifier))
            for kind in ('selector','health'):
                node=ns[kind]
                if node>=0:require(r['order'if kind=='selector'else'health_order']==ranks[node],'Fleet callback/normal tie order differs')
                visible=r['visible'if kind=='selector'else'health_visible']
                if visible:layers[node]=(self.frames[r['sprite'if kind=='selector'else'health_sprite']],r['position'if kind=='selector'else'health_position'])
        cu=self.visuals[3];typ=h['cursor'];require(typ==self.h['cursor_type']and cu['order']==32767,'Fleet cursor differs');require(h['cursor_frame']in(range(4)if typ==7 else(0,)),'Invalid fleet cursor frame')
        require(cu['sprite']==f'CUR_{ {0:"STD",5:"OWN",6:"SELECT",7:"SEA"}[typ]}_N{h["cursor_frame"]:02d}'and cu['position']==[self.logical[0]+(-18 if typ==7 else 0),self.logical[1]+(-17 if typ==7 else 0)],'Fleet cursor plane/hotspot differs')
        base=order.checkpoint_reference(self.reference,self.case,stage,self.samples[self.counter]);require(self.queue==base['expected_queue_rows'],'Fleet base renderer queue differs')
        frame=base['expected_image'].convert('RGBA')
        for node in overlays:
            if node not in layers:continue
            plane,(x,y)=layers[node];images._composite_clipped(frame,plane.resize((plane.width*2,plane.height*2),Image.Resampling.NEAREST),(x-576)*2,y*2)
        frame=self.line.overlay(frame,b);frame=images.compose_overlay(frame,[cu],visual_reference=self.reference['pointer_visuals'])
        self.rows[stage]={'expected_image':frame,'header':h,'box':b,'regions':base['regions']};self.checkpoints.append(stage);self.cp=None


def run(output):
    output=Path(output).resolve();require(not output.exists(),'Choose fresh box QA directory');output.mkdir(parents=True)
    model=Model();baseline=pointer.provenance();baseline['fleet_sources']={str(p.relative_to(ROOT)):menu.file_sha256(p)for p in [Path(__file__),ROOT/'tools/probe_ship_pending_selection.py',*sorted((ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime').rglob('*.cs'))]}
    env=os.environ.copy();env['DISPLAY']=menu.DISPLAY;env['LD_LIBRARY_PATH']=str(menu.TOOLCHAIN/'usr/lib/x86_64-linux-gnu')
    log=output/'player.log';launch=['bash',str(terrain.LAUNCHER),str(terrain.EXECUTABLE),'-logFile',str(log),'--ship-pointer-reference','--ship-pointer-fleet-selection','--ship-pointer-fleet-replay','--terrain-origin-x','9','--terrain-origin-y','0']
    metadata={'launch':launch,'provenance':baseline,'scope':'Three local actors;pending selection only;commands guarded;synthetic Mouse+Keyboard InputSystem;no nativeWin11/OSmouse/performance/final2026art claims'}
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
                    latest=re.findall(re.escape(REPLAY)+r'stage: ([^;\r\n]+);',terrain.read_log(log))
                    require(latest and latest[-1]==stage,'Fleet model processing missed its held checkpoint')
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
                    relevant=lambda rows:[line for line in rows if line.startswith((pointer.PREFIX,PREFIX,'[ShipBoxReference]','[ShipFleetReplay] stage:'))]
                    require(relevant(lines)==relevant(after_lines),'Box state changed during capture')
                    cp['expected_image'].save(output/(stage+'-expected.png'),compress_level=0)
                    captures[stage]={'attempts':attempts,'maximum_channel_error':maximum,'counter':cp['header']['counter'],'box':cp['box']};menu.write_json(output/'captures.json',captures)
            if player.poll()is not None:break
            require(time.monotonic()-started<180,'Box QA timeout');time.sleep(.01)
        require(player.wait(timeout=10)==0 and model.complete and model.checkpoints==STAGES,'Fleet replay incomplete')
        final=terrain.read_log(log);require('Exception'not in final,'Runtime box exception; see player.log');require('Mission unit reference cleanup: claimed_released=8; visual_refs_cleared=True'in final and pointer.PREFIX+'cleanup: input_unsubscribed=True; visual_refs_cleared=True'in final,'Box claims/resources leaked')
        require(pointer.provenance()=={k:v for k,v in baseline.items()if k!='fleet_sources'},'Pointer build/source changed during box QA')
        require(all(menu.file_sha256(ROOT/p)==sha for p,sha in baseline['fleet_sources'].items()),'Box source changed during QA')
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
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run(a.output);print(json.dumps({'passed':r['passed'],'frames':len(r['captures']),'events':len(r['events']),'releases':len(r['releases'])}))
if __name__=='__main__':main()
