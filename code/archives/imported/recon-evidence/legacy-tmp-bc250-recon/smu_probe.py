import sys, time
sys.path.insert(0, "/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages")
from bc250_smu.api import Bc250Smu

s = Bc250Smu(use_flock=True, allow_queue0=True)
print("=== exact bc250_detect sequence (with delays) ===")
try:
    r = s.send_message(3, 0x01, arg=123, pack=lambda a: a, decode=lambda x: x, check_status=True)
    print(f"test_message(123) -> {r} (expect 124): {'OK' if r==124 else 'MISMATCH'}")
except Exception as e:
    print("test_message ERR:", e)
time.sleep(0.1)
try:
    print("q3 smu_version:", hex(s.send_message(3, 0x02, decode=lambda x: x)))
except Exception as e:
    print("q3 0x02 ERR:", e)
time.sleep(0.1)
try:
    print("active_wgp:", s.query_active_wgp())
except Exception as e:
    print("active_wgp ERR:", e)
time.sleep(0.1)
try:
    feat = s.get_enabled_smu_features()
    print("enabled_smu_features:", hex(feat), "bin=", bin(feat))
except Exception as e:
    print("get_enabled_smu_features ERR:", e)
time.sleep(0.1)
try:
    s.set_core_enable_mask(0xFF)
    print("set_core_enable_mask(0xFF) OK")
    time.sleep(0.05)
    print("readback core_freq0:", s.q3_0x43_get_core_freq(0))
except Exception as e:
    print("set_core_enable_mask ERR:", e)
s.close()
print("DONE")