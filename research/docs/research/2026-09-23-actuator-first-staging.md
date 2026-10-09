# P2: first output-side causal test, VR command staging

The isolated ISL69247 helper at RVA6ED was executed with only two test instrumentation sites: helper565 jumps to a memory trace stub, and site733 stops before delay/poll. All other module bytes match the original. No ROM image was built and no hardware port instruction executed. This is explicitly instrumented execution, not an unchanged full PEIM run.

Input register index21, synthetic input word0123:

```text
65 <- C0
66 <- 21
70 <- 23
71 <- 01
63 <- 03
60 <- C0
```

Changing only the word to0456 changes only staging bytes70/71 to56/04. Restoring0123 restores the original six-write trace. Three processes exit0, stderr empty. Exact noninstrumented-byte comparisons pass for each executable.

Static caller link: ISL69247+30F tests Setup+1C9 enable, +314 loads Setup+1CA word, +31B calls6ED after pushing register21. These are VCORE-labelled controls. They must NOT be relabelled SoC. This experiment proves word-to-command staging only, not the physical transfer function, chip response, boot dispatch or safe voltage.

Artifacts: evidence/firmware-audit/20260923-actuator-first/staging.s and staging-result.json. Assembly/linker/dump-section/execution command results and exact instrumentation spans are included. No model-installed dependency or hardware load.

Next: extend this narrowly to the actual enable/control caller and then classify destination rail with existing board/controller evidence. Clock actuator branch still separate and open. Do not repeat generic INV parsing.
