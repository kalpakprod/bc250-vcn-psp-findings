/** @file Bc250VcnProbe3.c

  UEFI boot application (no Shell needed) for the BC-250 VCN bring-up
  (robin_5 SMU). Launched by the firmware boot manager from
  \EFI\BOOT\BOOTX64.EFI on a FAT32 USB stick.

  Automates the donor-plan capture (supersedes Bc250VcnProbe2 for the
  operator loop):
    1. Reads the same read-only register set as probe2: clock plan
       0x0115D000/D004 with the VCN descriptor window (both plan copies),
       the domain permission bitmap 0x0000CCB8, the power status
       0x01D80218, the clock request bits 0x0115F95C, and the clock
       controller window 0x0115F800..0x0115F974. NO register writes, no
       mailbox messages.
    2. Saves the full report to \probe2-out.txt on the volume that
       carries the \PROBE2.TXT marker (the only file it writes).
    3. Reboots the board (EfiResetCold). With a one-time USB boot pick
       the firmware then boots Linux as usual.

  Fallbacks: marker volume not found -> the report is printed to the
  console instead; ResetSystem returning -> exit EFI_SUCCESS and the boot
  manager continues with the next boot option.

  Runbook: docs/runbooks/2026-09-23-vcn-mailbox-sequence-DRAFT.md
  Driver:  candidates/vcn-unlock-driver-v000-DRAFT/BC250VCNUnlockDxe.c
**/

#include <Uefi.h>
#include <Protocol/SimpleFileSystem.h>
#include <Library/BaseLib.h>
#include <Library/BaseMemoryLib.h>
#include <Library/PciSegmentLib.h>
#include <Library/PrintLib.h>
#include <Library/UefiApplicationEntryPoint.h>
#include <Library/UefiBootServicesTableLib.h>
#include <Library/UefiLib.h>
#include <Library/UefiRuntimeServicesTableLib.h>

#define SMN_INDEX_OFFSET  0xB8
#define SMN_DATA_OFFSET   0xBC
#define HOST_CFG(Offset)  PCI_SEGMENT_LIB_ADDRESS (0, 0, 0, 0, (Offset))

#define PLAN_A       0x0115D000U
#define PLAN_B       0x0115D004U
#define DESC_OFF     0x560U
#define DESC_WORDS   10U
#define BITMAP       0x0000CCB8U
#define STATUS       0x01D80218U
#define REQ_BITS     0x0115F95CU
#define CTL_BASE     0x0115F800U
#define CTL_WORDS    0x60U

#define OUT_BUF_SZ   16384U
#define LINE_SZ      512U
#define MARKER_FILE  L"PROBE2.TXT"
#define OUT_FILE     L"probe2-out.txt"

STATIC CHAR8   mOut[OUT_BUF_SZ];
STATIC UINTN   mOutPos = 0;
STATIC BOOLEAN mSaved = FALSE;

STATIC UINT32 SmnRead32 (IN UINT32 Reg)
{
  PciSegmentWrite32 (HOST_CFG (SMN_INDEX_OFFSET), Reg);
  return PciSegmentRead32 (HOST_CFG (SMN_DATA_OFFSET));
}

STATIC VOID Out (IN CONST CHAR8 *Fmt, ...)
{
  VA_LIST  Args;
  UINTN    Len;
  CHAR8    Line[LINE_SZ];

  VA_START (Args, Fmt);
  AsciiVSPrint (Line, LINE_SZ, Fmt, Args);
  VA_END (Args);

  Print (L"%a", Line);

  Len = AsciiStrLen (Line);
  if (mOutPos + Len + 1 < OUT_BUF_SZ) {
    CopyMem (mOut + mOutPos, Line, Len);
    mOutPos += Len;
    mOut[mOutPos] = '\0';
  }
}

STATIC VOID Dump (IN CONST CHAR8 *Label, IN UINT32 Base, IN UINT32 Count)
{
  UINT32 i;

  Out ("%a:\n", Label);
  for (i = 0; i < Count; i += 4) {
    Out ("  +0x%05x: %08x %08x %08x %08x\n", Base + i,
         SmnRead32 (Base + i),      SmnRead32 (Base + i + 4),
         SmnRead32 (Base + i + 8),  SmnRead32 (Base + i + 12));
  }
}

