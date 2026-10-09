#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <dirent.h>
#include <fcntl.h>

#include <ps5/klog.h>
#include <ps5/kernel.h>

#include "defines.h"
#include "debug.h"

void decrypt_pups(const char *InputPath, const char *OutputPath);

static void escalate(void)
{
    pid_t pid = getpid();
    uint8_t caps[16];

    klog_printf("escalate: uid=%d authid=0x%llx\n",
                kernel_get_ucred_uid(pid),
                (unsigned long long)kernel_get_ucred_authid(pid));

    kernel_set_ucred_uid(pid, 0);
    kernel_set_ucred_ruid(pid, 0);
    kernel_set_ucred_svuid(pid, 0);
    kernel_set_ucred_rgid(pid, 0);
    kernel_set_ucred_svgid(pid, 0);
    kernel_set_ucred_authid(pid, 0x4800000000010003ULL);

    memset(caps, 0xFF, sizeof(caps));
    kernel_set_ucred_caps(pid, caps);

    {
        uint8_t attrs[32];

        if (kernel_get_ucred_attrs(pid, attrs) == 0) {
            attrs[3] |= 0x80; /* cr_sceAttr[0] root bit (p2jb/poops) */
            kernel_set_ucred_attrs(pid, attrs);
        }
    }

    /* P_SYSTEM on the process: classic gate for system devices. p_flag@0x28 */
    {
        intptr_t proc = kernel_get_proc(pid);
        uint64_t pflag = 0;

        if (proc != 0) {
            if (kernel_copyout(proc + 0x28, &pflag, 8) == 0) {
                uint64_t nf = pflag | 0x4000ULL; /* P_SYSTEM */

                kernel_copyin(&nf, proc + 0x28, 8);
                klog_printf("escalate: p_flag 0x%llx -> 0x%llx\n",
                            (unsigned long long)pflag,
                            (unsigned long long)nf);
            }
        }
    }

    /* direct kernel writes to the ucred (offset-verified from the dump) */
    {
        intptr_t ucred = kernel_get_proc_ucred(pid);
        uint32_t zero = 0;
        uint64_t ff = 0xFFFFFFFFFFFFFFFFULL;
        uint64_t authid = 0x4800000000010003ULL;
        uint8_t attrs[32];

        klog_printf("escalate: ucred=0x%llx\n", (unsigned long long)ucred);
        if (ucred != 0) {
            kernel_copyin(&zero, ucred + 0x04, 4);  /* cr_uid */
            kernel_copyin(&zero, ucred + 0x08, 4);  /* cr_ruid */
            kernel_copyin(&zero, ucred + 0x0C, 4);  /* cr_svuid */
            kernel_copyin(&zero, ucred + 0x14, 4);  /* cr_rgid */
            kernel_copyin(&zero, ucred + 0x18, 4);  /* cr_svgid */
            kernel_copyin(&ff, ucred + 0x60, 8);    /* caps */
            kernel_copyin(&ff, ucred + 0x68, 8);
            kernel_copyin(&authid, ucred + 0x58, 8);
            if (kernel_copyout(ucred + 0x80, attrs, sizeof(attrs)) == 0) {
                attrs[3] |= 0x80;
                kernel_copyin(attrs, ucred + 0x80, sizeof(attrs));
            }
        }
    }

    klog_printf("escalate: after uid=%d authid=0x%llx\n",
                kernel_get_ucred_uid(pid),
                (unsigned long long)kernel_get_ucred_authid(pid));
}

static int kread2(intptr_t a, void *b, size_t n);

