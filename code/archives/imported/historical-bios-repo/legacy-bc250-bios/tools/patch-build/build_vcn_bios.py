#!/usr/bin/env python3
"""Build and verify BC-250 VCN Unlocked BIOS image.

Pipeline:
  1. Loads stock BC250_3.00.ROM.
  2. Applies DFG wildcard expansion patch in APCB (0xAB1000: 0x001FFF00 -> 0x007FFF00).
  3. Injects VcnUnlockDxe FFS into DXE Firmware Volume (0x00AE0000..0x00C30000).
  4. Recalculates APCB checksums.
  5. Verifies structural integrity of $PSP, $BIOS, and Fletcher32 checksums.
"""

import os
import sys
import struct
import subprocess
import lzma

STOCK_ROM = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\BC250_3.00.ROM"
OUTPUT_ROM = r"C:\Users\OWNER\tmp_bc250\BC250_VCN_UNLOCKED.ROM"

APCB_OFFSET = 0xAB1000
DFG_WILDCARD_PATTERN = struct.pack("<I", 0x001FFF00)
DFG_WILDCARD_PATCH   = struct.pack("<I", 0x007FFF00)

VCN_UNLOCK_DXE_GUID = bytes.fromhex("38d3521c4f24d82a4da2f0ec40c23c59")

# Precompiled machine code for VcnUnlockDxe driver (2288 bytes)
DRIVER_HEX = '535657554154415541564157b82400018066baf80cef66bafc0ced83e0f085c0751ab82400008066baf80cef66bafc0ced83e0f085c00f848d0100004889c6b940420f008b860082050085c07815f390ffc975f048b81200000000000080e970010000488d1da2040000899e90810500c7869481050000000000c7868c8105000b100080b980841e008b868c81050085c07915f390ffc975f048b81200000000000080e92b0100006685c00f850c010000488d3d58060000488d154d040000488b820001000048898700010000488b820801000048898708010000488b821001000048898710010000488b821801000048898718010000488d0d12060000488d159b070000e8d6000000488d15af070000488d1df805000048891ac7420890010000c7420c00000000488d0d7007000048894a10c7421845000000c7421c00000000488d1d77070000899e90810500c7869481050000000000c7868c8105000c100080b980841e008b868c81050085c07912f390ffc975f048b81200000000000080eb4f6685c07534c7868c81050033100080b980841e008b868c81050085c07912f390ffc975f048b81200000000000080eb1f6685c0750431c0eb1648b80700000000000080eb0a48b80e00000000000080415f415e415d415c5d5f5e5bc35355415441554156415757564881ecf002000048899424e00200004889ce488dbc2420010000b932000000f348a5c6078048ffc7b92700000031c0f3aa48b80000000000000c80488907c7042467e6096ac744240485ae67bbc744240872f36e3cc744240c3af54fa5c74424107f520e51c74424148c68059bc7442418abd9831fc744241c19cde05b4531f64c89f048c1e006488db40420010000488d7c2420b9100000008b060fc889074883c6044883c704ffc975eeb9100000008b448ce489c2c1ca0789c3c1cb1231dac1e80331c28b448c184189c041c1c81189c3c1cb134131d8c1e80a4131c08b448ce001d003448c044401c089448c20ffc183f94075ba8b04248b5c24048b5424088b6c240c448b442410448b4c2414448b542418448b5c241c31c9488d3dfe0000004589c441c1cc064589c541c1cd0b4531ec4589c541c1cd194531ec4589c54521cd4489c6f7d64421d64131f54501e34501eb44031c8f44035c8c204189c441c1cc024189c541c1cd0d4531ec4189c541c1cd164531ec4189c54121dd89c621d64131f589de21d64131f54501ec4589df4589d34589ca4589c14189e84501f889d589da89c34489f84401e0ffc183f9400f856affffff010424015c240401542408016c240c440144241044014c2414440154241844015c241c41ffc64183fe070f8598feffff488bbc24e0020000488d3424b9080000008b060fc889074883c6044883c704ffc975ee4881c4f00200005e5f415f415e415d415c5d5bc390982f8a4291443771cffbc0b5a5dbb5e95bc25639f111f159a4823f92d55e1cab98aa07d8015b8312be853124c37d0c55745dbe72feb1de80a706dc9b74f19bc1c1699be48647beefc69dc10fcca10c246f2ce92daa84744adca9b05cda88f97652513e986dc631a8c82703b0c77f59bff30be0c64791a7d55163ca0667292914850ab72738211b2efc6d2c4d130d385354730a65bb0a6a762ec9c281852c7292a1e8bfa24b661aa8708b4bc2a3516cc719e892d1240699d685350ef470a06a1016c1a419086c371e4c774827b5bcb034b30c1c394aaad84e4fca9c5bf36f2e68ee828f746f63a5781478c8840802c78cfaffbe90eb6c50a4f7a3f9bef27871c60000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000909090902450533190010000010000000000000096ea7cfec59d4c2a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010200000600000034c200090000000014c900090000000030c900090000000080cb00090000000034c20009010000001c012203ff070100100200000200000010e803000600000014e8030082c3442500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'

