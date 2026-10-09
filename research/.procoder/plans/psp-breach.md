# PSP breach plan (BC-250, no soldering)

## Operator clarification 2026-09-27: one-time trust transition

The desired end state is one autonomous modified BIOS, potentially after using the operator's BC-250 and Waveshare once to cross the PSP trust boundary. This is not satisfied by a volatile runtime bypass that must be repeated at every boot. Hypothesis under evaluation: one-time PSP access could yield a persistent boot-accepted trust change or a reusable in-image bypass. Neither has been demonstrated. The observed plan's on-die ROM hash anchor over raw type-0x09 root material is not changed by replacing a signature or key in RAM; no writable persistent trust-anchor path is established. A boot-time TOCTOU rig must currently be assumed necessary on each cold boot for a custom-signed PSP chain, unless a separate persistent mechanism is proved. The in-image unsigned DXE/SMU lane is a different route to a self-contained BIOS and is not proof of PSP custom-signature acceptance. No cut, solder, lifted pin, rig hookup or flash action is approved by this consultation.

Operator priority, 2026-09-27: the target is the complete standalone firmware image, not a passive SPI trace as the main deliverable. The whole-repository audit and Understand Anything integration are means to close knowledge gaps before choosing the next firmware acceptance experiment. Do not substitute tool-generated summaries for byte evidence, successful build for boot, or an incomplete coverage index for a completed audit.

Operator correction, 2026-09-27: BIOS flashing through J4004 has already worked for him. Treat J4004 as a proven programmer route by operator report, with exact transcript and current wiring still unlocated in the project record. This resolves access to the flash while power is off. It does not resolve live boot-time substitution: the onboard flash and header share CS/data nets, so the v001 plan still needs a separately demonstrated way to avoid competing outputs. Do not ask the operator to cut or lift a pin merely to repeat an already solved programming step.

Audit continuity note, 2026-09-27: much of the candidate table below was written 2026-09-23 and is not the current flash queue. Later logs show v003c and v003e failed to boot (`docs/action-logs/2026-09-24-v003b-route-b.md`), and 2026-09-26 PSP/GASKET experiments failed and stock P3.00 was restored (`docs/action-logs/2026-09-26-psp-full-audit.md`, `2026-09-26-gasket-spoof-failed-analysis.md`). The 2026-09-26 DXE v002 report ends awaiting the programmer, not a verified VCN boot. Resolve the conflicting type-0x09/root-key descriptions before treating a custom PSP signature as a product path. No image in this plan is declared a completed autonomous VCN firmware by its build, write-verify, or old queue status alone.

Type-0x09 correction, 2026-09-27: on the exact restored stock P3.00 image, directory parsing locates this 0x440-byte body at `0x93F200`, not the CLV-specific `0x93F000`. Direct byte checks show raw RSA-key structure (version 1, known kid, e=65537, 2048-bit LE modulus); KDB carriers 0x50/0x51 reference that kid. The 2026-09-26 audit's "encrypted PSP L2 pointer" interpretation applied `$PS1` header offsets to a non-`$PS1` record and is withdrawn. This resolves record structure, **not** the on-die ROM anchoring or acceptance of our key on cold boot. Evidence: `docs/research/2026-09-27-autonomous-firmware-gaps.md` G2.

Created 2026-09-23 after the operator's order ("патчинг, обход, RSA, взлом — всё это нужно").
Skills used: lateral (drunk mode), universal-critical-thinking (this spine), rsa-attack-techniques
(audit executed). Supersedes no plan; runs alongside `vcn-verifier-first.md`, which stays the
methodology anchor for lane V2.

Route: Full. Mostly two-way doors (offline builds), hardware rungs are programmer-reversible
(three full flash cycles proven). Domain: Complex — cheapest experiment that discriminates wins.

## Frame

Goal: a bootable BIOS on BC250-01 with VCN unlocked. Crux: the trust root is a hash anchor in
on-die PSP ROM over the raw type-0x09 key blob (kid `ffc8acd4`, SPI `0x93F000`, 0x440 B, no
`$PS1` envelope, no signature) — found 2026-09-23. Everything below (KDB carriers `0x50/0x51`
-> leaf keys -> `0x24`/`0x45` locks) is transitive signatures we can verify and rebuild but
cannot sign. Good enough: one demonstrated bootable unlock; not good enough: claims without a
boot observation.

