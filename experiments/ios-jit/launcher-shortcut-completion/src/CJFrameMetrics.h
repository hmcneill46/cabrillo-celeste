#pragma once
#include <stddef.h>
#define CJ_FRAME_WINDOW 600
typedef struct {double intervals[CJ_FRAME_WINDOW],cpu[CJ_FRAME_WINDOW],last;size_t cursor,count,total;} CJFrameMetrics;
typedef struct {double fps,cpu_ms,one_percent_low,maximum_ms;size_t samples;} CJFrameSummary;
void CJFrameReset(CJFrameMetrics *metrics);
void CJFrameRecord(CJFrameMetrics *metrics,double timestamp,double cpu_seconds);
CJFrameSummary CJFrameSummarize(const CJFrameMetrics *metrics);
