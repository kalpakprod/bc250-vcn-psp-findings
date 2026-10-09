#!/usr/bin/env bash
# vcn_watch.sh — наблюдатель за запуском vcn_safe_run.sh: heartbeat + wedge alert.
# Usage: run `~/vcn_unlock/vcn_safe_run.sh` (bg or fg), then separately: ~/vcn_unlock/vcn_watch.sh
VB=/home/OWNER/vcn_unlock
LOG="$VB/vcn_safe_run"
HIST=90   # seconds without heartbeat advance => wedged
while :; do
  [ -f "$LOG/.run" ] || { echo "$(date +%FT%T) run ended"; break; }
  now=$(date +%s); last=$(tail -1 "$LOG/heartbeat.log" 2>/dev/null | sed -E 's/.*([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}).*//' | xargs -I{} date -d {} +%s 2>/dev/null)
  last=${last:-$now}
  gap=$((now-last))
  printf "%s  beat_gap=%ss  run=%s\n" "$(date +%FT%T)" "$gap" "$([ -f "$LOG/.run" ] && echo yes || echo no)" | tail -1 | tee -a "$LOG/watch.log"
  [ "$gap" -gt "$HIST" ] && { echo ">>> WEDGE ALERT: no heartbeat ${gap}s -> process wedged. Tail main.log; if wedged, cold power-cycle." ; }
  sleep 15
done
echo "$(date +%FT%T) watcher exiting" | tee -a "$LOG/watch.log"
