4347-
4348-
4349-
4350:/* FUN_000096fc @ 000096fc */
4351-
4352:undefined4 FUN_000096fc(int *param_1)
4353-
4354-{
4355-  ushort uVar1;
4356-  uint uVar2;
4357-  int iVar3;
4358-  uint uVar4;
4359-  uint uVar5;
4360-  int iVar6;
4361-  uint uVar7;
4362-  uint uVar8;
4363-  byte bVar9;
4364-  short sVar10;
4365-  undefined8 uVar11;
4366-  undefined4 local_198;
4367-  undefined4 uStack_194;
4368-  uint local_180;
4369-  uint auStack_17c [55];
4370-  undefined4 local_a0;
4371-  uint local_60 [8];
4372-  undefined auStack_40 [4];
4373-  uint local_3c;
4374-  undefined4 local_38;
4375-  int local_34;
4376-  int local_30;
4377-  int local_2c;
4378-  
4379-  iVar6 = *param_1;
4380-  uVar7 = 0;
4381-  thunk_FUN_00006c7e(local_60,0,0x20,iVar6);
4382-  FUN_0000140c(4,0,s_AGESA_MEM___Multi_Die___DRAM_Spe_000099ac);
4383-  FUN_0000140c(4,0,s_Synchronize_Mem_Speed_for_each_c_000099d8);
4384-  FUN_00006d20(auStack_40);
4385-  thunk_FUN_00006c7e(iVar6 + 0x278,0xff,0x40,iVar6);
4386-  if (local_3c < 2) {
4387-    FUN_0000140c(4,0,DAT_00009b0c);
4388-    for (; uVar7 < *(byte *)(*(int *)(iVar6 + 0x3c4) + 0x74); uVar7 = uVar7 + 1 & 0xff) {
4389-      iVar3 = uVar7 * 0x170 + 0x20;
4390-      uVar8 = (uint)*(ushort *)(*(int *)(*(int *)(iVar6 + 0x3c4) + 0x70) + iVar3);
4391-      *(uint *)(iVar6 + local_34 * 0x40 + local_30 * 0x40 + uVar7 * 4 + 0x278) = uVar8;
4392-      FUN_0000140c(4,0,s_Channel__d_Memory_Speed____d_00009b10,uVar7,uVar8);
4393-      *(uint *)(iVar6 + 700) = (uint)*(ushort *)(*(int *)(*(int *)(iVar6 + 0x3c4) + 0x70) + iVar3);
4394-    }
4395-  }
4396-  else {
4397-    if (local_2c == 0) {
4398-      sVar10 = *(byte *)(*(int *)(iVar6 + 0x3c4) + 0x74) + 1;
4399-      local_60[0] = CONCAT22(sVar10,CONCAT11((char)local_30,(char)local_34));
4400-      for (; uVar7 < *(byte *)(*(int *)(iVar6 + 0x3c4) + 0x74); uVar7 = uVar7 + 1 & 0xff) {
4401-        (*(code *)param_1[0x14b])(param_1,uVar7);
4402-        local_60[uVar7 + 1] = (uint)*(ushort *)(param_1[3] + 0x20);
4403-      }
4404-      iVar3 = FUN_0000128c(iVar6,0,local_60,sVar10,1);
4405-      if (iVar3 == 9) {
4406-        FUN_000065c8(DAT_00009ad8 + 0x24);
4407-      }
4408-      iVar3 = FUN_000011c0(iVar6,0,0x1000000,local_60,1);
4409-      if (iVar3 == 9) {
4410-        FUN_0000140c(0,0x40000000,s__ERROR___Slave__ABL__Error_ASSER_00009adc);
4411-        FUN_000065c8(DAT_00009ad8 + 0x33);
4412-      }
4413-      *(uint *)(iVar6 + 700) = local_60[0];
4414-      *(undefined *)(iVar6 + 0x2c0) = 1;
4415-      for (bVar9 = 0; bVar9 < *(byte *)((int)param_1 + 0x4b); bVar9 = bVar9 + 1) {
4416-        (*(code *)param_1[0x14b])(param_1,bVar9);
4417-        *(short *)(param_1[3] + 0x20) = (short)local_60[0];
4418-      }
4419-      return 0;
4420-    }
4421-    FUN_0000140c(4,0,s_Running_on_System_Master__Retrei_00009a14);
4422-    for (; uVar7 < *(byte *)((int)param_1 + 0x4b); uVar7 = uVar7 + 1 & 0xff) {
4423-      (*(code *)param_1[0x14b])(param_1,uVar7);
4424-      uVar1 = *(ushort *)(param_1[3] + 0x20);
4425-      *(uint *)(iVar6 + uVar7 * 4 + 0x278) = (uint)uVar1;
4426-      FUN_0000140c(4,0,s_Master_Channel__d_Memory_Speed___00009a50,uVar7,(uint)uVar1);
4427-    }
4428-    FUN_00001050(iVar6,&local_198);
4429-    for (uVar7 = 1; uVar7 < local_3c; uVar7 = uVar7 + 1 & 0xff) {
4430-      local_60[0] = auStack_17c[uVar7 * 7];
4431-      local_60[1] = auStack_17c[uVar7 * 7 + 1];
4432-      for (uVar8 = 0; uVar8 < *(byte *)(*(int *)(iVar6 + 0x3c4) + 0x74); uVar8 = uVar8 + 1 & 0xff) {
4433-        FUN_0000140c(4,0,s_Slave__d_Channel__d_Memory_Speed_00009a78,uVar7,uVar8,local_60[uVar8]);
4434-        uVar11 = FUN_000002f4(uVar7,local_38);
4435-        uVar4 = local_60[uVar8];
4436-        if (uVar4 == 0) {
4437-          uVar4 = 0x7d1;
4438-        }
4439-        *(uint *)(iVar6 + (int)uVar11 * 0x40 + (int)((ulonglong)uVar11 >> 0x20) * 0x40 + uVar8 * 4 +
4440-                 0x278) = uVar4;
4441-      }
4442-    }
4443-    uVar7 = 0;
4444-    uVar8 = 0x7d1;
4445-    do {
4446-      uVar4 = 0;
4447-      do {
4448-        uVar2 = 0;
4449-        do {
4450-          uVar5 = *(uint *)(iVar6 + uVar7 * 0x40 + uVar4 * 0x40 + uVar2 * 4 + 0x278);
4451-          if (uVar5 < uVar8) {
4452-            uVar8 = uVar5 & 0xffff;
4453-          }
4454-          uVar2 = uVar2 + 1 & 0xff;
4455-        } while (uVar2 < 0x10);
4456-        uVar4 = uVar4 + 1 & 0xffff;
4457-      } while (uVar4 == 0);
4458-      uVar7 = uVar7 + 1 & 0xffff;
4459-    } while (uVar7 == 0);
4460-    *(uint *)(iVar6 + 700) = uVar8;
4461-    for (bVar9 = 0; bVar9 < *(byte *)((int)param_1 + 0x4b); bVar9 = bVar9 + 1) {
4462-      (*(code *)param_1[0x14b])(param_1,bVar9);
4463-      *(short *)(param_1[3] + 0x20) = (short)uVar8;
4464-    }
4465-    FUN_0000140c(4,0,s_Sending_Synchronized_Speed_back_t_00009aa4,*(undefined2 *)(param_1[3] + 0x20)
4466-                );
4467-    local_198 = 0;
4468-    uStack_194 = 0x1000000;
4469-    local_a0 = 1;
4470-    local_180 = uVar8;
4471-    iVar3 = FUN_00000ed4(iVar6,&local_198);
4472-    if (iVar3 == 9) {
4473-      FUN_000065c8(DAT_00009ad8);
4474-    }
4475-  }
4476-  *(undefined *)(iVar6 + 0x2c0) = 1;
4477-  return 0;
4478-}
4479-
4480-
4481-
4482-/* FUN_00009b30 @ 00009b30 */
4483-
4484-undefined4 FUN_00009b30(int param_1,undefined4 param_2,int param_3)
4485-
4486-{
4487-  undefined uVar1;
4488-  int iVar2;
4489-  byte bVar3;
4490-  
4491-  uVar1 = *(undefined *)(param_1 + 0x49);
4492-  bVar3 = 0;
4493-  while( true ) {
4494-    if (*(byte *)(param_1 + 0x4b) <= bVar3) {
4495-      func_0x00010abc(param_1,uVar1);
4496-      return 1;
4497-    }
