#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_oc_profiles.py — генератор трёх калиброванных версий BIOS для AMD BC-250 (Oberon / Cyan Skillfish)
для снижения латентности памяти за счет синхронизации FCLK : UCLK : MCLK.

Требования:
  - CPU Frequency: СТОК (3600 МГц) во всех профилях, без разгона.
  - Память GDDR6: НЕ разгоняется (MCLK <= 1750 МГц).
  - Реализация полного синхрона 1:1:1 (UclkDiv1M0 = 0x01 @ 0x330, FCLK = MCLK = 1750 МГц).

Профили:
  1. Profile 1 (Sync 1:1 Fabric-to-UMC @ сток 1750 МГц GDDR6):
     FCLK = 875 МГц, UCLK = 875 МГц, MCLK = 1750 МГц (сток).
     FCLK:UCLK = 1:1, UCLK:MCLK = 1:2. Нулевой штраф CDC джиттера без подъема вольтажа SOC.
     CPU 3600 (сток), TCL = Auto (0xFF), DRAM Timing Controls = Auto (0xFF), BGS = Disabled, PPT = 105 Вт.

  2. Profile 2 (Full Sync 1:1:1 @ 1333 МГц — даунклок памяти для 100% стабильности):
     FCLK = 1333 МГц, UCLK = 1333 МГц (UclkDiv1M0 = 0x01), MCLK = 1330 МГц (0x1A).
     Истинный 1:1:1 на безопасной частоте шины без перегрева SOC (+35 мВ).
     CPU 3600 (сток), TCL = Auto (0xFF), DRAM Timing Controls = Auto (0xFF), BGS = Disabled, PPT = 120 Вт.

  3. Profile 3 (Full Sync 1:1:1 @ 1750 МГц — целевой экстремальный синхрон):
     FCLK = 1750 МГц (0x704 = 1750), UCLK = 1750 МГц (UclkDiv1M0 = 0x01 @ 0x330), MCLK = 1750 МГц (сток 0x23).
     Истинный 1:1:1 на стоковой частоте памяти. Устраняет 100% задержек CDC FIFO.
     CPU 3600 (сток), VDDCR_VDD Offset = +80 мВ (для удержания FCLK 1750), TCL = Auto (0xFF), DRAM Timing Controls = Auto (0xFF), BGS = Disabled, PPT = 130 Вт.
