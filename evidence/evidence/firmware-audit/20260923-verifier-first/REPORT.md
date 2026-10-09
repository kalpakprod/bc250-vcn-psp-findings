# CLV verifier-first: executed checkpoint

Scope: user-approved offline verifier isolation, not RSA key recovery, not flashing. Input `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, unchanged. No firmware patch produced.

## Executed results

1. Existing `scripts/psp_ps1_verify.py IMAGE --blocks 0`: exit1,14 stock containers PASS,2 key-database carriers unresolved (public trust anchor not in local KDB),3 noncontainers. This is not an all-green image verdict. Literal outputs `psp-verify.stdout`/`.stderr`.
2. `python evidence/firmware-audit/20260923-verifier-first/crypto_controls.py`: exit0. For exact stock type02 and type28, original=ACCEPT, body-one-bit=REJECT, signature-one-bit=REJECT. All6 controls pass using public RSA keys and real PSS/SHA256/salt32. Changes in memory only. No private key generated, read or persisted. HOST crypto verification, NOT execution of native PSP verifier.
3. Extracted exact type02 signed body to `clv-t02-signed-body.bin`, signed length0x13150, excluding container header/signature. Imported into Ghidra12.1.3 ARM:LE:32:v8 at base0, seeded observed vector offsets0/4/8/12/16/24. One CPU,1GiB, analysis took4 seconds,390 discovered functions. Import and7 subsequent targeted inspections exit0. This is static analysis, not processor execution. Absolute user-component runtime relocation remains to reconstruct, so all following offsets are BODY offsets.
4. Confirmed by independent LLVM Thumb decode: body120EC maps a payload via SVC62, checks `$PS1` at payload+10, calls body115B8 at1212C. Other calls traced from code, not symbolic names.
5. Loader115B8 has a path calling EEAE (callsite116D4), checks its result and takes error0x34 on that path. This alone does not identify RSA verification.
6. EEAE builds request op0x1005 at stack+0 and value2 at+4. Native instructions EEE8/EEEA/EEEC set r0=1, r1=sp and issue SVC F2. It is an inter-component request boundary, not an inline RSA implementation. `service1005-disassembly.txt` records actual bytes decoded, instruction outputs and exit0.
7. Kernel SVC vector240 -> indirect pointer at3CC (4545, Thumb) -> dispatcher4544 -> high SVC handler5050. F2 performs permission checks and a context switch through runtime component metadata. Destination of service1/op1005 is NOT yet resolved. Returning fake success here would fail the requested experiment.
8. TOS SVC A6 ->37AC is mapped register read-modify-write via308C, not a cryptographic check. SVC7C ->5C44 is a width-selected store via the same mapping helper. These older VCN service leads are not the desired RSA verification function.

## Important analysis correction

Ghidra decompiler treats some software_interrupt paths as nonreturning and omits real post-SVC branches as unreachable. In120EC the raw LLVM decode includes CBNZ after SVC62 and the `$PS1` compare that disappeared from C output. Do not use the current C output alone for a patch or signature verdict. LLVM control-flow bytes are the evidence for those edges. Decompiler prototypes/extraout values remain inferred, not verified ABIs.

Type01 at8E0400,sizeB600: no `$PS1` header and entropy7.9962 bits/byte. This establishes opaque content, NOT proven encryption/compression or executable ISA. No blind ARM disassembly was accepted for that region. Previous categorical description of a directly analyzable type01 signature verifier was unjustified.

## State / next executable action

Native signature verifier NOT yet isolated; native valid/invalid signature experiment UNRUN. No bypass patch, no unlock, no hardware test. Host crypto controls are completed and must not be repeated as a substitute for native progress.

NEXT: resolve service1 descriptor/context for the exact TOS F2 request0x1005 and map its destination component to an existing CLV payload. Then recover its return-value/ABI and replay the same stock-valid/body-invalid/signature-invalid cases in the native function, stopping on unknown service/MMIO. Do not treat the register-write SVCs or gate-byte E18B70 as RSA verifier.

Evidence files reopened: crypto-controls.json, controls.stdout/stderr, tos-services.txt, tos-load-targets.txt, tos-verify-candidates.txt, ps1-loader-disassembly.txt, service1005-disassembly.txt. Ghidra scripts and project preserved for continuation.
