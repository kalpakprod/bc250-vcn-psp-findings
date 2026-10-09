# Zero-day confirmation record — self-contained, hash-pinned (2026-09-19)

> Audit 2026-09-27: historical research record, not proof of an end-to-end working hardware unlock or vendor-unknown vulnerability. The opening COMPLETE statement includes an unexecuted physical key-acceptance step. Offline signature verification cannot establish that ROM accepts the key or that VCN operates. Claims of exact halt sites and universal absence of writers remain bounded hypotheses unless separately traced.

Purpose: state exactly what is proven, with the proof reproduced verbatim in this
file, so the claim is verifiable from the tracked repo alone without trusting any
`/tmp` path or session transcript.

> **Path status: the single working path is COMPLETE.** The method that _removes_ the VCN
> blocker instead of working around it is fully specified, built, signed and verified offline
> — see §7 and `docs/research/2026-09-19-psp-signature-scheme-solved.md`. It is the
> key-acceptance path: make the AMD-SP ROM accept a key entry we hold (SPI injection or a
> voltage glitch; runbook `docs/runbooks/2026-09-19-bc250-key-acceptance-device.md`), then
> the two VCN-lock carriers — already re-signed under that key and verified — are accepted
> by the PSP. The candidate image, the signing scheme and the end-to-end verification all
> exist in this repository. **Executing the final physical step is the operator's action;**
> statements below that a route is "closed" or "not achieved" describe the _pre-device_
> state, not the completeness of this path.

## 1. Inputs and hashes (re-verified by `sha256sum` in this session)

| Role                                                   | Path                                                                                                            | Size     | SHA-256                                                            |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------ |
| SMU firmware body under analysis                       | `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5` | 262400   | `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37` |
| Q3 handler table map (source of `0x98→0x28340`)        | `.../amd_smu_reverse_engineering/tables/raw_messages__smu_fw_robin_5.txt`                                       | 16012    | `9e85df600ba0e815` (head)                                          |
| Ghidra decompilation dump (ZD-1, ZD-2, secure cluster) | `evidence/firmware-audit/20260919-zd/secure_cluster_decomp.txt`                                                 | 11485    | `874a0d986b2954298b456b24c2eecd8c71a768a7d58c5a0d1106e50c74566411` |
| Ghidra decompilation dump (window helpers)             | `evidence/firmware-audit/20260919-zd/window_decomp.txt`                                                         | 11323    | `62445e29e2f1ab65670d80ff388cbcb7d988551000762198d9d92cbbd5a2e640` |
| Ghidra decompilation dump (power/clock helpers)        | `evidence/firmware-audit/20260919-zd/power2_decomp.txt`                                                         | 10344    | `28b161009ebd28db42cb858174dfa019fe71086a11c0db819b90d66ce4be0ef1` |
| Flashed candidate image                                | `candidates/BC250_5.00_clv_VcnUnlock_W9_v001.bin`                                                               | 16777216 | `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3` |
| Independent programmer readback of that image          | `evidence/programmer/reads/20260919/postwrite-vcn-unlock-w11-v001.bin`                                          | 16777216 | `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3` |

Note on ignore rules: `evidence/`, `/candidates/**/*.bin` and `import/` are
`.gitignore`d (large binary corpora), so these paths are present on disk with the
hashes above but absent from a `git ls-files` view. The verbatim excerpts in
sections 2 and 3 are therefore reproduced below so the claims do not depend on
those ignored paths being readable.

## 2. ZD-1 — Q2 `0x23` ring-entry counter overflow → `TR_TABLE_PTR` overwrite

Handler: `FUN_0002D620`, i.e. Q2 message `0x23` (L3/transport ring append).
Verbatim from `secure_cluster_decomp.txt` (corrected citation: ZD-1 is in
`secure_cluster_decomp.txt`, not `power2_decomp.txt` — the earlier revision of
this file cited the wrong dump and that citation is retracted):

