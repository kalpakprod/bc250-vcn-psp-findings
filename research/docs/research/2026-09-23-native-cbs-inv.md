# Native CbsBasePei acquisition to `$INV` serialization

The unchanged IA32 instructions of `CbsBasePei` were executed in a bounded user-process harness. Four controlled acquisition modes were rebuilt from one template. A copied acquired buffer was passed to serializer `0x36F0`, with no platform callback dispatch and no board I/O.

| Input mode             | Selected requests serialized                                                                   |
| ---------------------- | ---------------------------------------------------------------------------------------------- |
| Live variable succeeds | MCLK enum `35`, Tcl `16`, UCLK `1`, DRAM control `1`, VDD control `1`, VDD raw `80`, DF `1750` |
| Variable missing       | `255,255,255,15,0,0,255,1000` fallback values                                                  |
| Wrong size probe       | same fallback                                                                                  |
| Second read fails      | same fallback                                                                                  |

The serializer emits `$INV` records. Seven target tokens are found with the expected types: `0x11ED` (MCLK), `0x1204` (UCLK), `0x1331` (FCLK DPM), `0x1363/0x1364` (VDD offset control/value), `0x1373/0x1374` (DF control/value). It walks 1122 records. Required buffer capacity is `0x1605` (5637), and the constructed stream length is `5628`, so the observed writes fit.

All four modes, assembler/linker commands, eight exact module-section readbacks and the verifier exit `0` pass. Evidence: `evidence/firmware-audit/20260923-native-cbs-inv/result.json`, `verifier.stdout`, `verifier.stderr`, `verifier.exit`.

This closes the acquisition-to-serialization boundary under controlled PEI inputs. It does not prove which input branch the board selected, that `$INV` reaches a clock actuator, or that a VDD offset changes the physical SoC rail. No firmware file or hardware state changed. The harness's fallback cases are controlled statuses, not observations of the participant's board.

## Output correction

Only seven token values were captured by this serializer test: MCLK, UCLK, FCLK DPM, VDD control, VDD raw offset, DF control, DF request. Tcl, DRAM Timing User Controls and Memory P-state were NOT captured in this run. The previous prose table and chat listing mixed them with acquisition evidence and are superseded by result.json. Exact live values: 35/1/0/1/80/1/1750. Exact fallback: 255/255/15/0/0/255/1000.
