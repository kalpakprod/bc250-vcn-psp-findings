#!/usr/bin/env python3
"""Independent exact-byte verification of AmdFabricAriPei post-reader provider-object and caller boundary."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path("/home/OWNER/orca/projects/bc250")
OUT = Path(__file__).resolve().parent
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
FAB = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.bin"

checks = []
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(name, got, exp):
    ok = (got == exp)
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "got": got, "expected": exp})
    if not ok: raise AssertionError(f"{name}: {got!r} != {exp!r}")

def raw(rva, hx, name):
    b = FAB.read_bytes()
    off = rva - 0x198
    ck(name, b[off:off+len(bytes.fromhex(hx))].hex(), hx)

ck("ROM_hash", sha(ROM), "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8")
ck("FAB_hash", sha(FAB), "c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78")

# 1. 0x25D3: PeiServicesTablePointerLibIdt (GetPeiServicesTablePointer)
# 55 8b ec 83 ec 0c 8d 45 f4 89 45 fc 8b 45 fc 0f 01 08 8b 45 f6 8b 40 fc c9 c3
raw(0x25D3, "558bec83ec0c8d45f48945fc8b45fc", "get_pei_services_prologue_and_lea")
raw(0x25E2, "0f0108", "sidtd_at_0x25E2")
raw(0x25E5, "8b45f68b40fcc9c3", "load_idtr_base_and_read_peiservices_ptr")

# 2. 0x266F: PeiServicesCreateHob(Type, Length, &Hob)
# 55 8b ec 51 e8 5b ff ff ff 8b 08 8d 55 fc 52 ff 75 0c ff 75 08 50 ff 51 34 83 c4 10 85 c0 7d 04 83 65 fc 00 8b 45 fc c9 c3
raw(0x266F, "558bec51", "create_hob_prologue")
raw(0x2673, "e85bffffff", "call_get_pei_services_0x25d3")
raw(0x2678, "8b08", "load_pei_services_table")
raw(0x267A, "8d55fc52", "lea_hob_out_and_push")
raw(0x267E, "ff750c", "push_length_arg")
raw(0x2681, "ff7508", "push_type_arg")
raw(0x2684, "50", "push_pei_services_table_ptr")
raw(0x2685, "ff5134", "call_peiservices_createhob_slot_0x34")
raw(0x2688, "83c41085c07d048365fc008b45fcc9c3", "cleanup_check_status_return")

# 3. 0x2698: BuildGuidHob caller
# 8d 47 18 50 6a 04 e8 cc ff ff ff 59 59 85 c0 74 1c 83 c0 18 8b 0e 89 48 f0 8b 4e 04 89 48 f4 8b 4e 08 89 48 f8 8b 4e 0c 89 48 fc
raw(0x2698, "8d4718506a04", "build_guid_hob_push_len_and_type_0x4")
raw(0x269E, "e8ccffffff", "call_create_hob_0x266f")
raw(0x26A9, "83c018", "advance_to_guid_field")
raw(0x26AC, "8b0e8948f08b4e048948f48b4e088948f88b4e0c8948fc", "copy_16byte_guid")

# 4. 0x26D5: BuildMemoryAllocationHob caller
# 56 6a 30 6a 02 e8 90 ff ff ff 8b f0 59 59 85 f6 74 3c
raw(0x26D5, "566a306a02", "build_mem_alloc_hob_push_len_0x30_and_type_0x2")
raw(0x26DA, "e890ffffff", "call_create_hob_0x266f_from_mem_alloc")
raw(0x26E7, "8d46086a1050e88e440100", "zeromem_guid_descriptor")
raw(0x270E, "c746280a000000", "set_memory_type_0xA")

# 5. Bounded negative: no 0x1204 literal or token operand in these functions
b = FAB.read_bytes()
win_25d3 = b[0x25D3-0x198:0x25ED-0x198]
win_266f = b[0x266F-0x198:0x2698-0x198]
win_2698 = b[0x2698-0x198:0x26D5-0x198]
win_26d5 = b[0x26D5-0x198:0x2725-0x198]

ck("no_1204_in_25d3", b"\x04\x12" not in win_25d3, True)
ck("no_1204_in_266f", b"\x04\x12" not in win_266f, True)
ck("no_1204_in_2698", b"\x04\x12" not in win_2698, True)
ck("no_1204_in_26d5", b"\x04\x12" not in win_26d5, True)

result = {
    "status": "PASS",
    "checks": {
        "passed": sum(x["status"] == "PASS" for x in checks),
        "failed": sum(x["status"] == "FAIL" for x in checks),
        "total": len(checks)
    },
    "identity": {
        "module": "AmdFabricAriPei",
        "hash": sha(FAB),
        "function_0x25D3": "GetPeiServicesTablePointer (PeiServicesTablePointerLibIdt / sidtd [eax] -> IDTR.Base -> [Base-4])",
        "function_0x266F": "PeiServicesCreateHob (calls PeiServices->CreateHob at vtable offset 0x34)",
        "function_0x2698": "BuildGuidHob (calls CreateHob with Type 0x4 = EFI_HOB_TYPE_GUID_EXTENSION)",
        "function_0x26D5": "BuildMemoryAllocationHob (calls CreateHob with Type 0x2 = EFI_HOB_TYPE_MEMORY_ALLOCATION, Length 0x30, MemoryType 0xA)",
    },
    "token1204_status": "NOT_CONSUMED",
    "discriminating_result": "The edge 0x266F -> 0x25D3 -> [ECX+0x34] is the standard EDK II PI PEI PeiServices->CreateHob dispatch via IDT-based PeiServicesTablePointerLib. It creates generic HOBs (GUID HOBs and Memory Allocation HOBs) and does not consume, evaluate, or actuate token 0x1204 (UclkDiv1M0) or any clock/divider setting.",
    "checks_detail": checks
}

(OUT / "provider-object-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": result["status"], "checks": result["checks"], "identity": result["identity"], "discriminating_result": result["discriminating_result"]}, sort_keys=True))
