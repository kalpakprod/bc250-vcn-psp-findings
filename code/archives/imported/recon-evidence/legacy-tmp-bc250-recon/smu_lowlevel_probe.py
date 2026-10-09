import struct, os, time, sys
sys.path.insert(0, "/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages")
from bc250_smu.transport import Bc250PciTransport

bdf = "0000:01:00.0"
fd = os.open(f"/sys/bus/pci/devices/{bdf}/config", os.O_RDWR)
def rd(off): return struct.unpack("<I", os.pread(fd, 4, off))[0]
def wr(off, val): os.pwrite(fd, struct.pack("<I", val), off)

print("=== PCI config window ===")
for off in (0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70):
    print(f"  0x{off:02x}:", hex(rd(off)))

# Mailbox q3
CMD, RSP, ARG = 0x03B10A20, 0x03B10A80, 0x03B10A88
print("=== rsp read raw (before) ===")
wr(0xB8, RSP); print("  rsp =", hex(rd(0xBC)))
print("=== arg read raw (before) ===")
wr(0xB8, ARG); print("  arg =", hex(rd(0xBC)))
print("=== cmd read raw (before) ===")
wr(0xB8, CMD); print("  cmd =", hex(rd(0xBC)))

print("=== trigger msg 0x01 (test) at low level ===")
wr(0xB8, RSP); wr(0xBC, 0)          # clear rsp
wr(0xB8, ARG); wr(0xBC, 0x0000007B) # arg = 123
wr(0xB8, CMD); wr(0xBC, 0x01)       # msg 0x01
for i in range(15):
    wr(0xB8, RSP); r = rd(0xBC)
    print(f"  poll {i}: rsp={hex(r)}")
    if r in (0x01, 0xFF, 0xFE, 0xFD, 0xFC):
        print("  -> done status"); break
    time.sleep(0.02)

print("=== read back arg (expect 124 = 7B+1) ===")
wr(0xB8, ARG); print("  arg =", hex(rd(0xBC)))
os.close(fd)
print("done")
