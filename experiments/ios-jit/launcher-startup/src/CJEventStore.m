#import "CJEventStore.h"
#import <CommonCrypto/CommonDigest.h>
#import <fcntl.h>
#import <unistd.h>
#import <errno.h>
static const NSUInteger CJJournalLimit=4*1024*1024, CJMemoryLimit=2*1024*1024, CJAllocationLimit=65536;
static BOOL CJWrite(int fd,NSData *data) {
    const uint8_t *p=data.bytes;size_t left=data.length;
    while(left){ssize_t n=write(fd,p,left);if(n<0 && errno==EINTR)continue;if(n<=0)return NO;p+=n;left-=(size_t)n;}return YES;
}
static NSString *CJDigest(NSData *data){unsigned char d[32];CC_SHA256(data.bytes,(CC_LONG)data.length,d);NSMutableString *s=[NSMutableString string];for(int i=0;i<32;i++)[s appendFormat:@"%02x",d[i]];return s;}
@interface CJEventStore ()
@property(nonatomic) NSUInteger totalCount,ringBytes,milestoneBytes,rotations,evicted,oversize,allocations,allocationOverflow,fsyncCount;
@property(nonatomic) int fd,allocationFD;
@property(nonatomic) NSUInteger journalBytes;
@property(nonatomic) NSTimeInterval lastSync;
@property(nonatomic,strong) NSURL *url,*allocationURL;
@property(nonatomic,strong) NSMutableArray *head,*ring,*ringSizes,*milestoneKeys;
@property(nonatomic,strong) NSMutableDictionary *counts,*samples,*milestones,*milestoneSizes;
@property(nonatomic,strong) NSSet *routine;
@property(nonatomic,strong,nullable) NSString *error;
@end
@implementation CJEventStore
- (instancetype)initWithURL:(NSURL *)url {
    if(!(self=[super init]))return nil;
    _url=url;_fd=open(url.fileSystemRepresentation,O_CREAT|O_APPEND|O_WRONLY,0600);_allocationFD=-1;
    if(_fd<0)_error=@"Could not open diagnostic journal";
    _allocationURL=[url URLByAppendingPathExtension:@"allocations.bin"];
    _allocationFD=open(_allocationURL.fileSystemRepresentation,O_CREAT|O_EXCL|O_WRONLY,0600);
    if(_allocationFD<0)_error=@"Could not open allocation evidence";
    _head=[NSMutableArray array];_ring=[NSMutableArray array];_ringSizes=[NSMutableArray array];_counts=[NSMutableDictionary dictionary];_samples=[NSMutableDictionary dictionary];
    _milestones=[NSMutableDictionary dictionary];_milestoneSizes=[NSMutableDictionary dictionary];_milestoneKeys=[NSMutableArray array];
    _routine=[NSSet setWithArray:@[@"mono_jit_begin",@"mono_jit_done",@"mono_code_chunk_created",@"mono_hook_patch_applied",@"hook_code_patch",@"pinvoke_resolution",@"code_allocation",@"everest_assembly_resolution",@"everest_generated_mod_reference",@"fna_pinvoke_resolved",@"mono_pinvoke_resolved",@"mono_assembly_resolve",@"generated_mod_reference"]];
    return self;
}
- (void)dealloc { if(_fd>=0)close(_fd);if(_allocationFD>=0)close(_allocationFD); }
- (void)sync { if(_fd>=0 && fsync(_fd)!=0)_error=@"Could not sync diagnostic journal";if(_allocationFD>=0 && fsync(_allocationFD)!=0)_error=@"Could not sync allocation evidence";_fsyncCount++;_lastSync=NSProcessInfo.processInfo.systemUptime; }
- (void)writeRecord:(NSDictionary *)event {
    NSMutableData *data=[[NSJSONSerialization dataWithJSONObject:event options:NSJSONWritingSortedKeys error:NULL] mutableCopy];
    if(!data){_error=@"Diagnostic event was not valid JSON";return;}[data appendBytes:"\n" length:1];
    if(_journalBytes+data.length>CJJournalLimit){
        [self sync];close(_fd);_fd=-1;
        NSURL *previous=[_url URLByAppendingPathExtension:@"previouspart"];
        if(rename(_url.fileSystemRepresentation,previous.fileSystemRepresentation)!=0){_error=@"Could not rotate diagnostic journal";return;}
        _fd=open(_url.fileSystemRepresentation,O_CREAT|O_TRUNC|O_WRONLY,0600);_journalBytes=0;_rotations++;
        for(NSDictionary *header in _head){NSMutableData *h=[[NSJSONSerialization dataWithJSONObject:header options:0 error:NULL] mutableCopy];[h appendBytes:"\n" length:1];if(!CJWrite(_fd,h))_error=@"Could not write journal header";_journalBytes+=h.length;}
    }
    if(_fd<0 || !CJWrite(_fd,data))_error=@"Could not append diagnostic journal";_journalBytes+=data.length;
}
- (BOOL)append:(NSDictionary *)event {
    _totalCount++;
    NSMutableDictionary *sequenced=[event mutableCopy];sequenced[@"sequence"]=@(_totalCount);event=sequenced;
    NSString *name=event[@"event"]?:@"unknown";
    // Names are emitted by our native bridge; still cap cardinality explicitly.
    NSString *key=(_counts[name] || _counts.count<512)?name:@"other_event_names";
    NSUInteger count=[_counts[key] unsignedIntegerValue]+1;_counts[key]=@(count);
    if([name isEqualToString:@"code_allocation"]){
        if(_allocations<CJAllocationLimit){
            NSDictionary *f=event[@"fields"];unsigned long long address=strtoull([f[@"address"] UTF8String],NULL,0);
            uint64_t row[]={CFSwapInt64HostToLittle(address),CFSwapInt64HostToLittle([f[@"requested_bytes"] unsignedLongLongValue]),CFSwapInt64HostToLittle([f[@"total_reserved_bytes"] unsignedLongLongValue])};
            if(_allocationFD<0 || !CJWrite(_allocationFD,[NSData dataWithBytes:row length:sizeof(row)]))_error=@"Could not append allocation evidence";
            _allocations++;
        }else _allocationOverflow++;
    }
    BOOL routine=[_routine containsObject:name];
    if([name isEqualToString:@"mono_jit_done"] && ![event[@"fields"][@"in_prepared_allocation"] boolValue])routine=NO;
    if(routine){
        NSMutableDictionary *sample=_samples[name];if(!sample){sample=[NSMutableDictionary dictionaryWithDictionary:@{@"first":event}];_samples[name]=sample;}sample[@"last"]=event;
        // A few representative events survive a crash; full counts are flushed
        // on milestones and at least once per second while calls keep arriving.
        if(count>2){if(NSProcessInfo.processInfo.systemUptime-_lastSync>=1.0){[self writeRecord:@{@"event":@"diagnostic_counters",@"session":event[@"session"]?:@"",@"time_unix":event[@"time_unix"]?:@0,@"fields":@{@"total":@(_totalCount),@"counts":[_counts copy],@"allocation_records":@(_allocations),@"allocation_overflow":@(_allocationOverflow)}}];[self sync];}return NO;}
    }
    NSDictionary *retained=event;
    NSData *encoded=[NSJSONSerialization dataWithJSONObject:event options:0 error:NULL];
    if(encoded.length>256*1024){_oversize++;retained=@{@"sequence":@(_totalCount),@"event":name,@"session":event[@"session"]?:@"",@"fields":@{@"oversize_event_bytes":@(encoded.length),@"sha256":CJDigest(encoded),@"details_omitted":@YES}};encoded=[NSJSONSerialization dataWithJSONObject:retained options:0 error:NULL];}
    if(_head.count<8)[_head addObject:retained];
    else {
        [_ring addObject:retained];[_ringSizes addObject:@(encoded.length)];_ringBytes+=encoded.length;
        while(_ring.count>768 || _ringBytes>CJMemoryLimit){_ringBytes-=[_ringSizes.firstObject unsignedIntegerValue];[_ring removeObjectAtIndex:0];[_ringSizes removeObjectAtIndex:0];_evicted++;}
    }
    if(!routine){
        NSString *check=event[@"fields"][@"check"];
        if(!check && [name hasPrefix:@"graphics_check_"])check=event[@"fields"][@"message"];
        // Retain each startup phase after gameplay evicts the ordinary ring.
        // The four fixed phase names keep this within the existing bounds.
        if(!check && ([name isEqualToString:@"startup_phase_begin"] || [name isEqualToString:@"startup_phase_end"]))check=event[@"fields"][@"phase"];
        NSString *identity=check?[name stringByAppendingFormat:@":%@",check]:name;
        if(_milestones[identity]){_milestoneBytes-=[_milestoneSizes[identity] unsignedIntegerValue];[_milestoneKeys removeObject:identity];}
        _milestones[identity]=retained;_milestoneSizes[identity]=@(encoded.length);[_milestoneKeys addObject:identity];_milestoneBytes+=encoded.length;
        while(_milestoneKeys.count>256 || _milestoneBytes>2*CJMemoryLimit){NSString *key=_milestoneKeys.firstObject;_milestoneBytes-=[_milestoneSizes[key] unsignedIntegerValue];[_milestoneKeys removeObjectAtIndex:0];[_milestones removeObjectForKey:key];[_milestoneSizes removeObjectForKey:key];}
    }
    [self writeRecord:retained];
    // All non-routine milestones, exceptions and pre-execution checks are durable.
    if(!routine)[self sync];
    return !routine;
}
- (NSArray *)snapshot {
    NSMutableDictionary *unique=[NSMutableDictionary dictionary];
    for(NSDictionary *event in [[_head arrayByAddingObjectsFromArray:_ring] arrayByAddingObjectsFromArray:_milestones.allValues])if(event[@"sequence"])unique[event[@"sequence"]]=event;
    NSMutableArray *result=[NSMutableArray array];for(NSNumber *key in [unique.allKeys sortedArrayUsingSelector:@selector(compare:)])[result addObject:unique[key]];return result;
}
- (NSDictionary *)summary {
    [self sync];NSData *trace=[NSData dataWithContentsOfURL:_allocationURL]?:[NSData data];
    return @{@"policy":@"bounded_v1",@"total_events":@(_totalCount),@"retained_events":@([self snapshot].count),@"retained_milestones":@(_milestones.count),@"milestone_limit_bytes":@(2*CJMemoryLimit),@"routine_event_counts":[_counts copy],@"routine_samples":[_samples copy],@"evicted_selected_events":@(_evicted),@"oversize_events":@(_oversize),@"journal_rotations":@(_rotations),@"journal_part_limit_bytes":@(CJJournalLimit),@"ring_limit_bytes":@(CJMemoryLimit),@"fsync_checkpoints":@(_fsyncCount),@"allocation_trace":@{@"encoding":@"base64 of packed little-endian uint64 (address, requested_bytes, total_reserved_bytes)",@"records":@(_allocations),@"overflow_records":@(_allocationOverflow),@"bytes":@(trace.length),@"sha256":CJDigest(trace),@"base64":[trace base64EncodedStringWithOptions:0]},@"storage_error":_error?:NSNull.null};
}
@end
NSDictionary *CJReadBoundedJournal(NSURL *url) {
    NSFileHandle *f=[NSFileHandle fileHandleForReadingFromURL:url error:NULL];if(!f)return @{@"events":@[],@"unreadable":@YES};
    unsigned long long size=[f seekToEndOfFile];[f seekToFileOffset:0];
    const NSUInteger prefix=512*1024,tail=1024*1024;
    NSData *first=[f readDataOfLength:MIN(size,prefix)],*last=nil;
    BOOL clipped=size>prefix+tail;
    if(size>prefix){[f seekToFileOffset:clipped?size-tail:prefix];last=[f readDataToEndOfFile];}[f closeFile];
    NSMutableArray *records=[NSMutableArray array];NSUInteger invalid=0;
    if(!clipped && last){NSMutableData *both=[first mutableCopy];[both appendData:last];first=both;last=nil;}
    NSArray *chunks=last?@[first,last]:@[first];
    for(NSUInteger part=0;part<chunks.count;part++){
        NSData *chunk=chunks[part];
        if(clipped){const uint8_t *bytes=chunk.bytes;NSUInteger start=0,end=chunk.length;
            if(part==0){while(end && bytes[end-1]!='\n')end--;}
            else {while(start<end && bytes[start]!='\n')start++;if(start<end)start++;}
            chunk=[chunk subdataWithRange:NSMakeRange(start,end-start)];
        }
        NSString *text=[[NSString alloc] initWithData:chunk encoding:NSUTF8StringEncoding];
        if(!text){invalid++;continue;}NSArray *lines=[text componentsSeparatedByString:@"\n"];
        for(NSUInteger i=0;i<lines.count;i++){if([lines[i] length]==0)continue;
            id e=[NSJSONSerialization JSONObjectWithData:[lines[i] dataUsingEncoding:NSUTF8StringEncoding] options:0 error:NULL];if([e isKindOfClass:NSDictionary.class])[records addObject:e];else invalid++;
        }
    }
    return @{@"events":records,@"source_bytes":@(size),@"bounded_excerpt":@(clipped),@"invalid_or_partial_lines":@(invalid)};
}
