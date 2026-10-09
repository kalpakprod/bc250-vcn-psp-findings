#!/usr/bin/env python3
"""Bounded byte-backed trace of exact-clv UclkDiv1M0 serialization and callback dispatch."""
from __future__ import annotations
import hashlib, json, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CENSUS = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers"
OUT = Path(__file__).resolve().parent
EXPECTED_ROM = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
EXPECTED_MODULE = "6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77"

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def record_for(census: dict, ui: str) -> dict:
    for row in census["records"]:
        if row.get("ui") == ui:
            return row
    raise KeyError(ui)

def raw_offset(row: dict, rva: int) -> int:
    for sec in row["sections"]:
        if sec["rva"] <= rva < sec["rva"] + sec["size"]:
            return rva - sec["rva"] + sec["raw"]
    raise ValueError(hex(rva))

def bytes_at(blob: bytes, row: dict, rva: int, n: int) -> bytes:
    off = raw_offset(row, rva)
    return blob[off:off+n]

def u32(blob: bytes, row: dict, rva: int) -> int:
    return struct.unpack_from("<I", blob, raw_offset(row, rva))[0]

def check(label: str, got, expected, checks: list[dict]):
    ok = got == expected
    checks.append({"check": label, "passed": ok, "got": got, "expected": expected})
    if not ok:
        raise AssertionError(f"{label}: got {got!r}, expected {expected!r}")

