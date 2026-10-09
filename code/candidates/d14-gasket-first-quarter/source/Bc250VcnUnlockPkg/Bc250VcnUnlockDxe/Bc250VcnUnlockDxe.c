/** @file
  Bc250VcnUnlockDxe.c

  UEFI DXE Driver for Pre-OS Enablement of AMD BC-250 VCN (Cyan Skillfish).
  Executes early platform bring-up in the DXE phase before OS kernel boot.

  Copyright (C) 2026 Forge / Maxim
  SPDX-License-Identifier: MIT
**/

#include "Bc250VcnUnlockDxe.h"

#define D14_GASKET_WRITE_COUNT 14U

// 56 Gasket Bank 12 writes
STATIC CONST GASKET_WRITE_ENTRY mGasketBank12Writes[] = {
  { 0x0900C234U, 0x00000000U },
  { 0x0900C830U, 0x00FFFFFBU },
  { 0x0900C834U, 0x00FFFFFFU },
  { 0x0900C838U, 0x00FFFFFFU },
  { 0x0900C920U, 0x000003FFU },
  { 0x0900C92CU, 0x00000000U },
  { 0x0900C930U, 0x00000036U },
  { 0x0900C944U, 0x00000307U },
  { 0x0900C950U, 0x00000000U },
  { 0x0900C954U, 0x00000036U },
  { 0x0900C934U, 0x00021800U },
  { 0x0900C938U, 0x000218FFU },
  { 0x0900C968U, 0x00000307U },
  { 0x0900C974U, 0x00000000U },
  { 0x0900C978U, 0x00000036U },
  { 0x0900C958U, 0x00020300U },
  { 0x0900C95CU, 0x000206FFU },
  { 0x0900C98CU, 0x00000307U },
  { 0x0900C998U, 0x00000000U },
  { 0x0900C99CU, 0x00000036U },
  { 0x0900C97CU, 0x0001F844U },
  { 0x0900C980U, 0x0001F84FU },
  { 0x0900C9B0U, 0x00000307U },
  { 0x0900C9BCU, 0x00000000U },
  { 0x0900C9C0U, 0x00000036U },
  { 0x0900C9A0U, 0x00020180U },
  { 0x0900C9A4U, 0x00020183U },
  { 0x0900C9D4U, 0x00000307U },
  { 0x0900C9E0U, 0x00000000U },
  { 0x0900C9E4U, 0x00000036U },
  { 0x0900C9C4U, 0x00020108U },
  { 0x0900C9C8U, 0x00020117U },
  { 0x0900C9F8U, 0x00000307U },
  { 0x0900CA04U, 0x00000000U },
  { 0x0900CA08U, 0x00000036U },
  { 0x0900C9E8U, 0x00021078U },
  { 0x0900C9ECU, 0x0002107FU },
  { 0x0900CA1CU, 0x00000307U },
  { 0x0900CA28U, 0x00000000U },
  { 0x0900CA2CU, 0x00000036U },
  { 0x0900CA0CU, 0x00020EB0U },
  { 0x0900CA10U, 0x00020EB7U },
  { 0x0900CA40U, 0x00000307U },
  { 0x0900CA4CU, 0x00000000U },
  { 0x0900CA50U, 0x00000036U },
  { 0x0900CA30U, 0x0001F860U },
  { 0x0900CA34U, 0x0001F863U },
  { 0x0900CB80U, 0x000000FFU },
  { 0x0900C910U, 0x00497FFFU },
  { 0x0900C914U, 0x00007FFFU },
  { 0x0900C234U, 0x00000001U },
  { 0x0900C234U, 0x00000000U },
  { 0x0900C914U, 0x00000000U },
  { 0x0900C930U, 0x00000000U },
  { 0x0900CB80U, 0x00000000U },
  { 0x0900C234U, 0x00000001U }
};

// === S1..S6 Data-Fabric firewall writes (robin->cezanne SEC_GASKET delta) ===
// These are FIREWALL registers: must go via SmuWriteSmn32 (SMU privileged write), NOT x86 SmnWrite32.
STATIC CONST GASKET_WRITE_ENTRY mGasketDataFabricWrites[] = {
  { 0x03A2011CU, 0x0000107FU },  // S1 firewall LOW bound widen (was 0x87FF match-all)
  { 0x03A20124U, 0x000010FFU },  // S2 firewall HIGH bound
  { 0x03A20128U, 0xFFFF0000U },  // S4 secondary high window (Cezanne-only)
  { 0x03D2011CU, 0x0000107FU },  // parallel firewall bank copy
  { 0x03D20120U, 0xFFFF0000U },
  { 0x03D20124U, 0x000010FFU },
  { 0x0001C780U, 0x0002DF4DU },  // VCN_FABRIC routing-firewall (Cezanne value-then-0 pair)
  { 0x0001C780U, 0x00000000U },
  { 0x0001C784U, 0xFF100000U },
  { 0x0001C784U, 0x00000000U },
  { 0x0001C760U, 0x01E0A414U },
  { 0x0001C764U, 0x05F16E2CU },
  { 0x0001C768U, 0x01C11823U },
  { 0x0001C76CU, 0x05E514A0U },
  { 0x0003E810U, 0x00000006U },  // bind VCN_SEG0/1 MMIO to fabric router
  { 0x0003E814U, 0x2544C382U },  // VCN_SEG binding upper
};


