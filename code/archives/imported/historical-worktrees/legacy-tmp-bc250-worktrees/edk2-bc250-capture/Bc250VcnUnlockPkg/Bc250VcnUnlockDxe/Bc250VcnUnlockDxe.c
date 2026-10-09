/** @file
  Bc250UartDebugDxe — stock P3.00 + FCH UART0 init + SMU unlock + debug print.
  No VCN actions (mEnableVcnActions = FALSE). Purpose: enable UART for diagnostics.
**/

#include "Bc250VcnUnlockDxe.h"

/* ---- FCH UART0 hardware init ---- */

#define FCH_UART0_BASE      0xFEDC9000ULL
#define FCH_AOAC_BASE       0xFED81E00ULL
#define FCH_IOMUX_BASE      0xFED80D00ULL
#define UART0_AOAC_DEV      11U
#define GPIO_UART0_TX       138U
#define GPIO_UART0_RX       136U
#define UART_THR  0x00U
#define UART_DLL  0x00U
#define UART_DLM  0x04U
#define UART_IER  0x04U
#define UART_FCR  0x08U
#define UART_LCR  0x0CU
#define UART_MCR  0x10U
#define UART_LSR  0x14U
#define UART_LSR_THRE  0x20U

STATIC VOID
InitFchUart0 (VOID)
{
  /* AOAC: enable UART0 (device 11) */
  MmioWrite8 ((UINTN)(FCH_AOAC_BASE + UART0_AOAC_DEV * 2), 0x0B);
  gBS->Stall (1000);
  /* IOMUX: GPIO 138=TX func0, GPIO 136=RX func0 */
  MmioWrite8 ((UINTN)(FCH_IOMUX_BASE + GPIO_UART0_TX), 0x00);
  MmioWrite8 ((UINTN)(FCH_IOMUX_BASE + GPIO_UART0_RX), 0x00);
  gBS->Stall (100);
  /* 16550: 115200 8N1 */
  MmioWrite8 ((UINTN)(FCH_UART0_BASE + UART_IER), 0x00);
  MmioWrite8 ((UINTN)(FCH_UART0_BASE + UART_LCR), 0x83);
  MmioWrite8 ((UINTN)(FCH_UART0_BASE + UART_DLL), 0x1A);  /* 48MHz/16/115200=26 */
  MmioWrite8 ((UINTN)(FCH_UART0_BASE + UART_DLM), 0x00);
  MmioWrite8 ((UINTN)(FCH_UART0_BASE + UART_LCR), 0x03);
  MmioWrite8 ((UINTN)(FCH_UART0_BASE + UART_FCR), 0x07);
  MmioWrite8 ((UINTN)(FCH_UART0_BASE + UART_MCR), 0x03);
}

STATIC VOID
UartPutChar (CHAR8 Ch)
{
  UINTN T = 100000;
  while (!(MmioRead8 ((UINTN)(FCH_UART0_BASE + UART_LSR)) & UART_LSR_THRE) && T--);
  MmioWrite8 ((UINTN)(FCH_UART0_BASE + UART_THR), (UINT8)Ch);
}

STATIC VOID
UartPrint (CONST CHAR8 *S)
{
  while (*S) {
    if (*S == '\n') UartPutChar ('\r');
    UartPutChar (*S++);
  }
}

STATIC VOID
UartHex32 (UINT32 V)
{
  STATIC CONST CHAR8 H[] = "0123456789ABCDEF";
  UartPrint ("0x");
  for (INTN i = 7; i >= 0; i--) {
    UartPutChar (H[(V >> (i * 4)) & 0xF]);
  }
}

/* ---- SMN access (same as v002) ---- */

STATIC VOID
SmnWrite32 (IN UINT32 Address, IN UINT32 Value)
{
  PciSegmentWrite32 (BC250_PCI_SEGMENT_ADDRESS (SMN_INDEX_OFFSET), Address);
  PciSegmentWrite32 (BC250_PCI_SEGMENT_ADDRESS (SMN_DATA_OFFSET), Value);
}

STATIC UINT32
SmnRead32 (IN UINT32 Address)
{
  PciSegmentWrite32 (BC250_PCI_SEGMENT_ADDRESS (SMN_INDEX_OFFSET), Address);
  return PciSegmentRead32 (BC250_PCI_SEGMENT_ADDRESS (SMN_DATA_OFFSET));
}

