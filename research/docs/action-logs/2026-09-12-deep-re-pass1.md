# Deep-RE pass 1 action log (2026-09-12, Asia/Almaty)

## Intent (before any repo write except this log)

- Actor: root. Trigger: operator asked for full-BIOS RE, all exploitable
  vulns for future custom patched/AGESA BIOS builds, what to do about PSP,
  deeper process with RE skill, and whether the MCP reverse program helps.
- This turn is read-only toward hardware/firmware (no flash, no register
  writes, no MCP mutation). Planned repo writes after this intent:
  1. `docs/research/2026-09-12-bios-vuln-inventory.md` (the inventory).
  2. Result appendix in this log.
- Skills applied (read earlier this session): bc250-reverse-engineering,
  firmware-forensics, apcb-policy-analysis, uefi-dxe-validation,
  vcn-smu-probing, artifact-verification, cutter-reverse-engineering.
- Inputs (all existing, hashed): D10R rollback `post-rollback-d10r.bin`
  (`addef288...`, 16 MiB); its `post-rollback-firmware-audit.json`
  (19 PSP entries, 4 BHD entries, 4 FVs, 234 modules); NVAR probe output to
  `/tmp/d10r-nvar.json` (input untouched); AGESA `AmdPspDirectory.h`;
  upstream PSPTool `psptool/file.py` entry names; install manifest +
  eval doc for the Cutter/MCP stack; live `ss -ltnp` listener check.
- Rollback for the two planned files: working-tree diff, no commit.

## P1.5b interim result (2026-09-12, MCP session ports 8000/8001, observed)

- Cutter 2.5.0 + native MCP v0.1.6 live on loopback (`127.0.0.1:8001`,
  new `cutter` process; old instance still on 8000). Handshake:
  initialize 200, tools/list 200 (19 tools, 3 mutating untouched),
  health ok. Param lesson: detail/decompile take `addr`, not `offset`.
- Loaded + verified `0193_AmdNbioGfxARIPei_te.bin` (`63413be2...`, 78 fns):
  .text 85,423 B @0xa8. llvm-objdump rejects TE; used GNU objdump
  binary-mode `/tmp/gfxpei-dis.txt` (25,448 lines, scratch).
- FINDING 1: `0x1e0/0x1e1 <- 0x3` at file 0x24d4/0x24de sits in a defaults
  fill (fcn.00001bf8, struct +0x1cf..0x1ef+ get 0/1/3/7/0xf) — stock values
  come from PEIM defaults, not from a VCN-specific clamp.
- FINDING 2: fcn.00004c88 (57 KB) builds a `$VNI` (`0x564e4924`) init table:
  5-byte records (u16 ID, masked byte, value byte), 512-entry ID space
  0x1000+. Struct+0x1e0/0x1e1 serialize as IDs 0x10c3/0x10c4 (loop at file
  ~0x73xx: `mov %dx,(%rax)` + `and $0xfc`). Full decompile scratch:
  `/tmp/gfxpei-4c88-pseudo.c` (228,542 chars).
- FINDING 3 (closes an old misread): table IDs 0x13a9..0x13b7 are NOT NBIF
  registers. The chain report's S4 candidates (0x13b1005c…) do not occur;
  only ID 0x13b1 exists as a table tag. S4-negative fully explained.
- FINDING 4: `$VNI` magic occurs in NO extracted PE (runtime-built table).
  `IDS` string occurs in 5 DXE ARI drivers (CcxVh/Fabric/NbioGfx/NbioIOMMU/
  NbioPcie) — the table consumers. Next target: `0025_AmdNbioGfxARIDxe`
  (DXE), find ID→HW-register mapping = TRUE NBIF registers.
- FINDING 5 (port 8002, `0025_AmdNbioGfxARIDxe_pe32.bin` 13,376 B, 58 fns):
  DXE holds NO hardcoded $VNI IDs (table-driven); entry `AmdNbioGfxARIDxeEntry`;
  `GfxIntInfoTableInitARI` (ATOM display tables); `IdsHookFunc HookId %x`;
  I/O-port in/out cluster (fcn.00010f68 class) + rdmsr/wrmsr sites.
  Dispatcher fcn.00012274 walks hook table @vaddr 0x12990 for ID 0xB000000D
  (16-B entries: id/x/handler; local small-ID table [0x1B60..0x2A00,0x10080]
  has no B-hook → falls to generic IDS-protocol wrapper fcn.000125e0).
  Hook constant 0xB000000D occurs ONLY in 0025 across all 16 ARI binaries
  (4x: file 0xe91/0x22b1/0x22d6/0x230f). Next: decompile fcn.00010d28
  (0x10e91 user) + trace small-ID handlers' HW writes.
