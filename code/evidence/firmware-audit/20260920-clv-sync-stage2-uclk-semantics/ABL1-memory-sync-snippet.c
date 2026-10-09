  int local_34;
  int local_30;
  int local_2c;
  
  iVar6 = *param_1;
  uVar7 = 0;
  thunk_FUN_00006c7e(local_60,0,0x20,iVar6);
  FUN_0000140c(4,0,s_AGESA_MEM___Multi_Die___DRAM_Spe_000099ac);
  FUN_0000140c(4,0,s_Synchronize_Mem_Speed_for_each_c_000099d8);
  FUN_00006d20(auStack_40);
  thunk_FUN_00006c7e(iVar6 + 0x278,0xff,0x40,iVar6);
  if (local_3c < 2) {
    FUN_0000140c(4,0,DAT_00009b0c);
    for (; uVar7 < *(byte *)(*(int *)(iVar6 + 0x3c4) + 0x74); uVar7 = uVar7 + 1 & 0xff) {
      iVar3 = uVar7 * 0x170 + 0x20;
      uVar8 = (uint)*(ushort *)(*(int *)(*(int *)(iVar6 + 0x3c4) + 0x70) + iVar3);
      *(uint *)(iVar6 + local_34 * 0x40 + local_30 * 0x40 + uVar7 * 4 + 0x278) = uVar8;
      FUN_0000140c(4,0,s_Channel__d_Memory_Speed____d_00009b10,uVar7,uVar8);
      *(uint *)(iVar6 + 700) = (uint)*(ushort *)(*(int *)(*(int *)(iVar6 + 0x3c4) + 0x70) + iVar3);
    }
  }
  else {
    if (local_2c == 0) {
      sVar10 = *(byte *)(*(int *)(iVar6 + 0x3c4) + 0x74) + 1;
      local_60[0] = CONCAT22(sVar10,CONCAT11((char)local_30,(char)local_34));
      for (; uVar7 < *(byte *)(*(int *)(iVar6 + 0x3c4) + 0x74); uVar7 = uVar7 + 1 & 0xff) {
        (*(code *)param_1[0x14b])(param_1,uVar7);
        local_60[uVar7 + 1] = (uint)*(ushort *)(param_1[3] + 0x20);
      }
      iVar3 = FUN_0000128c(iVar6,0,local_60,sVar10,1);
      if (iVar3 == 9) {
        FUN_000065c8(DAT_00009ad8 + 0x24);
      }
      iVar3 = FUN_000011c0(iVar6,0,0x1000000,local_60,1);
      if (iVar3 == 9) {
        FUN_0000140c(0,0x40000000,s__ERROR___Slave__ABL__Error_ASSER_00009adc);
        FUN_000065c8(DAT_00009ad8 + 0x33);
      }
      *(uint *)(iVar6 + 700) = local_60[0];
      *(undefined *)(iVar6 + 0x2c0) = 1;
      for (bVar9 = 0; bVar9 < *(byte *)((int)param_1 + 0x4b); bVar9 = bVar9 + 1) {
        (*(code *)param_1[0x14b])(param_1,bVar9);
        *(short *)(param_1[3] + 0x20) = (short)local_60[0];
      }
      return 0;
    }
    FUN_0000140c(4,0,s_Running_on_System_Master__Retrei_00009a14);
    for (; uVar7 < *(byte *)((int)param_1 + 0x4b); uVar7 = uVar7 + 1 & 0xff) {
      (*(code *)param_1[0x14b])(param_1,uVar7);
      uVar1 = *(ushort *)(param_1[3] + 0x20);
      *(uint *)(iVar6 + uVar7 * 4 + 0x278) = (uint)uVar1;
      FUN_0000140c(4,0,s_Master_Channel__d_Memory_Speed___00009a50,uVar7,(uint)uVar1);
    }
    FUN_00001050(iVar6,&local_198);
    for (uVar7 = 1; uVar7 < local_3c; uVar7 = uVar7 + 1 & 0xff) {
      local_60[0] = auStack_17c[uVar7 * 7];
      local_60[1] = auStack_17c[uVar7 * 7 + 1];
      for (uVar8 = 0; uVar8 < *(byte *)(*(int *)(iVar6 + 0x3c4) + 0x74); uVar8 = uVar8 + 1 & 0xff) {
        FUN_0000140c(4,0,s_Slave__d_Channel__d_Memory_Speed_00009a78,uVar7,uVar8,local_60[uVar8]);
        uVar11 = FUN_000002f4(uVar7,local_38);
        uVar4 = local_60[uVar8];
        if (uVar4 == 0) {
          uVar4 = 0x7d1;
        }
        *(uint *)(iVar6 + (int)uVar11 * 0x40 + (int)((ulonglong)uVar11 >> 0x20) * 0x40 + uVar8 * 4 +
                 0x278) = uVar4;
      }
    }
    uVar7 = 0;
    uVar8 = 0x7d1;
    do {
      uVar4 = 0;
      do {
        uVar2 = 0;
        do {
          uVar5 = *(uint *)(iVar6 + uVar7 * 0x40 + uVar4 * 0x40 + uVar2 * 4 + 0x278);
          if (uVar5 < uVar8) {
            uVar8 = uVar5 & 0xffff;
          }
          uVar2 = uVar2 + 1 & 0xff;
        } while (uVar2 < 0x10);
        uVar4 = uVar4 + 1 & 0xffff;
      } while (uVar4 == 0);
      uVar7 = uVar7 + 1 & 0xffff;
    } while (uVar7 == 0);
    *(uint *)(iVar6 + 700) = uVar8;
    for (bVar9 = 0; bVar9 < *(byte *)((int)param_1 + 0x4b); bVar9 = bVar9 + 1) {
      (*(code *)param_1[0x14b])(param_1,bVar9);
      *(short *)(param_1[3] + 0x20) = (short)uVar8;
    }
    FUN_0000140c(4,0,s_Sending_Synchronized_Speed_back_t_00009aa4,*(undefined2 *)(param_1[3] + 0x20)
                );
    local_198 = 0;
    uStack_194 = 0x1000000;
    local_a0 = 1;
    local_180 = uVar8;
    iVar3 = FUN_00000ed4(iVar6,&local_198);
    if (iVar3 == 9) {
      FUN_000065c8(DAT_00009ad8);
    }
  }
  *(undefined *)(iVar6 + 0x2c0) = 1;
  return 0;
}



/* FUN_00009b30 @ 00009b30 */

undefined4 FUN_00009b30(int param_1,undefined4 param_2,int param_3)

