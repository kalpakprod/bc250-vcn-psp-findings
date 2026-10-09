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
 mov savedbuffer,%esi
 mov $acquired,%edi
 mov $0x8b5,%ecx
 rep movsb
 push $invsize
 push $invbuffer
 push $acquired
 mov $0x09ebd77c,%eax
 call *%eax
 add $12,%esp
 movzbl %al,%eax
 mov %eax,result
 mov invsize,%eax
 mov %eax,result+4
 push $invsize
 push $invbuffer
 push $acquired
 mov $0x09ebd77c,%eax
 call *%eax
 add $12,%esp
 movzbl %al,%eax
 mov %eax,result+8
 mov invbuffer,%eax
 mov %eax,result+12
 mov invbuffer+4,%eax
 mov %eax,result+16
 mov $invbuffer+32,%esi
 xor %ebp,%ebp
scan:
 cmp $invbuffer+8190,%esi
 jae fail
 movzwl (%esi),%ebx
 cmp $65535,%ebx
 je scanned
 inc %ebp
 cmp $2048,%ebp
 ja fail
 movzbl 2(%esi),%ecx
 and $3,%ecx
 mov $1,%edx
 shl %cl,%edx
 xor %edi,%edi
find:
 cmp $7,%edi
 je next
 cmp tokens(,%edi,4),%ebx
 je capture
 inc %edi
 jmp find
capture:
 cmp widths(,%edi,4),%edx
 jne fail
 bts %edi,seen
 jc fail
 mov 3(%esi),%eax
 cmp $1,%edx
 jne word
 and $255,%eax
 jmp store
word:
 cmp $2,%edx
 jne store
 and $65535,%eax
store:
 mov %eax,result+24(,%edi,4)
next:
 lea 3(%esi,%edx),%esi
 jmp scan
scanned:
 mov %ebp,result+52
 mov seen,%eax
 mov %eax,result+56
 lea 2(%esi),%eax
 sub $invbuffer,%eax
 mov %eax,result+60
 mov $4,%eax
 mov $1,%ebx
 mov $result,%ecx
 mov $64,%edx
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
result: .space 64
seen: .long 0
widths: .long 1,1,1,1,4,1,2
invsize: .long 0
tokens: .long 0x11ed,0x1204,0x1331,0x1363,0x1364,0x1373,0x1374
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
acquired: .space 0x8b5
.align 16
invbuffer: .space 8192
.section .nvram,"ax"
.incbin "evidence/firmware-audit/20260919-inv-token-consumers/NvramPei-cbc1def3ce53.bin"
.section .cbs,"ax"
.incbin "evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin"
.section .note.GNU-stack,"",@progbits
