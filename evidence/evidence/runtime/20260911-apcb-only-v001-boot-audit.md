# Runtime audit: APCB-only v001 boot (2026-09-11, SSH read-only)

- Access: steammachine@127.0.0.1, key ~/.ssh/id_ed25519 (found via config.windows-20260911 `steammachine` host entry). Passwordless sudo OK.
- Board time 2026-09-11 22:53 PKT; kernel 7.2.0-1.1-cachyos-bc250; cmdline includes video=DP-1:1920x1080@60.
- Board boots to Linux on APCB-only v001 (SPI 6b1fe8ef...): SSH alive, amdgpu bound to 1002:13fe, DP-1 connected, card1+renderD128 present.
- amdgpu IP blocks detected: 8 (common, gmc, ih, psp, smu, dm, gfx, sdma). NO vcn/uvd/vce/jpeg block. VCN firmware load lines absent.
- SMU 88.6.0 initialized successfully. Display-path errors present (dal_irq dummy ack/set, HPD clear fails) but DP-1 reports connected.
- Verdict: board boots + display path alive under APCB-only; VCN block NOT instantiated by stock driver (expected empty case IP_VERSION 2,0,3). Next: patched kernel / VCN fw staging (operator decision).
