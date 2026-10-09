# Open technical questions

These questions are retained from the imported research and remain open until a decisive test closes them. Statuses updated 2026-09-12 after the S2 C2P preflight and campaign corpus mining.

1. Does the closed PSP/supervisor accept and apply the runtime mailbox blob path on the target BC-250?
   - Status 2026-09-12: direct C2P transport tested negative on BAR5 (stage-1 `0x100B` token request: bit31 pre-set, TOS wrote nothing; direct `C2PMSG_35` write not the transport; result SHA `d6f74e4d...`). The Q2 ring path (msg `0x23`) remains untried from Linux and is the next transport candidate.
2. What exact signature span and verification transform does the target PSP use for modified `$PS1` blobs?
   - Status 2026-09-12: sharpened by the D3-B2 retest — with correct display wiring, policy carriers with stale signature material do not boot, while APCB-only does. Leading explanation: PSP rejects modified/relocated signed policy. Offline signature verification remains impossible (no signing capability).
3. Does the supervisor rebuild the policy registry from a mailbox-loaded blob, or only from boot-time signed blobs?
   - Still open; depends on question 1 (a working runtime transport) before it can be tested.
4. Does the target PMFW raise VCN domain and clock power after policy changes, or require a separate SMU path?
   - Status 2026-09-12: dom6 oracle (hardware 2026-08-25/26) shows the separate SMU path works: manual power-up + clock slots ON/READY, and the domain gate re-arms at every cold boot. The remaining unknown is not power but the NBIF/Fabric bridge (G5) and whether the gasket aperture must be programmed at boot or can be latched at runtime (question 8).
5. What exact host-visible command encoding maps to the inferred TOS/PSP mailbox commands?
   - Status 2026-09-12: `0x100B` token-request encoding on C2PMSG_64..66 measured clean-negative. SMU-side encodings are fully known (147-handler msg table, validated anchors). TOS-side encoding beyond `0x100B` remains unknown.
6. Which Linux driver and firmware changes are required after hardware discovery is enabled?
   - Still open. Known so far: the 1.92 probe kernel registers VCN (`vcn_v2_0`) and loads green_sardine_vcn.bin (mode1 hardware-verified 2026-09-12); wedge at first MMIO in mode2 without domain power.
7. Which candidate changes are actually reversible on the target board, and what is the tested recovery time?
   - Status 2026-09-12: runtime SMN writes are session-reversible (cold power cycle restores re-armed gates, proven twice); SPI reflashes proven reversible with flashrom VERIFIED + independent readback (three full cycles). NBIO S4 bit-writes are designed reversible but unrun.
8. NEW: Does a runtime SMN write to DF window `0x03A2011C` latch (survive into reads) on this board, or is the DF register space hardware-locked until cold reset?
   - ANSWERED 2026-09-12 (hardware-verified): the donor gasket writes LATCH — bank-12 commit readback = 1 after 59 accepted writes. But SMN READS of DF space hang the SMU mailbox in the never-programmed boot state (read wedge class closed); the latch was proven via the bank-12 control readback, not DF-window reads. The full result and wedge taxonomy are in `memory/firmware-audit.md` (S2-A section).
9. NEW: Do the NBIO candidate registers from the 2026-08-29 chain report (`0x13b1005c/0x13b10060/0x13b00084/0x13b0004c`) actually gate the NBIF/VCN bridge on this board?
   - Status 2026-09-12 (morning): S4 reads measured (safe class), no clamped candidate found; the four chain-report candidates are experimentally unsupported as clamp carriers.
   - ANSWERED BY STAGE5 (2026-09-12 06:50 PKT, hardware-verified): the full donor dataplane (NBIF routes `0x1C7xx`, NBIO `0x1F820/0x1F8A4`, IOHC `0x322`, DF `0x3D2`, binding `0x3E814`) was runtime-written ON TOP of the full bring-up + gasket (59/59, commit=1) — the arbiter stayed ALL-ONES with clean reads. The bridge is NOT a routing-values problem. The S4 NBIO bit-writes are also excluded (no candidate). Remaining suspects: island ISO/reset held outside the dom6 sequencer; an unmapped Q3 fw message (real PowerUpVcn equivalent); PSP-side isolation beyond the gasket. Next lever: Q3 msg-table deep decode + ISO chain in the SMU firmware image.

Each question needs a named input, baseline, one-variable test, expected signal, stopping condition, and evidence class.

- OQ12: PSP authority map — for each of the 19 `$PSP` entries in 5.00 clv, which `kid`
  verifies it, and is there any entry with no signature block at all? Untested statically.
  A "no-signature entry" or an entry verified by a kid that is not the one its type should
  use would be a pre-auth write primitive on a signed carrier — the only remaining lane
  that has authority over the VCN isolation grant. Requires: entry-body parse
  (signature block presence + length field consistency) and the kid→entry map.
  No hardware needed for the static half.
