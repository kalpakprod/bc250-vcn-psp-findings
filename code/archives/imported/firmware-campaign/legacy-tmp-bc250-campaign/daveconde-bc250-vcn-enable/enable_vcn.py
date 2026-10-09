#!/usr/bin/env python3
"""
enable_vcn.py -- execute the EXACT BC250-community ("Discord") VCN
enable sequence inside the SMU, using https://github.com/rw-r-r-0644/bc250-smu-unlock
(BC250 BIOS 3 / Robin1, PMFW 0.58.6.0).

THE SEQUENCE (verbatim -- this is all the code we install, nothing more):

    entry   a1, 0x20
    movi.n  a10, 0x16
    call8   0x00023744
    movi.n  a10, 0x17
    call8   0x00023744
    movi.n  a10, 0x18
    call8   0x00023744
    retw.n

FUN_00023744(slot) re-programs the domain-6 (VCN) per-slot clock for slots
0x16/0x17/0x18 (soc_clk_program_slot @0x2362c) -- the exact mirror of the
firmware's own teardown_dom6.

HOW IT IS EXECUTED (everything SMU-side through the unlock library, over PCI):

  1. unlock()      -- the library's Q2 ring-overflow exploit opens the
                      secure-access debug cluster (everything below needs it).
  2. install       -- the 20 sequence bytes are written to SMU scratch SRAM
                      0x3ff00 with smu_write32() (gated debug write, msgs
                      0x28/0x29, carried over the PCI config transport
                      0xB8/0xBC) and verified by read-back.
  3. repoint       -- the reserved Queue-3 msg-0x61 handler pointer (SMU SRAM
                      0x776c) is set to 0x3ff00, again via smu_write32().
                      The fw dispatcher calls that pointer (callx8) when it
                      sees msg 0x61 -- the only native execution vector the
                      SMU has; the sequence itself is entered with a fresh
                      frame (entry a1,0x20) and ignores the message context.
  4. fire          -- the unlock library's own Q3 mailbox send rings the
                      fw's doorbell: send_message(3, 0x61) writes rsp := 0,
                      arg0..arg5 := 0, cmd := 0x61 (SMN 0x03B10A20) over
                      the library's own flock-guarded PCI-config transport
                      (0xB8/0xBC) -- the byte-identical register sequence
                      the earlier raw fire used, now issued through the
                      library API. The Discord sequence does NOT complete
                      the mailbox protocol (it builds its own frame and
                      returns without setting a response), so the send's
                      response poll is EXPECTED to end in SmuTimeout ~5s
                      later -- that wait is the dispatch wait. (Same
                      pattern as the sibling tools' msg-0x61 fires.)
  5. engage        -- FUN_00023744's enable dance (+0x08=1 per slot) only runs
                      when a divider actually changes; on a converged table it
                      is skipped and the fw steady state leaves enable=0. This
                      step engages the three dom6 per-slot clock ENABLE bits
                      with the SAFE bounded window write (README 2.4) and then
                      reads the dom6 power sequencer (cmd/rail/status/ctrl) --
                      the authoritative SMU-side power oracle. Skip: --no-enable-engage.
  6. --direct-load  -- OPTIONAL stage, the one that bypasses the TEE
                      entirely: stage the navi10 VCN fw in VRAM OURSELVES and
                      boot VCN from userspace, register-for-register the way
                      the kernel's AMDGPU_FW_LOAD_DIRECT path does it
                      (amdgpu_vcn_resume + vcn_v2_0_mc_resume + non-DPG
                      vcn_v2_0_start). Proof = the driver's own ring test:
                      the fw must flip mmUVD_SCRATCH9 0xCAFEDEAD->0xDEADBEEF
                      by executing a ring packet fetched from OUR VRAM ring.
                      Needs amdgpu LOADED only as the raw MMIO/VRAM transport
                      (amdgpu_regs / amdgpu_vram); the dec-ring doorbell is
                      rung by writing the GPU's PCI BAR2 directly.
    7. --smn-vcn-probe -- OPTIONAL stage: ONE SMN read THROUGH the SMU (Q3
                        msg 0x2A, the "mem64 window"). The fw MASKS its
                        address arg to 20 bits and accesses it at SMU-local
                        0x01100000 + (arg & 0xFFFFF) (FUN_000235c8 decode)
                        -- the window can NEVER express a 0x024xxxxx fabric
                        address. WHICH fabric frame the SMU-local window maps
                        onto (SMN 0x011xxxxx NBIO frame vs SMN 0x000xxxxx
                        low frame vs SMU-private) is UNRESOLVED -- the probe
                        prints both candidate effective addresses. The 0x1F8xx
                        arg family is refused (dead responder under both
                        hypotheses -> the documented hard wedge).
    8. --vcn-power-regs -- STANDALONE diagnostic: probe the VCN FABRIC SLICE
                        (0x02403000..+0x40) plus THM/GC slice heads through
                        the ONE CPU-side transport proven to take full 32-bit
                        SMN addresses: the PCI-config 0xB8/0xBC window of
                        the root device (00:00.0, the library's own
                        transport). Step 0 also runs the FRAME DISCRIMINATOR
                        (core mask + dom6 sequencer at BOTH full spellings;
                        MEASURED 2026-08-25: the dom6 match at SMN
                        0x0006D1xx settles the frame = LOW) plus the
                        config-read LIVE-TRACKING cross-check. Config
                        WRITES to the sequencer are measured IGNORED
                        (2026-08-25: host fabric stores dropped; the
                        transport itself is source-verified) -- the
                        fw-window debug-write path (plain --manual-powerup)
                        is the live store vehicle; --config-writes now
                        serves as the block's write-capability probe.
                        TRANSPORT FIX 2026-08-24 evening: the old route P
                        mmap'd BAR0 and used bytes 0x38/0x3C as
                        PCIE_INDEX2/DATA2 -- but BAR0 is the 256MB VRAM
                        aperture, NOT the register file (July probe Test B);
                        every "window read" it ever made was a VRAM read
                        (uniform 0xb9f53acd; the INDEX2 "echo" passed because
                        it echoed into VRAM). The real register file is BAR5
                        (512KB), and reads through ITS PCIE_INDEX2/DATA2
                        window HANG the board on VCN addresses (July #1/#3).
                        The fabric slices are NOT register-file mirrors (no
                        VCN register uses BASE_IDX 2; GC's 1KB slice cannot
                        hold its ~35KB register file; no 0x024-frame writes
                        exist anywhere in the BIOS ROM). Ladder: proven
                        sanity reads -> frame discriminator -> THM slice ->
                        GC slice -> VCN slice, stopping if the frame proves
                        unreadable. Residual risk: first-ever 0x024-frame CPU
                        reads -- small cold-cycle risk. Route W stays retired.

REGISTER-ACCESS POLICY (2026-08-20, revised 2026-08-24): every SMU-side
register access in this tool flows through the unlock library --
smu.smu_read()/smu_write32() for SMU SRAM and its 0x0110000+(smn&0xFFFFF) SMN
data-window alias, smu.sec_smn_read32() for the mem64 window (NBIO frame
only -- 20-bit masked, see item 7), smu.send_message()/alive()/
secure_access_enabled() for the mailboxes, all over the library's own PCI
config transport (root device 00:00.0, config 0xB8/0xBC -- full 32-bit SMN
addressing). Route P of --vcn-power-regs rides that same transport for its
fabric-slice reads. The only non-library accesses left are the GPU-side
transports: --direct-load's amdgpu_regs/amdgpu_vram debugfs + the PCI BAR2
doorbell write. Those CANNOT flow through the SMU -- every SMU route into
the VCN register block is a measured hard wedge (CPU MMIO all-ones, PCIE
iso-clamp, msg 0x2A stall, transfer-engine stall, all 2026-08-20) -- so they
ride the kernel/GPU paths instead.

PSP LOAD_IP_FW (REMOVED 2026-08-20): the former --load-fw stage submitted a
LOAD_IP_FW of navi10_vcn (fw_type 13) through the kernel's own PSP GPCOM
ring (machinery inlined from psp_inject.py). It ran cleanly on hardware and
the TEE answered TEE_ERROR_ITEM_NOT_FOUND after 0.001s with fw_addr 0 -- the
image was never examined; identical to the driver's boot-time verdict. The
console TEE has no fw_type-13 slot (Wall B, confirmed at BOTH layers). The
code is deleted; --direct-load (stage 6 above) is the vehicle of record --
it never asks the TEE at all.

KNOWN RISK (measured on this project's headless card, README_bc250_vcn_master
§2.7): FUN_00023744/0x2362c can HARD-WEDGE the SMU (unbounded VCLK/DCLK polls
when there is no live clock rail). Run this ONLY from a shell/box you can
COLD POWER-CYCLE. Prechecks below abort on the worst-known variant
(dom6 state byte 0x00 -> the auto-power branch calls FUN_00023b14(6,1)).

USAGE (target box, library cloned next to this file or BC250_SMU_PATH set):
    sudo python3 enable_vcn.py             # full run: fire the sequence
    sudo python3 enable_vcn.py --no-fire   # install + prechecks only
    sudo python3 enable_vcn.py --verify    # read-only state dump
    sudo python3 enable_vcn.py --force     # proceed despite state==0
    sudo python3 enable_vcn.py --direct-load
                                                  # fire, then stage the VCN fw
                                                  # in VRAM OURSELVES and boot
                                                  # VCN from userspace (no PSP,
                                                  # no TEE, no kernel VCN code);
                                                  # proof = the driver's own ring
                                                  # test (SCRATCH9 DEADBEEF).
                                                  # amdgpu must be loaded (raw
                                                  # MMIO/VRAM transport only)
    --keep-vcn                                      # after a successful proof, do
                                                  # NOT park VCN (leave fw running)
    --no-enable-engage                             # skip the post-fire ENABLE
                                                  # (+0x08)=1 engage + dom6
                                                  # sequencer readout (default:
                                                  # engage all three slots)
    --smn-vcn-probe [--smn-vcn-addr A]           # one SMN read THROUGH the SMU
                                                  # (msg 0x2A). NBIO-frame targets
                                                  # only: the fw masks the arg to
                                                  # 20 bits (0x01100000 window) --
                                                  # a 0x024xxxxx arg silently
                                                  # aliases into NBIO. Wedge risk
                                                  # on dead NBIO offsets (opt-in)
    --vcn-power-regs                             # FABRIC-SLICE PROBE: THM/GC/VCN
                                                  # slices via the PCI-config
                                                  # 0xB8/0xBC SMN window (the
                                                  # library transport, full
                                                  # 32-bit addresses). Ladder
                                                  # stops if the 0x024 frame
                                                  # reads dead. First-ever
                                                  # 0x024-frame CPU reads: small
                                                  # cold-cycle risk (see item 8)
    --vcn-power-regs-w                           # ALSO run route W (SMU data
                                                  # window 0x0111F8xx): MEASURED
                                                  # HARD WEDGE, cold-cycle only --
                                                  # do not run route W again
    --manual-powerup [--config-writes]         # manual dom6 rail power-up
                                               # (--config-writes: stores and
                                               # read-backs through the PCI-config
                                               # window at the runtime-discriminated
                                               # full fabric spelling -- a physical
                                               # path the night-1 'sat dirty' fw-window
                                               # stores never touched)
    --manual-powerup [--thunk-writes]            # manual dom6 rail power-up
                                                  # (fw-exact FUN_00023b14 decode,
                                                  # BOUNDED host-side polls --
                                                  # cannot wedge). FIXED step [0]
                                                  # releases ctrl gate bits 0/1/2
                                                  # (the fw's dom7 caller writes 0
                                                  # to the whole reg). Follow with
                                                  # --vcn-power-regs: the fabric-
                                                  # slice probe is the arbiter
                                                  #   --manual-powerup --thunk-writes        # same, but the
                                                  # ctrl/cmd/rail stores ride the INLINE store thunk
                                                  # (the fw's own store sequence executed in the
                                                  # msg-0x61 handler thunk at the preflight depth;
                                                  # mailbox-OK = the store executed in firmware).
                                                  # NIGHT-4: both CALL-vehicles (0x233e8, 0x235c8)
                                                  # wedged the SMU; the inline vehicle bypasses
                                                  # depth/gate/fallback entirely
"""
import os
import struct
import sys
import time
import argparse

