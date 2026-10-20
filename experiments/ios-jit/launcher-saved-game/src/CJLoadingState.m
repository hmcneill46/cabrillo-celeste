#import "CJLoadingState.h"
#import <os/lock.h>
#include <math.h>
#include <string.h>

static os_unfair_lock gLock = OS_UNFAIR_LOCK_INIT;
static NSDictionary *gState;
static double gBegan;
static double gEnded;
static NSString *Bounded(NSString *value) {
    if(value.length<=240)return value;
    NSRange last=[value rangeOfComposedCharacterSequenceAtIndex:239];
    return [value substringToIndex:NSMaxRange(last)<=240?240:last.location];
}
void CJLoadingBegin(void) {
    os_unfair_lock_lock(&gLock);
    gBegan=NSProcessInfo.processInfo.systemUptime;
    gEnded=0;
    gState=@{@"active":@YES,@"failed":@NO,@"ready":@NO,@"phase":@"selection",
             @"detail":@"Checking your selected mods",@"completed":@(-1),@"total":@(-1),@"abi":@1};
    os_unfair_lock_unlock(&gLock);
}
void CJLoadingStage(NSString *phase, NSString *detail) {
    os_unfair_lock_lock(&gLock);
    if([gState[@"active"] boolValue] && ![gState[@"failed"] boolValue]) {
        NSMutableDictionary *next=[gState mutableCopy];
        next[@"phase"]=Bounded(phase);next[@"detail"]=Bounded(detail);
        next[@"completed"]=@(-1);next[@"total"]=@(-1);gState=next;
    }
    os_unfair_lock_unlock(&gLock);
}
BOOL CJLoadingAccept(const char *json) {
    if(!json)return NO;
    size_t length=strnlen(json,8193);if(length>8192)return NO;
    id value=[NSJSONSerialization JSONObjectWithData:[NSData dataWithBytes:json length:length] options:0 error:nil];
    if(![value isKindOfClass:NSDictionary.class] || ![value[@"abi"] isEqual:@1])return NO;
    NSSet *phases=[NSSet setWithArray:@[@"platform",@"settings",@"hooks",@"window",@"everest",@"content_index",@"mod_index",@"mods",@"dependencies",@"maps",@"mod_options",@"verify_mods",@"game_content",@"ready"]];
    NSString *phase=value[@"phase"], *detail=value[@"detail"];
    if(![phase isKindOfClass:NSString.class] || ![phases containsObject:phase] || ![detail isKindOfClass:NSString.class])return NO;
    NSArray *keys=@[@"completed",@"total",@"archives_processed",@"archives_total",@"module_attempts",@"modules_loaded",@"load_failures",@"skipped",@"delayed",@"managed_thread",@"monotonic_seconds"];
    for(NSString *key in keys) {
        id number=value[key];double n=[number isKindOfClass:NSNumber.class]?[number doubleValue]:NAN;
        if(!isfinite(n) || n< -1)return NO;
        if(![key isEqualToString:@"monotonic_seconds"] && (floor(n)!=n || n>INT_MAX))return NO;
    }
    if([value[@"total"] intValue]>=0 && ([value[@"completed"] intValue]<0 || [value[@"completed"] intValue]>[value[@"total"] intValue]))return NO;
    if([value[@"archives_total"] intValue]>=0 && ([value[@"archives_processed"] intValue]<0 || [value[@"archives_processed"] intValue]>[value[@"archives_total"] intValue]))return NO;
    os_unfair_lock_lock(&gLock);
    // A valid late observer report cannot reopen a completed/failed presentation.
    if(![gState[@"active"] boolValue] || [gState[@"failed"] boolValue]) {os_unfair_lock_unlock(&gLock);return YES;}
    NSMutableDictionary *next=[gState mutableCopy];
    for(NSString *key in keys)next[key]=value[key];
    next[@"phase"]=phase;next[@"detail"]=Bounded(detail);
    next[@"ready"]=@([phase isEqualToString:@"ready"]);gState=next;
    os_unfair_lock_unlock(&gLock);return YES;
}
void CJLoadingFail(NSString *detail) {
    os_unfair_lock_lock(&gLock);
    NSMutableDictionary *next=[(gState?:@{}) mutableCopy];
    if(![gState[@"failed"] boolValue])gEnded=NSProcessInfo.processInfo.systemUptime;
    next[@"active"]=@YES;next[@"failed"]=@YES;next[@"ready"]=@NO;
    next[@"failure"]=Bounded(detail?:@"Celeste could not finish starting.");gState=next;
    os_unfair_lock_unlock(&gLock);
}
void CJLoadingEnd(void) {
    os_unfair_lock_lock(&gLock);
    NSMutableDictionary *next=[(gState?:@{}) mutableCopy];
    if([gState[@"active"] boolValue])gEnded=NSProcessInfo.processInfo.systemUptime;
    next[@"active"]=@NO;gState=next;
    os_unfair_lock_unlock(&gLock);
}
NSDictionary *CJLoadingSnapshot(void) {
    os_unfair_lock_lock(&gLock);
    NSMutableDictionary *snapshot=[(gState?:@{}) mutableCopy];
    snapshot[@"started_uptime"]=@(gBegan);
    snapshot[@"elapsed_seconds"]=@(gBegan>0?MAX(0,(gEnded>0?gEnded:NSProcessInfo.processInfo.systemUptime)-gBegan):0);
    os_unfair_lock_unlock(&gLock);return snapshot;
}
