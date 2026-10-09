#!/usr/bin/env python3
# Standalone integrity check for BC-250 D3 test images (no dependencies).
# Usage: py verify_image.py <image.bin>
import sys, hashlib, struct

KNOWN = {
    "7607a34caeca1ffb95e1f7c52ca227d5": "00_BASE-reference_stock (или твой сток, если md5 совпал)",
    "67b8a7fd8c9d3e47fd8775518eff0c7e": "01_D3-C SIGNED-gasket-relocation (механика)",
    "448f5df5dfd44b95cc82f5b170dfa94f": "02_D3-B2 MAIN ACPB-DFG-i + gasket A+B + TOS-политика A+B unsigned",
    "bd2605e5869b21ec7426e3084d69aec8": "03_D3-A CONTROL APCB-DFG-i only",
}
DIR, BHD, APCB = 0x8E0000, 0xAB0000, 0xAB1000


def fletcher32(data):
    s1 = s2 = 0
    for i in range(0, len(data), 2):
        w = data[i] | (data[i + 1] << 8)
        s1 = (s1 + w) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


def main(path):
    b = open(path, "rb").read()
    problems = []
    print("файл:", path)
    print("размер:", len(b), "(ожидается 16777216)")
    if len(b) != 16777216:
        problems.append("размер не 16МБ")
    md5 = hashlib.md5(b).hexdigest()
    print("md5:", md5, "->", KNOWN.get(md5, "НЕИЗВЕСТНЫЙ образ (не из пакета!)"))
    if md5 not in KNOWN:
        problems.append("md5 не совпадает ни с одним образом пакета")

    # --- PSP dir ---
    e24 = e45 = None
    if b[DIR:DIR + 4] != b"$PSP":
        problems.append("нет $PSP @0x8E0000")
    else:
        cnt = struct.unpack_from("<I", b, DIR + 8)[0]
        calc = fletcher32(b[DIR + 8: DIR + 0x10 + 16 * cnt])
        stored = struct.unpack_from("<I", b, DIR + 4)[0]
        print("PSP-каталог: записей=%d контрольная сумма: %s (%#x)" % (cnt, "OK" if calc == stored else "ОШИБКА", stored))
        if calc != stored:
            problems.append("контрольная сумма PSP-каталога неверна")
        e24 = e45 = None
        for i in range(cnt):
            eo = DIR + 0x10 + 16 * i
            t = struct.unpack_from("<I", b, eo)[0]
            if t == 0x24:
                e24 = struct.unpack_from("<IIQ", b, eo)
            if t == 0x45:
                e45 = struct.unpack_from("<IIQ", b, eo)
        print("запись 0x24 (блок политики): size=%#x loc=%#x" % (e24[1], e24[2]))
        print("запись 0x45 (TOS-политика): size=%#x loc=%#x" % (e45[1], e45[2]))

    # --- BHD dir ---
    if b[BHD:BHD + 4] != b"$BHD":
        problems.append("нет $BHD @0xAB0000")
    else:
        cnt = struct.unpack_from("<I", b, BHD + 8)[0]
        calc = fletcher32(b[BHD + 8: BHD + 0x10 + 24 * cnt])
        stored = struct.unpack_from("<I", b, BHD + 4)[0]
        print("BIOS-каталог: записей=%d контрольная сумма: %s" % (cnt, "OK" if calc == stored else "ОШИБКА"))
        if calc != stored:
            problems.append("контрольная сумма BIOS-каталога неверна")

    # --- APCB ---
    if b[APCB:APCB + 4] != b"APCB":
        problems.append("нет APCB @0xAB1000")
    else:
        size = struct.unpack_from("<I", b, APCB + 8)[0]
        cks = b[APCB + 0x10]
        calc = (0x100 - sum(b[APCB + i] for i in range(size) if i != 0x10)) & 0xFF
        w130 = b[APCB + 0x130:APCB + 0x134].hex()
        w16c = b[APCB + 0x16C:APCB + 0x170].hex()
        print("APCB: size=%#x контр.байт=%#x %s; строки-джокеры: +%#x=%s +%#x=%s" % (
            size, cks, "OK" if cks == calc else "ОШИБКА", 0x130, w130, 0x16C, w16c))
        if cks != calc:
            problems.append("контрольный байт APCB неверен")
        patched = w130 == "00ff7f00" and w16c == "00ff7f00"
        stock = w130 == "00ff1f00" and w16c == "00ff1f00"
        print("APCB-патч: %s" % ("ПРИМЕНЁН (0x7f)" if patched else ("сток (0x1f)" if stock else "НЕИЗВЕСТНОЕ состояние")))
        if not (patched or stock):
            problems.append("строки-джокеры APCB в неожиданном состоянии")

    # --- per-image expectations ---
    kind = md5 if md5 in KNOWN else None
    if kind == "67b8a7fd8c9d3e47fd8775518eff0c7e":  # D3-C
        blob_new = b[0x9E0000:0x9E0000 + 0x2E50]
        blob_old = b[0x982000:0x982000 + 0x2E50]
        print("D3-C: блоб на новом месте = оригиналу:", "ДА (подпись валидна)" if blob_new == blob_old else "НЕТ")
        if blob_new != blob_old:
            problems.append("D3-C: перенесённый блоб не совпадает с оригиналом")
        if e24 is None or not (e24[1] == 0x2E50 and e24[2] == 0xFF9E0000):
            problems.append("D3-C: запись 0x24 не указывает на 0x9E0000/0x2E50")
    if kind == "448f5df5dfd44b95cc82f5b170dfa94f":  # D3-B2
        if e24 is None or not (e24[1] == 0x3010 and e24[2] == 0xFF9E0000):
            problems.append("D3-B2: запись 0x24 не указывает на 0x9E0000/0x3010")
        if e45 is None or not (e45[1] == 0x708 and e45[2] == 0xFF9E4000):
            problems.append("D3-B2: запись 0x45 не указывает на 0x9E4000/0x708")
        g = 0x9E0000
        s14 = struct.unpack_from("<Q", b, g + 0x14)[0]
        tot = struct.unpack_from("<I", b, g + 0x6C)[0]
        body = b[g + 0x100: g + 0x100 + 0x2E10]
        off, groups = 0x40, []
        while off + 8 <= len(body):
            t, c = struct.unpack_from("<II", body, off)
            if t == 0 or t > 0xFFFF or c > 0x100000:
                break
            groups.append((t, c))
            off += 8 + c * 8
        nvcn = sum(1 for i in range(0, len(body) - 8, 4) if 0x0900C000 <= struct.unpack_from("<I", body, i)[0] <= 0x0900CFFF)

        def vals(body, addr):
            out, pat, i = [], struct.pack("<I", addr), -1
            while True:
                i = body.find(pat, i + 1)
                if i < 0:
                    return out
                if i % 4 == 0:
                    out.append(struct.unpack_from("<I", body, i + 4)[0])
        print("D3-B2 гаскет: size@14=%#x total@6C=%#x; группы=%s (конец %#x); VCN-банк=%d" % (
            s14, tot, [(hex(t), c) for t, c in groups], off, nvcn))
        if not (s14 == 0x2E10 and tot == 0x3010):
            problems.append("D3-B2: поля размеров гаскета неверны")
        if not (off == 0x2E10 and [t for t, _ in groups] == [0x201, 0x203, 0x210, 0x280, 0x281] and [c for _, c in groups] == [1281, 31, 13, 105, 31]):
            problems.append("D3-B2: структура групп гаскета нарушена")
        if nvcn != 56:
            problems.append("D3-B2: VCN-банк != 56 записей")
        for a, exp in ((0x03E810, [6]), (0x03A2011C, [0x107FF, 0x107FF]), (0x03A20124, [0x10FFF])):
            got = vals(body, a)
            print("  регистр %#010x -> %s (ожидается %s)" % (a, ["%#x" % v for v in got], ["%#x" % v for v in exp]))
            if got != exp:
                problems.append("D3-B2: значение регистра %#x неверное" % a)
        # --- TOS_SECURITY_POLICY blob @0x9E4000 ---
        p = 0x9E4000
        ps14 = struct.unpack_from("<Q", b, p + 0x14)[0]
        ptot = struct.unpack_from("<I", b, p + 0x6C)[0]
        pbody = b[p + 0x100: p + 0x100 + 0x508]
        poff, pgroups = 0x40, []
        while poff + 8 <= len(pbody):
            t, c = struct.unpack_from("<II", pbody, poff)
            if t == 0 or t > 0xFFFF or c > 0x100000:
                break
            pgroups.append((t, c))
            poff += 8 + c * 8
        print("D3-B2 TOS-политика: size@14=%#x total@6C=%#x; группы=%s (конец %#x)" % (
            ps14, ptot, [(hex(t), c) for t, c in pgroups], poff))
        if not (ps14 == 0x508 and ptot == 0x708):
            problems.append("D3-B2: поля размеров TOS-политики неверны")
        if not (poff == 0x508 and [t for t, _ in pgroups] == [0x210, 0x211, 0x280, 0x281] and [c for _, c in pgroups] == [13, 0, 105, 31]):
            problems.append("D3-B2: структура групп TOS-политики нарушена")
        for a, exp in ((0x03E810, [6]), (0x03A2011C, [0x107FF])):
            got = vals(pbody, a)
            print("  регистр %#010x -> %s (ожидается %s)" % (a, ["%#x" % v for v in got], ["%#x" % v for v in exp]))
            if got != exp:
                problems.append("D3-B2: значение регистра %#x в TOS-политике неверное" % a)
        vtail = []
        for i in range(0, len(pbody) - 8, 4):
            a = struct.unpack_from("<I", pbody, i)[0]
            if 0x0900C000 <= a <= 0x0900CFFF:
                vtail.append((a, struct.unpack_from("<I", pbody, i + 4)[0]))
        want = [(0x0900C234, 0), (0x0900C914, 0), (0x0900C930, 0), (0x0900CB80, 0), (0x0900C234, 1)]
        print("  VCN-хвост TOS-политики:", [("%#x" % a, "%#x" % v) for a, v in vtail])
        if vtail != want:
            problems.append("D3-B2: VCN-хвост TOS-политики не совпадает с донорским")
    if kind == "bd2605e5869b21ec7426e3084d69aec8":  # D3-A
        if e24 is None or not (e24[1] == 0x2E50 and e24[2] == 0xFF982000):
            problems.append("D3-A: запись 0x24 должна остаться стоковой")

    print()
    if problems:
        print("ПРОБЛЕМЫ:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("IMAGE OK — можно прошивать (не забудь: полный дамп чипа уже снят?)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("запуск: py verify_image.py <образ.bin>")
        sys.exit(2)
    main(sys.argv[1])
