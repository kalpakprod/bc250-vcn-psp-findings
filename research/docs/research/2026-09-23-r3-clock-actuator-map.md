# R3 — Clock actuator map: domains, chains, and the 1:1:1 boundary

Date: 2026-09-23 (Asia/Almaty)
Task: Plane «BC250» issue #3 (R3) — resolve clock semantics (MemoryClockSpeed,
UclkDiv1M0, MemoryPstate, FclkDpm, DfClockOverrideControl/DfClockOvrd consumers;
the 1:1:1 vs native-help contradiction; justified initial profile).
Status: **SMU-side actuator map + ABL-side producer chains proven** (static + image
bytes + bounded emulation + an empirical diff of the operator's four SYNC OC
profiles). The 1:1:1 negative is now corroborated empirically: the Setup→clock
bridge does not exist on the analyzed surface — the boot chain reads APCB tokens
only, and the operator's own 1:1:1 mods edited NVRAM only, leaving the APCB
byte-identical. **Units closed at the query surface by a live hardware run**
(2026-09-23 probe4l/probe4l2: the SMU's own clock answers are real MHz/mV, and
the DF pstate row values + derivation pattern are confirmed by the SMU's own
answers — §5). Not a profile recommendation; the only hardware actions were
read-only mailbox queries.

## 1. The clock-domain actuator (byte-proven)

Every clock domain is programmed through one generic engine:

```text
FUN_00023890(domain, code)
  -> descriptor: [slot 0x1745c] + domain*0x1C  (table base = 0x0F568 in image)
       +0x254 : raw program offset
       +0x80/0x83/0x98: group/ramp/hook flags  (second base [slot 0x178fc] = 0x0F728)
  -> FUN_000235c8(raw, code)
       write: *( (raw & 0xFFFFF) + 0x010FFE00 + 0x200 ) = code     [slots 0x17134/0x17160]
       poll:  same window +0x24, bit 0x10000
       IPC branch: raw in ( [slot 0x178b8], [slot 0x178bc] ] -> func_0x0001b514 transport
  -> descriptor +0x82 (current code cache) updated; ramp helpers 0x23fb8/0x24084/0x24128
     step the code when the domain has the ramp flag.
```

Domain table from the image (program cells `[0x0F568 + id*0x1C + 0x254]`):

| domain | role (from byte-proven callers)              | raw     | SMN program | SMN poll   |
| ------ | -------------------------------------------- | ------- | ----------- | ---------- |
| 0x03   | channel-sync pair member (FUN_0001efb4/ef90) | 0x5B18C | 0x0115B18C  | 0x0115B1B0 |
| 0x04   | channel-sync pair member                     | 0x5B1B4 | 0x0115B1B4  | 0x0115B1D8 |
| 0x0E   | **FCLK** (SetupFclkPll)                      | 0x5C0FC | 0x0115C0FC  | 0x0115C120 |
| 0x0F   | **UCLK** (SetupUclkPll)                      | 0x5C8FC | 0x0115C8FC  | 0x0115C920 |
| 0x10   | derived (UCLK/2^k within bounds)             | 0x5C924 | 0x0115C924  | 0x0115C948 |
| 0x11   | UCLK mirror                                  | 0x6C0FC | 0x0116C0FC  | 0x0116C120 |
| 0x12   | derived mirror                               | 0x6C124 | 0x0116C124  | 0x0116C148 |
| 0x13   | power-gate special (0x01D80214/218 block)    | 0x6C900 | 0x0116C900  | 0x0116C924 |
| 0x18   | selector-11 domain (group 6)                 | 0x6D150 | 0x0116D150  | 0x0116D174 |

Cross-check: domain 0x18 → SMN 0x0116D150/0x0116D174 is byte-identical to the
independent decode in `docs/research/2026-09-21-smu-domain-selector.md`. Domains
0x03/0x04 (raw 0x5B18C/0x5B1B4) fall inside the IPC interval (0x5AFFF..0x5B7FF per the
selector report) and take the `func_0x0001b514` transport branch in `FUN_000235c8`,
not the direct SMN window.

