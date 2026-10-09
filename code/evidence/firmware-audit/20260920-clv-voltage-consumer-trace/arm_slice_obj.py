#!/usr/bin/env python3
"""Wrap a raw byte slice in a minimal ELF32 relocatable object so that the local
llvm-objdump (the only ARM-capable disassembler on this host) can disassemble it.

usage: arm_slice_obj.py <blob> <offset> <length> <out.o>
No project dependency is added: llvm-objdump is already installed (LLVM 22.1.8).
"""
import struct, sys

def build(data: bytes, vma: int) -> bytes:
    EH, SH = 52, 40
    text_off = EH
    shstr = b"\x00.text\x00.shstrtab\x00"
    shstr_off = text_off + len(data)
    shoff = shstr_off + len(shstr)
    shoff += (-shoff) % 4
    eh = b"\x7fELF\x01\x01\x01\x00" + b"\x00" * 8
    eh += struct.pack("<HHIIIIIHHHHHH",
                      1,          # ET_REL
                      40,         # EM_ARM
                      1,          # version
                      0, 0, shoff, 0x05000000,
                      EH, 0, 0, SH, 3, 2)
    sh = b"\x00" * SH
    sh += struct.pack("<IIIIIIIIII", 1, 1, 0x6, vma, text_off, len(data), 0, 0, 4, 0)
    sh += struct.pack("<IIIIIIIIII", 7, 3, 0, 0, shstr_off, len(shstr), 0, 0, 1, 0)
    return eh + data + shstr + b"\x00" * (shoff - shstr_off - len(shstr)) + sh

if __name__ == "__main__":
    blob, off, ln, out = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0), sys.argv[4]
    raw = open(blob, "rb").read()
    open(out, "wb").write(build(raw[off:off + ln], off))
    print(f"wrote {out}: {ln} bytes at vma 0x{off:x}")