## MECE attack surface

| Lane | Idea | Status tonight | Next |
|---|---|---|---|
| V1 forge RSA-2048 | break the math | CLOSED with own evidence: 10 moduli, no shared factors, no Wiener, no tiny factors (`evidence/firmware-audit/20260923-psp-root-swap/manual-rsa-audit.json`) | none |
| V2 verifier bug | implementation bug in native verify | LEANING ROM: op1005 consumer absent from image; reject plumbing (`115B8`->`EEAE`->`0x34`) enforced, no accept-on-error path; `$PS1` sizes trusted with align/min checks only (worker A report) | dead unless runtime ROM dump or emu appears |
| V2b type-0x44 tail | container signs 0x10 B, carries 0x6400 B UNSIGNED tail (`0x9C4400`) | UPGRADED (worker verdict, `2026-09-23-type44-tail-consumer.md`): the tail is NOT padding — it holds TWO ~0x3200 B SMU-style CODE blobs with unsigned sub-`$PS1` headers (`0x9C4620`/`0x9C7820`, code at +0xF0, shared 16-B id, tokens `0x0101101D`/`0x0101101E`); the SIGNED 0x10-B table maps workload ids → exact code offsets (`0x101D:0x210`, `0x101E:0x3410`); consumer = on-die ROM (zero references in the image) | UNRESOLVED leaning TRUSTS-TAIL: if the ROM executes code at those offsets, this is pre-auth unsigned code exec BY CONSTRUCTION; next: decode the blob headers' fields + design a tail-swap discriminator candidate (kept OUT of the first flash pair — outcome would be ambiguous) |
| V3 root swap | replace modulus in raw `0x09` | RUNG 1 BUILT: `candidates/BC250_5.00_clv_ROOTKEY-swap-0x09_v001.bin` sha256 `46ec00bbcda7a4d0e6fbe6b9a39457395b573f8667141919e58e7f146ca8ecbf`, 256 B changed, kid/e/tail untouched | operator flash approval -> boot reads the anchor question directly |
| V4 lock absence | remove `0x24`/`0x45` from `$PSP` dir | RUNG BUILT: `candidates/BC250_5.00_clv_PSP-entry-absence_0x24-0x45_v001.bin` sha256 `02d6e33f3c8a99db27a003b1da8d093163ad4583181e958a5cda214c19e3127c` | operator flash approval -> reads whether lock defaults exist |
| V5 SMU 2nd core | ZD-1 code exec + direct `func_0x1b514` calls into window `0x5B000..0x5B7FF` | UPGRADED (external PoC hunt, `2026-09-23-external-poc-hunt.md`): our ZD-1 (Q2 `0x23`) is PUBLICLY exploited on BIOS 3 (`rw-r-r-0644/bc250-smu-unlock`: overflow -> secure-access unlock -> arb SMU r/w + CODE EXEC); BIOS 5 offsets = ours (robin_5 decoded). Community VCN state: power domain 6 ON via `FUN_00023b14(6,1)`; blocker = second gate (clock/reset/isolation, slots 0x16/0x17/0x18, `FUN_00024764`) — all inside OUR body | offline: find the secure-access gate in robin_5 + port patches.hex format; runtime: staged gate-clearing through SMU-internal calls (per operator steering, keep BIOS-baked as primary and this as the session payload) |
| V6 S3 script | unsigned AMI S3 script executes MMIO at resume; lock may re-open at wake | CLOSED-NEGATIVE (2026-09-23, root): no S3-script persistence markers exist in the image (no `MemBootScript`/`BootScript`/`S3SS` UTF-16 or ASCII; `S3PT` appears once inside BootScriptExecutorDxe at `0xECF3E4`) -> the script is rebuilt into RAM each boot, not read from NVRAM; AMD's own S3 table is signature-checked (`PspS3Smm`: "AmdS3Lib table Signature check fail"); and even a forged script could only replay MMIO writes already proven insufficient for the bridge (C3) | dead; root-on-board S3 persistence is NOT a lane here |
| V7' SPI TOCTOU (NEW PRIMARY, 2026-09-23) | Pico 2 dual-flash on the SPI bus: PSP reads every module body TWICE; feed patched KDB/key on read 1, original on read 2 | PROVEN ON THIS BOARD by PT (Habr 979470, CCC 2025 "Opening pAMDora's box"): Fedora booted with re-signed TRUSTED_OS — key 39BF spoofed, our exact signing scheme; `91de01eb…` IS the patched dump for this attack; PSP code exec + privilege escalation (SVC 0xF2/0xF3) + PSP ROM dumped via CCP DMA (matches 4700S bootrom). SERVE MAP BUILT (`scripts/build_toctou_serve_map.py`, `evidence/firmware-audit/20260923-toctou-serve-map/`): 6 changed ranges / 14,442 B total; the ONLY root-signature TOCTOU window = the t50 key entry `0x9DB560..0x9DB6A0` (320 B): serve ORIGINAL while the root verifies the KDB records, PATCHED while the rebuilt gasket (signed by our key) is verified | build the rig (no solder: SOIC-8 clip + Pico 2; doubles as sniffer/programmer/debug), flash the Pico with the serve map, session on operator go |
| V7 EMFI | coil over PSP die during the `0x09` hash check | FALLBACK now: the TOCTOU lane needs no fault injection; revisit only if the rig shows anti-TOCTOU behavior | parked |
| V8 recovery/PSP mailbox | recovery path or SMM mailbox commands accept more than the main path | UNTOUCHED tonight | low priority, after V6 |
| V9 SMU forged-record MMIO | ZD-1 ring overflow (Q2 `0x23`) -> forged transfer records -> applier `FUN_0002D4E0` executes attacker-chosen masked 32-bit write anywhere in MMIO (PSP APB `0x02B1xxxx` reachable: `0x16C00000+0xEB3FFE00+0x200=0x02000000`) | PRIMITIVE PROVEN-STATIC (worker, `2026-09-23-smu-chain-development.md`): SMU code-exec = NO (data-only, zero CALL/JUMP refs into `0x188A0-0x1A5D0`); SMU->PSP C2P dedicated sender = NO. Staging plan BUILT and image-verified: 120 appends, forged record -> q0 table `0x18E20` at #88, count flip `0x1901C=1` at #119 (`scripts/smu_forged_record_plan.py`, `evidence/firmware-audit/20260923-smu-forged-record-plan/plan-result.json`) | RUNTIME — PARKED per operator steering 2026-09-23: runtime-only unlock contradicts field experience; keep only as an optional diagnostic probe (PSP_APB_PROBE) if the board is up during an instrumented session |
| V11 BIOS-5 port of the public SMU unlock (IN-IMAGE PRODUCT CORE) | One flashable image: our proven unsigned DXE carrier -> mailbox (PCI `0xB8/0xBC`) -> Q2 `0x23` record-engine (`FUN_0002D620`) count-walk overflow -> clear gate -> VCN payload `FUN_00023B14(6,1)` + second-gate slots `0x16/0x17/0x18`. No extra hardware: operator verdict 2026-09-23 — людям даём «прошил BIOS — VCN работает»; Pico/EMFI TOCTOU -> archive only | PORT DECODED (`docs/research/2026-09-23-bios5-gate-port.md`, decompile outputs `evidence/firmware-audit/20260923-bios5-gate-port/`): (1) secure gate for the whole `q2_0x0A` class = **bit 9 of u32 at `0x032000E8`** (guard `FUN_0002A018` = plain bit test; BIOS-3 analog = DBG_DISABLE `0x7B3C`); (2) Q2 `0x23` handler = record engine `FUN_0002D620`: instance array `0x188A0`, stride `0x794`, sub-regions `0x1E` records × 0x10, count byte at `+0x780` unbounded vs region -> count-walk to `0xFF`; inst-1 walk covers `0x196B0..0x19EA4` incl. dispatcher state `0x197D0/0x197E0/0x197E4`; (3) record consumer is reachable ONLY via literals `0x181B0 -> 0x188A0`, `0x181A4 -> 0x18FB4` (no other xrefs) -> forging = overwrite the literal; (4) Q3 `0x23` (`FUN_0001BBC0`) dispatches via a function-pointer table (`+0x44`, 0x24 stride) gated by permission bits (`+0x54`) — second code-exec candidate | OFFLINE decode RESOLVED 2026-09-23 (port doc §7-8): the second gate needs NO exploit — the community DXE driver exposed host SMN read/write via the `0xB8/0xBC` config pair, and robin_5 carries an UNGUARDED mailbox pair `q3_0x28` (store SMN address @ `0x8B08`) + `q3_0x29` (write value through it) = arbitrary 32-bit SMN write; `q3_0x1A(6,1)` = VCN domain power (thelamer-proven), `q3_0x87` = clock program; V9 applier windows proven only 4 MiB (bound `w0<=0x1FFFFF`, script corrected). Product = DXE + mailbox messages ONLY; worker runbook LANDED (`docs/runbooks/2026-09-23-vcn-mailbox-sequence-DRAFT.md`): shortest path = **q3 0x1B** (direct full power-up incl. clock program; 0x1A = state-machine twin), domain-permission bit 6 @ `0x0000CCB8` resolved by our own 0x28/0x29 write pair (no "canonical" message needed), clock-plan population = runtime check (O6) with donor-value fallback | DRIVER FILLED + EMULATION-COMPLETE 2026-09-23: full q3 0x1B body executed in Ghidra emulation (8865 steps, RET_MAGIC); O6 RESOLVED NEGATIVELY (empty clock plan hangs SMU in FUN_00024594 tail poll → donor fill MANDATORY, guard in driver aborts cleanly); driver `Bc250VcnUnlockDxe.ffs` built+static-verified (8066400b, guid b6250780); read-only donor-plan probe `Bc250VcnProbe2.efi` built (2ee54e86) — UEFI Shell, zero writes, output = donor plan; **CANDIDATE v002 BUILT on drivers-only base** `BC250_5.00_clv_MeiMeiDXEv3-drivers-only_vcn_v002.bin` (1b0dfd0f; 194 files, PSP byte-identical, changes in capsule only); v001 (56c1b089, on af531026) = WRONG-BASE, discarded (MISTAKES.md rule: base from plan, never "last working") | NEXT: operator runs Probe2 from USB → donor plan → bake into driver constant → rebuild → re-inject; THEN flash session (explicit approval + recovery dump + readback). Base RESOLVED: FD's own image re-acquired from the live Forbidden-Darkness repo (606a7a7f, preserved in evidence/donor/fd-v22-20260923/); **v003 = the VCN driver on the FD community base** (`BC250_3.00_MeiMeiDXEv3_vcn_v003.bin`, 0fafe2c1; PSP byte-identical, changes in capsule only); v002 (drivers-only, 1b0dfd0f) = fallback |

