# B1f: annotated dispatcher command table (from b1_emul2 emulation), merged
# with known applier identities. Produces evidence/b1_cmdmap.txt.
import struct
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
CON = ROM[0x984F00:0x984F00 + 0x1A790]
body = CON[0x100:]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.skipdata = True

out = []
P = out.append
P("== Карта команд mailbox-диспатчера fn@0xBA98 (cmd = [r4], switch с 0xBB10) ==")
P("   Проверено конкретной эмуляцией цепочки сравнений + tbb-таблиц (b1_emul2.py).")
P("")
P("== Ключевые применители политик ==")
P("  cmd 0x1033    -> arm 0xC344 -> bl fn@0x20D4  (СЕКВЕНСЕР; группы 0x201,0x205,0x203,0x20A,0x20B,0x210)")
P("  cmd 0xFFFF0001-> arm 0xC1BC -> bl fn@0xFE04 (ПОЛНЫЙ ПРИМЕНИТЕЛЬ «применить всё»)")
P("  cmd 0xFFFF0005-> arm 0xC1BC -> bl fn@0xFE04 (второй вход того же arm)")
P("  cmd 0x100C    -> arm 0xC0D0 -> bl fn@0x13468 @0xC0DA ($PS1-ЗАГРУЗЧИК блоба)")
P("  cmd 0x1000    -> arm 0xBF6A -> bl fn@0x946C @0xBF6E (ДОНОР-обработчик -> 0x9606 -> fn@0xA4E4)")
P("  cmd 0x310F    -> arm 0xC630 -> bl fn@0xCA78 @0xC632 (-> fn@0x1EF4, группа 0x211)")
P("  cmd 0x3110    -> arm 0xC638 -> bl fn@0xCAA4 (группа 0x214)")
P("  cmd 0x1026    -> arm 0xC2B0 -> bl 0x20D0 -> fn@0x1EC4 (10 фиксированных пар)")
P("  cmd 0x1005    -> arm 0xC022 -> bl fn@0xD1FC (крипто-верификатор RSA/SHA)")
P("  cmd 0x1040    -> arm 0xC3B4 -> svc 0x9e (прямой гипервызов)")
P("")
P("== Проверка гипотезы «командные слова группы 0x210 = команды диспатчера» ==")
P("  Все 12 слов E814 и все их маски (raw, &0xFFFF, >>16, &0xFFF, |0x1000/0x2000/0x3000)")
P("  НЕ попадают ни в один arm диспатчера (эмуляция: default -> выход 0xC7AA).")
P("  Слова — ЗНАЧЕНИЯ пар группы 0x210: применяются секвенсером fn@0x20D4 через")
P("  fn@0x2178 как svc 0x7c(0x0003E814, слово, 4); пара-триггер: svc 0x7c(0x0003E810, значение, 4).")
P("  Сток: 0x3E810->0; донор: 0x3E810->6 (патч D3-B2), слово донора 0x2544C382.")
P("  Дополнительные пары донора: 0x1F8A4->0xB; 0x1F820->0x185103.")
P("")
P("== Полная таблица (cmd -> arm-точка входа -> первый bl/svc) ==")
import re
prev = None
for line in open(r"C:\Users\OWNER\bc250-bios\evidence\b1_emul2.txt", errors="replace"):
    m = re.match(r"\s+cmd (0x[0-9a-f]+)(?:\.\.(0x[0-9a-f]+))?\s+-> (0x[0-9a-f]+)\s+(.*?)\s+;\s+action: (.*)", line)
    if m:
        lo, hi, addr, instr, act = m.group(1), m.group(2) or m.group(1), m.group(3), m.group(4), m.group(5)
        if "add sp, #0x24" in instr:
            continue  # default/exit
        P("  cmd %-10s %s -> %#-8s %s" % (lo if lo == hi else lo + ".." + hi, "", addr, act))

open(r"C:\Users\OWNER\bc250-bios\evidence\b1_cmdmap.txt", "w").write("\n".join(out))
print("written b1_cmdmap.txt, %d lines" % len(out))