STATIC EFI_STATUS
SmuMailboxSend (
  IN  UINT32 CmdReg, IN  UINT32 RspReg, IN  UINT32 ArgReg,
  IN  UINT32 MsgId,  IN  CONST UINT32 *Args OPTIONAL,
  IN  UINTN  ArgCount, OUT UINT32 *Response OPTIONAL,
  OUT UINT32 *ArgOut OPTIONAL
  )
{
  UINT32 Rsp;
  UINTN  Poll;
  SmnWrite32 (RspReg, 0);
  if (Args) {
    for (UINTN i = 0; i < ArgCount && i < SMU_MAILBOX_ARGS; i++)
      SmnWrite32 (ArgReg + (UINT32)(i * sizeof (UINT32)), Args[i]);
  }
  SmnWrite32 (CmdReg, MsgId);
  for (Poll = 0; Poll < SMU_MAILBOX_TIMEOUT_ITERS; Poll++) {
    gBS->Stall (SMU_MAILBOX_POLL_DELAY_US);
    Rsp = SmnRead32 (RspReg);
    if (Rsp != 0) break;
  }
  if (Response) *Response = Rsp;
  if (ArgOut)   *ArgOut = SmnRead32 (ArgReg);
  return (Rsp == SMU_RETURN_OK) ? EFI_SUCCESS : EFI_DEVICE_ERROR;
}

STATIC VOID
SmuWriteSram32 (IN UINT32 Addr, IN UINT32 Value)
{
  UINT32 Args[2] = { Addr, Value };
  SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x0A, Args, 2, NULL, NULL);
}

/* ---- SMU unlock (proven in D10) ---- */

STATIC EFI_STATUS
PerformSmuUnlockDxe (VOID)
{
  UINT32 ProbeVal = 0;
  UINT32 Arg, Rsp;
  UINTN  i;

  UartPrint ("[SMU] Checking probe...\n");
  Arg = PROBE_ADDR;
  if (EFI_ERROR (SmuMailboxSend (Q3_CMD, Q3_RSP, Q3_ARG, 0x2A, &Arg, 1, &Rsp, &ProbeVal))) {
    UartPrint ("[SMU] Probe read failed\n");
  }
  UartPrint ("[SMU] Probe="); UartHex32 (ProbeVal); UartPrint ("\n");

  if (ProbeVal == 0xFF) {
    UartPrint ("[SMU] Already unlocked\n");
    return EFI_SUCCESS;
  }

  UartPrint ("[SMU] Unlocking (Q2 0x23 x30)...\n");
  for (i = 0; i < 30; i++) {
    Arg = 0;
    SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x23, &Arg, 1, NULL, NULL);
  }
  Arg = FAKE_ENTRY_KEY;
  SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x0A, &Arg, 1, NULL, NULL);

  UartPrint ("[SMU] Phase 2 (Q2 0x23 x29)...\n");
  for (i = 0; i < 29; i++) {
    Arg = 0;
    SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x23, &Arg, 1, NULL, NULL);
  }
  SmuWriteSram32 (DBG_DISABLE, 0);
  Arg = NEW_ENTRY_KEY;
  SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x0A, &Arg, 1, NULL, NULL);

  /* Verify */
  Arg = PROBE_ADDR;
  SmuMailboxSend (Q3_CMD, Q3_RSP, Q3_ARG, 0x2A, &Arg, 1, &Rsp, &ProbeVal);
  UartPrint ("[SMU] Post-unlock probe="); UartHex32 (ProbeVal); UartPrint ("\n");

  if (ProbeVal != 0xFF) {
    UartPrint ("[SMU] UNLOCK FAILED\n");
    return EFI_DEVICE_ERROR;
  }
  UartPrint ("[SMU] Unlock OK\n");
  return EFI_SUCCESS;
}

/* ---- Entry point ---- */

STATIC volatile BOOLEAN mEnableVcnActions = FALSE;

EFI_STATUS
EFIAPI
Bc250VcnUnlockDxeEntryPoint (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  EFI_STATUS Status;
  (VOID)SystemTable;

  /* FIRST: init UART so we can see what happens */
  InitFchUart0 ();
  UartPrint ("\n\n=== BC250 UART Debug DXE v001 ===\n");
  UartPrint ("[BOOT] DXE entry point reached\n");

  /* SMU unlock */
  Status = PerformSmuUnlockDxe ();
  if (EFI_ERROR (Status)) {
    UartPrint ("[BOOT] SMU unlock failed, continuing\n");
  }

  /* Read some diagnostic registers */
  UartPrint ("[DIAG] SMN 0x5A870 = "); UartHex32 (SmnRead32 (0x0005A870U)); UartPrint ("\n");

  if (mEnableVcnActions) {
    UartPrint ("[VCN] Actions enabled (not in this build)\n");
  } else {
    UartPrint ("[VCN] Actions DISABLED (diagnostic only)\n");
  }

  Status = gBS->InstallProtocolInterface (
                  &ImageHandle,
                  &gBc250VcnUnlockProtocolGuid,
                  EFI_NATIVE_INTERFACE,
                  NULL
                  );
  UartPrint ("[BOOT] Protocol installed, status=");
  UartHex32 ((UINT32)(UINTN)Status);
  UartPrint ("\n=== BC250 DXE complete ===\n\n");
  return Status;
}
