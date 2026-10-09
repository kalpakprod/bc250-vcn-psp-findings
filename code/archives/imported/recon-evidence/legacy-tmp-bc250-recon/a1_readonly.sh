#!/usr/bin/env bash
# A1 read-only VCN recon for BC-250. No MMIO, no SMU writes, no firmware install.
set -uo pipefail
OUT="${1:-/tmp/a1_vcn_readonly.out}"
TS=$(date -Is 2>/dev/null || date)
{
echo "############ A1 READ-ONLY VCN RECON ############"
echo "ts=$TS"
echo "host=$(hostname) user=$(whoami)"
echo

echo "############ KERNEL / CMDLINE ############"
uname -a
cat /proc/cmdline; echo
echo "--- modules ---"
lsmod | grep -iE 'amdgpu|amdxcp|drm|vcn|psp' || true
echo "--- amd_psp module ---"
lsmod | grep -i amd_psp || echo "amd_psp: not loaded"
modinfo amd_psp 2>/dev/null | head -5 || echo "amd_psp: no modinfo"

echo
echo "############ GPU PCI ############"
lspci -nn | grep -iE '1002|vga|display|multimedia|audio' || true
echo "--- 13fe verbose ---"
lspci -d 1002:13fe -vv 2>/dev/null | head -80 || true
echo "--- BARs (names only, no mmap) ---"
for d in /sys/bus/pci/devices/*/vendor; do
  v=$(cat "$d" 2>/dev/null)
  [ "$v" = "0x1002" ] || continue
  dev=$(dirname "$d")
  echo "DEV=$dev"
  cat "$dev/device" 2>/dev/null; echo
  ls -l "$dev/resource"* 2>/dev/null | head -20
  echo "enable=$(cat "$dev/enable" 2>/dev/null) irq=$(cat "$dev/irq" 2>/dev/null)"
done

echo
echo "############ DRM / MEDIA NODES ############"
ls -l /dev/dri/ 2>/dev/null || true
ls -l /dev/video* /dev/media* 2>/dev/null || echo "no /dev/video* or /dev/media*"
command -v vainfo >/dev/null && { echo "--- vainfo ---"; vainfo 2>&1 | head -40; } || echo "vainfo: absent"
command -v vdpauinfo >/dev/null && { echo "--- vdpauinfo ---"; vdpauinfo 2>&1 | head -20; } || echo "vdpauinfo: absent"
command -v ffmpeg >/dev/null && ffmpeg -hide_banner -hwaccels 2>&1 | head -20 || true

echo
echo "############ AMDGPU SYSFS (read-only) ############"
for card in /sys/class/drm/card[0-9]; do
  [ -e "$card/device/vendor" ] || continue
  vend=$(cat "$card/device/vendor" 2>/dev/null || true)
  [ "$vend" = "0x1002" ] || continue
  echo "=== $card ==="
  echo "device=$(cat "$card/device/device" 2>/dev/null) rev=$(cat "$card/device/revision" 2>/dev/null)"
  for f in firmware_info ip_discovery ip_blocks gpu_metrics pp_dpm_sclk pp_dpm_mclk pp_dpm_fclk pp_dpm_socclk pp_dpm_vclk pp_dpm_dclk pp_features pp_power_profile_mode current_link_speed current_link_width mem_info_vram_total mem_info_vram_used mem_info_gtt_total; do
    p="$card/device/$f"
    if [ -e "$p" ]; then
      echo "--- $f ---"
      # binary-ish metrics: hexdump head only
      case "$f" in
        gpu_metrics|firmware_info|ip_discovery|ip_blocks)
          wc -c < "$p" 2>/dev/null | awk '{print "bytes="$1}'
          od -An -tx1 -N 256 "$p" 2>/dev/null | head -20
          # also try strings for firmware_info
          if [ "$f" = "firmware_info" ] || [ "$f" = "ip_blocks" ]; then
            cat "$p" 2>/dev/null | tr '\0' '\n' | head -40
          fi
          ;;
        *)
          head -c 4096 "$p" 2>/dev/null; echo
          ;;
      esac
    else
      echo "missing: $f"
    fi
  done
  # debugfs if mounted and readable (no writes)
  if [ -d /sys/kernel/debug/dri ]; then
    echo "--- debugfs dri ---"
    ls /sys/kernel/debug/dri/ 2>/dev/null || echo "debugfs dri not readable"
  fi
done

echo
echo "############ HWMON / CLOCKS (safe) ############"
for h in /sys/class/drm/card*/device/hwmon/hwmon*; do
  [ -d "$h" ] || continue
  echo "=== $h ==="
  for f in "$h"/name "$h"/temp*_input "$h"/freq*_input "$h"/power*_average "$h"/power*_cap "$h"/fan*_input "$h"/pwm*; do
    [ -e "$f" ] || continue
    # skip pwm write nodes content if not readable; still list
    if [ -r "$f" ]; then
      echo "$(basename "$f")=$(cat "$f" 2>/dev/null)"
    else
      echo "$(basename "$f")=UNREADABLE"
    fi
  done
done

echo
echo "############ FIRMWARE BLOBS ############"
echo "--- cyan_skillfish* ---"
ls -la /lib/firmware/amdgpu/cyan_skillfish* 2>/dev/null || echo "none"
echo "--- *vcn* ---"
ls -la /lib/firmware/amdgpu/*vcn* 2>/dev/null || echo "none"
echo "--- find cyan*vcn anywhere (maxdepth limited) ---"
sudo -n find /lib/firmware /usr/lib/firmware /home -maxdepth 5 -iname '*cyan*vcn*' 2>/dev/null | head -20 || true
sudo -n find /lib/firmware /usr/lib/firmware -maxdepth 4 -iname '*skillfish*vcn*' 2>/dev/null | head -20 || true
echo "--- initramfs mention (names only) ---"
ls /boot 2>/dev/null | head -40

echo
echo "############ SMU READ-ONLY (known-safe msgs only) ############"
# Uses bc250_smu if present. Only query APIs already used successfully on this board.
sudo -n python3 - <<'PY' 2>&1 || echo "smu python probe failed"
import sys
try:
    from bc250_smu.api import Bc250Smu
except Exception as e:
    print("import_fail", e)
    sys.exit(0)
s = Bc250Smu(use_flock=True, allow_queue0=True)
# open via context if available
open_fn = getattr(s, "__enter__", None)
try:
    if open_fn:
        s.__enter__()
    else:
        # older API may open in ctor
        pass
except Exception as e:
    print("open_fail", type(e).__name__, e)
    sys.exit(0)

def call(label, fn, *a, **k):
    try:
        r = fn(*a, **k)
        print(f"{label} = {r!r}")
    except Exception as e:
        print(f"{label} ERR {type(e).__name__}: {e}")

# only documented/known-safe reads
if hasattr(s, "check_test_message"):
    call("test_message", s.check_test_message)
if hasattr(s, "get_smu_version"):
    call("smu_version", s.get_smu_version)
elif hasattr(s, "smu_version"):
    call("smu_version", s.smu_version)
# generic msg helpers if present
for name in ("get_enabled_smu_features", "query_active_wgp", "query_gfxclk", "get_gfxclk", "query_enabled_smu_features"):
    if hasattr(s, name):
        call(name, getattr(s, name))
# dump public callables (names only)
names = sorted(n for n in dir(s) if not n.startswith("_") and callable(getattr(s, n, None)))
print("api_methods:", ", ".join(names[:80]))
try:
    s.__exit__(None, None, None)
except Exception:
    pass
PY

echo
echo "############ KERNEL SOURCE GREP (local tree) ############"
KSRC=$(ls -d /home/OWNER/linux-cachyos-bc250* 2>/dev/null | head -1)
echo "KSRC=${KSRC:-none}"
if [ -n "${KSRC:-}" ] && [ -d "$KSRC" ]; then
  echo "--- soc15 / cyan / vcn registration ---"
  grep -nE 'cyan_skillfish|Cyan Skillfish|CHIP_CYAN|IP_VERSION\(10, 1, 3\)|vcn_v2_0|vcn_v[0-9]' \
    "$KSRC/drivers/gpu/drm/amd/amdgpu/soc15.c" 2>/dev/null | head -60 || true
  echo "--- nv.o / gfxhub skip patterns ---"
  grep -rnE 'cyan_skillfish|CYAN_SKILLFISH|chip_cyan' \
    "$KSRC/drivers/gpu/drm/amd/amdgpu/" 2>/dev/null | head -40 || true
  echo "--- dpm_set_vcn / PowerUpVcn / VCN enable ---"
  grep -rnE 'dpm_set_vcn|PowerUpVcn|PowerDownVcn|vcn_enable|set_powergating_state.*vcn|AMDGPU_PP_SENSOR_VCLK|VCLK|DCLK' \
    "$KSRC/drivers/gpu/drm/amd/" 2>/dev/null | head -50 || true
  echo "--- harvest / ip discovery vcn ---"
  grep -rnE 'VCN_H|vcn_harvest|IP_DISCOVERY.*VCN|AMD_IP_BLOCK_TYPE_VCN' \
    "$KSRC/drivers/gpu/drm/amd/amdgpu/" 2>/dev/null | head -40 || true
fi

echo
echo "############ BC250-SMU-OC PACKAGE SURFACE ############"
SP=$(find /home/OWNER -maxdepth 8 -type d -path '*bc250*smu*' 2>/dev/null | head -5)
echo "paths:"
echo "$SP"
PIPX=/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc
if [ -d "$PIPX" ]; then
  echo "--- pipx site-packages tree ---"
  find "$PIPX/lib" -type f -name '*.py' 2>/dev/null | head -40
  echo "--- msg constants / VCN-ish names ---"
  grep -rnE 'VCN|Vcn|vclk|dclk|power.?domain|0x23|msg_|MSG_|domain' \
    "$PIPX/lib" --include='*.py' 2>/dev/null | head -60 || true
fi

echo
echo "############ SERVICES / BASELINE ############"
systemctl list-units --type=service --all 2>/dev/null | grep -iE 'bc250|smu|gpu|fan|netconsole|telemetry' || true
echo "--- gpu fixed conf ---"
sudo -n cat /etc/bc250-gpu-fixed.conf 2>/dev/null || echo "no /etc/bc250-gpu-fixed.conf"
echo "--- cu layout ---"
systemctl is-active bc250-cu-layout.service bc250-cpu-oc.service bc250-gpu-fixed.service bc250-netconsole.service 2>/dev/null || true

echo
echo "############ JOURNAL / NETCONSOLE HINTS ############"
# journal may be empty if loglevel=0; still try
journalctl -k -b --no-pager 2>/dev/null | grep -iE 'amdgpu|vcn|psp|smu|firmware|skillfish' | tail -80 || echo "journal empty/no match"
echo "--- local agent-reach logs if any ---"
ls -la /home/OWNER/.agent-reach/bc250/ 2>/dev/null || true

echo
echo "############ MESA / VULKAN (context only) ############"
echo "VK_DRIVER_FILES=${VK_DRIVER_FILES:-}"
echo "VK_ICD_FILENAMES=${VK_ICD_FILENAMES:-}"
ls -la /opt/bc250-gfx1013 2>/dev/null | head || echo "no /opt/bc250-gfx1013"
command -v vulkaninfo >/dev/null && vulkaninfo --summary 2>&1 | head -40 || echo "vulkaninfo absent"

echo
echo "############ DONE A1 ############"
} >"$OUT" 2>&1
echo "rc=$? wrote $OUT bytes=$(wc -c <"$OUT" 2>/dev/null)"
