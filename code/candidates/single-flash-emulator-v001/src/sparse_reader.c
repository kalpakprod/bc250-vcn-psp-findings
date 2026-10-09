#include "sparse_reader.h"
#include <string.h>

#define HEADER_SIZE 64u
#define MAGIC "B250SPM1"
#define ERASED_PAGE 0xffffffffu

static uint16_t le16(const uint8_t *p) { return (uint16_t)p[0] | ((uint16_t)p[1] << 8); }
static uint32_t le32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

bool bc250_sparse_open(bc250_sparse_reader_t *reader, const uint8_t *data,
                       size_t size) {
    if (!reader) return false;
    memset(reader, 0, sizeof(*reader));
    if (!data || size < HEADER_SIZE || memcmp(data, MAGIC, 8) != 0)
        return false;
    const uint16_t version = le16(data + 8);
    const uint16_t page_size = le16(data + 10);
    const uint32_t image_size = le32(data + 12);
    const uint32_t page_count = le32(data + 16);
    const uint32_t payload_pages = le32(data + 20);
    const uint32_t payload_size = le32(data + 24);
    if (version != 1u || page_size == 0u || (page_size & (page_size - 1u)) != 0u ||
        image_size == 0u || image_size > 16777216u || image_size % page_size != 0u ||
        page_count != image_size / page_size || payload_pages > page_count ||
        (uint64_t)payload_size != (uint64_t)payload_pages * page_size)
        return false;
    const size_t map_size = (size_t)page_count * 4u;
    const size_t payload_offset = HEADER_SIZE + map_size;
    if (payload_offset > size || payload_size != size - payload_offset)
        return false;
    /* Bound validation stack to 512 bytes for the target's 4KiB-page format. */
    if (page_size != 4096u || page_count > 4096u) return false;
    uint8_t seen[512] = {0};
    for (uint32_t i = 0; i < page_count; ++i) {
        uint32_t index = le32(data + HEADER_SIZE + (size_t)i * 4u);
        if (index == ERASED_PAGE) continue;
        if (index >= payload_pages) return false;
        uint8_t bit = (uint8_t)(1u << (index % 8u));
        if (seen[index / 8u] & bit) return false;
        seen[index / 8u] |= bit;
    }
    for (uint32_t i = 0; i < payload_pages; ++i)
        if (!(seen[i / 8u] & (1u << (i % 8u)))) return false;
    reader->map = data + HEADER_SIZE;
    reader->payload = data + payload_offset;
    reader->page_size = page_size;
    reader->image_size = image_size;
    reader->page_count = page_count;
    reader->payload_pages = payload_pages;
    reader->ready = true;
    return true;
}

bool bc250_sparse_read(const bc250_sparse_reader_t *reader, uint32_t address,
                       uint8_t *out, size_t size) {
    if (!reader || !reader->ready || (!out && size)) return false;
    if (address > reader->image_size || size > reader->image_size - address)
        return false;
    while (size) {
        uint32_t page = address / reader->page_size;
        uint32_t offset = address % reader->page_size;
        uint32_t payload_page = le32(reader->map + (size_t)page * 4u);
        size_t count = reader->page_size - offset;
        if (count > size) count = size;
        if (payload_page == ERASED_PAGE) {
            memset(out, 0xff, count);
        } else {
            memcpy(out, reader->payload + (size_t)payload_page * reader->page_size + offset, count);
        }
        address += (uint32_t)count;
        out += count;
        size -= count;
    }
    return true;
}
