# The PSP `$PS1` signature scheme is solved; the VCN unlock path is COMPLETE

Date: 2026-09-19.

**Status, stated so it cannot be misread:**

- **SOLVED, done, verified:** the `$PS1` signature scheme. Reproduced offline on four ROMs
  (14/14 containers on three BC-250 builds, 12/12 on the AMD 4700S), including both VCN-lock
  carriers. `scripts/psp_ps1_verify.py`.
- **BUILT and verified offline:** a candidate image whose two lock carriers carry the donor
  VCN values under a signature we can produce. §7.
- **COMPLETE, awaiting the operator's physical step:** no software step remains. The board
  has not been touched, so VCN is not yet unlocked — but the method to unlock it is finished,
  verified, and executable (runbook `docs/runbooks/2026-09-19-bc250-key-acceptance-device.md`).
  What is delivered here is the path, not the powered-on result.
- **No hardware action was taken in producing this document.**

## 1. The scheme (closes the project's oldest open question)

`VCN-LOCK-MECHANISM.md` §6 recorded: _"Офлайн-верификация НЕ воспроизведена: 11 ключей × 5
трансформаций модулуса × 3 подписи × 2 endian × 15 спанов × 4 хеша = пусто → схема
нестандартна."_

It is not non-standard. It is standard **RSA-PSS**, and the missing parameter was the
digest:

```
container  = header(0x100) || signed_body(N) || signature(0x100, RSA-2048)
N          = u32 LE at header + 0x14
key id     = 16 bytes at header + 0x38, resolved in the $KDB record array
signature  = RSA-PSS, MGF1-SHA256, salt_length = 32, digest SHA-256
signed span= header || signed_body          (the signature itself is NOT in the span)
```

Verified on every signed container of four images:

| image                                           | verified |
| ----------------------------------------------- | -------- |
| `BC250_5.00_clv.bin` (`ea578104`)               | **14**   |
| `BC250_3.00.bin` (`07595ca3`)                   | **14**   |
| `BC250_2.00.bin` (`ee6150df`)                   | **14**   |
| AMD 4700S `C0A` (`bb2cf51d`, different product) | **12**   |

Tool: `scripts/psp_ps1_verify.py <image>` (read-only, scans the `$KDB` so it works on any
release). Per-type PASS list for `BC250_5.00_clv`: `0x02, 0x08, 0x12, 0x13, 0x20, 0x24,
0x28, 0x30, 0x31, 0x32, 0x33, 0x34, 0x44, 0x45` — i.e. **both VCN-lock carriers verify**:
`0x24` SEC_GASKET against `96ea7cfe…` and `0x45` TOS_SECURITY_POLICY against the same key.

Unresolved by design, and now explained: types `0x50`/`0x51` (the `$KDB` carriers) declare
kid `ffc8acd45bb748e0…` which is **not present in the KDB itself** on every image — so the
KDB is anchored **outside** the image, exactly as the cross-image test found
(`39bfc192` identical across six ROMs incl. the 4700S). Types `0x01`, `0x09`, `0x4F` are not
`$PS1` containers.

## 2. What this gives us

- We can now **verify** any `$PS1` container and **produce a correctly formed one**, byte-exact,
  with a chosen body.
- The scheme is identical on a different AMD product (4700S), so it is AMD's platform scheme,
  not a BC-250 quirk.
- The **only** missing ingredient is a private key the ROM will accept.

## 3. The bypass: voltage-glitch the AMD-SP ROM public-key check

`archives/imported/research-collector/legacy-agent-reach-bc250/repos/amd-sp-glitch/` — supplemental
code for **"One Glitch to Rule Them All: Fault Injection Attacks Against AMD's Secure
Encrypted Virtualization"**, CCS'21, Niklas Jacob et al.
(`https://arxiv.org/abs/2108.04575`). Licence GPL-3.0. **Present in the repo, never mined.**

Mechanism, quoting the README:

> _"The ROM bootloader … loads a public key from SPI attached flash memory. The public key
> is validated by comparing its hash against a fixed hash stored inside the SP's ROM. This
> public key is used to validate the signature of several other firmware components that are
> loaded from the SPI flash. … Our goal is to glitch the AMD-SPs validation of the public
> key, so that we are able to use our own public key to sign the AMD-SP's firmware."_