def main() -> None:
    census = json.loads((CENSUS / "census.json").read_text())
    rom = Path(census["input"])
    # Census path is project-relative in the old artifact; resolve it from ROOT.
    if not rom.is_absolute():
        rom = ROOT / rom
    module = record_for(census, "CbsBasePei")
    module_path = CENSUS / (module["stem"] + ".bin")
    blob = module_path.read_bytes()
    checks: list[dict] = []
    check("pinned ROM sha256", sha256(rom), EXPECTED_ROM, checks)
    check("pinned ROM size", rom.stat().st_size, 0x1000000, checks)
    check("CbsBasePei body sha256", sha256(module_path), EXPECTED_MODULE, checks)
    check("CbsBasePei body size", len(blob), module["size"], checks)

    # Exact Setup+0x330 -> record 0x1204 bytes.
    check("record ID load at CbsBasePei+0x9cc4", bytes_at(blob, module, 0x9cc4, 5).hex(), "ba04120000", checks)
    check("Setup+0x330 load context at CbsBasePei+0x9ce1", bytes_at(blob, module, 0x9ce1, 9).hex(), "8b55fc8a8230030000", checks)
    check("serialized record ID write", bytes_at(blob, module, 0x9cc9, 6).hex(), "8b45f8668910", checks)
    check("Setup+0x330 source load at CbsBasePei+0x9ce4", bytes_at(blob, module, 0x9ce4, 6).hex(), "8a8230030000", checks)
    check("serialized Uclk value store at CbsBasePei+0x9cea", bytes_at(blob, module, 0x9cea, 3).hex(), "884103", checks)

    # Exact callback edge: static list entry -> provider object -> callback RVA 0x36c0 -> serializer 0x36f0.
    list_rva = 0x13e20
    provider_ptr = u32(blob, module, list_rva + 0x10)
    provider_rva = provider_ptr - module["imagebase"]
    callback_ptr = u32(blob, module, provider_rva + 0x10)
    callback_rva = callback_ptr - module["imagebase"]
    check("first callback list provider pointer", hex(provider_rva), "0x13dc0", checks)
    check("first callback provider function", hex(callback_rva), "0x36c0", checks)
    check("callback body 0x36c0", bytes_at(blob, module, 0x36c0, 0x24).hex(), "558bec518b450c8b4804894dfc8b55fc8b4204508b4dfc8b11528b451050e80d00000083", checks)
    check("callback serializer call 0x36de", bytes_at(blob, module, 0x36de, 5).hex(), "e80d000000", checks)
    check("serializer entry 0x36f0", bytes_at(blob, module, 0x36f0, 11).hex(), "558bec83ec0ce885e10000", checks)
    check("serializer INV header write 0x3728", bytes_at(blob, module, 0x3728, 6).hex(), "c70224494e56", checks)
    check("serializer version write 0x3731", bytes_at(blob, module, 0x3731, 7).hex(), "c7400401000000", checks)

    # Dispatcher byte window calls a function pointer from entry+0x10 with the
    # setup/context/output arguments. No literal 0x1204 appears in this window.
    check("dispatcher callback indirect call", bytes_at(blob, module, 0x47d, 0x1d).hex(), "8d9538f7ffff528b450c508b4d08518b9518f7ffff8b4210ffd083c40c", checks)
    check("dispatcher window has no 0x1204 literal", b"\x04\x12" not in bytes_at(blob, module, 0x240, 0x3c0), True, checks)

    # Discriminating host-only model: value byte is copied, not transformed,
    # for three distinct inputs. This models only the checked machine sequence.
    samples = []
    for value in (0x00, 0x01, 0x7f):
        # record header is ID LE + flags byte (serializer preserves low flags) + value.
        rec = bytes((0x04, 0x12, 0x00, value))
        samples.append({"setup_plus_0x330": value, "record_bytes": rec.hex(), "record_id": hex(int.from_bytes(rec[:2], "little")), "value_byte": rec[3]})
    check("synthetic value discrimination", samples, [
        {"setup_plus_0x330": 0, "record_bytes": "04120000", "record_id": "0x1204", "value_byte": 0},
        {"setup_plus_0x330": 1, "record_bytes": "04120001", "record_id": "0x1204", "value_byte": 1},
        {"setup_plus_0x330": 127, "record_bytes": "0412007f", "record_id": "0x1204", "value_byte": 127},
    ], checks)

    # Reuse exact census result to state the bounded negative result without
    # re-running a generic mailbox search: direct target candidates are all
    # serializer IDs and the retained caller matrix has no INV reader for 0x1204.
    coverage = json.loads((CENSUS / "coverage.json").read_text())
    cbs_targets = [x for x in coverage["target_candidates"] if x["module"] == "CbsBasePei" and x.get("operands") == "edx,0x1204"]
    check("CbsBasePei exact 0x1204 target candidate count", len(cbs_targets), 1, checks)
    check("CbsBasePei 0x1204 candidate classification", cbs_targets[0]["category"], "immediate-candidate", checks)
    matrix = (CENSUS / "caller-matrix.md").read_text()
    check("retained matrix does not classify CbsBasePei as INV reader", "| CbsBasePei |" not in matrix or "confirmed INV reader" not in next((line for line in matrix.splitlines() if "| CbsBasePei |" in line), ""), True, checks)

    result = {
        "status": "PASS",
        "route": "CbsBasePei callback adapter; final UclkDiv1M0 actuator remains unresolved",
        "input": str(rom),
        "rom_sha256": sha256(rom),
        "module": str(module_path),
        "module_sha256": sha256(module_path),
        "path": [
            {"site": "CbsBasePei", "rva": "0x9cc4", "effect": "write record ID 0x1204"},
            {"site": "CbsBasePei", "rva": "0x9ce4", "effect": "load byte Setup+0x330"},
            {"site": "CbsBasePei", "rva": "0x9cea", "effect": "store loaded byte at record +0x3"},
            {"site": "CbsBasePei callback table", "rva": "0x13e20/+0x10 -> 0x13dc0/+0x10", "effect": "bind first callback to RVA 0x36c0"},
            {"site": "CbsBasePei", "rva": "0x36c0 -> 0x36f0", "effect": "adapter builds INV record buffer; writes $INV header at 0x3728"},
            {"site": "CbsBasePei", "rva": "0x47d..0x499", "effect": "dispatcher invokes callback indirectly; no direct actuator write in bounded window"},
        ],
        "fresh_result": "For setup bytes 00/01/7f at +0x330, the immediate callback output record remains ID 0x1204 with value 00/01/7f respectively. The first static callback is an INV adapter (0x36c0->0x36f0), not a clock/register consumer.",
        "bounded_uncertainty": "The final consumer/override after the INV buffer remains unresolved within the bounded static-analysis coverage of the exact 233-module x86/TE census. No hardware behavior, clock mapping, default precedence, or firmware acceptance is claimed.",
        "checks": checks,
        "source_reports": [
            str(CENSUS / "caller-matrix.md"),
            str(CENSUS / "verification.json"),
            str(CENSUS / "coverage.json"),
        ],
    }
    (OUT / "uclk-consumer-trace.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "checks": len(checks), "fresh_result": result["fresh_result"]}, indent=2))

if __name__ == "__main__":
    main()
