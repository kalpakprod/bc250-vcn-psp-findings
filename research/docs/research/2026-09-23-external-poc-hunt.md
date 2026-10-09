# External PoC / exploit / CVE hunt (operator order 2026-09-23)

Operator order: find proof of concept, exploits, and vulnerabilities (zero-days first) —
everything needed to crack the task. Sources given by operator:
crowdere/Awesome-RE-MCP, river-li/awesome-uefi-security (registered separately in
`2026-09-23-external-uefi-security-sources.md`), chipsec/chipsec. All fetched 2026-09-23.
Nothing executed or installed; adoption goes through `external-stack-evaluation`.

## T1. DIRECT HIT: our ZD-1 bug is publicly exploited (BIOS 3)

`rw-r-r-0644/bc250-smu-unlock` (MIT, 13 stars, last push 2026-09-18):
"exploit **queue 2 msg 0x23** bug to unlock secure access functions (which allow fully
arb SMU rd/wr and **code exec**)". Repo note: "current repo is **BIOS 3 only**! (patches
etc. need different offsets for the SMU fw in BIOS 5!)".

- Queue 2 msg 0x23 is EXACTLY our ZD-1 ring-append overflow
  (`2026-09-23-smu-chain-development.md` §1, robin_5 geometry decoded to the byte).
- Independent confirmation the bug is real and weaponizable. Their chain: overflow ->
  unlock "secure access functions" -> arbitrary SMU rd/wr + code exec. Our worker's
  "data-only" verdict stands for the static window scan; the community path stages a
  firmware PATCH through the data primitive (their `patches/patches.hex` + `patcher.py`)
  instead of redirecting control flow from the overflow window directly.
- The BIOS 5 port needs: SMU fw offsets for robin_5 — WE HAVE THEM (our body IS the
  BIOS 5 SMU fw, sha `cae8617c…`): ring geometry `0x188A0/0x19034`, counters
  `0x19020..`, applier `0x2D4E0`, dispatcher `0x36428` state words, context ptr
  `0x197D0`. Port = identify the secure-access gate in robin_5 + rebuild patches.hex.
- Tool surface: `unlock.py`, `rpc_demo.py` (call-any-function primitive, added
  2026-09-05), `set_core_mask.py`, `patcher.py`, pyproject packaging.

## T2. VCN on BC250: community state of the art (Aug 2026)

`thelamer/bc250-vcn` (working notes, 2 commits, 2026-08-18). Converges with our own
findings and EXTENDS them:

| Fact                                                                                               | Their claim                    | Our record                        |
| -------------------------------------------------------------------------------------------------- | ------------------------------ | --------------------------------- |
| VCN 2.0.3 present, harvest=0                                                                       | confirmed                      | same (VCN-LOCK-MECHANISM)         |
| amdgpu skips VCN on Cyan Skillfish; no `dpm_set_vcn_enable`                                        | confirmed                      | —                                 |
| PSP rejects VCN fw: type 13 → `ITEM_NOT_FOUND` (`0xffff0008`)                                      | confirmed                      | matches our t02/park finding      |
| PSP type 64 TEE → `TEE_SUCCESS` but no-op; AMD-signed TAs load fail-open                           | confirmed                      | our V8 adjacent                   |
| **No `PowerUpVcn` message in SMU 11.8** (Xtensa, PMFW 88.6.0)                                      | proven by full decompile       | our C3 closure (PowerUpVcn NULL)  |
| **VCN POWER DOMAIN 6 IS ON**: `FUN_00023b14(6, 1)`, HW-acknowledge poll survives                   | NEW — power is NOT the blocker | our body: `0x23B14` in robin_5    |
| Blocker = SECOND GATE: clock/reset/isolation (slots `0x16/0x17/0x18`, teardown ref `FUN_00024764`) | NEW — their open threads       | our J3 fork = the same question   |
| Direct VCN MMIO (BAR5/UMR/SMN debugfs) hangs the board                                             | proven                         | matches operator field experience |
| Queue 3 msg `0x98` = ungated arbitrary SMN write (`0x00FF` to any SMN), PCI `0xB8/0xBC`            | the core-unlock primitive      | our 8c lineage                    |
| Debug setup: blacklist amdgpu, SSH, `dmesg -wH`, then modprobe; hangs need power-cycle             | operational gold               | adopt in runbooks                 |

