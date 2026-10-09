import struct
from pathlib import Path

raw = Path("/sys/class/drm/card1/device/gpu_metrics").read_bytes()
print(f"gpu_metrics raw length = {len(raw)}")

# V2.2 header
size, fmt, content = struct.unpack_from("<HBB", raw, 0)
print(f"Header: size={size}, fmt={fmt}, content={content}")

# Clocks in v2.2
avg_gfx = struct.unpack_from("<H", raw, 0x04)[0]
avg_soc = struct.unpack_from("<H", raw, 0x06)[0]
avg_uclk = struct.unpack_from("<H", raw, 0x08)[0]
avg_fclk = struct.unpack_from("<H", raw, 0x0A)[0]
avg_vclk = struct.unpack_from("<H", raw, 0x0C)[0]
avg_dclk = struct.unpack_from("<H", raw, 0x0E)[0]

cur_gfx = struct.unpack_from("<H", raw, 0x10)[0]
cur_soc = struct.unpack_from("<H", raw, 0x12)[0]
cur_uclk = struct.unpack_from("<H", raw, 0x14)[0]
cur_fclk = struct.unpack_from("<H", raw, 0x16)[0]
cur_vclk = struct.unpack_from("<H", raw, 0x18)[0]
cur_dclk = struct.unpack_from("<H", raw, 0x1A)[0]

print(f"GFXCLK: cur={cur_gfx} MHz, avg={avg_gfx} MHz")
print(f"SOCCLK: cur={cur_soc} MHz, avg={avg_soc} MHz")
print(f"VCLK  : cur={cur_vclk} MHz, avg={avg_vclk} MHz")
print(f"DCLK  : cur={cur_dclk} MHz, avg={avg_dclk} MHz")





