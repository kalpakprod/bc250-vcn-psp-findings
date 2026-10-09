# BC-250 VCN: trusted-environment and secure-debug audit

**Status:** partially outdated; later runtime-replay and evidence corrections are authoritative in `2026-08-26-bc250-vcn-evidence-reassessment-and-safe-next-slice.md`.  
**Date:** 2026-08-25  
**Board:** `steammachine`, BIOS `P3.00`, PMFW `0x580600`, kernel `7.2.0-1.1-cachyos-bc250`

## Verdict

A normal Linux AMD-TEE call path is not available on this board. The native PMFW domain-6 path has now been closed experimentally, including a genuine electrical OFF -> ON cycle. VCN MMIO remains uniformly `0xffffffff` afterward.

The only trusted path found in Robin firmware that can broadly alter secure hardware policy is `DEBUG_UNLOCK`. It is enabled by policy but requires a valid RSA-2048 signed debug token. The BIOS contains only the public verification key, not the signing key.

No callable signed TA or Trusted OS command for VCN, NBIF, SEC_GASKET, or arbitrary SMN access was identified.

## 1. Native PMFW OFF -> ON result

The corrected `native_domain6_cycle.py` executed both firmware-owned transitions:

```text
before:
  state  = 0x00010101
  ctrl   = 0x00000000
  status = 0x01010101

after native FUN_00024764 OFF:
  state  = 0x00010100
  ctrl   = 0x00000007
  status = 0x01011010
  slot clocks = 0 / 0 / 0

after native FUN_00023b14(6,1) + slot restore:
  state  = 0x00010101
  ctrl   = 0x00000000
  status = 0x01010101
  slot clocks = 18 / 32 / 20
```

SMU remained alive through both transitions. Final metrics were `VCLK=625`, `DCLK=1111`, SMU version `0x580600`, WGP 12.

The subsequent guarded MMIO ladder still returned `0xffffffff` for all 11 registers across both VCN segments, including static `UVD_VERSION`. Therefore the clamp is not released by any domain-6 PMFW power edge available in this firmware.

Evidence:

- `tmp_bc250/recon/native_domain6_cycle_2026-08-25.out`
- `tmp_bc250/recon/native_cycle_clock_enable_2026-08-25.out`
- `tmp_bc250/recon/native_cycle_manual_powerup_2026-08-25.out`
- `tmp_bc250/recon/vcn_mmio_liveness_after_native_cycle_2026-08-25.out`

## 2. Linux AMD-TEE reachability

The kernel contains the generic stack:

```text
CONFIG_TEE=m
CONFIG_AMDTEE=m
CONFIG_CRYPTO_DEV_SP_PSP=y
amdtee.ko present
```

Runtime result:

```text
modprobe amdtee
amdtee: tee not present
modprobe: ERROR: could not insert 'amdtee': No such device
```

No `/dev/tee*` device exists. No CCP/PSP PCI function is bound to the system `ccp` driver; only the module object is present. Consequently `psp_check_tee_status()` returns `-ENODEV` because no system PSP `tee_data`/TEE ring was initialized.

The PSP ring inside `amdgpu` is a separate GPU firmware command path. It does not make the generic system AMD-TEE GlobalPlatform interface available.

Evidence:

- `tmp_bc250/recon/amdtee_probe_2026-08-25.out`
- `tmp_bc250/recon/ccp_psp_probe_2026-08-25.out`

## 3. Trusted OS and DRIVER_ENTRIES

Robin contains:

- `PSP_FW_TRUSTED_OS~0x2_0.1C.0.2`: AMD Trusted OS kernel;
- `DRIVER_ENTRIES~0x28_0.1C.0.2`: GlobalPlatform runtime/drivers;
- `TOS_SECURITY_POLICY~0x45_B.51.1.16`: signed Trusted OS policy;
- `DEBUG_UNLOCK~0x13_29.1C.0.1`: secure-debug authorization module.

`DRIVER_ENTRIES` exposes generic GP TEE properties such as `gpd.tee.deviceID`, `gpd.tee.debug.DLM_available`, `amd.fw.SecPatchLevel`, and `amd.ta.version`. Static string/literal scanning found no VCN, UVD, NBIF, gasket, or SMN management service. This does not prove no internal primitive exists, but there is no identified command ABI that Linux can invoke.

