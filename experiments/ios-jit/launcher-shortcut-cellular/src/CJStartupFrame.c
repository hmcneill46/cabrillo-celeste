#include "CJStartupFrame.h"
#include <string.h>
void CJStartupFrameObserve(CJStartupFrame *state, const char *event, const char *message, bool mainThread) {
    if(!state || !event || !mainThread)return;
    if(!strcmp(event,"game_first_draw"))state->drawn=true;
    const char prefix[]="phase=after_present;";
    if(state->drawn && !strcmp(event,"game_backbuffer_frame_pass") && message && !strncmp(message,prefix,sizeof(prefix)-1))state->readback=true;
}