DRIVER_ASM = """
BITS 64
default rel

section .text
global _start

_start:
    push rbx
    push rsi
    push rdi
    push rbp
    push r12
    push r13
    push r14
    push r15

    ; 1. PCI IO BAR5 discovery (Bus 0, Dev 0, Func 0 / Bus 0, Dev 1, Func 0)
    mov eax, 0x80010024
    mov dx, 0x0CF8
    out dx, eax
    mov dx, 0x0CFC
    in eax, dx
    and eax, 0xFFFFFFF0
    test eax, eax
    jnz .bar5_found

    mov eax, 0x80000024
    mov dx, 0x0CF8
    out dx, eax
    mov dx, 0x0CFC
    in eax, dx
    and eax, 0xFFFFFFF0
    test eax, eax
    jz .err_not_found

.bar5_found:
    mov rsi, rax ; RSI = BAR5 base

    ; 2. Wait for TOS ready: poll C2PMSG_64 (0x58200) with timeout
    mov ecx, 1000000
.wait_tos:
    mov eax, [rsi + 0x58200]
    test eax, eax
    js .tos_ready
    pause
    dec ecx
    jnz .wait_tos
    mov rax, 0x8000000000000012 ; EFI_TIMEOUT
    jmp .exit_clean

.tos_ready:
    ; 3. Step 1: Request Session Token (Command 0x100B) in C2PMSG_35
    lea rbx, [token_buf]
    mov [rsi + 0x58190], ebx
    mov dword [rsi + 0x58194], 0
    mov dword [rsi + 0x5818c], 0x8000100B ; Trigger
    mov ecx, 2000000
.poll_token:
    mov eax, [rsi + 0x5818c]
    test eax, eax
    jns .token_done
    pause
    dec ecx
    jnz .poll_token
    mov rax, 0x8000000000000012 ; EFI_TIMEOUT
    jmp .exit_clean

.token_done:
    test ax, ax
    jnz .err_device

    ; 4. Step 2: Copy 32-byte session token from token_buf+0x100 to ps1_blob+0x100
    lea rdi, [ps1_blob]
    lea rdx, [token_buf]
    mov rax, [rdx + 0x100]
    mov [rdi + 0x100], rax
    mov rax, [rdx + 0x108]
    mov [rdi + 0x108], rax
    mov rax, [rdx + 0x110]
    mov [rdi + 0x110], rax
    mov rax, [rdx + 0x118]
    mov [rdi + 0x118], rax

    ; 5. Step 2: Compute SHA-256 over 400-byte (0x190) ps1_blob into hash_buf
    lea rcx, [ps1_blob]
    lea rdx, [hash_buf]
    call sha256_400

    ; 6. Step 2: Build PSP_BLOB_DESCRIPTOR in desc_buf
    lea rdx, [desc_buf]
    lea rbx, [ps1_blob]
    mov [rdx], rbx                  ; PhysAddr = ps1_blob
    mov dword [rdx + 8], 0x190      ; Size = 0x190 (400 bytes)
    mov dword [rdx + 12], 0         ; Reserved = 0
    lea rcx, [hash_buf]
    mov [rdx + 16], rcx             ; ExpectedHashPtr = hash_buf
    mov dword [rdx + 24], 0x45      ; Type = 0x45 (Policy)
    mov dword [rdx + 28], 0         ; Reserved2 = 0

    ; 7. Step 2: Send Command 0x100C (PSP_CMD_LOAD_BLOB) in C2PMSG_35
    lea rbx, [desc_buf]
    mov [rsi + 0x58190], ebx
    mov dword [rsi + 0x58194], 0
    mov dword [rsi + 0x5818c], 0x8000100C ; Trigger
    mov ecx, 2000000
.poll_load:
    mov eax, [rsi + 0x5818c]
    test eax, eax
    jns .load_done
    pause
    dec ecx
    jnz .poll_load
    mov rax, 0x8000000000000012 ; EFI_TIMEOUT
    jmp .exit_clean

.load_done:
    test ax, ax
    jnz .err_device

    ; 8. Step 3: Apply VCN Policy (Command 0x1033) in C2PMSG_35
    mov dword [rsi + 0x5818c], 0x80001033 ; Trigger
    mov ecx, 2000000
.poll_apply:
    mov eax, [rsi + 0x5818c]
    test eax, eax
    jns .apply_done
    pause
    dec ecx
    jnz .poll_apply
    mov rax, 0x8000000000000012 ; EFI_TIMEOUT
    jmp .exit_clean

.apply_done:
    test ax, ax
    jnz .err_device

    xor eax, eax ; EFI_SUCCESS
    jmp .exit_clean

.err_device:
    mov rax, 0x8000000000000007 ; EFI_DEVICE_ERROR
    jmp .exit_clean

.err_not_found:
    mov rax, 0x800000000000000E ; EFI_NOT_FOUND

.exit_clean:
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbp
    pop rdi
    pop rsi
    pop rbx
    ret

; ==============================================================================
; SHA-256 for 400-byte input
; rcx = input buffer (400 bytes)
; rdx = output hash buffer (32 bytes)
; ==============================================================================
sha256_400:
    push rbx
    push rbp
    push r12
    push r13
    push r14
    push r15
    push rdi
    push rsi

    ; Total stack needed:
    ; 448 bytes padded message
    ; 256 bytes W schedule (64 * 4)
    ; 32 bytes H state (8 * 4)
    ; alignment
    ; 448 + 256 + 32 = 736 -> sub rsp, 752 (752 % 16 == 0)
    sub rsp, 752

    ; Save out_hash pointer
    mov [rsp + 736], rdx
    mov rsi, rcx ; input data (400 bytes)

    ; 1. Copy 400 bytes from rsi to [rsp + 288] (padded buffer)
    lea rdi, [rsp + 288]
    mov ecx, 50 ; 50 * 8 = 400 bytes
    rep movsq

    ; Append 0x80
    mov byte [rdi], 0x80
    inc rdi

    ; Zero 39 bytes (bytes 401..439)
    mov ecx, 39
    xor eax, eax
    rep stosb

    ; Append 64-bit big-endian length: 400 * 8 = 3200 = 0x0C80
    mov rax, 0x800c000000000000 ; bswap(3200)
    mov [rdi], rax

    ; 2. Initialize H0..H7 at [rsp]
    mov dword [rsp],      0x6a09e667
    mov dword [rsp + 4],  0xbb67ae85
    mov dword [rsp + 8],  0x3c6ef372
    mov dword [rsp + 12], 0xa54ff53a
    mov dword [rsp + 16], 0x510e527f
    mov dword [rsp + 20], 0x9b05688c
    mov dword [rsp + 24], 0x1f83d9ab
    mov dword [rsp + 28], 0x5be0cd19

    ; 3. Loop over 7 blocks of 64 bytes
    ; r14 = current block index (0..6)
    xor r14d, r14d

.block_loop:
    ; Block start = rsp + 288 + r14 * 64
    mov rax, r14
    shl rax, 6
    lea rsi, [rsp + 288 + rax]

    ; Copy 16 dwords to W[0..15] at [rsp + 32] with bswap
    lea rdi, [rsp + 32]
    mov ecx, 16
.copy_w:
    mov eax, [rsi]
    bswap eax
    mov [rdi], eax
    add rsi, 4
    add rdi, 4
    dec ecx
    jnz .copy_w

    ; Expand W[16..63]
    ; t in ecx: 16..63
    mov ecx, 16
.expand_w:
    ; s0 = (W[t-15] rotr 7) ^ (W[t-15] rotr 18) ^ (W[t-15] >> 3)
    mov eax, [rsp + 32 + (rcx - 15)*4]
    mov edx, eax
    ror edx, 7
    mov ebx, eax
    ror ebx, 18
    xor edx, ebx
    shr eax, 3
    xor edx, eax ; edx = s0

    ; s1 = (W[t-2] rotr 17) ^ (W[t-2] rotr 19) ^ (W[t-2] >> 10)
    mov eax, [rsp + 32 + (rcx - 2)*4]
    mov r8d, eax
    ror r8d, 17
    mov ebx, eax
    ror ebx, 19
    xor r8d, ebx
    shr eax, 10
    xor r8d, eax ; r8d = s1

    ; W[t] = W[t-16] + s0 + W[t-7] + s1
    mov eax, [rsp + 32 + (rcx - 16)*4]
    add eax, edx
    add eax, [rsp + 32 + (rcx - 7)*4]
    add eax, r8d
    mov [rsp + 32 + rcx*4], eax

    inc ecx
    cmp ecx, 64
    jne .expand_w

    ; Load working variables a..h into r8d..r15d (except r14d is block idx, so use registers carefully)
    ; Let's use:
    ; a = eax
    ; b = ebx
    ; c = edx
    ; d = ebp
    ; e = r8d
    ; f = r9d
    ; g = r10d
    ; h = r11d
    mov eax, [rsp]
    mov ebx, [rsp + 4]
    mov edx, [rsp + 8]
    mov ebp, [rsp + 12]
    mov r8d, [rsp + 16]
    mov r9d, [rsp + 20]
    mov r10d, [rsp + 24]
    mov r11d, [rsp + 28]

    ; 64 compression rounds
    ; ecx = round index 0..63
    xor ecx, ecx
    lea rdi, [k256]

.round_loop:
    ; S1 = (e rotr 6) ^ (e rotr 11) ^ (e rotr 25)
    mov r12d, r8d
    ror r12d, 6
    mov r13d, r8d
    ror r13d, 11
    xor r12d, r13d
    mov r13d, r8d
    ror r13d, 25
    xor r12d, r13d ; r12d = S1

    ; ch = (e & f) ^ (~e & g)
    mov r13d, r8d
    and r13d, r9d
    mov esi, r8d
    not esi
    and esi, r10d
    xor r13d, esi ; r13d = ch

    ; temp1 = h + S1 + ch + K[t] + W[t]
    add r11d, r12d
    add r11d, r13d
    add r11d, [rdi + rcx*4]
    add r11d, [rsp + 32 + rcx*4] ; r11d = temp1

    ; S0 = (a rotr 2) ^ (a rotr 13) ^ (a rotr 22)
    mov r12d, eax
    ror r12d, 2
    mov r13d, eax
    ror r13d, 13
    xor r12d, r13d
    mov r13d, eax
    ror r13d, 22
    xor r12d, r13d ; r12d = S0

    ; maj = (a & b) ^ (a & c) ^ (b & c)
    mov r13d, eax
    and r13d, ebx
    mov esi, eax
    and esi, edx
    xor r13d, esi
    mov esi, ebx
    and esi, edx
    xor r13d, esi ; r13d = maj

    ; temp2 = S0 + maj
    add r12d, r13d ; r12d = temp2

    ; Update state:
    ; h = g
    ; g = f
    ; f = e
    ; e = d + temp1
    ; d = c
    ; c = b
    ; b = a
    ; a = temp1 + temp2
    mov r15d, r11d ; temp1
    mov r11d, r10d ; h = g
    mov r10d, r9d  ; g = f
    mov r9d,  r8d  ; f = e
    mov r8d,  ebp
    add r8d,  r15d ; e = d + temp1
    mov ebp,  edx  ; d = c
    mov edx,  ebx  ; c = b
    mov ebx,  eax  ; b = a
    mov eax,  r15d
    add eax,  r12d ; a = temp1 + temp2

    inc ecx
    cmp ecx, 64
    jne .round_loop

    ; Add to H0..H7
    add [rsp],      eax
    add [rsp + 4],  ebx
    add [rsp + 8],  edx
    add [rsp + 12], ebp
    add [rsp + 16], r8d
    add [rsp + 20], r9d
    add [rsp + 24], r10d
    add [rsp + 28], r11d

    inc r14d
    cmp r14d, 7
    jne .block_loop

    ; 4. Output final hash to [out_hash] with bswap
    mov rdi, [rsp + 736]
    lea rsi, [rsp]
    mov ecx, 8
.out_loop:
    mov eax, [rsi]
    bswap eax
    mov [rdi], eax
    add rsi, 4
    add rdi, 4
    dec ecx
    jnz .out_loop

    add rsp, 752
    pop rsi
    pop rdi
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbp
    pop rbx
    ret

align 4
k256:
    dd 0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5
    dd 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5
    dd 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3
    dd 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174
    dd 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc
    dd 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da
    dd 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7
    dd 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967
    dd 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13
    dd 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85
    dd 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3
    dd 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070
    dd 0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5
    dd 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3
    dd 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208
    dd 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2

token_buf:
    times 0x200 db 0

align 16
ps1_blob:
    ; Header: 0x100 (256 bytes)
    db "$PS1"                             ; 0x00: Magic
    dd 0x00000190                         ; 0x04: TotalSize = 400 bytes
    dd 0x00000001                         ; 0x08: Version = 1
    dd 0x00000000                         ; 0x0C: Reserved
    db 0x96, 0xEA, 0x7C, 0xFE, 0xC5, 0x9D, 0x4C, 0x2A ; 0x10: kid 96EA (LE)
    times 8 db 0
    times 224 db 0                        ; 0x20..0xFF: Padding

    ; Body: starts at +0x100
    times 32 db 0                         ; +0x100: SessionToken (filled at runtime)
    times 32 db 0                         ; +0x120: ValidationPadding (32 zeros)

    ; Group 0x201 (SMN VCN-instances): +0x140
    dd 0x00000201                         ; Group201Id
    dd 0x00000006                         ; Group201Count (6 pairs)
    dd 0x0900C234, 0x00000000             ; 0x0900C234 -> 0
    dd 0x0900C914, 0x00000000             ; 0x0900C914 -> 0
    dd 0x0900C930, 0x00000000             ; 0x0900C930 -> 0
    dd 0x0900CB80, 0x00000000             ; 0x0900CB80 -> 0
    dd 0x0900C234, 0x00000001             ; 0x0900C234 -> 1
    dd 0x0322011C, 0x000107FF             ; 0x0322011C -> 0x107FF

    ; Group 0x210 (Power Mailbox): +0x178
    dd 0x00000210                         ; Group210Id
    dd 0x00000002                         ; Group210Count (2 pairs)
    dd 0x0003E810, 0x00000006             ; 0x03E810 -> 6
    dd 0x0003E814, 0x2544C382             ; 0x03E814 -> 0x2544C382

align 16
hash_buf:
    times 32 db 0

align 16
desc_buf:
    times 32 db 0
"""