## Analysis (base rate -> update)

Implementation bugs in vendor boot verifiers are historically common (a large share of
published PSP/ABL/PE advisories are parse/verify implementation bugs, not math), so V2b/V2
keep priority despite V2 leaning ROM. Absence-default-unlocked (V4) is the long shot: the
platform programs explicit zeros ("явный ноль = главный kill"), which argues defaults are
unsafe; base rate ~15%, low confidence. V5 inherits the strongest prior: every element of the
runtime bring-up chain is hardware-proven except this one window. Batch the two flash rungs
(V3+V4) into one sitting to amortize operator cost — they are independent discriminators.
V9 changes the endgame arithmetic: it is a RUNTIME, flashless, reboot-reversible primitive
(no image, no glitch, no solder) whose only gate is a booting board — re-ranked by the
operator's steering below (runtime-only closed by field experience).

## New lanes from the 2026-09-23 inversion pass (operator: «какие пути мы ещё не делали»)

| V12 PSP ROM acquisition (KEY TO ALL OFFLINE QUESTIONS) | The KDB-walk / verifier lives in on-die ROM (unread); PT (Habr 979470) dumped it via CCP-DMA-after-reset (public recipe, SomnacinDumper); their commenters hold the 4700S-family dump | anonpsp/bootroms = Zen/Zen2 only (checked 2026-09-23, NOT our family); SomnacinDumper repo = payloads+PicoModchip, no dump; CCC fahrplan slides / media.ccc.de talk / Positive Labs telegram = unmined sources | MINED 2026-09-23 (`docs/research/2026-09-23-v12-pamdora-ccc-mining.md`, transcript preserved `evidence/donor/ccc-39c3-20260923/`): tihmstar 39C3 talk = full ROM-dump recipe (early code exec -> chained CCP DMA with delay transfer -> CPU self-reset via brute-forced MMIO reg -> board reset, SRAM survives -> second boot streams SRAM out; strip 30-byte per-board tail); their ROM IS dumped (not published); TOCTOU production exploit = ONE Pico, ONE lifted pin (CS proxy) - simplifies our V7' rig; ROM contents: fuse-decided NO-SIG alt boot path ("test mode"), banked-register boot-to-0 bug (no non-watchdog FIQ trigger known), I2C boot-trigger chip (A0/A4/A8 -> boot addr FF821000); NEW lane to decode: swap Secure OS body in our own PSP dir (fletcher-only) for PSP EL1 without any rig | board-side: check for the I2C chip + V13 still gated on OUR ROM semantics. V14 (Secure-OS body swap, no rig) DECODED+CLOSED-NEGATIVE same day (`docs/research/2026-09-23-v12-pamdora-ccc-mining.md` §V14): all loadable bodies = signed $PS1 (14/14 PASS, kid 5a3587b5 owns 0x02+0x28, 663ca522 owns ABLs), dir-rebuild can't escape body signatures (C1 root); non-containers 0x01 (encrypted OCB)/0x09 (root key)/0x4F (AMD pubkeys) = no payload slot; the talk's route needs the V7' TOCTOU rig by construction |
| V13 KDB-carrier union + 4700S SMU-fw swap | PSP dir is NOT signed (fletcher only, we already rebuild it); 0x50 AND 0x51 carriers coexist, both container-signed by the SAME external kid `ffc8acd4`; `9ace85d9` is a key held by BOTH carriers on both platforms → if the PSP unions carriers, a third (4700S) carrier delivers the 4700S SMU-fw leaf `b6f9ac22` with a fully valid chain | CHECKED 2026-09-23: naive 4700S SMU swap = `kid-not-in-KDB` (dead); BC250/4700S key sets nearly disjoint (7 vs 5 platform-only); downgrade dead (0x24/0x45 byte-identical across 2.00/3.00/5.00) | DECIDABLE ONLY WITH ROM SEMANTICS (V12). If union: hybrid = BC250 base + 4700S 0x50 carrier as a new dir entry + 4700S type-0x8 body — pure BIOS patch, valid AMD signatures, no exploit |
| Dead classes (evidence-pinned) | RSA forgery/brute-force: 11 records, RSA-2048, e=65537, no shared factors, no Wiener/Fermat (`kdb-rsa-weakness-audit-clv500.json`); unauthenticated carriers: none (all 19 have signature tails); desktop Ryzen TOCTOU: not vulnerable (Quad mode, single reads) | closed | — |

