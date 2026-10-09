# CLV ABL1 item-0x17 reachable output edge

Date: 2026-09-21  
Evidence class: observed-bytes and static-analysis.

## Confirmed local edge

The exact CLV ABL1 caller reads context+0x2BC at 0x7E40 after the item-0x17 service call. At 0x7E74, it passes R0=R4 (caller context), R1=R5, and R2=R6 (the value read from +0x2BC) to 0x5E68. In 0x5E68, R4=R2; after local branching/reader work it writes a derived halfword to [R5+0x78] at 0x5FBA, where R5 is the input context saved from R0 at 0x5E70.

After 0x5E68 returns, the caller reads a halfword from [channel+0x20] at 0x7E7E and compares it with raw immediate 0x6D6. It conditionally updates a status byte at nested offset +0x74B; no write to channel+0x20 occurs at this instruction. The downstream selector/callback semantics are not assigned units or product names here.

## Branch and pointer qualifications

The earlier statement that helper 0x6D10 == 1 guarantees the 0x95FC -> 0x984E path is corrected. Independent review docs/research/2026-09-21-item17-reachability-review.md and its machine result (PASS, 128/128) show that after 0x6C20 writes 1 to [SP+0x164], 0x95FC calls fill helper 0x6B78 at 0x963A with destination R4+0x278, fill byte 0xFF, length 0x40. No address relation proves this range disjoint from SP+0x160..0x178. The BLS 0x9744 -> 0x984E route, its table read at 0x986E, and the consequent +0x2BC write at 0x989A are therefore conditional on no alias/clobber.

For the later outer-routine call, the fresh caller slice shows ADD.W R4,R4,#0x2C0 at 0x7F4C, followed by SUB.W R4,R4,#0x2C0 at 0x7FC2; arithmetic alone cancels. The code then loops through 0x843C and reaches 0x8418..0x8438. At 0x8420..0x8424, it loads [R4+0x0C], tests [channel+0x28], and skips the next call if that value is zero. If nonzero, 0x8426 copies the current R4 to R0 and 0x8428 calls 0x10200.

The object identity at 0x8428 is **not proven to be the same object passed at 0x7E74**. The path contains a conditional indirect dispatch at 0x83B0 -> 0x10958; prior bounded analysis shows 0x10958 branches through a callback pointer loaded from the current object’s +0x660, whose target/value is unresolved. The call argument can therefore be stated exactly as current R4 after the observed +0x2C0/-0x2C0 pair and intervening calls, but not promoted to a stable alias of the earlier context without resolving that callback path.

## Nearest field consumer and stop

In the bounded 0x10200 slice, R0 is copied to R4 at 0x10208; its local branch reaches LDRH R0,[R4,#0x78] at 0x107E4. It compares the raw halfword against 0x3E8 and 0x4B0, selects one of raw codes 0, 0x260, 0x264, 0x464, and calls 0x10958 at 0x10820. This establishes a downstream local reader only **if** the 0x8428 object is the same base that received the 0x5FBA store. It does not establish a hardware or training consumer: the closest dispatcher is indirect and its callback target/effect remains unresolved.

No frequency or clock unit is assigned. The exact earlier aggregate path remains conditional on the fill-range alias check; the 0x8428 branch is additionally conditional on [channel+0x28] != 0 and the current R4 object provenance.

## Fresh evidence

All new Thumb listings were generated from the copied exact ELF wrapper with /usr/bin/llvm-objdump LLVM 22.1.8; command ledgers record exit 0 and empty stderr:

- caller-post-item17.objdump (0x7E30..0x7EA0)
- exact-aggregate-producer.objdump (0x984E..0x98B0)
- aggregate-map-helper.objdump (0x751C..0x75A0)
- caller-next-helper.objdump (0x61A0..0x6260)
- caller-continuation.objdump (0x7E6E..0x7F40)
- aggregate-consumer-5e68.objdump (0x5E68..0x602C)
- caller-to-8428.objdump (0x7E3E..0x8450)
- fclk-field-consumer-10200.objdump (0x10200..0x10850)

The unique evidence directory is /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-reachable-output/. TARGET wrapper SHA-256 is adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6; pinned CLV ROM SHA-256 is ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8.

Machine-readable result: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-reachable-output/reachable-output-result.json. Final evidence checksums: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-reachable-output/SHA256SUMS.final. The report hash itself is recorded in the final manifest.

No ROM, firmware, NVRAM, register, hardware, network, install, or candidate write occurred. Rollback is deletion of this report and the unique evidence directory; retain the append-only action log.
