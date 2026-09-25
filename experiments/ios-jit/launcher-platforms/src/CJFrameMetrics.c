#include "CJFrameMetrics.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
void CJFrameReset(CJFrameMetrics *m){memset(m,0,sizeof(*m));}
void CJFrameRecord(CJFrameMetrics *m,double timestamp,double cpu){
    if(!isfinite(timestamp)||!isfinite(cpu)||cpu<0)return;
    double interval=timestamp-m->last;m->total++;
    if(m->last>0 && interval>0){m->intervals[m->cursor]=interval;m->cpu[m->cursor]=cpu;m->cursor=(m->cursor+1)%CJ_FRAME_WINDOW;if(m->count<CJ_FRAME_WINDOW)m->count++;}
    m->last=timestamp;
}
static int descending(const void *left,const void *right){double a=*(const double*)left,b=*(const double*)right;return a<b?1:a>b?-1:0;}
CJFrameSummary CJFrameSummarize(const CJFrameMetrics *m){
    CJFrameSummary s={.samples=m->count};if(!m->count)return s;
    double sum=0,cpu=0,sorted[CJ_FRAME_WINDOW];
    for(size_t i=0;i<m->count;i++){sum+=m->intervals[i];cpu+=m->cpu[i];sorted[i]=m->intervals[i];}
    qsort(sorted,m->count,sizeof(double),descending);s.fps=m->count/sum;s.cpu_ms=cpu*1000/m->count;s.maximum_ms=sorted[0]*1000;
    if(m->count>=120){size_t n=(m->count+99)/100;double worst=0;for(size_t i=0;i<n;i++)worst+=sorted[i];s.one_percent_low=n/worst;}
    return s;
}
