#import "CJModStore.h"
#import "CJEventStore.h"
#import "CJFrameMetrics.h"
#import "CJLauncher-Swift.h"
// Game-stage launcher fork of the accepted build 11 host. G1/G2 sources remain immutable.
#import <UIKit/UIKit.h>
#import <Foundation/Foundation.h>
#import <mach/mach.h>
#import <mach/vm_map.h>
#import <libkern/OSCacheControl.h>
#import <CommonCrypto/CommonDigest.h>
#import <sys/sysctl.h>
#import <sys/utsname.h>
#import <sys/stat.h>
#import <fcntl.h>
#import <unistd.h>
#import <errno.h>
#import <pthread.h>
#import <stdatomic.h>
#import <TargetConditionals.h>
#import "CJHookProtocol.h"
#import "VMRange.h"
#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>
#import "CJCodeArena.h"
#import "CJGraphicsManaged.h"
#import "CJGraphicsPlatform.h"
#import "CJContentImport.h"
#import <QuartzCore/QuartzCore.h>

extern int csops(pid_t pid, unsigned int operations, void *useraddr, size_t usersize);
static const uint32_t CJDebuggedFlag = 0x10000000;
static CJMailbox gMailbox;
static BOOL gLandscapeOnly=NO;
static CJFrameMetrics __attribute__((unused)) gFrameMetrics;

static NSString *CJHex(const void *bytes, size_t count) {
    const uint8_t *p = bytes;
    NSMutableString *s = [NSMutableString stringWithCapacity:count * 2];
    for (size_t i = 0; i < count; i++) [s appendFormat:@"%02x", p[i]];
    return s;
}
static NSString *CJSHA256(NSData *data) {
    unsigned char digest[CC_SHA256_DIGEST_LENGTH];
    CC_SHA256(data.bytes, (CC_LONG)data.length, digest);
    return CJHex(digest, sizeof(digest));
}
static NSDictionary *CJProtocolConfiguration(void) {
    return @{@"protocol": @(CJCompiledProtocol.version), @"bytes_per_arena": @(CJCompiledProtocol.arenaLength),
             @"arena_count": @2, @"mailbox_bytes": @(CJCompiledProtocol.mailboxBytes),
             @"response_offset": @(CJCompiledProtocol.responseOffset), @"error_offset": @(CJCompiledProtocol.errorOffset)};
}
static NSDictionary *CJCreateJITRequest(CJMailbox *mailbox, uint64_t pid, size_t pageSize, NSString *requestID) {
    memset(mailbox, 0, sizeof(*mailbox));
    memcpy(mailbox->magic, "CJT0MBX1", 8);
    mailbox->version = CJCompiledProtocol.version;
    arc4random_buf(mailbox->nonce, sizeof(mailbox->nonce));
    mailbox->pid = pid; mailbox->requestedLength = CJCompiledProtocol.arenaLength; mailbox->status = 1;
    return @{@"protocol": @(mailbox->version), @"pid": @(pid),
             @"mailbox": [NSString stringWithFormat:@"0x%llx", (unsigned long long)(uintptr_t)mailbox],
             @"header": CJHex(mailbox, CJCompiledProtocol.responseOffset), @"length": @(mailbox->requestedLength),
             @"pageSize": @(pageSize), @"requestID": requestID};
}
static NSString *CJBindJITScript(NSDictionary *request, NSString *source) {
    NSData *json = [NSJSONSerialization dataWithJSONObject:request options:NSJSONWritingSortedKeys error:NULL];
    if (!json || !source) return nil;
    return [NSString stringWithFormat:@"const CJIT_REQUEST = %@;\n%@", [[NSString alloc] initWithData:json encoding:NSUTF8StringEncoding], source];
}
static NSString *CJConsoleTail(NSURL *directory, NSString *session) {
    NSURL *url = [directory URLByAppendingPathComponent:[NSString stringWithFormat:@"console-%@.txt", session]];
    NSFileHandle *file = [NSFileHandle fileHandleForReadingFromURL:url error:NULL];
    if (!file) return @"";
    unsigned long long length = [file seekToEndOfFile];
    [file seekToFileOffset:length > 131072 ? length - 131072 : 0];
    NSData *data = [file readDataToEndOfFile]; [file closeFile];
    return [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding] ?: @"Console contained non-UTF8 data; retrieve its file separately.";
}

static NSDictionary *CJProcessState(void) {
    uint32_t flags = 0;
    errno = 0;
    int csResult = csops(getpid(), 0, &flags, sizeof(flags));
    int csError = csResult == 0 ? 0 : errno;
    struct kinfo_proc process = {0};
    int mib[] = {CTL_KERN, KERN_PROC, KERN_PROC_PID, getpid()};
    size_t size = sizeof(process);
    errno = 0;
    int sysResult = sysctl(mib, 4, &process, &size, NULL, 0);
    int sysError = sysResult == 0 ? 0 : errno;
    BOOL known = sysResult == 0 && size == sizeof(process);
    return @{@"pid": @(getpid()), @"csops_result": @(csResult), @"csops_errno": @(csError),
             @"code_sign_flags": [NSString stringWithFormat:@"0x%08x", flags],
             @"cs_debugged": @(csResult == 0 && (flags & CJDebuggedFlag) != 0),
             @"get_task_allow_flag": @(csResult == 0 && (flags & 4) != 0),
             @"trace_known": @(known), @"traced": @(known && (process.kp_proc.p_flag & P_TRACED) != 0),
             @"sysctl_errno": @(sysError), @"sysctl_returned_bytes": @(size),
             @"kernel_process_name": known ? ([NSString stringWithUTF8String:process.kp_proc.p_comm] ?: @"unknown") : @"unknown"};
}

@interface CJLog : NSObject
@property(nonatomic) dispatch_queue_t queue;
@property(nonatomic) int fd;
@property(nonatomic, strong) NSURL *directory;
@property(nonatomic, strong) NSURL *sessionURL;
@property(nonatomic, strong) NSString *sessionID;
@property(nonatomic, strong) CJEventStore *store;
@property(nonatomic, strong) NSDictionary *buildInfo;
@property(nonatomic, strong) NSDictionary *deviceInfo;
@property(nonatomic, strong) NSString *storageError;
+ (instancetype)shared;
- (void)event:(NSString *)name fields:(NSDictionary *)fields;
- (NSArray *)snapshot;
- (NSURL *)exportDiagnostics;
@end

@implementation CJLog
+ (instancetype)shared {
    static CJLog *instance;
    static dispatch_once_t once;
    dispatch_once(&once, ^{ instance = [CJLog new]; });
    return instance;
}
- (instancetype)init {
    if (!(self = [super init])) return nil;
    _queue = dispatch_queue_create("celeste.probe.log", DISPATCH_QUEUE_SERIAL);
    _fd = -1;
    _sessionID = [[NSUUID UUID].UUIDString lowercaseString];
    NSURL *documents = [NSFileManager.defaultManager URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask].firstObject;
    _directory = [documents URLByAppendingPathComponent:@"Diagnostics" isDirectory:YES];
    NSError *error;
    if (![NSFileManager.defaultManager createDirectoryAtURL:_directory withIntermediateDirectories:YES attributes:@{NSFileProtectionKey: NSFileProtectionCompleteUntilFirstUserAuthentication} error:&error]) {
        _storageError = error.localizedDescription;
    }
    _sessionURL = [_directory URLByAppendingPathComponent:[NSString stringWithFormat:@"session-%@.jsonl", _sessionID]];
    _store = [[CJEventStore alloc] initWithURL:_sessionURL];
    _fd = _store.error ? -1 : 1;
    if (_store.error) _storageError = _store.error;
    NSURL *consoleURL = [_directory URLByAppendingPathComponent:[NSString stringWithFormat:@"console-%@.txt", _sessionID]];
    int console = open(consoleURL.fileSystemRepresentation, O_WRONLY | O_CREAT | O_APPEND, 0600);
    if (console >= 0) {
        dup2(console, STDOUT_FILENO); dup2(console, STDERR_FILENO); close(console);
        setvbuf(stdout, NULL, _IONBF, 0); setvbuf(stderr, NULL, _IONBF, 0);
    } else _storageError = @"Could not open the native runtime console log";
    NSData *buildData = [NSData dataWithContentsOfURL:[NSBundle.mainBundle URLForResource:@"BuildInfo" withExtension:@"json"]];
    _buildInfo = buildData ? [NSJSONSerialization JSONObjectWithData:buildData options:0 error:NULL] : @{};
    struct utsname machine;
    uname(&machine);
    _deviceInfo = @{@"hardware": [NSString stringWithUTF8String:machine.machine],
                    @"os_version": UIDevice.currentDevice.systemVersion,
                    @"os_build_description": NSProcessInfo.processInfo.operatingSystemVersionString,
                    @"page_size": @(getpagesize()), @"simulator": @(TARGET_OS_SIMULATOR),
                    @"guest_bundle_id": NSBundle.mainBundle.bundleIdentifier ?: @"unknown",
                    @"physical_memory_bytes": @(NSProcessInfo.processInfo.physicalMemory)};
    [self event:@"native_launch" fields:@{@"build": _buildInfo ?: @{}, @"device": _deviceInfo, @"process": CJProcessState(), @"persistent_log_available": @(_fd >= 0)}];
    [self event:@"compiled_jit_protocol" fields:CJProtocolConfiguration()];
    return self;
}
- (void)event:(NSString *)name fields:(NSDictionary *)fields {
    NSDictionary *entry = @{@"event": name, @"time_unix": @([NSDate date].timeIntervalSince1970),
                            @"uptime_seconds": @(NSProcessInfo.processInfo.systemUptime),
                            @"session": _sessionID, @"fields": fields ?: @{}};
    __block BOOL console=NO;
    dispatch_sync(_queue, ^{ console=[self.store append:entry]; if(self.store.error)self.storageError=self.store.error; });
    if(console && ![name isEqualToString:@"native_launch"]) NSLog(@"[CelesteJIT] %@ %@", name, fields ?: @{});
}
- (NSArray *)snapshot {
    __block NSArray *result;
    dispatch_sync(_queue, ^{ result=[self.store snapshot]; });
    return result;
}
- (NSUInteger)eventCount { __block NSUInteger count;dispatch_sync(_queue,^{count=self.store.totalCount;});return count; }
- (NSDictionary *)retention {
    __block NSDictionary *result;dispatch_sync(_queue,^{result=[self.store summary];});return result;
}
- (NSURL *)exportDiagnostics {
    [self event:@"diagnostics_export" fields:@{}];
    NSMutableArray *previous = [NSMutableArray array];
    NSArray<NSURL *> *files = [NSFileManager.defaultManager contentsOfDirectoryAtURL:_directory includingPropertiesForKeys:@[NSURLContentModificationDateKey] options:0 error:NULL];
    files = [files sortedArrayUsingComparator:^NSComparisonResult(NSURL *a, NSURL *b) {
        NSDate *da, *db;
        [a getResourceValue:&da forKey:NSURLContentModificationDateKey error:NULL];
        [b getResourceValue:&db forKey:NSURLContentModificationDateKey error:NULL];
        return [(db ?: NSDate.distantPast) compare:(da ?: NSDate.distantPast)];
    }];
    for (NSURL *url in files) {
        // LiveContainer can expose /var and /private/var aliases for the same
        // file. URL object equality did not reliably exclude the current log.
        if (![url.pathExtension isEqualToString:@"jsonl"] || [url.lastPathComponent isEqualToString:_sessionURL.lastPathComponent] || previous.count >= 3) continue;
        NSDictionary *excerpt=CJReadBoundedJournal(url);
        NSArray *records=excerpt[@"events"];
        if ([records.firstObject[@"session"] isEqualToString:_sessionID]) continue;
        NSMutableDictionary *prior=[excerpt mutableCopy];prior[@"file"]=url.lastPathComponent;
        NSString *session=records.firstObject[@"session"]?:@"unknown";
        prior[@"native_console_tail"]=CJConsoleTail(_directory,session);
        NSURL *older=[url URLByAppendingPathExtension:@"previouspart"];
        if([NSFileManager.defaultManager fileExistsAtPath:older.path])prior[@"previous_journal_part"]=CJReadBoundedJournal(older);
        [previous addObject:prior];
    }
    NSUserDefaults *settings = NSUserDefaults.standardUserDefaults;
    NSDictionary *bundle = @{@"schema": @2, @"kind": @"celeste-jit-launcher-diagnostics",
                             @"session": _sessionID, @"build": _buildInfo ?: @{}, @"device": _deviceInfo,
                             @"reported_livecontainer_version": [settings stringForKey:@"livecontainerVersion"] ?: @"not supplied",
                             @"reported_stikdebug_version": [settings stringForKey:@"stikdebugVersion"] ?: @"not supplied",
                             @"reported_stikdebug_install": [settings stringForKey:@"stikdebugInstall"] ?: @"not supplied",
                             @"storage_error": _storageError ?: NSNull.null,
                             @"current_events": [self snapshot], @"retention": [self retention], @"previous_sessions": previous,
                             @"native_console_tail": CJConsoleTail(_directory, _sessionID),
                             @"scope": @"Native mod catalogue and normal play. Counts cover routine events; bounded samples and journal excerpts are explicit. Allocation trace is separate and complete unless overflow is nonzero."};
    NSData *data = [NSJSONSerialization dataWithJSONObject:bundle options:NSJSONWritingPrettyPrinted | NSJSONWritingSortedKeys error:NULL];
    NSURL *url = [_directory URLByAppendingPathComponent:[NSString stringWithFormat:@"CelesteJIT-%@.diagnostics.json", _sessionID]];
    return [data writeToURL:url options:NSDataWritingAtomic error:NULL] ? url : nil;
}
@end