The firmware can load external TAs only after signature verification. A locally built TA cannot be used as an arbitrary secure-world SMN writer without a trusted signing key or a vulnerability in the TA loader/runtime.

## 4. Secure Debug Unlock

The signed `DEBUG_UNLOCK` module implements the observed sequence:

1. `Svc_GetDebugUnlockInfo`;
2. `UnlockNegotiation`;
3. `SecureUnlock`;
4. success state `DBG_UNLOCK_MODULE::Securely UNLOCKED`;
5. optional ASIC lock finalization.

The SEC debug public key is identical in Robin BIOS 1.00 and 5.00:

```text
version          = 1
key usage        = 3
security features= 0x0000
RSA modulus      = 2048 bits
public exponent  = 65537
modulus SHA-256  = 6a3a7b2048c57d7290c108ba6e22d0809b558bddd8c8e9d2ef6f231cff359fbb
```

`security_features & DISABLE_SECURE_DEBUG_UNLOCK == 0`, so the firmware policy does not disable the mechanism. However a challenge-specific token must be signed by the corresponding private key. That private key is not present in the BIOS, public repositories searched, or the extracted firmware.

Therefore secure debug is supported but cryptographically unavailable without AMD/OEM authorization material or a secure-world vulnerability.

## 5. Working-sibling SEC_GASKET comparison

A working Cezanne BIOS (`A3MSTX_3.70E`) was extracted and parsed. Its hardware discovery reports VCN `HWID=12`, version `2.2.0`, harvest `0`, with the same three base families used by BC-250:

```text
0x00007800
0x00007e00
0x02403000
```

Two independent Cezanne PSP directories contain an identical 56-write security-gasket bank at `0x0900c000..0x0900cfff`. Decimal `0x0c` matches VCN HWID 12. The equivalent bank is completely absent from Robin 3.00:

```text
BC-250 VCN-bank writes:          0
working Cezanne VCN-bank writes: 56
working-bank SHA-256: 8c67c82a786081a83a82989904e024d1bbecaa429275105c7779f2c14fd46ad3
```

The working bank contains explicit VCN-register subranges, including:

```text
0x0900c934/38 -> 0x00021800..0x000218ff
0x0900c958/5c -> 0x00020300..0x000206ff
0x0900c97c/80 -> 0x0001f844..0x0001f84f
0x0900c9a0/a4 -> 0x00020180..0x00020183
0x0900c9c4/c8 -> 0x00020108..0x00020117
0x0900c9e8/ec -> 0x00021078..0x0002107f
0x0900ca0c/10 -> 0x00020eb0..0x00020eb7
0x0900ca30/34 -> 0x0001f860..0x0001f863
```

This is the first policy difference tied structurally to VCN rather than inferred from an all-ones host read. It strongly identifies the missing HWID-12 gasket bank as Robin's secure-world configuration gap. It is not yet proof that replaying the bank alone opens host BAR5 access; the fields still require semantic decoding and may grant PSP-client access rather than x86-host access.

At the time of this report, host reads returned `0xffffffff` and no writes had been attempted. A later privileged SMU experiment replayed all 56 writes successfully but did not open VCN MMIO; see `2026-08-25-bc250-vcn-gasket-diff.md`.

Evidence:

- `tmp_bc250/recon/working_vcn_gasket_template.json`
- `tmp_bc250/recon/vcn_hwid12_gasket_diff.txt`
- `tmp_bc250/recon/read_sec_gasket_policy_with_renoir_candidates_2026-08-25.out`
- `tmp_bc250/recon/cezanne_a3mstx_370e/dir1_hw_ip_parsed.json`
- `tmp_bc250/recon/cezanne_a3mstx_370e/dir3_hw_ip_parsed.json`

## 6. Remaining viable paths

1. **Decode the 56-write VCN bank:** map control fields, client masks, lock bits, and range descriptors without writing hardware.
2. **AMD/OEM signed debug token:** cleanest execution path, but requires unavailable private authorization material.
3. **Trusted-runtime vulnerability research:** audit `DEBUG_UNLOCK`, TA loading, and command-buffer validation. This remains analysis-only unless a separately authorized security-testing scope is established.
4. **Firmware topology/driver work:** still required after secure routing is opened. VCN must be added to the amdgpu IP topology and supplied with compatible firmware or direct-load support.

## Board state at report time

At report time the board was online, SMU responsive, and VCN clocks active at `625/1111 MHz`. This footer is historical, not the current operational state.
