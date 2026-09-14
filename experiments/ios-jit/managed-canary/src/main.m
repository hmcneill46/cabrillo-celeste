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
#import "ProbeProtocol.h"
#import "VMRange.h"
#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>
#import "CJCodeArena.h"
#import "CJManaged.h"

extern int csops(pid_t pid, unsigned int operations, void *useraddr, size_t usersize);
static const uint32_t CJDebuggedFlag = 0x10000000;
static CJMailbox gMailbox;

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
@property(nonatomic, strong) NSMutableArray *events;
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
    _events = [NSMutableArray array];
    _fd = -1;
    _sessionID = [[NSUUID UUID].UUIDString lowercaseString];
    NSURL *documents = [NSFileManager.defaultManager URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask].firstObject;
    _directory = [documents URLByAppendingPathComponent:@"Diagnostics" isDirectory:YES];
    NSError *error;
    if (![NSFileManager.defaultManager createDirectoryAtURL:_directory withIntermediateDirectories:YES attributes:@{NSFileProtectionKey: NSFileProtectionCompleteUntilFirstUserAuthentication} error:&error]) {
        _storageError = error.localizedDescription;
    }
    _sessionURL = [_directory URLByAppendingPathComponent:[NSString stringWithFormat:@"session-%@.jsonl", _sessionID]];
    _fd = open(_sessionURL.fileSystemRepresentation, O_WRONLY | O_CREAT | O_APPEND, 0600);
    if (_fd < 0) _storageError = [NSString stringWithUTF8String:strerror(errno)];
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
    return self;
}
- (void)event:(NSString *)name fields:(NSDictionary *)fields {
    NSDictionary *entry = @{@"event": name, @"time_unix": @([NSDate date].timeIntervalSince1970),
                            @"uptime_seconds": @(NSProcessInfo.processInfo.systemUptime),
                            @"session": _sessionID, @"fields": fields ?: @{}};
    dispatch_sync(_queue, ^{
        [self.events addObject:entry];
        if (self.fd >= 0) {
            NSMutableData *data = [[NSJSONSerialization dataWithJSONObject:entry options:NSJSONWritingSortedKeys error:NULL] mutableCopy];
            [data appendBytes:"\n" length:1];
            const uint8_t *p = data.bytes;
            size_t left = data.length;
            while (left > 0) {
                ssize_t count = write(self.fd, p, left);
                if (count < 0 && errno == EINTR) continue;
                if (count <= 0) { self.storageError = @"Could not append persistent log"; break; }
                p += count; left -= (size_t)count;
            }
            // Each pre-execution stage must survive a native crash or termination.
            if (fsync(self.fd) != 0) self.storageError = @"Could not sync persistent log";
        }
    });
    NSDictionary *consoleFields = [name isEqualToString:@"native_launch"] ? @{@"build_id": self.buildInfo[@"build_id"] ?: @"unknown", @"device": self.deviceInfo} : fields;
    NSLog(@"[CelesteJITCanary] %@ %@", name, consoleFields ?: @{});
    // The view's 0.5 s timer renders a snapshot. Never queue a TextKit refresh
    // for every JIT callback; the persistent event stream remains lossless.
}
- (NSArray *)snapshot {
    __block NSArray *result;
    dispatch_sync(_queue, ^{ result = [self.events copy]; });
    return result;
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
        if (![url.pathExtension isEqualToString:@"jsonl"] || [url.lastPathComponent isEqualToString:_sessionURL.lastPathComponent] || previous.count >= 5) continue;
        NSString *raw = [NSString stringWithContentsOfURL:url encoding:NSUTF8StringEncoding error:NULL];
        NSMutableArray *records = [NSMutableArray array];
        for (NSString *line in [raw componentsSeparatedByString:@"\n"]) {
            if (line.length == 0) continue;
            id event = [NSJSONSerialization JSONObjectWithData:[line dataUsingEncoding:NSUTF8StringEncoding] options:0 error:NULL];
            if (event) [records addObject:event];
        }
        if ([records.firstObject[@"session"] isEqualToString:_sessionID]) continue;
        [previous addObject:@{@"file": url.lastPathComponent, @"events": records,
                             @"native_console_tail": CJConsoleTail(_directory, records.firstObject[@"session"] ?: @"unknown")}];
    }
    NSUserDefaults *settings = NSUserDefaults.standardUserDefaults;
    NSDictionary *bundle = @{@"schema": @1, @"kind": @"celeste-jit-managed-canary-diagnostics",
                             @"session": _sessionID, @"build": _buildInfo ?: @{}, @"device": _deviceInfo,
                             @"reported_livecontainer_version": [settings stringForKey:@"livecontainerVersion"] ?: @"not supplied",
                             @"reported_stikdebug_version": [settings stringForKey:@"stikdebugVersion"] ?: @"not supplied",
                             @"reported_stikdebug_install": [settings stringForKey:@"stikdebugInstall"] ?: @"not supplied",
                             @"storage_error": _storageError ?: NSNull.null,
                             @"current_events": [self snapshot], @"previous_sessions": previous,
                             @"native_console_tail": CJConsoleTail(_directory, _sessionID),
                             @"scope": @"Imported DLL and Mono ARM64 JIT canary. No MonoMod, Celeste or Everest yet."};
    NSData *data = [NSJSONSerialization dataWithJSONObject:bundle options:NSJSONWritingPrettyPrinted | NSJSONWritingSortedKeys error:NULL];
    NSURL *url = [_directory URLByAppendingPathComponent:[NSString stringWithFormat:@"CelesteJIT-%@.diagnostics.json", _sessionID]];
    return [data writeToURL:url options:NSDataWritingAtomic error:NULL] ? url : nil;
}
@end

