#!/usr/bin/env bash
set +e
OUT=/tmp/a1_part2.out
{
echo "=== PART2 ts=$(date -Is) ==="
CARD=/sys/class/drm/card1/device
echo "card device=$(cat $CARD/device) rev=$(cat $CARD/revision)"
for f in mem_info_vram_total mem_info_vram_used mem_info_gtt_total mem_info_vis_vram_total current_link_speed current_link_width; do
  if [ -e "$CARD/$f" ]; then echo -n "$f="; timeout 2 cat "$CARD/$f" 2>/dev/null; echo; else echo "missing $f"; fi
done
for f in pp_dpm_sclk pp_dpm_mclk pp_dpm_fclk pp_dpm_socclk pp_dpm_vclk pp_dpm_dclk pp_features; do
  if [ -e "$CARD/$f" ]; then
    echo "--- $f ---"
    timeout 2 cat "$CARD/$f" 2>/dev/null | head -30 || echo "TIMEOUT/ERR $f"
  else
    echo "missing $f"
  fi
done
for f in firmware_info ip_blocks ip_discovery gpu_metrics; do
  p="$CARD/$f"
  if [ -e "$p" ]; then
    echo "--- $f size ---"; timeout 2 wc -c <"$p" 2>/dev/null
    timeout 2 od -An -tx1 -N 64 "$p" 2>/dev/null | head -5
  else
    echo "missing $f"
  fi
done
echo "--- hwmon ---"
for h in $CARD/hwmon/hwmon*; do
  [ -d "$h" ] || continue
  echo "HWMON=$h name=$(timeout 1 cat $h/name 2>/dev/null)"
  for x in $h/temp*_input $h/freq*_input $h/power1_average $h/power1_cap $h/fan*_input; do
    [ -e "$x" ] || continue
    echo "$(basename $x)=$(timeout 1 cat $x 2>/dev/null)"
  done
done
echo "=== PART2 DONE ==="
} >"$OUT" 2>&1
echo wrote:$OUT
wc -c "$OUT"