Their open threads (priority order): (1) diff VCN power/clock/reset/isolation regs
before/after `FUN_00023b14(6,1)` — name the asserted gate; (2) program slots
`0x16/0x17/0x18` (`FUN_00023744` → `FUN_0002362c`) as prerequisite; (3) trace
VCLK/DCLK enable; (4) cross-reference Renoir/Van Gogh `*_dpm_set_vcn_enable`
reset/isolation steps; (5) only then the decoder ring test.

Relation to our plan: T2 says the unlock sequence EXISTS and is runtime-doable THROUGH
SMU-internal calls (not raw MMIO from the host). That is precisely lane V5's mechanism
(SMU-side function calls via proven transports) fused with T1's code-exec PoC. The
operator's "BIOS-baked" directive stays primary; T1+T2 give the runtime lane its
missing engine (code exec) and the exact next registers to move.

## T3. PSP boot ROM vulnerability class — matches our encrypted-0x01 lane

CVE-2021-26315 / GHSA-4qp6-97jw-9prg (AMD SB-1021, Nov 2021, High): PSP boot ROM,
when loading/authenticating and DECRYPTING an encrypted FW image, insufficiently
verifies the integrity of the DECRYPTED image → arbitrary code execution in PSP when
encrypted firmware images are used.

- Why it matters here: the trust root is the on-die ROM (we cannot dump or patch it);
  this is a documented ROM-class bug where a malformed ENCRYPTED image in the BIOS
  yields PSP code exec — a BIOS-baked, no-glitch route to PSP code exec.
- Open question: does BC250 (Oberon/Cyan Skillfish, Zen 2 family, 2019-2020 silicon)
  carry the vulnerable ROM revision, and does the 5.00 CLV image ship ENCRYPTED PSP
  firmware (our KDB carries type `0x01` encrypted entries — the brainstorm lane
  "encrypted type 0x01 / recovery" pointed here). NOT resolved this session.
- Also from SB-1021: bugs in ASP network/SMU/firmware TPMs of that era; and
  `amd-lm32-smu-exploit` (jevinskie) targets LM32 SMU v7 — NOT applicable (our SMU is
  Xtensa robin). CVE-2025-54510 targets Zen 5 — not applicable. CVE-2023-31309 (PMFW
  info disclosure) — low value, noted.

## T4. Tooling from the operator's links

- `chipsec/chipsec` v2.0.8 (GPL, active; chipsec2 runs in UEFI Shell): post-boot
  audit of SPI/SMM/SMN state — useful for F4/F5 verification ONCE a board boots;
  UEFI-Shell mode could audit the PSP/SPI state from firmware level on the BC250.
  Adoption via external-stack-evaluation; do NOT run on a board mid-experiment.
- `crowdere/Awesome-RE-MCP`: RE-tooling MCP index (GhidraMCP, ida-pro-mcp, CutterMCP,
  frida-mcp…). We already run ghidra-mcp/ghidrassist-mcp/Cutter MCP locally. Fills F4
  analysis throughput; no exploit content.
- `awesome-uefi-security`: registered in `2026-09-23-external-uefi-security-sources.md`.
- Cited inside T1/T2 and now on our map: `bc250-collective/amd_smu_reverse_engineering`
  (SOURCE of our `smu_fw_robin_5` body), `rw-r-r-0644/bc250-core-unlock`,
  `RescueMei/BC250-DXE-SMU-Core-Unlock`, `bc250-collective/bc250_smu_oc`,
  `rpf16rj SMU-HANDLERS.md`, `dayzerosec/AMD-SP-Loader` (PSP emulator + Binja loader),
  Dayzerosec PSP reversing (SMN/Syshub `MapSmn()` — explains unmapped-SMN-frame hangs),
  Buhren BH2020 PSP internals, coreboot `bl_syscall_public.h`/`bl_errorcodes.h`,
  `smu_v11_8_pmfw.h` (64 feature bits), `amd/firmware_binaries/v2000a` (closest
  relative APU — VCN power-up chain reference), `elektricM/amd-bc250-docs`,
  `duggasco/bc250-40cu-unlock`, `Forbidden-Darkness` UEFI menu script.

## Net verdict

The task is no longer exploring alone: (1) our ZD-1 has a public PoC on BIOS 3 and we
hold the BIOS 5 offsets — the port is concrete offline work; (2) the VCN "second gate"
is named and its moving functions are in OUR decoded body; (3) CVE-2021-26315 gives a
candidate BIOS-baked, glitch-free PSP code-exec route IF the image carries encrypted
PSP FW and the ROM revision is vulnerable — worth a focused session on the type-0x01
entries. The single unchanged blocker: a booting, instrumented board for every
hardware observation.