- FINDING 6 (port 8002 cont.): fcn.00010d28 = DXE entry orchestrator
  (Entry/Exit prints, VBIOS logs, GfxIntInfoTableInit fcn.00010500, hook
  dispatch). fcn.00010f68 = POST-code/CAR debug helper (CF8/CFC writes
  0x80000068 + arg|0xB0000000, NOT NBIF programming). fcn.0001232c =
  CPU-frequency detector (MSR 0xC001001F/0xC0010064+, PCI 0x8100c45c).
  fcn.00010500 (GfxIntInfoTableInitARI, 16,878 chars pseudo) = pure ATOM
  display-table builder: no I/O, no hooks, no $VNI IDs. So 0025 programs
  NO NBIF HW itself — it builds tables + IDS plumbing.
- FINDING 7: all 7 ARI DXEs carry I/O + MSR + CF8 sites (CcxVh 23/105/2,
  Fabric 35/15/2, IOMMU 17/12/2, Alib 11/9/3, Base 6/2/2, Pcie 17/12/2,
  SocBl5 12/11/1). Per-driver ID→PCI-reg tracing remains; nearest: 0021
  Fabric ARI (the bridge owner). Strengthens the boot-time-PSP-applies
  model: DXE ARI = tables/plumbing, HW commit likely at PSP DRIVER_ENTRIES
  application or inside one ARI driver's hook handler (unmapped yet).
- FINDING 8 (port 8003, `0021_AmdFabricAriDxe`): Fabric dispatcher
  fcn.00013658 handles hook 0x20000006 (same pattern as GFX B-hook).
  `AGESA set MMIO pair` string is DEAD here (zero code/data refs) but ALIVE
  in `0196_AmdNbioBaseARIPei` (PEI) — MMIO-pair programming lives in PEI.
  ReadyToBoot callback (~0x10a84, Rizin shows no function) prints
  `FabricReadyToBoot: Disable extended configuration access` then calls
  fcn.0001327c = DF-indirect READ fcn.0001307c(0,0,1,0x200,0xFF), tests bit 27.
- FINDING 9 — DF-indirect primitive DECODED (fcn.0001307c, static-analysis):
  args (a1 0..1, a2 0..3, a3 0..7 -> uVar4, a4 reg <0x400 aligned, val or
  0xFF=read). Read: MMIO `0xE0000000|(uVar4<<12)|(a4&0xFFF)|uVar2`.
  Write: index `((uVar2|0x405C))+0xE0000000 <- (((val&0xFF)<<5|uVar4)<<11
  |(a4&0x7FC)|1`, data from `((uVar3&0xFFFF8000)|0x4098)+0xE0000000`.
  This is the TRUE fabric programming transport (E0000000+405C/4098).
  Next: `0196_AmdNbioBaseARIPei_te.bin` (live MMIO-pair string) in Cutter.
- FINDING 10 (port 8004, `0196_AmdNbioBaseARIPei` 117 fns): MMIO-pair/
  DstFabricID/IdsHookFunc strings DEAD in 0196, 0021, 0194, 0199 (zero
  code/data/pointer refs across all 4; 0199's 1 hit = the string bytes
  themselves). Shared-source debug leftovers, not live paths. Dead-end
  closed cheaply, no Cutter time wasted.
- FINDING 11: PEI-side DF helpers mapped: fcn.00003cf2 (236 B, write class:
  `or $0x405C`/`or $0x4098` @0x3d7c) + fcn.00003dde (170 B, read class).
  NO direct calls to either anywhere in .text (63 indirect `call *`
  sites: PEI works via PPI dispatch — helpers likely installed as PPI
  services for other PEIMs). fcn.000021c4 (2002 B) = MMIO-base setup
  (MSR 0xC0010058/0xC001001A, E0000000 region, die/socket loops) calling
  fcn.00002996; full pseudo scratch `/tmp/basepei-21c4-pseudo.c`.
