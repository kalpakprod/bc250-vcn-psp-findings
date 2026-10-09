/** @file
  VcnUnlockDxe.c - Early UEFI DXE driver to unlock VCN on AMD BC-250 (Cyan Skillfish).
  Executes PSP C2P Mailbox handshake:
    1. Command 0x100B: fetch dynamic session token (fn@0x3528 / @0xE25814).
    2. Build $PS1 policy blob in RAM (group 0x201 VCN ungate + group 0x210 power).
    3. Command 0x100C: register dynamic blob descriptor.
    4. Command 0x1033: execute TOS policy sequencer (fn@0x20D4 / fn@0x2178).
**/

#include <Uefi.h>
#include <Library/UefiBootServicesTableLib.h>
#include <Library/DebugLib.h>
#include <Library/BaseMemoryLib.h>
#include <Library/MemoryAllocationLib.h>
#include <Library/BaseCryptLib.h>
#include <IndustryStandard/Pci.h>
#include <Protocol/PciRootBridgeIo.h>

#define PSP_PCI_BUS      0x01
#define PSP_PCI_DEV      0x00
#define PSP_PCI_FUNC     0x00

#define C2PMSG_35_OFFSET 0x10530  // Command / Status
#define C2PMSG_36_OFFSET 0x10534  // Buffer Lo (32-bit physical address)
#define C2PMSG_37_OFFSET 0x10538  // Buffer Hi (32-bit physical address)

#define PSP_CMD_GET_TOKEN   0x100B
#define PSP_CMD_LOAD_BLOB   0x100C
#define PSP_CMD_APPLY_VCN   0x1033

#pragma pack(1)
typedef struct {
  UINT64 PhysAddr;
  UINT32 Size;
  UINT32 Reserved;
  UINT64 ExpectedHashPtr;
  UINT32 Type;
  UINT32 Reserved2;
} PSP_BLOB_DESCRIPTOR;

typedef struct {
  UINT32 Magic;        // '$PS1' = 0x31535024
  UINT32 TotalSize;
  UINT32 Version;
  UINT32 Reserved;
  UINT8  KeyId[16];
  UINT8  Padding[0xE0];
  UINT8  SessionToken[32];
  UINT8  ValidationPadding[32];
  // Payload: Gasket Group 0x201 & 0x210
  UINT32 Group201Id;
  UINT32 Group201Count;
  UINT32 Regs201[12];
  UINT32 Group210Id;
  UINT32 Group210Count;
  UINT32 Regs210[4];
} PSP_DYNAMIC_BLOB;
#pragma pack()

STATIC
EFI_STATUS
PspSendMailbox (
  IN EFI_PHYSICAL_ADDRESS Bar5Base,
  IN UINT32 Command,
  IN EFI_PHYSICAL_ADDRESS BufferPhys
  )
{
  volatile UINT32 *RegCmd = (volatile UINT32 *)(Bar5Base + C2PMSG_35_OFFSET);
  volatile UINT32 *RegBufLo = (volatile UINT32 *)(Bar5Base + C2PMSG_36_OFFSET);
  volatile UINT32 *RegBufHi = (volatile UINT32 *)(Bar5Base + C2PMSG_37_OFFSET);
  UINT32 Timeout = 1000000;

  *RegBufLo = (UINT32)(BufferPhys & 0xFFFFFFFF);
  *RegBufHi = (UINT32)((BufferPhys >> 32) & 0xFFFFFFFF);
  *RegCmd = Command | 0x80000000; // Trigger

  while ((*RegCmd & 0x80000000) && --Timeout) {
    gBS->Stall(10);
  }

  if (Timeout == 0) {
    return EFI_TIMEOUT;
  }
  return (*RegCmd & 0xFFFF) == 0 ? EFI_SUCCESS : EFI_DEVICE_ERROR;
}

