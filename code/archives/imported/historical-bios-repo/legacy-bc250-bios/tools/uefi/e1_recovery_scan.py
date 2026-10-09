#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase E: scan candidate modules for boot-fail/recovery/clear-CMOS logic
strings (ASCII + UTF-16) to answer 'why no auto-fallback on bad timings'."""
import re

BASE = r"C:\Users\OWNER\bc250-bios\evidence\fv_extract" + "\\"
FILES = {
    "AMITSE": BASE + r"BC250_3.00.ROM.dump\2 4F1C52D3-D824-4D2A-A2F0-EC40C23C5916\0 9E21FD93-9C72-4C15-8C4B-E77F1DB2D792\0 EE4E5898-3914-4259-9D6E-DC7BD79403CF\1 Volume image section\0 5C60F367-A505-419A-859E-2A4FF6CA6FE5\182 AMITSE\0 EE4E5898-3914-4259-9D6E-DC7BD79403CF\0 PE32 image section\body.bin",
    "Bds": BASE + r"BC250_3.00.ROM.dump\2 4F1C52D3-D824-4D2A-A2F0-EC40C23C5916\0 9E21FD93-9C72-4C15-8C4B-E77F1DB2D792\0 EE4E5898-3914-4259-9D6E-DC7BD79403CF\1 Volume image section\0 5C60F367-A505-419A-859E-2A4FF6CA6FE5\5 Bds\1 PE32 image section\body.bin",
    "AmdMemAm4Pei": BASE + r"BC250_3.00.ROM.dump\3 61C0F511-A691-4F54-974F-B9A42172CE53\1 147923CE-D0E9-4C4F-9B7B-AC02F8BD2763\1 Volume image section\0 61C0F511-A691-4F54-974F-B9A42172CE53\19 AmdMemAm4Pei\1 TE image section\body.bin",
    "CbsBasePei": BASE + r"BC250_3.00.ROM.dump\3 61C0F511-A691-4F54-974F-B9A42172CE53\1 147923CE-D0E9-4C4F-9B7B-AC02F8BD2763\1 Volume image section\0 61C0F511-A691-4F54-974F-B9A42172CE53\32 CbsBasePei\1 TE image section\body.bin",
    "AmiAgesaPei": BASE + r"BC250_3.00.ROM.dump\3 61C0F511-A691-4F54-974F-B9A42172CE53\1 147923CE-D0E9-4C4F-9B7B-AC02F8BD2763\1 Volume image section\0 61C0F511-A691-4F54-974F-B9A42172CE53\31 AmiAgesaPei\1 TE image section\body.bin",
    "AmdSetupNvar": BASE + r"BC250_3.00.ROM.dump\0 FA4974FC-AF1D-4E5D-BDC5-DACD6D27BAEC\0 NVAR store\4 AmdSetup\body.bin",
    "CbsSetupDxe": BASE + r"BC250_3.00.ROM.dump\2 4F1C52D3-D824-4D2A-A2F0-EC40C23C5916\0 9E21FD93-9C72-4C15-8C4B-E77F1DB2D792\0 EE4E5898-3914-4259-9D6E-DC7BD79403CF\1 Volume image section\0 5C60F367-A505-419A-859E-2A4FF6CA6FE5\42 CbsSetupDxe\1 PE32 image section\body.bin",
}
KW = re.compile(r"(clear.?cmos|cmos|fail|train|recover|fallback|default|reset|count|watchdog|safe|hook|boot.?flow|first.?boot)", re.I)


def main():
    for name, path in FILES.items():
        try:
            b = open(path, "rb").read()
        except OSError as e:
            print("!!", name, e)
            continue
        a = [m.group().decode("latin1") for m in re.finditer(rb"[\x20-\x7e]{6,}", b)]
        u = [m.group().decode("utf-16-le", "ignore") for m in re.finditer(rb"(?:[\x20-\x7e]\x00){6,}", b)]
        print("=== %s (%d bytes)" % (name, len(b)))
        seen = set()
        for s in a + u:
            if KW.search(s) and s not in seen:
                seen.add(s)
                print("    %s" % s[:110])
        print()


if __name__ == "__main__":
    main()
