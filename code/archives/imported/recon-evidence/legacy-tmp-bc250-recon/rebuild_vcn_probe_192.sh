#!/usr/bin/env bash
set -Eeuo pipefail

/tmp/prepare_vcn_probe_package.sh
/tmp/build_verify_vcn_probe_package.sh

echo VCN_PROBE_REBUILD_192_PASS
