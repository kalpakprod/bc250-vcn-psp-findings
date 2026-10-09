/*
 * A1.5 EXPLOIT: full SEC_GASKET replay (1461 writes) via x86 NBIO SMN port.
 * Transport: BAR5 + 0x38 (index) / 0x3C (data) — the x86/NBIO SMN master,
 * NOT the SMU (Q3 0x98). Tests VULN-1b 'owner' hypothesis: the DF firewall
 * may only honor gasket writes from the boot-master (x86 NBIO / PSP path).
 * Run as root on the probe kernel. Reversible: power-cycle.
 * Build: gcc -O2 -o a15_gasket_nbio a15_gasket_nbio.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <stdint.h>
#include <unistd.h>

static volatile uint32_t *bar5;
static uint64_t bar5_phys;

/* A1.5: writes via NBIO SMN port */
static void nbio_smn_write(uint32_t addr, uint32_t val) {
    bar5[0x38/4] = addr;
    bar5[0x3C/4] = val;
}
static uint32_t nbio_smn_read(uint32_t addr) {
    bar5[0x38/4] = addr;
    return bar5[0x3C/4];
}

/* VCN MMIO probes: offset within VCN BAR (from A1 script MMIO_PROBES) */
struct probe { const char *name; uint32_t off; int seg; };
static const struct probe probes[] = {
    {"UVD_PGFSM_CONFIG", 0x0000, 1},
    {"UVD_PGFSM_STATUS", 0x0001, 1},
    {"UVD_POWER_STATUS", 0x0004, 1},
    {"UVD_JPEG_POWER_STATUS", 0x000A, 1},
    {"UVD_MASTINT_EN", 0x0200, 1},
    {"UVD_STATUS", 0x026F, 1},
    {"UVD_VERSION", 0x05C9, 1},
    {"UVD_NO_OP", 0x05BF, 1},
    {"UVD_JPEG_CNTL", 0x0080, 0},
    {"UVD_JRBC_STATUS", 0x0109, 0},
};
/* VCN BAR segments: SEG1 = VCN1? offsets in DW. Use amdgpu vcn bar mapping:
 * we map the whole 512KB BAR5 region and use the same DW offsets as the
 * python VcnDirect (VCN_SEG1_DW / VCN_SEG0_DW base + offset). */

int main(int argc, char **argv) {
    /* 1. find BAR5 phys: /sys/bus/pci/devices/0000:01:00.0/resource1 (BAR5=resource idx 5? for this chip resource0=BAR0... use resource5) */
    char path[256];
    snprintf(path, sizeof path, "/sys/bus/pci/devices/0000:01:00.0/resource5");
    FILE *f = fopen(path, "r");
    if (!f) { printf("no %s\n", path); return 1; }
    uint64_t start, end; int flags;
    if (fscanf(f, "%llx-%llx %x", &start, &end, &flags) != 3) { printf("parse fail\n"); return 1; }
    fclose(f);
    bar5_phys = start;
    printf("BAR5 phys: %llx-%llx\n", (unsigned long long)start, (unsigned long long)end);
    int mm = open("/dev/mem", O_RDWR);
    bar5 = mmap(NULL, 0x100000, PROT_READ|PROT_WRITE, MAP_SHARED, mm, start & ~(uint64_t)0xfff);
    if (bar5 == MAP_FAILED) { perror("mmap"); return 1; }

    printf("SMN port test: read 0x03B10A68 (SMU ctrl) = %08x\n", nbio_smn_read(0x03B10A68));

    /* 2. the 1461 writes — loaded from JSON sidecar (full_gasket_replay_1461.json) */
    FILE *j = fopen("full_gasket_replay_1461.json", "r");
    if (!j) { printf("need full_gasket_replay_1461.json in cwd\n"); return 1; }
    char *buf = malloc(1<<20);
    size_t n = fread(buf, 1, 1<<20, j); fclose(j);
    /* naive parse: triples [grp, addr, val] */
    int total = 0;
    char *p = buf;
    uint32_t addrs[2000], vals[2000];
    while (total < 2000 && (p = strchr(p, '[')) != NULL) {
        /* [grp, 0xADDR, 0xVAL] */
        p++;
        int grp = (int)strtol(p, &p, 0);
        if (*p == ',') p++;
        uint32_t a = (uint32_t)strtol(p, &p, 0);
        if (*p == ',') p++;
        uint32_t v = (uint32_t)strtol(p, &p, 0);
        if (a > 0x10000000) { addrs[total] = a; vals[total] = v; total++; }
        if (*p == ']') p++;
    }
    printf("parsed %d writes; executing via NBIO...\n", total);
    for (int i = 0; i < total; i++) {
        nbio_smn_write(addrs[i], vals[i]);
        if (i % 200 == 199) printf("  [%d/%d]\n", i, total);
    }
    printf("all %d writes done. SMN readback:\n", total);
    uint32_t k[8] = {0x0900C234, 0x0900CB80, 0x0900C910, 0x0900C914, 0x09023234, 0x09300234, 0x0003E810, 0x0003E814};
    for (int i = 0; i < 8; i++)
        printf("  %08x = %08x\n", k[i], nbio_smn_read(k[i]));
    /* 3. MMIO probe (VCN BAR = BAR5 + 0x? — use same base as python: VCN_SEG0/1 DW bases from enable_vcn; here use raw BAR5 + offsets from /sys amdgpu vcn bar if present) */
    printf("MMIO probes (BAR5+DW):\n");
    for (int i = 0; i < (int)sizeof probes / sizeof probes[0]; i++) {
        uint32_t v = bar5[probes[i].off]; /* rough: DW index */
        printf("  %-20s = %08x %s\n", probes[i].name, v, v != 0xFFFFFFFF ? "<== ALIVE" : "");
    }
    return 0;
}
