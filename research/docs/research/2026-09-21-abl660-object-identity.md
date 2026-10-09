# CLV ABL1 +0x660 initializer versus active consumer object

Date: 2026-09-21  
Evidence class: observed-bytes and static-analysis.

## Result

The initializer that writes field +0x660 receives its root object in R0 at entry 0x7378. It saves that value in R5, and at 0x74DE passes R5 in R0 to initializer 0xAF90. Within 0xAF90, R4 is initially copied from R0; after a temporary +0x3C adjustment, the writeback load at 0xB04E restores R4 to the incoming object base. No further R4 write intervenes before 0xB0C4, where the literal loaded from 0xB168 is stored at [R4+0x660]. Thus the initialized field belongs to the object pointer originally supplied as R0 to 0x7378.

The active consumer is different evidence: at 0x10958 it loads the current incoming R0 object's [R0+0x660] and tail-dispatches through that pointer. The item-0x660 report shows a separate active call path where current R4 is constructed from [R6+0x3C4], adjusted at 0x7F4C/0x7FC2, and passed to 0x10200. The new bounded search found no direct BL to 0x7378 in the retained exact full Thumb listing (grep exit 1, zero matches). This does not exclude an indirect or external invocation.

Therefore the actual initialized object and the active consumer object are not proven identical. The exact missing input is the caller or indirect dispatch target that enters 0x7378, including its R0 object pointer, together with a same-run or statically established identity relation to the R0 used by 0x10958. Until then, the existing 0x60BD9 -> 0x9AD8 association remains only the prior conditional static mapping; this report does not repeat it or claim it is the active callback.

## Register and field facts

- At 0x7378 entry: R5=R0 (initializer root), R6=R1, R8=R2, R4=R3. On the success path, [R5] receives R6, [R5+0x20] receives R4, [R5+0x4] receives [R6+0x28], and [R5+0x8] receives [R6+0x3C4].
- At 0x74DE, R0=R5 and BL 0xAF90. The fresh 0xAF90 window shows R4=R0 at 0xAF94, R4=R4+0x3C at 0xAFA8, then LDR R3,[R4,#-0x3C]! at 0xB04E writes R4 back to the original root. At 0xB0C4 it stores the value loaded from 0xB168 to [R4+0x660].
- In 0x10958, the input R0 is retained. The dispatcher loads [R0+0x660] into R4, moves input R1 to R2 and input R2 to R3, sets R1=1, then BX R12. This is the observed register-level callback ABI; it does not establish which object base or callback value was active at runtime.
- The existing callback-field report/result already disassembled candidate body 0x9AD8 and reports 97/97 checks. Reuse that evidence rather than repeating its conditional pointer mapping or body scan.

## Reproduction and limits

New bounded LLVM 22.1.8 Thumb windows:

- Initializer entry: 0x7378..0x7500, exit 0, stderr empty.
- Initializer/store: 0xAF90..0xB0D0, exit 0, stderr empty.
- Active field reader: 0x10958..0x1096C, exit 0, stderr empty.
- Exact direct-call search for BL 0x7378 in the existing pinned full listing: exit 1, zero matches. This only rejects a direct BL in that listing; indirect and external invocation remain possible.

No active constructor caller, R0 root-object value, runtime load base, field identity, hardware behavior, or callback effect is established. No frequency unit, training outcome, or physical-clock claim is made. No ROM, firmware, NVRAM, register, hardware, network, install, or candidate write occurred.

Evidence directory: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl660-object-identity/. Existing detailed report: /home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-context660-callback-xhigh.md.
