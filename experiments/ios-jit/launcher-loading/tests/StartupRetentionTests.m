#import <Foundation/Foundation.h>
#import "CJEventStore.h"
#include <assert.h>

int main(int argc,const char **argv) { @autoreleasepool {
    assert(argc==2);
    NSURL *root=[NSURL fileURLWithPath:@(argv[1]) isDirectory:YES];
    assert(![NSFileManager.defaultManager fileExistsAtPath:root.path]);
    assert([NSFileManager.defaultManager createDirectoryAtURL:root withIntermediateDirectories:YES attributes:nil error:NULL]);
    CJEventStore *store=[[CJEventStore alloc] initWithURL:[root URLByAppendingPathComponent:@"session-test.jsonl"]];
    for(int i=0;i<8;i++)[store append:@{@"event":@"header",@"session":@"test",@"fields":@{@"index":@(i)}}];
    NSArray *phases=@[@"catalogue_quiescence",@"runtime_prepare",@"content_prepare",@"managed_start"];
    for(NSString *phase in phases)for(NSString *edge in @[@"begin",@"end"])
        [store append:@{@"event":[@"startup_phase_" stringByAppendingString:edge],@"session":@"test",@"fields":@{@"phase":phase,@"started_uptime":@1,@"seconds":@2,@"outcome":@"returned"}}];
    // A long game must not erase early phase timings when the ring wraps.
    for(int i=0;i<900;i++)[store append:@{@"event":@"game_progress",@"session":@"test",@"fields":@{@"frame":@(i)}}];
    NSMutableSet *retained=[NSMutableSet set];
    for(NSDictionary *event in [store snapshot])if([event[@"event"] hasPrefix:@"startup_phase_"])
        [retained addObject:[NSString stringWithFormat:@"%@:%@",event[@"event"],event[@"fields"][@"phase"]]];
    assert(retained.count==8);
    for(NSString *phase in phases)for(NSString *edge in @[@"begin",@"end"])
        assert(([retained containsObject:[NSString stringWithFormat:@"startup_phase_%@:%@",edge,phase]]));
    NSDictionary *summary=[store summary];
    assert(!store.error && [store snapshot].count<=1032);
    assert([summary[@"evicted_selected_events"] unsignedIntegerValue]>0);
    assert([summary[@"retained_milestones"] unsignedIntegerValue]==10);
    assert([summary[@"allocation_trace"][@"records"] unsignedIntegerValue]==0);
    NSData *report=[NSJSONSerialization dataWithJSONObject:@{@"status":@"PASS_STARTUP_PHASE_RETENTION",@"retained_phases":@4,@"retained_edges":@(retained.count),@"summary":summary} options:NSJSONWritingPrettyPrinted error:NULL];
    assert([report writeToURL:[root URLByAppendingPathComponent:@"result.json"] atomically:YES]);
    puts("PASS_STARTUP_PHASE_RETENTION: all 8 phase edges survived ring eviction");
    return 0;
} }
