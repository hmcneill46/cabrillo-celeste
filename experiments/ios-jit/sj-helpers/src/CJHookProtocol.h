#pragma once
// Select the managed-runtime contract explicitly. An unqualified ProbeProtocol.h
// can resolve to the older 64 KiB native probe through a different -I order.
#include "../../managed-canary/src/ProbeProtocol.h"
#include "CJHookMemory.h"
_Static_assert(CJ_HOOK_ARENA_LENGTH == 67108864, "Review the hook script when changing arena capacity");
_Static_assert(CJ_PROTOCOL_VERSION == 1, "Review the matching StikDebug script before changing protocol");

typedef struct {
    char magic[8];
    uint64_t version, arenaLength, mailboxBytes, responseOffset, errorOffset;
} CJProtocolDescriptor;
// Read by the actual request builder and independently extracted from the IPA.
static const CJProtocolDescriptor CJCompiledProtocol __attribute__((used, section("__TEXT,__cjprotocol"))) = {
    "CJITM1", CJ_PROTOCOL_VERSION, CJ_HOOK_ARENA_LENGTH, sizeof(CJMailbox),
    offsetof(CJMailbox, status), offsetof(CJMailbox, error)
};