static void CJEvent(NSString *name, NSDictionary *fields) { [[CJLog shared] event:name fields:fields]; }
static void __attribute__((unused)) CJAllocatorEvent(const char *name, uintptr_t address, size_t length, size_t used) {
    CJEvent([NSString stringWithUTF8String:name], @{@"address": [NSString stringWithFormat:@"0x%llx", (unsigned long long)address],
                                                  @"requested_bytes": @(length), @"total_reserved_bytes": @(used)});
}

#if !TARGET_OS_SIMULATOR
static void CJRecordVMEntry(uintptr_t cursor, const CJVMEntry *entry, size_t checked, void *context) {
    NSMutableArray *entries = (__bridge NSMutableArray *)context;
    [entries addObject:@{@"query_address": [NSString stringWithFormat:@"0x%llx", (unsigned long long)cursor],
                         @"region_start": [NSString stringWithFormat:@"0x%llx", (unsigned long long)entry->address],
                         @"region_bytes": @(entry->length), @"checked_bytes": @(checked),
                         @"protection": @(entry->protection), @"maximum_protection": @(entry->maximum_protection)}];
}
static NSDictionary *CJRegion(uintptr_t pointer, size_t needed) {
    NSMutableArray *entries = [NSMutableArray array];
    CJVMRangeReport report = CJInspectVMRange(pointer, needed, CJQueryDarwinVMEntry, NULL, CJRecordVMEntry, (__bridge void *)entries);
    return @{@"address": [NSString stringWithFormat:@"0x%llx", (unsigned long long)pointer], @"result": @(report.query_result),
             @"range_status": [NSString stringWithUTF8String:CJVMRangeStatusName(report.status)],
             @"covers_requested_bytes": @(report.status == CJVMRangeComplete), @"protection": @(report.common_protection),
             @"union_protection": @(report.union_protection), @"maximum_protection": @(report.maximum_protection_intersection),
             @"requested_bytes": @(needed), @"mapped_bytes": @(report.covered_bytes), @"entry_count": @(report.entry_count), @"entries": entries};
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
    BOOL bounds = first > 0 && second > 0 && first < limit - CJ_ARENA_LENGTH && second < limit - CJ_ARENA_LENGTH &&
                  length == CJ_ARENA_LENGTH && getpagesize() == 16384 && first % getpagesize() == 0 && second % getpagesize() == 0 &&
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
@property(nonatomic, strong) UIButton *dllButton;
@property(nonatomic, strong) NSURL *importedDLL;
@property(nonatomic) BOOL nativePassed;
@property(nonatomic) BOOL managedAttempted;
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
        [scroll.leadingAnchor constraintEqualToAnchor:self.view.leadingAnchor], [scroll.trailingAnchor constraintEqualToAnchor:self.view.trailingAnchor],
        [self.stack.topAnchor constraintEqualToAnchor:scroll.contentLayoutGuide.topAnchor constant:24],
        [self.stack.bottomAnchor constraintEqualToAnchor:scroll.contentLayoutGuide.bottomAnchor constant:-24],
        [self.stack.leadingAnchor constraintEqualToAnchor:scroll.contentLayoutGuide.leadingAnchor constant:24],
        [self.stack.trailingAnchor constraintEqualToAnchor:scroll.contentLayoutGuide.trailingAnchor constant:-24],
        [self.stack.widthAnchor constraintEqualToAnchor:scroll.frameLayoutGuide.widthAnchor constant:-48]]];
    UILabel *eyebrow = [self label:@"CELESTE  /  JIT RESEARCH" size:12 weight:UIFontWeightSemibold];
    eyebrow.textColor = [UIColor colorWithRed:1 green:0.55 blue:0.63 alpha:1];
    [self.stack addArrangedSubview:eyebrow];
    [self.stack addArrangedSubview:[self label:@"Managed JIT canary" size:31 weight:UIFontWeightBold]];
    [self.stack addArrangedSubview:[self label:@"Import the test DLL, enable JIT, then start the managed test." size:17 weight:UIFontWeightRegular]];
    self.statusLabel = [self label:@"READY · IMPORT TEST DLL" size:19 weight:UIFontWeightBold];
    self.statusLabel.accessibilityIdentifier = @"probe.status";
    [self.stack addArrangedSubview:self.statusLabel];
    self.detailLabel = [self label:@"Build 6 · This tests the runtime needed for Celeste and Everest. Choose Canary-v0.2.2.dll below. Keep Launch with JIT OFF in LiveContainer." size:15 weight:UIFontWeightRegular];
    self.detailLabel.textColor = UIColor.secondaryLabelColor;
    [self.stack addArrangedSubview:self.detailLabel];
    NSDictionary *process = CJProcessState();
    self.processLabel = [self label:[NSString stringWithFormat:@"PID %@ · %@\niOS %@ · %@", process[@"pid"], process[@"kernel_process_name"], UIDevice.currentDevice.systemVersion, [CJLog shared].buildInfo[@"build_id"] ?: @"unknown build"] size:13 weight:UIFontWeightMedium];
    self.processLabel.font = [UIFont monospacedSystemFontOfSize:12 weight:UIFontWeightRegular];
    self.processLabel.textColor = UIColor.secondaryLabelColor;
    [self.stack addArrangedSubview:self.processLabel];
    self.dllButton = [self button:@"1. Import Canary DLL" action:@selector(importDLL) prominent:YES];
    [self.stack addArrangedSubview:self.dllButton];
    self.enableButton = [self button:@"2. Enable via LiveContainer 2" action:@selector(enableJIT) prominent:YES];
    self.enableButton.accessibilityIdentifier = @"probe.enable";
    [self.stack addArrangedSubview:self.enableButton];
    UIButton *export = [self button:@"Export diagnostics" action:@selector(exportLogs) prominent:NO];
    export.accessibilityIdentifier = @"probe.export";
    [self.stack addArrangedSubview:export];
    self.runButton = [self button:@"3. Run managed JIT test" action:@selector(runManaged) prominent:YES];
    self.runButton.enabled = NO; [self.stack addArrangedSubview:self.runButton];
    self.scriptButton = [self button:@"Export session script (manual setup)" action:@selector(exportScript) prominent:NO];
    [self.stack addArrangedSubview:self.scriptButton];
    self.importedButton = [self button:@"Use imported script in LiveContainer 2" action:@selector(enableImportedScript) prominent:NO];
    [self.stack addArrangedSubview:self.importedButton];
    [self.stack addArrangedSubview:[self button:@"Record LiveContainer / StikDebug versions" action:@selector(recordVersions) prominent:NO]];
    [self.stack addArrangedSubview:[self label:@"What this checks" size:18 weight:UIFontWeightSemibold]];
    [self.stack addArrangedSubview:[self label:@"A separately imported .NET DLL, real JIT method addresses, Reflection.Emit, generic and struct returns, exception handling, GC, a managed thread and a native callback." size:14 weight:UIFontWeightRegular]];
    UILabel *scope = [self label:@"This is a runtime probe. Celeste, Everest and game mods come after the runtime and hook tests." size:13 weight:UIFontWeightRegular];
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
    self.timer = [NSTimer scheduledTimerWithTimeInterval:0.5 target:self selector:@selector(poll) userInfo:nil repeats:YES];