static void CJEvent(NSString *name, NSDictionary *fields) { [[CJLog shared] event:name fields:fields]; }
static void __attribute__((unused)) CJAllocatorEvent(const char *name, uintptr_t address, size_t length, size_t used) {
    CJEvent([NSString stringWithUTF8String:name], @{@"address": [NSString stringWithFormat:@"0x%llx", (unsigned long long)address],
                                                  @"requested_bytes": @(length), @"total_reserved_bytes": @(used), @"code_budget_bytes": @(CJ_HOOK_CODE_BUDGET)});
}

#if !TARGET_OS_SIMULATOR
typedef struct { __unsafe_unretained NSMutableArray *first; __unsafe_unretained NSMutableArray *last; CC_SHA256_CTX digest; size_t count; } CJVMTrace;
static void CJRecordVMEntry(uintptr_t cursor, const CJVMEntry *entry, size_t checked, void *context) {
    CJVMTrace *trace=context;
    uint64_t row[]={cursor,entry->address,entry->length,checked,(uint64_t)entry->protection,(uint64_t)entry->maximum_protection};
    CC_SHA256_Update(&trace->digest,row,sizeof(row));trace->count++;
    @autoreleasepool {
    NSDictionary *sample=@{@"query_address":[NSString stringWithFormat:@"0x%llx",(unsigned long long)cursor],@"region_start":[NSString stringWithFormat:@"0x%llx",(unsigned long long)entry->address],@"region_bytes":@(entry->length),@"checked_bytes":@(checked),@"protection":@(entry->protection),@"maximum_protection":@(entry->maximum_protection)};
    if(trace->first.count<8)[trace->first addObject:sample];
    else {if(trace->last.count==8)[trace->last removeObjectAtIndex:0];[trace->last addObject:sample];}
    }
}
static NSDictionary *CJRegion(uintptr_t pointer, size_t needed) {
    NSMutableArray *first=[NSMutableArray array],*last=[NSMutableArray array];CJVMTrace trace={.first=first,.last=last};CC_SHA256_Init(&trace.digest);
    CJVMRangeReport report=CJInspectVMRange(pointer,needed,CJQueryDarwinVMEntry,NULL,CJRecordVMEntry,&trace);
    unsigned char digest[CC_SHA256_DIGEST_LENGTH];CC_SHA256_Final(digest,&trace.digest);NSMutableString *hash=[NSMutableString string];for(unsigned i=0;i<sizeof(digest);i++)[hash appendFormat:@"%02x",digest[i]];
    NSArray *samples=[first arrayByAddingObjectsFromArray:last];
    return @{@"address":[NSString stringWithFormat:@"0x%llx",(unsigned long long)pointer],@"result":@(report.query_result),@"range_status":[NSString stringWithUTF8String:CJVMRangeStatusName(report.status)],@"covers_requested_bytes":@(report.status==CJVMRangeComplete),@"protection":@(report.common_protection),@"union_protection":@(report.union_protection),@"maximum_protection":@(report.maximum_protection_intersection),@"requested_bytes":@(needed),@"mapped_bytes":@(report.covered_bytes),@"entry_count":@(report.entry_count),@"entry_limit":@(report.entry_limit),@"page_bytes":@((size_t)getpagesize()),@"entry_trace_count":@(trace.count),@"entry_trace_sha256":hash,@"entry_trace_encoding":@"six little-endian uint64: query,start,length,checked,current,max",@"entries_sampled":@YES,@"entries":samples};
}

typedef struct { uintptr_t rx, rw; size_t length; } CJArena;
static CJArena gArenas[2];

static BOOL CJCheck(BOOL condition, NSString *check, NSDictionary *details) {
    CJEvent(condition ? @"check_pass" : @"check_fail", @{@"check": check, @"details": details ?: @{}});
    return condition;
}

static BOOL CJMapArena(CJArena *arena, uint64_t rx, size_t length, int index) {
    NSDictionary *before = CJRegion(rx, length);
    if (!CJCheck([before[@"covers_requested_bytes"] boolValue] && [before[@"protection"] intValue] == (VM_PROT_READ | VM_PROT_EXECUTE), @"prepared_region_is_rx", before)) return NO;
    vm_address_t rw = 0;
    vm_prot_t current = 0, maximum = 0;
    kern_return_t result = vm_remap(mach_task_self(), &rw, length, 0, VM_FLAGS_ANYWHERE, mach_task_self(), rx, FALSE, &current, &maximum, VM_INHERIT_NONE);
    CJEvent(@"vm_remap", @{@"arena": @(index), @"result": @(result), @"current_protection": @(current), @"maximum_protection": @(maximum)});
    if (!CJCheck(result == KERN_SUCCESS && rw != 0 && rw != rx, @"create_distinct_alias", @{@"result": @(result)})) return NO;
    result = vm_protect(mach_task_self(), rw, length, FALSE, VM_PROT_READ | VM_PROT_WRITE);
    if (!CJCheck(result == KERN_SUCCESS, @"protect_writable_alias", @{@"result": @(result)})) { vm_deallocate(mach_task_self(), rw, length); return NO; }
    NSDictionary *rxInfo = CJRegion(rx, length), *rwInfo = CJRegion(rw, length);
    BOOL valid = [rxInfo[@"covers_requested_bytes"] boolValue] && [rwInfo[@"covers_requested_bytes"] boolValue] &&
                 [rxInfo[@"protection"] intValue] == (VM_PROT_READ | VM_PROT_EXECUTE) &&
                 [rwInfo[@"protection"] intValue] == (VM_PROT_READ | VM_PROT_WRITE);
    if (!CJCheck(valid, @"wx_separate_aliases", @{@"rx": rxInfo, @"rw": rwInfo})) { vm_deallocate(mach_task_self(), rw, length); return NO; }
    *arena = (CJArena){rx, rw, length};
    return YES;
}

static void CJEmit(CJArena *arena, size_t offset, const void *bytes, size_t count) {
    NSCAssert(offset <= arena->length && count <= arena->length - offset, @"Emitter exceeds arena");
    memcpy((void *)(arena->rw + offset), bytes, count);
    sys_dcache_flush((void *)(arena->rw + offset), count);
    sys_icache_invalidate((void *)(arena->rx + offset), count);
}
static void CJReturnConstant(CJArena *arena, size_t offset, uint16_t value) {
    // movz w0, #imm16; ret. Verified by the host assembler/disassembler check.
    const uint32_t code[] = {0x52800000U | ((uint32_t)value << 5), 0xd65f03c0U};
    CJEmit(arena, offset, code, sizeof(code));
}
static int CJCall(CJArena *arena, size_t offset) { return ((int (*)(void))(arena->rx + offset))(); }
#endif

static BOOL CJRunNativeChecks(void) {
#if TARGET_OS_SIMULATOR
    CJEvent(@"simulator_execution_skipped", @{});
    return NO;
#else
    NSDictionary *state = CJProcessState();
    if (!CJCheck([state[@"trace_known"] boolValue] && ![state[@"traced"] boolValue] && [state[@"cs_debugged"] boolValue], @"debugger_detached_before_execution", state)) return NO;
    uint64_t first = gMailbox.rx1, second = gMailbox.rx2, length = gMailbox.length;
    uint64_t limit = 1ULL << 48;
    BOOL bounds = first > 0 && second > 0 && first < limit - CJ_HOOK_ARENA_LENGTH && second < limit - CJ_HOOK_ARENA_LENGTH &&
                  length == CJ_HOOK_ARENA_LENGTH && getpagesize() == 16384 && first % getpagesize() == 0 && second % getpagesize() == 0 &&
                  (first + length <= second || second + length <= first);
    if (!CJCheck(bounds && gMailbox.scriptVersion == 1 && gMailbox.error == 0, @"mailbox_response_valid", @{@"script_version": @(gMailbox.scriptVersion), @"length": @(length)})) return NO;
    for (int i = 0; i < 2; i++) {
        if (!gArenas[i].rw && !CJMapArena(&gArenas[i], i == 0 ? first : second, length, i + 1)) return NO;
        NSDictionary *rx = CJRegion(gArenas[i].rx, length), *rw = CJRegion(gArenas[i].rw, length);
        if (!CJCheck([rx[@"covers_requested_bytes"] boolValue] && [rw[@"covers_requested_bytes"] boolValue] &&
                     [rx[@"protection"] intValue] == 5 && [rw[@"protection"] intValue] == 3, @"mapping_still_valid", @{@"arena": @(i + 1), @"rx": rx, @"rw": rw})) return NO;
    }
    for (int i = 0; i < 2; i++) {
        CJArena *arena = &gArenas[i];
        uint16_t value = (uint16_t)(1000 + arc4random_uniform(30000));
        CJReturnConstant(arena, 0, value);
        if (!CJCheck(memcmp((void *)arena->rx, (void *)arena->rw, 8) == 0, @"aliases_share_bytes", @{@"arena": @(i + 1)})) return NO;
        CJEvent(@"about_to_execute_generated_code", @{@"arena": @(i + 1), @"expected": @(value)});
        int actual = CJCall(arena, 0);
        if (!CJCheck(actual == value, @"execute_generated_constant", @{@"arena": @(i + 1), @"expected": @(value), @"actual": @(actual)})) return NO;
        value += 100;
        CJReturnConstant(arena, 0, value);
        CJEvent(@"about_to_execute_patched_code", @{@"arena": @(i + 1), @"expected": @(value)});
        actual = CJCall(arena, 0);
        if (!CJCheck(actual == value, @"patched_instruction_cache_visible", @{@"arena": @(i + 1), @"expected": @(value), @"actual": @(actual)})) return NO;
        CJEvent(@"about_to_execute_all_prepared_pages", @{@"arena": @(i + 1)});
        for (size_t offset = 0; offset < length; offset += (size_t)getpagesize()) {
            uint16_t expected = (uint16_t)(100 + offset / getpagesize());
            CJReturnConstant(arena, offset + 64, expected);
            if (CJCall(arena, offset + 64) != expected) return CJCheck(NO, @"execute_prepared_page", @{@"arena": @(i + 1), @"page": @(offset / getpagesize())});
        }
        CJCheck(YES, @"all_prepared_pages_executed", @{@"arena": @(i + 1), @"pages": @(length / getpagesize())});
        CJReturnConstant(arena, length - 8, 777);
        CJEvent(@"about_to_execute_arena_end", @{@"arena": @(i + 1)});
        if (!CJCheck(CJCall(arena, length - 8) == 777, @"arena_end_executable", @{@"arena": @(i + 1)})) return NO;
    }
    const uint32_t addCode[] = {0x11001c00U, 0xd65f03c0U}; // add w0,w0,#7; ret
    CJEmit(&gArenas[0], 128, addCode, sizeof(addCode));
    CJEvent(@"about_to_execute_with_argument", @{});
    int (*add)(int) = (int (*)(int))(gArenas[0].rx + 128);
    if (!CJCheck(add(-11) == -4 && add(35) == 42, @"integer_argument_and_return", @{})) return NO;
    CJReturnConstant(&gArenas[1], 128, 321);
    uint8_t trampoline[16];
    const uint32_t jump[] = {0x58000050U, 0xd61f0200U}; // ldr x16, PC+8; br x16
    uint64_t destination = gArenas[1].rx + 128;
    memcpy(trampoline, jump, 8); memcpy(trampoline + 8, &destination, 8);
    CJEmit(&gArenas[0], 256, trampoline, sizeof(trampoline));
    CJEvent(@"about_to_execute_cross_arena_branch", @{});
    if (!CJCheck(CJCall(&gArenas[0], 256) == 321, @"cross_arena_generated_branch", @{})) return NO;
    // This tests a generated branch, not MonoMod or a managed method hook.
    CJEvent(@"about_to_execute_on_another_thread", @{});
    __block int threaded = 0;
    uint64_t callingThread = 0;
    __block uint64_t workerThread = 0;
    pthread_threadid_np(NULL, &callingThread);
    dispatch_group_t group = dispatch_group_create();
    dispatch_group_async(group, dispatch_get_global_queue(QOS_CLASS_UTILITY, 0), ^{
        pthread_threadid_np(NULL, &workerThread); threaded = CJCall(&gArenas[0], 256);
    });
    dispatch_group_wait(group, DISPATCH_TIME_FOREVER);
    if (!CJCheck(threaded == 321 && callingThread != 0 && workerThread != 0 && workerThread != callingThread,
                 @"execute_on_another_thread", @{@"actual": @(threaded), @"caller_thread": @(callingThread), @"worker_thread": @(workerThread)})) return NO;
    CJEvent(@"about_to_run_rewrite_stress", @{@"rewrites": @128, @"calls_per_rewrite": @128});
    for (int rewrite = 0; rewrite < 128; rewrite++) {
        uint16_t expected = (uint16_t)(200 + rewrite);
        CJReturnConstant(&gArenas[0], 512, expected);
        for (int call = 0; call < 128; call++) {
            if (CJCall(&gArenas[0], 512) != expected) return CJCheck(NO, @"rewrite_stress", @{@"rewrite": @(rewrite), @"call": @(call)});
        }
    }
    return CJCheck(YES, @"rewrite_stress", @{@"rewrites": @128, @"executions": @16384});
#endif
}

