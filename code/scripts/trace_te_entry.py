#!/usr/bin/env python3
"""Trace bounded direct control flow from a UEFI TE image entry point."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pypcode


@dataclass(frozen=True)
class Section:
    name: str
    virtual_address: int
    virtual_size: int
    raw_size: int
    file_offset: int

    def contains(self, address: int) -> bool:
        return self.virtual_address <= address < self.virtual_address + min(self.virtual_size, self.raw_size)


DIRECT_TARGET = re.compile(r"^0x([0-9a-fA-F]+)$")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_te(data: bytes) -> tuple[int, int, int, list[Section]]:
    if len(data) < 0x28 or data[:2] != b"VZ":
        raise ValueError("input is not a TE image")
    machine, section_count, _subsystem, stripped_size, entry_rva = struct.unpack_from("<HBBHI", data, 2)
    if machine != 0x14C:
        raise ValueError(f"expected IA32 TE machine 0x14C, got 0x{machine:X}")
    delta = stripped_size - 40
    if delta < 0:
        raise ValueError("invalid TE stripped-size delta")
    sections: list[Section] = []
    for index in range(section_count):
        offset = 0x28 + index * 40
        if offset + 40 > len(data):
            raise ValueError("truncated section table")
        name = data[offset : offset + 8].split(b"\0", 1)[0].decode("ascii", "replace")
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from("<IIII", data, offset + 8)
        file_offset = raw_pointer - delta
        if file_offset < 0 or file_offset + raw_size > len(data):
            raise ValueError(f"section {name} raw extent is out of bounds")
        sections.append(Section(name, virtual_address, virtual_size, raw_size, file_offset))
    return machine, stripped_size, entry_rva, sections


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-instructions", type=int, default=10000)
    parser.add_argument("--start-rva", type=lambda value: int(value, 0))
    args = parser.parse_args()
    data = args.image.read_bytes()
    machine, stripped_size, entry_rva, sections = parse_te(data)
    context = pypcode.Context("x86:LE:32:default")

    def instruction_at(address: int):
        section = next((item for item in sections if item.contains(address)), None)
        if section is None:
            return None
        relative = address - section.virtual_address
        file_offset = section.file_offset + relative
        maximum = min(16, section.raw_size - relative)
        decoded = context.disassemble(data[file_offset : file_offset + maximum], base_address=address, max_instructions=1)
        return decoded.instructions[0] if decoded.instructions else None

    start_rva = entry_rva if args.start_rva is None else args.start_rva
    if not any(section.contains(start_rva) for section in sections):
        raise ValueError(f"start RVA 0x{start_rva:X} is not mapped")
    pending: deque[int] = deque([start_rva])
    visited: dict[int, dict[str, object]] = {}
    direct_calls: list[dict[str, object]] = []
    indirect_calls: list[dict[str, object]] = []
    exits: list[dict[str, object]] = []
    errors: list[str] = []
    while pending and len(visited) < args.max_instructions:
        address = pending.popleft()
        if address in visited:
            continue
        instruction = instruction_at(address)
        if instruction is None:
            errors.append(f"unmapped or undecodable address 0x{address:X}")
            continue
        mnemonic = instruction.mnem.upper()
        body = instruction.body
        length = instruction.length
        fallthrough = address + length
        match = DIRECT_TARGET.match(body)
        direct_target = int(match.group(1), 16) if match else None
        visited[address] = {"address": f"0x{address:X}", "length": length, "mnemonic": mnemonic, "body": body}

        if mnemonic.startswith("RET") or mnemonic in {"IRET", "IRETD"}:
            exits.append({"address": f"0x{address:X}", "kind": mnemonic})
            continue
        if mnemonic == "JMP":
            if direct_target is None:
                exits.append({"address": f"0x{address:X}", "kind": "indirect-jump", "body": body})
            else:
                pending.append(direct_target)
            continue
        if mnemonic.startswith("J"):
            if direct_target is not None:
                pending.append(direct_target)
            else:
                errors.append(f"indirect conditional branch at 0x{address:X}: {body}")
            pending.append(fallthrough)
            continue
        if mnemonic == "CALL":
            record = {"site": f"0x{address:X}", "target": f"0x{direct_target:X}" if direct_target is not None else None, "body": body}
            (direct_calls if direct_target is not None else indirect_calls).append(record)
            pending.append(fallthrough)
            continue
        pending.append(fallthrough)

    if pending:
        errors.append(f"instruction limit reached with {len(pending)} addresses pending")
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/trace_te_entry.py",
        "pypcode_version": getattr(pypcode, "__version__", "unknown"),
        "input": {"path": str(args.image.resolve()), "size": len(data), "sha256": sha256(data)},
        "te": {
            "machine": f"0x{machine:X}",
            "stripped_size": f"0x{stripped_size:X}",
            "delta": f"0x{stripped_size - 40:X}",
            "entry_rva": f"0x{entry_rva:X}",
            "trace_start_rva": f"0x{start_rva:X}",
            "sections": [
                {
                    "name": item.name,
                    "virtual_address": f"0x{item.virtual_address:X}",
                    "virtual_size": item.virtual_size,
                    "raw_size": item.raw_size,
                    "file_offset": f"0x{item.file_offset:X}",
                }
                for item in sections
            ],
        },
        "trace": {
            "instruction_count": len(visited),
            "instructions": [visited[address] for address in sorted(visited)],
            "direct_calls": direct_calls,
            "indirect_calls": indirect_calls,
            "exits": exits,
            "errors": errors,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {args.output}")
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "instructions": len(visited), "direct_calls": len(direct_calls), "indirect_calls": len(indirect_calls), "exits": len(exits), "errors": len(errors)}))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
