#pragma once
#include <stdbool.h>
typedef struct { bool drawn, readback; } CJStartupFrame;
// Observes the pinned adapter's existing evidence around Draw and Present.
void CJStartupFrameObserve(CJStartupFrame *state, const char *event, const char *message, bool mainThread);