@interface CJViewController : UIViewController <UIDocumentPickerDelegate>
@property(nonatomic, strong) CJLauncherBridge *launcherBridge;
@property(nonatomic, strong) CJModLibrary *modLibrary;
@property(nonatomic, strong) NSDictionary *librarySnapshot;
@property(nonatomic) BOOL regressionMode;
@property(nonatomic) NSUInteger orientationWaits;
@property(nonatomic, strong) UIButton *dllButton;
@property(nonatomic, strong) NSURL *importedDLL;
@property(nonatomic) BOOL nativePassed;
@property(nonatomic) BOOL runtimeReady;
@property(nonatomic) BOOL choosingContent;
@property(nonatomic, strong) UIButton *contentButton;
@property(nonatomic, strong) UIButton *cancelContentButton;
@property(nonatomic, strong) NSTimer *contentTimer;
@property(nonatomic) BOOL managedAttempted;
@property(nonatomic) BOOL graphicsRunning;
@property(nonatomic) BOOL graphicsReady;
@property(nonatomic) BOOL graphicsPaused;
@property(nonatomic) BOOL graphicsFailed;
@property(nonatomic, copy) NSString *graphicsStopReason;
@property(nonatomic) BOOL finishing;
@property(nonatomic) NSTimeInterval gameBackgroundUptime;
@property(nonatomic) NSTimeInterval completedBackgroundSeconds;
@property(nonatomic) NSTimeInterval lastFrameTimestamp;
@property(nonatomic) double maximumFrameGap;
@property(nonatomic) NSUInteger frameCallbacks;
@property(nonatomic, strong) CADisplayLink *displayLink;
@property(nonatomic, strong) UIView *graphicsOverlay;
@property(nonatomic, strong) UILabel *graphicsLabel;
@property(nonatomic, strong) UIWindow *launcherWindow;
@property(nonatomic, strong) UIStackView *stack;
@property(nonatomic, strong) UILabel *statusLabel;
@property(nonatomic, strong) UILabel *detailLabel;
@property(nonatomic, strong) UILabel *processLabel;
@property(nonatomic, strong) UITextView *logView;
@property(nonatomic) NSUInteger renderedEventCount;
@property(nonatomic, strong) UIButton *enableButton;
@property(nonatomic, strong) UIButton *scriptButton;
@property(nonatomic, strong) UIButton *importedButton;
@property(nonatomic, strong) UIButton *runButton;
@property(nonatomic, strong) NSTimer *timer;
@property(nonatomic, strong) NSString *sessionScript;
@property(nonatomic, strong) NSDate *requestTime;
@property(nonatomic) BOOL busy;
@property(nonatomic) BOOL uiBurstStarted;
@property(nonatomic) BOOL uiExported;
@property(nonatomic,strong) CJModDownloader *modDownloader;
@property(nonatomic,strong) UIButton *downloadButton;
@property(nonatomic,strong) UIButton *cancelDownloadButton;
@property(nonatomic) BOOL attempted;
@property(nonatomic) BOOL timeoutLogged;
@property(nonatomic) uint64_t lastMailboxStatus;
@property(nonatomic) UIBackgroundTaskIdentifier backgroundTask;
@end

@implementation CJViewController
- (UILabel *)label:(NSString *)text size:(CGFloat)size weight:(UIFontWeight)weight {
    UILabel *label = [UILabel new];
    label.text = text; label.font = [UIFont systemFontOfSize:size weight:weight];
    label.textColor = UIColor.labelColor; label.numberOfLines = 0;
    return label;
}
- (UIButton *)button:(NSString *)title action:(SEL)action prominent:(BOOL)prominent {
    UIButtonConfiguration *configuration = prominent ? UIButtonConfiguration.filledButtonConfiguration : UIButtonConfiguration.tintedButtonConfiguration;
    configuration.title = title;
    configuration.cornerStyle = UIButtonConfigurationCornerStyleMedium;
    configuration.baseBackgroundColor = [UIColor colorWithRed:0.9 green:0.27 blue:0.39 alpha:1];
    configuration.baseForegroundColor = prominent ? UIColor.whiteColor : [UIColor colorWithRed:1 green:0.63 blue:0.68 alpha:1];
    configuration.contentInsets = NSDirectionalEdgeInsetsMake(14, 16, 14, 16);
    UIButton *button = [UIButton buttonWithConfiguration:configuration primaryAction:nil];
    [button addTarget:self action:action forControlEvents:UIControlEventTouchUpInside];
    return button;
}
- (void)viewDidLoad {
    [super viewDidLoad];
    self.overrideUserInterfaceStyle = UIUserInterfaceStyleDark;
    self.view.backgroundColor = [UIColor colorWithRed:0.055 green:0.063 blue:0.09 alpha:1];
    self.backgroundTask = UIBackgroundTaskInvalid;
    UIScrollView *scroll = [UIScrollView new]; scroll.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:scroll];
    self.stack = [UIStackView new]; self.stack.axis = UILayoutConstraintAxisVertical; self.stack.spacing = 14;
    self.stack.translatesAutoresizingMaskIntoConstraints = NO; [scroll addSubview:self.stack];
    [NSLayoutConstraint activateConstraints:@[
        [scroll.topAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.topAnchor],
        [scroll.bottomAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.bottomAnchor],
        [scroll.leadingAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.leadingAnchor], [scroll.trailingAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.trailingAnchor],
        [self.stack.topAnchor constraintEqualToAnchor:scroll.contentLayoutGuide.topAnchor constant:24],
        [self.stack.bottomAnchor constraintEqualToAnchor:scroll.contentLayoutGuide.bottomAnchor constant:-24],
        [self.stack.leadingAnchor constraintEqualToAnchor:scroll.contentLayoutGuide.leadingAnchor constant:24],
        [self.stack.trailingAnchor constraintEqualToAnchor:scroll.contentLayoutGuide.trailingAnchor constant:-24],
        [self.stack.widthAnchor constraintEqualToAnchor:scroll.frameLayoutGuide.widthAnchor constant:-48]]];
    UILabel *eyebrow = [self label:@"CELESTE  /  JIT RESEARCH" size:12 weight:UIFontWeightSemibold];
    eyebrow.textColor = [UIColor colorWithRed:1 green:0.55 blue:0.63 alpha:1];
    [self.stack addArrangedSubview:eyebrow];
    [self.stack addArrangedSubview:[self label:@"Celeste + Everest" size:31 weight:UIFontWeightBold]];
    [self.stack addArrangedSubview:[self label:@"Import your game once. Keep your files, mods and saves between app updates." size:17 weight:UIFontWeightRegular]];
    self.statusLabel = [self label:@"READY · IMPORT GAME FILES" size:19 weight:UIFontWeightBold];
    self.statusLabel.accessibilityIdentifier = @"probe.status";
    [self.stack addArrangedSubview:self.statusLabel];
    self.detailLabel = [self label:@"Build 19 · Strawberry Jam. Reuses your Celeste content. Download the original mods once (1.24 GB over Wi-Fi) into a separate profile. LiveContainer: Fix File Picker ON, Launch with JIT OFF." size:15 weight:UIFontWeightRegular];
    self.detailLabel.textColor = UIColor.secondaryLabelColor;
    [self.stack addArrangedSubview:self.detailLabel];
    NSDictionary *process = CJProcessState();
    self.processLabel = [self label:[NSString stringWithFormat:@"PID %@ · %@\niOS %@ · %@", process[@"pid"], process[@"kernel_process_name"], UIDevice.currentDevice.systemVersion, [CJLog shared].buildInfo[@"build_id"] ?: @"unknown build"] size:13 weight:UIFontWeightMedium];
    self.processLabel.font = [UIFont monospacedSystemFontOfSize:12 weight:UIFontWeightRegular];
    self.processLabel.textColor = UIColor.secondaryLabelColor;
    [self.stack addArrangedSubview:self.processLabel];
    self.contentButton = [self button:@"1. Import game ZIP" action:@selector(importContent) prominent:YES];
    self.contentButton.accessibilityIdentifier = @"content.import";
    [self.stack addArrangedSubview:self.contentButton];
    self.cancelContentButton = [self button:@"Cancel import" action:@selector(cancelContent) prominent:NO];
    self.cancelContentButton.hidden = YES;
    [self.stack addArrangedSubview:self.cancelContentButton];
    self.dllButton = [self button:@"2. Import test ZIPs" action:@selector(importDLL) prominent:YES];
    [self.stack addArrangedSubview:self.dllButton];
    self.downloadButton = [self button:@"Download Strawberry Jam (1.24 GB)" action:@selector(downloadMods) prominent:YES];
    self.downloadButton.accessibilityIdentifier=@"mods.download";
    [self.stack addArrangedSubview:self.downloadButton];
    self.cancelDownloadButton = [self button:@"Cancel download" action:@selector(cancelModDownload) prominent:NO];
    self.cancelDownloadButton.hidden=YES;[self.stack addArrangedSubview:self.cancelDownloadButton];
    self.enableButton = [self button:@"3. Enable via LiveContainer 2" action:@selector(enableJIT) prominent:YES];
    self.enableButton.accessibilityIdentifier = @"probe.enable";
    [self.stack addArrangedSubview:self.enableButton];
    UIButton *export = [self button:@"Export diagnostics" action:@selector(exportLogs) prominent:NO];
    export.accessibilityIdentifier = @"probe.export";
    [self.stack addArrangedSubview:export];
    self.runButton = [self button:@"4. Run Celeste + Everest" action:@selector(runManaged) prominent:YES];
    self.runButton.enabled = NO; self.runButton.accessibilityIdentifier = @"probe.run";
    [self.stack addArrangedSubview:self.runButton];
    self.scriptButton = [self button:@"Export session script (manual setup)" action:@selector(exportScript) prominent:NO];
    [self.stack addArrangedSubview:self.scriptButton];
    self.importedButton = [self button:@"Use imported script in LiveContainer 2" action:@selector(enableImportedScript) prominent:NO];
    [self.stack addArrangedSubview:self.importedButton];
    [self.stack addArrangedSubview:[self button:@"Record LiveContainer / StikDebug versions" action:@selector(recordVersions) prominent:NO]];
    [self.stack addArrangedSubview:[self label:@"What this checks" size:18 weight:UIFontWeightSemibold]];
    [self.stack addArrangedSubview:[self label:@"At the title, tap SJ lobby. Explore and jump, then tap Bing and play. Go Home for 30 seconds, return and jump again. Tap Finish and export diagnostics. Your previous helper-test profile is retained." size:14 weight:UIFontWeightRegular]];
    UILabel *scope = [self label:@"Private first-play test of original Strawberry Jam 1.0.12 and its complete pinned dependency set. Other maps and longer sessions still need testing." size:13 weight:UIFontWeightRegular];
    scope.textColor = UIColor.secondaryLabelColor; [self.stack addArrangedSubview:scope];
    [self.stack addArrangedSubview:[self label:@"Live log" size:18 weight:UIFontWeightSemibold]];
    self.logView = [UITextView textViewUsingTextLayoutManager:NO]; self.logView.editable = NO;
    self.logView.font = [UIFont monospacedSystemFontOfSize:11 weight:UIFontWeightRegular];
    self.logView.backgroundColor = [UIColor colorWithWhite:1 alpha:0.045]; self.logView.layer.cornerRadius = 12;
    self.logView.textContainerInset = UIEdgeInsetsMake(12, 10, 12, 10);
    [self.logView.heightAnchor constraintEqualToConstant:235].active = YES;
    [self.stack addArrangedSubview:self.logView];
    [NSNotificationCenter.defaultCenter addObserver:self selector:@selector(foreground) name:UIApplicationDidBecomeActiveNotification object:nil];
    [NSNotificationCenter.defaultCenter addObserver:self selector:@selector(background) name:UIApplicationDidEnterBackgroundNotification object:nil];
    [NSNotificationCenter.defaultCenter addObserver:self selector:@selector(resignActive) name:UIApplicationWillResignActiveNotification object:nil];
    [NSNotificationCenter.defaultCenter addObserver:self selector:@selector(willEnterForeground) name:UIApplicationWillEnterForegroundNotification object:nil];
    self.timer = [NSTimer scheduledTimerWithTimeInterval:0.5 target:self selector:@selector(poll) userInfo:nil repeats:YES];
