#pragma once
#include <cstdint>
#include <cstddef>
#include <cstring>

enum class UsbIdentityAction { None, Disconnect, Connect };

struct UsbIdentityGate {
    bool latched = false;
    bool reconnect_pending = false;
    uint32_t disconnected_at = 0;
    UsbIdentityAction step(uint32_t now, bool ready, bool suspended) {
        if (reconnect_pending) {
            if (suspended || uint32_t(now - disconnected_at) < 250) return UsbIdentityAction::None;
            reconnect_pending = false;
            latched = ready;
            return UsbIdentityAction::Connect;
        }
        if (!ready) latched = false;
        if (ready && !latched && !suspended) {
            latched = true;
            reconnect_pending = true;
            disconnected_at = now;
            return UsbIdentityAction::Disconnect;
        }
        return UsbIdentityAction::None;
    }
};

// Report 0 carries an in-band ID; state 0x02 needs only the wire prefix.
// Standard DS5 declares 47 bytes; Edge also includes 16 reserved bytes.
inline bool usb_set_report_length_ok(uint8_t report_id, const uint8_t *buffer,
                                     size_t received, size_t min_state_bytes) {
    if (!buffer || received == 0) return false;
    return report_id != 0 || buffer[0] != 0x02 || received >= 1 + min_state_bytes;
}

// The caller zero-initializes storage so omitted reserved bytes stay zero.
inline void usb_copy_set_state_payload(void *update, size_t update_bytes,
                                       const uint8_t *payload, size_t received) {
    std::memcpy(update, payload, received < update_bytes ? received : update_bytes);
}

inline uint16_t usb_feature_payload_length(size_t stored, uint16_t requested) {
    if (stored <= 1) return 0;
    const size_t payload = stored - 1; // TinyUSB adds the report ID itself.
    return uint16_t(payload < requested ? payload : requested);
}
