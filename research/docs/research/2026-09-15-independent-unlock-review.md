# BC-250 unlock-claim and parallel-track review

Date: 2026-09-15

Reviewer: `sol-reviewer` (independent author/model; not a different-family review).
Scope is read-only review of the current BC-250 evidence root and completed-track
artifacts. No firmware, register, mailbox, programmer, or hardware write was
performed. Requested `xhigh` effort is unconfirmed by runtime metadata.

## Overall verdict

**INCONCLUSIVE — no unlock method is supported as a working VCN unlock.**

The evidence supports several primitives and failure modes, but not bridge
opening, VCN power/clock acceptance, rings, encode/decode, or a user-visible
codec result. The three Luna tracks are classified below. A track without a
completed report at an exact path is **INCONCLUSIVE / unreviewed**, not approved
by inference from its worktree or dispatch status.

## Direct checks

| Check                                     | Result                        | Evidence and limitation                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ----------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Exact `BC250_VCN_UNLOCKED.ROM` provenance | PASS                          | `/home/OWNER/orca/projects/bc250/archives/imported/loose-tmp-bc250/BC250_VCN_UNLOCKED.ROM`, 16 MiB, SHA-256 `93edce09bd583216ee571d4aa167b012ee3fd2fb4db3845fa1cf599704ab22cc`; import manifest agrees.                                                                                                                                                                                                                                                       |
| ROM structural parser                     | PASS / FAIL by layer          | `scripts/firmware_audit.py` exits 0; PSP and BHD Fletcher checksums and four FV boundaries parse. APCB checksum is **FAIL**: stored `0x03`, calculated `0x41` in `evidence/firmware-audit/20260915-vcn-unlocked/{inventory.json,apcb.json}`. A parser exit is not PSP acceptance.                                                                                                                                                                                |
| APCB policy state                         | PASS (observation)            | `apcb.json` records DFG words `0x001FFF00` at `0x130` and `0x16C`, i.e. stock DFG, not the separately hardware-booted `0x007FFF00` candidate state.                                                                                                                                                                                                                                                                                                              |
| ROM delta versus current read             | PASS (observation)            | `evidence/firmware-audit/dump-2-comparison-to-full-images.json` records 1,367,865 changed bytes in 10,582 ranges versus `dump/2.bin`; region counts: PSP 0, APCB 318, BIOS/UEFI 1,333,738. Independent comparison to `evidence/programmer/reads/20260914-identification/read-a.bin` found 1,363,640 differing bytes, including 31,352 bytes in `0x000000..0x01FFFF` and 1,331,954 bytes in `0xAE0000..0xE00000`. This is not a minimal or isolated unlock delta. |
| `VcnUnlockDxe` presence                   | PASS (static only)            | Extracted module `evidence/firmware-audit/20260915-vcn-unlocked/extracted/modules/0002_VcnUnlockDxe_pe32.bin`, 3,584 bytes, SHA-256 `67c5b93e02dc67307db5196b486a41e775e4542957932b245a1a72d07560640`; disassembly shows PCI CF8/CFC accesses and C2P commands `0x100B`, `0x100C`, `0x1033`. Presence and write-capable instructions do not prove DXE dispatch, mailbox acceptance, bridge opening, or VCN function.                                             |
| SVC7C exact-code rerun                    | PASS (emulated/static scope)  | `uv run --python 3.13 --with unicorn==2.1.4 python evidence/firmware-audit/20260914-svc7c/test_null.py` returns 16/16 and byte-identical output to `evidence/firmware-audit/20260914-svc7c/result.json` (SHA-256 `22ef8ef01886e00bc6ce08e45e303e392aa14598b8a177e16c7aa85969a9c948`). It reproduces synthetic NULL-address stores. Caller authorization, live VBAR, real address-0 mapping, and VCN usefulness remain unrun.                                     |
| Current runtime evidence                  | PASS for bounded observations | `memory/firmware-audit.md`, `docs/action-logs/2026-09-12-s2a-runtime-donor-aperture.md`, and related logs support 59/59 gasket writes with commit readback `1`, five raw stage4 numeric-address reads returning `0xffffffff`, mode1 probe/firmware discovery, and mode2/SMU wedge classes. The stage4 VCN-register/arbiter labels are retracted and those reads do not establish bridge state.                                                                   |

## Completed Luna report review

### Luna runtime — corrected version `d402163`

Exact reviewed files:

- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-runtime/docs/research/2026-09-15-parked-runtime-smu-psp-vcn-audit.md`
- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-runtime/docs/action-logs/2026-09-15-parked-runtime-audit.md`
- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-runtime/.orchestra/tasks/2/TODO.md`
- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-runtime/.orchestra/kb/parked-runtime-smu-psp-vcn.md`
- commit `d402163af175b1f3ca1bf896bdf3960c910f4751`

**PASS for evidence calibration; INCONCLUSIVE for the proposed D-R1 and any
working unlock.** The earlier reviewed version `cb92048` is superseded.