#if TARGET_OS_SIMULATOR
    self.enableButton.enabled = NO; self.scriptButton.enabled = NO; self.importedButton.enabled = NO;
    self.statusLabel.text = @"SIMULATOR · UI ONLY";
    self.detailLabel.text = @"Simulator preview: game execution and JIT are disabled.";
#endif
    if ([CJLog shared].storageError) {
        self.enableButton.enabled = NO; self.scriptButton.enabled = NO; self.importedButton.enabled = NO;
        self.statusLabel.text = @"LOG STORAGE FAILED"; self.detailLabel.text = [CJLog shared].storageError;
    }
    NSDictionary *manifest=[self modManifest];
    NSMutableDictionary *compatibility=[NSMutableDictionary dictionary],*archiveNames=[NSMutableDictionary dictionary];
    for(NSString *name in manifest){
        NSDictionary *row=manifest[name];if(row[@"sha256"])archiveNames[row[@"sha256"]]=name;
        for(NSString *module in @[@"GravityHelper",@"CollabUtils2",@"FemtoHelper"])
            if([name hasPrefix:[module stringByAppendingString:@"-"]])compatibility[module]=row[@"sha256"];
    }
    self.modLibrary=[[CJModLibrary alloc] initWithProfile:[self modDirectory].URLByDeletingLastPathComponent compatibilityPins:compatibility archiveNames:archiveNames];
    __weak CJViewController *weakView=self;
    self.launcherBridge=[[CJLauncherBridge alloc] initWithAction:^(NSString *action,NSDictionary *fields){[weakView launcherAction:action fields:fields];}];
    UIViewController *front=self.launcherBridge.viewController;
    scroll.hidden=YES;
    [self addChildViewController:front];front.view.translatesAutoresizingMaskIntoConstraints=NO;[self.view addSubview:front.view];
    [NSLayoutConstraint activateConstraints:@[[front.view.topAnchor constraintEqualToAnchor:self.view.topAnchor],[front.view.bottomAnchor constraintEqualToAnchor:self.view.bottomAnchor],[front.view.leadingAnchor constraintEqualToAnchor:self.view.leadingAnchor],[front.view.trailingAnchor constraintEqualToAnchor:self.view.trailingAnchor]]];
    [front didMoveToParentViewController:self];
    self.detailLabel.text=TARGET_OS_SIMULATOR?@"Simulator preview. JIT and game execution require the iPhone.":@"Your existing game files, original SJ mods and saves are retained. Review Mods, enable JIT and play.";
    [self refreshImportedMods];
    [self refreshLog];
#if TARGET_OS_SIMULATOR
    if ([NSProcessInfo.processInfo.arguments containsObject:@"--hook-ui-test-protocol"]) {
        // Run only the shared native request builder. No debugserver, URL open,
        // allocation or generated code is used by this simulator fixture.
        CJMailbox mailbox;
        NSDictionary *request = CJCreateJITRequest(&mailbox, 501, 16384, @"simulator-protocol-regression");
        NSString *source = [NSString stringWithContentsOfURL:[NSBundle.mainBundle URLForResource:@"celeste-jit-probe" withExtension:@"js"] encoding:NSUTF8StringEncoding error:NULL];
        CJEvent(@"host_ui_protocol_request", @{@"request": request, @"mailbox_hex": CJHex(&mailbox, sizeof(mailbox)),
                @"session_script": CJBindJITScript(request, source) ?: @"", @"compiled_protocol": CJProtocolConfiguration(),
                @"simulator": @YES, @"debugger_commands_sent": @0});
    }
    if ([NSProcessInfo.processInfo.arguments containsObject:@"--content-ui-test-stage"]) [self performSimulatorContentImport];
    if ([NSProcessInfo.processInfo.arguments containsObject:@"--canary-ui-test-import"]) [self performSimulatorModImport];

#endif
#if TARGET_OS_SIMULATOR
    if ([NSProcessInfo.processInfo.arguments containsObject:@"--probe-ui-test-export"]) [self exportSimulatorWhenReady];
#endif
}
#if TARGET_OS_SIMULATOR
- (void)performSimulatorContentImport {
    if(self.busy){dispatch_after(dispatch_time(DISPATCH_TIME_NOW,NSEC_PER_SEC/2),dispatch_get_main_queue(),^{[self performSimulatorContentImport];});return;}
    [self stageContent:[[CJLog shared].directory.URLByDeletingLastPathComponent URLByAppendingPathComponent:@"content-ui-fixture.zip"]];
}
- (void)performSimulatorModImport {
    if(self.busy){dispatch_after(dispatch_time(DISPATCH_TIME_NOW,NSEC_PER_SEC/2),dispatch_get_main_queue(),^{[self performSimulatorModImport];});return;}
    NSURL *documents=[CJLog shared].directory.URLByDeletingLastPathComponent;NSMutableArray *fixtures=[NSMutableArray array];
    for(NSString *name in [self modManifest]) [fixtures addObject:[documents URLByAppendingPathComponent:name]];
    UIDocumentPickerViewController *picker=[[UIDocumentPickerViewController alloc] initForOpeningContentTypes:@[UTTypeItem] asCopy:YES];
    [self documentPicker:picker didPickDocumentsAtURLs:fixtures];fprintf(stderr,"CJIT native console recovery sentinel\n");
}
- (void)exportSimulatorWhenReady {
    if(self.uiExported)return;
    BOOL import=[NSProcessInfo.processInfo.arguments containsObject:@"--canary-ui-test-import"];
    if(self.busy || (import && !self.importedDLL)){dispatch_after(dispatch_time(DISPATCH_TIME_NOW,NSEC_PER_SEC/2),dispatch_get_main_queue(),^{[self exportSimulatorWhenReady];});return;}
    BOOL burst=[NSProcessInfo.processInfo.arguments containsObject:@"--canary-ui-test-log-burst"];
    if(burst && !self.uiBurstStarted){
        self.uiBurstStarted=YES;
        dispatch_async(dispatch_get_global_queue(QOS_CLASS_UTILITY,0),^{for(int i=0;i<800;i++)CJEvent(i==799?@"host_ui_burst_complete":@"host_ui_burst",@{@"index":@(i)});dispatch_after(dispatch_time(DISPATCH_TIME_NOW,2*NSEC_PER_SEC),dispatch_get_main_queue(),^{[self exportSimulatorWhenReady];});});return;
    }
    if(burst)CJEvent(@"host_ui_log_burst_check",@{@"rendered_through_burst":@([self.logView.text containsString:@"host_ui_burst_complete"])});
    if(import)CJEvent(@"host_ui_import_check",@{@"imported":@(self.importedDLL!=nil),@"managed_run_disabled_without_jit":@(!self.runButton.enabled)});
    if(import)fprintf(stderr,"CJIT native console recovery sentinel\n");
    self.uiExported=YES;[[CJLog shared] exportDiagnostics];
}
#endif

