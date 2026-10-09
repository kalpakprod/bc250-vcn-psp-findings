#!/usr/bin/env bash
set -Eeuo pipefail

readonly REPO='/home/OWNER/linux-cachyos-bc250'
readonly BUILD_DIR='/games/bc250-vcn-stable-src'
readonly PATCH_0009="$REPO/patches/kernel-7.2/0009-bc250-vcn-safe-direct-load.patch"
readonly PATCH_0011='/tmp/0011-bc250-vcn-probe-mode.patch'
readonly CHECKER='/tmp/check_vcn_probe_patch.py'
readonly INJECTOR='/tmp/inject_vcn_probe_pkgbuild.py'
readonly EXPECTED_RELEASE='7.2.0-1.92-cachyos-vcn-bc250'

fail() {
    printf 'VCN_PROBE_PREPARE_FAIL %s\n' "$*" >&2
    exit 1
}

[[ -f "$PATCH_0009" ]] || fail "missing patch: $PATCH_0009"
[[ -f "$PATCH_0011" ]] || fail "missing patch: $PATCH_0011"
[[ -f "$CHECKER" ]] || fail "missing checker: $CHECKER"
[[ -f "$INJECTOR" ]] || fail "missing injector: $INJECTOR"

env CACHYOS_SOURCE_VARIANT=linux-cachyos BC250_PKGREL=1 BUILD_DIR="$BUILD_DIR" "$REPO/scripts/prepare-pkgbuild.sh"

cp -- "$PATCH_0009" "$PATCH_0011" "$BUILD_DIR/"
python3 "$INJECTOR" "$BUILD_DIR/PKGBUILD" \
    "$BUILD_DIR/${PATCH_0009##*/}" "$BUILD_DIR/${PATCH_0011##*/}"

(
    cd "$BUILD_DIR"
    makepkg --nobuild --nodeps --noconfirm --skippgpcheck
)

source_candidates=()
for candidate in "$BUILD_DIR"/src/*; do
    [[ -d "$candidate" && -f "$candidate/Makefile" \
        && -d "$candidate/drivers/gpu/drm/amd/amdgpu" ]] \
        && source_candidates+=("$candidate")
done
(( ${#source_candidates[@]} == 1 )) \
    || fail "expected exactly one kernel source child, found ${#source_candidates[@]}"
source_dir=${source_candidates[0]}

python3 "$CHECKER" "$source_dir/drivers/gpu/drm/amd/amdgpu"
release=$(make -s -C "$source_dir" kernelrelease)
[[ "$release" == "$EXPECTED_RELEASE" ]] \
    || fail "kernelrelease mismatch: expected $EXPECTED_RELEASE, got $release"

printf 'VCN_PROBE_PREPARE_PASS release=%s\n' "$release"