## New lane from external hunt: V10 encrypted-PSP-FW ROM bug (CVE-2021-26315)

BIOS-baked, GLITCH-FREE PSP code-exec candidate: the PSP boot ROM insufficiently
verifies the integrity of a DECRYPTED encrypted firmware image (AMD SB-1021). If the
5.00 CLV image ships encrypted PSP FW (KDB type `0x01` entries exist) and the BC250 ROM
revision predates the fix, a malformed encrypted blob = arbitrary PSP code exec with no
EMFI. Next: focused session on the type-0x01 entries (decrypt/parse chain in the ROM
disassembly we already hold). See `docs/research/2026-09-23-external-poc-hunt.md` (T3).

## Operator steering (2026-09-23, after V9 report)

"На уровне системы у тебя ничего не получится. Мы уже пробовали, нет лока на уровне
системы. Это всё должно быть зашито в BIOS — патченный BIOS с глитчем, со спуфом, и
только тогда можно писать в систему." Meaning: the lock is boot-time, not a runtime
state; runtime/system-level unlock attempts were already tried in the field and failed
(consistent with the C3 closure: the runtime path needs SMU-side PowerUpVcn, which is
NULL on BC250, or the PSP release block). Therefore the deliverable is a patched BIOS
that pairs with the glitch — spoofed key + re-signed image + rebuilt lock carriers —
and EMFI is the remaining gate. Consequences: V7 promoted to PRIMARY; V3/V4 stay as
optional cheap discriminators inside the same flash session; V9/V5 PARKED (runtime
lanes contradict the operator's field data; V9 keeps value only as a diagnostic probe
if the board is up and the session is instrumented).