STATIC EFI_STATUS SaveResults (VOID)
{
  EFI_STATUS                        Status;
  EFI_HANDLE                        *Handles = NULL;
  UINTN                             Count = 0;
  UINTN                             Index;
  UINTN                             N;
  EFI_SIMPLE_FILE_SYSTEM_PROTOCOL   *Fs;
  EFI_FILE_PROTOCOL                 *Root = NULL;
  EFI_FILE_PROTOCOL                 *File = NULL;

  Status = gBS->LocateHandleBuffer (
                  ByProtocol,
                  &gEfiSimpleFileSystemProtocolGuid,
                  NULL,
                  &Count,
                  &Handles
                  );
  if (EFI_ERROR (Status)) {
    return Status;
  }

  for (Index = 0; Index < Count; Index++) {
    if (EFI_ERROR (gBS->HandleProtocol (
                     Handles[Index],
                     &gEfiSimpleFileSystemProtocolGuid,
                     (VOID **)&Fs
                     ))) {
      continue;
    }
    if (EFI_ERROR (Fs->OpenVolume (Fs, &Root))) {
      continue;
    }
    if (EFI_ERROR (Root->Open (Root, &File, MARKER_FILE,
                               EFI_FILE_MODE_READ, 0))) {
      Root->Close (Root);
      continue;
    }
    File->Close (File);

    if (!EFI_ERROR (Root->Open (Root, &File, OUT_FILE,
                                EFI_FILE_MODE_READ, 0))) {
      File->Delete (File);
    }
    Status = Root->Open (Root, &File, OUT_FILE,
                         EFI_FILE_MODE_CREATE | EFI_FILE_MODE_WRITE
                         | EFI_FILE_MODE_READ, 0);
    if (EFI_ERROR (Status)) {
      Root->Close (Root);
      continue;
    }
    N = AsciiStrLen (mOut);
    Status = File->Write (File, &N, mOut);
    if (!EFI_ERROR (Status)) {
      File->Flush (File);
    }
    File->Close (File);
    Root->Close (Root);
    gBS->FreePool (Handles);
    mSaved = TRUE;
    return Status;
  }

  gBS->FreePool (Handles);
  return EFI_NOT_FOUND;
}

EFI_STATUS
EFIAPI
UefiMain (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  UINT32  DescZero = 1;
  UINT32  Bitmap;
  UINT32  StatusReg;
  UINT32  ReqBits;
  UINT32  i;

  mOut[0] = '\0';
  Out ("BC250 VCN probe3 (auto: file save + reboot; registers read-only)\n");

  Out ("clock plan words: A=0x%08x B=0x%08x\n",
       SmnRead32 (PLAN_A), SmnRead32 (PLAN_B));

  Out ("VCN descriptor window (bits 0x2B00..0x2C15):\n");
  for (i = 0; i < DESC_WORDS; i++) {
    UINT32 a = SmnRead32 (PLAN_A + DESC_OFF + i * 4);
    UINT32 b = SmnRead32 (PLAN_B + DESC_OFF + i * 4);
    if ((a | b) != 0) {
      DescZero = 0;
    }
    Out ("  +%03x: A=%08x B=%08x\n", DESC_OFF + i * 4, a, b);
  }
  Out ("VCN descriptor: %a\n",
       DescZero ? "EMPTY (0x1B would hang SMU - donor fill required)"
                : "populated");

  Bitmap = SmnRead32 (BITMAP);
  Out ("domain bitmap 0x0000CCB8 = 0x%08x (bit6 VCN %a)\n",
       Bitmap, (Bitmap & 0x40U) ? "set" : "clear");

  StatusReg = SmnRead32 (STATUS);
  Out ("power status 0x01D80218 = 0x%08x (0x0C00 mask %a)\n",
       StatusReg, (StatusReg & 0x0C00U) ? "set" : "clear");

  ReqBits = SmnRead32 (REQ_BITS);
  Out ("request bits 0x0115F95C = 0x%08x\n", ReqBits);

  Dump ("clock controller 0x0115F800..0x0115F974", CTL_BASE, CTL_WORDS * 4);

  if (EFI_ERROR (SaveResults ())) {
    Out ("save FAILED (no marker volume or write error); report above only\n");
  } else {
    Out ("saved to %a\n", "probe2-out.txt");
  }
  Out ("probe3 done, rebooting\n");

  gBS->Stall (1000000);
  gRT->ResetSystem (EfiResetCold, EFI_SUCCESS, 0, NULL);

  Out ("ResetSystem returned; exiting (boot manager continues)\n");
  return EFI_SUCCESS;
}