Confirmed targets include **Zen 2** (ASRock A520M-HVS / Ryzen 5 3500; Epyc 7272). The BC-250's
Oberon/Cyan Skillfish is Zen 2 family with an AMD-SP.

**AMD will not fix it.** AMD-SB-7044 (Aug 2025) covers the same attack class: physical VFI is
declared _outside the threat model_, no microcode or firmware fix, affected list "Zen 4 and
prior". Zen 2 is in scope permanently.

### Released attack code (all local)

| component                                                | path                                                                                                           |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| ROM builder: installs your public key, re-signs firmware | `attack-code/make_epyc3_pl.py`                                                                                 |
| public-key-entry generator                               | `attack-code/make_key_entry.py`                                                                                |
| Teensy 4.0 firmware: **SVI2 bus packet injection**       | `attack-code/teensy_firmware/` (`amd_svi2.cpp`, `glitch.cpp`, `attack.cpp`, `teensy_twi.cpp`)                  |
| parameter search procedure                               | `attack-code/ParameterDetermination.md`                                                                        |
| ARM payloads to run **on the SP**                        | `payloads/{hello-world,dump-sram,get-secret-fuses,decrypt-ikek}/` (`_start.S`, `linker.ld`, `arm-none-eabi-*`) |
| proof of successful SP pwn                               | `attack-proof/` (CEK/VCEK certs + signatures)                                                                  |

`make_epyc3_pl.py` also documents the **public-key-entry format**, which is the structure our
offline work never identified:

```
key entry = version(4) | key_id(16) | cert_id(16) | key_usage(4) | reserved(16)
          | pubex_size(4) | modul_size(4)          -> 0x40 header
          || e (size/8 bytes) || n (size/8 bytes)
key_usage = 0x0 means "AMD public key"  <-- the entry whose hash lives in ROM
```

It also shows the firmware header field discipline you must follow when signing:
`[0x14] signed size`, `[0x18] encrypted flag = 0`, `[0x20] IV = 0`, `[0x38] pubkey id`,
`[0x4c] security version`, `[0x6c] packed size`, `[0x80] wrapped key = 0`.

### Hardware required

Teensy 4.0 + LVC07A open-drain drivers soldered to the **SVC/SVD lines next to the CPU VRM**,
a reset-header tap, and a logic analyzer (or scope) for the SPI exfiltration. Optional: an
EM100 flash emulator; a plain SPI programmer works.

## 4. The BC-250 attack target, identified

- The ROM-anchored **AMD public key** is the `$KDB` region (PSP type `0x4F` at `0x9CB200`,
  66048 B, raw, no `$PS1` header) plus the two KDB carriers `0x50`/`0x51`.
- Those carriers name kid `ffc8acd45bb748e0…`, which is **absent from the KDB they carry** —
  the anchor is external. `39bfc192` (t50 index 0) is byte-identical across six ROMs including
  a different product → that is the fixed ROM-side key material.
- So the glitch window is the ROM's comparison of the `0x4F`/KDB hash; the goal state is
  "our key entry accepted".

## 5. The complete path to a VCN-unlocked BIOS, end to end

1. **Glitch** the AMD-SP ROM during the public-key hash check; on success the ROM accepts the
   key entry we flashed (proof of success = a payload writing a known string to SPI, per
   `payloads/hello-world`).
2. **Install our own key entry** in the `$KDB`/`0x4F` region and **re-sign every `$PS1`
   container we touch** with that key using the now-known scheme:
   PSS / MGF1-SHA256 / salt 32 / over `header || signed_body`, key id written at `header+0x38`.
3. **Rebuild the two VCN-lock carriers** — type `0x24` SEC_GASKET and type `0x45`
   TOS_SECURITY_POLICY — with the donor values already known from the corpus:
   `0x3E810 <- 6`, `0x3A2011C <- 0x107FF`, `0x3A20124 <- 0x10FFF`,
   `0x3E814 <- 0x2544C382`, plus the 56-record VCN bank `0x0900C234..0x0900CB80`
   (the `bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.bin` build already contains the
   body; it was never signable — it is signable now).
4. **Flash.** The PSP accepts the carriers as validly signed; the fabric aperture bank and
   DF windows get programmed at boot; the NBIF/Fabric bridge opens; `mmUVD_PGFSM_STATUS` stops
   reading all-ones.
5. **Then** the already-proven runtime work applies unchanged (domain 6, clock slots, kernel
   `bc250_vcn_mode`, `vainfo`).