## Donor 4700S diff (2026-09-23, `2026-09-23-donor-4700s-vcn.md`)

The working-VCN relative ships NO `0x24`/`0x45` carriers; the generic blobs (`0x44`,
`0x4F`) are byte-identical to ours; our decoded robin_5 body == the BC250 type-`0x8`
$PS1 body verbatim; the Cezanne-derived unlock values (header 6 + `0x2544C382`) are
already half-present in BC250's own stock carriers. Net: the BIOS-side VCN difference
is exactly the two lock carriers the glitch-signed image already replaces — no new
copy-paste donor material exists in the 4700S. O5 of `vcn-unexpected-unlock` resolves:
the difference is the locks' absence, not a hidden working-chain procedure to lift.

## Premortem

It is a year later and this failed. Why: (1) every flash rung parked and no observation
channel existed to localize which check failed — mitigation: the standing instrument-first
rule (J5 UART) applies BEFORE the first rung, not after the second dead board; (2) rung
interpretation ambiguity (the 0x09 tail 64 B field is unknown — a park could be a tail check,
not the ROM hash) — mitigation: V3 rung 1 outcome "park" closes the whole root-swap ladder
regardless of which check inside it fired, and that is an acceptable answer; (3) type-0x44
tail consumer turns out to trust nothing — acceptable, one lane dies.