#if TARGET_OS_SIMULATOR
    self.enableButton.enabled = NO; self.scriptButton.enabled = NO; self.importedButton.enabled = NO;
    self.statusLabel.text = @"SIMULATOR · UI ONLY";
    self.detailLabel.text = @"This run checks startup, layout and log export. Native JIT checks are disabled in the simulator.";
#endif
    if ([CJLog shared].storageError) {
        self.enableButton.enabled = NO; self.scriptButton.enabled = NO; self.importedButton.enabled = NO;
        self.statusLabel.text = @"LOG STORAGE FAILED"; self.detailLabel.text = [CJLog shared].storageError;
    }
    [self refreshLog];
#if TARGET_OS_SIMULATOR
    if ([NSProcessInfo.processInfo.arguments containsObject:@"--canary-ui-test-import"]) {
        NSURL *fixture = [[CJLog shared].directory.URLByDeletingLastPathComponent URLByAppendingPathComponent:@"test-fixture.dll"];
        UIDocumentPickerViewController *testPicker = [[UIDocumentPickerViewController alloc] initForOpeningContentTypes:@[UTTypeItem] asCopy:YES];
        [self documentPicker:testPicker didPickDocumentsAtURLs:@[fixture]];
        CJEvent(@"host_ui_import_check", @{@"imported": @(self.importedDLL != nil), @"managed_run_disabled_without_jit": @(!self.runButton.enabled)});
        fprintf(stderr, "CJIT native console recovery sentinel\n");
    }
