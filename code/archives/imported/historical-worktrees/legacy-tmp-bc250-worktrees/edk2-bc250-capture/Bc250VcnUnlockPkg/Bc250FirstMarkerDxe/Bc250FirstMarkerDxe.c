/** @file
  Presence-only first-operation marker for BC-250 DXE dispatch validation.
  SPDX-License-Identifier: MIT
**/
#include <Uefi.h>
#include <Library/UefiBootServicesTableLib.h>
#include <Library/UefiDriverEntryPoint.h>
STATIC UINT32 mMarkerValue = 0x574D3442U;
STATIC CONST EFI_GUID mFirstMarkerGuid = { 0x0b2f8841, 0x8ca8, 0x42c6, { 0x91, 0x75, 0x79, 0xe1, 0x3f, 0x04, 0x57, 0x41 } };
EFI_STATUS EFIAPI Bc250FirstMarkerDxeEntryPoint(IN EFI_HANDLE ImageHandle,IN EFI_SYSTEM_TABLE *SystemTable){(VOID)ImageHandle;(VOID)SystemTable;return gBS->InstallConfigurationTable((EFI_GUID *)&mFirstMarkerGuid,&mMarkerValue);}
