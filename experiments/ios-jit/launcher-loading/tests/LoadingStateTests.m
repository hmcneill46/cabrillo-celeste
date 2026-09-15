#import <Foundation/Foundation.h>
#import "CJLoadingState.h"
#import "CJEventStore.h"
#include <assert.h>
#include <unistd.h>

static NSMutableDictionary *Progress(NSString *phase) {
    return [@{@"abi":@1,@"phase":phase,@"detail":@"Example 1.0.0",@"completed":@1,@"total":@3,
        @"archives_processed":@1,@"archives_total":@3,@"module_attempts":@2,@"modules_loaded":@2,
        @"load_failures":@0,@"skipped":@0,@"delayed":@1,@"managed_thread":@1,@"monotonic_seconds":@12.5} mutableCopy];
}
static BOOL Accept(NSDictionary *value) {
    NSData *data=[NSJSONSerialization dataWithJSONObject:value options:0 error:NULL];
    NSString *json=[[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
    return CJLoadingAccept(json.UTF8String);
}
int main(int argc,const char **argv) { @autoreleasepool {
    assert(argc==2);
    NSURL *root=[NSURL fileURLWithPath:@(argv[1]) isDirectory:YES];
    assert(![NSFileManager.defaultManager fileExistsAtPath:root.path]);
    assert([NSFileManager.defaultManager createDirectoryAtURL:root withIntermediateDirectories:YES attributes:nil error:NULL]);
    CJLoadingBegin(); assert([CJLoadingSnapshot()[@"active"] boolValue]);
    CJLoadingStage(@"runtime",@"Preparing");assert([CJLoadingSnapshot()[@"phase"] isEqual:@"runtime"]);
    assert(Accept(Progress(@"mods")));
    assert([CJLoadingSnapshot()[@"modules_loaded"] intValue]==2);
    NSArray *bad=@[@{@"phase":@"invented"},@{@"abi":@2},@{@"total":@0},@{@"completed":@4},
        @{@"archives_processed":@4},@{@"module_attempts":@0.5},@{@"managed_thread":@1e30},
        @{@"delayed":@(-2)},@{@"detail":@12},@{@"modules_loaded":@"2"}];
    for(NSDictionary *change in bad){NSMutableDictionary *value=Progress(@"mods");[value addEntriesFromDictionary:change];assert(!Accept(value));}
    assert(!CJLoadingAccept(NULL) && !CJLoadingAccept("[]") && !CJLoadingAccept("{"));
    NSMutableDictionary *longText=Progress(@"mods");
    longText[@"detail"]=[@"a" stringByPaddingToLength:239 withString:@"a" startingAtIndex:0];
    longText[@"detail"]=[longText[@"detail"] stringByAppendingString:@"🏔️"];assert(Accept(longText));
    assert([CJLoadingSnapshot()[@"detail"] length]==239);
    longText[@"detail"]=[@"a" stringByPaddingToLength:9000 withString:@"a" startingAtIndex:0];assert(!Accept(longText));
    assert(Accept(Progress(@"ready")));assert([CJLoadingSnapshot()[@"ready"] boolValue]);
    CJLoadingEnd();NSDictionary *finished=CJLoadingSnapshot();usleep(20000);
    assert([finished isEqual:CJLoadingSnapshot()]);
    assert(Accept(Progress(@"mods")) && [finished isEqual:CJLoadingSnapshot()]);
    CJLoadingBegin();CJLoadingFail(@"Test failure");NSDictionary *failure=CJLoadingSnapshot();usleep(20000);
    assert([failure isEqual:CJLoadingSnapshot()]);assert(Accept(Progress(@"ready")));
    assert([failure isEqual:CJLoadingSnapshot()]);CJLoadingStage(@"runtime",@"Must not replace failure");
    assert([failure isEqual:CJLoadingSnapshot()]);

    CJEventStore *store=[[CJEventStore alloc] initWithURL:[root URLByAppendingPathComponent:@"session-loading.jsonl"]];
    NSArray *phases=@[@"platform",@"settings",@"hooks",@"window",@"everest",@"content_index",@"mod_index",@"mods",@"dependencies",@"maps",@"mod_options",@"verify_mods",@"game_content",@"ready"];
    for(NSString *phase in phases)[store append:@{@"event":@"startup_progress",@"session":@"test",@"fields":@{@"progress":Progress(phase)}}];
    [store append:@{@"event":@"startup_failed",@"session":@"test",@"fields":@{@"failure":@"retained",@"requires_fresh_process":@YES}}];
    for(int i=0;i<1200;i++)[store append:@{@"event":@"game_progress",@"session":@"test",@"fields":@{@"frame":@(i)}}];
    NSMutableSet *retained=[NSMutableSet set];BOOL retainedFailure=NO;
    for(NSDictionary *event in store.snapshot){
        if([event[@"event"] isEqual:@"startup_progress"])[retained addObject:event[@"fields"][@"progress"][@"phase"]];
        if([event[@"event"] isEqual:@"startup_failed"])retainedFailure=YES;
    }
    assert(retained.count==phases.count && retainedFailure && !store.error);
    NSData *report=[NSJSONSerialization dataWithJSONObject:@{@"status":@"PASS_LOADING_STATE_AND_RETENTION",@"invalid_reports_rejected":@(bad.count+4),@"retained_phases":@(retained.count),@"terminal_state_stable":@YES,@"summary":store.summary} options:NSJSONWritingPrettyPrinted error:NULL];
    assert([report writeToURL:[root URLByAppendingPathComponent:@"result.json"] atomically:YES]);
    puts("PASS_LOADING_STATE_AND_RETENTION");return 0;
} }