#endif
    if ([NSProcessInfo.processInfo.arguments containsObject:@"--probe-ui-test-export"]) {
#if TARGET_OS_SIMULATOR
        if ([NSProcessInfo.processInfo.arguments containsObject:@"--canary-ui-test-log-burst"]) {
            dispatch_async(dispatch_get_global_queue(QOS_CLASS_UTILITY, 0), ^{
                for (int i = 0; i < 800; i++) CJEvent(i == 799 ? @"host_ui_burst_complete" : @"host_ui_burst", @{@"index": @(i)});
                dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 2 * NSEC_PER_SEC), dispatch_get_main_queue(), ^{
                    CJEvent(@"host_ui_log_burst_check", @{@"rendered_through_burst": @([self.logView.text containsString:@"host_ui_burst_complete"])});
                    [[CJLog shared] exportDiagnostics];
                });
            });
            return;
        }
#endif
        dispatch_async(dispatch_get_main_queue(), ^{
            NSURL *url = [[CJLog shared] exportDiagnostics];
            CJEvent(@"host_ui_export_check", @{@"written": @(url != nil), @"simulator": @(TARGET_OS_SIMULATOR)});
        });
    }
}
- (void)refreshLog {
    NSMutableString *text = [NSMutableString string];
    NSArray *events = [[CJLog shared] snapshot];
    if (events.count == self.renderedEventCount) return;
    self.renderedEventCount = events.count;
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
    memset(&gMailbox, 0, sizeof(gMailbox));
    memcpy(gMailbox.magic, "CJT0MBX1", 8);
    gMailbox.version = CJ_PROTOCOL_VERSION;
    arc4random_buf(gMailbox.nonce, sizeof(gMailbox.nonce));
    gMailbox.pid = getpid(); gMailbox.requestedLength = CJ_ARENA_LENGTH;
    gMailbox.status = 1;
    NSDictionary *request = @{@"protocol": @1, @"pid": @(getpid()),
                              @"mailbox": [NSString stringWithFormat:@"0x%llx", (unsigned long long)(uintptr_t)&gMailbox],
                              @"header": CJHex(&gMailbox, 48), @"length": @(CJ_ARENA_LENGTH), @"pageSize": @(getpagesize()),
                              @"requestID": [CJLog shared].sessionID};
    NSData *json = [NSJSONSerialization dataWithJSONObject:request options:NSJSONWritingSortedKeys error:NULL];
    NSString *source = [NSString stringWithContentsOfURL:[NSBundle.mainBundle URLForResource:@"celeste-jit-probe" withExtension:@"js"] encoding:NSUTF8StringEncoding error:NULL];
    if (!json || !source) { self.statusLabel.text = @"SCRIPT RESOURCE MISSING"; return NO; }
    self.sessionScript = [NSString stringWithFormat:@"const CJIT_REQUEST = %@;\n%@", [[NSString alloc] initWithData:json encoding:NSUTF8StringEncoding], source];
    self.requestTime = NSDate.date;
    CJEvent(@"jit_request_created", @{@"protocol": @1, @"pid": @(getpid()), @"request_id": [CJLog shared].sessionID,
                                     @"mailbox": request[@"mailbox"], @"arena_count": @2, @"bytes_per_arena": @(CJ_ARENA_LENGTH),
                                     @"session_script_sha256": CJSHA256([self.sessionScript dataUsingEncoding:NSUTF8StringEncoding]),
                                     @"script_template_sha256": [CJLog shared].buildInfo[@"script_template_sha256"] ?: @"unknown"});
    self.statusLabel.text = @"WAITING FOR STIKDEBUG";
    self.detailLabel.text = @"StikDebug must already be running in LiveContainer 2. Complete its request, then switch back to this running probe in LiveContainer 1. The checks start after a valid reply and detach.";
    return YES;
}
- (NSString *)sessionScriptName {
    return [NSString stringWithFormat:@"celeste-managed-PID%d-%@.js", getpid(), [CJLog shared].sessionID];
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
            self.busy = NO; self.nativePassed = passed; self.runButton.enabled = passed && self.importedDLL != nil;
            self.statusLabel.text = passed ? @"NATIVE PASS · READY FOR MONO" : @"FAIL · CHECK THE LOG";
            self.statusLabel.textColor = passed ? UIColor.systemGreenColor : UIColor.systemOrangeColor;
            self.detailLabel.text = passed ? @"Prepared memory passed. Import the Canary DLL if needed, then tap Run managed JIT test. This runs once per launch." : @"Export diagnostics and the StikDebug script log. The managed runtime has not started because native preparation failed.";
        });
    });
}
- (void)importDLL {
    if (self.busy || self.managedAttempted) return;
    UIDocumentPickerViewController *picker = [[UIDocumentPickerViewController alloc] initForOpeningContentTypes:@[UTTypeItem] asCopy:YES];
    picker.delegate = self; picker.allowsMultipleSelection = NO;
    [self presentViewController:picker animated:YES completion:nil];
}
- (void)documentPicker:(UIDocumentPickerViewController *)controller didPickDocumentsAtURLs:(NSArray<NSURL *> *)urls {
    (void)controller;
    if (self.busy || self.managedAttempted || urls.count != 1) return;
    NSURL *selected = urls.firstObject;
    BOOL scoped = [selected startAccessingSecurityScopedResource];
    NSNumber *size = nil;
    [selected getResourceValue:&size forKey:NSURLFileSizeKey error:NULL];
    NSData *data = nil;
    if ([selected.pathExtension.lowercaseString isEqualToString:@"dll"] && size && size.unsignedLongLongValue <= 1048576)
        data = [NSData dataWithContentsOfURL:selected options:0 error:NULL];
    if (scoped) [selected stopAccessingSecurityScopedResource];
    const uint8_t *bytes = data.bytes;
    if (data.length < 512 || bytes[0] != 'M' || bytes[1] != 'Z') {
        CJEvent(@"dll_import_rejected", @{@"reason": @"Select the supplied Canary DLL (under 1 MiB)"});
        self.detailLabel.text = @"Choose Canary-v0.2.2.dll from the build 6 folder. The selected file is not a suitable test DLL."; return;
    }
    NSString *hash = CJSHA256(data);
    NSURL *documents = [CJLog shared].directory.URLByDeletingLastPathComponent;
    NSURL *imports = [documents URLByAppendingPathComponent:@"Imports" isDirectory:YES];
    NSError *error = nil;
    [NSFileManager.defaultManager createDirectoryAtURL:imports withIntermediateDirectories:YES attributes:nil error:&error];
    NSURL *saved = [imports URLByAppendingPathComponent:[hash stringByAppendingPathExtension:@"dll"]];
    BOOL written = !error && [data writeToURL:saved options:NSDataWritingAtomic error:&error];
    if (!written) { CJEvent(@"dll_import_failed", @{@"error": error.localizedDescription ?: @"unknown"}); return; }
    self.importedDLL = saved;
    [self.dllButton setTitle:@"Test DLL imported ✓" forState:UIControlStateNormal];
    CJEvent(@"dll_imported", @{@"original_filename": selected.lastPathComponent, @"sha256": hash, @"bytes": @(data.length)});
    self.detailLabel.text = self.nativePassed ? @"DLL imported. Tap Run managed JIT test." : @"DLL imported. Enable JIT through LiveContainer 2, then return here.";
    self.runButton.enabled = self.nativePassed;
}
- (void)runManaged {
    if (self.busy || self.managedAttempted || !self.nativePassed || !self.importedDLL) return;
    NSDictionary *state = CJProcessState();
    if (![state[@"trace_known"] boolValue] || [state[@"traced"] boolValue] || ![state[@"cs_debugged"] boolValue]) {
        CJEvent(@"managed_start_rejected", state); self.detailLabel.text = @"Debugger detach could not be verified. Export diagnostics."; return;
    }
    self.managedAttempted = YES; self.busy = YES;
    self.runButton.enabled = NO; self.dllButton.enabled = NO;
    self.statusLabel.text = @"RUNNING MANAGED JIT";
    self.detailLabel.text = @"Startup and each JIT stage are saved. If this closes, reopen the app and export diagnostics before trying again.";
    NSURL *dll = self.importedDLL;
    NSData *data = [NSData dataWithContentsOfURL:dll];
    CJEvent(@"managed_test_start", @{@"process": state, @"imported_dll_sha256": data ? CJSHA256(data) : @"unreadable"});
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        @autoreleasepool {
            BOOL pass = NO;
#if !TARGET_OS_SIMULATOR
            CJCodeRegion regions[2] = {{gArenas[0].rx, gArenas[0].rw, gArenas[0].length}, {gArenas[1].rx, gArenas[1].rw, gArenas[1].length}};
            BOOL allocator = cj_code_arena_initialize(regions, getpagesize(), CJAllocatorEvent);
            CJEvent(@"managed_allocator_initialized", @{@"success": @(allocator)});
            if (allocator) pass = CJManagedRun(dll, [NSBundle.mainBundle.bundleURL URLByAppendingPathComponent:@"Managed" isDirectory:YES], ^(NSString *event, NSDictionary *fields) { CJEvent(event, fields); });
#endif
            CJEvent(pass ? @"g1_managed_pass" : @"g1_managed_fail", @{@"scope": @"canary_only_no_hooks_or_game", @"process": CJProcessState()});
            dispatch_async(dispatch_get_main_queue(), ^{
                self.busy = NO;
                self.statusLabel.text = pass ? @"PASS · MANAGED JIT" : @"STOPPED · EXPORT DIAGNOSTICS";
                self.statusLabel.textColor = pass ? UIColor.systemGreenColor : UIColor.systemOrangeColor;
                self.detailLabel.text = pass ? @"The imported DLL and runtime checks passed. Export diagnostics for review. Hook testing is the next step toward Everest." : @"The runtime did not complete every check. Export diagnostics; the stage and native console will identify the next fix. Relaunch for another attempt.";
                CJEvent(@"managed_result_presented", @{@"passed": @(pass)});
                if (pass) dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 5 * NSEC_PER_SEC), dispatch_get_main_queue(), ^{
                    CJEvent(@"managed_post_run_alive", @{@"seconds_after_result": @5, @"foreground": @(UIApplication.sharedApplication.applicationState == UIApplicationStateActive), @"process": CJProcessState()});
                });
            });
        }
    });
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
- (void)foreground { CJEvent(@"app_foreground", @{@"process": CJProcessState()}); [self endBackgroundTime]; [self poll]; }
- (void)background { CJEvent(@"app_background", @{@"process": CJProcessState()}); }
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
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)options {
    (void)application; (void)options;
    [NSUserDefaults.standardUserDefaults registerDefaults:@{@"stikdebugInstall": @"LiveContainer 2 (owner supplied)", @"livecontainerVersion": @"3.8.9 (previous test; update if changed)", @"stikdebugVersion": @"3.1.9 (previous test; update if changed)"}];
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