- (UIInterfaceOrientationMask)supportedInterfaceOrientations { return gLandscapeOnly?UIInterfaceOrientationMaskLandscape:UIInterfaceOrientationMaskAllButUpsideDown; }
- (void)updateLauncher {
    if(!self.launcherBridge)return;
    NSMutableDictionary *state=[(self.librarySnapshot?:@{}) mutableCopy];
    [state addEntriesFromDictionary:@{@"busy":@(self.busy),@"scanning":@(self.librarySnapshot==nil),@"used":@(self.managedAttempted),@"hasContent":@([self contentAvailable]),@"contentStaged":@([NSFileManager.defaultManager fileExistsAtPath:[[self contentStagingDirectory] URLByAppendingPathComponent:@"game-input.zip"].path]),@"jitReady":@(self.nativePassed),@"jitAvailable":@(self.enableButton.enabled && !TARGET_OS_SIMULATOR),@"canRun":@(self.runButton.enabled),@"status":self.statusLabel.text?:@"",@"message":self.detailLabel.text?:@"",@"process":self.processLabel.text?:@"",@"canCancelContent":@(!self.cancelContentButton.hidden),@"canCancelDownload":@(!self.cancelDownloadButton.hidden)}];
    [self.launcherBridge update:state];
}
- (void)launcherAction:(NSString *)action fields:(NSDictionary *)fields {
    CJEvent(@"launcher_ui_action",@{@"action":action,@"fields":fields?:@{},@"busy":@(self.busy),@"runtime_used":@(self.managedAttempted)});
    if([action isEqualToString:@"export"]){[self exportLogs];return;}
    if([action isEqualToString:@"versions"]){[self recordVersions];return;}
    if([action isEqualToString:@"cancelContent"]){[self cancelContent];return;}
    if([action isEqualToString:@"cancelDownload"]){[self cancelModDownload];return;}
    if(self.busy || self.managedAttempted)return;
    if([action isEqualToString:@"content"])[self importContent];
    else if([action isEqualToString:@"mods"])[self importDLL];
    else if([action isEqualToString:@"download"])[self downloadMods];
    else if([action isEqualToString:@"jit"])[self enableJIT];
    else if([action isEqualToString:@"script"])[self exportScript];
    else if([action isEqualToString:@"run"])[self runManaged];
    else if([action isEqualToString:@"refresh"])[self refreshImportedMods];
    else if([action isEqualToString:@"toggle"] || [action isEqualToString:@"all"]){
        self.busy=YES;self.runButton.enabled=NO;[self updateLauncher];
        dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^{
            NSError *error=nil;
            if([action isEqualToString:@"all"])[self.modLibrary setAllEnabled:[fields[@"enabled"] boolValue] error:&error];
            else [self.modLibrary setEnabled:[fields[@"enabled"] boolValue] filename:fields[@"filename"] error:&error];
            NSDictionary *snapshot=error?nil:[self.modLibrary scanWithForce:NO error:&error];
            CJEvent(error?@"launcher_selection_failed":@"launcher_selection_saved",@{@"action":action,@"fields":fields,@"error":error.localizedDescription?:@"",@"snapshot":snapshot?:@{}});
            dispatch_async(dispatch_get_main_queue(),^{
                self.busy=NO;if(snapshot)self.librarySnapshot=snapshot;
                self.importedDLL=[self.librarySnapshot[@"canRun"] boolValue]?[NSBundle.mainBundle.bundleURL URLByAppendingPathComponent:@"Managed/CelesteJITEverest.dll"]:nil;
                self.statusLabel.text=error?@"MOD CHOICES NOT SAVED":@"MOD CHOICES SAVED";
                self.detailLabel.text=error.localizedDescription?:@"These choices will be used when you start Celeste.";
                [self refreshContentStatus];[self updateLauncher];
            });
        });
    }
    [self updateLauncher];
}
- (void)refreshLog {
    NSMutableString *text = [NSMutableString string];
    NSArray *events = [[CJLog shared] snapshot];
    if ([[CJLog shared] eventCount] == self.renderedEventCount) return;
    self.renderedEventCount = [[CJLog shared] eventCount];
    NSUInteger start = events.count > 45 ? events.count - 45 : 0;
    for (NSUInteger i = start; i < events.count; i++) {
        NSDictionary *event = events[i];
        [text appendFormat:@"%@ %@\n", event[@"event"], event[@"fields"][@"check"] ?: @""];
    }
    self.logView.text = text;
    if (text.length) [self.logView scrollRangeToVisible:NSMakeRange(text.length - 1, 1)];
}
- (BOOL)makeRequest {
    if (self.sessionScript) return YES;
    if (getpagesize() != 16384 || TARGET_OS_SIMULATOR || [CJLog shared].storageError) return NO;
    if ([CJLog shared].buildInfo[@"bytes_per_arena"] == nil ||
        [[CJLog shared].buildInfo[@"bytes_per_arena"] unsignedLongLongValue] != CJCompiledProtocol.arenaLength) {
        CJEvent(@"jit_configuration_mismatch", CJProtocolConfiguration());
        self.statusLabel.text = @"JIT CONFIGURATION MISMATCH";
        self.detailLabel.text = @"This build's metadata and compiled request disagree. Export diagnostics; no JIT request was sent.";
        return NO;
    }
    NSDictionary *request = CJCreateJITRequest(&gMailbox, (uint64_t)getpid(), (size_t)getpagesize(), [CJLog shared].sessionID);
    NSString *source = [NSString stringWithContentsOfURL:[NSBundle.mainBundle URLForResource:@"celeste-jit-probe" withExtension:@"js"] encoding:NSUTF8StringEncoding error:NULL];
    self.sessionScript = CJBindJITScript(request, source);
    if (!self.sessionScript) { self.statusLabel.text = @"SCRIPT RESOURCE MISSING"; return NO; }
    self.requestTime = NSDate.date;
    CJEvent(@"jit_request_created", @{@"protocol": @1, @"pid": @(getpid()), @"request_id": [CJLog shared].sessionID,
                                     @"mailbox": request[@"mailbox"], @"arena_count": @2, @"bytes_per_arena": @(CJ_HOOK_ARENA_LENGTH),
                                     @"session_script_sha256": CJSHA256([self.sessionScript dataUsingEncoding:NSUTF8StringEncoding]),
                                     @"script_template_sha256": [CJLog shared].buildInfo[@"script_template_sha256"] ?: @"unknown"});
    self.statusLabel.text = @"WAITING FOR STIKDEBUG";
    self.detailLabel.text = @"StikDebug must already be running in LiveContainer 2. Complete its request, then switch back to this running probe in LiveContainer 1. The checks start after a valid reply and detach.";
    return YES;
}
- (NSString *)sessionScriptName {
    return [NSString stringWithFormat:@"celeste-game-PID%d-%@.js", getpid(), [CJLog shared].sessionID];
}
- (void)enableJIT { [self openStikRequestWithInlineScript:YES]; }
- (void)enableImportedScript { [self openStikRequestWithInlineScript:NO]; }
- (void)openStikRequestWithInlineScript:(BOOL)inlineScript {
    if (![self makeRequest] || gMailbox.status != 1) return;
    NSString *encoded = [[self.sessionScript dataUsingEncoding:NSUTF8StringEncoding] base64EncodedStringWithOptions:0];
    // Base64url avoids + interpretation in URL parsers. StikDebug accepts it.
    encoded = [[[encoded stringByReplacingOccurrencesOfString:@"+" withString:@"-"] stringByReplacingOccurrencesOfString:@"/" withString:@"_"] stringByReplacingOccurrencesOfString:@"=" withString:@""];
    NSURLComponents *components = [NSURLComponents new];
    components.scheme = @"stikdebug"; components.host = @"enable-jit";
    NSMutableArray *items = [NSMutableArray arrayWithArray:@[
        [NSURLQueryItem queryItemWithName:@"pid" value:[NSString stringWithFormat:@"%d", getpid()]],
        [NSURLQueryItem queryItemWithName:@"script-name" value:[self sessionScriptName]]]];
    if (inlineScript) [items addObject:[NSURLQueryItem queryItemWithName:@"script-data" value:encoded]];
    components.queryItems = items;
    // No guest bundle-id: target the real PID and avoid relaunching a container.
    NSURLComponents *route = [NSURLComponents new];
    route.scheme = @"livecontainer2"; route.host = @"open-url";
    NSString *innerURL = [[components.URL.absoluteString dataUsingEncoding:NSUTF8StringEncoding] base64EncodedStringWithOptions:0];
    route.queryItems = @[[NSURLQueryItem queryItemWithName:@"url" value:innerURL]];
    CJEvent(@"stikdebug_url_requested", @{@"target_pid": @(getpid()), @"route": @"livecontainer2://open-url", @"inline_script": @(inlineScript), @"script_filename": [self sessionScriptName], @"encoded_url_length": @(route.URL.absoluteString.length)});
    if (self.backgroundTask == UIBackgroundTaskInvalid) {
        __weak CJViewController *weakSelf = self;
        self.backgroundTask = [UIApplication.sharedApplication beginBackgroundTaskWithName:@"Celeste probe JIT handoff" expirationHandler:^{
            CJViewController *self = weakSelf;
            CJEvent(@"handoff_background_time_expired", @{});
            if (self && self.backgroundTask != UIBackgroundTaskInvalid) {
                [UIApplication.sharedApplication endBackgroundTask:self.backgroundTask]; self.backgroundTask = UIBackgroundTaskInvalid;
            }
        }];
    }
    [UIApplication.sharedApplication openURL:route.URL options:@{} completionHandler:^(BOOL success) {
        CJEvent(@"stikdebug_url_opened", @{@"success": @(success)});
        if (!success) {
            self.detailLabel.text = @"LiveContainer 2 did not open. Make sure StikDebug is running there, or export the session script and follow manual setup in INSTALL.md. Target the PID shown above.";
            [self endBackgroundTime];
        }
    }];
}
- (void)poll {
    [self updateLauncher];
    if (UIApplication.sharedApplication.applicationState == UIApplicationStateActive) [self refreshLog];
    if (!self.sessionScript || self.busy || self.attempted) return;
    atomic_thread_fence(memory_order_seq_cst);
    if (gMailbox.status != self.lastMailboxStatus) {
        self.lastMailboxStatus = gMailbox.status;
        CJEvent(@"mailbox_status_observed", @{@"status": @(gMailbox.status), @"script_version": @(gMailbox.scriptVersion),
                                            @"script_error": @(gMailbox.error), @"process": CJProcessState()});
    }
    if (gMailbox.status == 3) {
        self.attempted = YES; self.enableButton.enabled = NO; self.scriptButton.enabled = NO; self.importedButton.enabled = NO;
        self.statusLabel.text = @"SCRIPT PREPARATION FAILED";
        self.detailLabel.text = [NSString stringWithFormat:@"StikDebug reported phase %llu. Export diagnostics and the StikDebug script log. Relaunch the probe before a new request.", (unsigned long long)gMailbox.error];
        CJEvent(@"script_reported_failure", @{@"phase": @(gMailbox.error), @"process": CJProcessState()});
        [self endBackgroundTime]; return;
    }
    if (gMailbox.status == 2) {
        NSDictionary *process = CJProcessState();
        if (![process[@"trace_known"] boolValue]) {
            self.attempted = YES;
            self.statusLabel.text = @"COULD NOT VERIFY DETACH";
            self.detailLabel.text = @"The debugger replied, but trace status is unavailable. No generated code has run. Export diagnostics and the StikDebug log.";
            CJEvent(@"trace_status_unavailable", process); [self endBackgroundTime]; return;
        }
        if ([process[@"traced"] boolValue]) {
            self.statusLabel.text = @"WAITING FOR DEBUGGER DETACH";
            if (!self.timeoutLogged && -self.requestTime.timeIntervalSinceNow > 90) {
                self.timeoutLogged = YES;
                CJEvent(@"detach_wait_exceeded_90_seconds", process);
                self.detailLabel.text = @"StikDebug is still attached. Stop that session and export its log. No generated code has run.";
            }
            return;
        }
        if (UIApplication.sharedApplication.applicationState == UIApplicationStateActive) [self runChecks];
        return;
    }
    if (!self.timeoutLogged && -self.requestTime.timeIntervalSinceNow > 90) {
        self.timeoutLogged = YES;
        self.statusLabel.text = @"NO PREPARATION REPLY YET";
        self.detailLabel.text = @"No generated code has run. Check StikDebug's script log, then export diagnostics. If the process was restarted, create a fresh request in the new launch.";
        CJEvent(@"preparation_wait_exceeded_90_seconds", @{@"mailbox_status": @(gMailbox.status), @"process": CJProcessState()});
    }
}
- (void)runChecks {
    if (self.busy || gMailbox.status != 2 || TARGET_OS_SIMULATOR) return;
    self.busy = YES; self.attempted = YES;
    self.enableButton.enabled = NO; self.scriptButton.enabled = NO; self.importedButton.enabled = NO; self.runButton.enabled = NO;
    self.statusLabel.text = @"RUNNING NATIVE CHECKS";
    self.detailLabel.text = @"The log is saved before each execution stage. This test may reveal a platform fault; reopen the probe to export the previous session if it closes.";
    [self endBackgroundTime];
    CJEvent(@"native_checks_start", @{@"process": CJProcessState()});
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        BOOL passed = CJRunNativeChecks();
        CJEvent(passed ? @"g0_memory_pass" : @"g0_memory_fail", @{@"process": CJProcessState(), @"scope": @"native_memory_only"});
        dispatch_async(dispatch_get_main_queue(), ^{
            self.busy = NO; self.nativePassed = passed; [self refreshContentStatus];
            self.statusLabel.text = passed ? @"NATIVE PASS · READY FOR MONO" : @"FAIL · CHECK THE LOG";
            self.statusLabel.textColor = passed ? UIColor.systemGreenColor : UIColor.systemOrangeColor;
            self.detailLabel.text = passed ? @"Prepared memory passed. Import both mod ZIPs if needed, then tap Run Celeste + Everest. This runs once per launch." : @"Export diagnostics and the StikDebug script log. The managed runtime has not started because native preparation failed.";
        });
    });
}
- (NSURL *)contentStagingDirectory {
    return [[CJLog shared].directory.URLByDeletingLastPathComponent URLByAppendingPathComponent:@"ContentImport" isDirectory:YES];
}
- (BOOL)contentAvailable {
    NSURL *documents=[CJLog shared].directory.URLByDeletingLastPathComponent;
    NSString *identity=[CJLog shared].buildInfo[@"game_content_aggregate_sha256"];
    NSString *pointer=[NSString stringWithFormat:@"GameLibrary/v1/%@/active.json",identity];
    return [NSFileManager.defaultManager fileExistsAtPath:[[self contentStagingDirectory] URLByAppendingPathComponent:@"game-input.zip"].path] ||
           [NSFileManager.defaultManager fileExistsAtPath:[documents URLByAppendingPathComponent:pointer].path];
}
- (void)refreshContentStatus {
    BOOL staged=[NSFileManager.defaultManager fileExistsAtPath:[[self contentStagingDirectory] URLByAppendingPathComponent:@"game-input.zip"].path];
    BOOL available=[self contentAvailable];
    [self.contentButton setTitle:staged ? @"Game ZIP selected · ready to verify" : available ? @"Saved game files found ✓" : @"1. Import game ZIP" forState:UIControlStateNormal];
    self.runButton.enabled=available && self.importedDLL && self.nativePassed && !self.managedAttempted && !self.busy;
    CJEvent(@"content_library_checked",@{@"archive_staged":@(staged),@"installed_pointer_found":@(available && !staged),@"verified_this_session":@NO});
}
- (void)importContent {
    if (self.busy || self.managedAttempted) return;
    self.choosingContent=YES;
    UIDocumentPickerViewController *picker=[[UIDocumentPickerViewController alloc] initForOpeningContentTypes:@[UTTypeItem] asCopy:NO];
    picker.delegate=self; picker.allowsMultipleSelection=NO;
    [self presentViewController:picker animated:YES completion:nil];
}
- (void)documentPickerWasCancelled:(UIDocumentPickerViewController *)controller { (void)controller; self.choosingContent=NO; }
- (void)cancelContent {
    CJContentSetCancelled(YES); self.cancelContentButton.enabled=NO;
    self.detailLabel.text=@"Cancelling safely. Your source files and saves will be kept.";
    CJEvent(@"content_cancel_requested",@{});
}
- (void)beginContentProgress {
    self.cancelContentButton.hidden=NO; self.cancelContentButton.enabled=YES;
    self.contentTimer=[NSTimer scheduledTimerWithTimeInterval:0.3 target:self selector:@selector(updateContentProgress) userInfo:nil repeats:YES];
}
- (void)endContentProgress {
    [self.contentTimer invalidate]; self.contentTimer=nil; self.cancelContentButton.hidden=YES;
}
- (void)updateContentProgress {
    if (CJContentShouldCancel()) return;
    NSDictionary *progress=CJContentSnapshot(); double total=[progress[@"total"] doubleValue],done=[progress[@"bytes"] doubleValue];
    if (total>0) self.detailLabel.text=[NSString stringWithFormat:@"%.0f%% · %.1f / %.1f MB · %@ files. Keep this app open.",100.0*done/total,done/1000000.0,total/1000000.0,progress[@"files"]];
}
- (void)stageContent:(NSURL *)source {
    if (![@[@"zip",@"ipa"] containsObject:source.pathExtension.lowercaseString]) {
        self.detailLabel.text=@"Select the original Celeste game ZIP. Leave it unextracted in Files.";
        CJEvent(@"content_archive_picker_rejected",@{@"filename":source.lastPathComponent}); return;
    }
    self.busy=YES; self.runButton.enabled=NO; self.contentButton.enabled=NO; self.dllButton.enabled=NO;
    BOOL enable=self.enableButton.enabled,script=self.scriptButton.enabled,imported=self.importedButton.enabled;
    self.enableButton.enabled=NO; self.scriptButton.enabled=NO; self.importedButton.enabled=NO;
    self.statusLabel.text=@"COPYING GAME ZIP"; self.detailLabel.text=@"Downloading from Files if needed, then copying into this app. Keep the app open.";
    [self beginContentProgress];
    CJStageContentArchive(source,[self contentStagingDirectory],[[CJLog shared].buildInfo[@"game_content_bytes"] longLongValue],^(NSString *event,NSDictionary *fields){CJEvent(event,fields);},^(BOOL saved,NSError *error){
        self.busy=NO; [self endContentProgress]; self.contentButton.enabled=YES; self.dllButton.enabled=YES;
        self.enableButton.enabled=enable; self.scriptButton.enabled=script; self.importedButton.enabled=imported;
        [self refreshContentStatus];
        self.statusLabel.text=saved ? @"GAME ZIP SELECTED" : @"IMPORT STOPPED";
        self.detailLabel.text=saved ? @"The ZIP is ready. Check your mod ZIPs, enable JIT, then Run. Game files will be verified and kept for future launches." : error.localizedDescription;
#if TARGET_OS_SIMULATOR
        if ([NSProcessInfo.processInfo.arguments containsObject:@"--content-ui-test-stage"]) {
            CJEvent(@"host_ui_content_stage_check",@{@"staged":@(saved),@"run_disabled_without_jit":@(!self.runButton.enabled),@"progress":CJContentSnapshot()});
            [[CJLog shared] exportDiagnostics];
        }
#endif
    });
}
- (NSURL *)modDirectory {
    NSURL *documents = [CJLog shared].directory.URLByDeletingLastPathComponent;
    return [documents URLByAppendingPathComponent:@"Profiles/sj-first-play/Mods" isDirectory:YES];
}
- (NSDictionary *)modManifest {
    return [CJLog shared].buildInfo[@"mod_download_manifest"];
}
- (void)refreshImportedMods {
    if(self.busy || self.managedAttempted)return;
    self.busy=YES;self.runButton.enabled=NO;
    self.statusLabel.text=@"CHECKING MOD LIBRARY";[self updateLauncher];
    NSDictionary *expected=[self modManifest];NSURL *directory=[self modDirectory];
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^{
        NSError *error=nil;NSString *name=@"CJITCodeCanary-v1.0.0.zip";
        BOOL seeded=CJInstallMod([NSBundle.mainBundle.bundleURL URLByAppendingPathComponent:name],directory,name,expected[name],&error);
        NSDictionary *snapshot=seeded?[self.modLibrary scanWithForce:YES error:&error]:nil;
        CJEvent(@"launcher_library_checked",@{@"profile":@"sj-first-play",@"snapshot":snapshot?:@{},@"error":error.localizedDescription?:@""});
        dispatch_async(dispatch_get_main_queue(),^{
            self.busy=NO;self.librarySnapshot=snapshot?:@{@"issues":@[error.localizedDescription?:@"Could not read mod library."],@"canRun":@NO};
            self.importedDLL=[snapshot[@"canRun"] boolValue]?[NSBundle.mainBundle.bundleURL URLByAppendingPathComponent:@"Managed/CelesteJITEverest.dll"]:nil;
            self.dllButton.enabled=YES;self.downloadButton.enabled=YES;
            self.statusLabel.text=error?@"MOD LIBRARY NEEDS ATTENTION":@"MOD LIBRARY READY";
            if(error)self.detailLabel.text=error.localizedDescription;
            [self refreshContentStatus];[self updateLauncher];
        });
    });
}
- (void)downloadMods {
    if(self.busy || self.managedAttempted)return;
    self.busy=YES;self.runButton.enabled=NO;self.dllButton.enabled=NO;self.downloadButton.enabled=NO;self.contentButton.enabled=NO;
    self.cancelDownloadButton.hidden=NO;UIApplication.sharedApplication.idleTimerDisabled=YES;
    self.statusLabel.text=@"DOWNLOADING STRAWBERRY JAM";
    CJEvent(@"sj_download_started",@{@"profile":@"sj-first-play",@"pinned_archives":@52,@"original_zip_bytes":@1237284560});
    self.modDownloader=[[CJModDownloader alloc] initWithDirectory:[self modDirectory] manifest:[self modManifest]];
    __weak CJViewController *weakSelf=self;
    [self.modDownloader startWithProgress:^(NSString *name,NSUInteger done,NSUInteger total,int64_t received,int64_t expected){
        CJViewController *view=weakSelf;if(!view)return;
        view.detailLabel.text=[NSString stringWithFormat:@"%lu/%lu ready · %@\n%.1f / %.1f MB. Keep the app open on Wi-Fi; verified downloads survive cancellation.",(unsigned long)done,(unsigned long)total,name,(double)received/1000000,(double)expected/1000000];
    } completion:^(NSError *error){
        CJViewController *view=weakSelf;if(!view)return;
        view.busy=NO;view.modDownloader=nil;view.cancelDownloadButton.hidden=YES;view.contentButton.enabled=YES;UIApplication.sharedApplication.idleTimerDisabled=NO;
        view.statusLabel.text=error?@"DOWNLOAD PAUSED":@"STRAWBERRY JAM DOWNLOADED";
        view.detailLabel.text=error.localizedDescription?:@"Enable JIT via LiveContainer 2, then run Celeste + Everest.";
        CJEvent(error?@"sj_download_paused":@"sj_download_complete",@{@"error":error.localizedDescription?:@""});
        [view refreshImportedMods];
    }];
}
- (void)cancelModDownload { [self.modDownloader cancel]; }
- (void)importDLL {
    if (self.busy || self.managedAttempted) return;
    UIDocumentPickerViewController *picker = [[UIDocumentPickerViewController alloc] initForOpeningContentTypes:@[UTTypeItem] asCopy:NO];
    picker.delegate = self; picker.allowsMultipleSelection = YES;
#if TARGET_OS_SIMULATOR
    if([NSProcessInfo.processInfo.arguments containsObject:@"--launcher-ui-test"])picker.directoryURL=[[CJLog shared].directory.URLByDeletingLastPathComponent URLByAppendingPathComponent:@"LauncherImport" isDirectory:YES];
#endif
    [self presentViewController:picker animated:YES completion:nil];
}
- (void)documentPicker:(UIDocumentPickerViewController *)controller didPickDocumentsAtURLs:(NSArray<NSURL *> *)urls {
    (void)controller;
    if (self.busy || self.managedAttempted || urls.count == 0) return;
    if (self.choosingContent) { self.choosingContent=NO; [self stageContent:urls.firstObject]; return; }
    self.busy=YES;self.runButton.enabled=NO;
    self.statusLabel.text=@"IMPORTING MODS";self.detailLabel.text=@"Reading ZIP metadata and keeping your original files.";[self updateLauncher];
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^{
        NSMutableArray *errors=[NSMutableArray array];NSUInteger installed=0;
        for(NSURL *selected in urls){
            BOOL scoped=[selected startAccessingSecurityScopedResource];NSError *error=nil;
            NSDictionary *result=[self.modLibrary importZIP:selected error:&error];
            if(scoped)[selected stopAccessingSecurityScopedResource];
            if(result){installed++;CJEvent(@"mod_zip_imported",result);}
            else {NSString *reason=error.localizedDescription?:@"Could not read mod ZIP.";[errors addObject:[NSString stringWithFormat:@"%@: %@",selected.lastPathComponent,reason]];CJEvent(@"mod_import_rejected",@{@"filename":selected.lastPathComponent,@"reason":reason});}
        }
        dispatch_async(dispatch_get_main_queue(),^{self.busy=NO;
            self.detailLabel.text=errors.count?[errors componentsJoinedByString:@"\n"]:[NSString stringWithFormat:@"%lu mod ZIP(s) imported. Review dependencies and enable/disable choices in Mods.",(unsigned long)installed];
            [self refreshImportedMods];
        });
    });
}

