#!/bin/bash
set -x
echo "=== SSH_OK ==="
uname -a
echo "=== whoami ==="
whoami
echo "=== bc250_smu pipx ==="
ls -d ~/.local/share/pipx/venvs/bc250-smu-oc 2>/dev/null
pipx list 2>/dev/null | grep -i bc250
echo "=== gpu pci ==="
lspci -nn | grep -iE 'vga|display|3d'
echo "=== dmesg vcn/psp/amdgpu ==="
dmesg | grep -iE 'vcn|psp|amdgpu|skillfish|oberon' | head -40
echo "=== firmware amdgpu vcn/psp ==="
ls -la /lib/firmware/amdgpu/ 2>/dev/null | grep -iE 'vcn|skillfish|psp'
echo "=== done ==="