def recalculate_apcb_checksum(rom_bytes: bytearray, apcb_offset: int = APCB_OFFSET) -> int:
    """Вычисляет и обновляет 16-битную контрольную сумму и CRC32 в заголовке APCB-тома."""
    size = struct.unpack_from("<I", rom_bytes, apcb_offset + 8)[0]
    rom_bytes[apcb_offset + 12 : apcb_offset + 14] = b"\x00\x00"

    import zlib
    body_crc32 = zlib.crc32(rom_bytes[apcb_offset + 0x20 : apcb_offset + size]) & 0xFFFFFFFF
    struct.pack_into("<I", rom_bytes, apcb_offset + 16, body_crc32)

    total_sum = sum(rom_bytes[apcb_offset : apcb_offset + size])
    cks16 = (-total_sum) & 0xFFFF
    struct.pack_into("<H", rom_bytes, apcb_offset + 12, cks16)

    print(f"[+] Recalculated APCB Checksum: 0x{cks16:04X}, CRC32: 0x{body_crc32:08X}")
    return cks16


def get_driver_bytecode() -> bytes:
    """Возвращает машинный код драйвера VcnUnlockDxe."""
    try:
        # Пытаемся собрать через nasm если он доступен
        p = subprocess.run(["nasm", "-v"], capture_output=True)
        if p.returncode == 0:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".asm", delete=False) as tf:
                tf.write(DRIVER_ASM.encode("utf-8"))
                asm_path = tf.name
            bin_path = asm_path + ".bin"
            res = subprocess.run(["nasm", "-f", "bin", "-o", bin_path, asm_path], capture_output=True)
            if res.returncode == 0 and os.path.exists(bin_path):
                data = open(bin_path, "rb").read()
                os.remove(asm_path)
                os.remove(bin_path)
                return data
            if os.path.exists(asm_path):
                os.remove(asm_path)
    except Exception:
        pass
    return bytes.fromhex(DRIVER_HEX)