- (void)runManaged {
    if(self.busy || self.managedAttempted || !self.nativePassed || !self.importedDLL || ![self contentAvailable] || TARGET_OS_SIMULATOR)return;
    self.busy=YES;self.runButton.enabled=NO;self.statusLabel.text=@"VERIFYING MOD SELECTION";
    self.detailLabel.text=@"Checking ZIP identities and freezing your selected mod set.";[self updateLauncher];
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^{
        NSError *error=nil;NSDictionary *selection=[self.modLibrary prepareWithError:&error];
        CJEvent(selection?@"launcher_run_prepared":@"launcher_run_rejected",@{@"selection":selection?:@{},@"error":error.localizedDescription?:@""});
        dispatch_async(dispatch_get_main_queue(),^{
            self.busy=NO;
            if(!selection){self.statusLabel.text=@"MOD SELECTION NEEDS ATTENTION";self.detailLabel.text=error.localizedDescription;[self refreshImportedMods];return;}
            self.librarySnapshot=selection;
            self.regressionMode=[NSUserDefaults.standardUserDefaults boolForKey:@"launcher.sjRegression"];
            if(self.regressionMode){
                BOOL sj=NO;for(NSDictionary *mod in selection[@"modules"])if([mod[@"name"] isEqualToString:@"StrawberryJam2021"])sj=YES;
                if(!sj){self.detailLabel.text=@"Enable Strawberry Jam for the regression test, or turn that test off in Settings.";[self refreshContentStatus];[self updateLauncher];return;}
            }
            setenv("CJIT_VERIFY_SJ",self.regressionMode?"1":"0",1);
            [self beginManagedRun];
        });
    });
}