- PASS: report correctly keeps the runtime path parked rather than claiming a
  working unlock; records PMFW body SHA-256
  `5c805026581ace101ba43ef4d0f6b34354f4a61461a1c78d2fa6a335a53d9936`; and
  separates static, emulated, and hardware evidence.
- PASS: D-R1 is a bounded, no-hardware, offline discriminator. Existing logs
  support its premise: `docs/action-logs/2026-09-14-smu-window-followup.md`
  records callers at `0x2341C` and `0x24732`, ten `0x10D0` call candidates, and
  an unresolved receiver contract.
- PASS: the corrected D-R1 negative condition closes only the enumerated static
  scope; missing receiver semantics, indirect calls, or unmodeled entries remain
  **INCONCLUSIVE**. A positive identifies a candidate and does not prove a
  hardware transition.
- PASS: the corrected report treats stage4 as five raw numeric-address reads,
  not named VCN2 registers or a validated bridge/isolation oracle.
- PASS: D-R1 is no longer an H1 static falsifier. Challenging hardware isolation
  requires a separately approved experiment and a validated VCN2 observable.
- PASS: vulnerability labels are appropriately qualified where they distinguish
  primitive presence from attacker-controlled reachability (SVC7C NULL store,
  debug/write exposure, and internal IPC behavior). Hardware hazard claims are
  supported only for the recorded board procedures and regions.

### Luna PEI — corrected version `999a611`

Exact reviewed files:

- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-pei/docs/research/2026-09-15-offline-pei-vni-ids-unlock-analysis.md`
- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-pei/.orchestra/tasks/5/research.md`
- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-pei/.orchestra/kb/pei-vni-ids-unlock.md`
- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-pei/.orchestra/tasks/5/TODO.md`
- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-pei/docs/action-logs/2026-09-15-offline-pei-vni-ids-research.md`
- commit `999a6115bf0aebd73aa129f433fa702a27e29dac`

**PASS for corrected static evidence; INCONCLUSIVE for PEI acceptance and any
working unlock.**

- PASS: direct hashes of `dump/2.bin` and modules 0193/0196/0021/0025 match
  the report. Direct byte scans reproduce two `$IDS` markers per module and no
  literal `$VNI`; the report correctly does not treat the missing literal as
  evidence against a generated table.
- PASS: the corrected project log supports the exact 0196 primitive pair
  `0x3c0b`/`0x3cf2`, stock `0x2996` class-0/MSR-fed programming, nine 0021
  DXE write callers, and the empty stock-to-VCN segment-3 target delta. The
  proposed DF-windows-only V1 remains blocked because its target list is empty;
  the 56 VCN-specific writes are segment-9/HWID-12 with unresolved encoding.
- PASS: corrected artifacts attribute `0x14A35`/`0x14B1F` only to 0193 and use
  exact 0196 `0x3C0B`/`0x3CF2` with SHA-256 `51d96c1e...`.
- PASS: corrected artifacts describe range-check branches and ASSERT calls
  without claiming fail-stop rejection; helper `0x1318` remains unresolved.
- PASS: corrected V-PEI-1 limits PEI replacement to a static candidate surface;
  DXE replacement acceptance is not promoted to PEI acceptance.
- PASS with boundary: the examined `$VNI`-to-0196 aperture data path is refuted;
  this does not refute every `$VNI` consumer or a code-injection route.
- INCONCLUSIVE: `$IDS` consumer/hook structures and 0021 write sites establish
  an analysis surface, but the installer/producer, actual hook population,
  controllable inputs, and end-to-end target writes remain unidentified.

### Luna UEFI — corrected version `b780ff0`

Exact reviewed files:

- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-uefi/docs/research/2026-09-15-uefi-vcn-bridge-visibility.md`
- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-uefi/docs/action-logs/2026-09-15-uefi-vcn-bridge-research.md`
- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-uefi/.orchestra/tasks/3/research.md`
- `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/luna-uefi/.orchestra/kb/uefi-vcn-paths.md`
- commit `b780ff0b49beaceaf3e6519681434d8d46b2f0ba`

**PASS for corrected offline evidence and probe constraints; INCONCLUSIVE for
hardware observation and any working unlock.** The earlier `fa34af7` report is
superseded.

- PASS: `read-a.bin` and `read-b.bin` are byte-identical 16 MiB captures with
  SHA-256 `c0f5f1c59cd0503d99cec9fffc5b95c8897a2deabfa42dd389c924d6be6cc4de`.
  A fresh independent parser/extraction run returns 234 executable sections and
  reproduces the reported PSP/BHD/APCB/FV structure.
- PASS: source inspection establishes that `Bc250VcnProbeApp.c` is write-heavy
  and unsuitable as the proposed no-write probe. This is a source-tree claim,
  not yet an exact binary-equivalence claim.
- PASS: the corrected `BAR5 + 0x20F24` candidate offset is supported by the
  VCN2 header/base calculation. Its hardware meaning remains unrun, and the
  other historical VCN register labels remain unresolved.
- PASS: H1 now states that Shell visibility cannot falsify PEI ownership; a
  response observes aperture state only and does not identify the producer.