EFI_STATUS
EFIAPI
VcnUnlockDxeEntryPoint (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  EFI_STATUS Status;
  EFI_PCI_ROOT_BRIDGE_IO_PROTOCOL *PciIo;
  UINT64 PciAddress;
  UINT32 Bar5Lo, Bar5Hi;
  EFI_PHYSICAL_ADDRESS Bar5Base;
  UINT8 *TokenBuffer;
  PSP_DYNAMIC_BLOB *Blob;
  PSP_BLOB_DESCRIPTOR *Desc;
  UINT8 *HashBuffer;

  Status = gBS->LocateProtocol (&gEfiPciRootBridgeIoProtocolGuid, NULL, (VOID **)&PciIo);
  if (EFI_ERROR (Status)) {
    return Status;
  }

  // Read BAR5 of Cyan Skillfish GPU / PSP device (01:00.0)
  PciAddress = EFI_PCI_ADDRESS (PSP_PCI_BUS, PSP_PCI_DEV, PSP_PCI_FUNC, 0x24);
  PciIo->Pci.Read (PciIo, EfiPciWidthUint32, PciAddress, 1, &Bar5Lo);
  PciAddress = EFI_PCI_ADDRESS (PSP_PCI_BUS, PSP_PCI_DEV, PSP_PCI_FUNC, 0x28);
  PciIo->Pci.Read (PciIo, EfiPciWidthUint32, PciAddress, 1, &Bar5Hi);

  Bar5Base = ((EFI_PHYSICAL_ADDRESS)Bar5Hi << 32) | (Bar5Lo & ~0xF);
  if (Bar5Base == 0) {
    return EFI_NOT_FOUND;
  }

  // Allocate DMA buffers
  Status = gBS->AllocatePool (EfiBootServicesData, 0x200, (VOID **)&TokenBuffer);
  if (EFI_ERROR (Status)) return Status;
  ZeroMem (TokenBuffer, 0x200);

  Status = gBS->AllocatePool (EfiBootServicesData, sizeof(PSP_DYNAMIC_BLOB), (VOID **)&Blob);
  if (EFI_ERROR (Status)) return Status;
  ZeroMem (Blob, sizeof(PSP_DYNAMIC_BLOB));

  Status = gBS->AllocatePool (EfiBootServicesData, sizeof(PSP_BLOB_DESCRIPTOR), (VOID **)&Desc);
  if (EFI_ERROR (Status)) return Status;
  ZeroMem (Desc, sizeof(PSP_BLOB_DESCRIPTOR));

  Status = gBS->AllocatePool (EfiBootServicesData, 32, (VOID **)&HashBuffer);
  if (EFI_ERROR (Status)) return Status;

  // Step 1: Fetch session token
  Status = PspSendMailbox (Bar5Base, PSP_CMD_GET_TOKEN, (EFI_PHYSICAL_ADDRESS)(UINTN)TokenBuffer);
  if (EFI_ERROR (Status)) {
    return Status;
  }

  // Step 2: Build dynamic $PS1 blob
  Blob->Magic = 0x31535024; // '$PS1'
  Blob->TotalSize = sizeof(PSP_DYNAMIC_BLOB);
  Blob->Version = 1;
  CopyMem (Blob->SessionToken, TokenBuffer + 0x100, 32);

  // Group 0x201: VCN clock & SMN ungating
  Blob->Group201Id = 0x201;
  Blob->Group201Count = 6;
  Blob->Regs201[0]  = 0x0900C234; Blob->Regs201[1]  = 0x00000000;
  Blob->Regs201[2]  = 0x0900C914; Blob->Regs201[3]  = 0x00000000;
  Blob->Regs201[4]  = 0x0900C930; Blob->Regs201[5]  = 0x00000000;
  Blob->Regs201[6]  = 0x0900CB80; Blob->Regs201[7]  = 0x00000000;
  Blob->Regs201[8]  = 0x0900C234; Blob->Regs201[9]  = 0x00000001;
  Blob->Regs201[10] = 0x0322011C; Blob->Regs201[11] = 0x000107FF;

  // Group 0x210: Power mailbox
  Blob->Group210Id = 0x210;
  Blob->Group210Count = 2;
  Blob->Regs210[0]  = 0x0003E810; Blob->Regs210[1]  = 0x00000006;
  Blob->Regs210[2]  = 0x0003E814; Blob->Regs210[3]  = 0x2544C382;

  // Compute SHA256 of the blob
  Sha256HashAll ((CONST UINT8 *)Blob, sizeof(PSP_DYNAMIC_BLOB), HashBuffer);

  // Register blob descriptor
  Desc->PhysAddr = (UINT64)(UINTN)Blob;
  Desc->Size = sizeof(PSP_DYNAMIC_BLOB);
  Desc->ExpectedHashPtr = (UINT64)(UINTN)HashBuffer;
  Desc->Type = 0x45; // Policy type

  Status = PspSendMailbox (Bar5Base, PSP_CMD_LOAD_BLOB, (EFI_PHYSICAL_ADDRESS)(UINTN)Desc);
  if (EFI_ERROR (Status)) {
    return Status;
  }

  // Step 3: Trigger TOS sequencer
  Status = PspSendMailbox (Bar5Base, PSP_CMD_APPLY_VCN, 0);

  return Status;
}
