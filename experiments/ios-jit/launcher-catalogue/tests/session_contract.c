#include "CJSession.h"
#include <assert.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
static _Atomic int firstRequests, repeats;
static void *request(void *unused) {
    (void)unused;int result=CJSessionRequestQuit(1,1);
    assert(result==1 || result==2);
    if(result==1)atomic_fetch_add(&firstRequests,1);else atomic_fetch_add(&repeats,1);
    return NULL;
}
int main(void) {
    assert(!CJSessionRequestQuit(1,1));assert(!CJSessionOpen(99));
    assert(CJSessionOpen(1));assert(!CJSessionOpen(1));
    assert(!CJSessionRequestQuit(2,1));assert(!CJSessionRequestQuit(1,99));
    pthread_t threads[32];
    for(int i=0;i<32;i++)assert(!pthread_create(&threads[i],NULL,request,NULL));
    for(int i=0;i<32;i++)assert(!pthread_join(threads[i],NULL));
    assert(firstRequests==1 && repeats==31 && CJSessionQuitOrigin()==1);
    assert(CJSessionRequestQuit(1,2)==2 && CJSessionQuitOrigin()==1);
    for(int i=1;i<=8;i++) {
        assert(!CJSessionAdvance(99,i));assert(!CJSessionAdvance(1,i+1));
        assert(CJSessionAdvance(1,i));assert(!CJSessionAdvance(1,i));assert(CJSessionStage()==i);
    }
    CJSessionClose();assert(!CJSessionRequestQuit(1,1));assert(!CJSessionOpen(1));
    puts("PASS_SESSION_ABI_ORDER_CONCURRENT_QUIT_AND_CLOSED_LIFETIME");
}
