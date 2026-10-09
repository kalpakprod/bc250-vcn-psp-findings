.section .text
.global _start
_start:
 mov $5,%eax
 mov $source,%ebx
 xor %ecx,%ecx
 int $0x80
 test %eax,%eax
 js fail
 mov %eax,%ebx
 mov $3,%eax
 mov $rom,%ecx
 mov $0x20000,%edx
 int $0x80
 cmp $0x20000,%eax
 jne fail
 push $0x13579bdf
 push $0
 push $servicesptr
 mov $0x09eba2dc,%eax
 call *%eax
 add $12,%esp
 mov savedbuffer,%edx
 movzbl 0x316(%edx),%eax
 mov %eax,result
 movzbl 0x317(%edx),%eax
 mov %eax,result+4
 movzbl 0x330(%edx),%eax
 mov %eax,result+8
 movzwl 0x704(%edx),%eax
 mov %eax,result+12
 mov calls,%eax
 mov %eax,result+16
 mov $4,%eax
 mov $1,%ebx
 mov $result,%ecx
 mov $20,%edx
 int $0x80
 mov $1,%eax
 xor %ebx,%ebx
 int $0x80
fail:
 mov $1,%eax
 mov $99,%ebx
 int $0x80
fill:
 push %edi
 mov 8(%esp),%edi
 mov %edi,savedbuffer
 mov 12(%esp),%ecx
 mov 16(%esp),%eax
 rep stosb
 pop %edi
 xor %eax,%eax
 ret
locate:
 mov 20(%esp),%eax
 movl $ppi,(%eax)
 xor %eax,%eax
 ret
getvar:
 push %ebp
 mov %esp,%ebp
 incl calls
 cmpl $1,mode
 je missing
 cmpl $2,mode
 jne second
 mov 24(%ebp),%eax
 movl $0x8b4,(%eax)
 mov $0x80000005,%eax
 leave
 ret
second:
 cmpl $3,mode
 jne normal
 cmpl $2,calls
 je missing
normal:
 mov 24(%ebp),%eax
 push $live
 push 28(%ebp)
 push 20(%ebp)
 push 16(%ebp)
 push 12(%ebp)
 mov $0x09ed81cc,%edx
 call *%edx
 add $20,%esp
 leave
 ret
missing:
 mov $0x8000000e,%eax
 leave
 ret
.section .rodata
source: .asciz "/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260923-chat-case/nvar/oc_profiles_03.bin"
.section .data
.align 4
mode: .long MODE
calls: .long 0
savedbuffer: .long 0
result: .space 20
servicesptr: .long services
services:
 .space 0x20
 .long locate
 .space 0x30
 .long fill
ppi: .long getvar
live: .long rom,0x20000,rom+0x1fff0,rom+0x20000,rom+0x90,0,0,1,0,0
.section .bss
.align 4096
rom: .space 0x20000
.section .nvram,"ax"
.incbin "evidence/firmware-audit/20260919-inv-token-consumers/NvramPei-cbc1def3ce53.bin"
.section .cbs,"ax"
.incbin "evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin"
.section .note.GNU-stack,"",@progbits