STATIC
UINT32
SmnRead32 (
  IN UINT32 Address
  )
{
  PciSegmentWrite32 (BC250_PCI_SEGMENT_ADDRESS (SMN_INDEX_OFFSET), Address);
  return PciSegmentRead32 (BC250_PCI_SEGMENT_ADDRESS (SMN_DATA_OFFSET));
}

STATIC
VOID
SmnWrite32 (
  IN UINT32 Address,
  IN UINT32 Value
  )
{
  PciSegmentWrite32 (BC250_PCI_SEGMENT_ADDRESS (SMN_INDEX_OFFSET), Address);
  PciSegmentWrite32 (BC250_PCI_SEGMENT_ADDRESS (SMN_DATA_OFFSET), Value);
}

STATIC
EFI_STATUS
SmuMailboxSend (
  IN  UINT32 CmdReg,
  IN  UINT32 RspReg,
  IN  UINT32 ArgReg,
  IN  UINT32 MsgId,
  IN  CONST UINT32 *Args OPTIONAL,
  IN  UINTN NumArgs,
  OUT UINT32 *OutStatus OPTIONAL,
  OUT UINT32 *OutRet OPTIONAL
  )
{
  UINTN  Index;
  UINT32 Status;
  UINTN  Iters;

  SmnWrite32 (RspReg, 0);

  for (Index = 0; Index < SMU_MAILBOX_ARGS; Index++) {
    if (Index < NumArgs && Args != NULL) {
      SmnWrite32 (ArgReg + (UINT32)(Index * 4), Args[Index]);
    } else {
      SmnWrite32 (ArgReg + (UINT32)(Index * 4), 0);
    }
  }

  SmnWrite32 (CmdReg, MsgId);

  for (Iters = 0; Iters < SMU_MAILBOX_TIMEOUT_ITERS; Iters++) {
    Status = SmnRead32 (RspReg);
    if (Status != 0) {
      if (OutStatus != NULL) {
        *OutStatus = Status;
      }
      if (OutRet != NULL) {
        *OutRet = SmnRead32 (ArgReg);
      }
      return (Status == SMU_RETURN_OK) ? EFI_SUCCESS : EFI_ACCESS_DENIED;
    }
    gBS->Stall (SMU_MAILBOX_POLL_DELAY_US);
  }

  return EFI_TIMEOUT;
}

STATIC
EFI_STATUS
SmuWriteSram32 (
  IN UINT32 Addr,
  IN UINT32 Value
  )
{
  EFI_STATUS Status;
  UINT32     Arg;

  Arg = Addr;
  Status = SmuMailboxSend (Q3_CMD, Q3_RSP, Q3_ARG, 0x28, &Arg, 1, NULL, NULL);
  if (EFI_ERROR (Status)) {
    return Status;
  }

  Arg = Value;
  return SmuMailboxSend (Q3_CMD, Q3_RSP, Q3_ARG, 0x29, &Arg, 1, NULL, NULL);
}

STATIC
EFI_STATUS
SmuWriteSmn32 (
  IN UINT32 Addr,
  IN UINT32 Value
  )
{
  EFI_STATUS Status;
  UINT32     Arg;

  Arg = Addr;
  Status = SmuMailboxSend (Q3_CMD, Q3_RSP, Q3_ARG, 0x2B, &Arg, 1, NULL, NULL);
  if (EFI_ERROR (Status)) {
    return Status;
  }

  Arg = Value;
  return SmuMailboxSend (Q3_CMD, Q3_RSP, Q3_ARG, 0x2C, &Arg, 1, NULL, NULL);
}

STATIC
EFI_STATUS
SmuReadSmn32 (
  IN  UINT32 Addr,
  OUT UINT32 *Value
  )
{
  UINT32 Arg;
  Arg = Addr;
  return SmuMailboxSend (Q3_CMD, Q3_RSP, Q3_ARG, 0x2A, &Arg, 1, NULL, Value);
}