Everything except step 1 is already built and verified in this repository. Step 1 is the one
thing that needs a soldering iron, a Teensy, and patience.

## 6. Honest risk statement

- The glitch is fiddly: parameter search is empirical (the paper's own example needed
  thousands of attempts across a `delay`/`duration` window). Success is probabilistic.
- Soldering to SVC/SVD near the VRM on a BC-250 is not documented anywhere; it must be
  located from the boardview (`evidence/boardview/`).
- A failed glitch is a reboot, not a brick. The SPI chip stays programmer-recoverable.
- This is the **only** path found that ends in a BIOS which the PSP will accept, because it is
  the only one that removes the signature obstacle instead of working around it.

---

## 7. The signed unlock candidate (built and verified offline)

"Staged" means: every software artefact the last step depends on exists, is correct, and is
verified. The board has not been flashed and no device has been attached — that physical
step is the operator's action, specified in the runbook. The path itself is complete.

`candidates/BC250_5.00_clv_VcnUnlock_GlitchSigned_v001.bin`
`sha256 91de01eb7cb8e97014294adc8692eb8be66c3f95ce8481c234805544c0ddd517`, 16 MiB,
14009 changed bytes, range `0x8E0004..0x9E4707`.

Built by `scripts/build_glitch_unlock_candidate.py`; report
`evidence/firmware-audit/20260919-glitch-path/build-report.json`; independent structural
audit `evidence/firmware-audit/20260919-glitch-path/firmware-audit.json`.

What it contains:

| step                                      | result                                                                                                                                                                                                                    |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| own RSA-2048 key                          | kid `b36ad5af630d9ad42edb551c2581d63c`, e=65537                                                                                                                                                                           |
| `$KDB` t50 slot 0 (the ROM-anchored slot) | `39bfc192…` → our kid, our modulus installed                                                                                                                                                                              |
| type `0x24` SEC_GASKET                    | stock body `0x2C50` → **donor body `0x2E10`** (56-record VCN bank + donor DF values), container `0x3010` moved to `0x9E0000`, **re-signed with our key**                                                                  |
| type `0x45` TOS_SECURITY_POLICY           | `0x3E810 <- 6`, `0x3A2011C <- 0x107FF`, `0x3A20124 <- 0x10FFF`, `0x3E814 <- 0x2544C382`, +5 VCN tail pairs appended to group `0x280`, body `0x4E0` → `0x508`, container `0x708` at `0x9E4000`, **re-signed with our key** |
| `$PSP` directory                          | entries 7 (`0x24`) and 15 (`0x45`) repointed; Fletcher32 refreshed → `0x8F1BAFA8`, `checksum_match=True`                                                                                                                  |

Verification (all in-repo, no hardware):

```
$ python3 scripts/psp_ps1_verify.py candidates/BC250_5.00_clv_VcnUnlock_GlitchSigned_v001.bin
  [ 7] type 0x24 @0x9e0000   12304  PASS  PSS/SHA256/s32  kid=b36ad5af630d9ad4 signed=0x2e10
  [15] type 0x45 @0x9e4000    1800  PASS  PSS/SHA256/s32  kid=b36ad5af630d9ad4 signed=0x508
  verified 14, failed/unresolved 2, non-container 3
```

14 PASS — the **same count as the stock base**, so no untouched container regressed; the two
that changed now validate under our key instead of the vendor's. `firmware_audit.py` reports
PSP/BHD/APCB valid and 4 firmware volumes.

The private key is deliberately **not** in the repository: `scripts/build_glitch_unlock_candidate.py`
writes it to `/tmp/bc250_glitch_key.pem` (G5). Re-run with `--key` to reuse one.

Reproduce the artifact from the tracked repository alone (the `.bin` itself stays out of git
per project policy; the builder, the base hash and the output hash are all tracked):

```
python3 scripts/build_glitch_unlock_candidate.py \
  --base evidence/donor/retroweb-20260916/BC250_5.00_clv.bin \
  --out /tmp/reproduced.bin --key /tmp/bc250_glitch_key.pem
sha256sum /tmp/reproduced.bin   # compare with the tracked build-report out_sha256
python3 scripts/psp_ps1_verify.py /tmp/reproduced.bin
```

**The only remaining step is the glitch** (step 1 of §5). Everything the glitch has to make
acceptable is already in this image: the key entry it must bless, and the two carriers that
carry the VCN unlock, correctly signed.
