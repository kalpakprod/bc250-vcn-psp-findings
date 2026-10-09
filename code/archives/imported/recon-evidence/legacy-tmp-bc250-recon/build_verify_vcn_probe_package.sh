#!/usr/bin/env bash
set -Eeuo pipefail

build_dir=/games/bc250-vcn-stable-src
pkgbase=linux-cachyos-vcn-bc250
stock_pkgbase=linux-cachyos-bc250
pkgver=7.2.0-1.92
release=7.2.0-1.92-cachyos-vcn-bc250
output_dir=/tmp/bc250-vcn-probe-packages
kernel_package=${pkgbase}-${pkgver}-x86_64.pkg.tar.zst
headers_package=${pkgbase}-headers-${pkgver}-x86_64.pkg.tar.zst
module_path=usr/lib/modules/${release}/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko.zst
vmlinuz_path=usr/lib/modules/${release}/vmlinuz
headers_makefile_path=usr/lib/modules/${release}/build/Makefile
work_dir=

die() {
    printf 'VCN probe package failure: %s\n' "$*" >&2
    exit 1
}

package_version_or_absent() {
    local package=$1
    pacman -Q "$package" 2>/dev/null | awk '{print $2}' || printf 'absent\n'
}

remove_prior_package_files() {
    local directory=$1
    local -a package_files=()

    shopt -s nullglob
    package_files=("$directory"/"$pkgbase"-*.pkg.tar.*)
    shopt -u nullglob

    if ((${#package_files[@]})); then
        rm -f -- "${package_files[@]}"
    fi
}

recreate_output_dir() {
    [[ ! -L "$output_dir" ]] || die "refusing symlinked output directory: $output_dir"
    mkdir -p -- "$output_dir"
    remove_prior_package_files "$output_dir"

    if find "$output_dir" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
        die "refusing to remove non-package output content: $output_dir"
    fi

    rmdir -- "$output_dir"
    mkdir -- "$output_dir"
}

require_pkginfo() {
    local package_file=$1
    local expected_name=$2
    local pkginfo actual_name actual_version

    pkginfo=$(bsdtar -xOf "$package_file" .PKGINFO) || die "cannot read .PKGINFO: $package_file"
    actual_name=$(printf '%s\n' "$pkginfo" | awk -F ' = ' '$1 == "pkgname" { print $2 }')
    actual_version=$(printf '%s\n' "$pkginfo" | awk -F ' = ' '$1 == "pkgver" { print $2 }')
    [[ "$actual_name" == "$expected_name" ]] || die "unexpected package name in $package_file: $actual_name"
    [[ "$actual_version" == "$pkgver" ]] || die "unexpected package version in $package_file: $actual_version"
}

require_archive_path() {
    local package_file=$1
    local expected_path=$2

    bsdtar -tf "$package_file" | grep -Fqx -- "$expected_path" \
        || die "missing $expected_path in $package_file"
}

cleanup_module_extract() {
    [[ -n "$work_dir" && -d "$work_dir" ]] || return 0
    rm -f -- "$work_dir/amdgpu.ko.zst" "$work_dir/amdgpu.ko"
    rmdir -- "$work_dir" 2>/dev/null || true
}

verify_module() {
    local package_file=$1
    local vermagic vermagic_release

    work_dir=$(mktemp -d /tmp/bc250-vcn-probe.XXXXXX)
    bsdtar -xOf "$package_file" "$module_path" >"$work_dir/amdgpu.ko.zst" \
        || die "cannot extract $module_path"
    zstd -d -q -c -- "$work_dir/amdgpu.ko.zst" >"$work_dir/amdgpu.ko" \
        || die "cannot decompress amdgpu module"

    vermagic=$(modinfo -F vermagic "$work_dir/amdgpu.ko") \
        || die "cannot read amdgpu vermagic"
    vermagic_release=${vermagic%% *}
    [[ "$vermagic_release" == "$release" ]] \
        || die "unexpected amdgpu vermagic: $vermagic"
    modinfo -F parm "$work_dir/amdgpu.ko" | grep -q '^bc250_vcn_mode:' \
        || die "amdgpu module lacks bc250_vcn_mode"
    modinfo -F firmware "$work_dir/amdgpu.ko" \
        | grep -Eq '^(amdgpu/)?navi10_vcn\.bin$' \
        || die "amdgpu module lacks navi10_vcn.bin firmware declaration"
}

trap cleanup_module_extract EXIT

[[ -d "$build_dir" ]] || die "missing build directory: $build_dir"
stock_version_before=$(pacman -Q "$stock_pkgbase" | awk '{print $2}') 
[[ -n "$stock_version_before" ]] || die "cannot determine installed $stock_pkgbase version"
installed_kernel_before=$(package_version_or_absent "$pkgbase")
installed_headers_before=$(package_version_or_absent "${pkgbase}-headers")

remove_prior_package_files "$build_dir"
recreate_output_dir

(
    cd "$build_dir"
    _processor_opt=generic_v3 KCFLAGS=-mtune=znver2 MAKEFLAGS="-j$(nproc)" \
        makepkg --noextract --noprepare --nodeps --noconfirm --skippgpcheck
)

build_kernel_package=$build_dir/$kernel_package
build_headers_package=$build_dir/$headers_package
shopt -s nullglob
built_packages=("$build_dir"/"$pkgbase"-*.pkg.tar.zst)
shopt -u nullglob
[[ ${#built_packages[@]} -eq 2 ]] \
    || die "expected exactly two $pkgbase package files, found ${#built_packages[@]}"
[[ -f "$build_kernel_package" && -f "$build_headers_package" ]] \
    || die "expected kernel and headers packages were not both produced"

require_pkginfo "$build_kernel_package" "$pkgbase"
require_pkginfo "$build_headers_package" "${pkgbase}-headers"
require_archive_path "$build_kernel_package" "$module_path"
require_archive_path "$build_kernel_package" "$vmlinuz_path"
require_archive_path "$build_headers_package" "$headers_makefile_path"
verify_module "$build_kernel_package"

install -m 0644 -- "$build_kernel_package" "$build_headers_package" "$output_dir/"
sha256sum -- "$output_dir/$kernel_package" "$output_dir/$headers_package"

stock_version_after=$(pacman -Q "$stock_pkgbase" | awk '{print $2}')
[[ "$stock_version_after" == "$stock_version_before" ]] \
    || die "$stock_pkgbase version changed: $stock_version_before -> $stock_version_after"
installed_kernel_after=$(package_version_or_absent "$pkgbase")
installed_headers_after=$(package_version_or_absent "${pkgbase}-headers")
[[ "$installed_kernel_after" == "$installed_kernel_before" ]] \
    || die "$pkgbase changed during build: $installed_kernel_before -> $installed_kernel_after"
[[ "$installed_headers_after" == "$installed_headers_before" ]] \
    || die "${pkgbase}-headers changed during build: $installed_headers_before -> $installed_headers_after"

printf 'VCN_PROBE_PACKAGE_PASS release=%s packages=2\n' "$release"