- (void)beginManagedRun {
    if (self.busy || self.managedAttempted || !self.nativePassed || !self.importedDLL || ![self contentAvailable] || TARGET_OS_SIMULATOR) return;
    if (!self.importedDLL) return;
    NSDictionary *state=CJProcessState();
    if (![state[@"trace_known"] boolValue] || [state[@"traced"] boolValue] || ![state[@"cs_debugged"] boolValue]) {
        CJEvent(@"graphics_start_rejected",state); return;
    }
    self.managedAttempted=YES; self.busy=YES;
    self.runButton.enabled=NO; self.dllButton.enabled=NO; self.contentButton.enabled=NO;
    self.statusLabel.text=@"PREPARING GAME FILES";
    self.detailLabel.text=@"Verifying your game files. Keep this app open until the game starts.";
    CJContentSetCancelled(NO); [self beginContentProgress];
    self.launcherWindow=self.view.window;
    NSURL *dll=self.importedDLL;
    CJEvent(@"graphics_test_start",@{@"process":state,@"adapter_sha256":CJSHA256([NSData dataWithContentsOfURL:dll]),@"mod_profile":@"sj-first-play"});
#if !TARGET_OS_SIMULATOR
    BOOL alreadyPrepared=self.runtimeReady;
    if (!alreadyPrepared) CJGraphicsPlatformPrepare(^(NSString *event,NSDictionary *fields){CJEvent(event,fields);});
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0), ^{
        @autoreleasepool {
            BOOL ready=alreadyPrepared;
            if (!ready) {
                CJCodeRegion regions[2]={{gArenas[0].rx,gArenas[0].rw,gArenas[0].length},{gArenas[1].rx,gArenas[1].rw,gArenas[1].length}};
                BOOL allocator=cj_code_arena_initialize(regions,getpagesize(),CJAllocatorEvent);
                CJEvent(@"managed_allocator_initialized",@{@"success":@(allocator)});
                ready=allocator && CJGraphicsPrepare(dll,[NSBundle.mainBundle.bundleURL URLByAppendingPathComponent:@"Managed"],^(NSString *event,NSDictionary *fields){CJEvent(event,fields);});
            }
            int contentResult=0;
            BOOL contentOK=ready && CJGraphicsPrepareContent(&contentResult);
            dispatch_async(dispatch_get_main_queue(),^{
                self.runtimeReady=ready; [self endContentProgress];
                if (!ready || !contentOK) {
                    self.busy=NO; self.graphicsFailed=YES;
                    self.statusLabel.text=@"STARTUP STOPPED · EXPORT LOGS";
                    CJEvent(@"graphics_prepare_failed",@{}); return;
                }
                // Only remove our own staged copy. The Files-app source stays intact.
                NSURL *staged=[[self contentStagingDirectory] URLByAppendingPathComponent:@"game-input.zip"];
                NSError *cleanup=nil;
                if ([NSFileManager.defaultManager fileExistsAtPath:staged.path]) {
                    BOOL removed=[NSFileManager.defaultManager removeItemAtURL:staged error:&cleanup];
                    CJEvent(@"content_archive_released",@{@"removed":@(removed),@"error":cleanup.localizedDescription ?: @""});
                }
                if (contentResult!=1) {
                    self.busy=NO; self.managedAttempted=NO;
                    self.contentButton.enabled=YES; self.dllButton.enabled=YES;
                    [self refreshContentStatus];
                    self.statusLabel.text=contentResult==3 ? @"IMPORT CANCELLED" : @"GAME FILES NOT READY";
                    self.detailLabel.text=@"Your installed files and saves are preserved. Select the original Celeste FNA ZIP to try again, or export diagnostics.";
                    return;
                }
                self.graphicsReady=YES; self.statusLabel.text=@"STARTING CELESTE";
                [self startGraphics];
            });
        }
    });
#endif
}
- (void)startGraphics {
#if !TARGET_OS_SIMULATOR
    // Runtime bootstrap may finish while the owner is on the Home Screen.
    // Defer GPU/window work until UIKit is active again.
    if (!self.graphicsReady || self.graphicsRunning || self.finishing || UIApplication.sharedApplication.applicationState!=UIApplicationStateActive) return;
    if(!gLandscapeOnly){
        gLandscapeOnly=YES;[self setNeedsUpdateOfSupportedInterfaceOrientations];
        UIWindowSceneGeometryPreferencesIOS *geometry=[[UIWindowSceneGeometryPreferencesIOS alloc] initWithInterfaceOrientations:UIInterfaceOrientationMaskLandscape];
        [self.launcherWindow.windowScene requestGeometryUpdateWithPreferences:geometry errorHandler:^(NSError *error){CJEvent(@"launcher_orientation_error",@{@"error":error.localizedDescription});}];
    }
    if(!UIInterfaceOrientationIsLandscape(self.launcherWindow.windowScene.interfaceOrientation) || self.launcherWindow.bounds.size.width<self.launcherWindow.bounds.size.height){
        if(++self.orientationWaits>80){self.graphicsReady=NO;self.busy=NO;gLandscapeOnly=NO;[self setNeedsUpdateOfSupportedInterfaceOrientations];self.detailLabel.text=@"Could not switch to landscape. Rotate your phone, then close and relaunch the app before trying again.";CJEvent(@"launcher_orientation_failed",@{});return;}
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW,NSEC_PER_SEC/10),dispatch_get_main_queue(),^{[self startGraphics];});return;
    }
    CJEvent(@"launcher_landscape_ready",@{@"width":@(self.launcherWindow.bounds.size.width),@"height":@(self.launcherWindow.bounds.size.height),@"regression_mode":@(self.regressionMode)});
    self.graphicsReady=NO;
    int result=0;
    BOOL ok=CJGraphicsCall("Start",&result) && result==1;
    UIWindow *game=CJGraphicsPlatformWindow();
    NSDictionary *metrics=CJGraphicsPlatformSnapshot();
    ok=ok && game && game.windowScene==self.launcherWindow.windowScene && [metrics[@"metal_layer"] boolValue] && [metrics[@"gpu_readback_passed"] boolValue];
    CJEvent(@"graphics_start_result",@{@"passed":@(ok),@"native":metrics,@"runtime":CJGraphicsRuntimeStats()});
    if (!ok) { self.graphicsFailed=YES; self.graphicsStopReason=@"start_failure"; [self finishGraphics]; return; }
    self.graphicsRunning=YES; self.busy=NO;CJFrameReset(&gFrameMetrics);
    self.graphicsOverlay=[UIView new]; self.graphicsOverlay.translatesAutoresizingMaskIntoConstraints=NO;
    self.graphicsOverlay.backgroundColor=[UIColor colorWithWhite:0 alpha:0.7]; self.graphicsOverlay.layer.cornerRadius=10;
    [game.rootViewController.view addSubview:self.graphicsOverlay];
    self.graphicsLabel=[self label:@"Preparing frame metrics…" size:11 weight:UIFontWeightMedium];
    self.graphicsLabel.textColor=UIColor.whiteColor; self.graphicsLabel.translatesAutoresizingMaskIntoConstraints=NO;
    [self.graphicsOverlay addSubview:self.graphicsLabel];
    UIButton *finish=[self button:@"Finish" action:@selector(finishButtonPressed) prominent:NO];
    finish.accessibilityIdentifier=@"graphics.finish";
    UIButton *prologue=[self button:@"SJ lobby" action:@selector(startTestMap) prominent:NO];
    prologue.accessibilityIdentifier=@"game.prologue";
    UIButton *bing=[self button:@"Bing" action:@selector(startBing) prominent:NO];
    bing.accessibilityIdentifier=@"game.bing";
    UIStackView *buttons=[[UIStackView alloc] initWithArrangedSubviews:self.regressionMode?@[prologue,bing,finish]:@[finish]];
    buttons.axis=UILayoutConstraintAxisHorizontal;buttons.distribution=UIStackViewDistributionFillEqually;buttons.spacing=8;buttons.translatesAutoresizingMaskIntoConstraints=NO;
    [self.graphicsOverlay addSubview:buttons];
    UILayoutGuide *safe=game.rootViewController.view.safeAreaLayoutGuide;
    [NSLayoutConstraint activateConstraints:@[
        [self.graphicsOverlay.topAnchor constraintEqualToAnchor:safe.topAnchor constant:8],
        [self.graphicsOverlay.trailingAnchor constraintEqualToAnchor:safe.trailingAnchor constant:-8],
        [self.graphicsOverlay.widthAnchor constraintEqualToConstant:270],
        [buttons.topAnchor constraintEqualToAnchor:self.graphicsOverlay.topAnchor constant:4],
        [buttons.leadingAnchor constraintEqualToAnchor:self.graphicsOverlay.leadingAnchor constant:8],
        [buttons.trailingAnchor constraintEqualToAnchor:self.graphicsOverlay.trailingAnchor constant:-8],
        [buttons.heightAnchor constraintEqualToConstant:36],
        [self.graphicsLabel.topAnchor constraintEqualToAnchor:buttons.bottomAnchor constant:4],
        [self.graphicsLabel.leadingAnchor constraintEqualToAnchor:self.graphicsOverlay.leadingAnchor constant:8],
        [self.graphicsLabel.trailingAnchor constraintEqualToAnchor:self.graphicsOverlay.trailingAnchor constant:-8],
        [self.graphicsLabel.bottomAnchor constraintEqualToAnchor:self.graphicsOverlay.bottomAnchor constant:-6]]];
    self.displayLink=[CADisplayLink displayLinkWithTarget:self selector:@selector(graphicsFrame:)];
    self.displayLink.preferredFrameRateRange=CAFrameRateRangeMake(30,60,60);
    [self.displayLink addToRunLoop:NSRunLoop.mainRunLoop forMode:NSRunLoopCommonModes];
    CJEvent(@"graphics_display_link_started",@{@"main_thread":@(NSThread.isMainThread),@"target_fps":@60});
    if (UIApplication.sharedApplication.applicationState!=UIApplicationStateActive) [self resignActive];
