import sys
sys.path.insert(0, '/home/OWNER/vcn_unlock/bc250-smu-unlock')
from bc250_smu import Bc250Smu
import unlock

smu = Bc250Smu()
if not smu.secure_access_enabled():
    print("Unlocking SMU in Linux...")
    unlock.unlock(smu)

print("Checking Gasket Bank 12 live readback...")

test_regs = [
    ("BANK12_CTRL", 0x0900C234),
    ("BANK12_MASK0", 0x0900C830),
    ("BANK12_MASK1", 0x0900C834),
    ("BANK12_MASK2", 0x0900C838),
    ("BANK12_BMP", 0x0900C920),
    ("BANK12_RANGE0_START", 0x0900C934),
    ("BANK12_RANGE0_END", 0x0900C938),
    ("BANK12_RANGE0_ATTR", 0x0900C968),
]

for name, addr in test_regs:
    try:
        val = smu.smn_read32(addr)
        print(f"  {name:20s} (0x{addr:08X}) = 0x{val:08X}")
    except Exception as e:
        print(f"  {name:20s} (0x{addr:08X}) ERROR: {e}")