## 2. The boot chains (byte-proven handler bodies)

- **FCLK**: ABL1 `0x5E68` → SVC28 id `0x0E` (`SetupFclkPll`) → SMU `FUN_0001f218`:
  arg × 0.001 → `FUN_00023cb8` → `FUN_00023c78` divider code → `FUN_00023890(0xE, code)`
  → SMN 0x0115C0FC; also stores the resulting float at `[DF+0x00]` (current FCLK slot).
  Emulated end-to-end with the real APCB bytes: clean-CLV APCB gives arg **1420**
  (gate token 0x015F=1 at APCB+0xB99, value token 0x0160=**1420** at APCB+0xB9A);
  gate off → default **1200** (`docs/research/2026-09-23-abl-pll-service-boundary.md`).
- **UCLK**: ABL1 → SVC28 id `0x0F` (`SetupUclkPll`) → SMU `FUN_0001f2f0`: same encoder,
  programs domains **0x0F and 0x11**, then derives 0x10/0x12 by dividing the domain-3
  product by 2^k (k=0..3) until it fits the bounds at `[0x17488]`; fallback code 0x60.
  The ABL1 argument is the memory word shifted right by 1 (`LSR.W R8,R4,#1` at 0x5F30,
  overwriting R8): **mem word 1800 → UCLK arg 900** (emulated, 9 cases).
- **UCLK refinement (dead value-table, byte-proven)**: the same block contains a
  constant table (225→200, 450→400, 600→500, 850→750, 850+480→760, 850+900→1000,
  general path = `memword>>1` through float helpers with constant 1.9 and a
  200..1000 clamp). Every branch stores into `[sp,#4]` (`0x5F6C/0x5F70/0x5F8E/0x5F92`),
  and `0x5FA8` then **overwrites the same slot** with the FCLK default before any read —
  the table is dead code. The only live output of the block is the unconditional `LSR #1`
  at `0x5F30` whose result (R8) is the SVC28 `0x0F` argument at `0x5FF4..0x5FFA`.
  The earlier session's "table+clamp may refute the /2" concern is resolved: it was an
  artifact of reading the block without the `0x5FA8` overwrite.
- **Service names from the firmware's own strings** (inline after the function):
  entry `"GnbSmuInitAblCAR Entry"` (0x602C — function `0x5E68` is GnbSmuInitAblCAR),
  `"Send PSPSMC_MSG_SetupFclkPll"` (0x60C0, logs the `[sp,#4]` value at the `0x0E` SVC),
  `"Send PSPSMC_MSG_SetupUclkPll  0x%x"` (0x60E4, logs R8 at the `0x0F` SVC),
  `"Send PSPSMC_MSG_ConfigSocRail"` (0x6080, SVC28 id 9 with the composed word
  `0x5A | ulUMCEnValue<<24 | status-flags` — an R2-relevant observation: this early
  SoC-rail config message carries a UMC-enable value, **no voltage**).
- **DF p-states**: static rows at 0xCF0C/CF34/CF5C/CF84/CFAC (0x28 stride), row `+0x18`
  = the frequency float the query returns (`FUN_0001e7d8`: `[pstate*4 + DF+0x1C] + 0x18`;
  the pointer array at 0xCEFC is zero in the image — runtime-initialized, candidate
  `FUN_0001e038`). Image row values: **450, 450, 850, 1750, 250**, each with derived
  halves at +0x10 (row3: 875 = 1750/2) and +0x14 (row3: 109.375 = 1750/16).
  Switch: SVC28 id 7 (`SwitchToStartupDfPstate`) → `FUN_0001e720` → `FUN_0001e448`
  selects by index and feeds row fields to `0x23250`/`0x1e170` helpers.
- **Channel sync 3/4**: `FUN_0001efb4/ef90` drive `FUN_00024410/0x2445c` (channel table
  at `[0x1745c]`, 0x48 stride — RMW window write + program + restore), gated by the
  DF flag at `+0x19` and fed from PPTable byte `[0x17120+0x61] × [0x17450]`.

## 3. The OS route is closed for FCLK/UCLK (byte-proven negative)

