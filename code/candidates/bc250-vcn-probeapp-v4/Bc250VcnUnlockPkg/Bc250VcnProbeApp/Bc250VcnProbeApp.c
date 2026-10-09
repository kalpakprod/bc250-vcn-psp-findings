/** @file
  Bc250VcnProbeApp.c  --  v4 (2026-09-12)

  UEFI Shell Application for AMD BC-250 (Cyan Skillfish, 1002:13fe) VCN bring-up.

  v4 = v3 (2026-08-26) + the hardware-verified 2026-09-12 runtime runbook:
    1. Q2 0x23 transfer-table unlock (unchanged, field-proven).
    2. SMU internal state repair (unchanged).
    3. dom6 gate release via privileged SMN write 0x06D0F8 <- 0
       (2026-09-12: LANDED and HELD; boot value 0x02 = gate hold).
    4. Unified clock+power thunk (slots 0x16/0x17/0x18 via FUN_00023744,
       dom6 power via FUN_00023B14) fired through Q3 msg 0x61 (unchanged).
    5. Bank-12 gasket: 56-pair program -> masks -> requester policy ->
       8 aperture grants -> lock -> commit -> unlock tail (unchanged values).
    6. FULL donor dataplane routes (2026-09-12 stage5 list, never
       runtime-written before): NBIF 0x1C7xx, NBIO 0x1F820/0x1F8A4,
       IOHC windows 0x322, DF mirror 0x3D2, VCN_SEG binding 0x3E814.
       v3's partial/older DF values are preserved in comments for provenance.
    7. BAR5 MMIO arbiter read (UVD_VERSION 0x20f24, UVD_POWER_STATUS 0x1f810,
       UVD_NO_OP 0x20efc): baseline right after unlock, verdict after the
       gasket+routes. 2026-08-25 measurement: BAR5 VCN-segment reads post-clock
       work return all-ones + NO hang; single reads are the safe arbiter class.
    8. Same-session chainload of the NVMe bootloader (zero reboot: the VCN
       state persists into Linux).

  Write-first discipline (2026-09-12 wedge taxonomy): NO DF-space SMN reads,
  NO Q3 0x2A reads, no full-dump class transports. The BAR5 reads are a
  different transport (GPU MMIO, not SMN DF space).

  Copyright (C) 2026 Forge / Maxim
  SPDX-License-Identifier: MIT
**/

#include <Uefi.h>
#include <Guid/FileInfo.h>
#include <Protocol/LoadedImage.h>
#include <Protocol/SimpleFileSystem.h>
#include <Library/DevicePathLib.h>
#include <Library/BaseLib.h>
#include <Library/BaseMemoryLib.h>
#include <Library/IoLib.h>
#include <Library/MemoryAllocationLib.h>
#include <Library/PciSegmentLib.h>
#include <Library/PrintLib.h>
#include <Library/UefiApplicationEntryPoint.h>
#include <Library/UefiBootServicesTableLib.h>
#include <Library/UefiLib.h>

#include "../Bc250VcnUnlockDxe/Bc250VcnUnlockDxe.h"

#ifndef BC250_GPU_PCI_ADDRESS
#define BC250_GPU_PCI_ADDRESS(Offset) \
  PCI_SEGMENT_LIB_ADDRESS (0, 1, 0, 0, (Offset))
#endif

#ifndef RING_BASE
#define RING_BASE                   0x00018850U
#endif
#ifndef RING_ENTRY_SZ
#define RING_ENTRY_SZ               16U
#endif
#define RING_SUBQ_SLOTS             30U
#ifndef TR_TABLE_PTR
#define TR_TABLE_PTR                0x00019784U
#endif
#ifndef TR_TABLE_FAKE_RING_ENTRY
#define TR_TABLE_FAKE_RING_ENTRY    (TR_TABLE_PTR - 4U)
#endif
#ifndef FAKE_ENTRY_KEY
#define FAKE_ENTRY_KEY              0x13U
#endif
#ifndef NEW_ENTRY_KEY
#define NEW_ENTRY_KEY               0x37U
#endif
#ifndef DBG_DISABLE
#define DBG_DISABLE                 0x00007B3CU
#endif
#define NEW_ENTRY_ADDR              (DBG_DISABLE - 4U)
#ifndef PROBE_ADDR
#define PROBE_ADDR                  0x0005A870U
#endif