/* Find SceUpdatePupUtil (NPXS40091) and copy its ucred privileges. */
static void copy_updater_cred(void)
{
    intptr_t proc, ucred, myucred;
    unsigned char big[0x600];
    pid_t me = getpid();

    if (kread2(KERNEL_ADDRESS_ALLPROC, &proc, 8) != 0)
        return;
    while (proc != 0) {
        if (kread2(proc, big, sizeof(big)) != 0)
            break;
        if (memcmp(big + 0x470, "NPXS40091", 9) == 0) {
            ucred = 0;
            memcpy(&ucred, big + 0x40, 8);
            myucred = kernel_get_proc_ucred(me);
            klog_printf("updater proc=%llx pid=%d ucred=%llx\n",
                        (unsigned long long)proc,
                        *(int *)(big + 0xBC), (unsigned long long)ucred);
            if (ucred != 0 && myucred != 0) {
                unsigned char cred[0xA0];

                if (kread2(ucred, cred, sizeof(cred)) == 0) {
                    /* authid + caps(32B) + attrs(32B) + uid/gid = 0 */
                    uint32_t zero = 0;
                    size_t i;

                    for (i = 0x04; i <= 0x18; i += 4)
                        kernel_copyin(&zero, myucred + i, 4);
                    kernel_copyin(cred + 0x58, myucred + 0x58, 8);
                    kernel_copyin(cred + 0x60, myucred + 0x60, 32);
                    kernel_copyin(cred + 0x80, myucred + 0x80, 32);
                    klog_printf("updater cred copied: authid=%llx caps=%llx %llx\n",
                                (unsigned long long)*(uint64_t *)(cred + 0x58),
                                (unsigned long long)*(uint64_t *)(cred + 0x60),
                                (unsigned long long)*(uint64_t *)(cred + 0x68));
                }
            }
            break;
        }
        memcpy(&proc, big, 8);
    }
}

static void list_dev(void)
{
    DIR *d = opendir("/dev");
    struct dirent *e;

    if (d == NULL) {
        klog_printf("opendir /dev failed errno=%d\n", errno);
        return;
    }
    while ((e = readdir(d)) != NULL) {
        if (strstr(e->d_name, "pup") || strstr(e->d_name, "upd") ||
            strstr(e->d_name, "smu") || strstr(e->d_name, "sm_")) {
            klog_printf("dev: %s\n", e->d_name);
        }
    }
    closedir(d);
}

static int kread2(intptr_t a, void *b, size_t n)
{
    unsigned char *p = b;
    size_t d = 0;

    while (d < n) {
        intptr_t pg = (a + d) & ~(intptr_t)0xFFF;
        unsigned char t[0x1000];
        size_t m = n - d;

        if (kernel_copyout(pg, t, sizeof(t)) != 0)
            return -1;
        if (m > sizeof(t))
            m = sizeof(t);
        memcpy(p + d, t + ((a + d) - pg), m);
        d += m;
    }
    return 0;
}

int main(void)
{
    int fd;

    klog_printf("PUP Decrypt started!\n");
    escalate();
    list_dev();
    copy_updater_cred();

    {
        uint8_t qa[16] = {0};

        kernel_get_qaflags(qa);
        klog_printf("QA_FLAGS: %02x%02x%02x%02x %02x%02x%02x%02x\n",
                    qa[0], qa[1], qa[2], qa[3], qa[4], qa[5], qa[6], qa[7]);
        klog_printf("SECURITY_FLAGS: 0x%02x TARGET_ID: 0x%02x UTOKEN: 0x%02x\n",
                    kernel_getchar(KERNEL_ADDRESS_SECURITY_FLAGS),
                    kernel_getchar(KERNEL_ADDRESS_TARGETID),
                    kernel_getchar(KERNEL_ADDRESS_UTOKEN_FLAGS));
    }

    fd = open("/dev/pup_update0", O_RDWR, 0);
    klog_printf("open /dev/pup_update0: fd=%d errno=%d (%s)\n", fd, errno,
                strerror(errno));
    if (fd >= 0)
        close(fd);

    fd = open("/dev/sc_fw_update0", O_RDWR, 0);
    klog_printf("open /dev/sc_fw_update0: fd=%d errno=%d (%s)\n", fd, errno,
                strerror(errno));
    if (fd >= 0)
        close(fd);

    decrypt_pups(INPUTPATH, OUTPUTPATH);
    klog_printf("PUP Decrypt complete!\n");
    return 0;
}
