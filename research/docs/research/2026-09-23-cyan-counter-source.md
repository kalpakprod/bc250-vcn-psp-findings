# Cyan Skillfish hardware-counter source, not a memory-clock recipe

Goal: independent clock observation for CLV5001:1:1. No board access or hardware writes.

## Executed source check

Opened AMD-authored upstream Linux sources via GitHub contents API:

- https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/amd/display/dc/clk_mgr/dcn201/dcn201_clk_mgr.c
- https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/amd/display/dc/inc/hw/clk_mgr_internal.h
- https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/amd/include/cyan_skillfish_ip_offset.h
- https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/amd/include/asic_reg/clk/clk_11_0_1_offset.h

Source files copied with license headers, hashes in evidence/firmware-audit/20260923-cyan-counter-source/result.json. Retrieved2026-09-23; snapshots are hashed, not all from a pinned revision. Initial wrong path for clk_mgr_internal returned404, corrected to dc/inc/hw. No installation.

The actual Cyan-specific DCN201 constructor includes clk11_0_1 and CyanIP offsets. It reads CLK4_CLK2_CURRENT_CNT into dprefclk_khz, multiplies by100, substitutes600000 if zero. It also reads CLK4_CLK_PLL_REQ FbMult_int into display VCO state, multiplies by100000, substitutes3000000 if zero.

Native source macro resolves mmio dword index as CLK_BASE__INST0_SEG0(16C00)+register467F. Byte offset6C9FC. PLL_REQ460E similarly yields6C838. Arithmetic assertions passed. This is GPU MMIO address arithmetic, not automatically the same as rawSMN window mapping.

## Meaning and rejected shortcuts

This is a concrete hardware register-reading path for the display reference clock. It is NOT an independent UCLK/MCLK/FCLK measurement. A zero hardware value can produce a nonzero software fallback; displayed values cannot be accepted without checking raw value and origin.

A public dcn3_clk_internal struct has CLK4_CLK0_CURRENT_CNT annotated fclk, but that is a different display-IP context. It does not name Cyan's domain or prove the desired counter exists at extrapolated offsets. Renoir's counter reader similarly labels display clocks, notBC250 memory. UMR power/clock documentation does not establish independent memory-domain counters.

Decision: use Cyan-specific sources rather than generic register-base matching, but exclude this DPREFCLK counter from1:1:1 acceptance. No reads of inferred adjacent counters, no genericEFI register scan. Actual memory/fabric counter mapping and BIOSSoC setter remain open. Firmware and board unchanged.