#endif
}
- (void)graphicsFrame:(CADisplayLink *)link {
#if !TARGET_OS_SIMULATOR
    if (!self.graphicsRunning || self.graphicsPaused || self.finishing || UIApplication.sharedApplication.applicationState!=UIApplicationStateActive) return;
    if (self.lastFrameTimestamp>0) self.maximumFrameGap=MAX(self.maximumFrameGap,link.timestamp-self.lastFrameTimestamp);
    self.lastFrameTimestamp=link.timestamp;
    int result=0;double began=CACurrentMediaTime();
    BOOL invoked=CJGraphicsCall("Frame",&result); BOOL ok=invoked && result==1;
    CJFrameRecord(&gFrameMetrics,link.timestamp,CACurrentMediaTime()-began);
    if (!ok) { self.graphicsFailed=YES; self.graphicsStopReason=invoked?@"game_loop_ended":@"frame_failure"; CJEvent(@"graphics_frame_failed",@{@"runtime":CJGraphicsRuntimeStats(),@"callback_succeeded":@(invoked),@"managed_result":@(result),@"failure":CJGraphicsLastFailure()}); [self finishGraphics]; return; }
    self.frameCallbacks++;
    if (self.frameCallbacks==1) CJEvent(@"graphics_first_frame_returned",@{@"native":CJGraphicsPlatformSnapshot(),@"runtime":CJGraphicsRuntimeStats()});
    if (self.frameCallbacks%30==0) {
        CJFrameSummary frame=CJFrameSummarize(&gFrameMetrics);
        BOOL visible=[NSUserDefaults.standardUserDefaults boolForKey:@"launcher.metrics"];
        self.graphicsLabel.hidden=!visible;
        NSString *low=frame.samples>=120?[NSString stringWithFormat:@"%.1f",frame.one_percent_low]:@"warming up";
        self.graphicsLabel.text=visible?[NSString stringWithFormat:@"%.1f callback FPS · Frame %.1f ms\n1%% low %@ · last %lu frames",frame.fps,frame.cpu_ms,low,(unsigned long)frame.samples]:@"";
        if(self.frameCallbacks%600==0)CJEvent(@"launcher_frame_metrics",@{@"callback_fps":@(frame.fps),@"mean_frame_callback_ms":@(frame.cpu_ms),@"one_percent_low_fps":frame.samples>=120?@(frame.one_percent_low):NSNull.null,@"maximum_interval_ms":@(frame.maximum_ms),@"window_samples":@(frame.samples),@"gpu_completion_measured":@NO});
    }

#else
    (void)link;
#endif
}
- (void)startBing {
#if !TARGET_OS_SIMULATOR
    if(self.graphicsRunning && !self.graphicsPaused && !self.finishing) { CJGameQueueBing();CJEvent(@"sj_bing_button",@{}); }
#endif
}
- (void)startTestMap {
#if !TARGET_OS_SIMULATOR
    if(self.graphicsRunning && !self.finishing) {CJGameQueueTestMap();CJEvent(@"everest_test_map_button",@{});}
#endif
}
- (void)finishButtonPressed {
    if(!self.graphicsRunning || self.finishing)return;
    self.graphicsStopReason=@"finish_button";
    CJEvent(@"graphics_finish_button",@{@"frame_callbacks":@(self.frameCallbacks)});
    [self finishGraphics];
}
- (void)finishGraphics {
#if !TARGET_OS_SIMULATOR
    self.finishing=YES;
    if(self.graphicsRunning && UIApplication.sharedApplication.applicationState!=UIApplicationStateActive) {
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW,NSEC_PER_SEC/4),dispatch_get_main_queue(),^{[self finishGraphics];});return;
    }
    NSDictionary *lastMetrics=CJGraphicsPlatformSnapshot();
    CJEvent(@"graphics_stop_start",@{@"frame_callbacks":@(self.frameCallbacks),@"native":lastMetrics,@"reason":self.graphicsStopReason?:@"unspecified",@"failure":CJGraphicsLastFailure()});
    int result=0; BOOL stopped=CJGraphicsCall("Stop",&result);
    if(stopped && result==3) {
        self.graphicsLabel.text=@"Finishing game loading/saving before shutdown…";
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW,NSEC_PER_SEC/20),dispatch_get_main_queue(),^{
            if(UIApplication.sharedApplication.applicationState==UIApplicationStateActive && !self.graphicsPaused) {
                int value=0;if(!CJGraphicsCall("Frame",&value))self.graphicsFailed=YES;
            }
            [self finishGraphics];
        });return;
    }
    self.graphicsRunning=NO;[self.displayLink invalidate];self.displayLink=nil;
    [self.graphicsOverlay removeFromSuperview];self.graphicsOverlay=nil;
    BOOL detached=CJGraphicsDetachMain();
    CJGraphicsPlatformForgetWindow();
    gLandscapeOnly=NO;[self setNeedsUpdateOfSupportedInterfaceOrientations];
    [self.launcherWindow makeKeyAndVisible];
    self.busy=NO;
    BOOL pass=stopped && result==1 && detached && !self.graphicsFailed && (!self.regressionMode || self.completedBackgroundSeconds>=20) && [lastMetrics[@"gpu_readback_passed"] boolValue] && [lastMetrics[@"failed_checks"] unsignedIntValue]==0;
    self.statusLabel.text=pass?@"SESSION SAVED":@"SESSION STOPPED · EXPORT LOGS";
    self.statusLabel.textColor=pass?UIColor.systemGreenColor:UIColor.systemOrangeColor;
    NSString *failure=CJGraphicsLastFailure()[@"summary"];
    self.detailLabel.text=pass?@"Your session was saved. Close and relaunch to play again or change mods. Export diagnostics to build 22 Results.":
        [NSString stringWithFormat:@"%@\nExport diagnostics to build 22 Results, then close and relaunch the app. Recent progress may not have been saved.",failure.length?failure:@"The game stopped before a clean save and shutdown could be confirmed."];
    CJEvent(pass?@"graphics_bridge_pass":@"graphics_bridge_incomplete",@{@"stopped":@(stopped),@"managed_result":@(result),@"detached":@(detached),@"background_seconds":@(self.completedBackgroundSeconds),@"frame_callbacks":@(self.frameCallbacks),@"maximum_frame_gap_seconds":@(self.maximumFrameGap),@"runtime":CJGraphicsRuntimeStats(),@"process":CJProcessState(),@"gameplay_checks_completed":@(pass)});
    CJEvent(@"graphics_result_presented",@{@"passed":@(pass)});
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC),dispatch_get_main_queue(),^{
        CJEvent(@"graphics_post_run_alive",@{@"foreground":@(UIApplication.sharedApplication.applicationState==UIApplicationStateActive),@"process":CJProcessState()});
    });
#endif
}
- (void)share:(NSURL *)url {
    if (!url) {
        self.detailLabel.text = @"Could not write the export. The live log and Console output may still be available."; return;
    }
    UIActivityViewController *share = [[UIActivityViewController alloc] initWithActivityItems:@[url] applicationActivities:nil];
    share.popoverPresentationController.sourceView = self.view;
    share.popoverPresentationController.sourceRect = CGRectMake(self.view.bounds.size.width / 2, self.view.bounds.size.height / 2, 1, 1);
    [self presentViewController:share animated:YES completion:nil];
}
- (void)exportLogs { [self share:[[CJLog shared] exportDiagnostics]]; }
- (void)exportScript {
    if (![self makeRequest] || gMailbox.status != 1) return;
    NSURL *url = [[CJLog shared].directory URLByAppendingPathComponent:[self sessionScriptName]];
    BOOL written = [self.sessionScript writeToURL:url atomically:YES encoding:NSUTF8StringEncoding error:NULL];
    CJEvent(@"session_script_export", @{@"written": @(written), @"target_pid": @(getpid())});
    [self share:written ? url : nil];
}
- (void)recordVersions {
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:@"Test environment" message:@"These values are included in diagnostics. Leave blank if unknown." preferredStyle:UIAlertControllerStyleAlert];
    NSArray *keys = @[@"livecontainerVersion", @"stikdebugVersion", @"stikdebugInstall"];
    NSArray *hints = @[@"LiveContainer 1 / 2 versions", @"StikDebug version / build", @"StikDebug: standalone or another LC"];
    for (NSUInteger i = 0; i < keys.count; i++) {
        [alert addTextFieldWithConfigurationHandler:^(UITextField *field) {
            field.placeholder = hints[i]; field.text = [NSUserDefaults.standardUserDefaults stringForKey:keys[i]];
            field.autocorrectionType = UITextAutocorrectionTypeNo;
        }];
    }
    [alert addAction:[UIAlertAction actionWithTitle:@"Save" style:UIAlertActionStyleDefault handler:^(UIAlertAction *action) {
        (void)action;
        for (NSUInteger i = 0; i < keys.count; i++) [NSUserDefaults.standardUserDefaults setObject:alert.textFields[i].text ?: @"" forKey:keys[i]];
        CJEvent(@"test_environment_recorded", @{});
    }]];
    [alert addAction:[UIAlertAction actionWithTitle:@"Cancel" style:UIAlertActionStyleCancel handler:nil]];
    [self presentViewController:alert animated:YES completion:nil];
}
- (void)endBackgroundTime {
    if (self.backgroundTask != UIBackgroundTaskInvalid) {
        [UIApplication.sharedApplication endBackgroundTask:self.backgroundTask]; self.backgroundTask = UIBackgroundTaskInvalid;
    }
}
- (void)resignActive {
#if !TARGET_OS_SIMULATOR
    if (self.graphicsRunning && !self.graphicsPaused) {
        self.displayLink.paused=YES; self.graphicsPaused=YES; self.lastFrameTimestamp=0;CJFrameReset(&gFrameMetrics);
        int result=0;
        BOOL ok=CJGraphicsCall("Suspend",&result) && result==1;
        if (!ok) self.graphicsFailed=YES;
        CJEvent(@"graphics_native_paused",@{@"passed":@(ok),@"frame_callbacks":@(self.frameCallbacks)});
    }
    CJGraphicsPlatformEvent(1);
#endif
}
- (void)willEnterForeground {
#if !TARGET_OS_SIMULATOR
    CJGraphicsPlatformEvent(3);
#endif
}
- (void)foreground {
    CJEvent(@"app_foreground",@{@"process":CJProcessState()});
#if !TARGET_OS_SIMULATOR
    CJGraphicsPlatformEvent(4);
    if (self.graphicsReady) [self startGraphics];
    if (self.graphicsRunning && self.graphicsPaused) {
        if (self.gameBackgroundUptime>0) {
            self.completedBackgroundSeconds=MAX(self.completedBackgroundSeconds,NSProcessInfo.processInfo.systemUptime-self.gameBackgroundUptime);
            self.gameBackgroundUptime=0;
        }
        int result=0; BOOL ok=[CJGraphicsPlatformSnapshot()[@"audio_session_active"] boolValue] && CJGraphicsCall("Resume",&result) && result==1;
        CJEvent(@"graphics_native_resumed",@{@"passed":@(ok),@"background_seconds":@(self.completedBackgroundSeconds),@"process":CJProcessState()});
        if (!ok) { self.graphicsFailed=YES; self.graphicsStopReason=@"resume_failure"; [self finishGraphics]; }
        else { self.graphicsPaused=NO; self.displayLink.paused=NO; }
    }
#endif
    [self endBackgroundTime]; [self poll];
}
- (void)background {
    CJEvent(@"app_background",@{@"process":CJProcessState()});
#if !TARGET_OS_SIMULATOR
    CJGraphicsPlatformEvent(2);
    if (self.graphicsRunning) self.gameBackgroundUptime=NSProcessInfo.processInfo.systemUptime;
#endif
}

@end

@interface CJSceneDelegate : UIResponder <UIWindowSceneDelegate>
@property(nonatomic, strong) UIWindow *window;
@end
@implementation CJSceneDelegate
- (void)scene:(UIScene *)scene willConnectToSession:(UISceneSession *)session options:(UISceneConnectionOptions *)options {
    (void)session; (void)options;
    if (![scene isKindOfClass:UIWindowScene.class]) return;
    self.window = [[UIWindow alloc] initWithWindowScene:(UIWindowScene *)scene];
    self.window.rootViewController = [CJViewController new]; [self.window makeKeyAndVisible];
}
@end

@interface CJAppDelegate : UIResponder <UIApplicationDelegate>
@end
@implementation CJAppDelegate
- (UIInterfaceOrientationMask)application:(UIApplication *)application supportedInterfaceOrientationsForWindow:(UIWindow *)window { (void)application;(void)window;return gLandscapeOnly?UIInterfaceOrientationMaskLandscape:UIInterfaceOrientationMaskAllButUpsideDown; }
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)options {
    (void)application; (void)options;
    [NSUserDefaults.standardUserDefaults registerDefaults:@{@"launcher.metrics":@YES,@"launcher.sjRegression":@NO,@"stikdebugInstall": @"LiveContainer 2 (owner supplied)", @"livecontainerVersion": @"3.8.9 (previous test; update if changed)", @"stikdebugVersion": @"3.1.9 (previous test; update if changed)"}];
    CJLog *log = [CJLog shared];
#if TARGET_OS_SIMULATOR
    if ([NSProcessInfo.processInfo.arguments containsObject:@"--probe-ui-test-path-alias"]) {
        NSURL *alias = [log.directory.URLByDeletingLastPathComponent URLByAppendingPathComponent:@"DiagnosticsAlias"];
        NSError *error = nil;
        // Simulator reinstalls can relocate the data container. Replace only
        // this fixture's symlink, and use a relative target that survives that.
        if ([NSFileManager.defaultManager destinationOfSymbolicLinkAtPath:alias.path error:NULL])
            [NSFileManager.defaultManager removeItemAtURL:alias error:&error];
        if (!error)
            [NSFileManager.defaultManager createSymbolicLinkAtPath:alias.path withDestinationPath:log.directory.lastPathComponent error:&error];
        if (!error) log.sessionURL = [alias URLByAppendingPathComponent:log.sessionURL.lastPathComponent];
        CJEvent(@"host_ui_path_alias_check", @{@"enabled": @(!error), @"simulator": @YES});
    }
#else
    (void)log;
#endif
    return YES;
}
@end

int main(int argc, char **argv) {
    @autoreleasepool { return UIApplicationMain(argc, argv, nil, NSStringFromClass(CJAppDelegate.class)); }
}
