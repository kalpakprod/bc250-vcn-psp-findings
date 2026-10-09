#!/usr/bin/env bash
set -euo pipefail

# EDK2 build script for Bc250VcnUnlockDxe (.ffs generation for AMI BIOS injection)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$SCRIPT_DIR/Bc250VcnUnlockPkg"
MODULE_NAME="Bc250VcnUnlockDxe"
MODULE_GUID="b6250780-7e00-4203-900c-23443b1413fe"
ARCH="${ARCH:-X64}"
TARGET="${TARGET:-RELEASE}"
TOOL_CHAIN_TAG="${TOOL_CHAIN_TAG:-GCC5}"

echo "=== Building Bc250VcnUnlockDxe for ${ARCH} (${TARGET}) ==="
if [[ -z "${WORKSPACE:-}" ]]; then
    echo "Setting up workspace..."
    export WORKSPACE="$SCRIPT_DIR/Build/Workspace"
    mkdir -p "$WORKSPACE"
    ln -sfn "$PKG_DIR" "$WORKSPACE/Bc250VcnUnlockPkg"
fi

echo "To build in an EDK2 environment:"
echo "  build -a ${ARCH} -t ${TOOL_CHAIN_TAG} -b ${TARGET} -p Bc250VcnUnlockPkg/Bc250VcnUnlockPkg.dsc -m Bc250VcnUnlockPkg/Bc250VcnUnlockDxe/Bc250VcnUnlockDxe.inf"
echo "Output will produce ${MODULE_NAME}.ffs for injection into DXE Firmware Volume using UEFITool."