- INCONCLUSIVE: the report's opening sentence that the “bridge-control timing
  boundary is earlier than the current DXE candidates” is stronger than the
  evidence. PEI DF programming and later DXE writes/locking are static facts,
  but the decisive VCN bridge target and owner are unmapped. Read that sentence
  as a timing hypothesis, not a verified boundary.
- PASS: the corrected report excludes retracted stage4 labels from bridge
  evidence and keeps hardware isolation as a hypothesis.
- PASS: supplied EFI binaries are hash/type identified while source behavior is
  explicitly source-only; source-to-binary equivalence remains unverified.
- PASS: `20260914-identification/read-a.bin` is correctly labeled a dated
  historical capture, not live current-chip identity.
- PASS: the corrected manifest assigns exact selected-readback 0196 SHA-256
  `51d96c1e5a5e2c39f04fb962b0b5be686dea0a05eecbde829a4595fe3356884f`,
  and 0189 `AmdFabricAriPei` (96,680 bytes) SHA `c5b99650...`; offsets are kept
  tied to matching module identity.
- PASS: the proposed design requires PCI MSE, GPU/BAR validation, a known BAR5
  bound covering `0x20F24..0x20F27`, and exactly one dword read; it does not
  require bus mastering or write a BAR to discover size. A stall remains a
  cold-power recovery event.
- INCONCLUSIVE: Shell versus ReadyToBoot ordering, source/binary provenance,
  BAR5 preconditions, exact bridge state, PEI/DXE ownership, VCN power, rings,
  codecs, and hardware behavior are all unrun.

## Vulnerability and unlock-claim classification

| Claim                                                | Verdict                             | Boundary                                                                                                                                                                                                                               |
| ---------------------------------------------------- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| In-ship SMU debug primitive / Q2-Q3 write capability | PASS as a privileged primitive      | D9R/D10R evidence supports the carrier and SMU liveness; arbitrary user reachability and VCN effect are not proven.                                                                                                                    |
| Runtime gasket programming                           | PASS as transport/latch observation | 59/59 writes and commit `1` do not prove bridge state. The five stage4 `0xffffffff` values are raw numeric-address reads, not a validated VCN2 oracle.                                                                                 |
| Runtime route is logically impossible                | FAIL                                | Evidence parks/exhausts tested classes; it does not prove every alternate-core or future route impossible.                                                                                                                             |
| D-R1 static second-core IPC closure                  | INCONCLUSIVE (unrun)                | Safe next offline check; no board or firmware write authorized. A negative requires complete reachability/argument closure.                                                                                                            |
| Signed `$PS1` carrier as an unlock                   | FAIL as implemented                 | Correct-wiring D3-B2 no-boot evidence supports signature/policy rejection, but exact signature span remains unresolved.                                                                                                                |
| `BC250_VCN_UNLOCKED.ROM` as a working unlock image   | FAIL / unsupported                  | APCB checksum mismatches (`0x03` vs `0x41`), DFG is stock, image delta is broad, and only static DXE code presence is shown. This does **not** prove that the ROM cannot boot or execute; hardware acceptance and boot are unverified. |
| PEI DF read/write capability                         | PASS at static layer                | Exact 0196 `0x3c0b`/`0x3cf2` and stock callers support the primitive. ASSERT-driven input rejection and VCN target reachability remain unverified.                                                                                     |
| PEI module replacement/modifiability                 | INCONCLUSIVE                        | DXE replacement acceptance does not prove that a modified PEIM is accepted or dispatched. No PEI candidate was built or tested.                                                                                                        |
| PEI `$VNI` data-only aperture unlock                 | FAIL for examined path              | The examined 0196 aperture path is MSR-fed, while segment-3 supplies no VCN target delta. Other consumers are not globally refuted.                                                                                                    |
| SVC7C NULL-store as BIOS VCN unlock                  | FAIL                                | 16/16 emulation proves a defect under synthetic memory; no mutable caller or VCN-target path is proven.                                                                                                                                |
| Mode1 probe as VCN enablement                        | FAIL                                | It proves discovery/firmware loading only; attach, rings, codecs, and stability remain unrun.                                                                                                                                          |

## Unrun checks

- Full D-R1 static receiver and argument-provenance closure.
- DXE dispatch and mailbox acceptance for the `VcnUnlockDxe` in
  `BC250_VCN_UNLOCKED.ROM`.
- PSP acceptance, cold boot, a validated bridge transition, VCN power and clocks,
  rings, encode/decode/JPEG, and stability for that ROM.
- Live address-0 mapping, caller authorization, and VBAR state for SVC7C.
- Offline PSP signature-span/verification-transform proof.
- Hardware test of any proposed PEI, UEFI Shell, or runtime unlock method.

## Disposition

No reviewed claim supports authorizing a flash or hardware execution. Keep the
runtime path parked pending offline D-R1 closure. Keep the PEI route blocked on
target encoding and unverified PEI acceptance. Keep the UEFI probe design-only
until a separate build/review/approval path. The ROM checksum mismatch
and static-only evidence do not establish non-bootability. No PASS here grants
flash, mailbox-write, or hardware-test approval.
