"""Execute4ced80/545e00;observe lower renderer config/load boundaries only."""
from pathlib import Path
import argparse,json,struct
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EAX,UC_X86_REG_EIP
from tools import probe_ship_fleet_normal_task as normal
ROOT=normal.ROOT


class MarkerOracle(normal.TaskOracle):
    def __init__(self):
        self.marker_ready=False;self.configs=[];self.loads=[];self.recent=[]
        super().__init__(normal.source.membership.hover.source_metadata());self.marker_ready=True
    def hook(self,u,address,size,unused):
        if self.marker_ready:
            self.recent.append(hex(address));self.recent=self.recent[-20:]
            sp=u.reg_read(UC_X86_REG_ESP)
            if address==0x589c07:
                # operator_new58739e calls the CRT core directly;reuse the
                # same documented isolated allocator boundary as the parent.
                size=self.r(sp+4);pointer=self.heap;self.heap+=(size+15)&~15
                assert self.heap<0x72000000;self.ret(0,pointer);return
            if address==0x545e80:
                self.configs.append([self.r(sp+4*i)for i in range(1,5)])
                self.ret(16);return
            if address==0x546160:
                name=bytes(u.mem_read(self.r(sp+16),16)).split(b'\0')[0].decode('ascii')
                self.loads.append(dict(type=self.r(sp+8),mask=self.r(sp+12),name=name,last=self.r(sp+20)))
                self.ret(20,1);return
        super().hook(u,address,size,unused)
    def marker(self,ordinal):
        before=len(self.loads)
        try:self.invoke_fleet(0x4ced80,(ordinal,))
        except Exception as e:raise AssertionError(f'{e};EIP={self.u.reg_read(UC_X86_REG_EIP):x};recent={self.recent}')from e
        marker=self.u.reg_read(UC_X86_REG_EAX)
        assert marker and len(self.loads)==before+1
        assert self.r(marker)==0x59bb14 and self.signed(marker+0x41)==-1
        return dict(ordinal=ordinal,config=self.configs[-1][1:],load=self.loads[-1])


def position_fixture():
    # Actual4ced10 writes source pixel fields;handle remains-1 at lower renderer boundary.
    n=MarkerOracle();rows=[]
    for ordinal,(x,y)in enumerate(((0,0),(18,6),(16,4),(23,23),(-1,-1),(33554432,-33554433))):
        n.marker(ordinal);marker=n.u.reg_read(UC_X86_REG_EAX)
        vector=n.heap;record=vector+64;n.heap+=128
        n.u.mem_write(vector,bytes(64));n.w(vector+8,12);n.w(vector+12,1);n.w(vector+28,record)
        n.u.mem_write(record,struct.pack('<iiI',x,y,marker))
        n.invoke_fleet(0x4ced10,(vector,0))
        rows.append(dict(cell=[x,y],world=[n.signed(marker+0x59),n.signed(marker+0x5d)]))
    return rows


def fixture():
    n=MarkerOracle();return dict(schema_version=1,original_exe_sha256=normal.source.pointer.gate.EXPECTED,
        rows=[n.marker(i)for i in range(256)],scope=__doc__,graphics_constructor_executed=True,
        lower_renderer_config_and_load_are_boundaries=True,rendering_executed=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=fixture()
    a.output.write_text(json.dumps(d,separators=(',',':'))+'\n');print(dict(cases=len(d['rows']),first=d['rows'][:2],last=d['rows'][-1]))


if __name__=='__main__':main()