/* dom6 gate control (2026-09-12 manual-powerup target) */
#define DOM6_CTRL                   0x0006D0F8U

/* BAR5 VCN arbiter offsets (GPU MMIO space, NOT SMN) */
#define VCN_MMIO_UVD_VERSION        0x00020F24U
#define VCN_MMIO_UVD_POWER_STATUS   0x0001F810U
#define VCN_MMIO_UVD_NO_OP          0x00020EFCU

#ifndef RING_CMD_TYPE
#define RING_CMD_TYPE(Cmd, Subq)    (((UINT32)(Cmd) << 24) | ((UINT32)(Subq) & 0xFFU))
#endif

STATIC UINT32 mSubq4CurIdx = 0;

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

/* v3 legacy DF values kept for provenance (superseded by the donor b2a
 * capture in the chain report -- see mDonorRouteWrites below):
 *   0x0001C780 <- 0x0002DF4D / 0x00000000
 *   0x0001C784 <- 0xFF100000 / 0x00000000
 *   0x0001C760 <- 0x01E0A414   0x0001C764 <- 0x05F16E2C
 *   0x0001C768 <- 0x01C11823   0x0001C76C <- 0x05E514A0
 *   0x0003E810 <- 0x00000006   0x0003E814 <- 0x2544C382
 */
