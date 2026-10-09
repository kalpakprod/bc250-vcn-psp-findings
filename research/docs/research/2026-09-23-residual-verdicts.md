# Residual verdicts: S3, capsule, gasket executor, gitignore audit (2026-09-23)

Static analysis only. No image modified. Sources named per finding. Evidence
classes per `memory/evidence-model.md`.

## Task 1 — AmdPspSmmV2 SwSmiCallBack: NEGATIVE

Already closed in `docs/research/2026-09-23-smm-debug-surface.md` and
`.procoder/plans/vcn-verifier-first.md`. No pre-auth defect: the module never
touches port 0xB2; one SW-SMI registration at `.text+0xc98` → callback `0x54c`
→ `AmdSmmControl->Trigger` → `0x4169` debug stub only after BuildContext
checks; SMM core dispatch is the gate. Residual `SwSmiCmdtoBuildContext` is the
byte at platform-protocol struct `+1`, **printed** by SMM at `0x7ca` and
**read** by `AmdPspDxeV2` at `0x7d8` (`movzx ecx, BYTE PTR [rax+0x1]`); no
installer of that byte found in AmdPspDxeV2/PspDxe/PspPlatform/P2Cmbox
(`mov [reg+1], imm` sites are unrelated 0/1 flags). S3-resume logging only —
cannot reach `0x4169` from a booted OS.

Named next test (only if the numeric is ever needed): decode the
`InstallProtocolInterface` site for the PSP platform protocol and the dword/byte
write at struct `+1`. Not required for the unlock lane.

## Task 2 — PspS3Smm / BootScriptExecutor: verify-before-use on AS3T; boot-script opcodes have no table signature check

Modules: `scratch/smm-debug/ext/modules/0155_PspS3Smm_pe32.bin`,
`0047_BootScriptExecutorDxe_pe32.bin`, `0145_SmmS3SaveState_pe32.bin`,
`0206_S3Resume2Pei_te.bin`.

- **PspS3Smm**: `AmdS3Lib table Signature check fail` LEA at `0x1666`; caller
  `0x1740` does `call 0x1634` then `test eax,eax; jne 0x185f`. `0x185f` is the
  function epilogue (`add rsp,0x20; pop rbx; ret`) — fail **returns without**
  the success tail (`mov word [rcx+rax], 0xffff` at `0x1765`, further resume
  setup). Verdict: AS3T table is verified **before** the callback continues.
- **BootScriptExecutor**: opcode loop at `0x16e0`–`0x1763` (`cmp al,0xff`
  end-marker; IO_WRITE `out dx,ax` at `0x1713`; MEM_WRITE/width variants on
  the `sub ecx,r9d` arms). Whole-module string scan: no `SHA`, `CRC`, `Hash`,
  `verify`, `signature`, `AS3T`, `AmdS3`. `Security Violation` at `0x6730` is
  an EFI_STATUS name in the status-string table (immediate at `0x6a88`), not a
  check. Switch at `0x29ab` is PE/TE section-count bounds during DISPATCH image
  load — structural, not cryptographic.
- **SmmS3SaveState**: `LOCKB_64L`/`LOCKBOXDH` — script persisted via LockBox;
  integrity is lockbox + S3 NVS, not a per-table signature.
- **S3Resume2Pei** (5416 B): no verify-related strings.

Verdict: AS3T path = verify then execute. ACPI boot-script opcodes = execute
with structural image checks only (no table signature). Not an SMM pre-auth
defect by itself; exploitability would require write access to the lockbox/NVS
copy before resume.

## Task 3 — CapsulePei entry + platform capsule PCDs: structural CapP only; no update-policy PCD

Closes the named next test from
`docs/research/2026-09-19-zero-day-confirmation.md` §6.

- **Header**: PI-TE, machine `0x14c` (IA32), `nsec=3`, subsystem `11`
  (BS_DRIVER), `AddressOfEntryPoint=0x240`, `BaseOfCode=0x240`, sections
  `.text@0x240` `.data@0x1780` `.reloc@0x1900` (identity map for `.text`).
- **Entry `0x240`**: `push esi; push [esi+4]; push [esi]; push 0x38;
call 0x15a0` then folds `[ebx+0xa]` into `| 0x80000000` error return — PEI
  thunk, not a verifier.
