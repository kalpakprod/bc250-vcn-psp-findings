#!/usr/bin/env python3
"""Perform one real PMFW domain-6 OFF -> ON cycle, then restore VCN clocks."""
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
MSG_ID = 0x61
FUN_DOMAIN6_OFF = 0x24764
FUN_DOMAIN_POWER = 0x23B14
FUN_SLOT_CLOCK = 0x23744
DOMAIN6_STATE_WORD = 0xF714
DOMAIN6_CTRL = 0x06D0F8
DOMAIN6_STATUS = 0x06D190
SLOT_BASES = (0x06D100, 0x06D128, 0x06D150)
SLOTS = (0x16, 0x17, 0x18)
RETW_N = bytes.fromhex("1df0")
WIN_BASE = 0x01100000


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


def build_off_thunk() -> bytes:
    code = bytearray(enc_entry(1, 0x20))
    code += enc_call8(THUNK_ADDR + len(code), FUN_DOMAIN6_OFF)
    code += RETW_N
    return bytes(code)


def build_on_thunk() -> bytes:
    code = bytearray(enc_entry(1, 0x20))
    code += enc_movi_n(10, 6)
    code += enc_movi_n(11, 1)
    code += enc_call8(THUNK_ADDR + len(code), FUN_DOMAIN_POWER)
    for slot in SLOTS:
        code += enc_movi_n(10, slot)
        code += enc_call8(THUNK_ADDR + len(code), FUN_SLOT_CLOCK)
    code += RETW_N
    return bytes(code)


def read_word(smu: Bc250Smu, address: int) -> int:
    return struct.unpack("<I", smu.smu_read(address, 1))[0]


def read_win(smu: Bc250Smu, address: int) -> int:
    return read_word(smu, WIN_BASE + (address & 0xFFFFF))


def write_win(smu: Bc250Smu, address: int, value: int) -> None:
    smu.smu_write32(WIN_BASE + (address & 0xFFFFF), value & 0xFFFFFFFF)


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


def snapshot(smu: Bc250Smu, label: str) -> dict[str, object]:
    values: dict[str, object] = {
        "state": read_word(smu, DOMAIN6_STATE_WORD),
        "ctrl": read_win(smu, DOMAIN6_CTRL),
        "status": read_win(smu, DOMAIN6_STATUS),
        "slots": [],
    }
    for base in SLOT_BASES:
        values["slots"].append(
            {
                "clock": read_win(smu, base),
                "enable": read_win(smu, base + 0x08),
                "status": read_win(smu, base + 0x24),
            }
        )
    print(f"{label}={values}", flush=True)
    return values


def fire(smu: Bc250Smu, code: bytes, label: str) -> bool:
    write_bytes(smu, THUNK_ADDR, code)
    if smu.smu_read(THUNK_ADDR, (len(code) + 3) // 4)[: len(code)] != code:
        raise RuntimeError(f"{label} thunk read-back mismatch")
    smu.smu_write32(HANDLER_SLOT, THUNK_ADDR)
    if read_word(smu, HANDLER_SLOT) != THUNK_ADDR:
        raise RuntimeError(f"{label} handler repoint mismatch")
    print(f"fire_{label}={code.hex()}", flush=True)
    try:
        status, result = smu.send_message(3, MSG_ID, [], check_status=False)
        print(f"{label}_mailbox=0x{status:02x}/0x{result:08x}", flush=True)
    except SmuTimeout:
        print(f"{label}_mailbox_timeout=expected", flush=True)
    time.sleep(0.75)
    alive = debug_alive(smu)
    print(f"{label}_smu_alive={str(alive).lower()}", flush=True)
    if alive:
        smu.smu_write32(HANDLER_SLOT, 0)
        write_bytes(smu, THUNK_ADDR, bytes(len(code)))
    return alive


def main() -> int:
    off_code = build_off_thunk()
    on_code = build_on_thunk()
    print(f"off_thunk={off_code.hex()}", flush=True)
    print(f"on_thunk={on_code.hex()}", flush=True)

    smu = Bc250Smu()
    try:
        if not smu.alive():
            raise RuntimeError("SMU not alive before cycle")
        if not smu.secure_access_enabled():
            unlock.unlock(smu)
        if not smu.secure_access_enabled():
            raise RuntimeError("secure debug path did not open")
        if read_word(smu, HANDLER_SLOT) != 0:
            raise RuntimeError("reserved handler slot is not clean")

        before = snapshot(smu, "before")
        if (int(before["state"]) & 0xFF) != 1:
            raise RuntimeError("domain 6 must start in state 1")
        if int(before["ctrl"]) != 0:
            raise RuntimeError("domain 6 gate control must start fully released")

        if not fire(smu, off_code, "off"):
            return 2
        after_off = snapshot(smu, "after_off")
        if (int(after_off["state"]) & 0xFF) != 0:
            print("off_transition_did_not_land", flush=True)
            write_win(smu, DOMAIN6_CTRL, 0)
            for base in SLOT_BASES:
                write_win(smu, base + 0x08, 1)
            return 3

        if not fire(smu, on_code, "on"):
            return 4
        write_win(smu, DOMAIN6_CTRL, 0)
        for base in SLOT_BASES:
            write_win(smu, base + 0x08, 1)
        after_on = snapshot(smu, "after_on")
        if (int(after_on["state"]) & 0xFF) != 1:
            return 5
        if int(after_on["ctrl"]) != 0:
            return 6
        if any(int(slot["enable"]) != 1 for slot in after_on["slots"]):
            return 7
        print("cycle_complete=true", flush=True)
        return 0
    finally:
        if debug_alive(smu):
            try:
                smu.smu_write32(HANDLER_SLOT, 0)
                write_bytes(smu, THUNK_ADDR, bytes(max(len(off_code), len(on_code))))
                print("cleanup=ok", flush=True)
            except Exception as error:
                print(f"cleanup_error={error!r}", flush=True)
        else:
            print("cleanup=skipped_smu_unreachable", flush=True)
        smu.close()


if __name__ == "__main__":
    raise SystemExit(main())