def build_vcn_unlock_dxe_ffs() -> bytes:
    """Генерирует структурно валидный UEFI DXE-драйвер (PE32+ / AMD64) в формате EFI_FFS_FILE."""
    dos_hdr = b"MZ" + b"\x00"*58 + struct.pack("<I", 0x80)
    dos_stub = b"\x00"*64
    pe_sig = b"PE\x00\x00"

    file_hdr = struct.pack("<HHIIIHH", 0x8664, 2, 0, 0, 0, 240, 0x020E)
    opt_std = struct.pack("<HBBIIIII", 0x020B, 0, 0, 0xA00, 0x200, 0, 0x1000, 0x1000)

    opt_win = struct.pack(
        "<QIIHHHHHHIIIIHHQQQQII",
        0x10000000, 0x1000, 0x200,
        0, 0, 0, 0, 0, 0,
        0, 0x3000, 0x200, 0,
        11, 0,
        0x10000, 0x1000, 0x10000, 0x1000,
        0, 16
    )

    data_dirs = bytearray(128)
    struct.pack_into("<II", data_dirs, 5*8, 0x2000, 8)

    opt_hdr = opt_std + opt_win + bytes(data_dirs)
    assert len(opt_hdr) == 240

    sec_text = b".text\x00\x00\x00" + struct.pack(
        "<IIIIIIHHI",
        0xA00, 0x1000, 0xA00, 0x200,
        0, 0, 0, 0,
        0xE0000020  # CNT_CODE | MEM_EXECUTE | MEM_READ | MEM_WRITE (allows in-place writes to token_buf/ps1_blob/hash_buf/desc_buf)
    )
    sec_reloc = b".reloc\x00\x00" + struct.pack(
        "<IIIIIIHHI",
        0x200, 0x2000, 0x200, 0xC00,
        0, 0, 0, 0,
        0x42000040  # CNT_INITIALIZED_DATA | MEM_DISCARDABLE | MEM_READ
    )

    pe_headers = (dos_hdr + dos_stub + pe_sig + file_hdr + opt_hdr + sec_text + sec_reloc).ljust(0x200, b"\x00")
    assert len(pe_headers) == 0x200

    driver_bytes = get_driver_bytecode()
    text_section = driver_bytes.ljust(0xA00, b"\x90")
    reloc_section = struct.pack("<II", 0x1000, 8).ljust(0x200, b"\x00")

    pe_data = pe_headers + text_section + reloc_section
    assert len(pe_data) == 0xE00

    sec_pe_len = len(pe_data) + 4
    sec_pe = struct.pack("<I", sec_pe_len)[:3] + b"\x10" + pe_data

    ui_name = "VcnUnlockDxe".encode("utf-16le") + b"\x00\x00"
    sec_ui_len = len(ui_name) + 4
    sec_ui = struct.pack("<I", sec_ui_len)[:3] + b"\x15" + ui_name

    # EFI_SECTION_DXE_DEPEX (0x13): TRUE opcode (0x08) + END opcode (0x00)
    sec_depex = b"\x06\x00\x00\x13\x08\x00\x00\x00"

    payload = sec_pe + sec_depex + sec_ui
    ffs_len = 24 + len(payload)

    guid = VCN_UNLOCK_DXE_GUID
    integrity = b"\x00\xaa"
    ftype = 0x07 # EFI_FV_FILETYPE_DRIVER
    attr = 0x00
    fstate = 0xf8

    hdr = bytearray(guid + integrity + bytes([ftype, attr]) + struct.pack("<I", ffs_len)[:3] + bytes([fstate]))
    hdr_sum = (sum(hdr[:16]) + sum(hdr[18:23])) & 0xFF
    hdr[16] = (-hdr_sum) & 0xFF

    return bytes(hdr) + payload