STATIC CONST GASKET_WRITE_ENTRY mDonorRouteWrites[] = {
  /* NBIF routes (donor b2a, smn_lock_probe SURVEY + chain report) */
  { 0x0001C760U, 0xFF400000U },
  { 0x0001C764U, 0xFF400000U },
  { 0x0001C780U, 0x00000000U },
  { 0x0001C784U, 0x00000000U },
  { 0x0001C788U, 0x000000FFU },
  { 0x0001C78CU, 0x00000107U },
  /* NBIO VCN route (0x1F8A4 written twice per donor) */
  { 0x0001F820U, 0x00185103U },
  { 0x0001F8A4U, 0x0000000BU },
  { 0x0001F8A4U, 0x00000000U },
  /* IOHC 0x322 windows (b2b) */
  { 0x0322011CU, 0x00010000U },
  { 0x03220124U, 0x00010707U },
  { 0x0322012CU, 0x000101FFU },
  /* DF mirror 0x3D2 (b2a) */
  { 0x03D2011CU, 0x000107FFU },
  { 0x03D20124U, 0x00010FFFU },
  /* VCN_SEG binding (donor) */
  { 0x0003E810U, 0x00000006U },
  { 0x0003E814U, 0x2544C382U },
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
SmuMailboxSendGeneric (
  IN  UINT32        CmdReg,
  IN  UINT32        RspReg,
  IN  UINT32        ArgReg,
  IN  UINT32        MsgId,
  IN  CONST UINT32  *Args OPTIONAL,
  IN  UINTN         NumArgs,
  OUT UINT32        *OutStatus OPTIONAL,
  OUT UINT32        *OutRet OPTIONAL
  )
{
  UINTN  Index;
  UINTN  Iteration;
  UINT32 Status;

  SmnWrite32 (RspReg, 0);
  for (Index = 0; Index < SMU_MAILBOX_ARGS; Index++) {
    SmnWrite32 (
      ArgReg + (UINT32)(Index * sizeof (UINT32)),
      (Args != NULL && Index < NumArgs) ? Args[Index] : 0
      );
  }
  SmnWrite32 (CmdReg, MsgId);

  for (Iteration = 0; Iteration < SMU_MAILBOX_TIMEOUT_ITERS; Iteration++) {
    Status = SmnRead32 (RspReg);
    if (Status == SMU_RETURN_OK || Status == SMU_RETURN_REJECTED_BUSY ||
        Status == SMU_RETURN_REJECTED_PREREQ || Status == SMU_RETURN_BAD_COMMAND ||
        Status == SMU_RETURN_FAILED) {
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

  if (OutStatus != NULL) {
    *OutStatus = 0;
  }
  return EFI_TIMEOUT;
}

STATIC
EFI_STATUS
SmuQ2Send (
  IN  UINT32        MsgId,
  IN  CONST UINT32  *Args OPTIONAL,
  IN  UINTN         NumArgs,
  OUT UINT32        *OutStatus OPTIONAL,
  OUT UINT32        *OutRet OPTIONAL
  )
{
  return SmuMailboxSendGeneric (Q2_CMD, Q2_RSP, Q2_ARG, MsgId, Args, NumArgs, OutStatus, OutRet);
}

STATIC
EFI_STATUS
SmuQ3Send (
  IN  UINT32        MsgId,
  IN  CONST UINT32  *Args OPTIONAL,
  IN  UINTN         NumArgs,
  OUT UINT32        *OutStatus OPTIONAL,
  OUT UINT32        *OutRet OPTIONAL
  )
{
  return SmuMailboxSendGeneric (Q3_CMD, Q3_RSP, Q3_ARG, MsgId, Args, NumArgs, OutStatus, OutRet);
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
  Status = SmuQ3Send (0x28, &Arg, 1, NULL, NULL);
  if (EFI_ERROR (Status)) {
    return Status;
  }

  Arg = Value;
  return SmuQ3Send (0x29, &Arg, 1, NULL, NULL);
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
  Status = SmuQ3Send (0x2B, &Arg, 1, NULL, NULL);
  if (EFI_ERROR (Status)) {
    return Status;
  }

  Arg = Value;
  return SmuQ3Send (0x2C, &Arg, 1, NULL, NULL);
}

/* Liveness probe: Q3 test message 0x01 must echo arg+1 (field-proven). */
STATIC
BOOLEAN
SmuAlive (
  VOID
  )
{
  UINT32     TestVal;
  UINT32     Result;
  EFI_STATUS Status;

  TestVal = 0x1234;
  Result  = 0;
  Status  = SmuQ3Send (0x01, &TestVal, 1, NULL, &Result);
  return (BOOLEAN)(!EFI_ERROR (Status) && Result == 0x1235);
}

STATIC
VOID
OverwriteTrTablePtr (
  IN UINT32 ByteVal
  )
{
  UINT32 PtrSlot;
  UINT32 Count;
  UINT32 Idx;
  UINT32 Args[4];

  PtrSlot = (TR_TABLE_FAKE_RING_ENTRY - RING_BASE) / RING_ENTRY_SZ;
  Count = RING_SUBQ_SLOTS - mSubq4CurIdx;

  Args[0] = 0; Args[1] = 0; Args[2] = 0; Args[3] = RING_CMD_TYPE (1, 4);
  for (Idx = 0; Idx < Count; Idx++) {
    SmuQ2Send (0x23, Args, 4, NULL, NULL);
  }

  Args[0] = PtrSlot; Args[1] = 0; Args[2] = 0; Args[3] = RING_CMD_TYPE (1, 4);
  SmuQ2Send (0x23, Args, 4, NULL, NULL);

  Args[0] = 0; Args[1] = 0; Args[2] = ByteVal; Args[3] = RING_CMD_TYPE (1, 1);
  SmuQ2Send (0x23, Args, 4, NULL, NULL);

  mSubq4CurIdx = 2;
}

STATIC
EFI_STATUS
PerformSmuUnlock (
  IN EFI_PHYSICAL_ADDRESS PhysAddr,
  IN VOID                 *VirtAddr
  )
{
  UINT32 P;
  UINT32 N;
  UINT32 *Table;
  EFI_STATUS Status;
  UINT32 Idx;
  UINT32 Args[6];

  Print (L"[*] Starting SMU Q2 transfer-table exploit...\n");

  P = 0x0000797CU;
  N = (0x7B20U - P) / 4U;

  Table = (UINT32 *)VirtAddr;
  ZeroMem (Table, 4096);

  Table[0] = 1;
  Table[1] = 0;
  Table[2] = 0;
  Table[3] = 0;
  Table[4] = 0;
  Table[5] = 0;
  Table[6] = (UINT32)(FAKE_ENTRY_KEY | (N << 16));
  Table[7] = 0;

  // Stage 1: Point transfer table to P - 0x1C
  Print (L"[*] Stage 1: Overwriting transfer table pointer to (P - 0x1C = 0x%05X)...\n", P - 0x1CU);
  OverwriteTrTablePtr (P - 0x1CU);

  Args[0] = 0x23U;                           // Sub-opcode: DMA DRAM to SMU key entry
  Args[1] = (UINT32)(PhysAddr >> 32);        // DRAM Addr High
  Args[2] = (UINT32)(PhysAddr & 0xFFFFFFFF); // DRAM Addr Low
  Args[3] = 8U;                              // Words: fake table = 8 dwords
  Args[4] = 0U;
  Args[5] = 3U;                              // Target entry key: 3
  Status = SmuQ2Send (0x0A, Args, 6, NULL, NULL);
  if (EFI_ERROR (Status)) {
    Print (L"[-] Stage 1 transfer failed: %r\n", Status);
    return Status;
  }
  Print (L"[+] Stage 1: Fake transfer table transferred to SRAM.\n");

  // Stage 2: Overwrite 0x7B3C via transfer table at P
  Table[0] = 0;
  Print (L"[*] Stage 2: Overwriting transfer table pointer to P (0x%05X)...\n", P);
  OverwriteTrTablePtr (P);

  Args[0] = 0x23U;
  Args[1] = (UINT32)(PhysAddr >> 32);
  Args[2] = (UINT32)(PhysAddr & 0xFFFFFFFF);
  Args[3] = 1U;
  Args[4] = 0U;
  Args[5] = NEW_ENTRY_KEY;                   // Target entry key: 0x37
  Status = SmuQ2Send (0x0A, Args, 6, NULL, NULL);
  if (EFI_ERROR (Status)) {
    Print (L"[-] Stage 2 transfer failed: %r\n", Status);
    return Status;
  }
  Print (L"[+] Stage 2: Lock byte 0x7B3C cleared via DMA write.\n");

  // Stage 3: Fixup SMU internal state
  Print (L"[*] Repairing SMU internal pointers...\n");
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

  Print (L"[+] SMU repair complete.\n");
  return EFI_SUCCESS;
}

/* BAR5 MMIO arbiter: GPU MMIO transport, safe post-clock-work
 * (2026-08-25: all-ones + NO hang, twice). */
STATIC
VOID
Bar5Arbiter (
  IN UINT32 Bar5,
  IN CONST CHAR16 *Label
  )
{
  UINT32 Version;
  UINT32 PowerStatus;
  UINT32 NoOp;

  Version     = MmioRead32 (Bar5 + VCN_MMIO_UVD_VERSION);
  PowerStatus = MmioRead32 (Bar5 + VCN_MMIO_UVD_POWER_STATUS);
  NoOp        = MmioRead32 (Bar5 + VCN_MMIO_UVD_NO_OP);

  Print (L"[%s] UVD_VERSION=0x%08X POWER_STATUS=0x%08X NO_OP=0x%08X\n",
         Label, Version, PowerStatus, NoOp);
  if ((Version != 0xFFFFFFFFU) && (Version != 0)) {
    Print (L">>> BRIDGE OPEN (real UVD_VERSION read) -- %s <<<\n", Label);
  } else {
    Print (L"[*] Island reads all-ones/zero at %s (transport returned).\n", Label);
  }
}

STATIC CONST EFI_GUID mEfiFileInfoGuid = EFI_FILE_INFO_ID;

STATIC
EFI_STATUS
ChainloadLimine (
  IN EFI_HANDLE ImageHandle
  )
{
  EFI_STATUS                       Status;
  UINTN                            HandleCount;
  EFI_HANDLE                       *HandleBuffer;
  UINTN                            Index;
  EFI_SIMPLE_FILE_SYSTEM_PROTOCOL  *Fs;
  EFI_FILE_PROTOCOL                *Root;
  EFI_FILE_PROTOCOL                *File;
  EFI_FILE_INFO                    *FileInfo;
  UINTN                            InfoSize;
  UINTN                            FileSize;
  EFI_DEVICE_PATH_PROTOCOL         *FilePath;
  EFI_HANDLE                       TargetImageHandle;
  STATIC CONST CHAR16              *CandidatePaths[] = {
    L"EFI\\limine\\limine_x64.efi",
    L"\\EFI\\limine\\limine_x64.efi"
  };
  UINTN                            PathIdx;

  Print (L"\n[*] Searching for NVMe bootloader (Limine) to chainload...\n");

  Status = gBS->LocateHandleBuffer (
                  ByProtocol,
                  &gEfiSimpleFileSystemProtocolGuid,
                  NULL,
                  &HandleCount,
                  &HandleBuffer
                  );
  if (EFI_ERROR (Status)) {
    Print (L"[-] Failed to locate file system handles: %r\n", Status);
    return Status;
  }

  for (Index = 0; Index < HandleCount; Index++) {
    Status = gBS->HandleProtocol (
                    HandleBuffer[Index],
                    &gEfiSimpleFileSystemProtocolGuid,
                    (VOID **)&Fs
                    );
    if (EFI_ERROR (Status)) {
      continue;
    }

    Status = Fs->OpenVolume (Fs, &Root);
    if (EFI_ERROR (Status)) {
      continue;
    }

    for (PathIdx = 0; PathIdx < ARRAY_SIZE (CandidatePaths); PathIdx++) {
      Status = Root->Open (
                       Root,
                       &File,
                       (CHAR16 *)CandidatePaths[PathIdx],
                       EFI_FILE_MODE_READ,
                       0
                       );
      if (EFI_ERROR (Status)) {
        continue;
      }

      InfoSize = 0;
      Status = File->GetInfo (File, (EFI_GUID *)&mEfiFileInfoGuid, &InfoSize, NULL);
      if (Status != EFI_BUFFER_TOO_SMALL) {
        File->Close (File);
        continue;
      }

      Status = gBS->AllocatePool (EfiBootServicesData, InfoSize, (VOID **)&FileInfo);
      if (EFI_ERROR (Status)) {
        File->Close (File);
        continue;
      }

      Status = File->GetInfo (File, (EFI_GUID *)&mEfiFileInfoGuid, &InfoSize, FileInfo);
      if (EFI_ERROR (Status)) {
        gBS->FreePool (FileInfo);
        File->Close (File);
        continue;
      }

      FileSize = (UINTN)FileInfo->FileSize;
      gBS->FreePool (FileInfo);
      File->Close (File);

      if (FileSize < 50000) {
        continue;
      }

      Print (L"[+] Found bootloader on volume %d: %s (%d bytes)\n", Index, CandidatePaths[PathIdx], FileSize);

      FilePath = FileDevicePath (HandleBuffer[Index], CandidatePaths[PathIdx]);
      if (FilePath == NULL) {
        Print (L"[-] FileDevicePath failed\n");
        continue;
      }

      Print (L"[+] Loading bootloader via DevicePath from volume...\n");
      Status = gBS->LoadImage (
                      FALSE,
                      ImageHandle,
                      FilePath,
                      NULL,
                      0,
                      &TargetImageHandle
                      );
      if (EFI_ERROR (Status)) {
        Print (L"[-] LoadImage via DevicePath failed: %r\n", Status);
        continue;
      }

      Root->Close (Root);
      gBS->FreePool (HandleBuffer);

      Print (L"\n>>> CHAINLOADING DIRECTLY INTO LINUX (ZERO REBOOT / PERSISTENT VCN) <<<\n\n");
      gBS->Stall (1500000);
      Status = gBS->StartImage (TargetImageHandle, NULL, NULL);
      Print (L"[-] StartImage returned: %r\n", Status);
      return Status;
    }

    Root->Close (Root);
  }

  gBS->FreePool (HandleBuffer);
  Print (L"[-] No chainloadable bootloader found on storage volumes.\n");
  return EFI_NOT_FOUND;
}

STATIC
VOID
WaitForKey (
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  EFI_INPUT_KEY Key;
  UINTN         EventIndex;

  if (SystemTable == NULL || SystemTable->ConIn == NULL) {
    return;
  }

  Print (L"\nPress any key to exit.\n");
  if (!EFI_ERROR (gBS->WaitForEvent (1, &SystemTable->ConIn->WaitForKey, &EventIndex))) {
    SystemTable->ConIn->ReadKeyStroke (SystemTable->ConIn, &Key);
  }
}

EFI_STATUS
EFIAPI
UefiMain (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  EFI_STATUS           Status;
  EFI_PHYSICAL_ADDRESS DmaPhys;
  VOID                 *DmaVirt;
  UINT32               GpuId;
  UINT32               Bar5;
  UINTN                Index;

  (VOID)ImageHandle;

  Print (L"===========================================================\n");
  Print (L"  AMD BC-250 VCN UEFI BRING-UP v4 (2026-09-12 RUNBOOK)     \n");
  Print (L"===========================================================\n\n");

  GpuId = PciSegmentRead32 (BC250_GPU_PCI_ADDRESS (0x00));
  Bar5 = PciSegmentRead32 (BC250_GPU_PCI_ADDRESS (0x24)) & 0xFFFFFFF0U;
  {
      UINT16 PciCmd = PciSegmentRead16 (BC250_GPU_PCI_ADDRESS (0x04));
    if ((PciCmd & 0x0006U) != 0x0006U) {
      PciSegmentWrite16 (BC250_GPU_PCI_ADDRESS (0x04), PciCmd | 0x0006U);
    }
  }
  Print (L"GPU PCI 01:00.0 ID = 0x%08X (Expected: 0x13FE1002)\n", GpuId);
  Print (L"GPU BAR5 Base      = 0x%08X\n\n", Bar5);

  if (GpuId == 0xFFFFFFFFU) {
    Print (L"[-] FATAL: GPU 01:00.0 not enumerated. Aborting.\n");
    goto Exit;
  }

  // 1. Verify basic Q3 health
  if (!SmuAlive ()) {
    Print (L"[-] FATAL: SMU Q3 not responding.\n");
    goto Exit;
  }
  Print (L"[+] SMU Q3 responsive (test message OK)\n");

  // 2. Unlock privileged SMU access (Q2 transfer-table exploit)
  {
    DmaPhys = 0xFFFFFFFFULL;
    Status = gBS->AllocatePages (AllocateMaxAddress, EfiBootServicesData, 1, &DmaPhys);
    if (EFI_ERROR (Status)) {
      Print (L"[-] Failed to allocate DMA page: %r\n", Status);
      goto Exit;
    }
    DmaVirt = (VOID *)(UINTN)DmaPhys;

    Status = PerformSmuUnlock (DmaPhys, DmaVirt);
    gBS->FreePages (DmaPhys, 1);

    if (EFI_ERROR (Status)) {
      Print (L"[-] FATAL: Exploit failed. Halting before privileged operations.\n");
      goto Exit;
    }
  }

  if (!SmuAlive ()) {
    Print (L"[-] SMU dead after unlock -- cold power cycle required.\n");
    goto Exit;
  }
  Print (L"[+] SMU alive after unlock.\n");

  // 3. Baseline BAR5 arbiter (pre-gasket delta evidence)
  Bar5Arbiter (Bar5, L"BASELINE");

  // 4. dom6 gate release (2026-09-12: 0x02 -> 0x00 LANDED and HELD)
  Print (L"[*] Releasing dom6 gate (0x06D0F8 <- 0)...\n");
  Status = SmuWriteSmn32 (DOM6_CTRL, 0x00000000U);
  if (EFI_ERROR (Status)) {
    Print (L"[-] dom6 gate release failed: %r (continuing: gate may be open)\n", Status);
  } else {
    Print (L"[+] dom6 gate release accepted.\n");
  }

  // 5. Unified clocks + power thunk, fired via Q3 msg 0x61
  Print (L"\n[*] Executing Unified VCN Clocks & Power Bring-up Thunk...\n");
  {
    STATIC CONST UINT8 ThunkVcnBringup[28] = {
      0x36, 0x41, 0x00, 0x1C, 0x6A, 0xE5, 0x83, 0xE3,
      0x1C, 0x7A, 0xA5, 0x83, 0xE3, 0x1C, 0x8A, 0x65,
      0x83, 0xE3, 0x0C, 0x6A, 0x0C, 0x1B, 0xA5, 0xC0,
      0xE3, 0x1D, 0xF0, 0x00
    };
    UINT32 Word;
    for (Index = 0; Index < sizeof (ThunkVcnBringup); Index += 4) {
      CopyMem (&Word, &ThunkVcnBringup[Index], 4);
      Status = SmuWriteSram32 (THUNK_SRAM_ADDR + (UINT32)Index, Word);
      if (EFI_ERROR (Status)) {
        Print (L"[-] Failed writing unified thunk word %d: %r\n", Index, Status);
        goto Exit;
      }
    }
    SmuWriteSram32 (Q3_HANDLER_SLOT_61, THUNK_SRAM_ADDR);

    SmnWrite32 (Q3_RSP, 0);
    SmnWrite32 (Q3_CMD, 0x61);
    gBS->Stall (100000); // 100ms for hardware clock and power transitions

    SmuWriteSram32 (Q3_HANDLER_SLOT_61, 0);
    Print (L"[+] Unified VCN Clocks + Power sequence fired (msg 0x61).\n");
  }

  if (!SmuAlive ()) {
    Print (L"[-] SMU dead after fire 0x61 -- cold power cycle required.\n");
    goto Exit;
  }
  Print (L"[+] SMU alive after fire.\n");

  // 6. Bank-12 gasket (56 writes, values = decoded donor SEC_GASKET body)
  Print (L"[*] Applying %d Bank 12 Gasket configuration writes...\n", ARRAY_SIZE (mGasketBank12Writes));
  for (Index = 0; Index < ARRAY_SIZE (mGasketBank12Writes); Index++) {
    Status = SmuWriteSmn32 (mGasketBank12Writes[Index].Address, mGasketBank12Writes[Index].Value);
    if (EFI_ERROR (Status)) {
      Print (L"[-] Gasket write %d (0x%08X) failed: %r\n", Index, mGasketBank12Writes[Index].Address, Status);
      goto Exit;
    }
  }
  Print (L"[+] Bank 12 gasket: %d writes accepted.\n", ARRAY_SIZE (mGasketBank12Writes));

  if (!SmuAlive ()) {
    Print (L"[-] SMU dead after gasket -- cold power cycle required.\n");
    goto Exit;
  }

  // 7. FULL donor dataplane routes (never runtime-written before; stage5 list)
  Print (L"[*] Applying %d donor dataplane route writes...\n", ARRAY_SIZE (mDonorRouteWrites));
  for (Index = 0; Index < ARRAY_SIZE (mDonorRouteWrites); Index++) {
    Status = SmuWriteSmn32 (mDonorRouteWrites[Index].Address, mDonorRouteWrites[Index].Value);
    if (EFI_ERROR (Status)) {
      Print (L"[-] Donor route write %d (0x%08X) failed: %r\n",
             Index, mDonorRouteWrites[Index].Address, Status);
      goto Exit;
    }
  }
  Print (L"[+] Donor dataplane: %d writes accepted.\n", ARRAY_SIZE (mDonorRouteWrites));

  if (!SmuAlive ()) {
    Print (L"[-] SMU dead after donor routes -- cold power cycle required.\n");
    goto Exit;
  }

  // 8. VERDICT: BAR5 arbiter after the full donor dataplane
  gBS->Stall (200000); // 200ms settle
  Bar5Arbiter (Bar5, L"VERDICT ");

  // 9. Same-session chainload (zero reboot: VCN state persists into Linux)
  Status = ChainloadLimine (ImageHandle);
  if (EFI_ERROR (Status)) {
    Print (L"[-] Chainload failed (%r). Falling back to key wait.\n", Status);
  }

Exit:
  WaitForKey (SystemTable);
  return EFI_SUCCESS;
}
