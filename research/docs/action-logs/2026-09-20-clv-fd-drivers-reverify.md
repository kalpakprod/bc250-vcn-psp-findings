# FD v2.2 drivers-only candidate — reverification of the recorded artifact

Timestamp: 2026-09-20 (Asia/Almaty). Actor: root. Trigger: control-only continuation turn with no
new operator instruction; resumed the newest recorded unfinished operation on the bound object,
namely the verification gate of the newest unflashed candidate plus the `Unrun: repo pytest suite`
line in `docs/action-logs/2026-09-20-fd-v22-to-clv-port.md`.

Bound object (TARGET): `candidates/BC250_5.00_clv_MeiMeiDXEv3-drivers-only_v001.bin`
(`0968a70c4d6fbb51f43d3e0fb5e4b3783dec41e881246356a75c66dc5f19c554`), built from base
`evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
(`ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`) and donor
`import/from-windows/Users/kukuruza/tmp_bc250/ext/fd_repo/extracted/BC250_3.00_MeiMeiDXEv3`
(`606a7a7f9ef8fb1c445d8ccfa9640de0339bfec5ab52969135a9e87d62028182`).

## Intent and expected effect

Re-execute the existing verifier and builder routes on unchanged inputs, confirm that the recorded
candidate bytes are reproducible, and run the repository test suite that the previous log left
unrun. Read-only with respect to the repository: all outputs go to the disposable directory
`/tmp/clv-vob-repro`. No candidate write, no ROM/NVRAM/hardware change, no new parser.

## Observed result

A1. Reproduction of the newest evidence result (`verify_voltage_offset_boundary.py`, copied to
`/tmp/clv-vob-repro/repro.py` with only its output path repointed so the recorded evidence file is
not rewritten). Exit `0`, stderr `0` bytes, stdout `4146` bytes. Produced
`voltage-offset-boundary-result.json` SHA-256
`4026f8cebb814fc11fddb58eb5f5fd4e1e41fc878dbba3d3745161ddb7667bd3`; `cmp` against the recorded
`evidence/firmware-audit/20260920-clv-voltage-offset-consumer-boundary/voltage-offset-boundary-result.json`
is byte-identical.

A2. Reproducible rebuild. `python3 scripts/build_fd_drivers_clv.py --base
evidence/donor/retroweb-20260916/BC250_5.00_clv.bin --donor
import/from-windows/Users/kukuruza/tmp_bc250/ext/fd_repo/extracted/BC250_3.00_MeiMeiDXEv3 --output
/tmp/clv-vob-repro/rebuild.bin --manifest /tmp/clv-vob-repro/rebuild.manifest.json`. Exit `0`,
stderr empty. Output SHA-256
`0968a70c4d6fbb51f43d3e0fb5e4b3783dec41e881246356a75c66dc5f19c554`, byte-identical (`cmp`) to the
repository candidate. The builder's own post-build assertions (FV header checksum, FFS walk,
capsule header checksum, outer-FV prefix/suffix identity, PSP-directory entry equality, APCB
window equality) therefore all passed in this fresh run.

A3. Independent structural diff of candidate against base (separate script, no builder output
reuse for the diff). Total differing bytes `1342158`; first `0xAE0088`, last `0xC28F45`; bytes
outside `0xAE0000..0xE00000` byte-identical. Decompressed inner FV file count `187` (base) versus
`193` (candidate); inner FV size `0x41c000` -> `0x437000`. The set difference of GUIDs equals exactly
the six recorded `MeiMeiDXEv3_*` GUIDs; none of them is present in the base. Raw outer-image
`bytes_le` searches for those six GUIDs return `0` hits in both images, which is expected because
the injected files live inside the LZMA-compressed inner FV and is not a defect.

A4. Repository test suite (previously recorded as unrun). `/home/OWNER/.local/bin/pytest -q
tests/` -> `16 passed in 1.44s` (exit `0`). The shim resolves to
`/home/OWNER/.local/share/uv/tools/pytest/bin/python`; the system interpreter
`/usr/bin/python3` (3.14.7) has no `pytest` module, but `python3 -m unittest` also works with
`PYTHONPATH=.` (5 + 4 + 7 tests, all `OK`).

## State and limits

Status of the candidate is unchanged: `BUILT_OFFLINE_STATIC_VERIFIED`, `hardware_written=false`.
This log is a re-verification, not an independent second-family review and not operator flash
approval; neither gate is satisfied. Board `BC250-01` remains unreachable, so boot, DXE dispatch,
core selection, and VCN behavior are `UNRUN`. The presence and checksums of the injected modules are
`observed-bytes`/`static-analysis` only; no claim about PSP acceptance, POST, or hardware behavior
follows.

## Rollback

Delete this action log. All scratch outputs are in `/tmp/clv-vob-repro` and no repository input,
candidate, or evidence file was modified.

## Remaining uncertainty

Whether the six injected clv-volume DXE drivers are dispatched, and whether the earlier whole-FV
graft failure at P0 (`af531026`) is avoided, both require a board run. The consumer of `$INV`
record `0x1364` remains unresolved from the prior bounded static trace.