## Commit

Recommendation: run V2b (offline, now), V5 (runbook draft now, execute on go), and stage the
V3+V4 flash pair for one operator session with UART instrumented; accept that V1 is dead and
V2 is ROM-bound unless a ROM dump appears.

First actions: (1) V2b consumer hunt — me, today; (2) V5 runbook draft — me, next session;
(3) V3/V4 flash decision — operator, one session, exact hashes above.

Kill criteria: V2b — no consumer found trusting the tail after the t28 dispatch is decoded
(the tail may be decoy/padding); V3 — board parks on boot (ladder dead, EMFI target
confirmed); V4 — board boots with VCN still gated (defaults lock; absence lane dead); V5 —
the second-core window answers with the same all-ones arbiter (runtime lane joins C3);
V7 — after ~200 EMFI shots across the delay/duration window without a state change, stop and
re-target.

Open question that flips the ranking: does a UART/POST observation channel exist for BC250-01
(J5 pad location)? A yes reorders V3/V4 ahead of everything.

## Finish line (2026-09-23, operator's articulation)

The mission ends with a public writeup: "the BC-250 platform is fully reverse-engineered and
broken — custom drivers, VCN, OC all under our control." Checkable criteria:

1. F1 signature story: the PSP trust chain mapped to its root AND the root's behavior
   demonstrated on hardware (V3/V4 outcomes or EMFI), i.e. we can state exactly what the
   platform accepts and why.
2. F2 VCN working: a bootable image with VCN up (`vainfo` shows encode+decode, one real
   codec run) — or the hardware-proven statement of what holds it closed.
3. F3 custom code: unsigned DXE injection booting (ALREADY PROVEN: MeiMei/W11 lineage,
   8-core unlock live) + kernel side complete (mode0/1/2 kernels exist and boot).
