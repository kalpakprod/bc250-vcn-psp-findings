**SUPERSEDED in part.** The model below ("replay the 1379-step script") is wrong: the

> Историческая процедура, статус пересмотрен 2026-09-27. Старое «следующий шаг» не является текущим разрешением на прошивку или runtime-запись. Сверять точную ветку, полный путь и хеш; одинаковые v001/v002/v003 в разных каталогах не равнозначны. См. `docs/research/2026-09-27-vcn-smu-status-audit.md`.

script had already been decoded in the imported corpus, the lock is a closed DF window
(`0x03A2011C` bit 12), and the correct order is in
`docs/research/2026-09-19-gasket-script-decode.md`. Kept for the record.

# Path to VCN: the fabric routing is a scripted 1379-step table in the signed gasket

## Status (2026-09-19T14:47+0500, Asia/Almaty)

Static analysis complete for this layer. No hardware action in this pass.

## What was found

The SEC_GASKET carrier (PSP type `0x24`, SPI `0x982000`, size `0x2E50`) does not hold
opaque policy bytes. Its `$PS1` payload (`0x2C48` bytes) is an **ordered write script**:
a flat array of `(u32 addr, u32 value)` pairs, 1379 records, 8-byte stride, starting at
payload `+0x130`.

- Payload sha256 `7268388943f98834`.
- **Byte-identical across every BC250 BIOS revision** — 2.00, 3.00, 3.00_CHIPSETMENU,
  5.00, 5.00_clv: same payload hash, 1379 records, **zero differing records**.
  VCN was therefore never routed differently by any BC250 BIOS release; it is a single
  fixed vendor decision present from 2.00 onward.
- Cross-version report: `evidence/firmware-audit/gasket-script-crossversion.json`.

## The three sub-blocks that matter

### 1. Data Fabric segment translation table (`0x3E8xx`)

```
rec[1263]  0x3e810 <- 0x0            selector / command, left at 0
rec[1264]  0x3e814 <- 0x2232c240     entry
rec[1265]  0x3e814 <- 0x2233c241
rec[1266]  0x3e814 <- 0x2262c24e
rec[1267]  0x3e814 <- 0x226ec250
rec[1268]  0x3e814 <- 0x2278c261
rec[1269]  0x3e814 <- 0x244fc441
rec[1270]  0x3e814 <- 0x244ec442
rec[1271]  0x3e814 <- 0x244dc443
rec[1272]  0x3e814 <- 0x226cc24f
rec[1273]  0x3e814 <- 0x2440c440
rec[1274]  0x3e814 <- 0x2544c382
rec[1275]  0x3e814 <- 0xf853c480
```

`0x3e810` is a selector; `0x3e814` is the entry payload; the vendor writes twelve
entries and finishes with the selector at `0`. This is the fabric router's translation
table — the thing that makes a device's MMIO aperture actually reachable.

### 2. Firewall windows (`0x3A2xxxx` and its mirror `0x322xxxx`)

`0x3a2011c <- 0x87ff` is a block-everything default, followed by a run of
`0x3a20124 .. 0x3a201d4 <- 0x0`, then `0x3a20120 <- 0xffff0000`. The mirror bank
`0x322xxxx` carries the base/limit pairs:
`0x3220120 <- 0xb0000`, `0x3220128 <- 0x1030100`, `0x3220130 <- 0x57f057c`,
`0x3220178 <- 0xff0000`, `0x3220180 <- 0x57b0104`, `0x3220188 <- 0xfffb0580`,
`0x3220190 <- 0x10000c`, plus `0x322011c` written `0x8000` then `0x80ff`
(build-then-enable). `0x3220190`'s `0x10000c` and the `0x57f/0x57b` pairs are packed
base/limit windows.

### 3. VCN gasket register

`0x1f8a4 <- 0xb` — the register this project previously identified as the VCN gasket
de-isolate, and the vendor's script sets it to `0xb`, not `0`.

## Why the campaign stalled, and why the community stalled too

Our DXE driver's `mGasketDataFabricWrites` contains:

```
{ 0x0003E810, 0x00000006 }          <-- selector value 6; the vendor never writes 6
{ 0x0003E814, 0x2544C382 }          <-- a single entry, rec[1274] of twelve
{ 0x03A2011C, 0x0000107F }          <-- vendor writes 0x87FF here
```

Every one of those is a **fragment of a 1379-step script**, with a selector value the
vendor never uses. The rest of the table is derived from Cezanne, per the comments in
the source. Single-register pokes against a scripted sequencing table explain both
observed outcomes: no effect, or a wedged bus.

## The path

1. **Decode the script** (static, no hardware): identify every control/index field
   (`0x203 <- 0x1f`, `0x210 <- 0xd`, `0x280 <- 0x64`, `0x281 <- 0x1f`) and classify which
   of the twelve `0x3e814` entries is the VCN segment. Falsifiable: each entry's packed
   fields must decode to a device/function or aperture range that includes or excludes
   the VCN block.
2. **Replay the script from inside the SMU**, not from Linux and not from DXE SMN.
   Transport is already proven: Q3 message `0x32` at slot `0x7774` running our xtensa
   thunk at `0x3FF00`, which executes and returns status `0x1` with the SMU alive.
   This is the only route that is (a) privileged enough to write fabric registers,
   (b) pre-nest, so it cannot trigger the host-side Data Fabric sync flood that wedged
   the board in D17, and (c) does not require forging any signature — we are not
   modifying the signed carrier, we are re-issuing writes with different values.
3. **Stage it smallest-first.** Start with the `0x3E8xx` sub-block alone (13 writes,
   bounded), with the VCN entry enabled rather than the vendor's value. Expected signal:
   `mmUVD_PGFSM_STATUS` reaches `0` in mode 2 and `secure` stays `True` through the
   `amdgpu` load.
4. **Stability.** The vendor's script is re-applied by the SMU on every boot, so the
   replay must run every boot: the DXE injection path is proven working (FirstMarker
   telemetry), so the thunk goes out at ReadyToBoot. If the `amdgpu` load path re-runs
   the fence afterwards, the kernel side must re-arm — which is why the community's
   driver-side work (simpmix) is part of the answer and not a competing approach.

## What is not proven

- That enabling the VCN entry in the `0x3e814` table is sufficient. The table's encoding
  is not yet decoded; this is step 1.
- That the SMU will accept a rewrite of these registers after its own script has run.
  Fabric registers may latch.
- That a 1379-write replay is safe. Stage it; do not send the whole table first.

## Artifacts

- `evidence/firmware-audit/gasket-script-crossversion.json` (full ordered script + cross-version hashes)
- This file.
