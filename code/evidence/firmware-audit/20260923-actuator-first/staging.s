.section .text
.global _start
_start:
 mov $payload,%edi
 push $0x21
 mov $0x09ed31c9,%eax
 call *%eax
 mov $90,%ebx
 jmp terminate
capture:
 mov count,%eax
 cmp $6,%eax
 jae bad
 lea trace(,%eax,8),%edx
 mov 4(%esp),%ecx
 mov %ecx,(%edx)
 mov 8(%esp),%ecx
 mov %ecx,4(%edx)
 incl count
 xor %eax,%eax
 ret
finish:
 cmpl $6,count
 jne bad
 mov $4,%eax
 mov $1,%ebx
 mov $trace,%ecx
 mov $48,%edx
 int $0x80
 xor %ebx,%ebx
terminate:
 mov $1,%eax
 int $0x80
bad:
 mov $99,%ebx
 jmp terminate
.section .data
payload: .long VALUE
count: .long 0
trace: .space 48
.section .instrumented,"ax"
.incbin "evidence/firmware-audit/20260919-inv-token-consumers/ISL69247-3e1f753a6279.bin",0,0x3cd
 jmp capture
.incbin "evidence/firmware-audit/20260919-inv-token-consumers/ISL69247-3e1f753a6279.bin",0x3d2,0x1c9
 jmp finish
.incbin "evidence/firmware-audit/20260919-inv-token-consumers/ISL69247-3e1f753a6279.bin",0x5a0
.section .note.GNU-stack,"",@progbits
