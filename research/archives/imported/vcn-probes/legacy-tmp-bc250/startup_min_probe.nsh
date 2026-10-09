@echo -off
map -r

for %d in fs0 fs1 fs2 fs3 fs4 fs5 fs6 fs7 fs8 fs9
  if exist %d:\BC250_SCAN_MEDIA then
    %d:
    cd \
    echo === VCN probe write-only, then chainload Limine, no reset ===
    EFI\BOOT\BC250\Bc250VcnProbeApp.efi
    echo probe returned without chainload
    exit
  endif
endfor
echo BC250 probe media not found