STATIC
EFI_STATUS
PerformSmuUnlockDxe (
  VOID
  )
{
  EFI_STATUS           Status;
  EFI_PHYSICAL_ADDRESS DmaPhys;
  VOID                 *VirtAddr;
  UINT32               *Table;
  UINT32               ProbeVal;
  UINT32               Idx;
  UINT32               P;
  UINT32               N;
  UINT32               Args[6];

  Status = SmuReadSmn32 (0x0005A870U, &ProbeVal);
  if (!EFI_ERROR (Status)) {
    return EFI_SUCCESS;
  }

  DmaPhys = 0xFFFFFFFFULL;
  Status = gBS->AllocatePages (AllocateMaxAddress, EfiBootServicesData, 1, &DmaPhys);
  if (EFI_ERROR (Status)) {
    return Status;
  }

  VirtAddr = (VOID *)(UINTN)DmaPhys;
  Table = (UINT32 *)VirtAddr;
  ZeroMem (Table, 4096);

  P = 0x0000797CU;
  N = (0x7B20U - P) / 4U;

  Table[0] = 1;
  Table[6] = (UINT32)(0x13U | (N << 16));

  // Stage 1
  {
    UINT32 PtrSlot = (0x00019780U - 0x00018850U) / 16U;
    UINT32 Count = 30U;
    UINT32 RingArgs[4];

    RingArgs[0] = 0; RingArgs[1] = 0; RingArgs[2] = 0; RingArgs[3] = (((UINT32)1 << 24) | 4U);
    for (Idx = 0; Idx < Count; Idx++) {
      SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x23, RingArgs, 4, NULL, NULL);
    }
    RingArgs[0] = PtrSlot; RingArgs[1] = 0; RingArgs[2] = 0; RingArgs[3] = (((UINT32)1 << 24) | 4U);
    SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x23, RingArgs, 4, NULL, NULL);

    RingArgs[0] = 0; RingArgs[1] = 0; RingArgs[2] = P - 0x1CU; RingArgs[3] = (((UINT32)1 << 24) | 1U);
    SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x23, RingArgs, 4, NULL, NULL);
  }

  Args[0] = 0x23U;
  Args[1] = (UINT32)(DmaPhys >> 32);
  Args[2] = (UINT32)(DmaPhys & 0xFFFFFFFF);
  Args[3] = 8U;
  Args[4] = 0U;
  Args[5] = 3U;
  SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x0A, Args, 6, NULL, NULL);

  // Stage 2
  Table[0] = 0;
  {
    UINT32 PtrSlot = (0x00019780U - 0x00018850U) / 16U;
    UINT32 Count = 28U;
    UINT32 RingArgs[4];

    RingArgs[0] = 0; RingArgs[1] = 0; RingArgs[2] = 0; RingArgs[3] = (((UINT32)1 << 24) | 4U);
    for (Idx = 0; Idx < Count; Idx++) {
      SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x23, RingArgs, 4, NULL, NULL);
    }
    RingArgs[0] = PtrSlot; RingArgs[1] = 0; RingArgs[2] = 0; RingArgs[3] = (((UINT32)1 << 24) | 4U);
    SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x23, RingArgs, 4, NULL, NULL);

    RingArgs[0] = 0; RingArgs[1] = 0; RingArgs[2] = P; RingArgs[3] = (((UINT32)1 << 24) | 1U);
    SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x23, RingArgs, 4, NULL, NULL);
  }

  Args[0] = 0x23U;
  Args[1] = (UINT32)(DmaPhys >> 32);
  Args[2] = (UINT32)(DmaPhys & 0xFFFFFFFF);
  Args[3] = 1U;
  Args[4] = 0U;
  Args[5] = 0x37U;
  SmuMailboxSend (Q2_CMD, Q2_RSP, Q2_ARG, 0x0A, Args, 6, NULL, NULL);

  gBS->FreePages (DmaPhys, 1);

  // Fixup
  for (Idx = 0; Idx < (0x4CU / 4U); Idx++) {
    SmuWriteSram32 (0x7950U + Idx * 4U, 0);
  }
  for (Idx = 0; Idx < (0x1F0U / 4U); Idx++) {
    SmuWriteSram32 (0x18DF0U + Idx * 4U, 0);
  }
  SmuWriteSram32 (0x7B38U, 0);
  SmuWriteSram32 (0x19780U, 0x3F794U);
  SmuWriteSram32 (0x19784U, 0x3E000U);
  SmuWriteSram32 (0x19788U, 0);
  SmuWriteSram32 (0x1978CU, 0);
  SmuWriteSram32 (0x17E1CU, 0x8B08U);

  // Do not publish the laboratory protocol unless secure SMN access was
  // actually read back after the exploit and fixup.
  return SmuReadSmn32 (PROBE_ADDR, &ProbeVal);
}

