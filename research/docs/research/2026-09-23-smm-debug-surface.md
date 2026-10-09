# SMM debug surface of AmdPspSmmV2 — dispatch decoded (2026-09-23)

Static analysis, read-only, no image modified. Source image:
`evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`. Module extracted with
`python3 scripts/firmware_audit.py <image> --extract-image <image>
--extract-dir scratch/smm-debug/ext` (233 modules) into
`scratch/smm-debug/ext/modules/0136_AmdPspSmmV2_pe32.bin` (24064 B).
Disassembly kept at `scratch/smm-debug/amdpspsmmv2.asm` (`objdump -d -Mintel`,
4674 lines). All offsets below are module RVAs = file offsets (`.text` VMA
`0x2a0`, file off `0x2a0`, so RVA/offset are 1:1 in this PE).

## Q1 — the SwSmiCallBack dispatch chain, and what reaches the 0x4169 stub

### There is no port-0xB2 dispatch in the module

Whole-module scan of the disassembly: the module contains **zero** `in`/`out`
instructions with DX = 0xB2. Every port op is FCH PMIO (0xCD6/0xCD8, e.g.
`0x12b4: mov edx,0xcd6` … `0x12b9: out dx,al`) or PCI config
(0xCF8/0xCFC). The only `0xb2` in the file is the operand of
`0x4189: mov rax,0xb2` inside the debug stub — a data value, not a port write.
So the module never _reads_ a software-SMI command from APM I/O itself; it
**registers** a callback and the SMM core dispatches to it.

### The one SW SMI the module registers

Registration site (`amdpspsmmv2.asm` lines 610-632, offsets `0xc98`-`0xcd8`):

```
cac: 44 0f b6 1d 2d 4c 00 00  movzx r11d,BYTE PTR [rip+0x4c2d]   # 0x58e1
cc1: 48 8d 15 84 f8 ff ff     lea   rdx,[rip+0xfffffffffffff884] # 0x54c   <- callback
ccb: 4c 89 5c 24 78           mov   QWORD PTR [rsp+0x78],r11
cd0: c6 84 24 80 00 00 00 80  mov   BYTE PTR [rsp+0x80],0x80
cd8: ff 10                    call  QWORD PTR [rax]              <- SwDispatch->Register
```

- Callback = function at **`0x54c`** (prints `PSP.PspSmm.SwSmiCallBack`, string
  at file `0x4978`, via `lea rdx,[rip+0x440e] # 0x4978` at `0x563`).
- The SW SMI **command number is a runtime byte**, not a constant: the register
  descriptor's input value is the byte at `.data+0x58e1`, which is filled by
  `CopyMem` from the `PSP_PLATFORM_PROTOCOL` block
  (`0x8c7: lea rbx,[rip+0x5012] # 0x58e0` … `0x8ed: call 0x41a0`, 0x18-byte
  copy at `0x8f0`). The protocol's first dword is printed as
  `SwSmiCmdtoBuildContext:0x%x` (string file `0x4ab0`, print at `0x7c3`). The
  in-file byte at `0x58e1` is `00`; the actual command value is whatever the
  PSP DXE installs into `PSP_PLATFORM_PROTOCOL` at runtime, so **the numeric
  SMI command for the resume-context callback is UNRESOLVED from this module
  alone** (it lives in the `PSP_PLATFORM_PROTOCOL` installer, AmdPspDxeV2/
  PspDxe — not read this pass).

### What the registered callback does — and does not do

Callback `0x54c` (`0x54c`-`0x61a`): checks an init flag at `0x5800`, locates
the PSP mailbox SMM buffers via `call [rax+0xd0]` with GUID at `0x4510`
(prints `mPspMboxSmmBuffer 0x%x` / `mPspMboxSmmFlagAddr 0x%x`, strings
`0x4998`/`0x49b8`), then `0x5e5: call 0xdd4` = `CopySmmSaveAreaToLocal` (reads
MSR `0xC0010111` SMM base, +0xFE00 per CPU, copies 0x200-byte save areas,
`0xe78`-`0xf13`) and `0x5fb: call 0x1428` = `UpdateS3SaveAreaMap` (builds the
per-CPU SMI-entry redirect via MSR `0xC00110E0` SMM intercept, writes the
`0x305c` trampoline for cores 0..15). This is **S3/S0i3 CPU resume-context
reconstruction**, matching the string `Register SW SMI for prepare CPU resume
context` (file `0x4cd0`). No path from `0x54c`, `0xdd4`, `0x1428`, or the
mailbox sender `0x2f74` (writes command byte at `[rsi+8]`, flag `0x1` at
`[rdi]`, no I/O) reaches the stub at `0x4169`.

