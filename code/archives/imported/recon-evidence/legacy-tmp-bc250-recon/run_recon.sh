#!/usr/bin/env bash
set -uo pipefail
OUT=/tmp/recon_vcn.out
{
echo "############ KERNEL ############"
uname -a
echo "--- cmdline ---"; cat /proc/cmdline; echo
echo "############ GPU PCI ############"
lspci -nn | grep -iE 'vga|3d|display' | grep -i 1002 || echo "(no 1002 VGA)"
echo "--- 0x13fe detail ---"
lspci -d 1002:13fe -v 2>/dev/null | grep -iE 'slot|revision|class|region|kernel driver' | head -25 || echo "(0x13fe not present)"
echo
echo "############ amdgpu driver bound ############"
ls -l /sys/bus/pci/drivers/amdgpu/ 2>/dev/null | head; echo
echo "############ VCN firmware blobs ############"
echo "--- /lib/firmware/amdgpu (vcn/psp/skillfish/me) ---"
ls -la /lib/firmware/amdgpu/ 2>/dev/null | grep -iE 'vcn|psp|skillfish|^.*me_|sdma' || echo "(none)"
echo "--- full amdgpu dir (first 60) ---"
ls -la /lib/firmware/amdgpu/ 2>/dev/null | head -60
echo
echo "############ dmesg: amdgpu / vcn / psp / smu ############"
dmesg 2>/dev/null | grep -iE 'amdgpu|vcn|psp|smu|skillfish|cp|sdma' | tail -60 || echo "(dmesg empty)"
echo
echo "############ bc250-smu-oc / governor ############"
echo "--- pipx list bc250 ---"; pipx list 2>/dev/null | grep -i bc250 || echo "(pipx: no bc250)"
echo "--- which ---"; command -v bc250-smu-oc bc250-smu cyan-skillfish-governor 2>/dev/null || echo "(no bc250 bin on PATH)"
echo "--- services ---"; systemctl list-units --type=service 2>/dev/null | grep -iE 'bc250|governor|smu|skillfish' || echo "(no matching services)"
echo
echo "############ kernel source ############"
ls -d ~/linux-cachyos-bc250* 2>/dev/null || echo "(no linux-cachyos-bc250 source)"
KSRC=$(ls -d ~/linux-cachyos-bc250* 2>/dev/null | head -1)
if [ -n "$KSRC" ]; then
  echo "KSRC=$KSRC"
  echo "--- soc15.c: Cyan Skillfish / VCN ip_blocks ---"
  grep -nE 'Cyan Skillfish|cyan_skillfish|vcn_v2_0|IP_VERSION\(10, 1, 3\)|IP_BLOCK.*vcn' "$KSRC/drivers/gpu/drm/amd/amdgpu/soc15.c" 2>/dev/null | head -30 || echo "(no VCN refs in soc15.c)"
  echo "--- 40CU / extra core unlock mechanism (grep) ---"
  grep -rnE '40cu|40_cu|40CU|extra.*core|wgpr|enable.*core|unlock' "$KSRC/drivers/gpu/drm/amd/amdgpu/" 2>/dev/null | grep -iE 'skillfish|40cu|core' | head -20 || echo "(no 40CU unlock refs in kernel)"
  echo "--- SMU VcnPowerUp / Vcn messages ---"
  grep -rnE 'VcnPowerUp|Vcn.*Power|SMU_MSG.*Vcn|vcn.*power' "$KSRC/drivers/gpu/drm/amd/amdgpu/" 2>/dev/null | head -20 || echo "(no VcnPowerUp in smu)"
else
  echo "(no kernel source to grep)"
fi
echo
echo "############ bc250-smu-oc package internals (how unlock works) ############"
SP=$(find ~ -maxdepth 6 -type d -path '*bc250-smu-oc*' 2>/dev/null | head -1)
echo "SP=$SP"
if [ -n "$SP" ]; then
  echo "--- package tree ---"; find "$SP" -maxdepth 4 -type f \( -name '*.py' -o -name '*.toml' -o -name '*.cfg' \) 2>/dev/null | head -40
  echo "--- grep unlock/feature in package ---"; grep -rnE 'unlock|feature|enable|40cu|core|smu_msg|SMU_MSG' "$SP" 2>/dev/null | grep -iE 'py|toml' | head -30 || echo "(no unlock refs)"
fi
echo
echo "############ done ############"
} > "$OUT" 2>&1
echo "rc=$? wrote $OUT"