BC250_SMU_PATH = os.environ.get(
    "BC250_SMU_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "bc250-smu-unlock"))
sys.path.insert(0, BC250_SMU_PATH)

from bc250_smu import Bc250Smu, SmuError, SmuTimeout          # noqa: E402
from bc250_smu.api import DEFAULT_QUEUE_ADDRS                 # noqa: E402
from unlock import unlock                                     # noqa: E402

# ---------------- BIOS-3 / Robin1 offsets (proven) ----------------
THUNK_ADDR   = 0x0003ff00        # zero-padded tail of SMU SRAM (0x3ff00..0x40000)
FUN_SLOT_CLK = 0x00023744        # FUN_00023744(slot): re-program slot clock
SLOT         = 0x61              # reserved ("No Handler") Queue-3 message id
SLOT_FUNCPTR = 0x746c + (SLOT - 1) * 8   # = 0x776c, its handler-table entry

# domain-6 (VCN) live state (read via the unlocked debug path)
DOM6_STATE_WORD = 0x0000f714     # low byte = dom6 state (factory 0x01 here)
SLOT_ARRAY_BASE = 0x0000f710     # slot array, 28-byte stride
SLOT_STRIDE     = 28
SLOT_DOM_OFF    = 128            # owning domain byte
SLOT_CUR_OFF    = 130            # current clock value byte
SLOT_REMEM_OFF  = 134            # "remembered" clock value byte
SLOT_GATE_OFF   = 148            # dword: this slot's clock-gate SMN address

WIN_BASE = 0x01100000            # fw's own SMN data window: 0x1100000+(addr&0xFFFFF)
                                  # (a 1MB window into the 0x01100000 frame ONLY --
                                  #  it cannot reach VCN's 0x02403000 fabric frame)
DEGEN    = (0x1f800, 0x1f820)    # 0x1F804/0x1F810 window reads (0x0111F8xx) WEDGE the
                                  # SMU: no responder at NBIO-frame offset 0x1F8xx
                                  # (unrouted -- 0x1F8xx was never VCN's SMN address)
VCN_SLOTS = (0x16, 0x17, 0x18)

# dom6 (VCN) power-sequencer block registers (dom6 block base 0x6d000; decode
# from vcn_fullon_bios3.py / FUN_00023b14). cmd/status/rail are sequencer VIEW
# fields (writes are vacuous, README 2.7) but their VALUES are what the fw
# itself reads to decide power state -- rail == 0 means the dom6 power rail was
# NEVER commanded up, no matter what the clock files say. ctrl carries one GATE
# bit per dom6 slot (July baseline: 0x02 = slot 0x17's clock gated).
DOM6_BLOCK_REGS = (("cmd",    0x0006d17c),
                   ("rail",   0x0006d184),
                   ("status", 0x0006d190),
                   ("ctrl",   0x0006d0f8))

# ctrl gate bits <-> dom6 clock slots (set = that slot's domain-level clock
# GATED). These are LATCHED commands, not auto-tracking status -- proven
# 2026-08-20/21: bit1 survived two clock restores + the enable engage, and
# ctrl = 0x02 (not 0x07) says the fw's teardown (which ORs all three bits)
# never ran. The fw's own dom7 caller @0x246c3 writes 0 to the WHOLE reg
# before a power-up -- manual_powerup_dom6 step [0] mirrors that.
# RESOLVED 2026-08-25: step [0]'s fw-window store LANDED (0x02 -> 0x00) and
# persisted across processes -- the gate is released within the SMU session;
# a cold boot restores the factory 0x02.
CTRL_SLOT_BITS  = ((0, 0x16), (1, 0x17), (2, 0x18))

# manual dom6 rail power-up (FUN_00023b14 decode; see manual_powerup_dom6)
CMD_UP          = 0x00000001     # cmd  0x6d17c bit0: power-up request
RAIL_UP         = 0x00010000     # rail 0x6d184 bit16: rail-up (self-clears)
FUN_SMN_WRITE   = 0x000235c8     # fw's REAL window-store fn. RE-DECODED 2026-08-21 from
                                 # smu_fw_robin_5: entry-verified @0x235c8, called 30+ times
                                 # by the fw itself (clock/gate writers). Semantics: mask the
                                 # addr with 0xFFFFF, add window base 0x010ffe00, s32i at
                                 # +512 -> store at 0x01100000+(addr&0xFFFFF), with an
                                 # fn_2a018(4)-gated fast path + ranged slow route. THE OLD
                                 # 0x233e8 WAS NEVER A FUNCTION: it is a mid-function address
                                 # inside the fn @0x23370 (one byte into a sync!), reached by
                                 # no call and no pointer table anywhere in the image. A
                                 # call8 to it ran garbage-register code ending in a wild
                                 # store (s32i.n a9, a6, 44 through never-initialized a6) --
                                 # THAT was the 2026-08-21 wedge, both nights, regardless of
                                 # args. The fe4/fa8 tail is proven CORRECT (TestMessage
                                 # @0x1b3a8 and 500+ fw call sites use exactly our idiom:
                                 # mov.n a10,a2 / call8 0xfe4 / mov.n a10,a2 / movi.n a11,1 /
                                 # call8 0xfa8)
                                 # MEASURED 2026-08-21 night-4: calling this fn
                                 # via the thunk ALSO WEDGES the SMU (benign
                                 # idempotent target) -- its fn_2a018 head (an
                                 # SMN window read) runs at depth +3, one frame
                                 # deeper than anything ever proven. Kept for
                                 # decode provenance; stores ride the INLINE
                                 # thunk (build_inline_store_thunk) now.
FN_SET_RESPONSE = 0x00000fe4     # fn_fe4(ctx, value): set mailbox response
FN_COMPLETE     = 0x00000fa8     # fn_fa8(ctx, 1): mark message complete

# The ONE window OFFSET the mem64 window (Q3 msgs 0x2A read / 0x2B+0x2C write)
# is PROVEN to reach: 0x5A870, the CPU core-presence mask (unlock.py
# PROBE_ADDR, set_core_mask.py MASK_REG -- both directions proven on the
# card). The window's reach is otherwise NARROW and address-selective: the
# MP1 mailbox region 0x03B10xxx is NOT reachable from it (a read there stalls
# the SMN bus -> whole-SMU wedge, measured 2026-08-20), and the 0x1F8xx
# family likewise (July). Note: 0x5A870 is the WINDOW offset; its full SMN
# spelling (0x0115A870 vs 0x0005A870) is unresolved -- see CORE_MASK_SMN.
# Treat any other address as a wedge gamble.
SMN_PROVEN_ADDR = 0x0005A870

# ---------------- VCN power/harvest cluster ----------------
# navi10 VCN0's power/harvest registers (all BASE_IDX 1, kernel-verified
# 2026-08-24 against vcn_2_0_0_offset.h, torvalds master): UVD_PGFSM_CONFIG
# 0x1F800, UVD_PGFSM_STATUS 0x1F804, UVD_POWER_STATUS 0x1F810,
# CC_UVD_HARVESTING 0x1F81C -- MMIO byte offsets ((0x7E00 + mmREG) * 4).
#
# ADDRESS-SPACE MODEL v3 (2026-08-25 -- kernel-verified; supersedes v2):
#   1. MMIO byte offset (the BAR5 register file, kernel rmmio): reachable via
#      the amdgpu_regs debugfs route -- but CPU reads of the VCN segment HANG
#      the board while the island is dead (July x3: userspace BAR5, UMR, both
#      hung on the first read).
#   2. MMIO offsets are NOT SMN addresses (kernel-verified counter-example):
#      every IP's registers exist at SEVERAL spellings with different numerics.
#      The kernel talks to this card's MP1 (SMU) at MMIO 0x058A08 =
#      (MP1 SEG0 0x16000 + mmMP1_SMN_C2PMSG_66 0x282 dwords) * 4, while the
#      same PMFW's mailbox queues live at SMN 0x03B10A20 (the library
#      transport, hardware-proven). Only the SMALL discovery base values
#      (<= 0x10400 dwords) are MMIO spellings.
#   3. SMN fabric frame 0x024xxxxx: nearly every IP in the ROM's discovery
#      table carries one small (1-2 KB) slice here (VCN 0x02403000, GC
#      0x02402c00, THM 0x02400c00, MMHUB 0x02408800, MP0/MP1 0x0243fc00, ...;
#      full map in vcn2_register_map.md). CRITICAL: no VCN 2.0 register uses
#      BASE_IDX 2 (all 467 header entries are 0 or 1) -- the kernel derives no
#      address from SEG2 on ANY ASIC; the slices are too small to be
#      register-file mirrors (GC's MMIO file is ~35 KB, its slice 1 KB), and a
#      full-ROM scan finds NO register writes into the frame (the only
#      0x024xxxxx literals in the 16 MB image are the discovery table itself
#      @0x981a9c-0x981d60 -- the earlier "the BIOS GNB table programs THM/CLK
#      through their slices" claim is RETRACTED). Slice contents are UNKNOWN;
#      0x02403010 is simply the 5th dword of VCN's slice, NOT a known
#      spelling of mmUVD_POWER_STATUS. Route P dumps the slice to find out.
#   4. SMU mem64/data window (Q3 msgs 0x2A read / 0x2B+0x2C write; transfer
#      engine reads at the same offset): the fw masks every target to 20 bits
#      and accesses it at SMU-local 0x01100000 + (target & 0xFFFFF)
#      (FUN_000235c8 decode). The 20-bit MASK is fact; which fabric frame the
#      window maps onto is NOT established -- SMN 0x011xxxxx (NBIO frame, the
#      v2 assumption), SMN 0x000xxxxx (low frame), or an SMU-private bus.
#      Either way the mask makes it structurally unable to express 0x024xxxxx,
#      and it cannot reach the PMFW mailbox frame 0x03B1xxxx (measured stall,
#      2026-08-20). The 2026-08-24 "0x02403010 fast-0" mem64 read was the
#      MASKED alias (0x01103010 under the NBIO hypothesis / 0x00003010 under
#      the low-frame one) -- NOT a VCN access; retracted as VCN evidence.
#      0x1F8xx args (-> 0x0001F8xx under the corrected model) are the
#      documented wedge. RESOLVED 2026-08-25 (route P step 0, on hardware):
#      the dom6 sequencer matches at 0x0006D1xx (status=0x01010101 /
#      ctrl=0x02 -- distinctive) while 0x0116D1xx reads dead-zero -> the
#      window maps to the LOW frame. The core mask read 0x77 at BOTH
#      spellings (alias or coincidence -- ambiguous on its own). Dead
#      config reads on this box return 0x00000000 (THM/GC slices,
#      0x0116D1xx), not the 0xffffffff July #5 suggested.
# The ONE CPU-side transport proven to take FULL 32-bit SMN addresses on this
# box is the PCI-config window 0xB8/0xBC of the root device 00:00.0 (the
# library's own transport; live at SMN 0x03B10A20 on every mailbox send).
# Route P rides it. WRITE asymmetry (measured 2026-08-25): config stores to
# the MP1 mailbox region land (every send), but config stores to the dom6
# sequencer at SMN 0x0006D1xx are IGNORED (ctrl 0x02->0x00 read back 0x02
# immediately; transport source-verified write_smu_reg(reg, value) -- the
# stores were correctly issued). The sequencer sub-block is fabric-READABLE
# but host-fabric-write-protected; its slot sub-registers take fw-window
# (SMU-executed debug-write) stores -- the engage proved that -- so the
# debug-write path is the live store vehicle for the whole 0x06dxxx block.
VCN_SMN_BASE   = 0x02403000            # VCN's fabric slice base (discovery base_address[2];
                                       # ROM- and kernel-verified: identical to renoir's
                                       # UVD0_BASE__INST0_SEG2. Slice <= 2 KB (next IP's
                                       # slice starts at 0x02403800); contents UNKNOWN --
                                       # no vcn_2_0_0_offset.h register carries BASE_IDX 2,
                                       # so the kernel derives no address from it, ever.)
THM_SMN_BASE   = 0x02400c00            # THM slice (live IP -- route-P ladder step)
GC_SMN_BASE    = 0x02402c00            # GC slice (live IP -- route-P ladder step)
# The core-presence mask: PROVEN reachable at mem64/data-WINDOW offset 0x5A870
# (unlock.py reads and set_core_mask.py reads AND writes it through the window).
# Its FULL 32-bit SMN spelling is NOT yet proven: the window's math is
# "SMU addr 0x01100000 + (target & 0xFFFFF)" (fw-decoded), but WHICH fabric
# frame that SMU-local window maps onto is unresolved -- 0x0115A870 if the
# window mirrors the SMN 0x011xxxxx NBIO frame (model v2's assumption) or
# 0x0005A870 if it mirrors the low SMN frame. Route P step 0 reads BOTH
# spellings full-width through the config window and lets the 0x77/0xFF value
# decide. (The old route-P "0x0115A870 confirmed" readings were BAR0 VRAM
# artifacts -- retracted with the 2026-08-24 transport fix.)
CORE_MASK_SMN     = 0x0115A870         # hypothesis A: window == NBIO frame
CORE_MASK_SMN_ALT = 0x0005A870         # hypothesis B: window == low frame

# dom6 power-sequencer fabric spellings for the same discriminator: the rail
# register reads live at window offset 0x6D184 (rd_win, every run); if the
# sequencer block is fabric-visible at all, the full-width candidates are
# 0x0116D184 (window == NBIO frame) or 0x0006D184 (window == low frame).
DOM6_WINDOW_BASE_A = 0x01100000        # hypothesis A full-spelling base
DOM6_WINDOW_BASE_B = 0x00000000        # hypothesis B full-spelling base

# The MMIO spellings, kept for reference/direct-load docs (address space 1).
# Route P does NOT derive fabric addresses from these (see model v3 above).
VCN_PWR_CLUSTER  = (("UVD_PGFSM_CONFIG",  0x0001f800),
                    ("UVD_PGFSM_STATUS",  0x0001f804),
                    ("UVD_POWER_STATUS",  0x0001f810),
                    ("CC_UVD_HARVESTING", 0x0001f81c))
# Legacy 0x1F8xx-as-SMN spellings -- kept ONLY for the retired route W,
# which is structurally unable to reach VCN's real fabric frame anyway.
UVD_POWER_STATUS_SMN = 0x0001f810
UVD_HARVESTING_SMN   = 0x0001f81c

# ---------------- Xtensa encoders (calibrated against Robin1) ----------------
def enc_entry(as_, frame_bytes):
    """ENTRY as, frame_bytes -- the imm12 field is the frame size divided by 8.

    Disassemblers display the SCALED size: 'entry a1, 0x20' is bytes
    36 41 00 (imm12 = 4), the fw's most common prologue (1089 occurrences
    in the Robin1 image; soc_clk_program_slot opens 36 61 00 = entry a1,
    0x30). Encoding the displayed 0x20 verbatim emits 36 01 02, which is
    entry a1, 0x100 -- an 8x too deep stack frame. (Discord bug report,
    2026-08-20; verified against the fw image, fixed same day.)
    """
    if frame_bytes % 8 or not (0 <= frame_bytes <= 0xFFF * 8):
        raise ValueError(f"entry frame must be an 8-byte multiple <= {0xFFF * 8}: {frame_bytes}")
    return (0x36 | (as_ << 8) | ((frame_bytes // 8) << 12)).to_bytes(3, "little")

def enc_movi_n(dest, imm):
    """MOVI.N at, imm7  (bits[15:12]=imm[3:0], [11:8]=at, [6:4]=imm[6:4], [3:0]=0xC)."""
    if not (-0x40 <= imm < 0x80):
        raise ValueError(f"movi.n imm out of range: {imm}")
    v = imm & 0x7F
    W = ((v & 0xF) << 12) | (dest << 8) | (((v >> 4) & 7) << 4) | 0xC
    return W.to_bytes(2, "little")

def enc_call8(pc, target):
    """CALL8: W = (off18 << 6) | (2 << 4) | 5, target = ((pc+4)&~3) + (off<<2)."""
    off = (target - ((pc + 4) & ~3)) >> 2
    if not (-0x20000 <= off < 0x20000):
        raise ValueError(f"call8 0x{pc:x}->0x{target:x} out of range")
    return (((off & 0x3FFFF) << 6) | (2 << 4) | 5).to_bytes(3, "little")

RETW_N = bytes.fromhex("1df0")   # retw.n

def build_sequence(base=THUNK_ADDR, fn=FUN_SLOT_CLK):
    """The Discord sequence, byte-exact:
        entry a1,0x20; movi.n a10,0x16; call8 fn; (0x17); (0x18); retw.n
    (each call8 encodes to a different word because it is pc-relative)."""
    b = bytearray()
    b += enc_entry(1, 0x20)                     # entry   a1, 0x20
    for slot in (0x16, 0x17, 0x18):
        b += enc_movi_n(10, slot)               # movi.n  a10, 0x16/0x17/0x18
        b += enc_call8(base + len(b), fn)       # call8   0x00023744
    b += RETW_N                                 # retw.n
    return bytes(b)

# self-test: the assembled bytes are deterministic for the default placement
_EXPECTED = bytes.fromhex("364100" "1c6a" "e583e3" "1c7a" "a583e3"
                          "1c8a" "6583e3" "1df0")
assert build_sequence() == _EXPECTED, "sequence assembly mismatch"

# ---------------- unlocked-SMU access helpers (no mailbox API) ----------------
def rd_sram(smu, addr, words=1):
    """SMU SRAM read via the transfer engine (gated debug path)."""
    return int.from_bytes(smu.smu_read(addr, words), "little")

def rd_sram_byte(smu, addr):
    return (rd_sram(smu, addr & ~3) >> ((addr & 3) * 8)) & 0xFF

def rd_win(smu, smn, label=""):
    """SMN read via the fw's own data window (0x1100000+addr&0xFFFFF)."""
    if DEGEN[0] <= smn < DEGEN[1]:
        print(f"    [!] refusing degenerate read {label} 0x{smn:x}")
        return None
    try:
        return int.from_bytes(smu.smu_read(WIN_BASE + (smn & 0xFFFFF), 1), "little")
    except Exception as e:
        print(f"    [!] window read 0x{smn:x} {label}: {e.__class__.__name__}")
        return None

def gate_of(smu, slot):
    """This slot's clock-gate SMN base, read from the fw's own slot table."""
    return rd_sram(smu, SLOT_ARRAY_BASE + slot * SLOT_STRIDE + SLOT_GATE_OFF)

def _fx(v):
    return "ERR" if v is None else f"0x{v:08x}"

def dump_slots(smu, tag):
    print(f"[*] per-slot state, {tag}:")
    out = {}
    for s in VCN_SLOTS:
        e = SLOT_ARRAY_BASE + s * SLOT_STRIDE
        dom, cur, rem = (rd_sram_byte(smu, e + o) for o in
                         (SLOT_DOM_OFF, SLOT_CUR_OFF, SLOT_REMEM_OFF))
        g = gate_of(smu, s)
        reg = {off: rd_win(smu, g + off, f"slot0x{s:02x}+{off:#x}")
               for off in (0x00, 0x08, 0x14, 0x24)}
        out[s] = (dom, cur, rem, g, reg)
        en, st = reg[0x08], reg[0x24]
        print(f"    slot 0x{s:02x}  dom={dom}  table: cur(+130)={cur:3d} "
              f"remembered(+134)={rem:3d}   gate@0x{g:06x}")
        print(f"        +0x00 clock   = {_fx(reg[0x00])}"
              f"    +0x08 enable = {_fx(en)}"
              f"{'ON' if en is not None and en & 1 else 'off' if en is not None else ''}"
              f"    +0x14 divider = {_fx(reg[0x14])}"
              f"    +0x24 status = {_fx(st)}"
              f"{' READY(bit16)' if st is not None and st & 0x10000 else ''}")
    return out

def diff_slots(before, after):
    """Report every table/register change the sequence produced."""
    print("[*] changes (BEFORE -> AFTER):")
    n = 0
    for s in VCN_SLOTS:
        dom, cur, rem, g, reg = before[s]
        dom2, cur2, rem2, g2, reg2 = after[s]
        for name, a, b in (("table +130 cur", cur, cur2),
                           ("table +134 remembered", rem, rem2)):
            if a != b:
                print(f"    slot 0x{s:02x} {name:<22} {a} -> {b}")
                n += 1
        for off, name in ((0x00, "reg +0x00 clock"), (0x08, "reg +0x08 enable"),
                          (0x14, "reg +0x14 divider"), (0x24, "reg +0x24 status")):
            if reg[off] != reg2[off]:
                print(f"    slot 0x{s:02x} {name:<22} {_fx(reg[off])} -> {_fx(reg2[off])}")
                n += 1
    if not n:
        if all(before[s][1] == before[s][2] for s in VCN_SLOTS):
            print("    (nothing changed -- table was already CONVERGED")
            print("     (cur == remembered on every slot): the sequence")
            print("     re-commits remembered values, so a no-op here is BY")
            print("     DESIGN. It does NOT mean the sequence did not run --")
            print("     the fire/liveness path above is the execution proof.)")
        else:
            print("    (nothing changed -- sequence may not have executed)")

# ---------------- SMU-side power levers + oracle (no VCN register reads) ----------------
def engage_slot_enables(smu, after):
    """Engage the three dom6 per-slot clock ENABLE bits (gate+0x08 = 1).

    The fire's own enable dance only runs when a divider changes; steady state
    leaves enable = 0. This is the bounded data-window write proven SAFE and
    LIVE in vcn_enable_bits.py (README 2.4): smu_write32 to the window alias,
    read-back verify, no thunk, no poll loops, SMU survives. Watch the status
    reaction in the dump that follows (2026-08-20 baseline: 0x53 -> 0x50 on
    slots with a programmed clock).
    """
    print("[*] engaging dom6 per-slot clock ENABLE (+0x08)=1 (SMU window write):")
    for s in VCN_SLOTS:
        g = after[s][3]                      # this slot's gate SMN base
        old = rd_win(smu, g + 0x08, "enable")
        try:
            smu.smu_write32(WIN_BASE + ((g + 0x08) & 0xFFFFF), 1)
        except Exception as e:
            print(f"    slot 0x{s:02x}: window write failed ({e.__class__.__name__})")
            continue
        time.sleep(0.02)
        new = rd_win(smu, g + 0x08, "enable")
        if new is None:
            print(f"    slot 0x{s:02x}: {_fx(old)} -> read-back FAILED")
        elif new & 1:
            print(f"    slot 0x{s:02x}: {_fx(old)} -> {_fx(new)}  LANDED")
        elif old is not None and new == old:
            print(f"    slot 0x{s:02x}: {_fx(old)} -> {_fx(new)}  UNCHANGED -- write sat "
                  "dirty in the mirror; --manual-powerup --thunk-writes is the "
                  "fw-sync path")
        else:
            print(f"    slot 0x{s:02x}: {_fx(old)} -> {_fx(new)}  (unexpected value)")

def dom6_block_report(smu):
    """dom6 power-sequencer readout -- the authoritative SMU-side power oracle.

    Pure SMU-local window reads (zero wedge risk). Register semantics decoded
    from the fw's FUN_00023b14 (see vcn_fullon_bios3.py) + the 2026-08-20
    --probe-domains cross-domain baseline:
      cmd    0x6d17c: bit0 = up-request, bit4 = down-request; SELF-CLEARS when
                      the FSM takes them (cmd=0 on every domain incl. powered
                      dom0-3 and down dom7 -- idle, carries no state)
      rail   0x6d184: write 0x10000 = rail-up cmd, bit16 SELF-CLEARS when
                      taken; rail=0 is the IDLE state on powered dom0-3 too
                      (probe 2026-08-20) -- it does NOT mean "never commanded"
      status 0x6d190: bit8 = up-ack (persists), bit12 = down-ack (persists);
                      dom0-6 all read 0x01010101 (up-residue), dom7 (the one
                      fw-commanded domain) reads 0x01011010 (down-residue)
      ctrl   0x6d0f8: bit0 = gate (fw clears it before power-up); higher bits
                      per-domain clock-ctrl
    """
    print("[*] dom6 (VCN) power sequencer (SMU-side power oracle):")
    vals = {}
    for name, addr in DOM6_BLOCK_REGS:
        vals[name] = rd_win(smu, addr, name)
        print(f"    {name:<6} @0x{addr:06x} = {_fx(vals[name])}")
    rail, st, ctrl = vals.get("rail"), vals.get("status"), vals.get("ctrl")
    if st is not None:
        if st & 0x100:
            print("    -> status bit8 SET (up-ack residue): dom6 matches the")
            print("       powered dom0-5 baseline (probe 2026-08-20); only the")
            print("       fw-commanded dom7 differs (bit12 down-ack, state 0).")
        if st & 0x1000:
            print("    -> status bit12 SET (down-ack residue): this domain was")
            print("       commanded DOWN through the fw path.")
    if ctrl is not None:
        held = [f"slot 0x{s:02x} (bit{b})" for b, s in CTRL_SLOT_BITS
                if ctrl >> b & 1]
        if held:
            print(f"    -> ctrl = 0x{ctrl:08x}: domain-level clock GATE held on "
                  + ", ".join(held))
            print("       (bits 0/1/2 <-> slots 0x16/0x17/0x18, set = gated; these")
            print("       are LATCHED commands, not auto-tracking status -- bit1")
            print("       survived two clock restores + the enable engage, and")
            print("       0x02 != 0x07 says the fw's teardown (ORs all three) NEVER")
            print("       ran. The fw's dom7 caller writes 0 to the WHOLE reg")
            print("       before power-up; --manual-powerup step [0] releases all")
            print("       three bits.)")
        elif ctrl == 0:
            print("    -> ctrl = 0x00000000: no gate hold on any dom6 slot")
            print("       (bits 0/1/2 all clear). Boot value on this card was")
            print("       0x02 (slot 0x17's gate, held through every prior run);")
            print("       the 2026-08-25 --manual-powerup released it and the")
            print("       release PERSISTED across processes. A cold boot")
            print("       restores 0x02 -- the release lives only in the SMU")
            print("       session (re-run --manual-powerup after any cold cycle).")
        else:
            print(f"    -> ctrl = 0x{ctrl:08x}: no gate bits set (bits 0/1/2")
            print("       clear) -- higher bits carry per-domain clock-ctrl.")
    if rail is not None:
        if rail & 0x10000:
            print("    -> rail bit16 SET: rail-up command in flight")
        elif rail == 0:
            print("    -> rail = 0: IDLE -- the rail-up bit self-clears when the")
            print("       sequencer takes it, so 0 carries no state by itself")
            print("       (powered dom0-3 also read 0). MEASURED 2026-08-25: the")
            print("       rail-up store landed (the ctrl store in the same run")
            print("       did) yet moved nothing -- favored reading: an already-")
            print("       up rail consumed the one-shot instantly. The SMU-side")
            print("       power question is as settled as this oracle can make")
            print("       it; the VCN register block itself (the --direct-load")
            print("       POWER_STATUS MMIO read) is the arbiter.")
        else:
            print(f"    -> rail = {_fx(rail)} (non-zero -- compare against the fw decode)")

# ---------------- manual dom6 rail power-up (fw-exact, bounded) ----------------
# Port of the reference decode (vcn_fullon_bios3.py manual_powerup_domain /
# call_thunk) INTO this fielded script, with the 2026-08-21 ctrl fix: step [0]
# clears gate bits 0/1/2 (the fw's dom7 caller @0x246c3 writes 0 to the ENTIRE
# ctrl reg; a bit0-only clear no-ops on our ctrl=0x02 and leaves slot 0x17's
# latched domain gate held through the whole protocol).

def wr_win(smu, smn, value, label=""):
    """SMN window write -- the SAME path engage_slot_enables uses (proven
    safe and live: the 0x6d1xx writes of 2026-08-20 landed and persisted
    across processes)."""
    if DEGEN[0] <= smn < DEGEN[1]:
        print(f"    [!] refusing degenerate write {label} 0x{smn:x}")
        return False
    smu.smu_write32(WIN_BASE + (smn & 0xFFFFF), value & 0xFFFFFFFF)
    return True

def enc_l32r(pc, at, target):
    """L32R at, [target]: W = 1 | (at<<4) | (off16<<8); target=((pc+3)&~3)+off*4.
    Calibrated against the Robin1 image (same encoder as the reference decode)."""
    if target & 3:
        raise ValueError("l32r target must be 4-byte aligned")
    off = (target - ((pc + 3) & ~3)) >> 2
    if not (-0x8000 <= off < 0x8000):
        raise ValueError(f"l32r from 0x{pc:x} to 0x{target:x} out of range")
    return (1 | (at << 4) | ((off & 0xFFFF) << 8)).to_bytes(3, "little")

def build_call_thunk(fn, arg0, arg1):
    """36-byte thunk @ THUNK_ADDR: call fn(arg0, arg1) with the windowed ABI,
    then complete the mailbox (fn_fe4/fn_fa8) so the mailbox ANSWERS -- a
    completed send proves the call ran in-firmware (no timeout ambiguity):
        entry a1,0x20; l32r a10,[arg0]; l32r a11,[arg1]; call8 fn;
        mov.n a11,a10; mov.n a10,a2; call8 fn_fe4; mov.n a10,a2;
        movi.n a11,1; call8 fn_fa8; retw.n; <arg0> <arg1>"""
    b = bytearray()
    b += enc_entry(1, 0x20)                                  # 0x00 entry a1, 0x20
    b += enc_l32r(THUNK_ADDR + 0x03, 10, THUNK_ADDR + 0x1c)  # 0x03 l32r a10, arg0
    b += enc_l32r(THUNK_ADDR + 0x06, 11, THUNK_ADDR + 0x20)  # 0x06 l32r a11, arg1
    b += enc_call8(THUNK_ADDR + 0x09, fn)                    # 0x09 call8 fn
    b += bytes.fromhex("bd0a")                               # 0x0c mov.n a11, a10
    b += bytes.fromhex("ad02")                               # 0x0e mov.n a10, a2
    b += enc_call8(THUNK_ADDR + 0x10, FN_SET_RESPONSE)       # 0x10 call8 fn_fe4
    b += bytes.fromhex("ad02")                               # 0x13 mov.n a10, a2
    b += bytes.fromhex("0c1b")                               # 0x15 movi.n a11, 1
    b += enc_call8(THUNK_ADDR + 0x17, FN_COMPLETE)           # 0x17 call8 fn_fa8
    b += RETW_N                                              # 0x1a retw.n
    assert len(b) == 0x1c, hex(len(b))
    b += struct.pack("<II", arg0 & 0xFFFFFFFF, arg1 & 0xFFFFFFFF)
    assert len(b) == 0x24, hex(len(b))
    return bytes(b)

def build_inline_store_thunk(smn_addr, value):
    """48-byte thunk @ THUNK_ADDR: the fw's OWN window-store sequence
    (FUN_000235c8's fast path, decoded @0x235d0-0x235e5 of robin_5)
    INLINED into the handler thunk -- NO fw function is called, so the
    call chain stays at the ABI-preflight envelope (dispatcher -> thunk
    -> fe4/fa8), the only depth ever proven on hardware. Bypasses
    fn_2a018's bridge-gate read and the beqz fallback entirely:
        entry a1,0x20; l32r a9,[addr&0xfffff]; l32r a10,[0x010ffe00];
        add.n a9+=a10; MEMW; l32r a8,[value]; s32i a8,a9,512;
        mov.n a11,a8; mov.n a10,a2; call8 fn_fe4; mov.n a10,a2;
        movi.n a11,1; call8 fn_fa8; retw.n; <addr> <base> <value>
    Store target = 0x01100000+(addr&0xfffff) -- byte-identical math to
    the fw's fast path (add.n/MEMW/s32i field-copied from the image;
    s32i source reg a3->a8). Mailbox response = the stored value."""
    a = smn_addr & 0xFFFFF
    b = bytearray()
    b += enc_entry(1, 0x20)                                    # 0x00 entry
    b += enc_l32r(THUNK_ADDR + 0x03, 9, THUNK_ADDR + 0x24)     # 0x03 l32r a9, addr
    b += enc_l32r(THUNK_ADDR + 0x06, 10, THUNK_ADDR + 0x28)    # 0x06 l32r a10, base
    b += bytes.fromhex("aa99")                                 # 0x09 add.n a9 += a10
    b += bytes.fromhex("c02000")                               # 0x0b MEMW
    b += enc_l32r(THUNK_ADDR + 0x0e, 8, THUNK_ADDR + 0x2c)     # 0x0e l32r a8, value
    b += bytes.fromhex("826980")                               # 0x11 s32i a8, a9, 512
    b += bytes.fromhex("bd08")                                 # 0x14 mov.n a11, a8
    b += bytes.fromhex("ad02")                                 # 0x16 mov.n a10, a2 (ctx)
    b += enc_call8(THUNK_ADDR + 0x18, FN_SET_RESPONSE)         # 0x18 call8 fe4
    b += bytes.fromhex("ad02")                                 # 0x1b mov.n a10, a2 (ctx)
    b += bytes.fromhex("0c1b")                                 # 0x1d movi.n a11, 1
    b += enc_call8(THUNK_ADDR + 0x1f, FN_COMPLETE)             # 0x1f call8 fa8
    b += RETW_N                                                # 0x22 retw.n
    assert len(b) == 0x24, hex(len(b))
    b += struct.pack("<III", a, 0x010FFE00, value & 0xFFFFFFFF)
    assert len(b) == 0x30, hex(len(b))
    return bytes(b)

def write_and_verify(smu, addr, code, label="code"):
    for i in range(0, len(code), 4):
        smu.smu_write32(addr + i, int.from_bytes(code[i:i + 4], "little"))
    rb = b"".join(smu.smu_read(addr + i, 1) for i in range(0, len(code), 4))
    if rb != code:
        raise RuntimeError(f"{label} read-back mismatch:\n"
                           f"  wrote {code.hex()}\n  read  {rb.hex()}")

def call_thunk(smu, fn, arg0, arg1, label="CALL", code=None, desc=None):
    """Install a thunk (build_call_thunk by default, or caller-supplied
    code -- e.g. build_inline_store_thunk), repoint msg 0x61, fire,
    restore. Returns (completed, ret): completed=True iff the mailbox
    ANSWERED -- the call ran in-firmware. Bounded: a timeout is waited
    out (~10s SMN-bus self-recovery window), never polled forever."""
    if code is None:
        code = build_call_thunk(fn, arg0, arg1)
        desc = (f": thunk(fn=0x{fn:x}, a2=0x{arg0 & 0xFFFFFFFF:x}, "
                f"a3=0x{arg1 & 0xFFFFFFFF:x})")
    write_and_verify(smu, THUNK_ADDR, code, "call thunk")
    print(f"[*] {label}{desc} [{code.hex()}]")
    smu.smu_write32(SLOT_FUNCPTR, THUNK_ADDR)
    if rd_sram(smu, SLOT_FUNCPTR) != THUNK_ADDR:
        print("    [!] handler-slot repoint failed -- NOT firing")
        return False, None
    completed, ret = False, None
    try:
        st, ret = smu.send_message(3, SLOT, [], check_status=False)
        ret = ret & 0xFFFFFFFF if isinstance(ret, int) else None
        completed = True
        rtxt = "" if ret is None else f" ret=0x{ret:08x}"
        print(f"    [+] mailbox COMPLETED: status=0x{st:x}{rtxt} "
              "-- the call ran IN-FIRMWARE")
    except SmuTimeout:
        print("    -> SmuTimeout: thunk crashed, never ran, or its SMN access")
        print("       stalled (a stalled SMN bridge access usually self-recovers")
        print("       ~10s) -- waiting it out before cleanup ...")
        for _ in range(15):
            time.sleep(1)
            if smu.alive():
                print("    [+] SMU came back -- continuing cleanup")
                break
    finally:
        try:
            if rd_sram(smu, SLOT_FUNCPTR) != 0:
                smu.smu_write32(SLOT_FUNCPTR, 0)
                print(f"[*] restored msg-0x61 handler slot -> 0 "
                      f"(read-back 0x{rd_sram(smu, SLOT_FUNCPTR):x})")
            for i in range(0, len(code), 4):
                smu.smu_write32(THUNK_ADDR + i, 0)
        except Exception as e:
            print(f"[!] could not restore/wipe ({e.__class__.__name__}) -- "
                  f"cold power-cycle before anything else.")
    print("    [+] SMU still alive (debug path)" if debug_alive(smu) else
          "    [!] SMU NOT alive via debug path -- cold power cycle")
    return completed, ret

def _config_write_transport(smu):
    """The config-window WRITE primitive if the library exposes one.
    Returns (write_fn, None) or (None, message). SIGNATURE VERIFIED from the
    library source (bc250_smu/transport.py, 2026-08-25):

        def write_smu_reg(self, reg: int, value: int) -> None:
            pwrite(fd, pack(reg), 0xB8)      # SMN index
            pwrite(fd, pack(value), 0xBC)    # SMN data -- the write

    Same index/data mechanics as read_smu_reg and as every mailbox send
    (send_message writes rsp/args/cmd at SMN 0x03B10xxx through exactly
    this) -- so the MECHANISM is proven live on this box. MEASURED
    2026-08-25: correctly-issued config stores to the dom6 sequencer
    (0x0006D0F8/0x0006D17C/0x0006D184) produced NO register change (ctrl
    0x02->0x00 store read back 0x02 immediately) -- the sequencer block
    ignores host fabric writes. The block is fabric-READABLE (proven) but
    not fabric-WRITABLE."""
    tr, why = _config_transport(smu)
    if tr is None:
        return None, why
    for name in ("write_smu_reg", "wr_smu_reg", "smu_reg_write"):
        fn = getattr(tr, name, None)
        if callable(fn):
            return fn, None
    api = ", ".join(sorted(m for m in dir(tr) if not m.startswith("_")))
    return None, (f"transport has no write method (write_smu_reg/wr_smu_reg/"
                  f"smu_reg_write). Transport API: {api}")


def _config_write_capability_probe(smu, config_base):
    """Decisive config-write test on the 0x06dxxx block (--config-writes
    pre-check). Toggles slot 0x16's clock-ENABLE bit through the CONFIG
    window, reads it back through BOTH paths (config + fw window), then
    restores the original value via the fw window (the proven-landing
    path -- the engage used exactly it).

    Why the enable bit: it is (a) the one bit in this block PROVEN to
    change post-boot through the fw window (the engage: 0 -> 1, persisted),
    (b) trivially reversible, and (c) safe to drop for a few ms -- the
    island sat fully enable=0 for its whole life before the engage.

    Returns True  -- config store OBSERVED (the config window CAN write
                     this block; the sequencer regs specifically ignore it)
            False -- store not observed (the whole block ignores host
                     fabric writes; config stores are dead here)
            None  -- pre-check failed (could not establish a testable
                     state); caller should treat config mode as unusable.
    """
    tr, why = _config_transport(smu)
    if tr is None:
        print(f"    [!] {why}")
        return None
    try:
        g = gate_of(smu, 0x16)
    except Exception as e:
        print(f"    [!] slot 0x16 gate address unreadable ({e.__class__.__name__})")
        return None
    reg = g + 0x08
    cur = rd_win(smu, reg, "slot0x16 enable (fw window)")
    if cur is None:
        print("    [!] fw-window read of slot 0x16 enable failed")
        return None
    full = config_base + (reg & 0xFFFFF)
    target = cur ^ 1
    print(f"    config-write capability probe: slot 0x16 enable @SMN "
          f"0x{full:08x}: {cur & 1} -> {target & 1} (toggle + restore)")
    try:
        wr, _ = _config_write_transport(smu)
        if wr is None:
            return None
        wr(full, target & 0xFFFFFFFF)
        time.sleep(0.01)
        via_cfg = tr.read_smu_reg(full)
        via_win = rd_win(smu, reg, "slot0x16 enable (fw window)")
    except OSError as e:
        print(f"    [!] probe store/read failed: {e}")
        via_cfg = via_win = None
    landed = (via_cfg is not None and (via_cfg & 1) == (target & 1))
    # restore through the PROVEN path regardless
    try:
        wr_win(smu, reg, cur)
        time.sleep(0.01)
        back = rd_win(smu, reg, "slot0x16 enable (fw window)")
        restored = back is not None and (back & 1) == (cur & 1)
    except Exception:
        restored = False
    if landed:
        print(f"    -> config store OBSERVED (config reads {via_cfg & 1:#x}, "
              f"fw window {via_win & 1 if via_win is not None else 'ERR'})"
              + ("" if restored else "  [!] RESTORE FAILED -- re-engage "
                 "the enable bits (run the fire + engage)"))
        print("       the config window CAN write the slot sub-block; the")
        print("       sequencer registers specifically ignore it (write-")
        print("       protected sub-block). Config stores remain unusable")
        print("       for cmd/rail/ctrl -- but this is a clean finding.")
    else:
        print(f"    -> config store NOT observed (config reads "
              f"{(via_cfg & 1) if via_cfg is not None else 'ERR'}, fw window "
              f"{(via_win & 1) if via_win is not None else 'ERR'})"
              + ("" if restored else "  [!] RESTORE FAILED -- re-engage "
                 "the enable bits (run the fire + engage)"))
        print("       the whole 0x06dxxx block ignores host fabric WRITES")
        print("       (reads proven live, writes dropped). Config stores")
        print("       are dead here; the fw-window debug-write path (the")
        print("       engage's vehicle -- lands and persists) is the store")
        print("       path for this block.")
    return landed


def dom6_fabric_spelling(smu, verbose=True):
    """Discriminate the dom6 sequencer's full fabric spelling at runtime.

    Reads all four sequencer registers (cmd/rail/status/ctrl) through the
    fw's own window (rd_win offsets 0x6D1xx -- live on every run), then
    through the PCI-config window at BOTH candidate full spellings:
      0x0116Dxxx  (the SMU window mirrors the SMN 0x011xxxxx NBIO frame)
      0x0006Dxxx  (the SMU window mirrors the SMN 0x000xxxxx low frame)
    A candidate wins only if it matches the live value on EVERY register AND
    at least one matched register carries a DISTINCTIVE value (nonzero live
    value) -- a wrong address that happens to read 0 (or a dead 0xffffffff)
    can never win. Matching on a single all-zero register set is refused:
    zeros carry no information, and a wrong-address config WRITE is exactly
    what this discrimination must prevent.
    Returns the winning base (0x01100000 / 0x00000000) or None.
    """
    def say(msg):
        if verbose:
            print(msg)

    tr, why = _config_transport(smu)
    if tr is None:
        say(f"    [!] {why}")
        return None
    live = {}
    for name, addr in DOM6_BLOCK_REGS:
        live[name] = rd_win(smu, addr, f"{name} (fw window)")
    if any(v is None or v == 0xFFFFFFFF for v in live.values()):
        say("    [!] a fw-window sequencer read failed/dead -- cannot discriminate")
        return None
    say("    fw window (live): " + " ".join(f"{n}={v:08x}" for n, v in live.items()))
    # a distinctive register is one whose live value is nonzero -- the only
    # kind that can prove an address identity
    distinctive = [n for n, v in live.items() if v != 0]
    if not distinctive:
        say("    [!] every sequencer register reads 0 through the fw window --")
        say("        zeros cannot discriminate an address (a wrong address also")
        say("        reads 0); refusing to pick a spelling for config WRITES.")
        return None
    for base, tag in ((DOM6_WINDOW_BASE_A, "NBIO-frame spelling"),
                      (DOM6_WINDOW_BASE_B, "low-frame spelling")):
        vals, err = {}, False
        for name, addr in DOM6_BLOCK_REGS:
            try:
                vals[name] = tr.read_smu_reg(base + (addr & 0xFFFFF))
            except OSError as e:
                say(f"    [!] config read {base + (addr & 0xFFFFF):08x} ({name}) failed: {e}")
                err = True
                break
        if err:
            continue
        say("    config 0x{:08x} ({}): ".format(base, tag) +
            " ".join(f"{n}={v:08x}" for n, v in vals.items()))
        if all(vals[n] == live[n] for n in live) and                 any(vals[n] == live[n] and live[n] != 0 for n in distinctive):
            say(f"    -> MATCH on all four registers ({', '.join(distinctive)} distinctive)")
            return base
    say("    [!] no fabric spelling matched all four live values -- the dom6")
    say("        sequencer is not confirmed fabric-visible; --config-writes")
    say("        unavailable (the fw-window paths still work).")
    return None


def smn_store(smu, addr, value, via_thunk=False, config_base=None):
    """One SMN store for the power-up protocol, one of three vehicles:
      - config_base set (--config-writes): full-width store through the
        PCI-config window at config_base + (addr & 0xFFFFF). Physically the
        same registers the fw's own writer (FUN_000235c8) hits through its
        window -- a completely different access path than the fw window, so
        it sidesteps the measured 'store sat dirty' behaviour of the
        transfer-engine mirror. The mechanism is proven safe: every mailbox
        send is a config-window store (to the MP1 block).
      - via_thunk (--thunk-writes): the INLINE store thunk (the fw's own
        store sequence inside the msg-0x61 handler thunk; a mailbox-OK answer
        PROVES in-fw execution). Measured wedge risk.
      - default: bare fw-window write (proven-live block, but carries no
        in-fw sync -- the night-1 'sat dirty' path).
    Returns True/False if the vehicle proved execution, else None."""
    if config_base is not None:
        wr, why = _config_write_transport(smu)
        if wr is None:
            print(f"    [!] config write unavailable: {why}")
            return False
        full = config_base + (addr & 0xFFFFF)
        wr(full, value & 0xFFFFFFFF)
        print(f"    config store 0x{full:08x} <- 0x{value:08x}")
        return True
    if via_thunk:
        # INLINE vehicle (2026-08-21 night-4): calling FUN_000235c8 itself
        # WEDGED the SMU on a benign target (it calls fn_2a018 -- an SMN
        # window read -- at depth +3, one windowed frame deeper than
        # anything ever proven on hardware). The inline thunk runs the
        # fw's own store sequence at the preflight depth with NO fw fn
        # call at all.
        code = build_inline_store_thunk(addr, value)
        completed, _ = call_thunk(smu, 0, addr, value, "SMN write",
                                  code=code,
                                  desc=": inline store thunk "
                                       f"(0x{addr:x} <- 0x{value:08x})")
        return completed
    wr_win(smu, addr, value)
    return None

def poll_win(smu, addr, mask, want_set, tries=60, delay=0.05, label=""):
    """Bounded window poll. THE key difference vs the firmware: FUN_00023b14
    polls FOREVER (that is what wedged the SMU on a fully-gated domain);
    this gives up on a count and the host stays in control."""
    for n in range(tries):
        v = rd_win(smu, addr, label)
        if v is None:
            return False
        if bool(v & mask) == want_set:
            if n >= 2:
                print(f"      ... poll[{label}] settled after {n} tries")
            return True
        if n < 2 or (n + 1) % 20 == 0:
            print(f"      poll[{n:02d}] 0x{addr:x} = 0x{v:08x} "
                  f"(waiting for bit {'SET' if want_set else 'CLEAR'})")
        time.sleep(delay)
    return False

def _smu_dead_bail(smu, step):
    """After an in-fw store that did not complete: if the SMU is DEAD, the
    predicted SmuTimeout fork has fired mid-sequence. Print the verdict and
    tell the caller to STOP -- every further read is just another ~5s
    timeout, and nothing left in the sequence can observe anything.
    Returns True iff the SMU is dead (caller should return True = wedged)."""
    if debug_alive(smu):
        return False
    print(f"    [!] SMU WEDGED at step {step}: the in-fw store (inline")
    print("        store thunk via msg-0x61) took the SMU down -- mailbox silent,")
    print("        transfer-engine debug path dead, window reads dead. The")
    print("        handler-slot repoint and thunk bytes could NOT be restored")
    print("        (still live in SRAM). This is the predicted SmuTimeout fork:")
    print("        the in-fw write path is the blocker. COLD POWER-CYCLE before")
    print("        anything else; then --thunk-probe (benign target) to split")
    print("        vehicle-vs-target before re-trying anything in-fw.")
    return True


def thunk_probe(smu, reg=None, value=None, fn=None):
    """Benign-vehicle probe -- the 2026-08-21 wedge discriminator.
    With fn set (--probe-fn): RAW-ARGS mode -- call fn(reg, value)
    through the same thunk (the depth/bridge ladder, e.g. fn_2a018).

    Root cause of BOTH 2026-08-21 wedges (night-2 cmd store AND this
    probe run) -- FOUND 2026-08-21 by re-decoding smu_fw_robin_5: the old
    FUN_SMN_WRITE constant 0x233e8 was a MID-FUNCTION address (inside the
    fn @0x23370, one byte into a sync; zero calls and zero pointer-table
    refs anywhere in the image). call8 to it executed garbage-register
    code ending in a wild store (s32i.n a9, a6, 44) -- argument-
    independent, hence identical wedges on a benign target. NOT the tail,
    NOT the target, NOT the encoding. Corrections landed since:
      - FUN_SMN_WRITE = 0x235c8 -- the fw's REAL window-store fn
        (entry-verified, called 30+ times by the fw itself), and
      - the fe4/fa8 tail is now PROVEN correct by firmware idiom
        (TestMessage @0x1b3a8 + 500+ call sites do exactly our sequence),
        and the project's earlier ABI preflight (msg 0x61 -> TestMessage,
        answer = arg0+1) already proved repoint+dispatch+tail+mailbox on
        hardware once.
    This probe now rides the CORRECTED vehicle: one idempotent store via
    the fw's own primitive to slot 0x17's clock reg, re-writing its
    CURRENT value (no-op even if it lands)."""
    try:
        gate = gate_of(smu, 0x17)
    except Exception:
        gate = 0x0006d128
    if reg is None:
        reg = gate                     # +0x00: the clock value reg itself
    if fn is not None:
        # raw-args mode: reg/value are a2/a3, not register+value; no
        # idempotency discipline -- the fn under test must be a
        # KNOWN-harmless leaf.
        if value is None:
            value = 0
        print(f"[*] fn vehicle probe: fn@0x{fn:x}(0x{reg:x}, 0x{value:08x})")
        print("    raw-args mode: the depth/bridge ladder. Expected outcome")
        print("    for a leaf with no fe4/fa8 tail: SmuTimeout with the SMU")
        print("    ALIVE -- the signal is ALIVE vs WEDGED, not the mailbox.")
        completed, ret = call_thunk(smu, fn, reg, value,
                                    f"fn probe via 0x{fn:x}")
        if completed:
            rtxt = "" if ret is None else f" (ret=0x{ret:08x})"
            print(f"    [+] mailbox ANSWERED{rtxt} -- fn ran in-fw AND")
            print("        completed (it carries its own fe4/fa8 tail).")
        elif not debug_alive(smu):
            print("    [!] VERDICT: fn WEDGED the SMU at depth +2 -- the fn")
            print("        (or its bridge access) is the killer even at the")
            print("        preflight depth. COLD POWER-CYCLE before anything.")
        else:
            print("    [~] VERDICT: timeout but SMU ALIVE -- dispatch of this")
            print("        fn at depth +2 is SAFE (preflight depth). If this")
            print("        was fn_2a018: the SMN window read of 0x032000e8")
            print("        is FINE from handler context -- the night-4 wedge")
            print("        was depth (+3) or 0x235c8's gate-fallback path.")
            print("        Next: --inline-store-probe.")
        return
    cur = rd_win(smu, reg, "probe target")
    if cur is None:
        print("[!] cannot read the probe target through the window -- abort")
        return
    if value is None:
        value = cur                    # idempotent by construction
    print(f"[*] thunk vehicle probe: FUN_000235c8(0x{reg:x}, 0x{value:08x})")
    if reg == gate:
        print("    target = slot 0x17's clock reg -- a proven-live window")
        print("    address (the fw's own slot code reads/writes this block");
        print("    through the same window); value = the register's CURRENT")
        print("    value -- a no-op even if the store lands. CORRECTED vehicle:")
        print("    FUN_000235c8 (the fw's real window-store fn) + the fe4/fa8")
        print("    tail (proven-correct idiom). The old 0x233e8 constant was a")
        print("    mid-function address -- that, not the tail, was the wedge.")
    else:
        print(f"    target = 0x{reg:x} (operator-specified via --probe-reg --")
        print(f"    make sure the value is a no-op); current value 0x{cur:08x}.")
    completed, ret = call_thunk(smu, FUN_SMN_WRITE, reg, value,
                                "vehicle probe via FUN_000235c8")
    alive = debug_alive(smu)
    cur2 = rd_win(smu, reg, "probe target")
    if completed:
        rtxt = "" if ret is None else f", ret=0x{ret:08x}"
        print(f"    [+] idempotency: target reads {_fx(cur2)} (was 0x{cur:08x})")
        print(f"    [+] VERDICT: VEHICLE PROVEN on hardware{rtxt} -- thunk +")
        print("        FUN_000235c8 + the fe4/fa8 tail all ran in-fw and the")
        print("        mailbox ANSWERED. The corrected vehicle is live: in-fw")
        print("        stores are now a proven capability (--thunk-writes can")
        print("        be un-gated). Next rung: --manual-powerup --thunk-writes")
        print("        --force-thunk-writes (the fw-exact rail protocol with")
        print("        in-fw stores).")
    elif not alive:
        print("    [!] VERDICT: calling 0x235c8 wedges the SMU even though the")
        print("        encoding, args and tail are all verified correct.")
        print("        fn_2a018 is DECODED (harmless 29-byte leaf: one SMN")
        print("        window read of 0x032000e8 through the 0x031ffe00")
        print("        window) -- the remaining suspects: (a) DEPTH: this")
        print("        chain is one windowed frame deeper (+3) than anything")
        print("        ever proven on hardware; (b) the SMN-bridge access")
        print("        itself from handler context; (c) 2a018's gate returning")
        print("        0 -> the beqz fallback path. Next: --inline-store-probe")
        print("        (bypasses all three at the proven depth), or the ladder")
        print("        --thunk-probe --probe-fn 0x2a018 --probe-reg 4 (bridge")
        print("        read isolated at the safe +2 depth). COLD POWER-CYCLE.")
    else:
        print("    [~] VERDICT: timeout but the SMU is ALIVE -- the store did")
        print("        not complete the mailbox yet the fw survived (a bus")
        print("        stall would have killed it). Leans dispatch/tail, not")
        print("        the store. Re-running the probe is safe.")


def inline_store_probe(smu, reg=None, value=None):
    """THE night-4 discriminator: one idempotent in-fw store with the
    INLINE store thunk -- the fw's own store sequence executed inside
    the handler thunk, NO fw fn called. Call depth = the ABI-preflight
    envelope (dispatcher -> thunk -> fe4/fa8), the only depth ever
    proven on hardware (2026-08-21: msg 0x61 -> TestMessage answered).
    Splits the three surviving night-4 hypotheses in one shot:
      ANSWERS  -> in-fw stores PROVEN at safe depth (un-gate
                 --thunk-writes; smn_store already uses this vehicle)
      WEDGES   -> an SMN-bridge access from handler context is itself
                 the killer (fn and depth exonerated) -- in-fw stores
                 are off the table; the rail protocol stays on
                 host-side window writes (proven safe and live)
      timeout+ALIVE -> the store stalled without wedging; re-run once."""
    try:
        gate = gate_of(smu, 0x17)
    except Exception:
        gate = 0x0006d128
    if reg is None:
        reg = gate
    cur = rd_win(smu, reg, "probe target")
    if cur is None:
        print("[!] cannot read the probe target through the window -- abort")
        return
    if value is None:
        value = cur                    # idempotent by construction
    print(f"[*] inline store probe: [0x01100000+(0x{reg:x}&0xfffff)] <- "
          f"0x{value:08x}  (the fw's own fast-path math, in-thunk)")
    if reg == gate:
        print("    target = slot 0x17's clock reg, value = its CURRENT value")
        print("    (cold: 0x00000000 -> the purest possible no-op store).")
    print("    vehicle = build_inline_store_thunk: entry/l32r/add.n/MEMW/")
    print("    s32i + the proven fe4/fa8 tail -- ZERO fw fn calls, depth =")
    print("    the ABI-preflight envelope (+1/+2).")
    code = build_inline_store_thunk(reg, value)
    completed, ret = call_thunk(smu, 0, reg, value, "inline store probe",
                                code=code,
                                desc=": inline store thunk")
    alive = debug_alive(smu)
    cur2 = rd_win(smu, reg, "probe target")
    if completed:
        rtxt = "" if ret is None else f", response=0x{ret:08x}"
        print(f"    [+] mailbox ANSWERED{rtxt} -- the store ran IN-FIRMWARE")
        print(f"    [+] idempotency: target reads {_fx(cur2)} "
              f"(was 0x{cur:08x})")
        print("    [+] VERDICT: IN-FW STORES PROVEN at the preflight depth.")
        print("        The 0x235c8 wedge was its extra call frame / its gate")
        print("        path, not the store. --thunk-writes is un-gated (its")
        print("        stores now ride THIS vehicle). Next rung:")
        print("        --manual-powerup --thunk-writes --force-thunk-writes.")
    elif not alive:
        print("    [!] VERDICT: the INLINE store wedged the SMU -- with fn,")
        print("        args, encoding, depth and tail ALL exonerated, an")
        print("        SMN-BRIDGE ACCESS FROM HANDLER CONTEXT is the killer.")
        print("        In-fw stores are OFF the table; the rail protocol")
        print("        stays on host-side window writes (proven safe).")
        print("        COLD POWER-CYCLE before anything else.")
    else:
        print("    [~] VERDICT: timeout but SMU ALIVE -- the store stalled")
        print("        without wedging; safe to re-run the probe once.")


def manual_powerup_dom6(smu, via_thunk=False, via_config=False):
    """FW-exact dom6 rail power-up -- the FUN_00023b14 decode, every poll
    BOUNDED on the host (cannot wedge). Steps:
        [0] ctrl &= ~0b111   (FIXED: release gate bits 0/1/2 -- the fw's dom7
                              caller writes 0 to the WHOLE reg; a bit0-only
                              clear no-ops on ctrl=0x02 and leaves slot 0x17's
                              latched domain gate held through the protocol)
        [1] cmd |= 1         (power-up request; bit0 self-clears when taken)
        [2] poll status != 0 (fw: bge loop; VACUOUS if residue predated CMD)
        [3] rail = 0x10000   (rail-up command; bit16 self-clears when taken)
        [4] poll rail bit16 clear (success ONLY if the write was OBSERVED in
                              read-back first -- night-1 lesson)
        [5] state byte |= 1  (factory state already carries it)
    Night-1 (2026-08-20, window stores) was INCONCLUSIVE -- and its "stores
    sat dirty" ctrl evidence was VACUOUS: the old bit0-only clear computed
    ctrl & ~1 = 0x02 and wrote 0x02 over 0x02 (identical value; "unchanged"
    read-back proved nothing). The FIXED all-three-bits clear (a REAL
    0x02->0x00 change) has never executed through the fw window -- and that
    path is proven to land on this block's slot sub-registers (the engage:
    enable 0->1, read-back verified, persisted across processes).

    MEASURED 2026-08-25 (--config-writes, first run): correctly-issued
    config stores (transport source-verified: write_smu_reg(reg, value),
    the same 0xB8/0xBC mechanics as every mailbox send) produced NO
    register change on the sequencer -- ctrl 0x02->0x00 read back 0x02
    immediately; cmd/rail no side effects; status unmoved. The sequencer
    sub-block is fabric-READABLE but ignores host fabric WRITES. So the
    remaining host-side store vehicle for cmd/rail/ctrl is the fw-window
    debug-write path (plain --manual-powerup) -- the rung that has never
    been tried with a real ctrl change. --config-writes now runs the
    config-write capability probe (slot-0x16 enable toggle) first and
    reports the block's write capability."""
    regs = dict(DOM6_BLOCK_REGS)
    state = rd_sram(smu, DOM6_STATE_WORD) & 0xFF
    if via_config and via_thunk:
        print("[!] --config-writes and --thunk-writes are exclusive; dropping")
        print("    --thunk-writes for this run.")
        via_thunk = False
    config_base = None
    mode = ("config-window stores (full fabric spelling)"
            if via_config else
            "thunk stores (inline vehicle)" if via_thunk else "window stores")
    print(f"[*] manual dom6 power-up ({mode}, bounded polls):")
    if via_config:
        print("    discriminating the dom6 fabric spelling first ...")
        config_base = dom6_fabric_spelling(smu)
        if config_base is None:
            print("    [!] cannot resolve a fabric spelling for the dom6 block")
            print("        -- --config-writes aborted (no store issued). The")
            print("        bare window path (--manual-powerup) still works.")
            return
        print(f"    using fabric spelling base 0x{config_base:08x}")
        print("    config-write capability probe (slot-0x16 enable toggle) ...")
        landed = _config_write_capability_probe(smu, config_base)
        if landed is not True:
            print("    [!] config stores are not usable on this block -- the")
            print("        sequencer protocol cannot run in config mode.")
            print("        The window path (plain --manual-powerup, FIXED")
            print("        step [0] -- the never-tried real ctrl clear) is")
            print("        the next vehicle.")
            return

    def rd(addr, label=""):
        """Read the sequencer through the ACTIVE vehicle's path (config
        window in config mode; the fw window otherwise)."""
        if config_base is not None:
            tr, _ = _config_transport(smu)
            if tr is None:
                return None
            try:
                return tr.read_smu_reg(config_base + (addr & 0xFFFFF))
            except OSError:
                return None
        return rd_win(smu, addr, label)

    print(f"    state byte @0x{DOM6_STATE_WORD:x} = 0x{state:02x}")
    cmd, rail = rd(regs["cmd"], "cmd"), rd(regs["rail"], "rail")
    stat = rd(regs["status"], "status")
    ctrl = rd(regs["ctrl"], "ctrl")
    if None in (cmd, rail, stat, ctrl):
        print("    [!] a register read failed -- the 0x6d1xx block is proven live")
        print("        through the fw window, so treat this as a transport fault;")
        print("        aborting.")
        return
    print(f"    BEFORE: cmd=0x{cmd:08x} rail=0x{rail:08x} "
          f"status=0x{stat:08x} ctrl=0x{ctrl:08x}")
    thunk_all_ok = True          # only meaningful with via_thunk

    # [0] ctrl: release ALL THREE slot gates (bits 0/1/2 <-> 0x16/0x17/0x18)
    ctrl_released = False          # set when the store is observed to land
    if ctrl & 0b111:
        nv = ctrl & ~0b111 & 0xFFFFFFFF
        held = [f"slot 0x{s:02x}(bit{b})" for b, s in CTRL_SLOT_BITS
                if ctrl >> b & 1]
        print(f"    [0] ctrl  0x{regs['ctrl']:x}: 0x{ctrl:08x} -> 0x{nv:08x}  "
              f"(release {'gates' if len(held) > 1 else 'gate'} "
              + ", ".join(held) + ")")
        if smn_store(smu, regs["ctrl"], nv, via_thunk,
                     config_base=config_base) is False:
            thunk_all_ok = False
            if _smu_dead_bail(smu, "[0] ctrl"):
                return True
        c2 = rd(regs["ctrl"], "ctrl")
        if c2 is None:
            print("        read-back ERR")
        elif not (c2 & 0b111):
            ctrl_released = True
            print("        -> LANDED: all domain gate bits released"
                  " (first real ctrl change ever on this card -- the"
                  " gate bit that survived every prior run is clear)")
        elif c2 == ctrl:
            if config_base is not None:
                print("        -> UNCHANGED: the config store was dropped"
                      " (measured 2026-08-25: the sequencer ignores host"
                      " fabric writes)")
            elif via_thunk:
                print("        -> UNCHANGED: the in-fw store completed the"
                      " mailbox yet the register did not move -- the"
                      " sequencer ignores even SMU-executed stores here")
            else:
                print("        -> UNCHANGED: window store not observed on"
                      " the sequencer (NOTE: the slot sub-registers DO"
                      " take window stores -- the engage proved it; the"
                      " sequencer sub-block may be SMU-write-restricted)")
        else:
            print(f"        -> 0x{c2:08x} (still holding: "
                  + ", ".join(f"bit{b}" for b, _ in CTRL_SLOT_BITS
                                if c2 >> b & 1) + ")")
    else:
        print("    [0] ctrl gate bits 0/1/2 already clear -- no gate held")

    # [1] cmd |= 1 -- power-up request
    print(f"    [1] cmd   0x{regs['cmd']:x}: 0x{cmd:08x} -> 0x{cmd | CMD_UP:08x}  "
          f"(bit0 = up request)")
    cmd_store = smn_store(smu, regs["cmd"], cmd | CMD_UP, via_thunk,
                          config_base=config_base)
    if cmd_store is False:
        thunk_all_ok = False
        if _smu_dead_bail(smu, "[1] cmd"):
            return True
    c2 = rd(regs["cmd"], "cmd")
    if c2 is not None:
        if c2 & CMD_UP:
            note = "(bit0 SET -- request pending, or store dirty)"
        elif cmd_store is True and config_base is None:
            note = ("(bit0 CLEAR -- store PROVEN executed in-fw: the FSM took "
                    "the request and it self-cleared)")
        else:
            note = ("(bit0 CLEAR -- taken-and-self-cleared, or the store never "
                    "landed: cmd read 0 BEFORE the write, so the read-back "
                    "cannot distinguish)")
        print(f"        cmd reads back 0x{c2:08x} {note}")

    # [2] poll status nonzero (fw: bge loop, any positive value)
    residue = stat != 0
    ok_ack = poll_win(smu, regs["status"], 0xFFFFFFFF, True,
                      tries=60, delay=0.05, label="status")
    s2 = rd(regs["status"], "status")
    if residue:
        print(f"    [~] status was ALREADY nonzero before CMD (now {_fx(s2)}:")
        print("        boot up-ack residue) -- ack poll VACUOUS; a fresh ack is")
        print("        indistinguishable from residue on this domain.")
        ok_ack = None
    elif ok_ack:
        print(f"    [+] STATUS went NONZERO ({_fx(s2)}) -- fresh FSM ACK")
    else:
        print("    [!] status stayed 0 through the poll window -- FSM not")
        print("        acking; the rail step below is the decisive liveness test")

    # [3] rail = 0x00010000 -- THE lever
    print(f"    [3] rail  0x{regs['rail']:x}: 0x{rail:08x} -> 0x00010000  "
          f"(bit16 = rail-up cmd)")
    if smn_store(smu, regs["rail"], RAIL_UP, via_thunk,
                 config_base=config_base) is False:
        thunk_all_ok = False
        if _smu_dead_bail(smu, "[3] rail"):
            return True
    time.sleep(0.05)
    r2 = rd(regs["rail"], "rail")
    rail_seen = r2 is not None and r2 != rail
    if r2 is None:
        print("        read-back ERR")
    elif r2 == RAIL_UP:
        print("        -> write LANDED, bit16 still set (not yet taken)")
    elif r2 == rail:
        if ctrl_released:
            print("        -> read-back UNCHANGED -- but the ctrl store in step")
            print("           [0] LANDED, so this store landed too: the FAVORED")
            print("           reading is an already-up rail consuming the one-")
            print("           shot command instantly (powered dom0-3 read 0)")
        else:
            print("        -> read-back UNCHANGED: store not observed (sat dirty,")
            print("           or was consumed instantly on an already-up rail)")
    elif not (r2 & 0x10000):
        print(f"        -> rail 0x{rail:08x} -> 0x{r2:08x}: bit16 CLEARED --")
        print("           the sequencer TOOK the rail-up command")
    else:
        print(f"        -> rail 0x{rail:08x} -> 0x{r2:08x} (bit16 still set)")

    # [4] bounded poll: rail bit16 self-clear
    if config_base is not None:
        tr, _ = _config_transport(smu)
        ok_rail = False
        for n in range(60):
            try:
                v = tr.read_smu_reg(config_base + (regs["rail"] & 0xFFFFF))
            except OSError:
                v = None
            if v is None:
                break
            if not (v & 0x10000):
                if n >= 2:
                    print(f"      ... poll[rail] settled after {n} tries")
                ok_rail = True
                break
            if n < 2 or (n + 1) % 20 == 0:
                print(f"      poll[{n:02d}] rail = 0x{v:08x} (waiting bit16 CLEAR)")
            time.sleep(0.05)
    else:
        ok_rail = poll_win(smu, regs["rail"], 1 << 16, False,
                           tries=60, delay=0.05, label="rail")
    if ok_rail and rail_seen:
        print("    [+] RAIL write OBSERVED in read-back and bit16 self-cleared:")
        print("        rail-up DELIVERED and TAKEN -- sequence COMPLETED")
    elif ok_rail:
        ok_rail = None
        print("    [~] bit16 read CLEAR throughout but the write never showed in")
        print("        read-back -- poll VACUOUS (store sat dirty, or consumed")
        print("        instantly on an already-up rail)")
        if config_base is not None:
            print("        (config mode: the store was likely dropped -- see")
            print("         the ctrl result above)")
        elif not via_thunk:
            if ctrl_released:
                print("        (the ctrl store in step [0] LANDED -- this rail")
                print("         store landed too; already-up rail consuming the")
                print("         one-shot is the favored reading)")
            else:
                print("        (the ctrl result above is the cleaner store-landing")
                print("         oracle; --thunk-writes remains the in-fw ladder)")
    else:
        print("    [!] rail bit16 never cleared within the poll window")

    # [5] state byte |= 1 (fw: s8i a6, entry, 20)
    if not (state & 1):
        w = rd_sram(smu, DOM6_STATE_WORD)
        smu.smu_write32(DOM6_STATE_WORD, (w | 1) & 0xFFFFFFFF)
        print(f"    [5] state byte @0x{DOM6_STATE_WORD:x}: 0x{state:02x} -> 0x01")
    else:
        print("    [5] state byte already 0x01")

    # ---- verdict (read-back-observed criteria only) ----
    c3 = rd(regs["cmd"], "cmd")
    r3 = rd(regs["rail"], "rail")
    s3 = rd(regs["status"], "status")
    x3 = rd(regs["ctrl"], "ctrl")
    print(f"    AFTER: cmd={_fx(c3)} rail={_fx(r3)} "
          f"status={_fx(s3)} ctrl={_fx(x3)}")
    if ok_rail:
        print("    [+] VERDICT: RAIL-UP COMPLETED. Arbiter next:")
        print("        sudo python3 enable_vcn.py --vcn-power-regs")
        print("        (fabric-slice probe: dead -> live / values moving iff the")
        print("         rail actually landed -- the oracle alone is not proof)")
    elif ctrl_released and x3 is not None and not (x3 & 0b111):
        vehicle = ("config-window" if config_base is not None else
                   "fw-window" if via_thunk else "window")
        print(f"    [+] VERDICT: ctrl LANDED and HELD through the run "
              f"(0x{ctrl:08x} -> 0x{x3:08x}) --")
        print(f"        the first real sequencer state change on this card, via")
        print(f"        {vehicle} stores. Night-1's 'stores sat dirty on the")
        print("        sequencer' theory is DEAD: these stores land. By extension")
        print("        the cmd/rail stores in this run landed too -- their vacuous")
        print("        read-backs (one-shot/self-clear semantics) now read as")
        print("        TAKEN on an already-up rail. With status carrying the")
        print("        powered-domain up-ack residue, the SMU-side power state is")
        print("        as complete as this oracle can make it: clocks programmed")
        print("        + enables ON + gates released + rail vacuously taken.")
        print("        THE arbiter is now the VCN register block itself:")
        print("        sudo python3 enable_vcn.py --direct-load")
        print("        (first POWER_STATUS MMIO read: real values = island live;")
        print("         all-ones = isolation, clean abort; hang = cold cycle)")
        print("        Confirm ctrl persistence first with --vcn-power-regs"
              " (cross-process).")
    elif config_base is not None:
        print("    [~] VERDICT: rail-up NOT confirmed through the config window.")
        print("        MEASURED 2026-08-25: the sequencer ignores host fabric")
        print("        writes (ctrl 0x02->0x00 store read back 0x02 instantly;")
        print("        transport source-verified, so the stores were correctly")
        print("        issued). The remaining host-side vehicle is the fw-window")
        print("        debug-write path -- plain --manual-powerup with the FIXED")
        print("        step [0] (the never-tried REAL ctrl clear; the same path")
        print("        provably lands on this block's slot sub-registers).")
    elif ok_ack:
        print("    [+] VERDICT: fresh FSM ack observed -- the sequencer FSM is")
        print("        ALIVE on this domain; rail delivery is the open question.")
        if not via_thunk:
            print("        Next: --manual-powerup --thunk-writes")
    elif via_thunk and thunk_all_ok:
        print("    [~] VERDICT: INCONCLUSIVE even with in-fw stores -- the")
        print("        mailbox answered every store (they EXECUTED in firmware)")
        print("        yet no sequencer register moved: consistent with an")
        print("        already-up domain no-op'ing the command. The rail is then")
        print("        NOT the blocker; the open question becomes the VCN")
        print("        register ADDRESSES (0x1F8xx has zero refs in the fw image).")
        print("        Next: --vcn-power-regs (fabric-slice probe = the arbiter).")
    else:
        print("    [~] VERDICT: INCONCLUSIVE -- no sequencer register movement")
        print("        this run (ctrl unchanged, rail poll vacuous, no ack).")
        print("        Next: sudo python3 enable_vcn.py "
              "--manual-powerup --thunk-writes")

# ---------------- standalone: dom6 block dump (ISO/reset hunting) ----------------
# Known/annotated offsets inside the dom6 block (0x06D000..0x06D1FF). The
# whole block reads live through the fw window on every run; the dump hunts
# for ISO/reset/state bits beyond the four sequencer registers -- the open
# question after 2026-08-25 (sequencer says dom6 UP, VCN MMIO says CLOSED:
# if an isolation or reset latch exists in this block, it hides here).
DOM6_DUMP_BASE = 0x0006D000
DOM6_DUMP_DWORDS = 0x80                 # 0x06D000..0x06D1FF
# MEASURED 2026-08-25 (first full dump): the slot sub-blocks are 0x28 bytes
# apart and carry more fields than the sequencer decode: +0x04 (=5 on every
# slot -- second divider? voltage index?), +0x1c (=0x1000, bit12). The block
# head (+0x000..+0x0E0) and tail (+0x178..+0x1FC) hold ~50 more nonzero
# dwords -- see the highlights printed by dom6_block_dump.
DOM6_ANNOTATE = {
    0x0F8: "ctrl (domain clock gates; boot 0x02, released 2026-08-25)",
    0x17C: "cmd (sequencer one-shots)",
    0x184: "rail (bit16 = rail-up one-shot)",
    0x190: "status (0x01010101 up-residue / 0x01011010 down-residue pattern)",
    0x100: "slot 0x16 +0x00 clock", 0x104: "slot 0x16 +0x04 (5)",
    0x108: "slot 0x16 +0x08 enable", 0x114: "slot 0x16 +0x14 divider",
    0x11C: "slot 0x16 +0x1c (0x1000)", 0x124: "slot 0x16 +0x24 status",
    0x128: "slot 0x17 +0x00 clock", 0x12C: "slot 0x17 +0x04 (5)",
    0x130: "slot 0x17 +0x08 enable", 0x13C: "slot 0x17 +0x14 divider",
    0x144: "slot 0x17 +0x1c (0x1000)", 0x14C: "slot 0x17 +0x24 status",
    0x150: "slot 0x18 +0x00 clock", 0x154: "slot 0x18 +0x04 (5)",
    0x158: "slot 0x18 +0x08 enable", 0x164: "slot 0x18 +0x14 divider",
    0x16C: "slot 0x18 +0x1c (0x1000)", 0x174: "slot 0x18 +0x24 status",
    0x178: "just past the slot blocks (domain-level, =1)",
}


def dom6_block_dump(smu):
    """Read-only dump of the whole dom6 block through the fw window (the
    proven-safe path -- every run reads this block). Annotates the known
    registers and highlights nonzero UNKNOWN dwords: any ISO/reset latch
    the sequencer decode missed would show as an unexplained nonzero bit."""
    print("\n[*] dom6 block dump 0x%06x..0x%06x (fw window, read-only):"
          % (DOM6_DUMP_BASE, DOM6_DUMP_BASE + DOM6_DUMP_DWORDS * 4 - 4))
    print("    hunting for ISO/reset/state bits beyond the 4 sequencer regs --")
    print("    the 2026-08-25 contradiction (sequencer UP vs MMIO CLOSED) lives")
    print("    here if it lives anywhere SMU-side.")
    unknown_nonzero = []
    for i in range(DOM6_DUMP_DWORDS):
        a = DOM6_DUMP_BASE + i * 4
        v = rd_win(smu, a, "dump")
        if v is None:
            print(f"    0x{a:06x}: READ FAILED (block was live this run?)")
            continue
        note = DOM6_ANNOTATE.get(a - DOM6_DUMP_BASE, "")
        if v != 0 or note:
            mark = "" if v == 0 else f"0x{v:08x}"
            print(f"    0x{a:06x} (+0x{a - DOM6_DUMP_BASE:03x}): {mark:<12} {note}")
        if v != 0 and not note:
            unknown_nonzero.append((a, v))
    if unknown_nonzero:
        print(f"\n    [!] {len(unknown_nonzero)} NONZERO UNKNOWN dword(s):")
        for a, v in unknown_nonzero:
            print(f"        0x{a:06x} (+0x{a - DOM6_DUMP_BASE:03x}) = 0x{v:08x}")
        print("        (candidates: ISO latch, reset, per-domain state the")
        print("         sequencer decode missed -- diff against a POST-")
        print("         power-attempt re-run to see which move)")
    else:
        print("\n    [~] no nonzero unknown dwords -- nothing ISO/reset-like")
        print("        hides in this block's low half. The clamp (if any) is")
        print("        NOT SMU-visible here: PSP-side, or deeper fw path.")
    # ---- live probe of the +0x54 quad's candidate SMN address ----
    # The four (0x06900900, 0xe8) pairs are the block's most structured
    # unknown. If 0x06900900 is an SMN address, the config window can read
    # it full-width; dead frames read 0 safely on this transport (measured:
    # 0x024 slices, 0x0116D1xx). NONZERO = a responder -- likely the clamp
    # register family the dom6 sequence programs.
    try:
        tr, _ = _config_transport(smu)
    except Exception:
        tr = None
    if tr is not None:
        print("\n    live probe: SMN 0x06900900..0x0690090c (the +0x54 quad's")
        print("    candidate address, read-only via the config window -- dead")
        print("    reads return 0 on this transport):")
        for a in range(0x06900900, 0x06900910, 4):
            try:
                v = tr.read_smu_reg(a)
                tag = ("  <-- NONZERO (responder -- likely the clamp family)"
                       if v not in (0, 0xFFFFFFFF) else "")
                print(f"      SMN 0x{a:08x} -> 0x{v:08x}{tag}")
            except OSError as e:
                print(f"      SMN 0x{a:08x}: OSError ({e})")

    print("\n    structured highlights (Ghidra decode targets -- find the fw")
    print("    code that reads/writes these block offsets):")
    print("      +0x054..+0x070: FOUR identical (0x06900900, 0x000000e8) pairs")
    print("        -- the most structured unknown. If 0x06900900 is an SMN")
    print("        address it is in an UNMAPPED 0x069xxxxx frame; four")
    print("        (addr, value) templates the fw programs during the")
    print("        domain sequence are a PRIME ISO-clamp/release candidate")
    print("        (the July RE spoke of a PCIE iso-clamp).")
    print("      +0x044 0x10000001 / +0x074 0xc0000031 / +0x084 0x40840000 /")
    print("        +0x090 0x00100000 / +0x098 0x08000000 / +0x09c 0x64000000 /")
    print("        +0x1d0 0x40000000 -- single-bit registers: status/enable")
    print("        bits (one of these being a held ISO/reset is possible)")
    print("      +0x0d4/+0x0d8 = 30/30 and +0x0dc/+0x0e0 = 0x00080036 twice --")
    print("        config pairs (min/max? voltage offsets?)")
    print("      +0x1ec 0x010003e8 (1000 with bit24 -- timeout-ish)")
    print("      +0x1f0..+0x1fc: 8 / 347 / 194 / 312 -- small counters")
    print("      +0x0c0 0xcc0 (3264), +0x000 50, +0x010/14/18 36/32/40,")
    print("        +0x038/+0x03c 50/50, +0x040 16, +0x04c 17, +0x078 10,")
    print("        +0x088 25, +0x02c 100 -- domain config constants")
    return True


# ---------------- standalone: fw message-handler table dump ----------------
# The Q3 dispatcher maps msg id -> handler function pointer, 8 bytes per
# entry, entry for msg M at SRAM 0x746C + (M-1)*8 (the repoint math proven
# on hardware: msg 0x61 -> 0x776C). Zero entry = reserved/no handler.
#
# TRANSPORT CONTRACT (source-verified 2026-08-25, bc250_smu/primitives.py):
# smu_read(addr, n) reads AT MOST 18 WORDS per call -- the library's own
# window_read()/dump_sram() chunk at 18. The first version of this dump
# requested 32-word chunks (14 past the cap) and received GARBAGE: an
# 0x80-periodic pattern of session residue (the fire's read-back-verified
# thunk dwords 0x83a57a1c/0xf01de383, slot status 0x01490050 -- literally
# the last data the engine had staged). 18-word chunks + a single-dword
# cross-probe of the proven 0x776C slot validate the bulk data now.
#
# The kernel PPSMC list for this fw (smu_v11_8_ppsmc.h) has NO VCN message
# -- but the library's api_q3.py (source-verified) documents ~60 live Q3
# msg ids, incl. 0x3C/0x3D enable/disable SMU FEATURES (bitmask; renoir's
# PowerUpVcn is gated behind a VCN_PG feature bit there). Any message whose
# handler reaches FUN_00023b14 (0x23B14, domain power-up) or its wrapper
# 0x246C3 is the fw's own VCN-power vehicle.
MSG_TABLE_BASE = 0x746C
MSG_TABLE_DEFAULT_COUNT = 0xC0          # msg 0x01..0xC0 (library's highest known: 0xA8)

KNOWN_FNS = {
    0x00FE4: "fn_fe4 (set mailbox response)",
    0x00FA8: "fn_fa8 (mark message complete)",
    0x01B3A8: "TestMessage",
    0x023370: "fn @0x23370 (contains the old bogus 0x233E8)",
    0x02362C: "soc_clk_program_slot",
    0x0235C8: "FUN_000235c8 (fw window store)",
    0x023744: "FUN_00023744 (slot-clock program -- the Discord sequence's fn)",
    0x023B14: "FUN_00023b14 (DOMAIN POWER-UP -- the dom6 sequencer)",
    0x0246C3: "fw dom7 caller (ctrl=0 + power-up wrapper)",
    0x02A018: "fn_2a018 (bridge-gate SMN read leaf)",
}

# Live Q3 message ids (bc250_smu/api_q3.py, source-verified 2026-08-25).
KNOWN_Q3_MSGS = {
    0x01: "TestMessage (library alive()/test_message)",
    0x04: "unknown (library _q3_0x04)", 0x0A: "unknown (library _q3_0x0a)",
    0x0B: "unknown", 0x0C: "unknown", 0x0D: "unknown", 0x0E: "unknown",
    0x0F: "set CPU/GFX VID (mV)", 0x10: "unforce CPU/GFX VID",
    0x11: "unknown", 0x14: "unknown", 0x15: "unknown",
    0x18: "unknown", 0x19: "unknown", 0x1A: "unknown", 0x1B: "unknown",
    0x1D: "set soc clock for index", 0x1E: "set perf profile index",
    0x20: "set max temperature cpu/gpu",
    0x24: "unknown", 0x25: "set OC clk (core, MHz)", 0x26: "unset OC clk",
    0x27: "SECURE (undocumented sibling of the 0x28-0x2C cluster -- library: 'not wrapped')",
    0x28: "SECURE: set write ptr (SMU-local addr)",
    0x29: "SECURE: write-through 32",
    0x2A: "SECURE: mem64 SMN read",
    0x2B: "SECURE: set SMN write addr",
    0x2C: "SECURE: mem64 SMN write",
    0x2D: "SECURE (undocumented sibling -- library: 'not wrapped')",
    0x2E: "SECURE (undocumented sibling -- library: 'not wrapped')",
    0x2F: "SECURE (undocumented sibling -- library: 'not wrapped')",
    0x30: "get CPU/GFX dynamic VID offset", 0x34: "read dat_00015778",
    0x36: "get current CPU voltage (mV)", 0x37: "get current GPU voltage (mV)",
    0x38: "get clock assigned to state (a)", 0x39: "get clock assigned to state (b)",
    0x3A: "get clock assigned to state (c)",
    0x3B: "get clk assigned to P-state (MHz)",
    0x3C: "ENABLE SMU FEATURES (bitmask arg!)",
    0x3D: "disable SMU features (bitmask arg)",
    0x40: "get CPU temp max", 0x41: "read perf profile table",
    0x42: "get VDDCR_SOC DPM clock", 0x43: "get core frequency (MHz)",
    0x47: "returns 0xFE", 0x48: "returns 0xFE",
    0x49: "set CPU VID offset (+/-5)", 0x4A: "set GFX VID offset 1 (+/-5)",
    0x4B: "CPU droop calibration", 0x4C: "GFX droop calibration",
    0x4D: "set CPU VID float offset", 0x4E: "set GPU VID float offset",
    0x4F: "unknown", 0x50: "scale f VID curve", 0x51: "set CPU coeff",
    0x52: "set CPU clock stretch coeff", 0x53: "set CCX clock stretch coeff",
    0x54: "unknown", 0x55: "unknown", 0x56: "unknown",
    0x58: "unknown", 0x59: "unknown", 0x5A: "unknown", 0x5B: "unknown",
    0x5C: "freq related (a)", 0x5D: "freq related (b)",
    0x5E: "unknown", 0x5F: "write some cpu frequency",
    0x60: "pstate related",
    0x65: "set dat_000133fc", 0x66: "reset dat_000133fc to 0",
    0x67: "returns 0", 0x6A: "unknown", 0x6B: "unknown",
    0x6C: "set temperature parameters",
    0x6D: "force clock stretching VID", 0x6E: "CPU coefficients",
    0x6F: "unknown", 0x70: "unknown", 0x71: "unknown", 0x72: "unknown",
    0x73: "unknown", 0x74: "unknown", 0x75: "unknown", 0x76: "unknown",
    0x77: "set CPU max current (mA)",
    0x7F: "get current perf sample (us)", 0x80: "get sample interval max",
    0x85: "unknown", 0x86: "unknown", 0x87: "unknown",
    0x8B: "set CPU max temp", 0x8C: "set GPU max temp",
    0x8D: "get current sample interval", 0x8E: "set VID main 2 limit (mV)",
    0x8F: "set max CPU boost clk (MHz)",
    0x90: "unknown", 0x91: "unknown", 0x96: "unknown", 0x98: "unknown",
    0x99: "modify P-state-0 parameter",
    0x9A: "disable extra CPU/GPU voltage",
    0x9B: "switch core bilinear model", 0x9C: "unknown",
    0xA7: "CPU related (a)", 0xA8: "CPU related (b)",
}

# the unlock's staged zone (unlock.py: smu_memset32(0x7950, 0, 0x4C//4))
# overlaps table entries ~msg 0x9D..0xA6 -- those read 0 after unlocking
UNLOCK_STAGED_ZONE = (0x7950, 0x799C)


def msg_table_dump(smu, count=MSG_TABLE_DEFAULT_COUNT):
    """Read-only dump of the fw's Q3 message-handler table from SRAM.

    Validates the transport (18-word chunks -- smu_read's documented cap --
    plus a single-dword cross-probe of the PROVEN 0x776C slot) and the table
    premise (base 0x746C / stride 8 from the community RE; stride 4 tested
    too, since the single repoint cannot distinguish strides) against the
    library's live secure-cluster messages 0x28-0x2C before interpreting
    anything. On failure it reports instead of dumping garbage.
    """
    print(f"\n[*] fw Q3 message-handler table: SRAM 0x{MSG_TABLE_BASE:04x}, "
          f"msg 0x01..0x{count:02x} ({count} entries, read-only):")
    print("    transport: 18-word chunks (smu_read's documented cap; the first")
    print("    version of this dump requested 32-word chunks and received")
    print("    0x80-periodic session-residue garbage -- fixed 2026-08-25).")

    # ---- read the region in 18-word chunks (the documented cap) ----
    words = count * 2
    CH = 18
    raw = b""
    for i in range(0, words, CH):
        raw += smu.smu_read(MSG_TABLE_BASE + i * 4, min(CH, words - i))
    if len(raw) != words * 4:
        print(f"    [!] bulk read returned {len(raw)} bytes, expected {words * 4}")
        return None

    import struct as _s

    def dw(addr):                     # dword at SRAM addr from the bulk raw
        return _s.unpack_from("<I", raw, addr - MSG_TABLE_BASE)[0]

    # ---- single-dword cross-probe of the ONE proven slot ----
    prov_single = rd_sram(smu, 0x776C)
    prov_bulk = dw(0x776C)
    same = "CONSISTENT" if prov_single == prov_bulk else "MISMATCH"
    print(f"    cross-probe SRAM 0x776c: single read 0x{prov_single:08x}, "
          f"bulk 0x{prov_bulk:08x} -- {same}")
    if prov_single != prov_bulk:
        print("    [!] bulk and single reads disagree -- transport fault;")
        print("        dump aborted (do not interpret anything below 0x776c).")
        return None

    # ---- premise validation against PROVEN-live messages ----
    # Anchors (both proven on this card by the library):
    #   - secure msgs 0x28-0x2C are live handlers (the tool rides them)
    #   - msg 0x01 is TestMessage @0x1b3a8 (alive()/test_message sends Q3
    #     msg 0x01 and gets arg0+1 -- the project's ABI preflight used the
    #     same function)
    # A stride wins only if: all five secure msgs resolve to DISTINCT
    # plausible code pointers (a misaligned read pattern repeats the flags
    # dword -- the 2026-08-25 run's stride-4 probe read {6, x, 6, y, 6},
    # passing the old weak plausibility test) AND msg 0x01 resolves to
    # TestMessage exactly.
    KNOWN_LIVE = (0x28, 0x29, 0x2A, 0x2B, 0x2C)   # proven on this card
    TESTMESSAGE = 0x1B3A8
    print("    premise check -- anchors: live secure msgs 0x28-0x2C (distinct")
    print("    plausible code ptrs) + msg 0x01 == TestMessage (0x1b3a8):")
    stride = None
    for cand in (8, 4):
        base = 0x776C - (0x61 - 1) * cand
        hits = []
        for m in KNOWN_LIVE:
            v = dw(base + (m - 1) * cand)
            hits.append((m, v, 0 < v < 0x40000))
        vals = [v for _, v, _ in hits]
        distinct = len(set(vals)) == len(vals)
        ok = sum(1 for _, _, good in hits if good)
        tm = dw(base)                    # entry for msg 0x01
        tm_ok = tm == TESTMESSAGE
        verdict = ok == 5 and distinct and tm_ok
        detail = " ".join(f"0x{m:02x}->0x{v:05x}{'ok' if g else 'BAD'}"
                          for m, v, g in hits)
        print(f"      stride {cand} (base 0x{base:04x}): {ok}/5 plausible, "
              f"distinct={distinct}, msg0x01=0x{tm:05x} "
              f"{'== TestMessage' if tm_ok else '!= 0x1b3a8'} -- {detail}")
        if verdict and stride is None:
            stride = cand
    if stride is None:
        print("    [!] NO stride fully validates (distinctness and/or the")
        print("        TestMessage anchor failed): the 0x746C region is not")
        print("        the handler table, or the dispatcher indexes")
        print("        differently. The only PROVEN entry remains the 0x776C")
        print("        slot. Resolve the dispatcher's table walk in Ghidra")
        print("        before trusting any handler enumeration.")
        return None
    base = 0x776C - (0x61 - 1) * stride
    print(f"    premise VALIDATED at stride {stride} (base 0x{base:04x}).")

    # ---- dump the entries ----
    handlers = []
    for m in range(1, count + 1):
        a = base + (m - 1) * stride
        if stride == 8:
            lo, hi = dw(a), dw(a + 4)
        else:
            lo, hi = dw(a), 0
        if lo or hi:
            handlers.append((m, a, lo, hi))

    print(f"\n    {len(handlers)} msg id(s) with a handler:")
    for m, a, lo, hi in handlers:
        known = KNOWN_FNS.get(lo, "")
        desc = KNOWN_Q3_MSGS.get(m, "")
        parts = [f"msg 0x{m:02x} (@0x{a:04x}): 0x{lo:05x}"]
        if hi:
            parts.append(f"hi=0x{hi:08x}")
        if known:
            parts.append(f"== {known}")
        elif desc:
            parts.append(f"({desc})")
        if UNLOCK_STAGED_ZONE[0] <= a < UNLOCK_STAGED_ZONE[1]:
            parts.append("[inside the unlock's staged zone -- zeroed by unlock.py]")
        print("      " + "  ".join(parts))

    unknown = [(m, lo) for m, a, lo, hi in handlers
               if lo not in KNOWN_FNS]

    # ---- flags-field analysis (stride 8: the hi dword) ----
    # MEASURED 2026-08-25: hi is a FLAGS dword, not part of a pointer --
    #   0x00000006  most messages
    #   0x00000201  msgs 0x27-0x2F  (the secure cluster -- gated)
    #   0x00000206  msgs 0x71,0x72,0xA7,0xA8  (a SECOND gated group!)
    # bit 0x200 = "gated behind the secure-access unlock" is the working
    # decode; msgs 0x71/0x72/0xa7/0xa8 are gated messages the library never
    # wrapped. Decode the dispatcher's flag handling in Ghidra to confirm.
    if stride == 8:
        byflags = {}
        for m, a, lo, hi in handlers:
            byflags.setdefault(hi, []).append(m)
        print("\n    flags-field groups (hi dword):")
        for hi in sorted(byflags):
            msgs = byflags[hi]
            shown = [f"0x{m:02x}" for m in msgs[:8]]
            if len(msgs) > 8:
                shown.append("...")
            tag = ""
            if hi & 0x200:
                tag = "  <-- GATED (bit 0x200; needs the unlock)"
            print(f"      0x{hi:08x}: {len(msgs):3d} msg(s): "
                  + " ".join(shown) + tag)

    # ---- Ghidra shortlist: handlers in/near the power-code band ----
    # The fw's clock/power cluster spans 0x23370 (fn @0x23370) .. 0x246C3
    # (dom7 power-up caller), with 0x235c8/0x2362c/0x23744/0x23B14 inside.
    # Handlers inside or adjacent to that band are the prime candidates for
    # "message that calls the domain sequencer".
    if unknown:
        print(f"\n    [!] {len(unknown)} handler(s) not in the known-fn list --")
        print("        resolve them in the fw image (Ghidra).")
    print("\n    GHIDRA HUNT (in order of efficiency):")
    print("      1. xref 0x23b14 (domain power-up) and 0x246c3 (dom7 caller)")
    print("         in the fw image; list every caller; match each caller")
    print("         address against this table -- the match IS the msg id.")
    print("      2. handlers inside/near the power-code band (0x23370-0x246c3):")
    band = [(m, a, lo) for m, a, lo, hi in handlers
            if 0x23000 <= lo < 0x26000]
    for m, a, lo in sorted(band, key=lambda x: x[2]):
        d = ""
        if lo >= 0x246C3:
            d = f" (+0x{lo - 0x246C3:x} past the dom7 caller 0x246c3)"
        elif lo < 0x23370:
            d = f" (0x{0x23370 - lo:x} below fn@0x23370)"
        print(f"         msg 0x{m:02x} -> 0x{lo:05x}{d}")
    print("      3. msg 0x3C/0x3D (enable/disable SMU features, bitmask) --")
    print("         decode the bitmask: a VCN/PG bit (renoir's PowerUpVcn is")
    print("         feature-gated) plus its consumer would be the native path.")
    print("      4. the GATED unknowns from the flags analysis (0x71/0x72/")
    print("         0xa7/0xa8 if undocumented) -- gated msgs are the")
    print("         interesting ones (the secure cluster itself is gated).")
    print("      5. secure siblings 0x27/0x2D/0x2E/0x2F -- undocumented")
    print("         members of the mem64-window family; possibly bulk")
    print("         variants (accessible post-unlock).")
    return {m: (lo, hi) for m, a, lo, hi in handlers}


def smn_vcn_probe(smu, addr):
    """ONE SMN read through the SMU itself (Q3 msg 0x2A, the mem64 window).

    The fw MASKS the address argument to 20 bits and accesses it at SMU-local
    0x01100000 + (arg & 0xFFFFF) (the fw's own window idiom, FUN_000235c8
    decode). The mask is fact; WHICH fabric frame that SMU-local window maps
    onto is UNRESOLVED -- 0x011xxxxx (NBIO frame, model v2's assumption) or
    0x000xxxxx (low frame). Both candidate effective addresses are printed.
    Either way the window can NEVER express a 0x024xxxxx fabric address (the
    mask kills the top bits): the 2026-08-24 "0x02403010 fast 0" was the
    masked alias (0x01103010 / 0x00003010), NOT VCN. VCN fabric access rides
    --vcn-power-regs (the PCI-config window, full 32-bit addressing).

    Risk: a dead offset stalls the SMN bus and the SMU wedges (the documented
    0x1F8xx-as-arg family -- dead responders at both candidate spellings;
    README 2.7; self-recovers ~10s or needs a cold cycle). Sanity read first,
    one probe read only, recovery wait + alive check on timeout.
    """
    print("\n[*] SMN-route probe (Q3 msg 0x2A, mem64 window):")
    if DEGEN[0] <= addr < DEGEN[1]:
        print(f"    refusing 0x{addr:08x}: the 0x1F8xx arg family is the documented")
        print("    SMU wedge (no responder at the effective address under either")
        print("    frame hypothesis). Pick another --smn-vcn-addr.")
        return
    off = addr & 0xFFFFF
    eff_a, eff_b = 0x01100000 + off, 0x00000000 + off
    print(f"    target address: 0x{addr:08x}")
    if off != addr:
        print(f"    fw window offset: 0x{off:05x} (arg masked to 20 bits)")
        print(f"    effective address: 0x{eff_a:08x} (NBIO-frame hyp) or "
              f"0x{eff_b:08x} (low-frame hyp) -- UNRESOLVED, see --vcn-power-regs")
        print("    step 0. This probe can NEVER reach the 0x024 fabric frame")
        print("    (use --vcn-power-regs).")
    print("[!] WARNING: a dead offset stalls the SMN bus -- the SMU")
    print("    wedges (self-recovers ~10s, or cold power-cycle). Proceeding ...")

    # liveness pre-check: if an earlier stage already wedged the SMU, do not
    # spend the probe on it (its timeout would be misread as "no VCN route").
    if not debug_alive(smu):
        print("    [!] SMU debug path NOT answering BEFORE the probe -- an earlier")
        print("        stage already wedged it. Probe skipped: the target address is")
        print("        not what killed the SMU. COLD POWER-CYCLE.")
        return

    # sanity: the ONE address the mem64 window is PROVEN to reach -- window
    # offset 0x5A870, the CPU core-presence mask (unlock.py PROBE_ADDR;
    # set_core_mask.py reads AND writes it through this exact message pair).
    # The MP1 mailbox region (0x03B10xxx) is NOT reachable from the window
    # (measured 2026-08-20: that read stalls the SMN bus and wedges the whole
    # SMU). Never
    # use the mailbox as a sanity target again.
    try:
        st, val = smu.sec_smn_read32(SMN_PROVEN_ADDR)
    except (SmuError, SmuTimeout):
        print("    [!] sanity read of the PROVEN address timed out -- the mem64")
        print("        window itself is not answering in this fw state. Probe")
        print("        aborted; COLD POWER-CYCLE before retrying.")
        return
    print(f"    sanity: SMN 0x{SMN_PROVEN_ADDR:08x} (core-presence mask) -> "
          f"status 0x{st:02x}, value 0x{val:08x}")
    if st != 0x01:
        print("    [!] sanity status not OK -- the window rejected the read")
        print("        (unexpected on this proven address); probe aborted.")
        return
    m = val & 0xFF
    tag = ("0x77 stock 6c/12t" if m == 0x77 else
           "0xFF all-cores unlocked" if m == 0xFF else "?")
    print(f"    -> core mask 0x{m:02x} ({tag}) -- mem64 window is live")

    t0 = time.monotonic()
    try:
        st, val = smu.sec_smn_read32(addr)
    except (SmuError, SmuTimeout) as e:
        print(f"    -> {e.__class__.__name__}: no responder at the effective address")
        print(f"       (0x{eff_a:08x}/0x{eff_b:08x}) -- the SMN bus stalled inside")
        print("       the SMU (the documented wedge).")
        print(f"       Verdict: no responder behind mem64 arg 0x{addr:08x}.")
        print("[*] waiting 12s for the SMU to self-recover ...")
        time.sleep(12)
        if debug_alive(smu):
            print("[+] SMU recovered via the debug path.")
        else:
            print("[!] SMU still not answering -- wait ~10s more or COLD POWER-CYCLE.")
        return
    dt = (time.monotonic() - t0) * 1000.0
    if st != 0x01:
        print(f"    -> status 0x{st:02x} (not OK), value 0x{val:08x}")
        return
    if val == 0xFFFFFFFF:
        print(f"    -> 0x{val:08x} ({dt:.0f} ms): all-ones -- the route RESPONDS,")
        print("       but the target register is isolated/unreadable (island")
        print("       closed, or an unrouted offset under the true frame).")
    else:
        print(f"    -> 0x{val:08x} ({dt:.0f} ms): real value from the effective")
        print(f"       address (0x{eff_a:08x}/0x{eff_b:08x} -- frame unresolved;")
        print("       this is NOT a VCN fabric access; VCN rides --vcn-power-regs).")

# ------------- VCN power/harvest registers: fabric-slice probe -------------
def _config_transport(smu):
    """The library's PCI-config SMN transport (root 00:00.0, 0xB8/0xBC), or
    (None, reason). Proven live at SMN 0x03B10A20 on every mailbox send --
    the one CPU-side transport that takes full 32-bit SMN addresses."""
    tr = getattr(smu, "_transport", None)
    if tr is None or not hasattr(tr, "read_smu_reg"):
        return None, ("library transport not reachable (smu._transport) -- "
                      "library version mismatch?")
    return tr, None


def _fabric_window_reads(smu):
    """ROUTE P: 0x024 fabric-frame probe over the PCI-config SMN window.

    TRANSPORT FIX (2026-08-24 evening): the old route P mmap'd BAR0 and used
    bytes 0x38/0x3C as PCIE_INDEX2/DATA2 -- but BAR0 is the 256MB VRAM
    aperture, NOT the register file (July probe Test B: BAR0 reads real VRAM;
    the kernel's rmmio is BAR5, 512KB). Every "SMN window read" the old route
    ever made was a VRAM read at BAR0+0x3C (the uniform 0xb9f53acd et al.,
    boot-dependent), and its INDEX2 "echo" passed because it echoed into
    VRAM. CPU reads through the REAL window (BAR5+0x38/0x3C, kernel debugfs
    or userspace) are the July #1/#3 measured BOARD HANG on VCN addresses --
    that transport is off the table for VCN.

    The transport that IS proven on this box for full 32-bit SMN addresses is
    the library's own: PCI config 0xB8/0xBC of the root device 00:00.0
    (Bc250PciTransport.read_smu_reg) -- live at SMN 0x03B10A20 on every
    mailbox send. Unlike the SMU's mem64 window (msg 0x2A -- fw masks the arg
    to 20 bits, so it can never express a 0x024xxxxx address), it can express
    any fabric address.

    Targets: the per-IP fabric slices from IP discovery (ROM-verified, full
    map in vcn2_register_map.md). The slices are SMALL (VCN 2KB, GC 1KB) and
    are NOT register-file mirrors -- no SMN spelling of mmUVD_POWER_STATUS is
    known; 0x02403010 is just the 5th dword of VCN's slice. We dump slice
    heads and let the values speak.

    Ladder (each step stops the run on a dead frame):
      0. sanity + FRAME DISCRIMINATOR:
         - the PROVEN gate: one read of the Q3 mailbox cmd register (the
           config window hits it on every library send).
         - core mask at BOTH full spellings 0x0115A870 / 0x0005A870 (the
           window offset 0x5A870 is proven; the frame is not). Whichever
           returns 0x77/0xFF settles the SMU-window frame question.
         - dom6 rail at 0x0116D184 / 0x0006D184, compared against the LIVE
           value read through the fw's own window (rd_win). A match proves
           the dom6 power sequencer is fabric-visible -- and gives the exact
           spelling --manual-powerup --config-writes can drive.
      1. THM slice head (0x02400c00, 8 dwords) -- first 0x024-frame read ever
         attempted through this window, aimed at an always-live IP.
      2. GC slice head (0x02402c00, 4 dwords) -- second live-IP opinion.
      3. VCN slice (0x02403000, 16 dwords) -- the goal. Skipped unless step 1
         or 2 showed a live value (a dead frame makes the VCN read pure risk
         with no information gain).

    Risk: dead addresses through the config-window class do NOT hang (July
    #5 suggested clean 0xffffffff; MEASURED 2026-08-25 on this box they
    return clean 0x00000000 -- THM/GC slice anchors, the 0x0116D1xx
    spelling), so a hang is not expected. MEASURED 2026-08-25: the 0x024
    frame itself reads all-zero through this window even on live IPs (THM,
    GC) -- dead-or-zero is indistinguishable, so the slice probe carries no
    information on this box; the discriminator in step 0 is where the value
    is. Labeled, opt-in via --vcn-power-regs.

    Returns {byte_offset: value} for the VCN slice, or None if skipped.
    """
    print("\n[*] ROUTE P -- 0x024 fabric-frame probe via the PCI-config SMN")
    print("    window (root 00:00.0 config 0xB8/0xBC, the library transport):")
    tr, why = _config_transport(smu)
    if tr is None:
        print(f"    [!] {why} -- route P skipped")
        return None

    def rd_smn(a):
        return tr.read_smu_reg(a)

    # ---- step 0a: the PROVEN gate (the Q3 mailbox, hit on every send) ----
    print("    step 0: window sanity on the PROVEN SMN address ...")
    try:
        mb = rd_smn(DEFAULT_QUEUE_ADDRS[3][0])
    except OSError as e:
        print(f"    [!] mailbox sanity read failed: {e} -- route P skipped")
        return None
    print(f"    Q3 mailbox cmd  @SMN 0x{DEFAULT_QUEUE_ADDRS[3][0]:08x} -> "
          f"0x{mb:08x} (last message id -- plausible if small)")
    if mb == 0xFFFFFFFF:
        print("    [!] all-ones on the PROVEN mailbox address -- the config window")
        print("        is not answering; route P skipped (do not probe fabric).")
        return None

    # ---- step 0b: core-mask frame discriminator (which spelling is real?) ----
    # The window offset 0x5A870 is PROVEN (unlock.py/set_core_mask.py); the
    # full-width SMN spelling is not: 0x0115A870 (window==NBIO frame, the
    # model-v2 assumption) or 0x0005A870 (window==low frame). A 0x77/0xFF
    # answer picks the winner; both-dead = the SMU window maps neither frame
    # (SMU-private) -- informational, not fatal.
    print("    core-mask frame discriminator (proven window offset 0x5A870):")
    # MEASURED 2026-08-25 (first hardware run): BOTH spellings returned
    # 0x00000077 -- an alias of the two ranges or a coincidental register.
    # The core mask alone therefore CANNOT pick the frame; the dom6
    # discriminator below is the decisive one (its registers carry
    # distinctive live values).
    cm_hits = []
    for spelling in (CORE_MASK_SMN, CORE_MASK_SMN_ALT):
        try:
            v = rd_smn(spelling)
        except OSError as e:
            print(f"      SMN 0x{spelling:08x}: OSError ({e})")
            continue
        # match on the FULL value: the mask register reads 0x00000077 /
        # 0x000000FF, while dead reads return 0xffffffff (July #5 class) or
        # 0x00000000 (MEASURED 2026-08-25 on this box) -- masking first
        # would FALSELY match 0xffffffff&0xff==0xff as "unlocked".
        tag = ("0x77 stock 6c/12t" if v == 0x77 else
               "0xFF all-cores unlocked" if v == 0xFF else
               "dead (all-ones)" if v == 0xFFFFFFFF else
               "dead/zero" if v == 0 else "not the mask")
        print(f"      SMN 0x{spelling:08x} -> 0x{v:08x} ({tag})")
        if v in (0x77, 0xFF):
            cm_hits.append(spelling)
    if len(cm_hits) == 1:
        cm_hit = cm_hits[0]
        frame = ("NBIO frame (model v2 assumption CONFIRMED)"
                 if cm_hit == CORE_MASK_SMN else
                 "LOW frame (model v2 assumption WRONG -- the window base is 0)")
        print(f"    -> core mask lives at SMN 0x{cm_hit:08x}: the SMU window")
        print(f"       mirrors the {frame}.")
    elif len(cm_hits) == 2:
        print("    -> BOTH spellings return the mask value -- AMBIGUOUS (a")
        print("       fabric alias of the two ranges, or a second register")
        print("       holding the same value). The core mask cannot pick the")
        print("       frame; the dom6 discriminator below is decisive. (Alias")
        print("       test: set_core_mask -> 0xFF, re-read both -- both move")
        print("       = alias, one moves = coincidence.)")
    else:
        print("    -> neither spelling returned the mask: the SMU window maps")
        print("       neither frame full-width (SMU-private), or the mask moved.")
        print("       The fabric probe below is unaffected (it rides the config")
        print("       window directly).")

    # ---- step 0c: dom6 fabric-visibility discriminator ----
    # All four sequencer registers are read through the fw window (live on
    # every run) and through the config window at BOTH full spellings; a
    # spelling wins only on a full four-register match with a distinctive
    # (nonzero) value -- see dom6_fabric_spelling. A win means
    # --manual-powerup --config-writes can drive the rail through the config
    # window (no fw window, no thunk).
    print("    dom6 sequencer fabric discriminator (fw-window offsets 0x6Dxxx):")
    dom6_frame = dom6_fabric_spelling(smu, verbose=True)
    if dom6_frame is not None:
        print(f"    -> the dom6 power sequencer IS fabric-visible (full")
        print(f"       spelling = 0x{dom6_frame:08x} + fw-window offset).")
        print("       MEASURED 2026-08-25: config WRITES to it are ignored")
        print("       (host fabric stores dropped; --config-writes reports")
        print("       this and probes the block's write capability).")
    else:
        print("    -> the dom6 sequencer is NOT confirmed fabric-visible.")
        print("       --config-writes is unavailable (the fw-window paths")
        print("       are unaffected).")

    # ---- step 0d: config-read LIVE-TRACKING cross-check (read-only) ----
    # Slot 0x17's clock/enable registers changed AFTER boot during the fire
    # run's engage (clock 0x00->0x20, enable 0->1) and persist in this SMU
    # session. Reading them through the config window and comparing against
    # the live fw-window values tests whether config reads TRACK live
    # changes or serve a boot-time snapshot -- the assumption every
    # config-read conclusion above rests on. (Informative only while the
    # SMU has not been power-cycled since an engage run.)
    try:
        g17 = gate_of(smu, 0x17)
        for off, what in ((0x00, "clock value"), (0x08, "enable")):
            fwv = rd_win(smu, g17 + off, f"slot0x17 {what} (fw window)")
            try:
                cfgv = rd_smn(dom6_frame + ((g17 + off) & 0xFFFFF)) \
                    if dom6_frame is not None else None
            except OSError:
                cfgv = None
            if fwv is None or cfgv is None:
                print(f"    live-tracking check slot0x17+{off:#x} ({what}):"
                      " read failed -- skipped")
                continue
            match = "MATCH" if cfgv == fwv else "MISMATCH"
            print(f"    live-tracking slot0x17+{off:#x} ({what}): fw window "
                  f"0x{fwv:08x}, config 0x{cfgv:08x} -- {match}")
            if cfgv != fwv:
                print("      [!] MISMATCH: config reads do NOT track live")
                print("          state on this block -- every config-read")
                print("          conclusion above (incl. the discriminator")
                print("          match) may be a boot snapshot. Treat all")
                print("          config-window data on this block as")
                print("          suspect until re-established.")
        if dom6_frame is not None:
            print("    (a MATCH on a register that changed post-boot proves")
            print("     the config read path is LIVE, not a snapshot -- the")
            print("     basis for trusting the 'store not observed' verdicts)")
    except Exception as e:
        print(f"    live-tracking check skipped ({e.__class__.__name__})")

    def dump_slice(label, base, dwords):
        vals = {}
        for i in range(dwords):
            a = base + i * 4
            vals[a] = rd_smn(a)
            print(f"    {label} +0x{i * 4:03x}  @SMN 0x{a:08x} -> 0x{vals[a]:08x}")
        live = [v for v in vals.values() if v not in (0x00000000, 0xFFFFFFFF)]
        return vals, live

    # ---- step 1: THM slice (first-ever 0x024-frame read via this window) ----
    print("\n    step 1: THM slice head -- FIRST 0x024-frame read through this")
    print("    window (live IP; July #5 says dead addresses read clean")
    print("    0xffffffff here, but a wedged window = reboot/cold cycle) ...")
    thm_vals, thm_live = dump_slice("THM ", THM_SMN_BASE, 8)

    # ---- step 2: GC slice ----
    print("\n    step 2: GC slice head (second live-IP opinion) ...")
    gc_vals, gc_live = dump_slice("GC  ", GC_SMN_BASE, 4)

    if not thm_live and not gc_live:
        print("\n    [!] BOTH live-IP slices read dead (only 0x00000000/0xFFFFFFFF)")
        print("        -> the 0x024 fabric frame is NOT readable through the")
        print("           config window on this box. VCN probe SKIPPED (it")
        print("           could only add risk, not information). Remaining")
        print("           paths: the July TA/INVOKE_CMD route, or the MMIO")
        print("           read gamble after --manual-powerup.")
        return None
    if thm_live:
        print("    -> THM slice shows live values: the 0x024 frame IS readable")
    if gc_live:
        print("    -> GC slice shows live values: the 0x024 frame IS readable")
    print("       through the config window -- proceeding to VCN.")

    # ---- step 3: the VCN slice ----
    print("\n    step 3: VCN slice dump (0x02403000 + 0x00..0x3C) -- the goal.")
    print("    Slice semantics are UNKNOWN (not a register-file mirror); if")
    print("    anything SEG0-like lives here, the PGFSM/POWER_STATUS family")
    print("    spellings would be at +0x00/+0x04/+0x10/+0x1C -- treat the")
    print("    dump as raw until a pattern proves itself ...")
    vcn_vals, vcn_live = dump_slice("VCN ", VCN_SMN_BASE, 16)

    distinct = set(vcn_vals.values())
    if vcn_live:
        print("    -> VCN's fabric slice RESPONDS through the config window:")
        print("       differentiated values (island up, or slice decoupled")
        print("       from the island). Diff against a post-(--manual-powerup)")
        print("       re-run to correlate with the rail.")
    elif distinct == {0xFFFFFFFF}:
        print("    -> VCN's slice reads all-0xffffffff: no responder behind")
        print("       the slice address (frame unrouted for this slice, or")
        print("       the island/slice is dead). Cannot distinguish from")
        print("       here; the live THM/GC slices show the frame itself")
        print("       routes, so this is specific to VCN's slice.")
    else:
        print("    -> VCN's slice reads uniform-zero: reset state or dead")
        print("       slice. Re-run after --manual-powerup and compare.")
    return vcn_vals


def _window_route_reads(smu):
    """ROUTE W: the SMU data window (transfer engine) at 0x0110000+addr&0xFFFFF.

    The fw's own mirror path -- the one that reads the dom6 0x6d1xx block
    live on every run -- pointed at the 0x1F8xx family (rd_win refuses the
    range; Q3 msg 0x2A wedges there). MEASURED 2026-08-20 evening: STALL on
    the FIRST read (SmuTimeout after 5001 ms on 0x0111F81C), a HARD wedge
    with NO 12s self-recover -- cold power-cycle only. The host side is
    pure mailbox traffic (request + timeout), so a stall costs an
    SmuTimeout, never a process hang; no thunk is installed in this mode.
    REINTERPRETED 2026-08-24 (address-space fix): the window spans the
    0x01100000 SMN frame ONLY (1MB) -- 0x0111F810 was an NBIO-frame offset
    with no responder, and the window can NEVER express VCN's real fabric
    address 0x02403010 (masking to 20 bits aliases it to 0x03010). This
    route is structurally unable to reach VCN regardless of power state.
    DO NOT run this route again -- the mode is retired and this code is
    kept only for completeness.
    """
    print("\n[*] ROUTE W -- SMU data window (transfer engine, 0x0110000+addr):")
    print("[!] MEASURED HAZARD (2026-08-20 evening): this read STALLS on the")
    print("    first attempt and hard-wedges the SMU with NO 12s self-recover")
    print("    -- cold power-cycle is the only recovery. You opted in with")
    print("    --vcn-power-regs-w; this run may cost you a cold cycle.")
    try:
        v = int.from_bytes(smu.smu_read(WIN_BASE + 0x6d184, 1), "little")
    except Exception as e:
        print(f"    [!] window sanity read (dom6 rail 0x6d184) failed: "
              f"{e.__class__.__name__} -- transfer engine not answering;")
        print("        route W aborted (the SMU is likely already wedged).")
        return None
    print(f"    sanity: dom6 rail @window 0x{WIN_BASE + 0x6d184:08x} -> "
          f"0x{v:08x} (proven target) -- window live")

    vals = {}
    for label, smn in (("CC_UVD_HARVESTING", UVD_HARVESTING_SMN),
                       ("UVD_POWER_STATUS",  UVD_POWER_STATUS_SMN)):
        waddr = WIN_BASE + (smn & 0xFFFFF)
        print(f"    {label:<18} window 0x{waddr:08x} (SMN 0x{smn:08x}) ...")
        t0 = time.monotonic()
        try:
            v = int.from_bytes(smu.smu_read(waddr, 1), "little")
        except (SmuError, SmuTimeout) as e:
            dt = (time.monotonic() - t0) * 1000.0
            print(f"    -> {e.__class__.__name__} after {dt:.0f} ms: STALL -- no")
            print("       responder behind the mirror at SMN 0x1F8xx. Same")
            print("       fabric verdict as the July msg-0x2A wedge: the")
            print("       SMU-side path cannot enter the gated VCN island.")
            print("[*] waiting 12s for the SMU to self-recover ...")
            time.sleep(12)
            if debug_alive(smu):
                print("[+] SMU recovered via the debug path.")
            else:
                print("[!] SMU still not answering -- COLD POWER-CYCLE.")
            return vals
        dt = (time.monotonic() - t0) * 1000.0
        vals[smn] = v
        print(f"    -> 0x{v:08x} ({dt:.0f} ms)")
    return vals


def vcn_power_regs_report(smu, run_w=False):
    """Standalone diagnostic: probe VCN's fabric slice via the config window.

    MODEL v2 (2026-08-24 evening): there is NO known SMN spelling of
    mmUVD_POWER_STATUS / mmCC_UVD_HARVESTING -- the 0x024xxxxx fabric slices
    are small per-IP apertures, not register-file mirrors, and their contents
    are unknown per IP. So the old framing ("read UVD_POWER_STATUS at SMN
    0x02403010") is retracted; what this diagnostic actually does is dump
    VCN's slice (0x02403000 + 0x00..0x3C) through the ONE transport proven
    to take full 32-bit SMN addresses (PCI config 0xB8/0xBC, root device),
    gated behind live-IP slice reads (THM/GC) so the first-ever 0x024-frame
    read aims at the safest targets. If the slice responds, the values --
    whatever they are -- become the power-state oracle to diff against a
    post-(--manual-powerup) re-run. Route W (SMU data window) stays retired:
    measured 2026-08-20 to hard-wedge on 0x0111F8xx, AND structurally unable
    to reach the 0x024 frame (the window is 20-bit-masked to 0x01100000).
    """
    print("\n===== VCN fabric-slice probe (0x02403000 via config 0xB8/0xBC) =====")
    print("[*] question: does VCN's fabric slice RESPOND through the PCI-config")
    print("    SMN window, and do its contents move with the dom6 rail? (No")
    print("    register-level semantics are claimed for the slice -- see the")
    print("    address-space model v3 in the constants block.)")

    pv = _fabric_window_reads(smu)
    if not run_w:
        print("\n[*] ROUTE W -- SKIPPED (retired): the SMU data-window read of")
        print("    0x0111F8xx was MEASURED (2026-08-20 evening) to hard-wedge the")
        print("    SMU with NO self-recover -- and the window structurally cannot")
        print("    reach VCN's 0x02403000 fabric frame anyway (1MB window into the")
        print("    0x01100000 frame only). Opt in with --vcn-power-regs-w if you")
        print("    really want to re-measure the wedge.")
        wv = {}          # not run: retired (measured hard wedge)
    else:
        wv = _window_route_reads(smu)   # {} = ran+stalled, None = aborted

    print("\n[*] VERDICT (fabric-slice probe):")
    if pv is None:
        print("    - route P produced no VCN slice data (the 0x024 frame read")
        print("      dead-zero on the live-IP anchors -- MEASURED 2026-08-25,")
        print("      the slice probe carries no information on this box). The")
        print("      step-0 frame discriminator above still stands on its own:")
        print("      if it matched the dom6 sequencer, the lever is")
        print("      --manual-powerup --config-writes (drive the rail through")
        print("      the config window at the matched spelling); the VCN-side")
        print("      arbiters remain the MMIO read gamble after the rail")
        print("      attempt, or the July TA/INVOKE_CMD route.")
    else:
        vals = set(pv.values())
        if vals == {0xFFFFFFFF}:
            print("    - VCN slice: no responder (all 0xffffffff) while THM/GC")
            print("      slices are live -- the frame routes, VCN's slice does")
            print("      not answer. Consistent with a dead island behind the")
            print("      slice, or a slice the PSP never mapped. The MMIO read")
            print("      gamble and the TA/INVOKE_CMD path are the arbiters.")
        elif vals == {0x00000000}:
            print("    - VCN slice: uniform zero -- reset state or dead slice.")
            print("      Re-run after --manual-powerup and diff (the dom6 rail")
            print("      moving these zeros to anything else = the oracle hit).")
        else:
            print("    - VCN slice: LIVE, differentiated values through the")
            print("      config window. This is the first CPU-side window into")
            print("      anything VCN on this box. Next: (a) re-run after")
            print("      --manual-powerup and diff, (b) if a dword tracks the")
            print("      power sequence, THAT is the power-gate control to")
            print("      drive (and the July msg-0x98 write primitive can")
            print("      reach it), (c) correlate +0x00/+0x04/+0x10/+0x1C with")
            print("      the SEG0 PGFSM/POWER_STATUS spellings before trusting")
            print("      any register-level reading.")
    if wv:
        print("    - route W (opt-in) result retained above for the record; it")
        print("      cannot address the fabric frame (20-bit window).")


# ------------- the fire: the unlock library's Q3 mailbox send -------------
def fire_sequence(smu, msg_id):
    """Ring the fw's Queue-3 doorbell THROUGH THE UNLOCK LIBRARY.

    send_message(3, msg_id) issues the exact register sequence the earlier
    raw fire used -- rsp := 0, arg0..arg5 := 0, cmd := msg_id (SMN
    0x03B10A20) -- over the library's own flock-guarded PCI-config
    transport, then polls the response register. The Discord sequence does
    NOT complete the mailbox protocol (it builds its own frame and returns
    without setting a response), so that poll is EXPECTED to end in
    SmuTimeout after the mailbox timeout -- the wait doubles as the
    dispatch wait. Same pattern as the sibling tools' msg-0x61 fires
    (vcn_fullon_bios3.py fire(): send_message(check_status=False) +
    tolerated SmuTimeout). A DONE status would mean the dispatcher
    completed the message itself -- reported, not required.
    Returns True iff the mailbox completed."""
    cmd_addr, rsp_addr, arg_addr = DEFAULT_QUEUE_ADDRS[3]
    print(f"[*] fire via the unlock library's mailbox send (Q3 msg 0x{msg_id:02x}):")
    print(f"    rsp  @SMN 0x{rsp_addr:08x} <- 0")
    print(f"    args @SMN 0x{arg_addr:08x} <- 0 x6")
    print(f"    cmd  @SMN 0x{cmd_addr:08x} <- 0x{msg_id:02x}   (msg 0x61 -> thunk @0x{THUNK_ADDR:x})")
    try:
        st, ret = smu.send_message(3, msg_id, [], check_status=False)
        print(f"    -> mailbox COMPLETED: status=0x{st:02x} ret=0x{ret:08x}")
        return True
    except SmuTimeout:
        print("    -> SmuTimeout (EXPECTED: the Discord sequence does not complete")
        print("       the mailbox protocol; the doorbell rang, the sequence was")
        print("       dispatched -- the debug-path liveness check below is the verdict)")
        return False

def debug_alive(smu):
    """Liveness probe via the unlocked debug path only (no mailbox):
    read the debug-disable byte back through the transfer engine."""
    try:
        rd_sram(smu, 0x7B3C, 1)
        return True
    except Exception:
        return False


# ---------- GPU-side debugfs + VRAM transport (shared by --direct-load) ----------
# amdgpu debugfs is the raw MMIO/VRAM transport of the userspace direct load
# (stage 6 below) -- the ONLY part of this tool that does not flow through
# the unlock library, because the SMU physically cannot proxy it: every SMU
# route into the VCN register block is a measured hard wedge (CPU MMIO
# all-ones / PCIE iso-clamp / msg 0x2A stall / transfer-engine stall, all
# 2026-08-20). The former PSP GPCOM submit machinery that used to live here
# was removed with --load-fw (verdict: ITEM_NOT_FOUND at both layers -- the
# console TEE has no fw_type-13 slot; see the module docstring).

VRAM_MC_BASE = 0xf400000000   # BIOS-3 fallback; runtime value comes from GCMC FB_LOCATION

# MP0 C2PMSG register byte offsets in amdgpu_regs (the card-identity check
# reads the kernel PSP ring address through C2PMSG_69/70):
#   MP0 base = 0x16000 DWORDs; C2PMSG_N at MP0 + (0x40 + N) DWORDs
#   byte offset = (0x16000 + 0x40 + N) * 4 = (0x16040 + N) * 4
def c2pmsg(n):
    return (0x16040 + n) * 4

C2PMSG_69 = c2pmsg(69)   # kernel PSP ring addr low
C2PMSG_70 = c2pmsg(70)   # kernel PSP ring addr high (may be 0xf4 or 0xf5 in 8GB VRAM)

def find_regs():
    base = os.environ.get("BC250_DEBUGFS_DIR", "/sys/kernel/debug/dri")
    for n in range(8):
        p = os.path.join(base, str(n), "amdgpu_regs")
        if os.path.exists(p):
            return p
    sys.exit("amdgpu_regs not found (debugfs mounted? driver loaded?)")

def find_vram():
    base = os.environ.get("BC250_DEBUGFS_DIR", "/sys/kernel/debug/dri")
    for n in range(8):
        p = os.path.join(base, str(n), "amdgpu_vram")
        if os.path.exists(p):
            return p
    sys.exit("amdgpu_vram not found")

def read_reg(f, off):
    f.seek(off)
    data = f.read(4)
    if len(data) != 4:
        raise IOError(f"short read at reg 0x{off:06x} (got {len(data)} bytes)")
    return struct.unpack('<I', data)[0]

def write_reg(f, off, val):
    f.seek(off)
    f.write(struct.pack('<I', val & 0xFFFFFFFF))

def load_firmware(path, raw=False):
    """Load firmware file, auto-decompress .xz (formerly psp_inject.py's).

    raw=False (default): strip common_firmware_header, return raw ucode --
      exactly what the kernel copies to VRAM for the PSP (amdgpu_ucode.c):
        ucode_size = le32(header.ucode_size_bytes)
        ucode_addr = fw_data + le32(header.ucode_array_offset_bytes)

    raw=True: return the file as-is (after .xz decompression). For
      $PS1-wrapped blobs (auto-detected by magic at offset 0x10).

    Returns (raw_bytes, ucode_size, info_dict).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"firmware not found: {path}")

    # Auto-decompress .xz (kernel does this transparently via firmware_class)
    if path.endswith('.xz'):
        import lzma
        with lzma.open(path, 'rb') as f:
            data = f.read()
        print(f"    decompressed .xz: {len(data)} bytes")
    else:
        with open(path, 'rb') as f:
            data = f.read()

    # Auto-detect $PS1 format (Sony's signed wrapper): magic at 0x10
    is_ps1 = len(data) > 0x14 and data[0x10:0x14] == b'$PS1'
    if is_ps1:
        print(f"    $PS1 wrapper detected (Sony signed format)")
        if data[0xA0:0xA4] in (b'AW1B', b'AW2B'):
            print(f"    marker: {data[0xA0:0xA4]} (AGESA Boot Loader)")
        raw = True  # force raw mode for $PS1 blobs

    if raw or is_ps1:
        info = {
            'file_size':      len(data),
            'header_size':    0,
            'header_version': 'raw/$PS1',
            'ucode_version':  0,
            'ucode_size':     len(data),
            'ucode_offset':   0,
            'crc32':          0,
        }
        return data, len(data), info

    if len(data) < 256:
        raise ValueError(f"firmware too small: {len(data)} bytes (need >= 256 for header)")

    # Parse common_firmware_header (amdgpu_ucode.h):
    #   +0 u32 hdr_size  +4/+6 u16 ver maj/min  +8 u32 ip_version_id
    #   +12 u64 ucode_version  +20 u32 ucode_size  +24 u32 ucode_offset
    #   +28 u32 crc32
    hdr_size       = struct.unpack_from('<I', data, 0)[0]
    ver_major      = struct.unpack_from('<H', data, 4)[0]
    ver_minor      = struct.unpack_from('<H', data, 6)[0]
    ucode_version  = struct.unpack_from('<Q', data, 12)[0]
    ucode_size     = struct.unpack_from('<I', data, 20)[0]
    ucode_offset   = struct.unpack_from('<I', data, 24)[0]
    crc32          = struct.unpack_from('<I', data, 28)[0]

    info = {
        'file_size':      len(data),
        'header_size':    hdr_size,
        'header_version': f"{ver_major}.{ver_minor}",
        'ucode_version':  ucode_version,
        'ucode_size':     ucode_size,
        'ucode_offset':   ucode_offset,
        'crc32':          crc32,
    }

    # Extract raw ucode (exactly what kernel copies to VRAM for PSP)
    raw = data[ucode_offset:ucode_offset + ucode_size]
    if len(raw) != ucode_size:
        raise ValueError(
            f"firmware truncated: expected {ucode_size} bytes at offset {ucode_offset}, "
            f"file has {len(data)} bytes, got {len(raw)}")

    return raw, ucode_size, info

NAVI10_FW_SEARCH = [
    # distro path (bazzite/Fedora ships it COMPRESSED here; /lib is usually a
    # symlink to /usr/lib, but keep both spellings for non-merged-usr distros).
    # .xz entries first: that's what linux-firmware packages actually install.
    # Decompression is automatic (load_firmware above: lzma + AMD header
    # strip), so a .xz is just as good as a plain .bin.
    "/usr/lib/firmware/amdgpu/navi10_vcn.bin.xz",
    "/usr/lib/firmware/amdgpu/navi10_vcn.bin",
    "/lib/firmware/amdgpu/navi10_vcn.bin.xz",
    "/lib/firmware/amdgpu/navi10_vcn.bin",
    # dev-box checkout
    "/home/OWNER/linux-firmware/amdgpu/navi10_vcn.bin",
    # fallback: renoir is the same VCN 2.x APU family
    # (NOTE, diffed 2026-08-24: renoir_vcn.bin and navi10_vcn.bin are
    #  byte-identical except ONE version-tag byte at file offset 0x0E --
    #  the "fallback" is the same microcode, so switching between them
    #  is not a debugging lever)
    "/usr/lib/firmware/amdgpu/renoir_vcn.bin.xz",
    "/usr/lib/firmware/amdgpu/renoir_vcn.bin",
    "/lib/firmware/amdgpu/renoir_vcn.bin.xz",
    "/lib/firmware/amdgpu/renoir_vcn.bin",
]

# ---------- optional stage 6: USERSPACE direct VCN firmware load ----------
# What: stage the navi10 VCN fw in VRAM ourselves and bring the VCN block up
# ENTIRELY from userspace -- replicating the kernel's own AMDGPU_FW_LOAD_DIRECT
# path register-for-register (amdgpu_vcn_resume + vcn_v2_0_mc_resume DIRECT
# branch + vcn_v2_0_start NON-DPG branch), then prove the microcontroller
# executes our image with the driver's own ring test (vcn_v2_0_dec_ring_test_ring:
# SCRATCH9 0xCAFEDEAD -> 0xDEADBEEF via a PACKET0 register-write the fw performs).
#
# Why: Wall B (fw_type 13 has no TEE slot) is confirmed at BOTH layers (driver
# boot-time load and manual GPCOM submit, 2026-08-20). The direct path never
# asks the TEE. The kernel never brings VCN up on this card, so the VCN
# register block is untouched by the driver -- ours to program. The Discord
# fire (dom6 slots 0x16/17/18) is the clock enabler. amdgpu must be LOADED
# only as the debugfs MMIO/VRAM access path (amdgpu_regs / amdgpu_vram); NO
# kernel VCN code runs. The doorbell (dec-ring wptr) is rung by writing the
# GPU's own PCI BAR2 (adev->doorbell.base = pci_resource_start(pdev, 2),
# amdgpu_doorbell_mgr.c:210) from userspace.
#
# Source map (torvalds/linux, drivers/gpu/drm/amd/):
#   amdgpu_vcn.c  amdgpu_vcn_resume()      -- non-PSP staging: ucode array ONLY
#                                              (header stripped) at bo start
#   vcn_v2_0.c    vcn_v2_0_mc_resume()     -- DIRECT branch: cache windows at
#                                              the driver's own VRAM bo
#   vcn_v2_0.c    vcn_v2_0_start()         -- non-DPG bring-up + VCPU boot poll
#   vcn_v2_0.c    vcn_v2_0_dec_ring_test_ring() -- the SCRATCH9 proof
#   navi10_ip_offset.h VCN_BASE__INST0_SEG1 = 0x07E00 (dwords)
#   vcn_2_0_0_offset.h / vcn_2_0_0_sh_mask.h -- offsets (BASE_IDX 1) and masks
#   nv.c nv_init_doorbell_index(): vcn_ring0_1 = 0x188 (AMDGPU_NAVI10_DOORBELL64_VCN0_1)

# ---- VCN register addressing (navi10) ----
# ALL mmUVD_* regs below are BASE_IDX 1: absolute MMIO byte offset in
# amdgpu_regs = (0x7E00 + off) * 4   [dword units -- same convention as the
# proven C2PMSG math above: mmMP0_SMN_C2PMSG_67=0x83, MP0 SEG0=0x16000 dwords]
VCN_SEG1_DW = 0x07E00
VCN_SEG0_DW = 0x07800          # SEG0 dwords (UVD0_BASE__INST0_SEG0 -- JPEG/decode cluster)

def _uvd(off):
    return (VCN_SEG1_DW + off) * 4

# vcn_2_0_0_offset.h (all BASE_IDX 1)
R_PGFSM_CONFIG     = 0x0000
R_PGFSM_STATUS     = 0x0001
R_POWER_STATUS     = 0x0004
R_SCRATCH2         = 0x0016
R_SCRATCH9         = 0x001d   # the proof register (external view)
R_GFX10_ADDR_CONFIG     = 0x004a
R_CGC_GATE              = 0x01ea
R_CGC_CTRL              = 0x01ec
R_LMI_CTRL2             = 0x01fd
R_MASTINT_EN            = 0x0200
R_LMI_CTRL              = 0x0226
R_LMI_STATUS            = 0x0227
R_LMI_SWAP_CNTL         = 0x022d
R_MPC_CNTL              = 0x0237
R_MPC_SET_MUXA0         = 0x0239
R_MPC_SET_MUXB0         = 0x023b
R_MPC_SET_MUX           = 0x023d
R_VCPU_CACHE_OFFSET0    = 0x0242
R_VCPU_CACHE_SIZE0      = 0x0243
R_VCPU_CACHE_OFFSET1    = 0x0244
R_VCPU_CACHE_SIZE1      = 0x0245
R_VCPU_CACHE_OFFSET2    = 0x0246
R_VCPU_CACHE_SIZE2      = 0x0247
R_VCPU_NONCACHE_OFFSET0 = 0x0254
R_VCPU_NONCACHE_SIZE0   = 0x0255
R_VCPU_CNTL             = 0x0258
R_SOFT_RESET            = 0x0260
R_LMI_RBC_RB_VMID       = 0x0263
R_RBC_RB_RPTR           = 0x0264
R_RBC_RB_WPTR           = 0x0265
R_RBC_RB_CNTL           = 0x0269
R_STATUS                = 0x026f   # bit0 RBC_BUSY, bits[7:1] VCPU_REPORT
R_CONTEXT_ID            = 0x027d
R_RB_BASE_LO2           = 0x05e1
R_RB_BASE_HI2           = 0x05e2
R_RB_SIZE2              = 0x05e3
R_RB_RPTR2              = 0x05e4
R_RB_WPTR2              = 0x05e5
R_RB_BASE_LO            = 0x05e6
R_RB_BASE_HI            = 0x05e7
R_RB_SIZE               = 0x05e8
R_RB_RPTR               = 0x05e9
R_RB_WPTR               = 0x05ea
R_LMI_VCPU_CACHE_64BIT_BAR_HIGH  = 0x061e
R_LMI_VCPU_CACHE_64BIT_BAR_LOW   = 0x061f
R_LMI_VCPU_NC0_64BIT_BAR_HIGH    = 0x0622
R_LMI_VCPU_NC0_64BIT_BAR_LOW     = 0x0623
R_LMI_RBC_RB_64BIT_BAR_HIGH      = 0x0628
R_LMI_RBC_RB_64BIT_BAR_LOW       = 0x0629
R_LMI_VCPU_CACHE1_64BIT_BAR_LOW  = 0x05ac
R_LMI_VCPU_CACHE1_64BIT_BAR_HIGH = 0x05ad
R_LMI_VCPU_CACHE2_64BIT_BAR_LOW  = 0x05b0
R_LMI_VCPU_CACHE2_64BIT_BAR_HIGH = 0x05b1

# bit masks (vcn_2_0_0_sh_mask.h + amdgpu_vcn.h enums)
M_VCPU_SOFT_RESET   = 0x00000008   # UVD_SOFT_RESET__VCPU_SOFT_RESET_MASK
M_LMI_SOFT_RESET    = 0x00000004   # UVD_SOFT_RESET__LMI_SOFT_RESET_MASK
M_LMI_UMC_SOFT_RESET= 0x00002000   # UVD_SOFT_RESET__LMI_UMC_SOFT_RESET_MASK
M_VCPU_CNTL_CLK_EN  = 0x00000200   # UVD_VCPU_CNTL__CLK_EN_MASK
M_MASTINT_VCPU_EN   = 0x00000002   # UVD_MASTINT_EN__VCPU_EN_MASK
M_LMI_CTRL_COHER    = (0x00000100 | 0x00001000 | 0x00002000 | 0x00200000)
  # WRITE_CLEAN_TIMER_EN | MASK_MC_URGENT | DATA_COHERENCY_EN | VCPU_DATA_COHERENCY_EN
M_STALL_ARB_UMC     = 0x00000100   # UVD_LMI_CTRL2__STALL_ARB_UMC_MASK
M_CGC_GATE_ALL      = 0x000FFFFF   # SYS..SCPU (21 bits) -- disable_clock_gating clears all
UVD_STATUS_BUSY     = 0x4          # amdgpu_vcn.h: UVD_STATUS__UVD_BUSY
UVD_STATUS_IDLE     = 0x2          # amdgpu_vcn.h: UVD_STATUS__IDLE (VCPU_REPORT=1)
M_LMI_STATUS_CLEAN  = 0x0000000F   # VCPU_LMI_WRITE_CLEAN|READ_CLEAN|WRITE_CLEAN|WRITE_CLEAN_RAW
M_LMI_STATUS_UMC    = 0x00000240   # UMC_READ_CLEAN_RAW|UMC_WRITE_CLEAN_RAW

# fw-internal register offsets used inside ring packets (vcn_v2_0.c:44-56).
# These are the VCPU-side addresses the RBC writes -- NOT the MMIO offsets.
INT_GPCOM_CMD       = 0x503
INT_GPCOM_DATA0     = 0x504
INT_GPCOM_DATA1     = 0x505
INT_SCRATCH9        = 0xc01d

# dec-ring packet values (amdgpu_vcn.h)
VCN_DEC_KMD_CMD     = 0x80000000
VCN_DEC_CMD_PACKET_START = 0x0a

# layout constants (amdgpu_vcn.h)
VCN_STACK_SIZE      = 128 * 1024
VCN_CONTEXT_SIZE    = 512 * 1024
AMDGPU_UVD_FIRMWARE_OFFSET = 256      # amdgpu_uvd.h -- VCPU_CACHE_OFFSET0 = 256>>3
AMDGPU_VCN_MULTI_QUEUE_FLAG = (1 << 8)  # amdgpu_vcn.h -- fw_shared present_flag_0
VCN_RB_SIZE         = 4096            # dec/enc ring bytes: max_dw(512)*4*sched_hw_submission(2)
DEC_RB_BUFSZ        = 12              # order_base_2(4096) -> RBC_RB_CNTL RB_BUFSZ field
ENC_RB_SIZE_DW      = 1024            # 4096/4 dwords -> mmUVD_RB_SIZE

# doorbell (navi10): vcn_ring0_1 = 0x188 (64-bit slot) -> dec-ring dword index
# 0x188<<1 = 0x310 -> BAR2 byte offset 0x310*4 (amdgpu_mm_wdoorbell: u32* + index)
DB_DEC_INDEX_DW     = 0x188 << 1
DB_DEC_BYTE         = DB_DEC_INDEX_DW * 4

# nbio: mmBIF_MMSCH0_DOORBELL_RANGE (BASE_IDX 2; NBIO SEG2 = 0xD20 dwords)
NBIO_SEG2_DW        = 0x00D20
BIF_MMSCH0_DB_RANGE = (NBIO_SEG2_DW + 0x01D3) * 4
MMSCH_DB_RANGE_OFF_MASK  = 0x00000FFC   # <<2
MMSCH_DB_RANGE_OFF_SHIFT = 2
MMSCH_DB_RANGE_SIZE_MASK = 0x001F0000   # <<16
MMSCH_DB_RANGE_SIZE_SHIFT= 16

# GC: register offsets in gc_10_1_0_offset.h, GC SEG0 = 0x1260 dwords.
GC_SEG0_DW = 0x1260
GB_ADDR_CONFIG_BYTE = (GC_SEG0_DW + 0x13DE) * 4
GCMC_VM_FB_LOCATION_BASE_BYTE = (GC_SEG0_DW + 0x1720) * 4
GCMC_VM_FB_LOCATION_TOP_BYTE = (GC_SEG0_DW + 0x1721) * 4

# BC250 PCI id (auto-detect for the doorbell BAR)
BC250_PCI_ID = (0x1002, 0x13FE)


def _pkt0(reg, n=0):
    """PACKET0 header (soc15d.h): (0<<30) | (reg & 0xFFFF) | ((n & 0x3FFF) << 16)."""
    return (reg & 0xFFFF) | ((n & 0x3FFF) << 16)


def find_bc250_bdf():
    """Locate the BC250 GPU (1002:13FE) for the doorbell BAR2."""
    import glob
    for d in sorted(glob.glob("/sys/bus/pci/devices/*")):
        try:
            with open(os.path.join(d, "vendor")) as f:
                v = int(f.read().strip(), 16)
            with open(os.path.join(d, "device")) as f:
                dev = int(f.read().strip(), 16)
        except (IOError, ValueError):
            continue
        if (v, dev) == BC250_PCI_ID:
            return os.path.basename(d)
    return None


class VcnDirect:
    """Userspace replication of the vcn_v2_0 DIRECT (non-PSP, non-DPG) path.

    MMIO:  amdgpu_regs debugfs (same proven transport the PSP path uses).
    VRAM:  amdgpu_vram debugfs (4-byte aligned; large writes are slow).
    Doorbell: PCI BAR2 (adev->doorbell.base) via sysfs resource2 mmap.
    """

    def __init__(self):
        self.rf = open(find_regs(), 'r+b', buffering=0)
        self.vram_fd = os.open(find_vram(), os.O_RDWR)
        self.db = None

    # ---- MMIO ----
    def rd(self, off):
        return read_reg(self.rf, off)

    def wr(self, off, val):
        write_reg(self.rf, off, val)

    def rmw(self, off, and_mask=0xFFFFFFFF, or_mask=0):
        v = (self.rd(off) & and_mask) | or_mask
        self.wr(off, v)
        return v

    def wait_reg(self, off, mask, val, timeout, label):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            v = self.rd(off)
            if (v & mask) == val:
                return True, v, time.monotonic() - t0
            time.sleep(0.005)
        return False, self.rd(off), time.monotonic() - t0

    # ---- VRAM ----
    def vr_read(self, off, size):
        os.lseek(self.vram_fd, off, os.SEEK_SET)
        data = b''
        while len(data) < size:
            chunk = os.read(self.vram_fd, size - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def vr_write(self, off, data):
        if len(data) & 0x3 or off & 0x3:
            raise ValueError(f"misaligned VRAM write: off=0x{off:x} len={len(data)}")
        os.lseek(self.vram_fd, off, os.SEEK_SET)
        total = 0
        while total < len(data):
            n = os.write(self.vram_fd, data[total:])
            if n <= 0:
                raise IOError(f"VRAM write failed at 0x{off + total:x}")
            total += n
        return total

    def vr_read32(self, off):
        return struct.unpack('<I', self.vr_read(off, 4))[0]

    def vr_write32(self, off, val):
        self.vr_write(off, struct.pack('<I', val & 0xFFFFFFFF))

    def vr_write_byte(self, off, val):
        """Byte-granular VRAM write via dword RMW (write_vram needs 4B align)."""
        base = off & ~3
        d = self.vr_read32(base)
        shift = (off & 3) * 8
        d = (d & ~(0xFF << shift)) | ((val & 0xFF) << shift)
        self.vr_write32(base, d)

    # ---- doorbell (PCI BAR2) ----
    def doorbell_open(self, bdf):
        import mmap as _mmap
        path = f"/sys/bus/pci/devices/{bdf}/resource2"
        fd = os.open(path, os.O_RDWR | os.O_SYNC)
        size = os.fstat(fd).st_size
        if size < DB_DEC_BYTE + 4:
            os.close(fd)
            raise RuntimeError(f"BAR2 too small ({size:#x}) for doorbell {DB_DEC_BYTE:#x}")
        self.db = _mmap.mmap(fd, size, _mmap.MAP_SHARED,
                             _mmap.PROT_READ | _mmap.PROT_WRITE)
        os.close(fd)   # mmap keeps the mapping alive
        return size

    def doorbell_ring(self, value):
        self.db[DB_DEC_BYTE:DB_DEC_BYTE + 4] = struct.pack('<I', value & 0xFFFFFFFF)


def attempt_direct_load(fw_path, fw_vram_off=None, park=True):
    """Stage the navi10 VCN fw in VRAM and boot VCN from userspace.

    Replicates, register-for-register, the kernel's non-PSP VCN 2.0 path
    (non-DPG), then runs the driver's own ring test as the proof of life.
    Returns True only if SCRATCH9 flips 0xCAFEDEAD -> 0xDEADBEEF (i.e. the
    VCN microcontroller fetched our ring packets from VRAM and executed
    them as register writes).
    """
    print("\n[*] USERSPACE direct VCN firmware load (no PSP, no TEE, no kernel VCN code)")

    # ---- phase 0: prerequisites ----
    try:
        regs_path = find_regs()
        vram_path = find_vram()
    except SystemExit as e:
        sys.exit("[!] amdgpu debugfs not available: {}\n"
                 "    The direct path uses amdgpu_regs/amdgpu_vram as its raw MMIO/VRAM\n"
                 "    transport -- amdgpu must be LOADED. Un-blacklist and reboot.".format(e))
    print(f"    regs: {regs_path}")
    print(f"    vram: {vram_path}")

    bdf = find_bc250_bdf()
    if bdf is None:
        print("[!] BC250 (1002:13FE) not on the PCI tree -- no doorbell BAR2. Aborting.")
        return False

    v = VcnDirect()
    try:
        db_size = v.doorbell_open(bdf)
        print(f"    BC250:  {bdf}   doorbell BAR2 {db_size // 1024}KB "
              f"(dec-ring wptr doorbell @ byte 0x{DB_DEC_BYTE:x})")
    except (IOError, RuntimeError) as e:
        print(f"[!] doorbell BAR2 unavailable: {e}")
        return False

    # Card identity + runtime VRAM MC range. The old check required the PSP
    # ring's high dword to equal 0xf4, but this 8GB card legitimately allocates
    # the ring in the upper 4GB at 0xf5fffe0000. Validate the debugfs BDF and
    # that the complete ring address lies inside GCMC's live FB range instead.
    debugfs_bdf = os.path.basename(os.path.realpath(os.path.dirname(regs_path)))
    if debugfs_bdf != bdf:
        print(f"[!] debugfs device {debugfs_bdf} != detected BC250 {bdf}. Aborting.")
        print("    On a multi-GPU box: export BC250_DEBUGFS_DIR=/sys/kernel/debug/dri/N "
              "for the BC250 and re-run.")
        return False
    fb_base_raw = v.rd(GCMC_VM_FB_LOCATION_BASE_BYTE)
    fb_top_raw = v.rd(GCMC_VM_FB_LOCATION_TOP_BYTE)
    vram_mc_base = fb_base_raw << 24
    vram_mc_end = (fb_top_raw + 1) << 24
    ring_addr = (v.rd(C2PMSG_70) << 32) | v.rd(C2PMSG_69)
    if not (vram_mc_base <= ring_addr < vram_mc_end):
        print(f"[!] PSP ring MC address 0x{ring_addr:012x} is outside live FB range "
              f"0x{vram_mc_base:012x}..0x{vram_mc_end - 1:012x}. Aborting.")
        return False
    print(f"    debugfs device {debugfs_bdf} -- BC250 identity confirmed")
    print(f"    live FB MC range 0x{vram_mc_base:012x}..0x{vram_mc_end - 1:012x}; "
          f"PSP ring 0x{ring_addr:012x} inside range")

    gb_addr = v.rd(GB_ADDR_CONFIG_BYTE)
    print(f"    mmGB_ADDR_CONFIG = 0x{gb_addr:08x} (will be mirrored into UVD_GFX10_ADDR_CONFIG)")
    if not gb_addr or gb_addr == 0xFFFFFFFF:
        print("[!] mmGB_ADDR_CONFIG unreadable -- wrong debugfs device or GC down. Aborting.")
        return False

    # ---- phase 1: firmware ----
    if not fw_path:
        fw_path = next((p for p in NAVI10_FW_SEARCH if os.path.exists(p)), None)
        if fw_path is None:
            sys.exit("[!] no VCN firmware found (searched: {})\n"
                     "    pass --direct-load /path/to/navi10_vcn.bin".format(
                         ", ".join(NAVI10_FW_SEARCH)))
    print(f"[*] firmware: {fw_path}")
    raw_fw, fw_size, fw_info = load_firmware(fw_path)
    print(f"    header version: {fw_info['header_version']}   "
          f"ucode_version: 0x{fw_info['ucode_version']:016x}")
    print(f"    ucode: {fw_size} bytes (AMD header stripped -- exactly what")
    print(f"           amdgpu_vcn_resume() copies to the bo start in DIRECT mode)")

    # ---- phase 2: staging layout + zero-probe + write ----
    fw_win = (fw_info['file_size'] + 4 + 0xFFF) & ~0xFFF   # VCPU_CACHE_SIZE0
    span = fw_win + VCN_STACK_SIZE + VCN_CONTEXT_SIZE + 4 * 4096
    off_fw      = 0
    off_stack   = fw_win
    off_ctx     = off_stack + VCN_STACK_SIZE
    off_dec_rb  = off_ctx + VCN_CONTEXT_SIZE
    off_enc0_rb = off_dec_rb + VCN_RB_SIZE
    off_enc1_rb = off_enc0_rb + VCN_RB_SIZE
    off_shared  = off_enc1_rb + VCN_RB_SIZE
    assert off_shared + 4096 == span

    if fw_vram_off is None:
        cands = [0x800000 + k * 0x200000 for k in range(8)]   # 8MB..24MB
    else:
        cands = [fw_vram_off & ~0xFFF]

    print(f"[*] staging span {span // 1024}KB: fw {fw_win // 1024}KB + stack 128KB + "
          f"context 512KB + RBs 12KB + fw_shared 4KB")
    base = None
    for c in cands:
        probe = v.vr_read(c, span)
        if len(probe) == span and not any(probe):
            base = c
            print(f"    candidate 0x{c:08x}: all zero ({span} bytes verified) -- using it")
            break
        nz = sum(1 for b in probe if b)
        print(f"    candidate 0x{c:08x}: NOT zero ({nz} nonzero bytes) -- skipping")
    if base is None:
        print("[!] no clean staging span found in candidates -- aborting "
              "(would overwrite live data). Pass --fw-offset to pick one.")
        return False

    mc = lambda o: vram_mc_base + base + o
    print(f"[*] writing fw image + fw_shared to VRAM 0x{base:08x} "
          f"(MC 0x{mc(0):012x}) ...")
    t0 = time.monotonic()
    v.vr_write(base + off_fw, raw_fw)
    v.vr_write32(base + off_shared + 0, AMDGPU_VCN_MULTI_QUEUE_FLAG)
    print(f"    written in {time.monotonic() - t0:.1f}s")
    if v.vr_read(base + off_fw, 16) != raw_fw[:16]:
        print("[!] fw read-back mismatch after staging -- aborting")
        return False
    print(f"    fw_shared present_flag_0 = 0x{AMDGPU_VCN_MULTI_QUEUE_FLAG:08x} "
          f"(AMDGPU_VCN_MULTI_QUEUE_FLAG, vcn_v2_0_sw_init)")
    print("[+] staged and verified")

    # ---- phase 3: register bring-up (vcn_v2_0_start, non-DPG) ----
    print("\n[*] VCN bring-up (vcn_v2_0.c vcn_v2_0_start, non-DPG branch):")
    # ---- VCN MMIO segment ladder ----
    # MEASURED 2026-08-25 (this run, first hardware attempt post-everything):
    # POWER_STATUS reads 0xffffffff and the board does NOT hang -- the July
    # hang did not reproduce with clocks programmed + enables ON + gates
    # released. All-ones is now the measured SAFE behavior of a closed
    # island, so we can map HOW closed it is: one register is not a probe.
    # The ladder spans both segments and deliberately includes UVD_VERSION
    # (a static version constant -- the cleanest possible register-file
    # liveness bit: state registers can read dead while ROM-ish constants
    # still decode if only part of the island is gated).
    print("    [!] first VCN MMIO reads follow -- July measured BOARD HANGs on")
    print("        VCN-segment reads while the island is dead (userspace BAR5,")
    print("        UMR, kernel debugfs); MEASURED 2026-08-25 post-clock-work:")
    print("        all-ones + NO hang, twice. If this hangs: cold power-cycle.")
    LADDER = (
        ("UVD_PGFSM_CONFIG",   0x0000, 1, "SEG1 power-cluster head (PG FSM)"),
        ("UVD_PGFSM_STATUS",   0x0001, 1, "PG FSM state"),
        ("UVD_POWER_STATUS",   0x0004, 1, "static PG state"),
        ("CC_UVD_HARVESTING",  0x0007, 1, "harvest config"),
        ("UVD_JPEG_POWER_STATUS", 0x000A, 1, "JPEG PG state"),
        ("UVD_MASTINT_EN",     0x0200, 1, "SEG1 top-level"),
        ("UVD_STATUS",         0x026F, 1, "RBC/VCPU status"),
        ("UVD_VERSION",        0x05C9, 1, "STATIC VERSION CONSTANT -- liveness key"),
        ("UVD_NO_OP",          0x05BF, 1, "no-op register"),
        ("UVD_JPEG_CNTL",      0x0080, 0, "SEG0 head (JPEG decode)"),
        ("UVD_JRBC_STATUS",    0x0109, 0, "SEG0 JRBC"),
    )
    vals = {}
    for name, off, seg, note in LADDER:
        mmio = ((VCN_SEG1_DW if seg else VCN_SEG0_DW) + off) * 4
        vals[name] = v.rd(mmio)
        dead = "  <-- DEAD" if vals[name] == 0xFFFFFFFF else ""
        print(f"    {name:<22} MMIO 0x{mmio:05x} -> 0x{vals[name]:08x}{dead}"
              f"   ({note})")
    live = [n for n, x in vals.items() if x != 0xFFFFFFFF]
    if vals.get("UVD_POWER_STATUS") == 0xFFFFFFFF:
        if not live:
            print("[!] UNIFORM all-ones across BOTH segments (incl. the static")
            print("    UVD_VERSION constant): the whole VCN register file is")
            print("    clamped -- island closed at the root (rail/isolation),")
            print("    not a per-register artifact. GC reads fine through the")
            print("    same route (GB_ADDR_CONFIG above), so the transport is")
            print("    good. CONTRADICTION on the table: the SMU-side oracle")
            print("    (clocks + enables + gates + rail + up-residue status)")
            print("    says dom6 is UP while the island says CLOSED. Remaining")
            print("    suspects: (a) the fw's real power-up has steps the host")
            print("    replica lacks (enumerate the fw's own message handlers:")
            print("    --msg-table; decode FUN_00023b14's full body in the fw")
            print("    image), (b) an ISO/reset held outside the dom6 sequencer")
            print("    (--dom6-dump the whole block), (c) PSP-side isolation.")
            print("    NOTE: renoir -- same silicon family, working VCN -- opens")
            print("    the island via the PMFW message PPSMC_MSG_PowerUpVcn;")
            print("    this PMFW's driver message list (kernel smu_v11_8_ppsmc.h)")
            print("    has NO VCN message -- but its INTERNAL Q3 message space")
            print("    (the one this script speaks) is only partially mapped.")
        else:
            print(f"[!] PARTIAL: {', '.join(live)} read REAL values while")
            print("    POWER_STATUS is all-ones -- the register file is PARTIALLY")
            print("    alive (per-cluster gating, not a closed island). If")
            print("    UVD_VERSION answered, at least the file periphery is up;")
            print("    the power cluster being dead is then an intra-island PG")
            print("    problem, a very different (and more tractable) one.")
        return False
    print("    (VCN register block ACKs on MMIO -- the power island is OPEN)")

    # vcn_v2_0_disable_static_power_gating -- FULL function now (HEAD added
    # 2026-08-24; the old code ran only the POWER_STATUS tail). The kernel
    # drives the intra-VCN power FSM to all-sub-blocks-on BEFORE booting the
    # VCPU (vcn_v2_0.c, pg_flags==0 path): PGFSM_CONFIG = 1<<shift for all
    # ten sub-blocks (UVDM/UVDU/UVDF/UVDC/UVDB/UVDIL/UVDIR/UVDTD/UVDTE/UVDE,
    # 2-bit fields at shifts 0,2,...,0x12) = 0x55555, then polls
    # PGFSM_STATUS == 0. On a card whose firmware has NEVER initialized VCN
    # the FSM can come up holding sub-blocks gated -> the VCPU never reports
    # ("fw did not boot") even with the island powered and MMIO alive.
    v.wr(_uvd(R_PGFSM_CONFIG), 0x00055555)
    ok_fsm, fsm, _ = v.wait_reg(_uvd(R_PGFSM_STATUS), 0xFFFFF, 0, 1.0, "pgfsm")
    if ok_fsm:
        print("    PGFSM_CONFIG = 0x55555 -> PGFSM_STATUS = 0 (all sub-blocks ON)")
    else:
        print(f"    [!] PGFSM_STATUS = 0x{fsm:08x} (did not settle to 0 within 1s)")
        print("        continuing -- but a held sub-block gate here is a known")
        print("        VCPU-no-boot cause (kernel treats this as fatal)")
    # ... disable_static_power_gating TAIL (kernel-exact):
    v.rmw(_uvd(R_POWER_STATUS), and_mask=~0x103)
    print("    POWER_STATUS      &= ~0x103            (disable_static_power_gating tail)")
    # set UVD busy
    v.rmw(_uvd(R_STATUS), or_mask=UVD_STATUS_BUSY)
    print(f"    STATUS            |= 0x{UVD_STATUS_BUSY:x}                (set busy)")
    # vcn_v2_0_disable_clock_gating
    v.rmw(_uvd(R_CGC_CTRL), and_mask=~0x1, or_mask=(1 << 2) | (4 << 6))
    v.rmw(_uvd(R_CGC_GATE), and_mask=~M_CGC_GATE_ALL)
    print("    CGC_CTRL          = ~DYN_CLOCK_MODE|dly1|off4; CGC_GATE &= ~0xFFFFF")
    # enable VCPU clock
    v.rmw(_uvd(R_VCPU_CNTL), or_mask=M_VCPU_CNTL_CLK_EN)
    print("    VCPU_CNTL         |= CLK_EN")
    # disable master interrupt
    v.rmw(_uvd(R_MASTINT_EN), and_mask=~M_MASTINT_VCPU_EN)
    # LMI ctrl
    v.rmw(_uvd(R_LMI_CTRL), or_mask=M_LMI_CTRL_COHER)
    # MPC
    v.rmw(_uvd(R_MPC_CNTL), and_mask=~0x38, or_mask=(2 << 3))
    v.wr(_uvd(R_MPC_SET_MUXA0), (1 << 6) | (2 << 12) | (3 << 18) | (4 << 24))
    v.wr(_uvd(R_MPC_SET_MUXB0), (1 << 6) | (2 << 12) | (3 << 18) | (4 << 24))
    v.wr(_uvd(R_MPC_SET_MUX), (1 << 3) | (2 << 6))
    print("    LMI_CTRL/MPC/MUX  programmed")

    # vcn_v2_0_mc_resume, DIRECT branch
    v.wr(_uvd(R_LMI_VCPU_CACHE_64BIT_BAR_LOW),  mc(off_fw) & 0xFFFFFFFF)
    v.wr(_uvd(R_LMI_VCPU_CACHE_64BIT_BAR_HIGH), mc(off_fw) >> 32)
    v.wr(_uvd(R_VCPU_CACHE_SIZE0), fw_win)
    v.wr(_uvd(R_VCPU_CACHE_OFFSET0), AMDGPU_UVD_FIRMWARE_OFFSET >> 3)
    v.wr(_uvd(R_LMI_VCPU_CACHE1_64BIT_BAR_LOW),  mc(off_stack) & 0xFFFFFFFF)
    v.wr(_uvd(R_LMI_VCPU_CACHE1_64BIT_BAR_HIGH), mc(off_stack) >> 32)
    v.wr(_uvd(R_VCPU_CACHE_OFFSET1), 0)
    v.wr(_uvd(R_VCPU_CACHE_SIZE1), VCN_STACK_SIZE)
    v.wr(_uvd(R_LMI_VCPU_CACHE2_64BIT_BAR_LOW),  mc(off_ctx) & 0xFFFFFFFF)
    v.wr(_uvd(R_LMI_VCPU_CACHE2_64BIT_BAR_HIGH), mc(off_ctx) >> 32)
    v.wr(_uvd(R_VCPU_CACHE_OFFSET2), 0)
    v.wr(_uvd(R_VCPU_CACHE_SIZE2), VCN_CONTEXT_SIZE)
    v.wr(_uvd(R_LMI_VCPU_NC0_64BIT_BAR_LOW),  mc(off_shared) & 0xFFFFFFFF)
    v.wr(_uvd(R_LMI_VCPU_NC0_64BIT_BAR_HIGH), mc(off_shared) >> 32)
    v.wr(_uvd(R_VCPU_NONCACHE_OFFSET0), 0)
    v.wr(_uvd(R_VCPU_NONCACHE_SIZE0), 4096)
    v.wr(_uvd(R_GFX10_ADDR_CONFIG), gb_addr)
    print(f"    mc_resume DIRECT:  fw window  @MC 0x{mc(off_fw):012x} size {fw_win:#x}")
    print(f"                       stack      @MC 0x{mc(off_stack):012x} size 128KB")
    print(f"                       context    @MC 0x{mc(off_ctx):012x} size 512KB")
    print(f"                       fw_shared  @MC 0x{mc(off_shared):012x} (noncache window)")

    # boot: release VCPU reset
    v.rmw(_uvd(R_SOFT_RESET), and_mask=~M_VCPU_SOFT_RESET)
    print("    SOFT_RESET        &= ~VCPU_SOFT_RESET   (BOOT -- VCPU starts fetching)")
    v.rmw(_uvd(R_LMI_CTRL2), and_mask=~M_STALL_ARB_UMC)
    v.rmw(_uvd(R_SOFT_RESET), and_mask=~(M_LMI_SOFT_RESET | M_LMI_UMC_SOFT_RESET))
    v.wr(_uvd(R_LMI_SWAP_CNTL), 0)

    # poll for the fw to report (driver: status & 2, 10 x 1s, VCPU-reset retry)
    booted = False
    for i in range(10):
        ok, st, _ = v.wait_reg(_uvd(R_STATUS), 0x2, 0x2, 1.0, "VCPU report")
        if ok:
            booted = True
            break
        print(f"    [!] VCN decode not responding (STATUS=0x{st:08x}) -- "
              f"VCPU reset + retry {i + 1}/10 (driver behavior)")
        v.rmw(_uvd(R_SOFT_RESET), or_mask=M_VCPU_SOFT_RESET)
        time.sleep(0.01)
        v.rmw(_uvd(R_SOFT_RESET), and_mask=~M_VCPU_SOFT_RESET)
        time.sleep(0.01)
    if not booted:
        st = v.rd(_uvd(R_STATUS))
        print(f"[--] VCPU did not report (STATUS=0x{st:08x}). The fw did not boot.")
        print("    Likely causes: clock gate still active (check --verify slots),")
        print("    fw image mismatch, or the block needs a PSP-side handoff.")
        return False
    print("[+] VCPU REPORTED -- the microcontroller booted from OUR staged image")

    # post-boot
    v.rmw(_uvd(R_MASTINT_EN), or_mask=M_MASTINT_VCPU_EN)
    v.rmw(_uvd(R_STATUS), and_mask=~UVD_STATUS_BUSY)
    v.wr(_uvd(R_LMI_RBC_RB_VMID), 0)

    # ---- phase 4: ring setup (rest of vcn_v2_0_start) ----
    sh = base + off_shared
    v.wr(_uvd(R_RBC_RB_CNTL),
         (DEC_RB_BUFSZ << 0) | (1 << 8) | (1 << 16) | (1 << 24) | (1 << 28))
    v.vr_write_byte(sh + 57, 1)          # decode_queue_mode |= FW_QUEUE_RING_RESET
    v.wr(_uvd(R_LMI_RBC_RB_64BIT_BAR_LOW),  mc(off_dec_rb) & 0xFFFFFFFF)
    v.wr(_uvd(R_LMI_RBC_RB_64BIT_BAR_HIGH), mc(off_dec_rb) >> 32)
    v.wr(_uvd(R_RBC_RB_RPTR), 0)
    v.wr(_uvd(R_RBC_RB_WPTR), 0)
    v.vr_write_byte(sh + 57, 0)          # decode_queue_mode &= ~RESET
    v.vr_write_byte(sh + 58, 1)          # enc gp queue reset
    v.wr(_uvd(R_RB_RPTR), 0)
    v.wr(_uvd(R_RB_WPTR), 0)
    v.wr(_uvd(R_RB_BASE_LO), mc(off_enc0_rb) & 0xFFFFFFFF)
    v.wr(_uvd(R_RB_BASE_HI), mc(off_enc0_rb) >> 32)
    v.wr(_uvd(R_RB_SIZE), ENC_RB_SIZE_DW)
    v.vr_write_byte(sh + 58, 0)
    v.vr_write_byte(sh + 59, 1)          # enc ll queue reset
    v.wr(_uvd(R_RB_RPTR2), 0)
    v.wr(_uvd(R_RB_WPTR2), 0)
    v.wr(_uvd(R_RB_BASE_LO2), mc(off_enc1_rb) & 0xFFFFFFFF)
    v.wr(_uvd(R_RB_BASE_HI2), mc(off_enc1_rb) >> 32)
    v.wr(_uvd(R_RB_SIZE2), ENC_RB_SIZE_DW)
    v.vr_write_byte(sh + 59, 0)
    v.rd(_uvd(R_STATUS))                 # read-back fence (driver comment)
    print("[+] decode + encode rings programmed (RBC + fw_shared queue resets)")

    # nbio: route the dec-ring doorbell to VCN (vcn_v2_0_hw_init ->
    # nbio_v2_3_vcn_doorbell_range: OFFSET=0x310, SIZE=8)
    v.rmw(BIF_MMSCH0_DB_RANGE,
          and_mask=~(MMSCH_DB_RANGE_OFF_MASK | MMSCH_DB_RANGE_SIZE_MASK),
          or_mask=(DB_DEC_INDEX_DW << MMSCH_DB_RANGE_OFF_SHIFT) |
                  (8 << MMSCH_DB_RANGE_SIZE_SHIFT))
    print(f"[+] BIF_MMSCH0_DOORBELL_RANGE: OFFSET={DB_DEC_INDEX_DW:#x} SIZE=8 "
          f"(dec-ring doorbell routed to VCN)")

    # ---- phase 5: THE PROOF (vcn_v2_0_dec_ring_test_ring) ----
    print("\n[!] ring test (the driver's own proof, vcn_v2_0_dec_ring_test_ring):")
    print("    SCRATCH9 = 0xCAFEDEAD; submit a PACKET0 that tells the fw to write")
    print("    0xDEADBEEF into ITS view of SCRATCH9; poll the external view.")
    v.wr(_uvd(R_SCRATCH9), 0xCAFEDEAD)
    packets = struct.pack('<4I',
                          _pkt0(INT_GPCOM_CMD),            # PACKET0(internal cmd)
                          VCN_DEC_KMD_CMD | (VCN_DEC_CMD_PACKET_START << 1),
                          _pkt0(INT_SCRATCH9),             # PACKET0(internal scratch9)
                          0xDEADBEEF)
    v.vr_write(base + off_dec_rb, packets)   # 4 dwords at RB[0]
    v.wr(_uvd(R_RBC_RB_WPTR), 4)             # wptr += 4 dwords
    v.doorbell_ring(4)                       # WDOORBELL32(0x310, 4)
    print("    RB[0..3] <- [P0(cmd) KMD|START<<1, P0(scratch9) 0xDEADBEEF]")
    print("    RBC_RB_WPTR = 4 (reg) + doorbell 0x310 <- 4 (BAR2 0x{:x})".format(DB_DEC_BYTE))

    ok, val, el = v.wait_reg(_uvd(R_SCRATCH9), 0xFFFFFFFF, 0xDEADBEEF, 2.0, "scratch9")
    rptr = v.rd(_uvd(R_RBC_RB_RPTR))
    if ok:
        print(f"[+] *** SCRATCH9 = 0x{val:08x} after {el * 1000:.0f}ms ***")
        print(f"    RBC_RB_RPTR advanced 0 -> {rptr} (the fw consumed all 4 dwords)")
        print("    The VCN microcontroller EXECUTED our ring packet: it fetched")
        print("    the packet from OUR VRAM ring and performed the register write.")
        print("    VCN on this BC250 is ALIVE, running OUR staged firmware.")
        proved = True
    else:
        print(f"[--] SCRATCH9 = 0x{val:08x} (expected 0xDEADBEEF); RBC_RB_RPTR = {rptr}")
        print("    The VCPU booted (reported) but the ring did not complete.")
        print("    Check: doorbell routing, RB size field, fw_shared queue bits.")
        proved = False

    # ---- phase 6: park or leave running ----
    if park:
        print("\n[*] parking VCN (vcn_v2_0_stop, register-level; PGFSM/SMU untouched)...")
        ok1, st, _ = v.wait_reg(_uvd(R_STATUS), 0x7, UVD_STATUS_IDLE, 2.0, "idle")
        ok2, ls, _ = v.wait_reg(_uvd(R_LMI_STATUS), M_LMI_STATUS_CLEAN,
                                M_LMI_STATUS_CLEAN, 2.0, "lmi clean")
        v.rmw(_uvd(R_LMI_CTRL2), or_mask=M_STALL_ARB_UMC)
        v.wait_reg(_uvd(R_LMI_STATUS), M_LMI_STATUS_UMC, M_LMI_STATUS_UMC, 2.0, "umc")
        v.rmw(_uvd(R_VCPU_CNTL), and_mask=~M_VCPU_CNTL_CLK_EN)
        v.rmw(_uvd(R_SOFT_RESET), or_mask=M_LMI_UMC_SOFT_RESET)
        v.rmw(_uvd(R_SOFT_RESET), or_mask=M_LMI_SOFT_RESET)
        v.rmw(_uvd(R_SOFT_RESET), or_mask=M_VCPU_SOFT_RESET)
        v.wr(_uvd(R_STATUS), 0)
        v.rd(_uvd(R_STATUS))
        print(f"    idle={'ok' if ok1 else 'TIMEOUT'} lmi_clean={'ok' if ok2 else 'TIMEOUT'}; "
              f"VCPU clock off, resets asserted, STATUS cleared")
        print("    (clock-gating/PGFSM re-enable omitted deliberately -- SMU-adjacent)")
    else:
        print("\n[*] VCN left RUNNING (fw executing; staging VRAM at "
              f"0x{base:08x} is unmanaged -- do NOT start GPU workloads)")
    return proved


# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--no-fire", action="store_true",
                    help="unlock + prechecks + install the sequence, but do not trigger")
    ap.add_argument("--verify", action="store_true",
                    help="read-only: dump dom6/slot state, install nothing")
    ap.add_argument("--force", action="store_true",
                    help="proceed even if the dom6 state byte is 0x00 "
                         "(wrapper would auto-power dom6 first -- known wedge)")
    ap.add_argument("--fw-offset", type=lambda s: int(s, 0), default=None,
                    metavar="VRAM_OFF",
                    help="with --direct-load: pin the VRAM staging offset "
                         "(default: auto-walk zero spans at 8MB..24MB)")
    ap.add_argument("--direct-load", nargs="?", const="", default=None, metavar="PATH",
                    help="after the Discord fire, stage the navi10 VCN fw in VRAM "
                         "from USERSPACE and bring VCN up the driver's DIRECT way "
                         "(no PSP/TEE) -- then run the driver's own ring test as "
                         "proof. Needs amdgpu LOADED (raw MMIO/VRAM transport only)")
    ap.add_argument("--keep-vcn", action="store_true",
                    help="with --direct-load: leave VCN running after the proof "
                         "(default parks it again -- vcn_v2_0_stop register-level)")
    ap.add_argument("--no-enable-engage", action="store_true",
                    help="skip the post-fire step that engages the three dom6 "
                         "per-slot clock ENABLE (+0x08)=1 bits (the safe bounded "
                         "window write from README 2.4) and reads the dom6 power "
                         "sequencer. Default: engage + read out.")
    ap.add_argument("--smn-vcn-probe", action="store_true",
                    help="after the main stages, ONE SMN read THROUGH the SMU "
                         "(Q3 msg 0x2A, the mem64 window) at --smn-vcn-addr. "
                         "CORRECTED 2026-08-24: the fw MASKS the arg to 20 "
                         "bits (base 0x01100000) -- the window reaches the "
                         "NBIO frame ONLY and can never express a 0x024xxxxx "
                         "fabric address (a fabric arg silently aliases into "
                         "NBIO). WARNING: a dead NBIO offset stalls the SMN "
                         "bus -- SMU wedge, self-recovers ~10s or cold cycle")
    ap.add_argument("--smn-vcn-addr", type=lambda s: int(s, 0), default=0x01103010,
                    help="SMN address --smn-vcn-probe reads, as passed to the "
                         "mem64 window (default 0x01103010 -- the "
                         "NBIO-frame-hypothesis spelling of the 2026-08-24 "
                         "'fast 0' masked alias of the 0x02403010 arg; under "
                         "the low-frame hypothesis the same read hit "
                         "0x00003010 -- the frame question is what route P "
                         "step 0 discriminates). The sanity read uses the "
                         "PROVEN 0x5A870 window offset (core mask). The "
                         "0x1F8xx family is refused (dead responder under "
                         "either frame hypothesis -- the documented hard "
                         "wedge)")
    ap.add_argument("--vcn-power-regs", action="store_true",
                    help="standalone: FABRIC-SLICE PROBE -- dump VCN's "
                         "0x024xxxxx slice (0x02403000 + 0x00..0x3C) plus "
                         "THM/GC live-IP slice anchors through the PCI-config "
                         "SMN window (root 00:00.0 config 0xB8/0xBC, the "
                         "library transport; full 32-bit SMN addresses -- "
                         "the ONE CPU-side transport not measured to hang). "
                         "TRANSPORT FIX 2026-08-24 evening: the old route P "
                         "mmap'd BAR0 (VRAM!) -- its reads were VRAM "
                         "artifacts; the BAR5 PCIE_INDEX2 window is the "
                         "measured board-hang path. Step 0 also runs the "
                         "FRAME DISCRIMINATOR: core mask at BOTH full "
                         "spellings (0x0115A870/0x0005A870) + dom6 rail at "
                         "0x0116D184/0x0006D184 vs the live fw-window value "
                         "-- resolves the SMU-window frame question and "
                         "tells you whether --manual-powerup --config-writes "
                         "is available. Ladder: proven sanity reads -> frame "
                         "discriminator -> THM slice -> GC slice -> VCN "
                         "slice (VCN skipped if the frame reads dead). "
                         "Residual risk: first-ever 0x024-frame CPU reads -- "
                         "small cold-cycle risk, run nothing else after it")
    ap.add_argument("--vcn-power-regs-w", action="store_true",
                    help="with --vcn-power-regs: ALSO run route W (SMU data "
                         "window 0x0111F8xx). MEASURED 2026-08-20: stall on "
                         "the first read, HARD SMU wedge, NO self-recover, "
                         "cold power-cycle only. The route's question is "
                         "already answered -- do not run it.")
    ap.add_argument("--manual-powerup", action="store_true",
                    help="standalone: run the fw-exact dom6 rail power-up "
                         "protocol (FUN_00023b14 decode) with BOUNDED "
                         "host-side polls -- cannot wedge the SMU. Step [0] "
                         "releases ALL THREE ctrl gate bits (0/1/2 <-> slots "
                         "0x16/0x17/0x18; the fw's dom7 caller writes 0 to "
                         "the whole reg). Follow it with --vcn-power-regs: "
                         "the fabric-slice probe is the arbiter (slice dead "
                         "-> live / values moving = the rail landed)")
    ap.add_argument("--thunk-writes", action="store_true",
                    help="with --manual-powerup: route the ctrl/cmd/rail "
                         "stores through the INLINE store thunk (the fw's "
                         "own window-store sequence executed in the msg-0x61 "
                         "handler thunk at the preflight depth; a mailbox-OK "
                         "answer PROVES each store executed in firmware) "
                         "instead of bare window stores. The 0x233e8 and "
                         "0x235c8 call-vehicles BOTH WEDGED the SMU "
                         "(2026-08-21) -- needs --force-thunk-writes until "
                         "--inline-store-probe proves the inline vehicle "
                         "(mailbox ANSWERS)")
    ap.add_argument("--config-writes", action="store_true",
                    help="with --manual-powerup: route the ctrl/cmd/rail "
                         "stores AND read-backs through the PCI-config SMN "
                         "window at the runtime-discriminated full fabric "
                         "spelling (all four live sequencer values must "
                         "match first). MEASURED 2026-08-25: the sequencer "
                         "IGNORES host fabric writes (ctrl 0x02->0x00 store "
                         "read back 0x02 instantly; the transport itself is "
                         "source-verified and proven by every mailbox "
                         "send) -- the mode now serves as the block's "
                         "config-write capability probe (slot-0x16 enable "
                         "toggle) and reports. The fw-window debug-write "
                         "path (plain --manual-powerup, FIXED step [0]) is "
                         "the live store vehicle")
    ap.add_argument("--force-thunk-writes", action="store_true",
                    help="explicitly accept the MEASURED wedge risk of "
                         "--thunk-writes (2026-08-21: the in-fw cmd store "
                         "killed the SMU; cold power-cycle recovery)")
    ap.add_argument("--thunk-probe", action="store_true",
                    help="standalone: ONE benign in-fw store via the "
                         "call-thunk vehicle (FUN_000235c8 + fe4/fa8 tail) "
                         "on a PROVEN no-op target -- slot 0x17's clock reg, "
                         "re-writing its current value. MEASURED 2026-08-21 "
                         "night-4: WEDGED the SMU (fn/args/encoding/tail "
                         "all verified correct) -- surviving suspects: "
                         "depth +3, SMN-bridge access from handler context, "
                         "or 2a018's gate fallback. Use --inline-store-probe "
                         "next (bypasses all three), or --probe-fn for the "
                         "raw depth/bridge ladder")
    ap.add_argument("--inline-store-probe", action="store_true",
                    help="standalone: ONE idempotent in-fw store with the "
                         "INLINE store thunk -- the fw's own window-store "
                         "sequence (decoded from FUN_000235c8's fast path) "
                         "executed INSIDE the msg-0x61 handler thunk, zero "
                         "fw fn calls: call depth stays at the ABI-preflight "
                         "envelope (dispatcher -> thunk -> fe4/fa8), the "
                         "only depth ever proven on hardware. ANSWERS -> "
                         "in-fw stores proven (--thunk-writes un-gates); "
                         "WEDGES -> SMN-bridge access from handler context "
                         "is the killer (stores stay host-side)")
    ap.add_argument("--dom6-dump", action="store_true",
                    help="standalone, READ-ONLY: dump the whole dom6 block "
                         "0x06D000-0x06D1FF through the fw window (the "
                         "proven-safe path). Annotates the known sequencer/"
                         "slot registers and highlights NONZERO UNKNOWN "
                         "dwords -- the hunting ground for an ISO/reset "
                         "latch the sequencer decode missed (the 2026-08-25 "
                         "contradiction: sequencer says dom6 UP, VCN MMIO "
                         "reads all-ones CLOSED)")
    ap.add_argument("--msg-table", action="store_true",
                    help="standalone, READ-ONLY: dump the fw's Q3 message-"
                         "handler table (SRAM 0x746C, msg 0x01..0xC0; entry "
                         "for msg M at 0x746C+(M-1)*8 -- the same math the "
                         "fire's repoint uses). Lists every msg id that has "
                         "a handler and cross-references known fw functions. "
                         "The kernel PPSMC list for this PMFW has NO VCN "
                         "message (smu_v11_8_ppsmc.h) -- but the internal "
                         "space is only partially mapped (0x2A-0x2D etc. "
                         "aren't PPSMC either). Resolve unknown pointers in "
                         "the fw image: a handler reaching FUN_00023b14 "
                         "(domain power-up) is the fw's OWN power-up vehicle "
                         "-- the renoir PPSMC_MSG_PowerUpVcn analog")
    ap.add_argument("--probe-fn", type=lambda s: int(s, 0), default=None,
                    metavar="ADDR",
                    help="with --thunk-probe: call an arbitrary fw fn "
                         "instead of FUN_000235c8 (--probe-reg/--probe-value "
                         "become raw a2/a3 arguments). Depth/bridge ladder: "
                         "--probe-fn 0x2a018 --probe-reg 4 tests the SMN "
                         "window read of 0x032000e8 (the bridge-gate leaf) "
                         "at the SAFE +2 depth; ALIVE = bridge access fine "
                         "at preflight depth, WEDGED = the bridge access "
                         "itself is the killer")
    ap.add_argument("--probe-reg", type=lambda s: int(s, 0), default=None,
                    metavar="SMN",
                    help="with --thunk-probe: override the target register "
                         "(default: slot 0x17's clock reg from the slot "
                         "table)")
    ap.add_argument("--probe-value", type=lambda s: int(s, 0), default=None,
                    help="with --thunk-probe: override the stored value "
                         "(default: the register's CURRENT value -- the "
                         "probe is idempotent by construction)")
    ap.add_argument("--bdf", default="0000:00:00.0")
    args = ap.parse_args()

    if args.direct_load is not None and args.verify:
        sys.exit("--direct-load and --verify are mutually exclusive (--verify is read-only)")
    if args.direct_load is not None and args.no_fire:
        sys.exit("--direct-load requires the fire (VCN must be clocked before it "
                 "can boot); drop --no-fire")
    if args.keep_vcn and args.direct_load is None:
        sys.exit("--keep-vcn only makes sense together with --direct-load")
    if args.smn_vcn_probe and args.verify:
        sys.exit("--smn-vcn-probe can wedge the SMU and --verify is strictly "
                 "witness reads -- drop one of the two")
    if args.vcn_power_regs_w and not args.vcn_power_regs:
        sys.exit("--vcn-power-regs-w modifies --vcn-power-regs; pass both")
    if args.vcn_power_regs_w and args.verify:
        sys.exit("--vcn-power-regs-w is a measured SMU wedge and --verify is "
                 "strictly witness reads -- drop one of the two")
    if args.vcn_power_regs and (args.direct_load is not None or
                                args.smn_vcn_probe):
        sys.exit("--vcn-power-regs is a standalone diagnostic; do not combine "
                 "with --direct-load / --smn-vcn-probe (run it as "
                 "its own command)")
    if args.thunk_writes and not args.manual_powerup:
        sys.exit("--thunk-writes only makes sense together with --manual-powerup")
    if args.config_writes and not args.manual_powerup:
        sys.exit("--config-writes only makes sense together with --manual-powerup")
    if args.config_writes and args.thunk_writes:
        sys.exit("--config-writes and --thunk-writes are two different store "
                 "vehicles; pick one (config-window stores are the safer new "
                 "path -- they run at host level, no SMU code execution)")
    if args.manual_powerup and args.verify:
        sys.exit("--manual-powerup WRITES the dom6 sequencer regs; --verify is "
                 "strictly witness reads -- drop one of the two")
    if args.manual_powerup and (args.direct_load is not None or
                                args.smn_vcn_probe or args.vcn_power_regs):
        sys.exit("--manual-powerup is a standalone rail attempt; run it as its "
                 "own command (follow it with --vcn-power-regs)")
    if args.thunk_writes and not args.force_thunk_writes:
        sys.exit("--thunk-writes MEASURED to wedge the SMU (2026-08-21, both "
                 "vehicles): the corrected FUN_000235c8 call-vehicle ALSO "
                 "wedged on a benign target. Stores now ride the INLINE store "
                 "thunk (the fw's own store sequence in-thunk, preflight "
                 "depth, no fw fn call) -- run --inline-store-probe first; if "
                 "the mailbox ANSWERS, pass --force-thunk-writes for the rail "
                 "protocol.")
    if args.thunk_probe and (args.verify or args.direct_load is not None or
                             args.smn_vcn_probe or args.vcn_power_regs or
                             args.manual_powerup or args.thunk_writes or
                             args.inline_store_probe):
        sys.exit("--thunk-probe is a standalone vehicle probe; run it as its "
                 "own command (it fires exactly one in-fw store)")
    if args.inline_store_probe and (args.verify or
                                    args.direct_load is not None or
                                    args.smn_vcn_probe or args.vcn_power_regs or
                                    args.manual_powerup or args.thunk_writes):
        sys.exit("--inline-store-probe is a standalone vehicle probe; run it "
                 "as its own command (it fires exactly one in-fw store)")
    if args.dom6_dump and (args.verify or args.direct_load is not None or
                           args.smn_vcn_probe or args.vcn_power_regs or
                           args.manual_powerup or args.thunk_writes or
                           args.thunk_probe or args.inline_store_probe or
                           args.msg_table):
        sys.exit("--dom6-dump is a standalone read-only diagnostic; run it as "
                 "its own command")
    if args.msg_table and (args.verify or args.direct_load is not None or
                           args.smn_vcn_probe or args.vcn_power_regs or
                           args.manual_powerup or args.thunk_writes or
                           args.thunk_probe or args.inline_store_probe or
                           args.dom6_dump):
        sys.exit("--msg-table is a standalone read-only diagnostic; run it as "
                 "its own command")
    if (args.probe_reg is not None or args.probe_value is not None) \
            and not (args.thunk_probe or args.inline_store_probe):
        sys.exit("--probe-reg/--probe-value only make sense with "
                 "--thunk-probe (target/value; raw a2/a3 with --probe-fn) "
                 "or --inline-store-probe (target/value)")
    if args.probe_fn is not None and not args.thunk_probe:
        sys.exit("--probe-fn only makes sense with --thunk-probe")

    if os.geteuid() != 0:
        sys.exit("needs root")

    smu = Bc250Smu(bdf=args.bdf)
    installed = False
    try:
        if not smu.alive():
            sys.exit("[!] SMU not alive -- cold power cycle")
        print("[*] SMU alive")

        if not smu.secure_access_enabled():
            print("[*] secure access closed -- running the library unlock ...")
            sys.modules["unlock"].smu = smu
            unlock(smu)
        if not smu.alive():
            sys.exit("[!] SMU died after unlock -- cold power cycle")
        if not smu.secure_access_enabled():
            sys.exit("[!] unlock did not open secure access -- cold cycle and retry")
        print("[*] secure access open (unlocked SMU debug path active)")

        # ---- state snapshot + prechecks (reads via the unlocked debug path) ----
        state_word = rd_sram(smu, DOM6_STATE_WORD)
        state = state_word & 0xFF
        print(f"[*] dom6 state word @0x{DOM6_STATE_WORD:x} = 0x{state_word:08x} "
              f"(state byte = 0x{state:02x})")
        before = dump_slots(smu, "BEFORE")

        # ---- standalone: VCN power/harvest cluster reads (two routes) ----
        if args.vcn_power_regs:
            dom6_block_report(smu)     # the SMU-side power oracle (context)
            vcn_power_regs_report(smu, run_w=args.vcn_power_regs_w)
            return

        # ---- standalone: manual dom6 rail power-up (bounded, fw-exact) ----
        # The fire prechecks below guard the DISCORD SEQUENCE's auto-power
        # branch; the manual protocol is host-bounded and needs no such guard.
        if args.manual_powerup:
            wedged = manual_powerup_dom6(smu, via_thunk=args.thunk_writes,
                                         via_config=args.config_writes)
            if not wedged:
                print("\n[*] arbiters, in order of information:")
                print("    1. the ctrl read-back inside this run (a LANDED")
                print("       0x02->0x00 is itself the first real state change;")
                print("       confirm cross-process persistence with")
                print("       --vcn-power-regs)")
                print("    2. THE arbiter -- the VCN MMIO read:")
                print("       sudo python3 enable_vcn.py --direct-load")
                print("       (the fire is a designed no-op on a converged")
                print("        table; its first POWER_STATUS read answers")
                print("        everything: real values = island live -> fw")
                print("        boot + ring test; all-ones = isolation, clean")
                print("        abort (measured 2026-08-20 behavior); hang =")
                print("        cold cycle (July, pre-clock-work only). The")
                print("        0x024 slice probe is dead on this box -- MMIO")
                print("        is the only VCN window left)")
            return

        # ---- standalone: dom6 block dump (read-only ISO/reset hunt) ----
        if args.dom6_dump:
            dom6_block_dump(smu)
            return

        # ---- standalone: fw message-handler table dump (read-only) ----
        if args.msg_table:
            msg_table_dump(smu)
            return

        # ---- standalone: benign thunk-vehicle probe (wedge discriminator) ----
        if args.thunk_probe:
            thunk_probe(smu, reg=args.probe_reg, value=args.probe_value,
                        fn=args.probe_fn)
            return

        # ---- standalone: inline-store probe (the night-4 discriminator) ----
        if args.inline_store_probe:
            inline_store_probe(smu, reg=args.probe_reg,
                               value=args.probe_value)
            return

        not_ready = [s for s in VCN_SLOTS
                     if before[s][4][0x24] is None or not (before[s][4][0x24] & 0x10000)]
        if not_ready:
            print(f"[!] slot(s) {[hex(s) for s in not_ready]} status bit16 not SET: "
                  f"the fw poll inside 0x2362c may never resolve -> wedge risk.")
        if state == 0x00 and not args.force:
            sys.exit("[!] dom6 state byte is 0x00 -- FUN_00023744 would take the "
                     "auto-power branch (FUN_00023b14(6,1), known SMU wedge on a\n"
                     "    gated domain). Cold-cycle to restore the factory 0x01, or "
                     "re-run with --force to allow it.")

        if args.verify:
            print("\n[--verify: read-only. exiting]")
            return

        # ---- install the exact sequence at 0x3ff00 (debug write, verified) ----
        code = build_sequence()
        print(f"\n[*] installing the sequence at SMU SRAM 0x{THUNK_ADDR:x} "
              f"({len(code)} bytes, via smu_write32 debug path):")
        print("      " + " ".join(f"{b:02x}" for b in code))
        print("      entry   a1, 0x20")
        for slot in VCN_SLOTS:
            print(f"      movi.n  a10, 0x{slot:02x}")
            print(f"      call8   0x{FUN_SLOT_CLK:05x}")
        print("      retw.n")
        for i in range(0, len(code), 4):
            smu.smu_write32(THUNK_ADDR + i,
                            int.from_bytes(code[i:i + 4], "little"))
        installed = True
        rb = smu.smu_read(THUNK_ADDR, len(code) // 4)
        if rb != code:
            sys.exit(f"[!] thunk read-back mismatch:\n  wrote {code.hex()}\n  read  {rb.hex()}")
        print("[+] sequence installed and read-back verified")

        stale = rd_sram(smu, SLOT_FUNCPTR)
        if stale:
            print(f"[*] note: msg-0x61 handler slot was non-zero (0x{stale:x}) "
                  f"-- leftover from an earlier run; overwriting.")

        # ---- repoint the reserved msg-0x61 handler at the sequence ----
        smu.smu_write32(SLOT_FUNCPTR, THUNK_ADDR)
        got = rd_sram(smu, SLOT_FUNCPTR)
        if got != THUNK_ADDR:
            sys.exit(f"[!] handler slot repoint failed (read back 0x{got:x})")
        print(f"[*] Q3 msg-0x61 handler slot @0x{SLOT_FUNCPTR:x} -> 0x{THUNK_ADDR:x} "
              f"(read-back ok)")

        if args.no_fire:
            print("\n[--no-fire: install + repoint verified, NOTHING triggered. "
                  "Disarming now (handler slot restored, thunk wiped).]")
            return

        print("\n[!] LAST WARNING: this path is documented to hard-wedge the SMU "
              "on a headless BC250 (README §2.7).")
        print("    Fire in 3s ...")
        time.sleep(3)

        # ---- trigger: the library's Q3 mailbox send as the doorbell ----
        fire_sequence(smu, SLOT)   # the send's response poll IS the dispatch wait

        if debug_alive(smu):
            print("[+] SMU still alive via the debug path -- sequence returned.")
            after = dump_slots(smu, "AFTER")
            diff_slots(before, after)

            # ---- engage the per-slot clock ENABLEs (the fw dance's missing tail) ----
            # The fire programs the slot clocks but skips the enable dance when
            # the table is converged (steady state enable=0). README 2.4: the
            # bounded window write is safe, lands, and gets a live reaction --
            # the one SMU-side lever that can follow the fire.
            if not args.no_enable_engage:
                engage_slot_enables(smu, after)
                after = dump_slots(smu, "ENGAGED")

            # ---- SMU-side power oracle (authoritative, no VCN register reads) ----
            dom6_block_report(smu)

            # ---- optional stage 6: USERSPACE direct load + bring-up ----
            if args.direct_load is not None:
                if any(after[s][1] != after[s][2] for s in VCN_SLOTS):
                    print("[!] slot table not fully converged after the fire -- "
                          "clock state is uncertain; SKIP the direct load.")
                else:
                    attempt_direct_load(args.direct_load, args.fw_offset,
                                        park=not args.keep_vcn)

            # ---- optional stage 7: SMN-route VCN probe (opt-in; may wedge) ----
            if args.smn_vcn_probe:
                smn_vcn_probe(smu, args.smn_vcn_addr)
        else:
            print("[!] debug path is NOT answering -- SMU wedged inside the "
                  "sequence (expected failure mode). COLD POWER-CYCLE.")
            print("    The three FUN_00023744 calls may still have partially run.")
            if args.direct_load is not None:
                print("[!] skipping the --direct-load attempt: VCN clock state "
                      "is unknown after the SMU wedge.")
    finally:
        # hygiene: restore the reserved handler slot + wipe the thunk (best effort)
        try:
            if rd_sram(smu, SLOT_FUNCPTR) != 0:
                smu.smu_write32(SLOT_FUNCPTR, 0)
                print(f"[*] restored msg-0x61 handler slot -> 0 "
                      f"(read-back 0x{rd_sram(smu, SLOT_FUNCPTR):x})")
            if installed:
                for i in range(0, len(build_sequence()), 4):
                    smu.smu_write32(THUNK_ADDR + i, 0)
                print("[*] thunk scratch wiped")
        except Exception as e:
            print(f"[!] could not restore/wipe ({e.__class__.__name__}) -- "
                  f"SMU unreachable; cold power-cycle before anything else.")
        smu.close()


if __name__ == "__main__":
    main()