The sibling Sleep callback `0x504` (string `PSP.PspSmm.SleepCallBack`,
`0x4958`) reads its command byte from the caller's context
(`0x52c: mov cl,BYTE PTR [rbx]; 0x52e: call 0x2f74`) and forwards it to the
PSP mailbox — again no 0xB2 I/O and no path to the stub.

### Every SMI command number handled

| #   | Command                                                                                                                         | Source                                  | Handler            | Effect                                       |
| --- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- | ------------------ | -------------------------------------------- |
| 1   | SW SMI, value = runtime byte `PSP_PLATFORM_PROTOCOL.SwSmiCmdtoBuildContext` (file byte `0x58e1` = 00; numeric value UNRESOLVED) | registered at `0xcd8`                   | `0x54c`            | S3/S0i3 CPU resume context via PSP mailbox   |
| 2   | Sleep SMI                                                                                                                       | separate registration, callback `0x504` | `0x504` → `0x2f74` | forwards a command byte into the PSP mailbox |

That is the complete SW-SMI surface of AmdPspSmmV2. **No SMI command number in
this module reaches the `0x4169` stub.**

### The 0x4140-0x4195 stub is unreferenced dead code

- No direct call: `grep "call   0x4165\|call   0x4144"` → zero hits.
- No data/lea reference: `grep "# 0x4165\|# 0x4144\|# 0x4130"` → zero hits.
- Byte-level pointer scan of the whole 24064-B PE for `0x4144`, `0x4165`,
  `0x4169` as DWORD RVA or QWORD VA → zero hits.
- `movabs rdi,0x9c5a203a` (magic `0x9c5a203a`) is **not unique to this
  module**: the 32-bit LE pattern `3a 20 5a 9c` occurs in ~40 extracted
  modules (CpuDxe `0x4a65`, AmdSmmControl `0x1b95`,
  AmdSmmCommunication `0x2975`, FchDxe `0x2435`, CbsSetupDxe `0xb015`, …),
  and the raw image carries 19 copies (e.g. SPI `0xe10837`, `0xe181a7`) plus
  19 copies of the paired CPUID leaf `0xbaccd00b`. In `0011_CpuDxe_pe32.bin`
  the bytes at file `0x4a50` are **byte-identical** to AmdPspSmmV2
  `0x4140`-`0x4164`: `51 57 50 52 48 b9 0a 10 01 c0 … 0f 30 48 c7 c0 b2 00
00 00 f1 5a 58 5f 59 c3`.
- Conclusion: the `rdmsr 0xC001100A / or rax,1 / wrmsr / int1` stub plus the
  `cpuid 0xbaccd00b` probe are a **linked-in AMD debug-library artifact
  replicated across the AGESA build**, not a PSP-SMM feature. Nothing in this
  module — no SMI command, no protocol, no data pointer — transfers control
  to it. `and rax,0xffffffffffffffff; or rax,0x1` (bytes `48 83 e0 ff / 48 83
c8 01` at `0x417f`-`0x4186`) remains a no-op-masked bit-0 set of MSR
  `0xC001100A`, by whoever would call it — and nobody in-image does.

## Q2 — OS reachability

- AmdPspSmmV2 never reads APM I/O (`out`/`in` with DX=0xB2 absent), so the
  only OS-visible SMI entry is whatever command the SMM core routes to the
  registered callback — and that callback is the S3-resume context builder
  with no branch to the stub.
- Guards on the callback: the init flag `[0x5800]` (one-shot, set at `0x60c`,
  cleared at `0x6b1`), and the PSP mailbox buffers must be located via the
  GUID at `0x4510` before the S3 path runs. `mPspMboxSmmBuffer`/
  `mPspMboxSmmFlagAddr` are printed for debug only, no magic check.
