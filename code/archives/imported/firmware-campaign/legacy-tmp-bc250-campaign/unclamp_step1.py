#!/usr/bin/env python3
"""S1 IF/Fabric unclamp: single reversible SMN write of 0x3a2011c (firewall LOW bound)
-> 0x107FF (Cezanne exact), then read-back, smu.alive(), and re-read VCN mmUVD_VERSION
via safe driver-based amdgpu_regs AND raw /dev/mem ladder. Report BEFORE/AFTER."""
import os, sys, struct, time
from pathlib import Path
SMU_LIB = Path(os.environ.get("BC250_SMU_PATH", "/home/OWNER/vcn_unlock/bc250-smu-unlock"))
VCN_SRC = Path(os.environ.get("BC250_VCN_SOURCE", "/home/OWNER/vcn_unlock/daveconde-bc250-vcn-enable"))
sys.path.insert(0, str(SMU_LIB)); sys.path.insert(0, str(VCN_SRC))
import unlock
from bc250_smu import Bc250Smu, SmuError
import enable_vcn

REGS = "/sys/kernel/debug/dri/1/amdgpu_regs"  # card1
AMDPGU_REGS = {
    "mmUVD_POWER_STATUS": 0x01E2F0,  # dword 0x78BC
    "mmUVD_STATUS":       0x01E2F4,  # dword 0x78BD
    "mmUVD_SEMA_ADDR_LOW":0x01E004,  # dword 0x7801
    "mmUVD_SCRATCH9":     0x01E324,  # dword 0x78C9
    "mmUVD_VERSION":      0x01E328,  # dword 0x78CA  (per read_vcn_direct.py)
}
def rd_amdgpu(byte_off):
    with open(REGS,"rb") as f:
        f.seek(byte_off); return struct.unpack("<I", f.read(4))[0]

def snprint(prefix, regs, smu):
    out=[]
    for r in regs: out.append((hex(r), hex(smu.smn_read32(r))))
    print(prefix+" "+", ".join("%s=%s"%a for a in out), flush=True)

def main():
    smu = Bc250Smu()
    if not smu.alive(): print("E: SMU not alive"); return 1
    print("[*] SMU alive", flush=True)
    if not smu.secure_access_enabled():
        print("[*] unlocking...", flush=True); unlock.smu=smu; unlock.unlock(smu)
    if not smu.secure_access_enabled(): print("E: secure not open"); return 1
    print("[*] SMU secure access OPEN", flush=True)

    fw=[0x3A2011C, 0x0322011C, 0x3A20124, 0x1C780, 0x1C784, 0x3E810, 0x3E814]
    print("[--] BASELINE SMN firewall regs [--]", flush=True)
    snprint("base", fw, smu)
    print("[--] BASELINE VCN mmUVD_* via amdgpu_regs (safe driver) [--]", flush=True)
    for name,bo in AMDPU_REGS.items():
        print("   %s=0x%08X"%(name, rd_amdgpu(bo)), flush=True)

    TARGET=0x0000107FF
    print("[++] WRITE 0x3A2011C <= 0x%08X (single reversible store)"%TARGET, flush=True)
    smu.smn_write32(0x3A2011C, TARGET)
    ok=smu.alive()
    print("[+] smu.alive() AFTER write = %s"%ok, flush=True)
    if not ok:
        print("!! SMU wedged after write -- REVERT by power-cycle; NOT continuing.", flush=True)
        print("[--] readback after wedge [--]")
        snprint("rb post-write", fw, smu)
        smu.close(); return 4

    rb=smu.smn_read32(0x3A2011C)
    print("[+] readback 0x3A2011C = 0x%08X (expect 0x%08X)"%(rb, TARGET), flush=True)
    rb2=smu.smn_read32(0x0322011C)
    print("[+] 0x0322011C after write = 0x%08X (tracks? 0x3A2011C=0x%08X)"%(rb2, TARGET), flush=True)

    print("[++] AFTER: VCN mmUVD_* via amdgpu_regs (safe driver)", flush=True)
    for name,bo in AMDPU_REGS.items():
        v=rd_amdgpu(bo); mark=" <<< VISIBLE" if v!=0xFFFFFFFF else ""
        print("   %s=0x%08X%s"%(name, v, mark), flush=True)
    print("[++] AFTER: raw /dev/mem ladder (smn tool) -- cross check", flush=True)
    direct=None
    try:
        direct=enable_vcn.VcnDirect()
        for name,off,_ in enable_vcn.MMIO_PROBES:
            mmio=(enable_vcn.VCN_SEG1_DW if name in ("UVD_JPGW_POWER_STATUS",) else enable_vcn.VCN_SEG0_DW)+off
            print("   %s=0x%08X"%(name, direct.rd(mmio*4)), flush=True)
    except Exception as e:
        print("   ladder_err:",e, flush=True)
    finally:
        if direct is not None:
            try: direct.rf.close(); os.close(direct.vram_fd)
            except Exception: pass
    print("DONE_S1", flush=True)
    smu.close(); return 0

if __name__=="__main__":
    raise SystemExit(main())