- STRATEGIC INFERENCE (static-analysis, needs test): NBIF/fabric HW
  programming happens in PEI phase via patchable PEIMs (0196/0193) + PPI
  services, DXE ARI = tables/plumbing/hooks, Fabric DXE locks ext config
  at ReadyToBoot. The D-series failed plausibly because DXE-time writes
  come TOO LATE (island down/locked). A PEI-time approach (patched PEIM
  defaults like fcn.00001bf8's fill, or $VNI/IDS inputs) runs while the
  fabric is still open AND keeps PSP acceptance (PEI FV unsigned — same
  proven V2 surface as DXE). Next: Init-Config-Struct source (HOB/PCD/
  NVRAM?) + DF-helper PPI install site + $VNI consumer in PEI phase.
- FINDING 12 (0196 chain CLOSED, direct calls): fcn.000021c4 (MMIO-base
  setup) -> fcn.00002996 (MMIO-pair programmer: per-die/unit loops,
  3 DF writes per pair via fcn.00003cf2: base, top, control with
  DstFabricID-ish bits; matches the dead debug format) -> fcn.00003cf2
  (DF-write primitive). Rizin xrefs confirm 2996<-21c4 and 3cf2<-2996
  (3x)+<-3dde. The earlier "PPI-dispatched services" hypothesis is
  SUPERSEDED for this chain: it is plain direct calls. Full pseudos:
  `/tmp/basepei-21c4-pseudo.c`, `/tmp/basepei-2996-pseudo.c`.
- CORRECTION (tool fallibility, own error caught): Rizin's 6 CALL xrefs
  to 0193:0x1BF8 (defaults fill) are FALSE — all 6 sites are indirect
  `call *%rdx` through the PEI Services Table (LocatePpi-class dispatch
  with PPI GUIDs like 0x9e51c84); zero static refs (code/imm/data) to
  0x1BF8 exist anywhere. The fill code is real and embedded in a larger
  live function (no padding at Rizin's 0x1BF2/0x1BF8 split — a function-
  split artifact), but its true entry/callers are UNRESOLVED. Lesson:
  never trust an indirect-call xref without checking the call instruction.
- CORRECTION 2 (own address-mapping slip, caught + fixed same session):
  `/tmp/basepei-dis.txt` and `/tmp/gfxpei-dis.txt` were built with
  `--adjust-vma=0xb0/0xa8` although both TEs map vaddr==paddr — every
  cited address from them was +0xb0/+0xa8 off. Redone cleanly
  (`/tmp/basepei-dis2.txt`, `/tmp/gfxpei-dis2.txt`, no shift) and all
  material attributions RE-VERIFIED: clamp `movb $0x3,0x1e0` at file
  0x242c inside MCP 0x1bf8-range; serializer `mov %dx,(%rax)` at files
  0x4ce1+ inside MCP 0x4c88-range; `call 0x3cf2` byte-confirmed 3x from
  0x2a41/0x2a5a/0x2a8d (all inside prologue-confirmed 0x2996) + 1x from
  0x3e7a (inside 0x3dde) — the 2996->3cf2x3 chain and the 3dde->3cf2 xref
  that Rizin reported were RIGHT. DF-codec sites: file 0x3CCC (inside
  0x3c0b) and 0x3DB7 (inside 0x3cf2); validators ASSERT df030256-59 in
  0x3e8e+ zone; bit27/ctz counters in 0x3e8e-0x3f40 zone (callee names
  Rizin-mapped, treat as provisional). Lesson: for TE always verify
  vaddr==paddr from segments BEFORE choosing objdump base; re-verify one
  anchor address per file.
- OPEN: Init-Config-Struct source (trace enclosing function's entry args);
  $VNI consumer in PEI phase; which MMIO pairs stock programs (run 2996
  inputs: 21c4's MSR/die computation vs donor behavior).
- FINDING 13 (0196 callees): fcn.00003c0b = DF READ primitive (same
  encoding as DXE fcn.0001307c; 2996 seeds its control word from
  3c0b(0,0,0xFF) low 2 bits). fcn.00001c14 = PPI-locate-and-call
  trampoline (GUID fragment in arg1: 0x9e6c4d8/0x9e6e030 class).
- FINDING 14 (0193 entry 0x1880): locates PPIs by GUID (0x9e51c84 class),
  then CPUID-ish silicon detect (`call 0x15d3`, mask `0xFFF0F00` =
  ExtFamily/ExtModel/BaseFamily) storing silicon ID + zeroed struct slot.
  Struct pointer for the defaults fill is passed as an ARG (fill reads
  -0x4(%rbp) set once from arg), likely via silicon-ID-keyed table
  dispatch — source still OPEN. Rizin's 6 xrefs stay classified FALSE.
- NEXT (ranked): (a) enumerate stock-programmed MMIO pairs exactly —
  cheapest decisive route is a post-restore runtime DF readback, not more
  static; (b) donor-side 2996-equivalent comparison (no VCN donor PEIM in
  corpus — gap); (c) $VNI consumer in PEI phase.
- No repo inputs modified; no MCP mutation called; no flash/hardware touched.

## Result (2026-09-12, after intent; observed)

- Inventory written: `docs/research/2026-09-12-bios-vuln-inventory.md`
  (19 PSP entries named via AGESA header + PSPTool, 234-module FFS census,
  V1-V15 with proven/open status, PSP strategy, MCP verdict, ranked next).
- PASS checks this pass: PSP/BHD/FV census from existing signed audit JSON
  (no re-parse needed); NVAR names via `scripts/nvar_audit.py` to /tmp
  (SecureBoot names redacted by tool design -> V15 inconclusive, test named);
  listener check confirms no MCP running.
- No hardware/firmware/register state changed. No MCP server started.
- `/tmp` probes kept out of the repo: `/tmp/d10r-nvar.json`.
- Open: V13 microcode path, V15 SecureBoot state, V5 S3 handler semantics,
  MCP GUI bring-up (operator path).
