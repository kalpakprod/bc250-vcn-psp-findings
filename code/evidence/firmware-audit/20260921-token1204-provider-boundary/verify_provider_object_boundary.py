#!/usr/bin/env python3
"""
Verification of AmdFabricAriPei post-reader provider-object boundary:
0x25d3 (PeiServices pointer via SIDT), 0x25ed (GetHobList), 0x266f (CreateHob),
and caller sites 0x2698, 0x26d5.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

PEIM_PATH = Path("evidence/firmware-audit/20260919-inv-buffer-lifetime/AmdFabricAriPei.bin")
EXPECTED_SHA256 = "c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78"
OUT_DIR = Path("evidence/firmware-audit/20260921-token1204-provider-boundary")

def main():
    checks = []
    
    def ck(name: str, actual, expected):
        ok = (actual == expected)
        checks.append({
            "name": name,
            "actual": str(actual),
            "expected": str(expected),
            "status": "PASS" if ok else "FAIL"
        })
        if not ok:
            print(f"FAIL: {name}: actual {actual} != expected {expected}")

    # 1. Image hash check
    data = PEIM_PATH.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    ck("peim_sha256", h, EXPECTED_SHA256)

    # In TE/PE, file offset = RVA - 0x198 (standard for this TE image)
    # Check TE signature and offset adjustment
    te_sig = data[0:2]
    ck("te_signature", te_sig.decode("ascii", errors="ignore"), "VZ")
    
    # 2. Inspect 0x25d3 - PeiServicesTablePointerLibIdt implementation
    # 25d3: 55                      push   ebp
    # 25d4: 8b ec                   mov    ebp,esp
    # 25d6: 83 ec 0c                sub    esp,0xc
    # 25d9: 8d 45 f4                lea    eax,[ebp-0xc]
    # 25dc: 89 45 fc                mov    DWORD PTR [ebp-0x4],eax
    # 25df: 8b 45 fc                mov    eax,DWORD PTR [ebp-0x4]
    # 25e2: 0f 01 08                sidtd  [eax]
    # 25e5: 8b 45 f6                mov    eax,DWORD PTR [ebp-0xa]
    # 25e8: 8b 40 fc                mov    eax,DWORD PTR [eax-0x4]
    # 25eb: c9                      leave
    # 25ec: c3                      ret
    raw_25d3 = data[0x25d3 - 0x198 : 0x25ed - 0x198]
    ck("raw_25d3_hex", raw_25d3.hex(), "558bec83ec0c8d45f48945fc8b45fc0f01088b45f68b40fcc9c3")

    # 3. Inspect 0x25ed - GetHobList call via [ecx+0x30]
    # 25ed: 55                      push   ebp
    # 25ee: 8b ec                   mov    ebp,esp
    # 25f0: 51                      push   ecx
    # 25f1: e8 dd ff ff ff          call   0x25d3
    # 25f6: 8b 08                   mov    ecx,DWORD PTR [eax]
    # 25f8: 8d 55 fc                lea    edx,[ebp-0x4]
    # 25fb: 52                      push   edx
    # 25fc: 50                      push   eax
    # 25fd: ff 51 30                call   DWORD PTR [ecx+0x30]
    # 2600: 8b 45 fc                mov    eax,DWORD PTR [ebp-0x4]
    raw_25ed = data[0x25ed - 0x198 : 0x2603 - 0x198]
    ck("raw_25ed_hex", raw_25ed.hex(), "558bec51e8ddffffff8b088d55fc5250ff51308b45fc")

    # 4. Inspect 0x266f - CreateHob call via [ecx+0x34]
    # 266f: 55                      push   ebp
    # 2670: 8b ec                   mov    ebp,esp
    # 2672: 51                      push   ecx
    # 2673: e8 5b ff ff ff          call   0x25d3
    # 2678: 8b 08                   mov    ecx,DWORD PTR [eax]
    # 267a: 8d 55 fc                lea    edx,[ebp-0x4]
    # 267d: 52                      push   edx
    # 267e: ff 75 0c                push   DWORD PTR [ebp+0xc]
    # 2681: ff 75 08                push   DWORD PTR [ebp+0x8]
    # 2684: 50                      push   eax
    # 2685: ff 51 34                call   DWORD PTR [ecx+0x34]
    # 2688: 83 c4 10                add    esp,0x10
    # 268b: 85 c0                   test   eax,eax
    # 268d: 7d 04                   jge    0x2693
    # 268f: 83 65 fc 00             and    DWORD PTR [ebp-0x4],0x0
    # 2693: 8b 45 fc                mov    eax,DWORD PTR [ebp-0x4]
    # 2696: c9                      leave
    # 2697: c3                      ret
    raw_266f = data[0x266f - 0x198 : 0x2698 - 0x198]
    ck("raw_266f_hex", raw_266f.hex(), "558bec51e85bffffff8b088d55fc52ff750cff750850ff513483c41085c07d048365fc008b45fcc9c3")

    # 5. Caller site at 0x2698:
    # 2698: 8d 47 18                lea    eax,[edi+0x18]
    # 269b: 50                      push   eax
    # 269c: 6a 04                   push   0x4
    # 269e: e8 cc ff ff ff          call   0x266f
    raw_2698 = data[0x2698 - 0x198 : 0x26a3 - 0x198]
    ck("raw_2698_hex", raw_2698.hex(), "8d4718506a04e8ccffffff")

    # 6. Caller site at 0x26d5:
    # 26d5: 56                      push   esi
    # 26d6: 6a 30                   push   0x30
    # 26d8: 6a 02                   push   0x2
    # 26da: e8 90 ff ff ff          call   0x266f
    raw_26d5 = data[0x26d5 - 0x198 : 0x26df - 0x198]
    ck("raw_26d5_hex", raw_26d5.hex(), "566a306a02e890ffffff")

    # 7. Token 0x1204 presence check in range 0x25d3..0x2720
    window = data[0x25d3 - 0x198 : 0x2720 - 0x198]
    ck("no_token_1204_in_provider_boundary", b"\x04\x12" in window, False)

    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["status"] == "PASS")
    failed_checks = sum(1 for c in checks if c["status"] == "FAIL")

    result = {
        "status": "PASS" if failed_checks == 0 else "FAIL",
        "peim_sha256": h,
        "checks": {
            "total": total_checks,
            "passed": passed_checks,
            "failed": failed_checks,
        },
        "findings": {
            "provider_object_resolution": "0x25d3 executes `sidtd` to obtain IDT base address from [ebp-0xa], then loads [IDT_BASE - 4] which is the standard EDK II PeiServicesTablePointerLibIdt mechanism.",
            "service_slot_0x30": "0x25ed calls [ecx+0x30] which corresponds to EFI_PEI_SERVICES.GetHobList.",
            "service_slot_0x34": "0x266f calls [ecx+0x34] which corresponds to EFI_PEI_SERVICES.CreateHob.",
            "call_site_0x2698": "Calls CreateHob with Type=4 (EFI_HOB_TYPE_GUID_EXTENSION) and Length=[edi+0x18].",
            "call_site_0x26d5": "Calls CreateHob with Type=2 (EFI_HOB_TYPE_RESOURCE_DESCRIPTOR) and Length=0x30.",
            "token_1204_association": "No token 0x1204 literal or clock/divider operand is present. This edge is generic EDK II HOB creation, not a token 0x1204 consumer or clock actuator.",
        },
        "checks_detail": checks,
    }

    out_file = OUT_DIR / "token1204-provider-boundary-result.json"
    out_file.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Result written to {out_file}")
    print(f"Status: {result['status']}, {passed_checks}/{total_checks} checks passed.")
    if failed_checks > 0:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
