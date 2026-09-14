#pragma once
#include <stdint.h>
#include <stddef.h>

// Little-endian ARM64 mailbox. The debugger only writes the response (48..95).
// No executable memory or breakpoint is needed to publish/receive this request.
typedef struct __attribute__((aligned(16))) {
    char magic[8];
    uint64_t version;
    uint8_t nonce[16];
    uint64_t pid;
    uint64_t requestedLength;
    volatile uint64_t status; // 0 idle, 1 requested, 2 prepared, 3 script failed
    volatile uint64_t rx1;
    volatile uint64_t rx2;
    volatile uint64_t length;
    volatile uint64_t scriptVersion;
    volatile uint64_t error;
} CJMailbox;

_Static_assert(sizeof(CJMailbox) == 96, "Script mailbox size changed");
_Static_assert(offsetof(CJMailbox, status) == 48, "Script response offset changed");
_Static_assert(offsetof(CJMailbox, error) == 88, "Script error offset changed");

#define CJ_PROTOCOL_VERSION 1
#define CJ_ARENA_LENGTH 4194304