The q3 `0x1D` selector array (cells `0x13EF0 + sel*4`, sel 1..20, read from the image)
maps selectors to domains:

```text
1:0x0D  2:0x00  3:0x01  4:0x02  5:0x03  6:0x04  7:0x05  8:0x06  9:0x07  10:0x0A
11:0x18 12:0x13 13:0x14 14:0x15 15:0x16 16:0x17 17:0x0B 18:0x08 19:0x09 20:0x0C
```

**Domains 0x0E, 0x0F, 0x10, 0x11, 0x12 are absent from the array.** The runtime q3 0x1D
mechanism (the community `set_soc_clock_for_index`) cannot reach the FCLK/UCLK PLL
domains; they are programmed only by the early ABL1 boot services. This closes the
"OS can reprogram FCLK/UCLK at runtime" hypothesis within the analyzed surface.

## 4. The row+0x18 writer — extended bounded negative

`FUN_00022d6c` transitive closure (depth 3, 49 functions dumped this session) contains
no writer of the DF pstate rows or `row+0x18`. Combined with the prior bounded pass
(`row-writer-result.json`: 53 l32r leads, 7 candidates classified, none a row writer),
the working conclusion is that **the DF pstate frequency table is a firmware constant**
(450/450/850/1750/250), runtime pointers aside. Bound: the census covers the mailbox
handlers and the 22D6C closure, not every SMU-internal loop; the negative is bounded,
not absolute.

## 4a. Producer chains: Setup values do not reach the boot clocks

Proven this session (byte-level + census + empirical profile diff); the earlier open
producer edges are now closed.

**The MCLK policy (ABL service item 0x17 = `0x95FC`).** The caller at `0x7E30..0x7E74`
invokes service 0x17 (`movs r1,#0x17; bl 0xc60`), which is the function at `0x95FC`
(service-table entry, per `20260923-mclk-item17`). It fills `context+0x2BC` (the memory
word) from three candidate writers; the executed source is the **APCB item-7 token**
(runtime cache `+0x482`, enum `0x24` = 36 = 1800 in the donor image). The writer census
(emulated native window `0x221D..0x1F000`, real APCB at 0x7B000): item7 `0x24` →
policy 1800, item7 `0x23` → policy 1750, and a **different CMOS/Setup word (CTX+0x516)
is ignored** (1650 injected with native APCB → still 1800). No writer outside the
native CMOS/APCB paths touches the watched APCB offsets — verdict CLOSED-NEGATIVE.

**The serialized CBS tokens have no consumer.** All seven target tokens
(`0x11ED` MemoryClockSpeed, `0x1204` UclkDiv1M0, `0x1203`, `0x1331` FclkDpm,
`0x1363/0x1364` VDDCR_VDD offset, `0x1373/0x1374` DfClockOverride) are written into the
NVTB/INV buffer by exactly 7 ARI/CBS PEIM modules at 49 serializer sites
(`20260919-inv-token-consumers`, byte-verified). The only direct readers of that buffer
in the whole extracted corpus are 4 call sites requesting tokens
`0x10FF/0x1104` (AmdFabricAriPei) and `0x1000/0x1001` (AmdCcxVhAriDxe) — **none of our
tokens**. `UclkDiv1M0` (INV `0x1204`) has no consumer anywhere in the corpus.

**APCB token 21 ("UclkDiv") has no reader either.** The APCB runtime cache carries a
token-21 entry (`+0x86E..0x872`, value `01`), labeled by the prior session's native
parser decode. The provider `0x463C` (runtime-cache token read via `0x4800`, valid
IDs 1..0x160) is called from exactly **one** ABL1 site (`0x5FAE`) with ID `0x0F`
(the FCLK override). No code reads token 21; the UCLK argument is the unconditional
`memword>>1`. UclkDiv1M0 is an orphan on both surfaces (NVTB token and APCB token).

