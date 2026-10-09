#!/usr/bin/env python3
"""Force one real FUN_00023b14(6, 1) transition on BC-250 BIOS P3.00.

Volatile SMU SRAM only. Cold power-cycle restores the factory state.
"""
from __future__ import annotations

import os
import struct
import sys
import time
from pathlib import Path

LIB = Path(os.environ.get("BC250_SMU_PATH", "/home/OWNER/vcn_unlock/bc250-smu-unlock"))
sys.path.insert(0, str(LIB))

from bc250_smu import Bc250Smu, SmuTimeout  # noqa: E402
import unlock  # noqa: E402

THUNK_ADDR = 0x3FF00
HANDLER_SLOT = 0x776C
DOMAIN6_STATE_WORD = 0xF714
FUN_DOMAIN_POWER = 0x23B14
MSG_ID = 0x61
RETW_N = bytes.fromhex("1df0")


def enc_entry(register: int, frame_bytes: int) -> bytes:
    return (0x36 | (register << 8) | ((frame_bytes // 8) << 12)).to_bytes(3, "little")


def enc_movi_n(register: int, immediate: int) -> bytes:
    value = immediate & 0x7F
    word = ((value & 0xF) << 12) | (register << 8) | (((value >> 4) & 7) << 4) | 0xC
    return word.to_bytes(2, "little")


def enc_call8(pc: int, target: int) -> bytes:
    offset = (target - ((pc + 4) & ~3)) >> 2
    if not (-0x20000 <= offset < 0x20000):
        raise ValueError("call8 target out of range")
    return (((offset & 0x3FFFF) << 6) | (2 << 4) | 5).to_bytes(3, "little")


def build_thunk() -> bytes:
    code = bytearray(enc_entry(1, 0x20))
    code += enc_movi_n(10, 6)       # callee a2 = domain 6 after call8 window rotation
    code += enc_movi_n(11, 1)       # callee a3 = target state 1 (ON on this PMFW)
    code += enc_call8(THUNK_ADDR + len(code), FUN_DOMAIN_POWER)
    code += RETW_N
    return bytes(code)


def read_word(smu: Bc250Smu, address: int) -> int:
    return struct.unpack("<I", smu.smu_read(address, 1))[0]


def write_bytes(smu: Bc250Smu, address: int, data: bytes) -> None:
    padded = data + bytes((-len(data)) % 4)
    for offset in range(0, len(padded), 4):
        smu.smu_write32(address + offset, struct.unpack_from("<I", padded, offset)[0])


def debug_alive(smu: Bc250Smu) -> bool:
    try:
        smu.smu_read(0x7B3C, 1)
        return True
    except Exception:
        return False


def main() -> int:
    code = build_thunk()
    print("thunk=" + code.hex(), flush=True)
    smu = Bc250Smu()
    original_handler = 0
    state_forced = False
    installed = False
    try:
        if not smu.alive():
            raise RuntimeError("SMU not alive before experiment")
        if not smu.secure_access_enabled():
            unlock.unlock(smu)
        if not smu.secure_access_enabled():
            raise RuntimeError("secure debug path did not open")

        original_state = read_word(smu, DOMAIN6_STATE_WORD)
        original_handler = read_word(smu, HANDLER_SLOT)
        print(f"state_before=0x{original_state:08x}", flush=True)
        print(f"handler_before=0x{original_handler:08x}", flush=True)
        if (original_state & 0xFF) != 1:
            raise RuntimeError(f"expected domain6 state byte 1, got {original_state & 0xFF}")

        # Force the software state byte OFF while clocks/rail are already live, so
        # FUN_00023b14(6,1) cannot take its early-return path and must execute the
        # firmware's complete native ON sequence once.
        forced_state = original_state & ~0xFF
        smu.smu_write32(DOMAIN6_STATE_WORD, forced_state)
        state_forced = True
        forced_readback = read_word(smu, DOMAIN6_STATE_WORD)
        print(f"state_forced=0x{forced_readback:08x}", flush=True)
        if forced_readback != forced_state:
            raise RuntimeError("domain6 state-byte force did not persist")

        write_bytes(smu, THUNK_ADDR, code)
        installed = True
        if smu.smu_read(THUNK_ADDR, (len(code) + 3) // 4)[:len(code)] != code:
            raise RuntimeError("thunk read-back mismatch")
        smu.smu_write32(HANDLER_SLOT, THUNK_ADDR)
        if read_word(smu, HANDLER_SLOT) != THUNK_ADDR:
            raise RuntimeError("handler repoint read-back mismatch")

        print("fire=FUN_00023b14(6,1)", flush=True)
        try:
            status, result = smu.send_message(3, MSG_ID, [], check_status=False)
            print(f"mailbox_status=0x{status:02x} result=0x{result:08x}", flush=True)
        except SmuTimeout:
            print("mailbox_timeout=expected", flush=True)

        time.sleep(0.5)
        if not debug_alive(smu):
            print("smu_alive_after=false", flush=True)
            return 2
        final_state = read_word(smu, DOMAIN6_STATE_WORD)
        print("smu_alive_after=true", flush=True)
        print(f"state_after=0x{final_state:08x}", flush=True)
        print(f"transition={(original_state & 0xFF)}->{final_state & 0xFF}", flush=True)
        return 0 if (final_state & 0xFF) == 1 else 3
    finally:
        if debug_alive(smu):
            try:
                smu.smu_write32(HANDLER_SLOT, original_handler)
                if installed:
                    write_bytes(smu, THUNK_ADDR, bytes(len(code)))
                # If the native call did not restore state=1, restore the original
                # descriptor word to avoid leaving a false software state behind.
                current = read_word(smu, DOMAIN6_STATE_WORD)
                if state_forced and (current & 0xFF) != 1:
                    smu.smu_write32(DOMAIN6_STATE_WORD, original_state)
                print("cleanup=ok", flush=True)
            except Exception as error:
                print(f"cleanup_error={error!r}", flush=True)
        else:
            print("cleanup=skipped_smu_unreachable", flush=True)
        smu.close()


if __name__ == "__main__":
    raise SystemExit(main())
