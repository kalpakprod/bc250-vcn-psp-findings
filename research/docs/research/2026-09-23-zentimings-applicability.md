# ZenTimings/ZenStates is not a recovered BC250 synchronization switch

Source pinned from ZenTimings submodule: ZenStates-Core ab5414a4038bb0f567e418c52bdd93bdace5cdcb. Public source only; no installation or execution on the board.

https://github.com/irusanov/ZenStates-Core/tree/ab5414a4038bb0f567e418c52bdd93bdace5cdcb

Opened Hardware/PowerTable.cs, Hardware/DRAM/Ddr4Timings.cs, MemoryConfig.cs, BaseDramTimings.cs and Cpu.cs. Retained files and LICENSE under evidence/firmware-audit/20260923-zentimings-source/; hashes in result.json.

Observed source assertions:

- MCLK/FCLK/UCLK each assigned from GetDiscreteValue(pt,tableDef.offset...) with BCLK correction. Refresh obtains data via smu.ReadPmTable/UpdatePmTable.
- Ddr4Timings.ReadRatio reads offset|50200 bits0..6 and divides by3.
- Inspected MemoryConfig dispatch constructs DDR4/LPDDR4 or DDR5/LPDDR5 timing readers; no GDDR6 branch in that class.

Decision: no demonstrated Cyan-compatible independent clock/divider source is supplied by these paths. This does not prove global project incompatibility or that every power-table value is merely a requested value. Producer semantics would need separate proof for the exact BC250 table. Do not run desktopDDR4 register reads on BC250 or bypass D17 because the external tool has a read-only label.

The specific public BC250 counter search returned community SMU getter reports and ordinary metrics sources, not an independently established counter. Such reports remain participant evidence. No firmware settings, candidate, voltage or1:1:1 claim results.

Remaining blocker is unchanged: actual CLV field-to-divider/physical-domain mapping and true BIOS SoC control. Current P3-reported board metadata and saved P3 executable set are not CLV hardware acceptance. Do not rerun known log-only/cache/DPREFCLK checks as the next step.
