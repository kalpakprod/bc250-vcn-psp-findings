#!/usr/bin/env bash
set -Eeuo pipefail

# Helper script for resuming or managing the user-unit build if needed
UNIT=bc250-vcn-build3.service
BUILD_DIR=/home/OWNER/linux-cachyos-bc250/build/linux-cachyos-rc
PKG_DEST=/tmp/bc250-vcn-packages

mkdir -p "$PKG_DEST"
cd "$BUILD_DIR"
export PKGDEST="$PKG_DEST"
exec makepkg --noextract --noprepare --nodeps --noconfirm --skippgpcheck