- **CapP validator `0x8d4`**: `cmp [esi], 'CapP'`; header dword checks at
  `+4/+8/+0xc/+0x10/+0x14`; element walk `lea eax,[esi+edi*8+0x18]` with size
  bounds; helpers `0x11b5` (size/offset join), `0x11d4` (16-byte compare —
  GUID, not hash). Errors `0x8000000A` (bad magic/layout), `0x80000009`
  (bad counts). **No RSA/SHA/PKCS/Auth/Cert** in CapsulePei, CapsuleX64, or
  CapsuleRuntimeDxe (string scan).
- **CapP builder `0xf9f`**: writes `'CapP'` into a local header — format tag,
  not a MAC.
- **Platform PCDs**: full-ROM scan (ASCII + UTF-16): zero `PcdCapsule*`,
  `PcdValidate*`, `PcdSecure*`, `PcdUpdate*`, `Require signature`. Present
  HII/globals are stock EDK2 capsule plumbing: `CapsuleUpdateData`,
  `CapsuleLongModeBuffer`, `CapsuleStatusHob`. `SecurityStubDxe` (5984 B):
  no `Capsule`/`Authenticate`/`Verify` — does not hook this path.

Verdict: unsigned-capsule acceptance path is structurally open in the three
x86 capsule modules (no signature check, no policy PCD). Already-closed
lane-C limit stands: that only writes FV regions already SPI-writable; PSP
still verifies boot components (`$PS1` / type `0x01`/`0x02`). No new
bypass-value.

## Task 4 — SEC_GASKET executor: group dispatch, requester, commit+lock, state prediction

Carrier: PSP type `0x24`, SPI `0x982000`, body `0x2E50`
(`evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`). Payload
`evidence/firmware-audit/ps1/dump-2-sec-gasket-payload.bin` (11344 B,
sha256 `d16f7dac…` in `sec-gasket-summary.json`).

### Framing

```
u32 group_count          // header +0x00 = 5
u32 …                    // +0x04 0x0b510016, +0x08 0x21, +0x0c 0xff, +0x10 2
// from +0x40, repeated:
u32 type; u32 count; count × { u32 address; u32 value }
```

| type  | count | role (policy-chain / VCN-LOCK)                                                 |
| ----- | ----: | ------------------------------------------------------------------------------ |
| 0x201 |  1230 | SMN banks + DF windows + NBIO pre-init; last pair `0x090ab234←1` commit marker |
| 0x203 |    31 | NBIF varA `0x0322xxxx`                                                         |
| 0x210 |    13 | VCN mailbox `0x03E810/0x03E814`                                                |
| 0x280 |   100 | recommit subset (DF + same commit tail as 0x201)                               |
| 0x281 |    31 | NBIF re-mask (`0x0322011c←0x80ff` style)                                       |

### Dispatch (TOS interpreter, corpus + re-check)

- Registry: `fn@0x1167c(type)` @ `0xE5CBDC`; consumers `fn@0xfeac`,
  `fn@0x2178`, `fn@0xa4e4` (`01-psp-policy-chain.md`).
- Sequencer `fn@0x20d4` sets a done-flag and applies via `fn@0x2178` fixed
  order **0x201, 0x205, 0x203, 0x20A, 0x20B, 0x210**. Absent types return
  nonzero from registry and are skipped (stock has no 0x205/0x20A/0x20B).
- `fn@0x2178`: types `0x203`/`0x217` → direct 4-byte write; all others →
  `svc 0x7c(address, value, 4)`.
- `fn@0xfeac` (outside-container / ROM): `0x281` direct; `0x280`/`0x282`/
  `0x284` → `svc 0x7c(…, value, 4)`; other types → `svc 0x7c(…, 0, 4)` zero.
  **No in-container caller of `fn@0xfeac`** — 0x280/0x281 are not applied by
  the in-image sequencer; they are the external recommit lane.

### Requester / commit / lock (HWID 12 VCN bank)

From `VCN-LOCK-MECHANISM.md` (re-checked against payload):

1. `{0x0900C234, 0}` program
2. base masks `0x0900C830–838`
3. requester policy `{0x0900C910, 0x497fff}`, `{0x0900C914, 0x7fff}`
4. eight aperture grants
5. `{0x0900CB80, 0xFF}` lock
6. `{0x0900C234, 1}` commit
7. grp `0x280` tail: program again, clear `914`/`930`, `B80←0` unlock, re-commit