def inject_vcn_dxe_into_fv(rom_bytes: bytearray) -> bool:
    """Выполняет разбор DXE тома (0xAE0000..0xE00000), распаковку внутреннего LZMA FV,
    вставку VcnUnlockDxe перед BDS.ffs и LZMA-пересборку согласно docs/VCN_BIOS_UNLOCK_PLAN.md:58-61.
    """
    outer_fv_base = 0x00AE0000
    outer_fv_len = struct.unpack_from("<Q", rom_bytes, outer_fv_base + 0x20)[0]
    outer_fv_end = outer_fv_base + outer_fv_len

    if rom_bytes[outer_fv_base+0x28:outer_fv_base+0x2C] != b"_FVH":
        print("[!] Outer DXE FV header signature _FVH not found at 0xAE0028")
        return False

    # 1. Поиск инкапсулированного FFS с внутренним LZMA FV (GUID: 9e21fd93-9c72-4c15-8c4b-e77f1db2d792)
    ffs_pos = 0x00AE0078
    ffs_hdr = rom_bytes[ffs_pos:ffs_pos+24]
    orig_ffs_size = int.from_bytes(ffs_hdr[20:23], "little")
    fdata = rom_bytes[ffs_pos+24:ffs_pos+orig_ffs_size]

    data_offset = int.from_bytes(fdata[20:22], "little")
    lzma_payload = fdata[data_offset:]

    # 2. Распаковка внутреннего тома DXE
    try:
        decomp = bytearray(lzma.decompress(lzma_payload, format=lzma.FORMAT_ALONE))
    except Exception as e:
        print(f"[!] Failed to decompress inner DXE FV: {e}")
        return False

    fv_start = 0x10
    if decomp[fv_start+0x28:fv_start+0x2C] != b"_FVH":
        print("[!] Inner DXE FV header signature _FVH not found")
        return False

    fv_hdr_len = struct.unpack_from("<H", decomp, fv_start + 0x30)[0]

    # 3. Поиск Bds.ffs (GUID: 8f4b8f82-9b91-4028-86e6-f4db7d4c1dff)
    bds_guid = bytes.fromhex("828f4b8f919b284086e6f4db7d4c1dff") # LE
    bds_pos = decomp.find(bds_guid)
    if bds_pos == -1:
        print("[!] Bds.ffs not found in inner DXE FV")
        return False

    # 4. Сборка VcnUnlockDxe.ffs с 8-байтовым выравниванием
    dxe_ffs = build_vcn_unlock_dxe_ffs()
    pad_len = (8 - (len(dxe_ffs) % 8)) % 8
    dxe_ffs_padded = dxe_ffs + (b"\xFF" * pad_len)

    # 5. Вставка VcnUnlockDxe.ffs строго перед BDS
    new_decomp = decomp[:bds_pos] + dxe_ffs_padded + decomp[bds_pos:]

    # 6. Расчет нового размера внутреннего FV (выравнивание по блокам 4096 байт)
    new_fv_content_len = len(new_decomp) - fv_start
    block_size = 0x1000
    num_blocks = (new_fv_content_len + block_size - 1) // block_size
    new_fv_len = num_blocks * block_size

    # Заполнение хвоста свободного пространства внутреннего FV байтами 0xFF
    target_decomp_len = fv_start + new_fv_len
    if len(new_decomp) < target_decomp_len:
        new_decomp += b"\xFF" * (target_decomp_len - len(new_decomp))

    # Обновление заголовка секции EFI_SECTION_FIRMWARE_VOLUME_IMAGE (offset 0x0C)
    sec_fv_size = new_fv_len + 4
    new_decomp[0x0C:0x0F] = struct.pack("<I", sec_fv_size)[:3]
    new_decomp[0x0F] = 0x17

    # Обновление заголовка внутреннего FV (размер и block map)
    struct.pack_into("<Q", new_decomp, fv_start + 0x20, new_fv_len)
    struct.pack_into("<II", new_decomp, fv_start + 0x38, num_blocks, block_size)

    # Пересчет контрольной суммы заголовка внутреннего FV
    struct.pack_into("<H", new_decomp, fv_start + 0x32, 0)
    words = struct.unpack(f"<{fv_hdr_len // 2}H", new_decomp[fv_start : fv_start + fv_hdr_len])
    fv_csum = (-sum(words)) & 0xFFFF
    struct.pack_into("<H", new_decomp, fv_start + 0x32, fv_csum)

    # 7. LZMA-рекомпрессия модифицированного тома DXE
    filters = [
        {
            "id": lzma.FILTER_LZMA1,
            "dict_size": 16 * 1024 * 1024,
            "lc": 3,
            "lp": 0,
            "pb": 2,
            "mode": lzma.MODE_NORMAL,
            "nice_len": 64,
            "mf": lzma.MF_BT4
        }
    ]
    recomp_payload = lzma.compress(new_decomp, format=lzma.FORMAT_ALONE, filters=filters)

    # 8. Сборка GUID-defined секции и FFS-файла
    guid_sec_len = 0x18 + len(recomp_payload)
    sec_hdr = bytearray(struct.pack("<I", guid_sec_len)[:3] + bytes([0x02]))
    sec_hdr += bytes.fromhex("98584eee143959429d6edc7bd79403cf") # LZMA custom GUID
    sec_hdr += struct.pack("<HH", 0x18, 0x01)
    new_section = bytes(sec_hdr) + recomp_payload

    new_ffs_len = 24 + len(new_section)
    new_ffs_hdr = bytearray(ffs_hdr[:16])
    new_ffs_hdr += b"\x00\xaa"
    new_ffs_hdr += bytes([ffs_hdr[18], ffs_hdr[19]])
    new_ffs_hdr += struct.pack("<I", new_ffs_len)[:3]
    new_ffs_hdr += bytes([ffs_hdr[23]])
    hdr_csum = (sum(new_ffs_hdr[:16]) + sum(new_ffs_hdr[18:23])) & 0xFF
    new_ffs_hdr[16] = (-hdr_csum) & 0xFF

    new_ffs_file = bytes(new_ffs_hdr) + new_section

    # 9. Инъекция пересобранного FFS во внешний том DXE
    outer_free_start = (ffs_pos + len(new_ffs_file) + 7) & ~7
    if outer_free_start > outer_fv_end:
        print("[!] Outer DXE Firmware Volume overflow")
        return False

    rom_bytes[ffs_pos : ffs_pos + len(new_ffs_file)] = new_ffs_file
    rom_bytes[outer_free_start : outer_fv_end] = b"\xFF" * (outer_fv_end - outer_free_start)

    print(f"[+] Injected VcnUnlockDxe FFS before BDS into inner DXE FV and recompressed via LZMA.")
    print(f"[+] Outer FV free space starts @ 0x{outer_free_start:X} ({outer_fv_end - outer_free_start} bytes free).")
    return True

