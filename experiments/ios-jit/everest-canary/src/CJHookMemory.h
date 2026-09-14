#pragma once
// Hook-generated assemblies each reserve Mono code-manager chunks. This is a
// separate canary budget; the accepted managed-only probe keeps its 4 MiB arenas.
#define CJ_HOOK_ARENA_LENGTH 33554432
#define CJ_HOOK_CODE_BUDGET (2 * CJ_HOOK_ARENA_LENGTH)
