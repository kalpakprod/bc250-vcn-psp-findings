# Directory checksum: AGESA header says "32 bit CRC of header items below and the entire table".
# BHD entries are 24 bytes (with Destination) -> PSP table=[0,0x1A0), BHD table=[0,0x70).
# Try CRC32 variants + Fletcher32 over [0x08,end) and [0,end) with zeroed checksum.
import struct, zlib

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
b = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()

DIRS = [
    ("PSP", 0x8E0000, 0x63FFFCC8, 19, 16),
    ("BHD", 0xAB0000, 0xECE7B2E6, 4, 24),
]


def fletcher32(data):
    # classic fletcher32 over 16-bit words
    if len(data) % 2:
        data = data + b"\x00"
    s1 = s2 = 0
    for i in range(0, len(data), 2):
        w = data[i] | (data[i + 1] << 8)
        s1 = (s1 + w) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


def crc32c(data):
    # CRC-32C (Castagnoli), reflected
    poly = 0x82F63B78
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ poly if crc & 1 else crc >> 1
    return crc ^ 0xFFFFFFFF


def crc32_posix(data):
    poly = 0x04C11DB7
    crc = 0
    for byte in data:
        crc ^= byte << 24
        crc &= 0xFFFFFFFF
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFFFFFFFF if crc & 0x80000000 else (crc << 1) & 0xFFFFFFFF
    return crc


for name, base, stored, count, esz in DIRS:
    end = base + 0x10 + count * esz
    tbl = b[base:end]
    tbl_z = bytearray(tbl)
    tbl_z[4:8] = b"\x00\x00\x00\x00"
    print("\n%s dir: table=[%#x,%#x) size=%#x stored=%#x" % (name, base, end, end - base, stored))
    cands = {
        "crc32 [0x08,end)": zlib.crc32(tbl[8:]) & 0xFFFFFFFF,
        "crc32 [0,end) zcks": zlib.crc32(bytes(tbl_z)) & 0xFFFFFFFF,
        "crc32 [0x08,end) neg": (-zlib.crc32(tbl[8:])) & 0xFFFFFFFF,
        "crc32 [0,end) zcks neg": (-zlib.crc32(bytes(tbl_z))) & 0xFFFFFFFF,
        "fletcher32 [0x08,end)": fletcher32(tbl[8:]),
        "fletcher32 [0,end) zcks": fletcher32(bytes(tbl_z)),
        "crc32c [0x08,end)": crc32c(tbl[8:]),
        "crc32c [0,end) zcks": crc32c(bytes(tbl_z)),
        "crc32posix [0x08,end)": crc32_posix(tbl[8:]),
        "crc32posix [0,end) zcks": crc32_posix(bytes(tbl_z)),
        "crc32 [0x0C,end)": zlib.crc32(tbl[0xC:]) & 0xFFFFFFFF,
        "crc32 [0x10,end)": zlib.crc32(tbl[0x10:]) & 0xFFFFFFFF,
    }
    for k, v in cands.items():
        print("  %-28s %#010x %s" % (k, v, "<<<< MATCH" if v == stored else ""))