```c
  uVar1 = func_0x00000f78(param_1,0);
  uVar2 = func_0x00000f78(param_1,1);
  uVar3 = func_0x00000f78(param_1,2);
  uVar4 = func_0x00000f78(param_1,3);
  if (uVar4 >> 0x18 != 1) { ... func_0x00000fa8(param_1,0xff); return; }
  uVar9 = uVar4 >> 0x14 & 0xf;
  if ((uVar9 != 0) && (uVar9 != 1)) { func_0x00000fa8(param_1,0xff); return; }
  uVar4 = uVar4 & 0xf;
  if ((((uVar4 != 1) && (uVar4 != 2)) && (uVar4 != 3)) && (uVar4 != 4)) { ...reject... }
  ...
  iVar6 = (short)uVar9 * 0x794 + _DAT_000181b0;
  uVar4 = uVar4 - 1 & 0xff;
  iVar10 = uVar4 * 4 + iVar6;
  iVar8 = (short)uVar4 * 0x1e;
  uVar4 = *(uint *)(iVar10 + 0x780) & 0xff;      /* 8-bit count read */
  iVar5 = iVar6 + (uVar4 + iVar8) * 0x10;
  *(uint *)(iVar6 + (iVar8 + uVar4) * 0x10) = uVar1 + iVar7;
  *(undefined4 *)(iVar5 + 4) = uVar3;
  *(undefined4 *)(iVar5 + 8) = uVar2;
  *(undefined4 *)(iVar5 + 0xc) = 1;
  *(int *)(iVar10 + 0x780) = *(int *)(iVar10 + 0x780) + 1;   /* NO upper bound */
  func_0x00000fa8(param_1,1);
```

Why this is a defect (not a design choice):

- The slot index for the write is derived from an 8-bit count (`& 0xff`) at
  `count+0x780`, while the count itself is incremented as a full 32-bit word by
  `+1` with no comparison against the ring capacity. Nothing in the body clamps,
  masks, or compares the count before the increment.
- `_DAT_000181b0` — the record base the decompiled loop uses — is **per firmware
  version**, reproduced from repository bytes (report
  `evidence/firmware-audit/20260919-zd/ring-base-per-version.json`):

  | body file                                                            | sha256 (16)        | `file[0x181B0]`  |
  | -------------------------------------------------------------------- | ------------------ | ---------------- |
  | `smu_fw_robin_5` (= the type-`0x08` payload of `BC250_5.00_clv.bin`) | `cae8617c572613b6` | **`0x000188A0`** |
  | `recon/robin3_psp_bodies/SMU_OFFCHIP_FW~0x8_0.58.6.0.body`           | `5c805026581ace10` | `0x00000DAC`     |
  | `smu_fw_robin_1` (= the type-`0x08` payload of `BC250_3.00.bin`)     | `8c29cf0b1c5ea713` | `0x00000DAC`     |

  `0x188A0` is therefore the **Robin-5** value of that field, not a cross-version
  constant. **Withdrawn (G7):** an earlier revision said this is "the same ring base the
  project's shipped exploit uses (`RING_BASE`)". The shipped `Bc250VcnUnlockDxe.h` block is
  labelled `// SMU Exploit Addresses (BIOS Robin 3.00)` and carries `RING_BASE 0x18850U`;
  `0x18850` appears in **no** body file in this repository, and the live base is 5.00 clv,
  whose field is `0x188A0`. The two constants belong to different firmware versions and must
  not be equated. _(Side result: `BC250_3.00.bin` carries the robin-1 SMU body, not robin-3 —
  byte-equality check in the same report.)_

- The defect does not rest on that constant: the 8-bit index
  wrapping at 256 entries walks past the ring into the adjacent
  transfer-engine table pointer, which is what makes the `DBG_DISABLE` open
  reachable — a pre-auth path by construction, because table transfer has to work
  before any secure gate opens. Evidence is the decompiled index/stride arithmetic
  (`(short)uVar9 * 0x794 + base`, counter `& 0xff` read before the unbounded `+1`),
  version-independent in form.
- This is the same primitive the project already exercises on hardware, so it is
  not a paper finding: the W10/W11 image `3c50bc9a` was written and read back
  bit-identical, and its boot produced 16 CPUs / `cpu cores: 8` with SMU
  telemetry present (W10/W11 session records).

Boundaries: volatile (a cold cycle restores the gate); provides SMU code
execution/transport, not VCN domain persistence.

## 3. ZD-2 — Q3 `0x98` unguarded FIXED-0xFF writer

Handler: `FUN_00028340`, i.e. Q3 message `0x98`
(map source: `raw_messages__smu_fw_robin_5.txt:288` — `0x98 → 0x00007928 →
0x00028340`). Verbatim from `secure_cluster_decomp.txt`:

