/** @file Bc250VcnProbe4.c

  UEFI boot application (no Shell needed) for the BC-250 VCN bring-up
  (robin_5 SMU). Launched by the firmware boot manager from
  \EFI\BOOT\BOOTX64.EFI on a FAT32 USB stick.

  Supersedes probe3 after run 1 (2026-09-23): probe3's raw SMN reads
  through the PCI 0xB8/0xBC window WEDGED the board at the first read
  (SMN 0x0115D000, clock plan A) - the known DF/SMU-space read-wedge
  class. probe4 changes the transport, not the target set:

    1. Hardware-proven SMU debug unlock (the D9R/D10/d19
       PerformSmuUnlockDxe sequence: Q2 ring writes + DMA table + SRAM
       fixup; writes are the proven-safe first touch on this board).
    2. All register reads go through the SMU's own Q3 0x2A secure-read
       service (hardware-proven at early DXE: SMN 0x0005A870 read with
       status 0x01, SMU alive after). The raw 0xB8/0xBC window is used
       ONLY for the Q2/Q3 mailbox registers (0x03B1xxxx), which are the
       proven-safe addresses.
    3. Same report set as probe3: clock plan 0x0115D000/D004 + VCN
       descriptor window (+0x560, both copies), domain bitmap
       0x0000CCB8, power status 0x01D80218, request bits 0x0115F95C,
       clock controller 0x0115F800..0x0115F974.
    4. Saves \probe2-out.txt to the volume carrying \PROBE2.TXT, then
       reboots (EfiResetCold). With a one-time USB boot pick the
       firmware boots Linux as usual.

  Progress is printed per phase so that, if the board ever wedges again,
  the LAST LINE ON SCREEN names the transport step and address that
  wedged it (probe3's banner-only screen proved the value of this).

  Risk boundary (honest): probe4 is NOT read-only like probe3 claimed to
  be. The unlock writes SMU SRAM (proven sequence, lived inside flashed
  D9R/D10 images that booted normally; non-persistent - PSP re-applies
  state at every boot). The reads ask the SMU to read its own space. If
  anything wedges: cold power cycle; the flashed image is untouched.

  Runbook: docs/runbooks/2026-09-23-vcn-mailbox-sequence-DRAFT.md
  Transport provenance: candidates/d19-gasket-c830-only/source/.../
  Bc250VcnUnlockDxe.c (SmuMailboxSend / PerformSmuUnlockDxe / SmuReadSmn32)
  and the community Bc250CoreUnlockDxe.c mailbox layer.
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

#define BC250_HOST_PCI_SEGMENT   0
#define BC250_HOST_PCI_BUS       0
#define BC250_HOST_PCI_DEVICE    0
#define BC250_HOST_PCI_FUNCTION  0

#define SMN_INDEX_OFFSET  0xB8
#define SMN_DATA_OFFSET   0xBC
#define HOST_CFG(Offset)  PCI_SEGMENT_LIB_ADDRESS (0, 0, 0, 0, (Offset))

// SMU Queue register sets (the ONLY SMN addresses touched raw).
#define Q2_CMD  0x03B10528U
#define Q2_RSP  0x03B10564U
#define Q2_ARG  0x03B10998U
#define Q3_CMD  0x03B10A20U
#define Q3_RSP  0x03B10A80U
#define Q3_ARG  0x03B10A88U

#define SMU_MAILBOX_ARGS          6U
#define SMU_MAILBOX_POLL_DELAY_US 1000U
#define SMU_MAILBOX_TIMEOUT_ITERS 5000U
#define SMU_RETURN_OK             0x01U
#define PROBE_ADDR                0x0005A870U

// Target register set (same as probe3; read via Q3 0x2A only).
#define PLAN_A     0x0115D000U
#define PLAN_B     0x0115D004U
#define DESC_OFF   0x560U
#define DESC_WORDS 10U
#define BITMAP     0x0000CCB8U
#define STATUS     0x01D80218U
#define REQ_BITS   0x0115F95CU
#define CTL_BASE   0x0115F800U
#define CTL_WORDS  0x60U

#define OUT_BUF_SZ  16384U
#define LINE_SZ     512U
#define MARKER_FILE L"PROBE2.TXT"
#define OUT_FILE    L"probe2-out.txt"

STATIC CHAR8   mOut[OUT_BUF_SZ];
STATIC UINTN   mOutPos = 0;
STATIC BOOLEAN mSaved = FALSE;
/* Abort the survey after 3 consecutive mailbox TIMEOUTs: the SMU stopped
   responding; grinding through the rest would only stall ~5 s per read. */
