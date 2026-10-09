# VCN MMIO map audit — 2026-09-14, Asia/Almaty

## Intent

Root compares the historical runtime arbiter script to the public VCN2 register
header and retained driver. No hardware reads/writes or parser mutation.
Record corrections before any later probe design. Rollback: append corrections.

## Result

Public comparison: Linux v6.8
https://raw.githubusercontent.com/torvalds/linux/v6.8/drivers/gpu/drm/amd/include/asic_reg/vcn/vcn_2_0_0_offset.h
Fetched 2026-09-14. VERSION=0x5C9, POWER_STATUS=4, STATUS=0x26F,
SCRATCH9=0x1D; all BASE_IDX=1. Using the recorded discovery base1=0x7E00
in dwords gives byte addresses VERSION=0x20F24, POWER_STATUS=0x1F810,
STATUS=0x201BC, SCRATCH9=0x1F874.

`recon/read_vcn_direct.py` instead labels base0=0x7800 plus offsets
0xCA,0xBC,0xBD,0xC9 as those registers. Those label/address mappings conflict
with VCN2. In particular 0x1E328 is not VERSION under this interface.
The values actually read remain historical measurements at their numeric
addresses; they do not prove the named registers' state.

The historical full `enable_vcn.py` ladder DOES use base1=0x7E00 and the
VCN2 offsets above and also records all-ones. Therefore this finding invalidates
the short arbiter's labels, not every historical negative VCN result.
Fresh on-board address validation and boot identity remain unrun.

## Experiment reconciliation intent and result

Root correlates prior action logs with exact scripts/addresses before deciding
whether a new hardware experiment adds information. No firmware changes.
Read-only SSH identification attempt at the authorized board 127.0.0.1
failed with `No route to host`; it establishes network unreachability only,
not power-off, firmware identity or reset state.

| Experiment | Preparation | Observer | Evidence limit |
| --- | --- | --- | --- |
| Aug25 native clock/direct-load archive | domain6 gate released, slots22-24 enabled | full VCN2 ladder, including VERSION0x20F24 | all-ones recorded; exact same-session full gasket state not established by this file |
| Sep12 S2-A cycle4 | logged59 writes, C234=1, power/clock setup | runbook specifies VERSION0x1E328 and other conflicting offsets | named VCN register verdict invalid; raw script hash recorded but actual deployed script/output not present in bounded local inventory |
| Sep12 stage5 | log reports15 route writes and all-ones BAR5 probes | exact deployed observer source still needs retrieval | cannot independently verify register map from labels alone |
| Sep12 D19 | C830 write on ReadyToBoot | liveness False after boot | establishes failed candidate behavior, not VCN power-domain identity or all routes closed |

Important: an earlier correctly addressed negative under a different preparation
does not validate S2-A's incorrectly addressed post-gasket verdict. Do not merge
those sessions into a fictitious complete test. The combined requirement is:
same boot, identified BIOS/PMFW, source/divider/gate recorded, exact gasket
sequence confirmed, then the matching device's correctly mapped VCN observer.
Neither a proposed read-only label nor a host timeout establishes safe MMIO.

Next read-only collection when the board is reachable: retrieve only the
known deployed stage2b/stage4/stage5 scripts and their named outputs, verify
hashes, inspect commands offline. Do not replay them automatically.

## Retrieval checkpoint

Second bounded SSH attempt failed with No route to host. Recursive filename
inventory including ignored files under evidence/scripts/candidates/import
found no deployed stage2b_writefirst.py, stage4_arbiter.py,
stage5_full_dataplane.py or their named September12 outputs.
This is a loose-file inventory, not a claim that every archive was exhausted.
Archive filenames inspected mostly identify captures predating September12;
no extraction of unrelated exports or credential-bearing material performed.

## Board retrieval closure

The board became reachable on 2026-09-14 after operator power-on. The exact stage2b/stage4/stage5 sources and named outputs were retrieved read-only into `evidence/runtime/20260914-board-retrieval/`.

Direct source inspection confirms the stage4 observer used the conflicting base0/offset labels identified above. Its all-ones output is preserved only as five raw numeric-address reads, not as correctly named VCN2 register evidence. Stage2b and stage5 JSON files independently support their write-count, commit-readback, liveness, and configuration-capture claims.

The retrieval blocker is closed. Do not replay these scripts: stage2b/stage5 are write-capable, and stage4's address labels are invalid for the intended VCN2 names.

Exact next retrieval set from /home/OWNER/vcn_unlock:
- stage2b_writefirst.py; stage4_arbiter.py; stage5_full_dataplane.py
- stage2b_writefirst_20260912_052757.json
- stage4_arbiter_20260912_052802.txt
- stage2b_writefirst_20260912_064724.json
- stage5_full_dataplane_20260912_064729.json
Expected stage4 script hash from contemporaneous journal:
821635e2c0f80a34f03a2a82902d1f3b65c5ec451110ec602c01b1da0d883227.
Files must be source-reviewed and outputs sanitized before preservation.

Operator input is needed to establish current board state and make these
files accessible. Do not request a boot blindly while programmer attachment
and flashed image are unknown. No firmware write or mailbox execution is
part of the requested evidence retrieval. The broad unlock goal remains open.

## Bounded archive alternative

Read-only archive member listings checked BC250_VCN_test_package_v2.zip
(9 members; latest recorded member September3) and bc250_flashkit.zip
(12 members; latest recorded member2024). Neither contains the seven
exact requested source/output filenames. vcn_campaign.tgz member names
also contain none of stage2b_writefirst/stage4_arbiter/stage5_full_dataplane.
No archive payloads or unrelated exports were extracted. This closes these
three recovery alternatives, not all possible archives. The known board
directory remains the primary source for September12 evidence.
