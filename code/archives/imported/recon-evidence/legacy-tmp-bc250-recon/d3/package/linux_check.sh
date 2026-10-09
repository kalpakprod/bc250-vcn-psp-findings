#!/bin/sh
# BC-250 VCN check script. Run as root ON THE BOARD:  sh linux_check.sh
# Collects driver + direct-hardware evidence of VCN state into vcn_check_<date>.txt
OUT="vcn_check_$(date +%Y%m%d_%H%M%S).txt"
exec > >(tee "$OUT") 2>&1 || exec > "$OUT" 2>&1

echo "==== BC-250 VCN CHECK $(date) ===="
echo "== system =="
uname -a
cat /proc/cmdline 2>/dev/null
echo

echo "== dmesg: amdgpu / vcn / psp / firmware =="
dmesg 2>/dev/null | grep -iE 'amdgpu|vcn|uvd|psp|firmware' | tail -n 120
echo "---- dmesg tail (context) ----"
dmesg 2>/dev/null | tail -n 40
echo

echo "== amdgpu firmware info =="
for d in /sys/kernel/debug/dri/*/; do
  echo "-- $d"
  cat "$d/amdgpu_firmware_info" 2>/dev/null | grep -iE 'vcn|uvd|loaded|firmware' || echo "   (нет amdgpu_firmware_info или debugfs недоступен)"
done
ls /lib/firmware/amdgpu/ 2>/dev/null | grep -i vcn || echo "(нет *vcn* в /lib/firmware/amdgpu)"
echo

echo "== GPU в PCI =="
lspci -nn 2>/dev/null | grep -iE '1002|vga|display' || echo "(lspci нет)"
lspci -v 2>/dev/null | grep -A3 -iE 'vga|display' | grep -i memory
echo "== /proc/iomem (amdgpu/drm) =="
grep -iE 'amdgpu|drm' /proc/iomem 2>/dev/null || echo "(нет amdgpu в iomem)"
echo

echo "== MMIO: прямой опрос регистров VCN (не зависит от драйвера) =="
# базовый физ.адрес MMIO-области GPU:
GPU_BASE=$(awk 'BEGIN{FS=":"} /amdgpu|drm/ {split($2,a,"-"); print a[1]}' /proc/iomem 2>/dev/null | head -n1)
if [ -z "$GPU_BASE" ]; then
  for r in /sys/class/drm/card*/device/resource0; do
    [ -f "$r" ] && GPU_BASE=$(awk '{printf "%x", $1; exit}' "$r")
  done
fi
echo "GPU MMIO base: ${GPU_BASE:-НЕ НАЙДЕН}"
DEVMEM=$(command -v devmem || command -v busybox)
probe() {
  addr=$1
  if [ -n "$DEVMEM" ]; then
    if [ "$DEVMEM" = "$(command -v busybox)" ]; then busybox devmem "$addr" 32
    else devmem "$addr" 32; fi
  else
    python3 - "$addr" <<'EOF'
import sys, mmap, struct
a = int(sys.argv[1], 16)
try:
    f = open("/dev/mem", "r")
    m = mmap.mmap(f.fileno(), 8, mmap.MAP_SHARED, mmap.PROT_READ, offset=a & ~0xFFF)
    print("%08x" % struct.unpack_from("<I", m, a & 0xFFF)[0])
except Exception as e:
    print("нет доступа к /dev/mem:", e)
EOF
  fi
}
if [ -n "$GPU_BASE" ]; then
  BASE=$(( 0x$GPU_BASE ))
  for off in 0x7800 0x7804 0x780c 0x7810 0x78d4 0x78000 0x78038 0x7803c 0x78060 0x78064; do
    printf "GPU+%-7s : " "$off"
    probe "$(printf '%x' $(( BASE + off )) )"
  done
else
  echo "(!) не смог определить базу MMIO — приложи вывод lspci -v в отчёт вручную"
fi
echo "(все значения ffffffff/00000000 и одинаковые = блок выключен; живые разные значения = блок включён)"
echo

echo "== vainfo (если установлен) =="
command -v vainfo >/dev/null && vainfo 2>&1 | head -n 40 || echo "(vainfo нет — не страшно)"
echo
echo "==== ГОТОВО. Этот файл приложи к отчёту: $OUT ===="