4. F4 platform map: PSP region 19/19 entries named (DONE); SMU 147-handler table decoded
   (DONE), second-core window resolved (V5 pending); ABL0-4 decoded (PARTIAL); the on-die
   PSP ROM and the fuses are documented as the platform's only unread surfaces, with the
   exact reason (no dump channel) — a boundary named is a result, not a failure.
5. F5 the package: community writeup + tools + reproduction steps, hashes pinned.

Current state (UPDATE 2026-09-23, operator correction): the product is ONE FLASHABLE
IMAGE — «прошил BIOS — VCN работает», no extra hardware for end users; the Pico/EMFI
TOCTOU rig is archived (fallback only). Primary = V11: our proven unsigned DXE carrier +
mailbox + Q2 `0x23` count-walk overflow + gate bit 9 @ `0x032000E8` + VCN payload
(`FUN_00023B14(6,1)` + slots 0x16/0x17/0x18). Port decode: gate/overflow geometry DONE
(`docs/research/2026-09-23-bios5-gate-port.md`); open = how to flip literal `0x181B0`
(record-consumer pointer, sole xref to the tables) or the Q3 function-pointer path.
F-state: F3 ~90%, F4 ~80% (PSP ROM readable per Habr/PT method), F1 path now fully
in-image (no rig dependency), F2 blocked on V11 payload decode, F5 80% (community writeup
`docs/research/2026-09-23-bc250-platform-complete-writeup.md` drafted covering F1-F5,
candidate v003 staged in `firmware-flash-pkg/20260923-v003-community-vcn/`, sha256 `0fafe2c1…`,
runbook `docs/guides/bc250-v003-community-vcn-programmer-flash-runbook.md` complete).
V10 status: checked 2026-09-23 — BC250 type-0x1 entry (IPL, 46,592 B) is the ONLY
encrypted PSP blob (no `$PS1` magic, high-entropy body); 0x2/0x8/0x12/0x28/0x30 carry
plain `$PS1`. CVE-2021-26315 therefore has exactly one local target (the IPL decrypt
path) — kept as a research lane, not the product path.

## Re-ranking 2026-09-23 (operator-confirmed): v003-class first, deletion demoted

The operator challenged the deletion-first ranking («как тебе твоё решение
удалить») and ordered the lateral skill. Assumption inversion was run on the
deletion decision; the operator confirmed the corrected ranking in chat
(«подтверждаю») the same day.

Inversion verdict on the deletion lane:

1. "Absence = neutral" contradicts the platform's own explicit-zeros habit;
   the plan's base rate for absence-default-unlocked stays ~15%.
2. The 4700S donor diff is a symptom of a different SKU policy, not causal
   proof of transfer: absence on the donor was never an edit.
3. Deletion spends the UNPROVEN surface (the unsigned $PSP directory) on an
   unpredictable bet; the driver lane spends PROVEN surfaces (unsigned DXE
   injection boots, mailbox writes accepted) and leaves one unknown.
4. v004 (absence + driver) violates the plan's own single-variable
   discipline: a park could not be attributed. Same reason the tail-swap
   stayed out of the first flash pair.
5. Survived inversion unchanged: the lock is decided at boot and is
   unreachable from the OS (dom14 hardware denial, 5 runtime experiments +
   the D3-A flash). A law, not an assumption.

CONFIRMED RANKING (supersedes the chat lineup that named the combined v004
«primary target»; the V11 row's NEXT sequence below stands unchanged and is
now the only queue):

1. Product and first rung: v003-class — the V11 driver on the FD community
   base, zero PSP-byte changes, zero deletions
   (`BC250_3.00_MeiMeiDXEv3_vcn_v003.bin`, `0fafe2c1` lineage; the 3.00 FD
   base family is boot-proven on this board). Single unknown: boot-time
   mailbox acceptance.
2. v005 (pure absence on the 3.00 base, `28cc548d`) — optional
   single-variable walker-semantics question, low prior; after or never.
   The older clv-base V4 rung (`02d6e33f`) stays parked: the clv lineage's
   only flashed image died at P0.
