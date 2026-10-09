# Caller coverage matrix

All addresses hexadecimal, module RVA. GUID raw offsets shown. Indirect edge counts are retained UNRESOLVED module-wide, not asserted reader callers.

| Module | Type | GUID raw | NVTB raw | Reader / direct callers : token | Indirect edges | Classification |
|---|---|---|---|---|---:|---|
| AmdCcxVhAriDxe | PE32 | 7D90 | 5AEA | 5AC4 / 5CA5:1000, 5CF1:1001 | 133 | confirmed INV reader |
| AmdIdsDebugPrintDxe | PE32 | 25B0 | — | none identified | 10 | heap-library marker only; no literal NVTB/INV parser |
| AmdFabricAriDxe | PE32 | 58C0 | — | none identified | 49 | heap-library marker only; no literal NVTB/INV parser |
| FchDxe | PE32 | ADD0 | — | none identified | 75 | heap-library marker only; no literal NVTB/INV parser |
| AmdMemSmbiosV2Dxe | PE32 | CD0 | — | none identified | 7 | heap-library marker only; no literal NVTB/INV parser |
| AmdNbioGfxARIDxe | PE32 | 28B0 | — | none identified | 91 | heap-library marker only; no literal NVTB/INV parser |
| AmdNbioIOMMUARIDxe | PE32 | 4310 | — | none identified | 66 | heap-library marker only; no literal NVTB/INV parser |
| AmdNbioAlibARIDxe | PE32 | 11B0 | — | none identified | 25 | heap-library marker only; no literal NVTB/INV parser |
| AmdNbioPcieARIDxe | PE32 | 6BA0 | — | none identified | 49 | heap-library marker only; no literal NVTB/INV parser |
| AmdNbioSmuV10Dxe | PE32 | 5BC0 | — | none identified | 101 | heap-library marker only; no literal NVTB/INV parser |
| AmdPspDxeV2 | PE32 | 2750 | — | none identified | 51 | heap-library marker only; no literal NVTB/INV parser |
| AmdApcbObrDxe | PE32 | 3450 | — | none identified | 49 | heap-library marker only; no literal NVTB/INV parser |
| AmdSocBl5AriDxe | PE32 | 1D00 | — | none identified | 25 | heap-library marker only; no literal NVTB/INV parser |
| AmdAcpiDxe | PE32 | 32D0 | — | none identified | 71 | heap-library marker only; no literal NVTB/INV parser |
| AmdSmbiosDxe | PE32 | 30F0 | — | none identified | 34 | heap-library marker only; no literal NVTB/INV parser |
| AmiApcbLibInterface | PE32 | 19D0 | — | none identified | 32 | heap-library marker only; no literal NVTB/INV parser |
| CbsSetupDxe | PE32 | B1C0 | — | none identified | 76 | heap-library marker only; no literal NVTB/INV parser |
| PspDxe | PE32 | 1E90 | — | none identified | 52 | heap-library marker only; no literal NVTB/INV parser |
| PspResource | PE32 | 1B50 | — | none identified | 45 | heap-library marker only; no literal NVTB/INV parser |
| AmdCcxVhAriSmm | PE32 | 2ED0 | — | none identified | 26 | heap-library marker only; no literal NVTB/INV parser |
| FchSmmInit | PE32 | A748 | — | none identified | 64 | heap-library marker only; no literal NVTB/INV parser |
| FchSmmDispatcher | PE32 | 51F0 | — | none identified | 81 | heap-library marker only; no literal NVTB/INV parser |
| Usb3PortProtectWA | PE32 | 2310 | — | none identified | 22 | heap-library marker only; no literal NVTB/INV parser |
| CardinalSystemHubSmmInit | PE32 | 3230 | — | none identified | 48 | heap-library marker only; no literal NVTB/INV parser |
| AmdPspP2CmboxV2 | PE32 | 44F0 | — | none identified | 54 | heap-library marker only; no literal NVTB/INV parser |
| AmdPspSmmV2 | PE32 | 4480 | — | none identified | 57 | heap-library marker only; no literal NVTB/INV parser |
| AmdApcbObrSmm | PE32 | 4FE0 | — | none identified | 57 | heap-library marker only; no literal NVTB/INV parser |
| AmdSmmCommunication | PE32 | 2C80 | — | none identified | 28 | heap-library marker only; no literal NVTB/INV parser |
| BctBaseSmm | PE32 | 7E20 | — | none identified | 43 | heap-library marker only; no literal NVTB/INV parser |
| PspS3Smm | PE32 | 3470 | — | none identified | 54 | heap-library marker only; no literal NVTB/INV parser |
| AmdCcxVhAriPei | TE | 37A0 | — | none identified | 44 | heap-library marker only; no literal NVTB/INV parser |
| AmdIdsDebugPrintPei | TE | 1B90 | — | none identified | 7 | heap-library marker only; no literal NVTB/INV parser |
| AmdFabricAriPei | TE | 16A08 | 1BB6 | 1D3C / 1EBD:10FF, 1F94:1104 | 31 | confirmed INV reader |
| FchPei | TE | 60F8 | — | none identified | 32 | heap-library marker only; no literal NVTB/INV parser |
| AmdMemSmbiosV2Pei | TE | 1330 | — | none identified | 6 | heap-library marker only; no literal NVTB/INV parser |
| AmdNbioGfxARIPei | TE | 14E78 | — | none identified | 29 | heap library plus INV serializer; no literal NVTB/INV reader |
| AmdNbioIOMMUARIPei | TE | 1990 | — | none identified | 6 | heap-library marker only; no literal NVTB/INV parser |
| AmdNbioBaseARIPei | TE | 17890 | — | none identified | 65 | heap library plus INV serializer; no literal NVTB/INV reader |
| AmdNbioPcieARIPei | TE | 185B8 | — | none identified | 112 | heap library plus INV serializer; no literal NVTB/INV reader |
| AmdNbioSmuV10Pei | TE | 15840 | — | none identified | 37 | heap library plus INV serializer; no literal NVTB/INV reader |
| AmdPspPeiV2 | TE | 2450 | — | none identified | 11 | heap-library marker only; no literal NVTB/INV parser |
| AmdSocBl5AriPei | TE | 15358 | — | none identified | 51 | heap library plus INV serializer; no literal NVTB/INV reader |