STATIC
EFI_STATUS
EnableVcnHardwareUnified (
  VOID
  )
{
  STATIC CONST UINT8 ThunkVcnBringup[28] = {
    0x36, 0x41, 0x00, 0x1C, 0x6A, 0xE5, 0x83, 0xE3,
    0x1C, 0x7A, 0xA5, 0x83, 0xE3, 0x1C, 0x8A, 0x65,
    0x83, 0xE3, 0x0C, 0x6A, 0x0C, 0x1B, 0xA5, 0xC0,
    0xE3, 0x1D, 0xF0, 0x00
  };
  UINTN  Idx;
  UINT32 Word;

  for (Idx = 0; Idx < sizeof (ThunkVcnBringup); Idx += 4) {
    CopyMem (&Word, &ThunkVcnBringup[Idx], 4);
    SmuWriteSram32 (THUNK_SRAM_ADDR + (UINT32)Idx, Word);
  }

  SmuWriteSram32 (Q3_HANDLER_SLOT_61, THUNK_SRAM_ADDR);

  SmnWrite32 (Q3_RSP, 0);
  SmnWrite32 (Q3_CMD, 0x61);
  gBS->Stall (100000);

  SmuWriteSram32 (Q3_HANDLER_SLOT_61, 0);

  DEBUG ((DEBUG_INFO, "Bc250VcnUnlockDxe: Unified VCN Clocks and Power activated\n"));
  return EFI_SUCCESS;
}

STATIC
EFI_STATUS
ConfigureVcnGasketApertures (
  VOID
  )
{
  UINTN      Index;
  EFI_STATUS Status;

  STATIC_ASSERT (D14_GASKET_WRITE_COUNT < ARRAY_SIZE (mGasketBank12Writes), "D14 must be a strict prefix");

  for (Index = 0; Index < D14_GASKET_WRITE_COUNT; Index++) {
    Status = SmuWriteSmn32 (
               mGasketBank12Writes[Index].Address,
               mGasketBank12Writes[Index].Value
               );
    if (EFI_ERROR (Status)) {
      return Status;
    }
  }

  DEBUG ((DEBUG_INFO, "Bc250VcnUnlockDxe: Bank 12 Gasket apertures configured (%d writes)\n",
          D14_GASKET_WRITE_COUNT));
  return EFI_SUCCESS;
}


STATIC
EFI_STATUS
ConfigureVcnDataFabric (VOID)
{
  UINTN i;
  for (i = 0; i < ARRAY_SIZE (mGasketDataFabricWrites); i++) {
    EFI_STATUS s = SmuWriteSmn32 (mGasketDataFabricWrites[i].Address, mGasketDataFabricWrites[i].Value);
    DEBUG ((DEBUG_INFO, "DFabric write %08x<-%08x %r\n", mGasketDataFabricWrites[i].Address, mGasketDataFabricWrites[i].Value, s));
  }
  return EFI_SUCCESS;
}

STATIC EFI_EVENT mReadyToBootEvent;
STATIC volatile BOOLEAN mEnableDeferredActions = FALSE;

STATIC
VOID
EFIAPI
Bc250GasketReadyToBoot (
  IN EFI_EVENT Event,
  IN VOID      *Context
  )
{
  EFI_STATUS Status;

  (VOID)Context;
  gBS->CloseEvent (Event);
  mReadyToBootEvent = NULL;
  Status = ConfigureVcnGasketApertures ();
  DEBUG ((DEBUG_INFO, "Bc250SmuUnlockDxe: ReadyToBoot gasket=%r\n", Status));
}

EFI_STATUS
EFIAPI
Bc250VcnUnlockDxeEntryPoint (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  EFI_STATUS Status;

  (VOID)SystemTable;

  DEBUG ((DEBUG_INFO, "=== Bc250SmuUnlockDxe: early DXE unlock starting ===\n"));
  Status = PerformSmuUnlockDxe ();
  if (EFI_ERROR (Status)) {
    DEBUG ((DEBUG_ERROR, "Bc250SmuUnlockDxe: early unlock failed: %r\n", Status));
    return Status;
  }

  if (mEnableDeferredActions) {
    EnableVcnHardwareUnified ();
    ConfigureVcnDataFabric ();
  }

  Status = gBS->CreateEventEx (
                  EVT_NOTIFY_SIGNAL,
                  TPL_CALLBACK,
                  Bc250GasketReadyToBoot,
                  NULL,
                  &gEfiEventReadyToBootGuid,
                  &mReadyToBootEvent
                  );
  if (EFI_ERROR (Status)) {
    return Status;
  }

  Status = gBS->InstallProtocolInterface (
                  &ImageHandle,
                  &gBc250VcnUnlockProtocolGuid,
                  EFI_NATIVE_INTERFACE,
                  NULL
                  );
  DEBUG ((DEBUG_INFO, "=== Bc250SmuUnlockDxe: early unlock complete, protocol=%r ===\n", Status));
  return Status;
}