STATIC UINTN   mTimeoutStreak = 0;
#define TIMEOUT_STREAK_LIMIT 3U

/* ------------------------- raw window (mailbox regs only) ---------- */

STATIC UINT32 SmnRead32 (IN UINT32 Reg)
{
  PciSegmentWrite32 (HOST_CFG (SMN_INDEX_OFFSET), Reg);
  return PciSegmentRead32 (HOST_CFG (SMN_DATA_OFFSET));
}

STATIC VOID SmnWrite32 (IN UINT32 Reg, IN UINT32 Value)
{
  PciSegmentWrite32 (HOST_CFG (SMN_INDEX_OFFSET), Reg);
  PciSegmentWrite32 (HOST_CFG (SMN_DATA_OFFSET), Value);
}

/* ------------------------- report buffer --------------------------- */

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

/* ------------------------- SMU mailbox layer (d19-proven) ---------- */

STATIC EFI_STATUS SmuMailboxSend (
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

STATIC EFI_STATUS SmuWriteSram32 (
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

/* Q3 0x2A: ask the SMU to read its own SMN address; value returns in ARG. */
STATIC EFI_STATUS SmuReadSmn32 (
  IN  UINT32 Addr,
  OUT UINT32 *Value
  )
{
  UINT32 Arg;
  Arg = Addr;
  return SmuMailboxSend (Q3_CMD, Q3_RSP, Q3_ARG, 0x2A, &Arg, 1, NULL, Value);
}

/* ------------------------- SMU debug unlock (D9R/D10/d19-proven) --- */

STATIC EFI_STATUS PerformSmuUnlock (OUT BOOLEAN *AlreadyUnlocked)
{
  EFI_STATUS           Status;
  EFI_PHYSICAL_ADDRESS DmaPhys;
  UINT32               *Table;
  UINT32               ProbeVal;
  UINT32               Idx;
  UINT32               P;
  UINT32               N;
  UINT32               Args[6];

  *AlreadyUnlocked = FALSE;

  Out ("unlock: probing secure read 0x%08x\n", PROBE_ADDR);
  Status = SmuReadSmn32 (PROBE_ADDR, &ProbeVal);
  if (!EFI_ERROR (Status)) {
    Out ("unlock: already open (0x%08x = 0x%08x)\n", PROBE_ADDR, ProbeVal);
    *AlreadyUnlocked = TRUE;
    return EFI_SUCCESS;
  }
  if (Status == EFI_TIMEOUT) {
    Out ("unlock: mailbox not answering at all - aborting (SMU dead or wedged)\n");
    return Status;
  }

  Out ("unlock: locked (refused), running the proven sequence\n");

  DmaPhys = 0xFFFFFFFFULL;
  Status = gBS->AllocatePages (AllocateMaxAddress, EfiBootServicesData, 1, &DmaPhys);
  if (EFI_ERROR (Status)) {
    return Status;
  }

  Table = (UINT32 *)(UINTN)DmaPhys;
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
  Out ("unlock: stage 1 sent\n");

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
  Out ("unlock: stage 2 sent\n");

  gBS->FreePages (DmaPhys, 1);

  Out ("unlock: fixup writes\n");

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

  Out ("unlock: verifying secure read\n");
  return SmuReadSmn32 (PROBE_ADDR, &ProbeVal);
}

/* ------------------------- read helpers ---------------------------- */

/* One secure read with an on-screen trace line; returns the value.
   EFI_TIMEOUT means the SMU stopped answering the mailbox: counted toward
   the abort streak (a wedged SMU never recovers without a power cycle). */
STATIC UINT32 ReadTraced (IN CONST CHAR8 *Tag, IN UINT32 Addr, OUT BOOLEAN *Ok)
{
  UINT32 V;
  EFI_STATUS S;

  if (mTimeoutStreak >= TIMEOUT_STREAK_LIMIT) {
    *Ok = FALSE;
    return 0;
  }

  Out ("read %a 0x%08x\n", Tag, Addr);
  S = SmuReadSmn32 (Addr, &V);
  if (S == EFI_TIMEOUT) {
    mTimeoutStreak++;
    *Ok = FALSE;
    Out ("read %a 0x%08x TIMEOUT (%u)\n", Tag, Addr, (UINT32)mTimeoutStreak);
    return 0;
  }
  mTimeoutStreak = 0;
  if (EFI_ERROR (S)) {
    *Ok = FALSE;
    Out ("read %a 0x%08x DENIED\n", Tag, Addr);
    return 0;
  }
  *Ok = TRUE;
  return V;
}

/* ------------------------- file save (probe3-proven) --------------- */

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

/* ------------------------- entry point ----------------------------- */

EFI_STATUS
EFIAPI
UefiMain (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  EFI_STATUS Status;
  BOOLEAN    Ok;
  BOOLEAN    AlreadyUnlocked;
  UINT32     DescZero = 1;
  UINT32     Bitmap;
  UINT32     StatusReg;
  UINT32     ReqBits;
  UINT32     PlanA;
  UINT32     PlanB;
  UINT32     i;

  mOut[0] = '\0';
  Out ("BC250 VCN probe4 (mailbox transport: SMU unlock + Q3 0x2A secure reads)\n");

  Status = PerformSmuUnlock (&AlreadyUnlocked);
  if (EFI_ERROR (Status)) {
    Out ("unlock FAILED (%r); no raw reads will be attempted\n", Status);
  }

  // Single control words, lowest-risk first (SMU SRAM / SMU space).
  Bitmap   = ReadTraced ("bitmap",   BITMAP,   &Ok);
  StatusReg = ReadTraced ("status",  STATUS,   &Ok);
  ReqBits  = ReadTraced ("reqbits",  REQ_BITS, &Ok);

  // Clock plan words (probe3's first-read wedge point, now via 0x2A).
  PlanA = ReadTraced ("planA", PLAN_A, &Ok);
  PlanB = ReadTraced ("planB", PLAN_B, &Ok);
  Out ("clock plan words: A=0x%08x B=0x%08x\n", PlanA, PlanB);

  // VCN descriptor window (both plan copies), printed as it goes.
  Out ("VCN descriptor window (bits 0x2B00..0x2C15):\n");
  for (i = 0; i < DESC_WORDS; i++) {
    UINT32 a = ReadTraced ("descA", PLAN_A + DESC_OFF + i * 4, &Ok);
    UINT32 b = ReadTraced ("descB", PLAN_B + DESC_OFF + i * 4, &Ok);
    if ((a | b) != 0) {
      DescZero = 0;
    }
    Out ("  +%03x: A=%08x B=%08x\n", DESC_OFF + i * 4, a, b);
  }
  Out ("VCN descriptor: %a\n",
       DescZero ? "EMPTY (0x1B would hang SMU - donor fill required)"
                : "populated");

  Out ("domain bitmap 0x0000CCB8 = 0x%08x (bit6 VCN %a)\n",
       Bitmap, (Bitmap & 0x40U) ? "set" : "clear");
  Out ("power status 0x01D80218 = 0x%08x (0x0C00 mask %a)\n",
       StatusReg, (StatusReg & 0x0C00U) ? "set" : "clear");
  Out ("request bits 0x0115F95C = 0x%08x\n", ReqBits);

  // Clock controller window, 4 words per line, traced.
  Out ("clock controller 0x0115F800..0x0115F974:\n");
  for (i = 0; i < CTL_WORDS; i += 4) {
    UINT32 w0 = ReadTraced ("ctl", CTL_BASE + i * 4, &Ok);
    UINT32 w1 = ReadTraced ("ctl", CTL_BASE + (i + 1) * 4, &Ok);
    UINT32 w2 = ReadTraced ("ctl", CTL_BASE + (i + 2) * 4, &Ok);
    UINT32 w3 = ReadTraced ("ctl", CTL_BASE + (i + 3) * 4, &Ok);
    Out ("  +0x%05x: %08x %08x %08x %08x\n",
         CTL_BASE + i * 4, w0, w1, w2, w3);
  }

  if (mTimeoutStreak >= TIMEOUT_STREAK_LIMIT) {
    Out ("survey ABORTED: SMU stopped answering the mailbox (%u timeouts)\n",
         (UINT32)mTimeoutStreak);
  }

  if (EFI_ERROR (SaveResults ())) {
    Out ("save FAILED (no marker volume or write error); report above only\n");
  } else {
    Out ("saved to %a\n", "probe2-out.txt");
  }
  Out ("probe4 done, rebooting\n");

  gBS->Stall (1000000);
  gRT->ResetSystem (EfiResetCold, EFI_SUCCESS, 0, NULL);

  Out ("ResetSystem returned; exiting (boot manager continues)\n");
  return EFI_SUCCESS;
}