**Empirical corroboration: the operator's own 1:1:1 attempts were structurally inert.**
ROM `0x0` is the EFI variable store (`EFI_SYSTEM_NV_DATA_FV` GUID at ROM 0x10,
`_FVH` at 0x28) — that is where Setup values persist. The four SYNC OC profiles
(including both 1:1:1 attempts) differ from the clean donor **only inside this NVRAM
region** (~3 KB, 369-371 ranges): MCLK enum `0x24→0x23` at 0x7E5 (1800→1750;
profile 02 uses `0x1A` = its 1333 target), DfClockOverride `1420→875/1333/1750` at
0xBD3..0xBD4, a UclkDiv-region `01→03` edit at 0x716..0x71C. Their **APCB region
(0xAB1000, 2972 B) is byte-identical to the donor** — zero diff ranges. The mod
author's own arithmetic is visible: profile 01 sets FCLK = 1750/2 = 875
("FclkUclk 1:1" = FCLK=UCLK at half rate), profile 03 sets FCLK = 1750 = MCLK
("full 1:1:1") — both assume UCLK can be driven to MCLK; the firmware hardcodes
UCLK = MCLK/2, so no NVRAM-only edit can reach 1:1:1, and the ABL/SMU chain never
sees the NVRAM values at all (APCB is the only boot input).