- `SmmCommunicationProtocol` appears only in the string
  `AmdS3SaveLib locate SmmCommunicationProtocol fail` (`0x4fe8`) — a debug
  print from the S3-save lib, not a runtime communicate surface in this
  module.
- The `ApSmmResumeVector`/`BspSmmResumeVector` strings (`0x4e48`/`0x4e60`)
  belong to the same S3 resume path.

Verdict for Q2: the stub is not reachable from a booted OS through this
module's SW SMI surface; it is not reachable from any in-module caller at all.

## Q3 — `DBG_UNLOCK_MODULE` strings at SPI `0x98082B`

- `0x98082B` falls inside the **PSP directory entry index 5, type `0x13`**
  (directory at `0x8E0010`; entry body SPI `0x97F700`-`0x981840`, 8512 B,
  body SHA-256 `d21f7eeda1af91c9c350e21767d6379f0e768e2269ce6fa2c3a03abfd67e321a`,
  verified by hashing the byte range). String offset in body: `0x112b`.
- The surrounding bytes are **ARM Thumb code, not x86**: e.g.
  `2d e9 ff 4f` (`push {r0-r12,lr}`), `85 b0` (`sub sp,#0x214`),
  `ff f7 …` (`bl`), `_ ea 00 0a` (`orr.w`) immediately after the strings
  (raw dump: `…-\xe9\xffO\x85\xb0\x83FO\xf0\x00\t\x02!\x01\x22\x03\x91…`).
- Full string set in that entry (raw offsets `0x980779`-`0x980867`):
  `Svc_GetDebugUnlockInfo Status = `, `Received UnlockMode = `,
  `UnlockNegotiation with HdtError = `, `SecureUnlock with HdtError = `,
  `Securely UNLOCKED`, `Failed to Lock ASIC`.
- Reading: this is the **PSP-side (ARM) Hardware-Debug-Tool unlock state
  machine**. `Svc_*` are PSP secure-service calls; the module queries debug
  unlock info, negotiates an unlock mode, performs SecureUnlock, prints
  `Securely UNLOCKED` on success and re-locks the ASIC afterwards
  (`Failed to Lock ASIC` is the failure path). The state that
  `Securely UNLOCKED` reflects is the **PSP HDT (JTAG-class on-die debug)
  grant**, negotiated inside the PSP security processor — it is not an x86
  SMM variable and not gated by any port-0xB2 command. It is a boot-time /
  PSP-firmware-internal surface; the linked predecessor analysis
  (`docs/research/2026-09-19-zero-day-confirmation.md` §5.1) treated it as
  "same feature family", which is now narrowed: **different processor, no
  decoded linkage to the x86 stub**.

## Q4 — verdict

**UNRESOLVED as an OS-reachable unlock — and the evidence points negative: the
x86 `rdmsr/int1` stub is unreferenced dead code replicated AGESA-wide, the
only SW SMI AmdPspSmmV2 registers is a runtime-keyed S3-resume context builder
with no path to the stub, and the `DBG_UNLOCK_MODULE` "Securely UNLOCKED"
state belongs to an ARM Thumb PSP-side HDT module (PSP entry type `0x13`,
body `d21f7eed`), so no software-reachable debug unlock from the booted OS is
established by this image.**

## What was checked and not found

- `call`/`lea`/pointer references to `0x4140`-`0x4169` in AmdPspSmmV2: none.
- Port `0xB2` reads/writes in AmdPspSmmV2: none.
- Other modules calling into AmdPspSmmV2's stub: not traced cross-module by
  SMM-core registration (the stub is not registered anywhere — no reference
  bytes exist in the module).
- The numeric value of `SwSmiCmdtoBuildContext` (the one SW SMI command
  number): set at runtime by the `PSP_PLATFORM_PROTOCOL` installer; the
  candidate installers are `0031_AmdPspDxeV2_pe32.bin` / `0068_PspDxe_pe32.bin`
  — not decoded in this pass. This is the single open byte for a complete
  command-number answer.
