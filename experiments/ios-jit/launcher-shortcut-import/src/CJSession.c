#include "CJSession.h"
#include <stdatomic.h>
static _Atomic int opened, quitOrigin, currentStage;
int CJSessionOpen(int abi) {
    int expected=0;
    return abi==CJ_SESSION_ABI && atomic_compare_exchange_strong(&opened,&expected,1);
}
int CJSessionRequestQuit(int abi,int origin) {
    if(abi!=CJ_SESSION_ABI || (origin!=1 && origin!=2) || atomic_load(&opened)!=1)return 0;
    int expected=0;
    return atomic_compare_exchange_strong(&quitOrigin,&expected,origin)?1:2;
}
int CJSessionQuitOrigin(void) { return atomic_load(&quitOrigin); }
int CJSessionStage(void) { return atomic_load(&currentStage); }
int CJSessionAdvance(int abi,int stage) {
    if(abi!=CJ_SESSION_ABI || atomic_load(&opened)!=1 || stage<1 || stage>8)return 0;
    int expected=stage-1;
    return atomic_compare_exchange_strong(&currentStage,&expected,stage);
}
void CJSessionClose(void) { atomic_store(&opened,2); }
const char *CJSessionStageName(int stage) {
    static const char *names[]={"Playing","Finishing pending saves","Verifying saved data","Ending the game loop","Releasing textures","Closing game and mod hooks","Closing platform services","Removing host hooks","Complete"};
    return stage>=0 && stage<=8?names[stage]:"Unknown";
}