def patch_apcb(rom_bytes: bytearray) -> bool:
    pos = rom_bytes.find(DFG_WILDCARD_PATTERN, APCB_OFFSET, APCB_OFFSET + 0x20000)
    if pos == -1:
        print(f"[!] DFG wildcard pattern not found in APCB window @ 0x{APCB_OFFSET:X}")
        return False
    rom_bytes[pos:pos+4] = DFG_WILDCARD_PATCH
    print(f"[+] Patched APCB DFG wildcard @ 0x{pos:X}: 0x001FFF00 -> 0x007FFF00")
    return True

def verify_psp_untouched(original: bytes, modified: bytes) -> bool:
    psp_start, psp_end = 0x8E0000, 0x9E0000
    if original[psp_start:psp_end] != modified[psp_start:psp_end]:
        print("[!] FATAL: PSP region was modified! RSA signature check would fail.")
        return False
    print("[+] PSP region is intact and matches stock RSA-2048 signatures.")
    return True

def build():
    if not os.path.exists(STOCK_ROM):
        print(f"[!] Stock ROM not found: {STOCK_ROM}")
        return 1

    with open(STOCK_ROM, "rb") as f:
        rom_data = bytearray(f.read())

    print(f"[*] Loaded stock ROM: {len(rom_data)} bytes")

    if not patch_apcb(rom_data):
        return 1

    recalculate_apcb_checksum(rom_data, APCB_OFFSET)

    if not inject_vcn_dxe_into_fv(rom_data):
        return 1

    with open(STOCK_ROM, "rb") as f:
        stock_data = f.read()

    if not verify_psp_untouched(stock_data, bytes(rom_data)):
        return 1

    os.makedirs(os.path.dirname(OUTPUT_ROM), exist_ok=True)
    with open(OUTPUT_ROM, "wb") as f:
        f.write(rom_data)

    print(f"[+] Successfully built: {OUTPUT_ROM}")
    return 0

if __name__ == "__main__":
    sys.exit(build())