3. v004 (combined monolith, absence + autonomous driver, `2981b252`) —
   WITHDRAWN from the flash queue. Package
   `firmware-flash-pkg/20260923-v004-combined-o3/` and its runbook are
   retained as provenance only; not for flashing.

Sequence for the v003 rung (the V11 NEXT, now the only queue): probe3
reads the donor clock plan at boot -> bake into the driver constant ->
rebuild -> re-inject -> flash the rebuilt v003b with exact approval, full
dump, readback.

Probe route update 2026-09-23 (evening): no UEFI Shell exists in either
image (stock read-a 83c4e420: 188 files; community 606a7a7f: 193 files, no
nested FVs), so the Shell+startup.nsh route is impossible and the
Shell-launched Bc250VcnProbe2 is superseded for the operator loop by
Bc250VcnProbe3 (`c281d5d8…`): a self-contained boot app
(`\EFI\BOOT\BOOTX64.EFI`) that reads the same read-only register set,
writes `probe2-out.txt` to the FAT32 stick carrying the `PROBE2.TXT`
marker, then reboots the board back to Linux. Staged:
`firmware-flash-pkg/20260923-probe2-usb/` + `scripts/probe2.sh` (push /
fetch-with-timer). Per run the operator does only: reboot + ONE-TIME USB
boot pick (never a boot-order change: probe -> reset -> USB would loop).
Live run pending: the operator's 32 GB stick did not enumerate on the
board (only the Ugreen dual-bay and the keyboard hub visible; buses 1-5
empty) nor on the agent host (empty card reader only); waiting for a
re-plug into a working port before `push`.

Board-state correction 2026-09-23 evening (live-verified, retracts the revive
step this section carried earlier today): the "chip currently holds af531026,
P0 fail" line was built on the Sep-17 commits (66b9c92 04:57 flash, d83c041
05:03 P0) and was six days stale. Live check: BC250-01 host UP (ping
127.0.0.1 0% loss; SSH ok; booted 2026-09-23 09:25:46, kernel
7.2.6-1.206-cachyos-bc250); dmidecode reports BIOS `P3.00 12/09/2021` on
chip — af531026 is NOT on the chip. Memory project-state.md already recorded
the board UP on P3.00 on 2026-09-21 (operator's empirical OC track). No
revive flash exists; the first flash of this queue is the rebuilt v003b
itself. Chip-image variant (stock read-a vs MeiMeiDXEv3 3.00 family)
unverified; not blocking — Probe2 and the v003b flash both overwrite it.

Driver-identity verification 2026-09-23 (supersedes the pre-bake ban written
earlier today): the staged `20260923-v003-community-vcn` package carries the
GUARD driver — proven by extraction from the image itself, not from the
manifest: the in-image FFS (inner FV off 0x432000, 194 files, state byte
0xF8, whole-file sha256 `0a4c997b…`) is byte-equal to prep_blob of the
preserved guard ffs `8066400b…` (`bin/Bc250VcnUnlockDxe.ffs.draft-o6`); the
autonomous rebuild (`b9b6f8d3` raw / `da2f70cc` normalized) went only into
withdrawn v004. The guard aborts cleanly on the empty clock plan
(emulation-validated O6: an empty plan would hang SMU; the guard prevents
the send), so a pre-bake flash of the staged package is boot-safe and
behaves as the bare community base; it does NOT unlock — the unlock rung
remains Probe2 -> bake -> rebuild. Revive-image choice (staged v003 vs
bare base `606a7a7f`) and all flash-sequence decisions remain the operator's.

No deletion enters the product path. Flash-sequence decisions remain the
operator's.

## Local boardview correction — 2026-09-27
User pointed to boardview in current repository. Read evidence/hardware/ASRock AMD BC-250_ISL_X5R r1.00.cad directly. SHA256 decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8 equals prior source CAD hash. Raw lines 65425-65428 identify BIOS_A1 flash and BIOS_S_A1 socket; 72752-72757 confirm shared CS. CAD socket entry establishes design footprint, not actual population. Do not classify socket as unpopulated without physical evidence. No new boardview request needed.