Payload groups **0** writes in `0x0900C000–0x0900CFFF` for current + robin3
(`hwid12_range_write_count=0`); **56** for `historical_unsigned_vcn_candidate`
and `historical_cezanne_dir1`. DF window `0x03A2011C←0x87FF` (bit12 **clear**)
in stock 0x201 and 0x280; `0x03E810←0` in 0x210.

### Predicted internal state

|                              | stock / dump-2 gasket                     | donor-style gasket (56 bank12)            |
| ---------------------------- | ----------------------------------------- | ----------------------------------------- |
| sequencer applies            | 0x201, 0x203, 0x210                       | same + bank12 records if in 0x201         |
| 0x280/0x281 in-container     | **not applied** (no `fn@0xfeac` caller)   | not applied until external ROM step       |
| DF `0x03A2011C` bit12        | **0** (window closed)                     | set in bank12 recipe before lock          |
| VCN bank commit `0x0900C234` | **absent** → stays 0                      | 0→1 after requester+lock                  |
| catalog order                | type `0x24` idx7 before type `0x45` idx15 | same — `0x45` last-writer-wins on overlap |

Stock boot: DF window stays shut, no VCN program/commit → host VCN still
all-ones. That matches the 2026-09-12 campaign result without needing a new
hardware run.

## Task 5 — git check-ignore matrix + self-containedness

Command: `git check-ignore -v --no-index --stdin` over every
`evidence|scratch|candidates|import|tools/…` path cited in 862 tracked MDs
(`docs/`, `memory/`, `specs/`), 1221 unique citations.

| bucket                                                             |                                   count |
| ------------------------------------------------------------------ | --------------------------------------: |
| ignored (non-negated)                                              |                                    1161 |
| negated whitelist (matched but kept)                               |                                      12 |
| path exists on disk                                                |                                    1126 |
| exists **and** ignored                                             |                                    1085 |
| exists, not ignored                                                |                                      29 |
| ignored but already `git ls-files` tracked                         | 25 (all under `evidence/smu-ipc-d-r1/`) |
| missing on disk after filtering prose fragments / truncated tokens |                                     ~62 |

Ignored by topdir: `evidence` 1000, `import` 87, `candidates` 64, `tools` 10.
Dominant rules: `.gitignore:35` `/evidence/*`, `:37`
`/evidence/firmware-audit/*`, `:47` `/import/`, `:52`
`/candidates/**/*.bin`. Whitelist (`!`) still active:
`evidence/firmware-audit/20260919-zd/*.txt`, `gasket-script-crossversion.json`
(12 hits) — those files show as `??` untracked, not ignored.

### Self-containedness (key research docs)

| doc                                       | inline sha256 |          cites into ignored |                missing | verdict                                                         |
| ----------------------------------------- | ------------: | --------------------------: | ---------------------: | --------------------------------------------------------------- |
| `2026-09-23-smm-debug-surface.md`         |             1 |               1 (donor ROM) |                      0 | OK — module paths + offsets local                               |
| `2026-09-19-gasket-script-decode.md`      |             0 | 1 (`VCN-LOCK-MECHANISM.md`) |                      0 | OK — body states every claim re-checked against ROM bytes       |
| `2026-09-19-zero-day-confirmation.md`     |             6 |                           5 |                      0 | OK — hashes inline for the decisive images                      |
| `2026-09-12-bios-vuln-inventory.md`       |             0 |                           0 | 2 (`tools/list` prose) | OK — table is the content                                       |
| `2026-09-12-unlock-paths-map.md`          |             0 |                           0 |                      0 | OK — no path cites                                              |
| `2026-09-23-verifier-destination-hunt.md` |             1 |                           7 |                      0 | Weak — worker artifacts ignored; relies on narrative + one hash |

Missing ~62: mostly action-log ephemera (`run-20260921T…`, `verifier.exit`),
regex truncation (`evidence/firmware-audit/20260921-`), and prose fragments
(`evidence/docs/memory`). Not cite-bugs in the research docs above.

**Conclusion:** ignore policy is intentional (binary dumps stay out of git).
Cited-but-ignored is normal for this repo. Research docs that carry claims
either inline hashes or re-state the byte checks; no fix required for tasks
1–4 inputs. Optional hygiene: stop citing per-run scratch paths in
action-logs, or whitelist the few JSON reports that reviews actually need.
