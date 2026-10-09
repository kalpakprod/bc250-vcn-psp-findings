import struct
# exact 128B from probe_vcn3.out od dump
raw = bytes.fromhex(
    "80000202"  # size=0x80 fmt=2 cont=2
    "00193e17"  # t_gfx t_soc
    "ffffffffffffffff"  # t_core0-3
    "e015c715ffffffff"  # t_core4-7
    "a8168f16"  # t_l3
    "3901ffff"  # act_gfx act_mm
    "85edaeccb3000000"  # clock_counter
    "feff3f1bffffdfbd"  # p_socket p_cpu p_soc p_gfx
    "ffff470138012c0b"  # p_core0-3
    "3b0803000d010300"  # p_core4-7
    "b203e604c201c20100005704"  # avg gfx soc uclk fclk vclk dclk
    "d007e604c201c20100005704"  # cur gfx soc uclk fclk vclk dclk
    "a00fa00fa00fa00f"  # coreclk0-3
    "a00ff106a00ff106"  # coreclk4-7
    "a00fa00f"  # l3clk
    "00000000"  # throttle u32
    "ffff"  # fan_pwm
    "ffffffffffff"  # pad0-2
    "ffffffffffffffff"  # indep_throttle - may be short; pad
)
# trim/pad to layout size
LAYOUT = "<HBB" + "HH" + "8H" + "2H" + "HH" + "Q" + "HHHH" + "8H" + "6H" + "6H" + "8H" + "2H" + "I" + "H" + "3H" + "Q"
need = struct.calcsize(LAYOUT)
print("need", need, "raw", len(raw))
if len(raw) < need:
    raw = raw + bytes(need - len(raw))
else:
    raw = raw[:need]
FIELDS = [
    "size", "fmt", "cont",
    "t_gfx", "t_soc",
    *[f"t_core{i}" for i in range(8)],
    "t_l3_0", "t_l3_1",
    "act_gfx", "act_mm",
    "clock_counter",
    "p_socket", "p_cpu", "p_soc", "p_gfx",
    *[f"p_core{i}" for i in range(8)],
    "avg_gfxclk", "avg_socclk", "avg_uclk", "avg_fclk", "avg_vclk", "avg_dclk",
    "cur_gfxclk", "cur_socclk", "cur_uclk", "cur_fclk", "cur_vclk", "cur_dclk",
    *[f"coreclk{i}" for i in range(8)],
    "l3clk_0", "l3clk_1",
    "throttle", "fan_pwm",
    "pad0", "pad1", "pad2",
    "indep_throttle",
]
vals = struct.unpack_from(LAYOUT, raw, 0)
d = dict(zip(FIELDS, vals))
for k in [
    "size","fmt","cont",
    "avg_gfxclk","avg_socclk","avg_uclk","avg_fclk","avg_vclk","avg_dclk",
    "cur_gfxclk","cur_socclk","cur_uclk","cur_fclk","cur_vclk","cur_dclk",
    "act_gfx","act_mm","t_gfx","t_soc","throttle",
]:
    print(f"{k}={d[k]}")
