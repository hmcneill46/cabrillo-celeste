#import "CJGameInputState.h"

static NSMutableArray<NSString *> *checks;
static void Check(BOOL passed, NSString *label) {
    if (!passed) { fprintf(stderr, "FAIL %s\n", label.UTF8String); exit(1); }
    [checks addObject:label];
}
static void Write(NSURL *root, NSString *path, id value) {
    NSURL *url = [root URLByAppendingPathComponent:path];
    NSError *error = nil;
    Check([NSFileManager.defaultManager createDirectoryAtURL:url.URLByDeletingLastPathComponent
                                withIntermediateDirectories:YES attributes:nil error:&error], @"fixture directory created");
    NSData *data = [NSJSONSerialization dataWithJSONObject:value options:0 error:&error];
    Check(data != nil && [data writeToURL:url options:NSDataWritingAtomic error:&error], @"fixture metadata written");
}
static id Read(const char *path) {
    NSData *data = [NSData dataWithContentsOfFile:@(path)];
    return data ? [NSJSONSerialization JSONObjectWithData:data options:0 error:nil] : nil;
}
static void Report(NSURL *root, NSString *status, NSArray *rejections) {
    NSDictionary *report = @{@"status":status, @"checks":checks, @"rejections":rejections,
                             @"actual_packaged_metadata":@YES, @"game_files_used":@NO};
    NSData *data = [NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted error:nil];
    [data writeToURL:[root URLByAppendingPathComponent:@"results.json"] atomically:YES];
    puts(status.UTF8String);
}
int main(int argc, const char **argv) { @autoreleasepool {
    if (argc != 4) return 2;
    checks = [NSMutableArray array];
    id info = Read(argv[1]), recipe = Read(argv[2]);
    NSURL *root = [NSURL fileURLWithPath:@(argv[3]) isDirectory:YES];
    [NSFileManager.defaultManager createDirectoryAtURL:root withIntermediateDirectories:YES attributes:nil error:nil];
    if (![info isKindOfClass:NSDictionary.class] || ![recipe isKindOfClass:NSDictionary.class]) return 2;
    NSArray *sources = recipe[@"sources"];
    if (![sources isKindOfClass:NSArray.class] || sources.count != 4 ||
        ![recipe[@"schema"] isEqual:@2] || ![recipe[@"legacy_source_id"] isKindOfClass:NSString.class]) return 2;
    NSMutableArray *expected = [NSMutableArray array];
    for (NSDictionary *source in sources)
        [expected addObject:@{@"source_id":source[@"source_id"], @"kind":source[@"kind"]}];
    NSMutableArray *rejections = [NSMutableArray array];
    if (![info[@"game_code_legacy_source_id"] isEqual:recipe[@"legacy_source_id"]])
        [rejections addObject:@"game_code_legacy_source_id differs from the actual package recipe"];
    if (![info[@"game_code_sources"] isEqual:expected])
        [rejections addObject:@"game_code_sources differs from the actual package recipe"];
    NSString *content = info[@"game_content_aggregate_sha256"];
    if (![content isKindOfClass:NSString.class] || content.length != 64) return 2;
    NSURL *legacy = [root URLByAppendingPathComponent:@"legacy"];
    Check(!CJGameInputsAvailable(legacy, info), @"fresh installation is unavailable");
    NSString *assetPath = [NSString stringWithFormat:@"GameLibrary/v1/%@/active.json", content];
    Write(legacy, assetPath, @{});
    Check(!CJGameInputsAvailable(legacy, info), @"retained assets without original code are unavailable");
    Write(legacy, [NSString stringWithFormat:@"GameCode/v1/original/%@/source.json", recipe[@"legacy_source_id"]],
          @{@"source_id":recipe[@"legacy_source_id"]});
    if (rejections.count) {
        // This runs the actual production function with the faulty IPA metadata;
        // the first combined package rejects valid retained originals here.
        Check(!CJGameInputsAvailable(legacy, info), @"missing packaged native catalogue reproduces retained-original rejection");
        Report(root, @"REJECTED_PACKAGE_NATIVE_GAME_INPUT_METADATA", rejections);
        return 3;
    }
    Check(CJGameInputsAvailable(legacy, info), @"legacy retained originals work without selected-source pointer or staged ZIP");
    for (NSDictionary *source in sources) {
        NSString *identity = source[@"source_id"];
        NSURL *documents = [root URLByAppendingPathComponent:identity];
        Write(documents, assetPath, @{});
        Write(documents, @"GameCode/v1/selected-source.json", @{@"schema":@1, @"source":identity});
        Check(!CJGameInputsAvailable(documents, info), @"selected original code is required");
        Write(documents, [NSString stringWithFormat:@"GameCode/v1/original/%@/source.json", identity],
              @{@"source_id":identity});
        Check(CJGameInputsAvailable(documents, info), [@"retained source available with no staged ZIP: " stringByAppendingString:identity]);
        Write(documents, @"GameCode/v1/selected-source.json", @{@"schema":@1, @"source":@"../../outside"});
        Check(!CJGameInputsAvailable(documents, info), @"invalid selected source remains rejected");
    }
    Report(root, @"PASS_PACKAGED_NATIVE_RETAINED_INPUTS", @[]);
    return 0;
} }