"""

import os
import struct
import hashlib
import json
import zipfile

BASE_PATHS = [
    r"C:\Users\OWNER\Downloads\AyuGram Desktop\W25Q128BV@SOIC8.zip",
    r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\W25Q128BV@WSON8_20250122_140516.BIN",
    r"C:\Users\OWNER\bc250-bios\evidence\fv_extract\BC250_3.00.ROM",
    r"BC250_3.00.ROM",
]

OUT_DIR = r"C:\Users\OWNER\tmp_bc250\recon\oc_profiles"
LOCAL_OUT_DIR = r"oc_profiles"

PROFILES = [
    {
        "name": "01_BC250_SYNC_FclkUclk_1to1_Mclk1750_StockCPU",
        "description": "Синхронизация Fabric-to-UMC 1:1 при стоковой памяти: FCLK 875 МГц, UCLK 875 МГц, MCLK 1750 МГц, CPU 3600 (сток)",
        "patches": [
            ("Force CPU Frequency", 0x701, "<H", 3600),  # СТОК
            ("DF Clock Override Control", 0x703, "<B", 0x01),
            ("DF Clock Override", 0x704, "<H", 875),   # FCLK = UCLK = 875 МГц (1:1)
            ("FCLK_DPM", 0x6a3, "<B", 0x00),
            ("UclkDiv1M0", 0x330, "<B", 0x00),         # 1:2 (UCLK = 875 МГц)
            ("VDDCR_VDD Voltage Offset Control", 0x6e5, "<B", 0x00),
            ("VDDCR_VDD Voltage Offset", 0x6e6, "<B", 0),
            ("Memory Clock Speed", 0x316, "<B", 0x23),  # СТОК 1750 МГц (14 Gbps)
            ("DRAM Timing User Controls", 0x32f, "<B", 0xFF),  # Auto (предотвращает LoadXmt Fail)
            ("Tcl", 0x317, "<B", 0xFF),  # Auto (0xFF)
            ("BankGroupSwap", 0x32d, "<B", 0x00),  # Disabled
            ("FAST_PPT_LIMIT", 0x70c, "<I", 105000),  # 105 Вт
            ("SLOW_PPT_LIMIT", 0x710, "<I", 85000),   # 85 Вт
            ("VRM_CURRENT_LIMIT", 0x718, "<I", 75000), # 75 А
            ("VRM_MAXIMUM_CURRENT_LIMIT", 0x71c, "<I", 100000), # 100 А
        ]
    },
    {
        "name": "02_BC250_SYNC_Full_1to1to1_1333MHz_StockCPU",
        "description": "Полный синхрон 1:1:1 на 1333 МГц: FCLK 1333, UCLK 1333, MCLK 1333 (даунклок памяти), CPU 3600 (сток)",
        "patches": [
            ("Force CPU Frequency", 0x701, "<H", 3600),  # СТОК
            ("DF Clock Override Control", 0x703, "<B", 0x01),
            ("DF Clock Override", 0x704, "<H", 1333),  # FCLK = 1333 МГц
            ("FCLK_DPM", 0x6a3, "<B", 0x00),
            ("UclkDiv1M0", 0x330, "<B", 0x01),         # 1:1 (UCLK = MCLK = 1333 МГц)
            ("VDDCR_VDD Voltage Offset Control", 0x6e5, "<B", 0x01),
            ("VDDCR_VDD Voltage Offset", 0x6e6, "<B", 35),  # +35 мВ для FCLK
            ("Memory Clock Speed", 0x316, "<B", 0x1A),  # 1330 МГц (даунклок памяти для 1:1:1)
            ("DRAM Timing User Controls", 0x32f, "<B", 0xFF),  # Auto (предотвращает LoadXmt Fail)
            ("Tcl", 0x317, "<B", 0xFF),  # Auto (0xFF)
            ("BankGroupSwap", 0x32d, "<B", 0x00),  # Disabled
            ("FAST_PPT_LIMIT", 0x70c, "<I", 120000),  # 120 Вт
            ("SLOW_PPT_LIMIT", 0x710, "<I", 95000),   # 95 Вт
            ("VRM_CURRENT_LIMIT", 0x718, "<I", 80000), # 80 А
            ("VRM_MAXIMUM_CURRENT_LIMIT", 0x71c, "<I", 110000), # 110 А
        ]
    },
    {
        "name": "03_BC250_SYNC_Full_1to1to1_1750MHz_StockCPU",
        "description": "Целевой полный синхрон 1:1:1 на стоковой частоте 1750 МГц: FCLK 1750, UCLK 1750, MCLK 1750, CPU 3600 (сток)",
        "patches": [
            ("Force CPU Frequency", 0x701, "<H", 3600),  # СТОК
            ("DF Clock Override Control", 0x703, "<B", 0x01),
            ("DF Clock Override", 0x704, "<H", 1750),  # FCLK = 1750 МГц
            ("FCLK_DPM", 0x6a3, "<B", 0x00),
            ("UclkDiv1M0", 0x330, "<B", 0x01),         # 1:1 (UCLK = MCLK = 1750 МГц)
            ("VDDCR_VDD Voltage Offset Control", 0x6e5, "<B", 0x01),
            ("VDDCR_VDD Voltage Offset", 0x6e6, "<B", 80),  # +80 мВ (необходимо для FCLK 1750)
            ("Memory Clock Speed", 0x316, "<B", 0x23),  # СТОК 1750 МГц (без разгона памяти)
            ("DRAM Timing User Controls", 0x32f, "<B", 0xFF),  # Auto
            ("Tcl", 0x317, "<B", 0xFF),  # Auto (0xFF)
            ("BankGroupSwap", 0x32d, "<B", 0x00),  # Disabled
            ("FAST_PPT_LIMIT", 0x70c, "<I", 130000),  # 130 Вт
            ("SLOW_PPT_LIMIT", 0x710, "<I", 105000),  # 105 Вт
            ("VRM_CURRENT_LIMIT", 0x718, "<I", 90000), # 90 А
            ("VRM_MAXIMUM_CURRENT_LIMIT", 0x71c, "<I", 120000), # 120 А
        ]
    }
]


def load_base_rom():
    for p in BASE_PATHS:
        if not os.path.exists(p):
            continue
        if p.lower().endswith(".zip"):
            with zipfile.ZipFile(p, "r") as zf:
                for name in zf.namelist():
                    if name.lower().endswith((".bin", ".rom")):
                        print(f"Извлечение базового ROM из архива: {name}")
                        return f"{p}::{name}", zf.read(name)
        else:
            with open(p, "rb") as f:
                return p, f.read()
    return None, None


def locate_amdsetup_body(rom_data):
    marker = b"AmdSetup\x00"
    pos = rom_data.find(marker)
    if pos == -1:
        raise ValueError("Маркер AmdSetup не найден в образе BIOS")
    
    body_offset = 0x4CF
    if len(rom_data) > body_offset + 0x703 and struct.unpack_from("<H", rom_data, body_offset + 0x701)[0] == 3600:
        return body_offset
    return pos + len(marker)


def build_profiles():
    base_label, base_data = load_base_rom()
    if not base_data:
        print("Ошибка: базовый файл прошивки не найден")
        return False

    body_off = locate_amdsetup_body(base_data)
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(LOCAL_OUT_DIR, exist_ok=True)
    os.makedirs(r"tools\patch-build\out", exist_ok=True)

    manifest = {
        "base_image": base_label,
        "base_md5": hashlib.md5(base_data).hexdigest(),
        "amdsetup_body_offset": f"0x{body_off:X}",
        "profiles": []
    }

    for prof in PROFILES:
        img = bytearray(base_data)
        changes_log = []
        for name, off, fmt, val in prof["patches"]:
            abs_off = body_off + off
            sz = struct.calcsize(fmt)
            old_bytes = img[abs_off:abs_off + sz]
            new_bytes = struct.pack(fmt, val)
            img[abs_off:abs_off + sz] = new_bytes
            changes_log.append({
                "parameter": name,
                "amdsetup_offset": f"0x{off:X}",
                "rom_offset": f"0x{abs_off:X}",
                "old_hex": old_bytes.hex(),
                "new_hex": new_bytes.hex(),
                "new_val": val
            })

        out_path = os.path.join(OUT_DIR, prof["name"] + ".bin")
        with open(out_path, "wb") as f:
            f.write(img)

        with open(os.path.join(LOCAL_OUT_DIR, prof["name"] + ".bin"), "wb") as f:
            f.write(img)

        with open(os.path.join(r"tools\patch-build\out", prof["name"] + ".bin"), "wb") as f:
            f.write(img)

        out_md5 = hashlib.md5(img).hexdigest()
        manifest["profiles"].append({
            "name": prof["name"],
            "file": out_path,
            "md5": out_md5,
            "description": prof["description"],
            "changes": changes_log
        })
        print(f"Собран: {out_path} [MD5: {out_md5}]")

    manifest_path = os.path.join(OUT_DIR, "build_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    with open(os.path.join(LOCAL_OUT_DIR, "build_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    with open(os.path.join(r"tools\patch-build\out", "build_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Манифест записан: {manifest_path}")
    return True


if __name__ == "__main__":
    import sys
    success = build_profiles()
    sys.exit(0 if success else 1)



if __name__ == "__main__":
    build_profiles()