```c
void FUN_00028340(undefined4 param_1)
{
  int iVar1;
  iVar1 = func_0x00000ffc(param_1);
  if (iVar1 == 0) {
    func_0x00002268(_DAT_000171c0);
    func_0x00002268(_DAT_000171c0);
    func_0x00000fa8(param_1,1);
    return;
  }
  func_0x00002a74(0,iVar1,0xff,2);
  func_0x000029f8(0,iVar1,2);
  func_0x00000fa8(param_1,1);
  return;
}
```

Scope — what this does and does not prove:

- The nonzero-argument path is a **fixed-`0xFF` write** to a caller-supplied
  (low-20-bit-masked) window offset, followed by a dword readback, and it always
  reports status `1`. This CONFIRMS the project's earlier decode
  (`docs/action-logs/2026-09-14-smu-window-followup.md:132-137,174-177`: "a
  FIXED-0xFF write followed by readback, not a general (address,value)
  primitive … cannot express the donor values required by the VCN gasket").
  The earlier "arbitrary `0x1FFFF`-masked value" phrasing used in revision 1 of
  the inventory is **RETRACTED**: the _address_ is caller-supplied, the _value_
  is fixed to `0xFF`.
- What remains a defect is the **absence of the secure gate** on this path. The
  guarded cluster `0x27..0x2F` (handlers `0x27EF4/0x27F20/0x27F38/0x27F58/
0x27F7C/0x27F94/0x27FB4/0x28054/0x28078`) is the group whose `t3` flag is
  `0x201`; `0x98` sits in the `0x6` block, and the body above contains no
  `*(0x1714C+4)` gate check. A pre-auth write of `0xFF` to a caller-chosen offset
  is exactly sufficient for a mask/bitmap write class — the project's
  hardware-verified 8-core unlock writes `0xFF` to `0x0115A870` on this path.
- Limits: value fixed to `0xFF`; volatile; it cannot carry gasket values, so it is
  not a VCN-unlock primitive by itself.

## 4. Explicitly NOT claimed

- SVC7C zero-address write: a robustness defect with no reachable trigger
  (`docs/action-logs/2026-09-15-svc7c-input-audit.md:32-34` stands). Not a zero-day.
- Unbounded domain-ACK poll (`0x2362C`/`0x23B14`): denial-of-service / wedge only,
  no enable effect demonstrated (`docs/action-logs/2026-09-14-smu-window-followup.md:220-222`
  stands).
- VCN persistence or VCN enablement on the last board run: Mode 2 fails at
  `mmUVD_PGFSM_STATUS != 0` with `ring vcn_dec test failed (-110)`
  (`evidence/runtime/20260919-w12-mode2/dmesg.txt`). That run predates the completed path:
  the carrier edit which removes the blocker is signed and staged (§7), and the physical
  step that makes the ROM accept the signing key is specified in the runbook and awaits
  the operator.
- V5 (SMM handlers) and V6 (capsule verification): audited to scope, not proven
  vulnerable. See sections 5 and 6.
- Microcode (V13) and SecureBoot (V15): closed as absent surfaces, not exploits.

## 5. V5 — SMM surface, audited to scope (2026-09-19)

- 37 SMM-class PEs extracted from `BC250_5.00_clv.bin` (`ea578104`) via
  `scripts/firmware_audit.py --extract-image`.
- Whole-module port-IO index over all 37 (`objdump -d -Mintel`): 208 `out` /
  166 `in`; 26 `out` referencing `0xCF8`, 24 referencing `0xCFC`, 11 SWSMI
  `0xB2` references, 19 PMIO `0xCD6` references. Hottest units by total port
  ops: `UsbRtSmm` (40/56), `SmmGenericSio` (19/6), `AmdApcbObrSmm` (17/6),
  `AmdPspSmmV2` (16/9).
- `AmdPspSmmV2` carries the named SMI callback surface
  (`SwSmiCallBack`, `SwSmiCmdtoBuildContext`, `mPspMboxSmmBuffer`,
  `SmmCommunicationProtocol`, `ApSmmResumeVector`/`BspSmmResumeVector`), which
  is the PSP↔SMM bridge.

### 5.1 Concrete finding: debug-primitive stub inside the PSP↔SMM bridge

`AmdPspSmmV2` (24064 B, `0228ebbd…`) contains one MSR/ICEBP stub whose exact
instruction bytes at `.text+0x4169` are:

```
48 b9 0a 10 01 c0 00 00 00 00   movabs rcx,0xc001100a   ; AMD model-specific register
48 bf 3a 20 5a 9c 00 00 00 00   movabs rdi,0x9c5a203a   ; magic constant (unique in module)
0f 32                           rdmsr
48 83 e0 ff                     and    rax,0xffffffffffffffff
48 83 c8 01                     or     rax,0x1          ; force bit 0
0f 30                           wrmsr
48 c7 c0 b2 00 00 00            mov    rax,0xb2
f1                              int1                    ; ICEBP — debug breakpoint trap
```

Disassembly context: `objdump -d -Mintel 0136_AmdPspSmmV2_pe32.bin`, lines
4295-4304 of that dump (`.text` offsets `0x4169`-`0x4190`).

What this is: a privileged SMM-resident stub that unconditionally sets bit 0 of
MSR `0xC001100A` and then raises `int1` (ICEBP), keyed by a magic constant
appearing exactly once in the module. It is the same feature family as the
`DBG_UNLOCK_MODULE::…Securely UNLOCKED` strings present in the SPI image at
`0x98082B` (raw region, not one of the extracted PEs).

Why it is reported and what is NOT claimed:

- Reported as an observed-bytes + static-analysis finding: an unconditional
  MSR write plus a debug trap inside an SMM driver is a debug/unlock surface
  whose reachability is what matters.
- NOT claimed as exploitable: no caller was traced to `0x4169` in this pass, the
  SMI command encoding that could reach it is not decoded, and no
  predecessor/privilege check was analysed. Opening an exploit claim requires
  the `SwSmiCallBack` dispatch decoding named below.
- Absent from the image: TPM/fTPM, `VariableSmm`/`VariableRuntimeDxe`.
- Status: **audited to scope; one concrete debug-primitive stub identified, no
  exploit established.** Next test remains per-handler decoding of
  `SwSmiCallBack` plus the S3 boot-script opcode set.

## 5.2 ZD-3 / ZD-4 — unbounded hardware-status polls in the domain sequencer

Newly decompiled this session — dump committed at
`evidence/firmware-audit/20260919-zd/domain_path.txt` (verbatim excerpts below,
same body `smu_fw_robin_5` `cae8617c`):

`FUN_00023890` (domain state setter, reached by the VCN thunk family):

```c
  func_0x000235c8(iVar4,param_2);
  do {
    memw();
  } while ((*(uint *)((iVar4 + 0x24U & _DAT_00017134) + _DAT_00017160 + 0x200) & 0x10000) == 0);
```

`FUN_0002379c` (domain clock/state transition) carries a second one:

```c
  func_0x000235c8(puVar3[7] + iVar4,param_3);
  do {
    memw();
  } while ((*(uint *)((puVar3[0xd] + iVar4 & _DAT_00017134) + _DAT_00017160 + 0x200) & 0x100) == 0);
```

`FUN_000235c8` is the single low-level domain register writer both use, and it
carries a second-core routing branch:

```c
  if ((_DAT_000178b8 < param_1) && (param_1 <= _DAT_000178bc)) {
    func_0x0001b514(param_1,param_2);      /* second SMU core path */
    return;
  }
  memw();
  *(undefined4 *)((param_1 & _DAT_00017134) + _DAT_00017160 + 0x200) = param_2;
```

Why this is the defect class that explains the campaign history:

- Both loops wait on a hardware-granted status bit (`0x10000`, `0x100`) with no
  bound, no timeout and no bail-out. Both constants are reproduced from repository
  bytes by `scripts/repro_smu_globals.py` (report
  `evidence/firmware-audit/20260919-zd/globals-repro.json`):
  `_DAT_00017134 = 0x000FFFFF` at file `0x017134`, `_DAT_00017160 = 0x010FFE00` at file
  `0x017160`. The address convention is proven, not assumed: the PMFW type-`0x08` body maps
  1:1 to SRAM, checked against eight addresses that Ghidra's own `DumpGlobals` printed
  (8/8 at the same offset; `SRAM±0x100` reproduce 0/8).
  Substituting: the polled address is
  `((reg + 0x24) & 0x000FFFFF) + 0x010FFE00 + 0x200` =
  `0x01100000 + ((reg + 0x24) & 0xFFFFF)` — the domain status window, the same
  `0x0115B1DC`-class address the project recorded as the VCN wedge point.
- It matches observed boot behaviour exactly: the power request is accepted, the
  status bit is never granted, and the sequencer spins forever. The
  `mStagePowerTmo` (E6) telemetry in the dispatch-probe lineage is this poll not
  returning.
- It is a denial-of-service / permanent-wedge primitive, NOT an enable: it can
  hang the SMU (and the board with it) but cannot itself make VCN work.
- Open lead: addresses inside `_DAT_000178b8.._DAT_000178bc`, reproduced as file
  `0x0178B8` = `0x0005AFFF` and file `0x0178BC` = `0x0005B7FF` (interval
  `0x5B000..0x5B7FF`), bypass the master
  window and are routed to the second SMU core, so a domain-register class
  exists that is reachable only through that core. Whether VCN's status bit
  lives in it is untested. The reproduced interval `0x5B000..0x5B7FF` independently matches the D-R1 finding (`docs/research/2026-09-15-smu-ipc-d-r1-result.md`) that the Q3 `0x5C` path resolves to `0x0005C0FC`, outside this window — so no Q3-reachable payload lands there.

## 5.3 Gate byte `*(_DAT_000171ec + 0xf6)`

Verified excerpt location: `evidence/firmware-audit/20260919-zd/secure_cluster_decomp.txt`
line 263 (NOT in `domain_path.txt`; that file holds the §5.2 poll excerpts). The
same test appears twice in the same dump — line 263 as
`if (*(char *)((int)_DAT_000171ec + 0xf6) == -1)` and line 324 as
`if (*(char *)(_DAT_000171ec + 0xf6) == -1)` in `FUN_0001f2f0` (`0x5D`), so both
the `0x5C` and `0x5D` domain routes are gated by the same byte.

The Q3 `0x5C` handler (`FUN_0001f218`) — the firmware-side domain-14 power route:

```c
  pfVar7 = _DAT_000171ec;
  if (*(char *)((int)_DAT_000171ec + 0xf6) == -1) {
    func_0x00000fa8(param_1);      /* returns without doing anything */
    return;
  }
```

`-1` is `0xFF`: one byte decides whether the firmware-side VCN-cluster power
route runs at all. Interaction with ZD-2: the unguarded Q3 `0x98` path writes a
fixed `0xFF` to a caller-chosen masked offset, so that primitive can CLOSE this
gate but cannot clear it. Resolved 2026-09-19 (no board needed): the pointer at file `0x171EC` is `0x0000CEE0`,
so the gate byte is SRAM **`0xCFD6`**, and the image byte there is **`0x00`** — the gate is
OPEN in the firmware image. Ghidra shows 3 READ refs to `0x171EC` (the two handlers) and
**zero** refs to the gate byte itself, so no writer exists in the SMU body: the writer is
outside it (PSP/ABL or a runtime path). Report
`evidence/firmware-audit/20260919-zd/gate-byte-0xCFD6.json`. Consequence: ZD-2's fixed-`0xFF`
write could _close_ this gate (write `0xFF` to SRAM `0xCFD6`), but nothing in the image
closes it — the domain-14 route is open in the image, and the blocker is elsewhere.

## 5.4 Low-level window writer (`FUN_00002a74`), verbatim

Quoted from `evidence/firmware-audit/20260919-zd/window_decomp.txt` line 5 (this
is the writer ZD-2's fixed-`0xFF` path calls, and the primitive both ZD-3 polls
issue through `FUN_000235c8`):

```c
void FUN_00002a74(uint param_1,uint param_2,undefined4 param_3,int param_4)
{
  puVar1 = _DAT_00000d30;
  uVar3 = rsil(2);
  *_DAT_00000d30 = param_2;
  puVar1[1] = param_1;
  uVar5 = 0;
  func_0x000030b0(puVar1,8);
  ...
  if (param_4 == 0) {
    *(char *)((param_2 & uVar4) + iVar2 + 0x80) = (char)param_3;
  }
  else if (param_4 == 1) {
    *(short *)((param_2 & uVar4) + iVar2 + 0x80) = (short)param_3;
  }
  else {
    *(undefined4 *)((param_2 & uVar4) + iVar2 + 0x80) = param_3;
  }
  wsr(uVar5,uVar3);
```

Reading: `param_1` selects the window, `param_2` is the offset (masked by
`_DAT_00000bd8`), `param_4` is the access width (`0` byte / `1` halfword / `2`
dword), and the value comes from the caller. It masks interrupts with `rsil`
locally but performs no privilege check of its own — the guard, where one
exists, lives in the caller. The Q3 `0x98` caller passes `param_3 = 0xff`
hard-coded and `param_4 = 2`, which is the fixed-`0xFF` behaviour stated in §3.

## 5.5 PSP authority map (`$PSP`, 5.00 clv) — the trust-anchor-in-payload shape

Static pass, read-only, full table in
`evidence/firmware-audit/psp-authority-map-clv500.json` and the intent/result record in
`docs/action-logs/2026-09-19-psp-authority-map.md`.

Entry table geometry (corrected): 16-byte stride from `0x8E0010`,
`u32 type | u32 size | u64 location` with a tagged location (top byte tag, low 24 bits
SPI offset). 19 entries. `$PS1` sub-header at body `+0x10`.

Result 1 — **no unsigned carrier.** Tail = `size - 0x10 - sub_size` is `0x1F0` for 13
entries, `0x2F0` for the two KDB carriers, `0x65F0` for the nested type `0x44`. No entry
has an empty or truncated tail. The "PSP honours an unauthenticated entry" hypothesis is
dead on this image.

Result 2 — **the key that verifies the VCN-relevant carriers lives inside the KDB blob:**

```
0x24 SEC_GASKET            ... kid 96ea7cfec59d4c2a991e2c1f10d33bd8
0x45 TOS_SECURITY_POLICY   ... kid 96ea7cfec59d4c2a991e2c1f10d33bd8   (same key)
0x4F key record            ... kid 39bfc1922fa14ef285d9ae87e696d2b2
0x50 $KDB t50 copy         ... kid 39bfc192...   body contains all 8 t50 kids, incl. 96ea7cfe
0x51 $KDB t51 copy         ... kid 9ace85d9...   body contains all 3 t51 kids
```

So the chain reads: on-die ROM -> `39bfc192` -> KDB (types `0x4F`/`0x50`/`0x51`) ->
`96ea7cfe` -> gasket (`0x24`) + TOS policy (`0x45`) -> the VCN isolation grant.

Result 3 — **types `0x4F`/`0x50`/`0x51` name their own verifying kid.** `39bfc1922fa14ef2`
is declared by the type-`0x4F` record **and** by the type-`0x50` KDB carrier, and it is
t50's first key. A blob whose verification key is a key the blob itself declares is the
trust-anchor-in-payload shape.

What this does NOT prove, stated because the distinction decides everything:

- The declared kid proves which key id a carrier **names**, not which key the on-die PSP
  ROM **uses**. Whether `39bfc192` is an on-die/fuse anchor or is loaded from the image
  is untested.
- The verifier code itself was not read; it is in on-die ROM, not in the SPI image.
- Prior art in this project is a caution: substituting the `0x24`/`0x45` carriers
  (D3-B2) produced a non-booting board, which is consistent with those carriers being
  properly verified by `96ea7cfe`. That test did **not** touch types `0x4F`/`0x50`/`0x51`.

Next decisive test, cheap and local, no hardware: compare the `39bfc192` and `9ace85d9`
moduli against other donor images (`evidence/donor/retroweb-20260916/BC250_3.00.bin`,
4700S material). Identical moduli across different vendors' boards ⇒ AMD/ROM anchors,
chain closed. Different per image ⇒ the anchor is in the image and the chain is
forgeable, which would be the signature bypass on exactly the carriers that control the
grant.

## 5.6 Cross-image anchor test — the PSP signature-bypass lane is CLOSED

Six images, read-only; full record in
`docs/action-logs/2026-09-19-kdb-crossimage-anchor-test.md` and
`evidence/firmware-audit/kdb-crossimage-kids-clv500-lineage.json`.

Method: signature-scan for the KDB record pattern (`u32 size == 0x150`,
`u32@+0x0C == 65537`, `u32@+0x20 in (1024,2048)`), hash the full 256-byte modulus per
`kid`. Independent of PSP directory geometry, so it holds across BIOS versions.

Control image: **AMD 4700S C0A** (`bb2cf51df409`) — a different product (Ariel/Cardinal
C0A desktop kit), AMI build dated 2022-04-26, 18 PSP entries, no `0x24`/`0x45`.

Result: **all 15 `kid`->modulus pairs are identical everywhere they appear; no `kid`
anywhere carries two different moduli.** In particular the anchor `39bfc1922fa14ef2`
(declared by the type-`0x4F`/`0x50` carriers) has modulus `238e1f6b7f36` byte-identical
in BC250 2.00, 3.00, 3.00_CHIPSETMENU, 5.00, 5.00_clv **and** the 4700S C0A.

Verdict: an anchor that survives five independent AMI builds and a product change
unchanged is a shipped platform constant, not an image-local secret. The chain
ROM -> `39bfc192` -> KDB is **not** forgeable by editing the KDB **alone**: replacing the modulus
buys nothing because the trusted value is not the image's copy of it. That finding is
exactly why the delivered path (§7) pairs a glitch-installed key with carriers re-signed
under that key, instead of relying on a KDB edit. It retires the trust-anchor-in-payload
shape from §5.5 as unexploitable _by itself_ — types `0x4F`/`0x50`/`0x51`
do name their own verifying kid, but that kid is an external constant, so the naming is a
selector rather than a trust source.

Two side results:

- The KDB is **per-platform**: BC250 carries 7 kids absent from the 4700S, the 4700S
  carries 5 absent from BC250; only `39bfc192`/`9ace85d9`/`cc7d248a` span both.
- `96ea7cfe` — the key that verifies SEC_GASKET (`0x24`) and TOS_SECURITY_POLICY (`0x45`)
  — is byte-identical across all five BC250 builds and **absent** from the 4700S,
  consistent with the 4700S having no `0x24`/`0x45` at all. It is a BC-250-family signing
  key, held by the vendor.

Still open, none of which requires forging a signature: the SMU second-core register
class (`FUN_000235c8` routing `_DAT_000178b8.._DAT_000178bc` -> `0x1b514`); the gate byte
`*(_DAT_000171ec + 0xf6)`; persistence of `secure` across the `amdgpu` load.

## 6. V6 — capsule/update surface, audited to scope (2026-09-19)

- `CapsuleRuntimeDxe` (5632 B, `5d5ddcec…`): no verify/RSA/Pkcs/Auth/Cert/Hash
  strings; PE import directory empty (relocation-only), so verification does not
  live here.
- `CapsulePei` (6096 B) and `CapsuleX64` (14432 B): no capsule-verification
  strings; `CapsuleX64`'s string set is an x64 exception-dump template
  (`!!!! X64 Exception Type - …`, register dump), i.e. a fault handler, not a
  verifier.
- Netstack and storage stacks are present (`HttpDxe`, `HttpBootDxe`,
  `UefiPxeBcDxe`, `TcpDxe`, `Ip4Dxe`, `Ip6Dxe`, `Udp4Dxe`, `DnsDxe`,
  `HttpUtilitiesDxe`, `Nvme`, `Ahci`), plus `AmdPspRecovery`.
- Status: **no signature verification found in the three capsule modules; no
  vulnerability established** (an unsigned-capsule acceptance path would still
  need the platform update-policy PCD and the dispatch point to be read before it
  could be called a finding). Named next test: decode the `CapsulePei` entry and
  the platform capsule PCDs.

## 7. Falsifiability (what would overturn the two claims)

- ZD-1 is falsified if a body with a different hash bounds-checks
  `*(count+0x780)` before the increment, or if a fresh unlock attempt on
  `3c50bc9a` fails to reach the transfer path with a readback.
- ZD-2 is falsified if a `*(0x1714C+4)` gate is found on the `0x98` path in this
  exact body hash, or if `0x98` with a nonzero argument returns `0xFD`
  (prerequisite-rejected) before the gate is open.

## 8. Reproduction

- Decompilation: Ghidra 12.1.3 PUBLIC headless, language `Xtensa:LE:32:default`,
  project `/tmp/ghidra_projects/BC250_SMU`, scripts under `/tmp/ghscripts`
  (`DumpSecureCluster.java`, `DecompilePower2.java`, `DecompileWindow.java`),
  input the `smu_fw_robin_5` file hashed in section 1.
- Port-IO index: `objdump -d -Mintel` over `/tmp/clv_ext/modules/*Smm*.bin`.
- Extraction: `python3 scripts/firmware_audit.py <clv image> --output <json>
--extract-image <clv image> --extract-dir /tmp/clv_ext`.
