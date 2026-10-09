#pragma once
#include <cstdint>

struct PsEventTracker {
    bool pressed=false;
    bool seen=false;
    uint32_t sequence=0;
    uint32_t last_rise=0;
    void update(bool level,uint32_t now) {
        if(level && !pressed) {
            if(++sequence==0)++sequence;
            last_rise=now;
            seen=true;
        }
        pressed=level;
    }
    uint32_t age(uint32_t now) const { return uint32_t(now-last_rise); }
};
