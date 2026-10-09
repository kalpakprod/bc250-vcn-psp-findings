/** @file Bc250VcnProbe2.c

  UEFI Shell read-only probe for the BC-250 VCN bring-up (robin_5 SMU).

  Prints the state the v001 driver needs before a flash session:
  clock plan 0x0115D000/D004 with the VCN descriptor window (both plan
  copies), the domain permission bitmap 0x0000CCB8, the power status
  0x01D80218, the clock request bits 0x0115F95C, and the clock controller
  window 0x0115F800..0x0115F974. NO WRITES, no mailbox messages.

  Run from UEFI Shell on USB. Exit codes: 0 always (diagnostics only).

  Runbook: docs/runbooks/2026-09-23-vcn-mailbox-sequence-DRAFT.md
  Driver:  candidates/vcn-unlock-driver-v000-DRAFT/BC250VCNUnlockDxe.c
**/

#include <Uefi.h>
#include <Library/BaseLib.h>
#include <Library/PciSegmentLib.h>
#include <Library/UefiApplicationEntryPoint.h>
#include <Library/UefiBootServicesTableLib.h>
#include <Library/UefiLib.h>

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

STATIC UINT32 SmnRead32 (IN UINT32 Reg)
{
  PciSegmentWrite32 (HOST_CFG (SMN_INDEX_OFFSET), Reg);
  return PciSegmentRead32 (HOST_CFG (SMN_DATA_OFFSET));
}

STATIC VOID Dump (IN CONST CHAR16 *Label, IN UINT32 Base, IN UINT32 Count)
{
  UINT32 i;

  Print (L"%s:\n", Label);
  for (i = 0; i < Count; i += 4) {
    Print (L"  +0x%05x: %08x %08x %08x %08x\n", Base + i,
           SmnRead32 (Base + i),     SmnRead32 (Base + i + 4),
           SmnRead32 (Base + i + 8), SmnRead32 (Base + i + 12));
  }
}

EFI_STATUS
EFIAPI
UefiMain (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  UINT32  DescZero = 1;
  UINT32  i;

  Print (L"BC250 VCN probe v2 (read-only)\n");

  Print (L"clock plan words: A=0x%08x B=0x%08x\n",
         SmnRead32 (PLAN_A), SmnRead32 (PLAN_B));

  Print (L"VCN descriptor window (bits 0x2B00..0x2C15):\n");
  for (i = 0; i < DESC_WORDS; i++) {
    UINT32 a = SmnRead32 (PLAN_A + DESC_OFF + i * 4);
    UINT32 b = SmnRead32 (PLAN_B + DESC_OFF + i * 4);
    if ((a | b) != 0) {
      DescZero = 0;
    }
    Print (L"  +%03x: A=%08x B=%08x\n", DESC_OFF + i * 4, a, b);
  }
  Print (L"VCN descriptor: %s\n",
         DescZero ? L"EMPTY (0x1B would hang SMU - donor fill required)"
                  : L"populated");

  Print (L"domain bitmap 0x0000CCB8 = 0x%08x (bit6 VCN %s)\n",
         SmnRead32 (BITMAP),
         (SmnRead32 (BITMAP) & 0x40U) ? L"set" : L"clear");

  Print (L"power status 0x01D80218 = 0x%08x (0x0C00 mask %s)\n",
         SmnRead32 (STATUS),
         (SmnRead32 (STATUS) & 0x0C00U) ? L"set" : L"clear");

  Print (L"request bits 0x0115F95C = 0x%08x\n", SmnRead32 (REQ_BITS));

  Dump (L"clock controller 0x0115F800..0x0115F974", CTL_BASE, CTL_WORDS * 4);

  Print (L"probe done\n");
  return EFI_SUCCESS;
}
