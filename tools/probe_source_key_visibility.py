"""Execute original4eff00/4e9710 bindings and visibility-envelope dispatch.

Global key registry and virtual dispatch recipients are explicit observation
boundaries;this does not execute OS keyboard polling or the full application.
"""
from pathlib import Path
import argparse,json,struct
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP
from tools import probe_wp_move as marker


class KeyVisibilityOracle(marker.MarkerOracle):
    def __init__(self):
        self.key_ready=False;self.bindings=[];self.forwarded=[]
        super().__init__();self.system=self.heap;self.table=self.heap+0x100;self.message=self.heap+0x200
        self.forward=self.heap+0x300;self.broadcast=self.heap+0x310;self.heap+=0x1000
        self.u.mem_write(self.system,bytes(0x400));self.w(self.system,self.table);self.w(self.system+0x14,77)
        self.w(self.table+0x18,self.forward);self.w(self.table+0x20,self.broadcast)
        self.u.mem_write(self.forward,b'\xc2\x04\0');self.u.mem_write(self.broadcast,b'\xc2\x04\0');self.key_ready=True
    def hook(self,u,address,size,unused):
        if self.key_ready:
            sp=u.reg_read(UC_X86_REG_ESP)
            if address==0x540540:
                msg=self.r(sp+4);kind=self.r(msg+0x10)
                assert kind in(0x10,0x11)
                raw=bytes(u.mem_read(self.r(msg+0x14),74));self.bindings.append(dict(kind=kind,payload_hex=raw.hex()))
                self.ret(4,0);return
            if address in(self.forward,self.broadcast):
                msg=self.r(sp+4);self.forwarded.append(dict(slot=0x18 if address==self.forward else 0x20,words=list(struct.unpack('<8I',u.mem_read(msg,32)))))
                self.ret(4,0);return
            if address==0x542490:self.ret(4,0);return
        super().hook(u,address,size,unused)
    def send(self,kind,value=0):
        self.bindings.clear();self.forwarded.clear();self.u.mem_write(self.message,struct.pack('<8I',0,0,0,0,kind,value,0,0))
        motion=marker.normal.pointer.motion;sp=motion.S.STACK+motion.S.STACK_SIZE-0x1000
        self.w(sp,motion.S.END);self.w(sp+4,self.message)
        self.u.reg_write(UC_X86_REG_ESP,sp);self.u.reg_write(UC_X86_REG_ECX,self.system)
        self.u.emu_start(0x4eff00,motion.S.END,count=500000)
        assert self.u.reg_read(UC_X86_REG_EIP)==motion.S.END
        return dict(message=kind,value=value,stored=self.r(self.system+0x20),bindings=list(self.bindings),forwarded=list(self.forwarded))


def fixture():
    n=KeyVisibilityOracle();operations=[(8,0),(0xc45d,1),(0xc45d,1),(0xc45d,0),(0xc45d,0),(0xc45d,1),(0xc45e,0),(0xc45d,0),(0xc45e,0),(9,0)]
    return dict(schema_version=1,original_exe_sha256=marker.normal.pointer.gate.EXPECTED,
        rows=[n.send(*op)for op in operations],scope=__doc__,system_id_input=77,
        registry_boundary='540540',virtual_dispatch_boundaries=['vtable+18','vtable+20'],base_message_boundary='542490')


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=fixture()
    a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print([(x['message'],x['value'],x['stored'],len(x['bindings']),len(x['forwarded']))for x in r['rows']])


if __name__=='__main__':main()
