fs0:
echo === ENTER_VCN_DRIVER_TEST ===
load Bc250VcnUnlockDxe.efi
echo DRIVER_LASTERROR=%lasterror%
echo === AFTER_DRIVER ===
reset -s