**The DfClockOverride → APCB 015F/0160 "producer link" is a shared build default,
not a bridge.** The donor APCB carries the pair (gate 1, value 1420) as a
build-time default matching the Setup default; the operator's board dump `2.bin`
(a different BIOS build, §6(d)) has a 2928-byte APCB whose tail override row is
present but **disabled** — (0, 0, 1000) vs the donor's (0, 1, 1420), see §7.3. No
Setup-path writer of the flash APCB exists on the analyzed surface (corpus reader
census + ABL window census + the profiles' untouched APCB).

Consequence for the falsifier list: **(a) is closed** — no `UclkDiv1M0` consumer
exists on either surface; the 1:1:1 negative now rests on the hardcoded `/2` plus
the closed OS route, with (b) second UCLK path, (c) units, (d) board revision as
the remaining named falsifiers.

Provenance caveat: the four SYNC profiles are imported recon artifacts; whether they
were constructed by a tool or dumped after Setup changes is not established. Either
way the conclusion is the same: the flash APCB was not touched by the Setup edits.

## 5. Units boundary (closed at the query surface by hardware, 2026-09-23)

Static basis: service args 1420/900 feed `FUN_00023cb8` (`trunc([0x1729c]·f·2)` with
/50 or /200 corrections) and `FUN_00023c78` (`current × 0.1 × 256 / f` → `+0x3F` →
`FUN_00023ecc` divider encoder). The final code is relative to runtime coefficients
([0x1729c], [0x1792c], [0x17930], VCO).

Hardware run (probe4l2, read-only public query messages over the Linux mailbox,
`evidence/runtime/20260923-234734-probe4l2-clocks-full.json`, SMU alive throughout):

- **The SMU's clock answers are real MHz across every family**: CPU p-state ladder
  3200/2550/2325/1960/1820/1600/1271/800 (q3 0x3B, 8 p-states; 3200 = the top of
  the board's own ladder — the silicon is the 4700S-family 8-core **Zen 2** with
  GDDR6, per the donor lineage `docs/action-logs/2026-09-14-donor-bios-4700s.md`),
  live per-core 2629/1400×5/1337/2386 (q3 0x43 — idle 1400, active 2629),
  GFX 2200 (q0 0x0F and 0x37 agree; 2200 = the board's known max GFX clock), SoC DPM
  1254/500/762/762 (q3 0x42 = q0 0x11). Voltages in mV: CPU 724, GPU 1018 (q3 0x36/37).
- **The DF pstate table is confirmed by the SMU's own answers** (selector family
  q3 0x38/0x39/0x3A, answers only for sel 0..3, clean 0xFF rejections beyond —
  exactly 4 reachable states):

  | sel (pstate) | 0x38 | 0x39 | 0x3A | static row (§2) | 0x39 check          | 0x3A check                |
  | ------------ | ---- | ---- | ---- | --------------- | ------------------- | ------------------------- |
  | 0            | 250  | 225  | 112  | 450             | 450/2 = 225 ✓       | 450/4 = 112.5 → 112 ✓     |
  | 1            | 250  | 225  | 112  | 450 (duplicate) | identical answers ✓ | identical ✓               |
  | 2            | 750  | 425  | 106  | 850             | 850/2 = 425 ✓       | 850/8 = 106.25 → 106 ✓    |
  | 3            | 1200 | 875  | 109  | 1750            | 1750/2 = 875 ✓      | 1750/16 = 109.375 → 109 ✓ |

  Four-for-four exact /2 matches (0x39), the k-derived pattern of the static +0x14
  fields (0x3A; row3 static 109.375, hardware 109), and the duplicate rows 0/1
  answering identically — the static decode at 0xCF0C.. is the table the SMU itself
  serves. The /2 derivation — the same arithmetic as the hardcoded UCLK = MCLK/2 —
  is hardware-observed at the query surface.

- **0x38 answers (250, 250, 750, 1200) are not the static +0x18 image constants**
  (450/450/850/1750). The +0x18 pointer array is runtime-initialized (§2, §4), so
  0x38 most plausibly returns the live per-pstate fabric clock; the top step 1200
  equals the FCLK **default** (gate-off emulated value), not the donor override 1420.
  Identity of 0x38 not fully pinned from one run; it contradicts nothing and matches
  the "runtime-initialized rows" reading. q0 0x13 reports the current DF pstate = 3.
- Remaining units gap (narrow): the live FCLK/UCLK/MEMCLK values themselves did not
  appear in any answered message, and the runtime coefficients [0x1729c]/[0x1792c]/
  [0x17930] are **measured-unreachable through 0x2A** (2026-09-24 probe4l3/4l4: the
  0x2A service is an aperture over a fixed register set — the image-offset SRAM
  slots and the 0x0115C/0x0116C PLL windows all answer status-0x1 + 0x00000000,
  while 0x0005A870/0x0000CCB8/0x0115Dxxx serve real data). The 1420/900 service
  args are MHz-class by family membership (same numeric family as the
  confirmed-MHz answers), which is the strongest units statement available. The
  remaining live-value routes are static (FUN_0001cd80 consumer census of the
  plan's low bits) or the v003b flash experiment (patch 0160 → 1800, flash,
  re-run the battery: the c38 top step moving = the override applies).

## 6. Consequence for the 1:1:1 goal (R3 core question)

- Byte-proven: on the **only** UCLK programming path found (ABL1 SetupUclkPll), the
  service argument is the memory word **divided by two** (`LSR #1`, executed and
  emulated). MCLK 1800 → UCLK 900. No consumer of `UclkDiv1M0` (AmdSetup+0x330) has
  been found anywhere in the bounded corpus; nothing conditions the division.
- Byte-proven: FCLK comes from the APCB 015F/0160 override (1420) or the 1200 default,
  and the pstate table tops out at 1750. Default config: FCLK 1420 > UCLK 900 — the
  native help's "FCLK > UCLK" is consistent with the firmware's own init values.
- Byte-proven: the runtime OS selector route cannot touch domains 0x0E–0x12.
- ⇒ Static verdict: **MCLK:UCLK:FCLK = 1:1:1 is not reachable through stock firmware
  on the analyzed paths.** UCLK is structurally MCLK/2 at the only found write site.
  Reaching 1:1 would require patching the ABL1 division (a firmware mod outside the
  stock-BIOS scope) or an unfound second UCLK path.
- Falsifiers: (a) **closed this session** — no `UclkDiv1M0` consumer exists on either
  surface (NVTB token 0x1204: no reader in the extracted corpus; APCB token 21: no
  reader in ABL1, provider called only for 0x0F); (b) a second UCLK programming path
  outside the swept mailbox + closure surface — still open, unbounded only by name;
  (c) units — **closed at the query surface** (§5 hardware run: the SMU's clock
  answers are real MHz/mV across every family, and the DF pstate row values +
  /2 + k-derivation pattern are confirmed by the SMU's own answers; what remains is
  the live FCLK/UCLK/MEMCLK read and the PLL coefficient slots, a measurement gap,
  not a units doubt); the residual "UCLK runs at MCLK anyway" reading stays excluded
  by the byte-proven /2 plus the closed OS route; (d) a different board/BIOS revision
  — **reframed this session**: the board currently runs the donor-derived flashed
  image (v001, readback-verified), so the analyzed chain is the running chain, and
  the four SYNC profiles share the donor bytes outside the NVRAM store (proven by the
  whole-image diff). The board's pre-flash stock BIOS (2.bin) is a **different build** —
  its SMU region (0x8FEF00, 262,400 B) agrees with the donor's at only 39.3% of
  same-offset bytes and the donor SMU body appears nowhere in the dump — so 2.bin's
  own chain semantics are unverified; only its APCB tail row is decoded (§7.3). The
  earlier "all five images agree on the chain semantics" wording was wrong for 2.bin
  and is withdrawn.
- Empirical corroboration: the operator's own 1:1:1 SYNC profiles were structurally
  inert — they edited only the NVRAM Setup store, the boot chain reads APCB only,
  and UCLK = MCLK/2 is hardcoded (§4a). This answers the "why didn't the mods work"
  question without a hardware run.
- Alternative profile direction (separate from the goal, per R3's own rule): the
  **proven forcing path for FCLK is a direct APCB patch** (tokens 0x015F/0x0160 →
  SVC28 0x0E, emulated with the real APCB bytes: 1420→1430 flips the PLL argument).
  The stock-tunable surface is therefore the APCB FCLK value, the DF pstate
  selection, and memory timings — a "half-sync" profile (FCLK set to UCLK = MCLK/2)
  is reachable by APCB patch alone; UCLK = MCLK is not reachable without patching the
  ABL1 division. No numeric recommendation until units are closed, and no recipe per
  the standing rule (no 1800/1800/1800 without a proven forcing path).

## 7. Open consumer edges (remaining R3 work)

Closed this session (see §4a): (1) `MemoryClockSpeed` → context+0x2BC — the consumed
producer is **APCB item 7**, the NVTB token 0x11ED has no reader; (2) `UclkDiv1M0` —
**no consumer on either surface** (falsifier (a) closed); (4) DfClockOverride → APCB
0x015F/0x0160 — **no producer bridge**; the numeric match is a shared build default,
and 2.bin lacks the pair entirely.

Still open:

1. `MemoryPstate` (+0x36D, serialized as 0x123C): **same serialization route as the
   other tokens** — `mov edx,0x123c; mov eax,[ebp-0x8]; mov [eax],dx`, 1 site in each
   of the same 7 modules (verified in the corpus this session; the 20260919 census
   simply did not include 0x123C in its target list, which is why it is absent from
   the 49 sites — the count was a filter artifact, not a different mechanism). It is
   likewise absent from the 4 direct readers → orphan status, consumer unknown
   (ABL/AGESA side). `FclkDpm` (+0x6A3, 0x1331): same status — serialized by all
   7 modules, no direct reader. The serializer total for the clock tokens is thus
   56 sites across 8 IDs (49 census + 7 MemoryPstate), all orphaned at the
   direct-reader level.
2. Units: the PLL coefficient slots `[0x1729c]`/`[0x1792c]`/`[0x17930]` and the VCO
   are still unread (0x2A-readable SMU SRAM class — next hardware run), and no public
   message answered the live FCLK/UCLK/MEMCLK values. The query-surface units question
   itself is closed (§5).
3. The 2.bin (board pre-flash BIOS) APCB layout — **answered at the APCB level this
   session**: its group skeleton matches the donor's exactly (same 6 groups, same
   gids/instances/sizes for UNKN/PSPG/DFG/MEMG/FCHG) except CBSG, which is 44 bytes
   smaller (inst13: 68 vs 72 B / 15 vs 16 rows; inst15: 1768 vs 1808 B / 440 vs 450
   rows; the donor's extra rows are 9 zeros + the override row). Its inst15 **tail
   row is (0, 0, 1000)** vs the donor's (0, 1, 1420) — the same structural override
   slot with **gate byte 0** (disabled) and a 1000 value. Under the donor chain
   semantics that means its boot takes the FCLK default (1200 emulated); but 2.bin
   is a different firmware build (SMU body 39.3% same-offset agreement, donor body
   absent — §6(d)), so its own parser/default is unverified. Moot for the running
   board: it is flashed with the donor-derived v001.

## Evidence

- Pinned body: robin_5 = CLV ROM `0x8FEF00`, 262,400 B,
  SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`.
- Pinned ABL1: `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`,
  SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`;
  donor ROM `ea5781049160ab33...`; board dump `2.bin` `83c4e4205eec3dda...`;
  the four SYNC profiles pinned by full-image SHA-256 in
  `evidence/firmware-audit/20260923-r3-producer-chains/verify_r3b.py` reads.
- `evidence/firmware-audit/20260923-r3-producer-chains/verify_r3b.py` —
  byte-backed assertions for the dead value-table, the service strings, the single
  provider call site, the APCB token values (item7 0x24, token21, 015F/0160), the
  NVRAM-store identification, the profiles' NVRAM-only edits, the corpus reader
  census (4 readers vs 7 targets, 49 serializer sites), the 7 MemoryPstate 0x123C
  serializer sites (56 sites across 8 clock-token IDs total, all reader-orphans),
  the 2.bin CBSG tail row (gate 0, value 1000) and its build-difference from the
  donor (SMU region 39.3% same-offset agreement, donor body absent), and the cited
  emulation results. PASS.
- `evidence/firmware-audit/20260923-abl1-apcb-writer-census/writer-census-result.json`
  (cited; produced by `scripts/abl1_apcb_writer_census.py`), and
  `evidence/firmware-audit/20260923-abl95fc-next/emulation-apcb-result.json` (cited).
- `evidence/firmware-audit/20260919-inv-token-consumers/` — corpus census reused
  (verification.json 517 checks, byte-verified readers/serializers).
- `evidence/firmware-audit/20260923-r3-clock-actuator/df-census-out.txt` — family
  decompiles, DF/row/descriptor hexdumps, 0x171ec ref census, 22D6C closure (49 funcs).
- Domain/selector/row values recomputed from the image and asserted by
  `evidence/firmware-audit/20260923-r3-clock-actuator/verify_r3.py`.
- Prior joins reused: `docs/research/2026-09-23-abl-pll-service-boundary.md` (ABL1
  SVC28, APCB 015F/0160, emulation tables), `docs/research/2026-09-21-smu-domain-selector.md`
  (q3 0x1D path, IPC bounds, domain 0x18 cross-check).
- **Hardware run (read-only queries, 2026-09-23 night, Linux mailbox route)**:
  `evidence/runtime/20260923-234415-probe4l-clockplan.json` (secure 0x2A reads:
  gate already open on v001, core mask 0xFF, domain bitmap 0x00000000, clock-plan
  words A=B=0x0000000E, VCN descriptor window all zeros — EMPTY), and
  `evidence/runtime/20260923-234734-probe4l2-clocks-full.json` (the §5 clock/voltage
  answer table; SMU alive before and after). Partial first battery:
  `evidence/runtime/20260923-234526-probe4l2-clocks.json` (stopped early on a clean
  0xFF rejection misclassified as death — scripts/probe4l2_clocks.py fixed after).
  Probe scripts: `scripts/probe4_linux.py`, `scripts/probe4l2_clocks.py` (board copies
  at ~/vcn_unlock/). Route history: the USB-boot-app phase wedges at ANY SMN/mailbox
  transaction (probe2/probe4 EFI runs, transport-independent — route closed); the
  Linux phase is the proven envelope; 0x2A of hard power-island registers (0x01D80218)
  kills the SMU while the host survives (probe4l run 1).
- Evidence classes: observed-bytes (image reads, decompiles), static-analysis (chains);
  emulation results are synthetic-environment confirmations, not hardware proof;
  probe4l/probe4l2 are live hardware measurements (read-only mailbox queries, no ROM
  write, no state change beyond the queries themselves).
