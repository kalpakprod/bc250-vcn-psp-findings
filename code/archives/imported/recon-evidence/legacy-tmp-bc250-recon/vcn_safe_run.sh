#!/usr/bin/env bash
# vcn_safe_run.sh — безопасный запуск VCN-включения BC-250 (WRITE-FIRST + мониторинг клина)
# Lesson (29.08): чтение VCN-MMIO(rd) по погашенному домену = завис шины. -> Включаем домен, ТОЛЬКО потом MMIO.
# Order: --verify(read-only) -> --no-fire(unlock+install+repoint) -> fire(msg0x61->domain6 clock) -> [--direct-load ring-test].
# Board: steammachine@127.0.0.1 ; sudo -n passwordless. Enable_vcn needs ROOT -> each step wrapped with `sudo -n`.
set -u
VB=/home/OWNER/vcn_unlock
SRC=/home/OWNER/vcn_unlock/bc250-smu-unlock
LOG="$VB/vcn_safe_run"; mkdir -p "$LOG"
HB="$LOG/heartbeat.log"; : > "$HB"
STATE="$LOG/run_state.txt"; : > "$STATE"
echo "$(date +%FT%T) START pid=$$ mode=$1" >> "$STATE"
# heartbeat: stamp liveness every 10s (if stamps STOP -> wedged)
( while [ -f "$LOG/.run" ]; do echo "$(date +%FT%T) beat" >> "$HB"; sleep 10; done ) &
HB_PID=$!
note(){ echo "[$(date +%FT%T)] $*" | tee -a "$LOG/main.log"; }
run_step(){ # step name ; args...
  local sname="$1"; shift
  note "== STEP: $sname =="
  local L="$LOG/$sname.log"; : > "$L"
  # launch enable_vcn.py as root (sudo preserves cwd); abs path (~ under root=/root)
  sudo -n bash -c "cd $VB && BC250_SMU_PATH=$SRC exec python3 enable_vcn.py "$@"" > "$L" 2>&1
  local rc=$?
  echo "$rc" > "$LOG/${sname}.rc"
  note "  $sname exit=$rc ($(wc -l < "$L") lines)"
  return $rc
}
# --direct-load optional arg
DL=""
[ "${1:-direct}" = "direct" ] && DL="--direct-load"
touch "$LOG/.run"
trap 'echo "[$(date +%FT%T)] INT" >> "$HB"; rm -f "$LOG/.run"; kill "$HB_PID" 2>/dev/null' INT TERM EXIT
set -e   # stop on first failure (enable_vcn exits nonzero on wedge/error)
run_step "verify"      --verify            # READ-ONLY first contact (SAFE)
run_step "unfire"      --no-fire           # unlock + install + repoint, disarm on exit
run_step "fire"                              # install + fire msg 0x61 -> enables domain6(VCN) clock
run_step "directload"  $DL                 # stage navi10_vcn in VRAM + ring-test (reads MMIO AFTER enable)
rm -f "$LOG/.run"; kill "$HB_PID" 2>/dev/null
note "ALL STEPS DONE. See logs in $LOG/ (verify.log,ofire.log,fire.log,directload.log,main.log,heartbeat.log)"
note "Success marker: directload.log shows mmUVD_SCRATCH9 CAFEDEAD->DEADBEEF (ring test passed)."
exit 0
