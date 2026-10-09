#ifndef BC250_SPARSE_READER_H
#define BC250_SPARSE_READER_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Read-only view of an image_pack.py container mapped in RP2350 XIP.
 * Caller owns its lifetime and must pin its source hash before provisioning.
 * Format validation here is not cryptographic integrity verification. */
typedef struct {
    const uint8_t *map;
    const uint8_t *payload;
    uint32_t page_size;
    uint32_t image_size;
    uint32_t page_count;
    uint32_t payload_pages;
    bool ready;
} bc250_sparse_reader_t;

bool bc250_sparse_open(bc250_sparse_reader_t *reader, const uint8_t *data,
                       size_t size);
bool bc250_sparse_read(const bc250_sparse_reader_t *reader, uint32_t address,
                       uint8_t *out, size_t size);
#endif
