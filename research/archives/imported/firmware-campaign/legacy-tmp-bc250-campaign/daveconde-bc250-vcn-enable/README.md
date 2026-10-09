# bc250-vcn-enable

`enable_vcn.py` — enable the VCN (Video Core Next) video encode/decode block on a
headless AMD BC250 mining card by executing the BC250-community ("Discord") VCN
enable sequence **inside the SMU firmware itself**, over PCI, using the
[bc250-smu-unlock](https://github.com/rw-r-r-0644/bc250-smu-unlock) library.

Target platform: **BC250, BIOS 3 (Robin1), PMFW 0.58.6.0.**
The unlock library is **BIOS-3-only** as of this writing — its patches need
different offsets for the SMU firmware in BIOS 5.

## What it does

The tool installs a 20-byte Xtensa sequence into SMU scratch SRAM and gets the
firmware's own dispatcher to execute it. The sequence is a verbatim mirror of
the firmware's domain-6 (VCN) teardown code: three `call8 0x00023744` slot-clock
reprograms for slots 0x16/0x17/0x18.

Every run shares the same preamble:

1. `unlock()` — the library's Q2 ring-overflow exploit opens the secure-access
   debug cluster (skipped automatically if secure access is already open).
2. dom6 state snapshot + slot-table dump (read via the unlocked debug path).

Then, depending on flags:

3. **install** — the sequence bytes are written to SMU SRAM `0x3ff00` and
   verified by read-back.
4. **repoint** — the reserved Queue-3 msg-`0x61` handler pointer (SMU SRAM
   `0x776c`) is set to `0x3ff00`. The fw dispatcher calls that pointer when it
   sees msg 0x61 — the SMU's only native execution vector.
5. **fire** — the library's Q3 mailbox send rings the fw's doorbell. The send's
   response poll is the dispatch wait (an `SmuTimeout` ~5s later is expected).
6. **engage** — the three dom6 per-slot clock ENABLE (`+0x08`)=1 bits are set
   with a bounded window write, then the dom6 power sequencer
   (cmd/rail/status/ctrl) is read — the authoritative SMU-side power oracle.
   Skip with `--no-enable-engage`.
7. Optional stages: `--direct-load` (userspace VCN firmware boot + ring-test
   proof) and `--smn-vcn-probe` (one SMN read of the VCN block through the SMU).

On exit (best effort) the reserved handler slot is restored to 0 and the thunk
scratch is wiped.

## Requirements

- AMD BC250 running **BIOS 3** (Robin1 / PMFW 0.58.6.0)
- Linux on the target box, **root** (the script exits with `needs root` otherwise)
- **Python 3** — the script and the unlock library are pure stdlib; no pip packages
- The [bc250-smu-unlock](https://github.com/rw-r-r-0644/bc250-smu-unlock) library,
  checked out next to the script (see below)
- For `--direct-load` only: the `amdgpu` driver **loaded** and debugfs mounted
  (used purely as a raw MMIO/VRAM transport), plus a navi10 VCN firmware image
  (from the `linux-firmware` package)
- **Physical access to the machine's power switch** — several code paths are
  measured SMU-wedge vectors and recovery is a COLD power cycle (see
  [Safety](#safety--known-risks))

## Setup: checking out the unlock library

`enable_vcn.py` imports `bc250_smu` and `unlock` from the bc250-smu-unlock
library **at startup**. It looks for the library in a `bc250-smu-unlock/`
directory **next to the script itself** (that path is prepended to `sys.path`).
Without it, the script dies immediately with `ModuleNotFoundError: No module
named 'bc250_smu'`.

Clone the library **into this repository's directory**:

```sh
git clone https://github.com/daveconde/bc250-vcn-enable
cd bc250-vcn-enable
git clone https://github.com/rw-r-r-0644/bc250-smu-unlock
```

Expected layout:

```
bc250-vcn-enable/
├── enable_vcn.py
├── README.md
├── .gitignore
└── bc250-smu-unlock/        # cloned dependency -- NOT committed (gitignored)
    ├── bc250_smu/           # the Python package (Bc250Smu, ...)
    ├── unlock.py            # the unlock() exploit entry point
    └── ...
```

> The library is intentionally **not** part of this repository. `.gitignore`
> excludes it so a plain `git add .` never nests the whole unlock repo inside
> yours.

**Alternative location:** if you keep the library somewhere else, point the
`BC250_SMU_PATH` environment variable at its checkout. Note `sudo` strips the
environment by default, so use `env`:

```sh
sudo env BC250_SMU_PATH=/opt/bc250-smu-unlock python3 enable_vcn.py --verify
```

## Usage

All commands are run from this directory on the target box, as root:

```sh
# read-only: dump dom6/slot state, install nothing (safe first contact)
sudo python3 enable_vcn.py --verify

# unlock + prechecks + install the sequence, but do not trigger
# (disarms on exit: handler slot restored, thunk wiped)
sudo python3 enable_vcn.py --no-fire

# full run: install + fire the Discord sequence (3s last warning, then fire)
sudo python3 enable_vcn.py

# proceed even if the dom6 state byte is 0x00 (known wedge risk)
sudo python3 enable_vcn.py --force

# fire, then stage the navi10 VCN firmware in VRAM from userspace and boot
# VCN the driver's DIRECT way (no PSP/TEE) -- proof = the driver's own ring
# test (mmUVD_SCRATCH9 0xCAFEDEAD -> 0xDEADBEEF). amdgpu must be loaded.
sudo python3 enable_vcn.py --direct-load

# same, with an explicit firmware image, and leave VCN running afterwards
sudo python3 enable_vcn.py --direct-load /path/to/navi10_vcn.bin --keep-vcn

# standalone diagnostics (each runs as its own command -- see flags below)
sudo python3 enable_vcn.py --vcn-power-regs
sudo python3 enable_vcn.py --manual-powerup
sudo python3 enable_vcn.py --inline-store-probe
```

Typical order for a fresh card, following the script's own next-step hints:
`--verify` first, then the fire (or `--no-fire` for a dry install). After a
`--manual-powerup` run, `--vcn-power-regs` is the arbiter — the route-P re-read
gives differentiated register values if and only if the island is actually
powered.

## Flags

### Core run

| Flag | Description |
|------|-------------|
| *(none)* | Full run: unlock, prechecks, install, repoint, fire, engage, dom6 sequencer readout. |
| `--no-fire` | Unlock + prechecks + install the sequence, but do not trigger. Disarms on exit (handler slot restored, thunk wiped). |
| `--verify` | Read-only: dump dom6/slot state, install nothing. |
| `--force` | Proceed even if the dom6 state byte is `0x00` (the wrapper would auto-power dom6 first — known wedge). |
| `--bdf BDF` | PCI bus/device/function of the BC250 (default `0000:00:00.0`). Find yours with `lspci`. |

### Direct firmware load (`--direct-load` stage)

| Flag | Description |
|------|-------------|
| `--direct-load [PATH]` | After the Discord fire, stage the navi10 VCN firmware in VRAM **from userspace** and bring VCN up the driver's DIRECT way (no PSP, no TEE, no kernel VCN code), then run the driver's own ring test as proof. Needs `amdgpu` **loaded** (raw MMIO/VRAM transport via debugfs only). Optional `PATH` overrides the firmware image. |
| `--keep-vcn` | With `--direct-load`: leave VCN running after the proof (default parks it again, register-level `vcn_v2_0_stop`). |
| `--fw-offset VRAM_OFF` | With `--direct-load`: pin the VRAM staging offset (default: auto-walk zero spans at 8MB..24MB). |

Without an explicit `PATH`, the firmware is searched in the standard
linux-firmware locations: `/usr/lib/firmware/amdgpu/navi10_vcn.bin` (and the
`.xz` compressed spelling, decompression is automatic), `/lib/firmware/amdgpu/…`,
with `renoir_vcn.bin` (same VCN 2.x APU family) as fallback.

### Post-fire options

| Flag | Description |
|------|-------------|
| `--no-enable-engage` | Skip the post-fire step that engages the three dom6 per-slot clock ENABLE (`+0x08`)=1 bits and reads the dom6 power sequencer. Default: engage + read out. |
| `--smn-vcn-probe` | After the main stages, ONE SMN read THROUGH the SMU (Q3 msg 0x2A, the "mem64 window") at `--smn-vcn-addr`. The fw masks the arg to 20 bits (SMU-local `0x01100000 + (arg & 0xFFFFF)`) — it can never express a `0x024xxxxx` fabric address. **Which fabric frame the window maps onto is unresolved (v3)** — the probe prints both candidate effective addresses. A dead offset stalls the SMN bus (wedge, self-recovers ~10s or cold cycle). |
| `--smn-vcn-addr ADDR` | Address `--smn-vcn-probe` passes to the mem64 window (default `0x01103010` — the NBIO-frame-hypothesis spelling of the 2026-08-24 "fast 0" masked alias of the `0x02403010` arg; under the low-frame hypothesis the same read hit `0x00003010`). The sanity read uses the proven `0x5A870` window offset (core mask); the `0x1F8xx` family is refused (dead responder under either frame hypothesis — the documented hard wedge). |

### Standalone diagnostics

Each of these runs as **its own command** (they early-return before the fire).

| Flag | Description |
|------|-------------|
| `--vcn-power-regs` | **Fabric-slice probe**: dump VCN's `0x024` slice (`0x02403000 + 0x00..0x3C`) plus THM/GC live-IP slice anchors through the **PCI-config SMN window** (root `00:00.0` config `0xB8/0xBC`, the library transport — the one CPU-side transport that takes full 32-bit SMN addresses and has never hung). **Transport fix 2026-08-24 evening:** the old route P mmap'd BAR0, which is the 256 MB **VRAM aperture**, not the register file — every "window read" it made was a VRAM artifact (uniform `0xb9f53acd`, boot-dependent; the INDEX2 "echo" echoed into VRAM). The real register file is BAR5, and reads through its PCIE_INDEX2/DATA2 window are the July-measured **board hang** on VCN addresses. **New 2026-08-25, step 0 frame discriminator:** the core mask is read at BOTH full spellings (`0x0115A870`/`0x0005A870`) and the dom6 rail at `0x0116D184`/`0x0006D184` (compared against the live fw-window value) — resolves the SMU-window frame question and reports whether `--manual-powerup --config-writes` is available. Ladder: proven sanity read → frame discriminator → THM slice → GC slice → VCN slice (VCN skipped if the frame reads dead). Residual risk: first-ever `0x024`-frame CPU reads — small cold-cycle risk. Preceded by a dom6 power-sequencer report (the SMU-side oracle). |
| `--vcn-power-regs-w` | With `--vcn-power-regs`: ALSO run route W (SMU data window `0x0111F8xx`). **MEASURED 2026-08-20: stall on the first read, HARD SMU wedge, NO self-recover — cold power-cycle only.** The window also cannot structurally reach VCN's `0x02403000` fabric frame (it is 20-bit-masked into the `0x01100000` NBIO frame). Do not run it. |
| `--manual-powerup` | Run the fw-exact dom6 rail power-up protocol (FUN_00023b14 decode) with BOUNDED host-side polls — cannot wedge the SMU. Fixed step [0] releases all three ctrl gate bits (0/1/2 ↔ slots 0x16/0x17/0x18). Follow it with `--vcn-power-regs`: the fabric-slice diff is the arbiter (slice dead → live / values moving iff the rail landed). |
| `--config-writes` | With `--manual-powerup`: config-window stores + read-backs at the runtime-discriminated spelling. **MEASURED 2026-08-25: the sequencer IGNORES host fabric writes** (ctrl `0x02→0x00` store read back `0x02` instantly; the transport is source-verified, so the stores were correctly issued). The mode now runs the **config-write capability probe** (slot-0x16 enable toggle through the config window, restored via the fw window) to pin down the block's write reach, and reports. The fw-window debug-write path (plain `--manual-powerup`) is the live store vehicle. |
| `--thunk-writes` | With `--manual-powerup`: route the ctrl/cmd/rail stores through the INLINE store thunk (the fw's own window-store sequence executed in the msg-0x61 handler thunk at preflight depth; a mailbox-OK answer PROVES each store executed in firmware) instead of bare window stores. **Measured wedge risk** — refused without `--force-thunk-writes`. Run `--inline-store-probe` first; only if the mailbox ANSWERS is the vehicle proven. |
| `--force-thunk-writes` | Explicitly accept the measured wedge risk of `--thunk-writes`. |
| `--dom6-dump` | Standalone, read-only: dump the whole dom6 block `0x06D000–0x06D1FF` through the fw window (proven-safe; single-dword reads). Annotates the known sequencer/slot registers, flags **nonzero unknown dwords**, prints structured highlights, and **live-probes SMN `0x06900900..0x0690090C`** (the +0x54 quad's candidate address — read-only via the config window; nonzero = the clamp-register family found). **First dump (2026-08-25): 52 unknown nonzero dwords** — the block is far richer than the 4-register sequencer decode. Top Ghidra targets: the **four identical `(0x06900900, 0xe8)` pairs at +0x54..+0x70** (if `0x06900900` is an SMN address it's in an unmapped `0x069xxxxx` frame — prime ISO-clamp/release candidate, cf. the July "PCIE iso-clamp" finding); single-bit registers at +0x044/+0x074/+0x084/+0x090/+0x098/+0x09c/+0x1d0; config pairs (30/30, `0x80036`×2); timeout-ish `0x010003e8` at +0x1ec; trailing counters 8/347/194/312; the slot sub-blocks are 0x28 bytes with extra fields (+0x04=5, +0x1c=`0x1000`). |
| `--msg-table` | Standalone, read-only: dump the fw's Q3 message-handler table (SRAM `0x746C`, msg 0x01–0xC0). **First run returned garbage (fixed 2026-08-25):** `smu_read(addr, n)` reads **at most 18 words** per call (library source) — the first version requested 32-word chunks and got 0x80-periodic session residue. Now: 18-word chunks + cross-probe of the proven `0x776C` slot + premise validation (live secure msgs `0x28`–`0x2C` must resolve to **distinct** plausible code pointers AND msg `0x01` must resolve to TestMessage `0x1B3A8` — the anchor the weak first validator missed; stride 8 and 4 both tested). **REAL DUMP (2026-08-25): 147 handlers, premise validated.** Findings: (a) the `hi` dword is a **flags field** — `0x6` normal, `0x201` = the gated secure cluster (0x27–0x2F, bit `0x200` = needs unlock), **`0x206` = a second gated group: msgs 0x71/0x72/0xA7/0xA8** (undocumented, accessible post-unlock); (b) **undocumented secure siblings 0x27/0x2D/0x2E/0x2F** (handlers interleaved with the mem64 family — likely more window primitives); (c) **msg 0x21 → handler `0x249DC`, 0x319 bytes past the dom7 power-up caller `0x246C3`** — the #1 Ghidra suspect; (d) an alias region at 0xAA+ (0xAA/0xBF → TestMessage); (e) msg 0x61 reads no handler — the fire's restore verifiably works. The dump prints a flags-group analysis and a Ghidra shortlist. **The hunt: xref `0x23B14`/`0x246C3` in Ghidra, match callers to this table — the match is the msg ID.** Also decode msg `0x3C`'s features bitmask (renoir's `PowerUpVcn` is feature-gated). |
| `--thunk-probe` | ONE benign in-fw store via the call-thunk vehicle (FUN_000235c8 + fe4/fa8 tail) on a proven no-op target — slot 0x17's clock reg, re-writing its current value. **MEASURED 2026-08-21 (night-4): wedged the SMU** even with fn/args/encoding/tail all verified. Use `--inline-store-probe` next, or `--probe-fn` for the raw depth/bridge ladder. |
| `--inline-store-probe` | ONE idempotent in-fw store with the INLINE store thunk — the fw's own store sequence executed INSIDE the msg-0x61 handler thunk, zero fw function calls, call depth stays at the ABI-preflight envelope. Mailbox ANSWERS → in-fw stores proven (`--thunk-writes` un-gates); WEDGES → SMN-bridge access from handler context is the killer (stores stay host-side). |

### Probe tuning (with `--thunk-probe` / `--inline-store-probe`)

| Flag | Description |
|------|-------------|
| `--probe-fn ADDR` | With `--thunk-probe`: call an arbitrary fw function instead of FUN_000235c8 (`--probe-reg`/`--probe-value` become raw a2/a3 arguments). Depth/bridge ladder example: `--probe-fn 0x2a018 --probe-reg 4` tests the SMN window read of `0x032000e8` (the bridge-gate leaf) at the safe +2 depth. |
| `--probe-reg SMN` | Override the target register (default: slot 0x17's clock reg from the slot table). |
| `--probe-value VALUE` | Override the stored value (default: the register's CURRENT value — the probe is idempotent by construction). |

## Firmware dump + local xref scan (the Ghidra-free hunt)

The fw's own callers of the domain power-up functions are sitting in SRAM as
Xtensa `call` instructions — the BC250 can dump them and
[`scan_fw.py`](../../../../../../code/archives/imported/firmware-campaign/legacy-tmp-bc250-campaign/daveconde-bc250-vcn-enable/scan_fw.py) finds them locally (call8's encoding is already
calibrated against Robin1 — it's the same encoder the Discord sequence uses).

**1. Dump the running PMFW from SRAM (on the box):**

```sh
cd ~/vcn_unlock/bc250-vcn-enable
sudo python3 - << 'EOF'
import sys
sys.path.insert(0, "bc250-smu-unlock")
from bc250_smu import Bc250Smu
from unlock import unlock
smu = Bc250Smu()
if not smu.alive():
    sys.exit("SMU not alive -- cold power cycle")
if not smu.secure_access_enabled():
    unlock(smu)
smu.dump_sram("smu_sram.bin")     # full 0..0x40000, ~30-60 s
smu.close()
EOF
```

(If you already have an address-compatible dump — e.g. the robin_5 image the
decode notes came from — skip this and scan that file.)

**2. Scan it locally (no hardware, no Ghidra):**

```sh
python3 scan_fw.py smu_sram.bin
```

It parses the Q3 handler table at `0x746C` (validates msg 0x01 ==
TestMessage), scans every byte for CALL4/8/12 to the hunt targets, scans for
literal/pointer references, and attributes each hit to its owning message
handler. Built-in controls validate the decode math on real data
(`0x235C8` should show ~30 call sites). Output tells you directly:
*"`msg 0x21` handler `0x249dc` calls `0x23b14`"* — the sendable message ID.

Note: `0x246C3` (the dom7-caller label) is **not 4-byte aligned — direct
calls cannot target it** (Xtensa call targets are always 4-aligned; the
label is mid-function, like the old bogus `0x233E8`). It is hunted via the
literal/pointer xref instead (a `callx` through an l32r-loaded register can
reach any byte).

**3. When the scan names a message** — decode that handler first (the dump
contains its bytes), then send it (adjust id/args to what the scan + decode
say; **do not** send blind):

```sh
sudo python3 - << 'EOF'
import sys
sys.path.insert(0, "bc250-smu-unlock")
from bc250_smu import Bc250Smu
smu = Bc250Smu()
if not smu.secure_access_enabled():
    sys.exit("run the unlock first (enable_vcn.py does it)")
st, ret = smu.send_message(3, 0x21, [0], check_status=False)   # EXAMPLE
print(f"status 0x{st:02x} ret 0x{ret:08x}")
smu.close()
EOF
```

Then re-run `--direct-load`'s segment ladder — `UVD_VERSION` answering
anything other than `0xffffffff` is the island opening.

## Flag compatibility rules

The script enforces these at startup (violations exit with an explanation):

- `--verify` is strictly read-only — it cannot be combined with `--direct-load`,
  `--smn-vcn-probe`, `--vcn-power-regs-w`, or `--manual-powerup`.
- `--direct-load` requires the fire (drop `--no-fire`); `--keep-vcn` and
  `--fw-offset` only make sense with `--direct-load`.
- `--vcn-power-regs` is standalone — not with `--direct-load` / `--smn-vcn-probe`.
- `--vcn-power-regs-w` requires `--vcn-power-regs` (pass both or neither).
- `--manual-powerup` is standalone — not with `--verify` / `--direct-load` /
  `--smn-vcn-probe` / `--vcn-power-regs`.
- `--thunk-writes` requires `--manual-powerup` **and** `--force-thunk-writes`
  (until `--inline-store-probe` proves the inline vehicle).
- `--config-writes` requires `--manual-powerup` and is exclusive with
  `--thunk-writes` (two different store vehicles; config-window stores run at
  host level — no SMU code execution — and are the safer new path).
- `--dom6-dump` and `--msg-table` are standalone read-only diagnostics — run
  each as its own command.
- `--thunk-probe` and `--inline-store-probe` are standalone — each fires exactly
  one in-fw store and combines with nothing else.
- `--probe-reg` / `--probe-value` require `--thunk-probe` or
  `--inline-store-probe`; `--probe-fn` requires `--thunk-probe`.

## Safety — known risks

- **Run this only from a shell/box you can COLD POWER-CYCLE.** The core fire can
  HARD-WEDGE the SMU (unbounded VCLK/DCLK polls when there is no live clock
  rail) — a documented failure mode on headless BC250 cards. A wedge is
  recovered by cutting power, not by rebooting.
- Measured wedge vectors (all 2026-08): the call-thunk vehicle
  (`--thunk-probe`), route W (`--vcn-power-regs-w` — no self-recover),
  `--thunk-writes` in-fw stores, and unrouted SMN addresses under
  `--smn-vcn-probe` (self-recovers ~10s or cold cycle).
- Prechecks abort on the worst-known fire variant (dom6 state byte `0x00` → the
  auto-power branch calls FUN_00023b14(6,1), a known wedge) unless `--force`.
- Safe, read-only entry points: `--verify` and `--vcn-power-regs` (route P).
- On exit the script restores the reserved msg-0x61 handler slot and wipes the
  thunk scratch (best effort). If the SMU is unreachable at exit it prints a
  cold-cycle instruction.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'bc250_smu'` | The unlock library is not cloned next to `enable_vcn.py` — see [Setup](#setup-checking-out-the-unlock-library), or set `BC250_SMU_PATH`. |
| `needs root` | Run with `sudo`. |
| `[!] SMU not alive -- cold power cycle` | The SMU is wedged or the card is powered down. Cold power-cycle, then retry. |
| `[!] unlock did not open secure access -- cold cycle and retry` | The unlock exploit did not take. Cold power-cycle and re-run. |
| `amdgpu_regs not found (debugfs mounted? driver loaded?)` | `--direct-load` needs the amdgpu driver loaded and debugfs mounted. |

## VCN IP discovery data (BIOS ROM)

Reverse-engineered from `BC250_3.00_CHIPSETMENU.ROM` (BIOS 3 / Robin1) by
parsing the amdgpu **IP discovery** structures. Layout reference: kernel
`drivers/gpu/drm/amd/include/discovery.h` (structs) and
`drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.c` (parse flow); `soc15_hw_ip.h`
(`VCN_HWID == UVD_HWID == 12`), `amdgpu_ip.h` (`VCN_HWIP == UVD_HWIP`).

### Discovery binary location

| item | value |
|------|-------|
| discovery binary start | ROM offset **`0x981a00`** (`binary_signature 0x28211407`) |
| `binary_size` | `0x44c` |
| `table_list[0]` IP_DISCOVERY | offset `0x003c` (abs `0x981a3c`), size `0x324`, checksum `0x48dc` (**verified OK**) |
| `table_list[1]` GC | offset `0x0360` |
| `table_list[2]` HARVEST_INFO | offset `0x03c4` |
| `table_list[3]` **VCN_INFO** | **`0x0000` — ABSENT** |
| `table_list[4]` MALL_INFO / `[5]` NPS_INFO | `0x0000` — absent |

`ip_discovery_header` @ `0x003c`: signature `0x53445049` ("IPDS"), version 2,
1 die. Die 0 @ `0x008c` (abs `0x981a8c`): `num_ips = 38`, followed by 38 packed
`struct ip` records (records span `0x981a90`–`0x981d60`; all 38 re-parsed
2026-08-25 — see the full per-IP slice map in
[`vcn2_register_map.md`](vcn2_register_map.md)).

The HARVEST_INFO table @ `0x03c4` (signature `0x56524148` "HARV", v0.0) has an
**empty harvest list** — no IP is harvested per the BIOS, consistent with the
VCN record's harvest nibble = 0. Note the kernel's static
`cyan_skillfish_ip_offset.h` is a *pruned* copy of this table (it lists only 4
of the NBIF record's 6 bases, dropping SEG4 `0x0241B000` and SEG5
`0x04040000`), so the absence of a SEG there carries no information.

### The VCN IP record

**VCN = die-0 IP record index 34**, at discovery-blob offset `0x310` =
**absolute ROM offset `0x981d10`**.

Raw bytes:
```
0c 00 | 00 | 03 | 02 00 03 | 00 | 00 78 00 00 00 7e 00 00 00 30 40 02
```

Parsed per `struct ip` (discovery.h):

| field | value |
|-------|-------|
| hw_id | **`0x000c` (12)** = `VCN_HWID`/`UVD_HWID` |
| instance_number | 0 |
| num_base_address | 3 |
| major.minor.revision | **2.0.3** (VCN 2.x) |
| byte 7 | **harvest nibble (low 4 bits) = 0, variant/reserved = 0** |
| base_address[0] | `0x00007800` dw = `0x1E000` bytes → `reg_offset[VCN_HWIP][0][0]` (main VCN/JPEG decode block) |
| base_address[1] | `0x00007e00` dw = `0x1F800` bytes → `reg_offset[VCN_HWIP][0][1]` (**power/PG/harvest cluster**) |
| base_address[2] | `0x02403000` (**SMN fabric base** — renoir's `UVD0_BASE__INST0_SEG2`, identical) |

(Re-parsed 2026-08-24 against the ROM with the kernel's `discovery.h` structs —
all 38 die-0 records cross-validate against the kernel's hardcoded
cyan-skillfish version table: GC 10.1.3, MP0/MP1 11.0.8, MMHUB 2.0.3,
HDP/OSSSYS/SDMA 5.0.1, NBIF 2.1.1, UMC 8.1.1. Every IP on this SoC carries a
`0x024xxxxx` fabric base as its last base address — VCN's is `0x02403000`.)

### Key takeaways

1. **No `VCN_INFO` table** exists in this BIOS (table_list[3] all zeros). The
   driver's VCN *fuse* data (`vcn_info_v1_0`: av1/vp9/hevc/h264_disabled) is
   therefore **not sourced from the BIOS** here — only the **IP_DISCOVERY**
   record above defines VCN (hw_id 12, v2.0.3, base addresses).
2. `base_address[0]=0x7800` / `base_address[1]=0x7E00` are the **local MM
   window** the driver uses for VCN; `base_address[2]=0x02403000` is VCN's
   **SMN fabric slice** base — a small (~2 KB) per-IP aperture whose contents
   are unknown, NOT a register-file mirror (see the address-space section
   below).
3. The record reports **VCN present, v2.0.3, NOT harvested** (byte 7's low
   nibble is the v2 `struct ip` harvest field — an earlier revision of this
   doc misread it as "sub_revision/variant" and claimed v2 has no harvest
   bit; both claims corrected 2026-08-24). `revision & 0xC0` — the kernel's
   `vcn_config` decode (`amdgpu_discovery.c`) — is 0 → **encode+decode both
   enabled**. Consistent with "power-gated, not absent", which is what the
   `--vcn-power-regs` / `--manual-powerup` routes are testing.
4. **Upstream Linux knows this chip and deliberately skips VCN.**
   `CHIP_CYAN_SKILLFISH` (incl. DID `0x13FE`, `amdgpu_drv.c`) exists; the
   kernel hardcodes `UVD_HWIP = IP_VERSION(2, 0, 3)` for it
   (`amdgpu_discovery.c`, via `cyan_skillfish_reg_init.c`) but the VCN
   ip-block switch has `case IP_VERSION(2, 0, 3): break;` — **no VCN block
   is ever added** (the console PSP TEE has no fw_type-13 slot, so a driver
   bring-up would fail its firmware load). The kernel's hand-written
   `cyan_skillfish_ip_offset.h` lists `UVD0_BASE__INST0_SEG2 = 0` only
   because the driver never needs SEG2 for a block it does not instantiate —
   the ROM's `0x02403000` is the hardware truth.

## VCN register addresses — the address-space model (v3, 2026-08-25)

Full table: **[`vcn2_register_map.md`](vcn2_register_map.md)** (467 registers,
VCN 2.0.3, plus the ROM-verified full 0x024-frame slice map). Generated from
the kernel register header
`drivers/gpu/drm/amd/include/asic_reg/vcn/vcn_2_0_0_offset.h` (re-verified
2026-08-25 against the kernel tree in `linux/`: all 467 registers, every
offset/bit-mask `--direct-load` uses, the doorbell/C2PMSG/GB_ADDR_CONFIG/
BIF_MMSCH0 spellings, and the whole `vcn_v2_0_start`/`mc_resume`/ring-test/
stop sequence) combined with the discovery `base_address[]` above.

**1. MMIO byte address** (the `amdgpu_regs` debugfs route `--direct-load`
uses) — from `RREG32_SOC15(VCN, inst, reg)` in `soc15_common.h`:

```
MM dword addr = base_address[reg_BASE_IDX] + mmREG      (SEG1 = 0x7E00 for the power cluster)
MM byte addr  = MM dword addr * 4                        (UVD_POWER_STATUS = 0x1F810)
```

CPU reads of the VCN segment **hang the board** while the island is dead
(July, measured three ways: userspace BAR5 mmap, UMR, kernel debugfs) — but
**MEASURED 2026-08-25, post-clock-work** (slots programmed + enables ON +
gates released): `POWER_STATUS` reads **all-ones and the board does NOT
hang**. With clocks on, all-ones is the reliable behavior of the closed
island; the July hang was a pre-clock-work behavior. `--direct-load`'s
segment ladder exploits this: it reads 11 registers across both segments
(incl. the static `UVD_VERSION` constant — the register-file liveness key)
and classifies the failure: **MEASURED 2026-08-25: uniform all-ones across
everything incl. UVD_VERSION — the whole register file is clamped at the
root**, not a per-cluster gating.

**2. MMIO offsets are NOT SMN addresses** (kernel-verified, v3): every IP's
registers exist at SEVERAL spellings whose numerics are unrelated. The kernel
talks to this card's MP1 (SMU) at MMIO `0x058A08` =
(`MP1_BASE__INST0_SEG0` 0x16000 + `mmMP1_SMN_C2PMSG_66` 0x282 dwords) × 4,
while the same PMFW's mailbox queues live at SMN `0x03B10A20` (the unlock
library's transport, hardware-proven). Same block, two unrelated frames. In
each IP's discovery `base_address[]` list only the small values
(≤ 0x10400 dwords) are MMIO spellings — this is the definitive refutation of
the old "MMIO offset == SMN offset" folklore.

**3. SMN fabric frame `0x024xxxxx`** — nearly every IP in the ROM's
discovery table carries one small slice here (VCN `0x02403000`, GC
`0x02402c00`, THM `0x02400c00`, MMHUB `0x02408800`, MP0/MP1 `0x0243fc00`, …
— full ROM-verified map in `vcn2_register_map.md`). ⚠ The slices are SMALL
(VCN's ≤ 2 KB, GC's 1 KB) and are NOT register-file mirrors (GC's MMIO file
alone is ~35 KB). **No VCN 2.0 register uses BASE_IDX 2** (all 467 header
entries are 0 or 1) — the kernel derives no address from SEG2 on ANY ASIC.
A full scan of the 16 MB BIOS ROM finds **no register writes into the frame**
(the only 0x024xxxxx literals are the discovery table itself) — the earlier
"the BIOS GNB table programs THM/CLK config through their slices" claim is
RETRACTED. **No SMN spelling of `mmUVD_POWER_STATUS` is known — `0x02403010`
is simply the 5th dword of VCN's slice.** `--vcn-power-regs` dumps the slice
and lets the values speak.

**4. SMU mem64/data window** (Q3 msgs 0x2A read / 0x2B+0x2C write; transfer
engine reads at the same offset) — the fw **masks its target to 20 bits** and
accesses it at SMU-local `0x01100000 + (target & 0xFFFFF)` (FUN_000235c8
decode). **RESOLVED 2026-08-25 (route P step 0, on hardware): the window maps
to the SMN LOW frame** — the dom6 sequencer's four registers match live at
`0x0006D1xx` (status=`0x01010101`, ctrl=`0x02` — distinctive) while the NBIO
spellings `0x0116D1xx` read dead-zero. So: **fw-window offset X == SMN
`0x000X`**. The core mask read `0x77` at BOTH spellings (alias or
coincidence — ambiguous on its own; the dom6 match is the decisive one). The
window still can never express `0x024xxxxx` and cannot reach the PMFW mailbox
frame `0x03B1xxxx` (measured stall). Dead config reads on this box return
`0x00000000` (THM/GC slices, `0x0116D1xx`) — not the `0xffffffff` July #5
suggested; this also fully explains the 2026-08-24 "fast 0": arg `0x02403010`
→ masked → low-frame `0x00003010` → dead → zero.

**5. PCI-config SMN window** (root `00:00.0`, config `0xB8/0xBC`) — the
library's own transport (`Bc250PciTransport`), proven live at SMN
`0x03B10A20` (every mailbox send). Full 32-bit SMN addressing, no masking.
Route P step 0 runs the **frame discriminator**: the core mask and the four
dom6 sequencer registers are read at BOTH full spellings, the latter compared
against the live fw-window values. **MEASURED 2026-08-25: the dom6 sequencer
IS fabric-visible at SMN `0x0006D1xx`** (status/ctrl distinctive-value match;
the NBIO spelling `0x0116D1xx` reads dead-zero) — the SMU window frame
question is settled: **LOW frame**. **MEASURED 2026-08-25: config WRITES to
the sequencer are IGNORED** — correctly-issued stores (transport
source-verified: `write_smu_reg(reg, value)`, the same index/data mechanics
as every mailbox send) to `0x0006D0F8/0x0006D17C/0x0006D184` produced no
register change (ctrl `0x02→0x00` read back `0x02` immediately). The block
is fabric-READABLE but host-fabric-write-protected; the fw-window debug-write
path (SMU-executed — provably lands and persists on BOTH the slot
sub-registers and the sequencer ctrl, measured 2026-08-25) is the live store
vehicle. **MEASURED 2026-08-25: the 0x024
frame reads dead-zero through this window even on live IPs** (THM/GC anchors
all `0x00000000`) — the fabric-slice probe carries no information on this
box; the dom6 sequencer registers (config-readable) and the VCN MMIO read
are the arbiters. Route P step 0d also runs the **live-tracking
cross-check** (slot 0x17's post-boot-changed clock/enable read via both
paths) to prove the config-read path tracks live state, not a boot snapshot.

**How working siblings open the island (kernel-verified 2026-08-25):**
renoir — the same silicon family with working VCN — powers the island via
the PMFW message `PPSMC_MSG_PowerUpVcn` (`smu_cmn_send_smc_msg_with_param`,
renoir_ppt.c), and that message is **feature-gated** behind
`SMU_FEATURE_VCN_PG_BIT` (the driver enables the feature first). This
card's PMFW driver message list (`smu_v11_8_ppsmc.h` — the Robin1
interface) has **no VCN message at all**, so the driver-facing surface is a
dead end. (Note: the kernel's MP1 C2PMSG mailbox and the PMFW's Q3 queues
are **different message spaces** — PPSMC 0x1D is SetMinDeepSleepGfxclkFreq
while Q3 0x1D is set-soc-clock; the kernel list never constrained Q3.) The
fw's *internal* Q3 message space (the one the unlock library speaks) is
rich: **147 live handlers enumerated 2026-08-25** — the library's own `api_q3.py` documents ~60 live
Q3 message ids — VID/clock/temp controls and notably **`0x3C`/`0x3D`
enable/disable SMU features (bitmask args)** plus `GetEnabledSmuFeatures`
(PPSMC 0x3D numbering). The Q3 handler table sits in SRAM at `0x746C`
(entry for msg M at `0x746C+(M-1)*8` — the same math the fire's repoint
uses). `--msg-table` enumerates it read-only (with transport + premise
validation — see the flag row); any message whose handler reaches
`FUN_00023b14` (the domain power-up sequencer) is the fw's *own* power-up
vehicle — the renoir `PowerUpVcn` analog — callable with the library's
mailbox send. Two concrete hunts: (a) resolve unknown handlers in Ghidra
for `0x23b14`/`0x246c3` callers; (b) decode the features bitmask of msg
`0x3C` — a VCN/PG bit there (renoir analog) plus whatever message consumes
it would be the native path.

**Night-1 correction (2026-08-25):** night-1's "stores sat dirty" ctrl
evidence was vacuous — the old bit0-only clear computed `ctrl & ~1 = 0x02`
and wrote `0x02` over `0x02` (identical value; the "unchanged" read-back
proved nothing). The FIXED all-three-bits clear ran 2026-08-25 (plain
`--manual-powerup`): **ctrl LANDED (`0x02→0x00`) and PERSISTED across
processes** (re-read `0x00000000` by a later `--vcn-power-regs` run) —
fw-window stores land on the sequencer sub-block; night-1's "sat dirty" is
dead. The cmd/rail stores in the same run are landed-by-inference with
vacuous read-backs (one-shot/self-clear semantics; favored reading: taken on
an already-up rail). A cold boot restores the factory `ctrl=0x02` — the
release lives only in the SMU session.

⚠ **Retracted claims (2026-08-24/25):**
- "MMIO offset == SMN offset" (the original model) — wrong, navi10 folklore;
  definitively refuted by the MP1 counter-example in space 2.
- "SMN = base[2] + mmREG*4, so 0x02403010 IS mmUVD_POWER_STATUS, and the
  msg-0x2A fast-0 proves the fabric route answers" — the formula is
  unsupported (slices aren't mirrors; no register uses BASE_IDX 2), and the
  fast-0 was the **masked alias** of the mem64 window (0x01103010 or
  0x00003010 depending on the unresolved frame).
- "the BIOS GNB table programs THM/CLK config through their 0x024 slices" —
  no 0x024-frame register writes exist anywhere in the ROM (full scan).
- "the core mask is proven at SMN 0x0115A870" — only the WINDOW OFFSET
  0x5A870 is proven; the old route-P "confirmations" were BAR0 VRAM
  artifacts. The full spelling is an open question the discriminator answers.

The measured rows, reinterpreted:

| address | what it actually is | measured behavior |
|---------|--------------------|-------------------|
| `0x1F810` as **MMIO** | UVD_POWER_STATUS in the GPU register file (BAR5) | reads **hang the board** while the island is dead (July ×3) |
| `0x1F810` as **mem64-window arg** | masked alias — no responder under either frame hypothesis | hard SMU wedge (route W, 2026-08-20; July msg-0x2A ×3) |
| `0x02403010` as **mem64-window arg** | masked alias (0x01103010 or 0x00003010) | fast 0 — **not a VCN read** (retracted as VCN evidence) |
| `0x02403000` as **SMN via BAR5 INDEX2** | VCN's fabric slice base | kernel-debugfs read **hung the board** (July #3) — the BAR5 window is off the table for VCN |
| `0x02403000` as **SMN via config 0xB8/0xBC** | VCN's fabric slice base | **not read** — the THM/GC live-IP anchors read dead-zero (measured 2026-08-25), so the ladder skipped the VCN slice (zero risk, zero info: the 0x024 frame is dead-or-zero through this window) |
| `0x0116D1xx` / `0x0006D1xx` as **config-window** | dom6 sequencer, full spellings | **measured 2026-08-25: `0x0006D1xx` matches all four live fw-window values (status/ctrl distinctive); `0x0116D1xx` reads dead-zero** ⇒ low frame confirmed, `--config-writes` armed |
| `0x0115A870` / `0x0005A870` as **config-window** | core mask, full spellings | **measured 2026-08-25: BOTH return `0x00000077`** — ambiguous (alias or coincidence); the dom6 match is the decisive frame evidence |
| `0x0006D0F8` / `0x0006D17C` / `0x0006D184` as **config-window WRITES** | dom6 sequencer ctrl/cmd/rail | **measured 2026-08-25: IGNORED** — correctly-issued stores (source-verified transport) produce no register change; ctrl `0x02→0x00` reads back `0x02` immediately. Fabric-readable, host-fabric-write-protected |
| slot regs `0x0006D100+` via **fw-window writes** | dom6 slot clock/enable registers | **proven landing** — the engage's enable `0→1` write, read-back verified, persisted across processes (the SMU-executed debug-write path works on this block) |
| dom6 ctrl `0x06D0F8` via **fw-window write** | domain gate release | **measured 2026-08-25: LANDED and PERSISTED** (`0x02→0x00`, re-read `0x00` by a later process) — fw-window stores land on the sequencer sub-block too; night-1's "sat dirty" is dead |
| dom6 cmd/rail (`0x06D17C`/`0x06D184`) via **fw-window writes** | sequencer one-shot commands | **measured 2026-08-25: landed-by-inference, read-backs vacuous** — cmd read 0 pre-write (self-clear indistinguishable); rail bit16 never showed (favored: an already-up rail consumed the one-shot instantly) |
| VCN MMIO segment ladder (11 regs, SEG0+SEG1, incl. `UVD_VERSION`) | the VCN register file itself | **measured 2026-08-25: uniform all-ones, NO hang** (post-clock-work; July's hang was pre-clock-work) — the whole register file is clamped at the root while the SMU sequencer reports dom6 UP. The contradiction is the open question |
| renoir `PPSMC_MSG_PowerUpVcn` vs this PMFW | island power via PMFW message | **kernel-verified 2026-08-25:** renoir's driver opens the island with this message (feature-gated behind `SMU_FEATURE_VCN_PG_BIT`); this PMFW's driver list (`smu_v11_8_ppsmc.h`) has **no VCN message** — the internal Q3 space (`--msg-table`) is the remaining place a fw-native power-up message can live |
| `smu_read(addr, n)` bulk reads | library transport contract | **source-verified 2026-08-25 (`bc250_smu/primitives.py`): n ≤ 18 words per call.** The first `--msg-table` run requested 32-word chunks and received 0x80-periodic session residue (the fire's thunk read-back dwords were in the "data") — every bulk read in this repo now chunks at ≤ 18 |
| Q3 handler table (SRAM `0x746C`, stride 8) | the fw's internal message surface | **dumped 2026-08-25: 147 handlers, premise validated** (secure msgs distinct + msg 0x01 == TestMessage). Flags field: `0x6` normal / `0x201` gated secure cluster / `0x206` a second gated group (0x71/0x72/0xA7/0xA8). **Msg 0x21 → `0x249DC` (+0x319 past the dom7 caller `0x246C3`) is the #1 power-message suspect.** Undocumented secure siblings 0x27/0x2D–0x2F exist. Alias region at 0xAA+ |

Power/PG/harvest cluster, MMIO spellings only (BASE_IDX 1):

| register | MMIO byte |
|----------|-----------|
| `mmUVD_PGFSM_CONFIG` / `mmUVD_PGFSM_STATUS` | `0x1F800` / `0x1F804` |
| `mmUVD_POWER_STATUS` | `0x1F810` |
| `mmCC_UVD_HARVESTING` | `0x1F81C` |
| `mmUVD_PG_IND_INDEX` / `mmUVD_PG_IND_DATA` | `0x1F814` / `0x1F818` |
| `mmUVD_DPG_LMA_CTL` / `_DATA` / `_MASK` | `0x1F844`–`0x1F84C` |
| `mmUVD_MASTINT_EN` / `mmUVD_STATUS` | `0x20000` / `0x201BC` |
| `mmUVD_CGC_GATE` / `mmUVD_CGC_CTRL` | `0x1FFA8` / `0x1FFB0` |
| `mmUVD_SUVD_CGC_GATE` / `_CTRL` | `0x20E90` / `0x20E98` |

(An SMN/fabric column is deliberately **absent** — no slice-relative spelling
is known for any of these. If the `--vcn-power-regs` slice dump shows a
pattern at `+0x00/+0x04/+0x10/+0x1C`, that SEG0-relative hypothesis gets
tested then, not before.)

## License / attribution

The exploit library this tool drives is
[bc250-smu-unlock](https://github.com/rw-r-r-0644/bc250-smu-unlock) by
rw-r-r-0644 (MIT). `enable_vcn.py` itself is provided as-is for BC250
hardware-enablement research.
