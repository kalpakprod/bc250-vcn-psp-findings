#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

#define ADAPTER_NET_MAGIC 0x31415657u
#define ADAPTER_NET_VERSION 1u
#define ADAPTER_NET_OFFSET 0x00ffc000u

typedef struct __attribute__((packed)) {
    uint32_t magic;
    uint16_t version;
    char ssid[33];
    char psk[65];
    char broker[16];
    uint16_t port;
    char mqtt_user[33];
    char mqtt_password[65];
    char web_token[65];
    uint32_t crc;
} adapter_net_config_t;

static inline bool adapter_http_ascii_equal(const char *value, const char *expected,
                                            size_t size) {
    for (size_t i=0;i<size;++i) {
        unsigned char a=(unsigned char)value[i],b=(unsigned char)expected[i];
        if(a>='A' && a<='Z')a+=(unsigned char)('a'-'A');
        if(b>='A' && b<='Z')b+=(unsigned char)('a'-'A');
        if(a!=b)return false;
    }
    return true;
}

/* Only complete CRLF header lines authorize; never inspect the request body.
   Header/scheme are case-insensitive, but token bytes stay exact. */
static inline bool adapter_http_token_ok(const char *request, size_t received,
                                         const char *token) {
    const size_t token_size=strlen(token);
    if(!token_size)return false;
    bool first=true,authorized=false;
    size_t start=0;
    while(start<received) {
        size_t end=start;
        while(end+1<received && !(request[end]=='\r' && request[end+1]=='\n'))++end;
        if(end+1>=received)return false;
        if(end==start)return authorized;
        if(!first) {
            const char *colon=(const char *)memchr(request+start,':',end-start);
            if(colon && (size_t)(colon-(request+start))==13 &&
               adapter_http_ascii_equal(request+start,"Authorization",13)) {
                if(authorized)return false; // Duplicate authorization is ambiguous.
                const char *value=colon+1,*line_end=request+end;
                while(value<line_end && (*value==' ' || *value=='\t'))++value;
                if((size_t)(line_end-value)!=7+token_size ||
                   !adapter_http_ascii_equal(value,"Bearer",6) || value[6]!=' ')return false;
                unsigned difference=0;
                for(size_t i=0;i<token_size;++i)
                    difference|=(unsigned char)value[7+i]^(unsigned char)token[i];
                if(difference)return false;
                authorized=true;
            }
        }
        first=false;start=end+2;
    }
    return false;
}

static inline uint32_t adapter_crc32(const uint8_t *data, size_t size) {
    uint32_t crc = 0xffffffffu;
    for (size_t i=0;i<size;++i) {
        crc ^= data[i];
        for (unsigned j=0;j<8;++j) crc=(crc>>1)^((0u-(crc&1u))&0xedb88320u);
    }
    return ~crc;
}
static inline bool adapter_net_valid(const adapter_net_config_t *c) {
    if (c->magic != ADAPTER_NET_MAGIC || c->version != ADAPTER_NET_VERSION) return false;
    if (c->crc != adapter_crc32((const uint8_t *)c, offsetof(adapter_net_config_t,crc))) return false;
    if (!memchr(c->ssid,0,sizeof(c->ssid)) || !c->ssid[0] || !memchr(c->psk,0,sizeof(c->psk))) return false;
    if (!memchr(c->broker,0,sizeof(c->broker)) || !memchr(c->mqtt_user,0,sizeof(c->mqtt_user)) || !memchr(c->mqtt_password,0,sizeof(c->mqtt_password))) return false;
    if (strlen(c->psk)<8 || strlen(c->psk)>63 || !memchr(c->web_token,0,sizeof(c->web_token))) return false;
    const size_t tokensize=strlen(c->web_token);
    if (tokensize<32 || tokensize>64 || c->port==0) return false;
    for (size_t i=0;i<tokensize;++i) {
        const char v=c->web_token[i];
        if (!((v>='0'&&v<='9')||(v>='a'&&v<='f'))) return false;
    }
    return true;
}
