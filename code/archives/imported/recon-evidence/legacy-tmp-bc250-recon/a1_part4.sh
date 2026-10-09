#!/usr/bin/env bash
set +e
OUT=/tmp/a1_part4.out
{
echo "=== PART4 kernel source + smu package ==="
KSRC=$(ls -d /home/OWNER/linux-cachyos-bc250* 2>/dev/null | head -1)
echo "KSRC=${KSRC:-none}"
if [ -n "${KSRC:-}" ] && [ -d "$KSRC" ]; then
  echo "--- soc15 cyan/vcn ---"
  grep -nE 'cyan_skillfish|Cyan Skillfish|CHIP_CYAN|IP_VERSION\(10, 1, 3\)|vcn_v2_0|vcn_v[0-9]' \
    "$KSRC/drivers/gpu/drm/amd/amdgpu/soc15.c" 2>/dev/null | head -80
  echo "--- cyan refs in amdgpu ---"
  grep -rnE 'cyan_skillfish|CYAN_SKILLFISH|chip_cyan' \
    "$KSRC/drivers/gpu/drm/amd/amdgpu/" 2>/dev/null | head -50
  echo "--- dpm/vcn power ---"
  grep -rnE 'dpm_set_vcn|PowerUpVcn|PowerDownVcn|AMDGPU_PP_SENSOR_VCLK|pp_dpm_vclk' \
    "$KSRC/drivers/gpu/drm/amd/" 2>/dev/null | head -40
  echo "--- VCN ip block type ---"
  grep -rnE 'AMD_IP_BLOCK_TYPE_VCN|vcn_harvest|VCN_H' \
    "$KSRC/drivers/gpu/drm/amd/amdgpu/" 2>/dev/null | head -40
fi
echo "--- pipx bc250_smu py files ---"
PIPX=/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc
if [ -d "$PIPX" ]; then
  find "$PIPX/lib" -type f -name '*.py' 2>/dev/null | head -40
  echo "--- VCN-ish symbols in package ---"
  grep -rnE 'VCN|Vcn|vclk|dclk|power_domain|domain' \
    "$PIPX/lib" --include='*.py' 2>/dev/null | head -40
  echo "--- msg map head ---"
  grep -rnE '0x[0-9A-Fa-f]+|MSG_|msg_' \
    "$PIPX/lib" --include='*.py' 2>/dev/null | head -60
fi
echo "--- mesa path ---"
ls -la /opt/bc250-gfx1013 2>/dev/null | head
echo "VK_DRIVER_FILES=${VK_DRIVER_FILES:-}"
echo "VK_ICD_FILENAMES=${VK_ICD_FILENAMES:-}"
command -v vulkaninfo >/dev/null && timeout 10 vulkaninfo --summary 2>&1 | head -30 || echo no_vulkaninfo
echo "--- journal amdgpu (may be empty loglevel=0) ---"
timeout 5 journalctl -k -b --no-pager 2>/dev/null | grep -iE 'amdgpu|vcn|psp|smu|firmware|skillfish' | tail -40 || echo journal_empty
echo "=== PART4 DONE ==="
} >"$OUT" 2>&1
echo wrote:$OUT
wc -c "$OUT"
