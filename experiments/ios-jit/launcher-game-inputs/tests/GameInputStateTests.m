#import "CJGameInputState.h"

static NSUInteger checks;
static void Check(BOOL pass, NSString *label) {
    if (!pass) { NSLog(@"FAIL %@",label); exit(1); }
    checks++; printf("PASS %s\n",label.UTF8String);
}
static void Write(NSURL *root, NSString *path, id value) {
    NSURL *url=[root URLByAppendingPathComponent:path];
    [NSFileManager.defaultManager createDirectoryAtURL:url.URLByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:nil];
    [[NSJSONSerialization dataWithJSONObject:value options:0 error:nil] writeToURL:url atomically:YES];
}
int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc != 2) return 2;
        NSURL *root=[NSURL fileURLWithPath:@(argv[1]) isDirectory:YES];
        NSString *content=[@"a" stringByPaddingToLength:64 withString:@"a" startingAtIndex:0];
        NSString *legacy=[@"b" stringByPaddingToLength:64 withString:@"b" startingAtIndex:0];
        NSString *steam=[@"c" stringByPaddingToLength:64 withString:@"c" startingAtIndex:0];
        NSDictionary *info=@{@"game_content_aggregate_sha256":content,@"game_code_legacy_source_id":legacy,
            @"game_code_sources":@[@{@"source_id":legacy},@{@"source_id":steam}]};
        NSString *pointer=@"GameCode/v1/selected-source.json";
        Check(!CJGameInputsAvailable(root,info),@"fresh installation needs import");
        Write(root,[NSString stringWithFormat:@"GameLibrary/v1/%@/active.json",content],@{});
        Check(!CJGameInputsAvailable(root,info),@"assets alone need game code");
        Write(root,[NSString stringWithFormat:@"GameCode/v1/original/%@/source.json",legacy],@{@"source_id":legacy});
        Check(CJGameInputsAvailable(root,info),@"build52 originals available without new selection");
        Write(root,pointer,@{@"schema":@1,@"source":steam});
        Check(!CJGameInputsAvailable(root,info),@"missing selected Steam originals do not fall back");
        Write(root,[NSString stringWithFormat:@"GameCode/v1/original/%@/source.json",steam],@{@"source_id":steam});
        Check(CJGameInputsAvailable(root,info),@"selected Steam originals available after staged ZIP deletion");
        Write(root,pointer,@{@"schema":@1,@"source":legacy});
        Check(CJGameInputsAvailable(root,info),@"switch back to retained originals");
        Write(root,pointer,@{@"schema":@1,@"source":@"../../bad"});
        Check(!CJGameInputsAvailable(root,info),@"traversal selection rejected");
        Write(root,pointer,@{@"schema":@1,@"source":content});
        Check(!CJGameInputsAvailable(root,info),@"unknown digest rejected");
        Write(root,pointer,@{@"schema":@2,@"source":steam});
        Check(!CJGameInputsAvailable(root,info),@"unknown selection schema rejected");
        Write(root,pointer,@[@1]);
        Check(!CJGameInputsAvailable(root,info),@"wrong JSON type rejected");
        [@"bad JSON" writeToURL:[root URLByAppendingPathComponent:pointer] atomically:YES encoding:NSUTF8StringEncoding error:nil];
        Check(!CJGameInputsAvailable(root,info),@"malformed JSON rejected");
        Write(root,pointer,@{@"schema":@1,@"source":steam});
        NSMutableDictionary *bad=[info mutableCopy];bad[@"game_code_sources"]=@"bad";
        Check(!CJGameInputsAvailable(root,bad),@"malformed catalogue rejected");
        bad=[info mutableCopy];bad[@"game_content_aggregate_sha256"]=@"../bad";
        Check(!CJGameInputsAvailable(root,bad),@"invalid asset identity rejected");
        [NSFileManager.defaultManager removeItemAtURL:[root URLByAppendingPathComponent:pointer] error:nil];
        NSURL *target=[root URLByAppendingPathComponent:@"elsewhere.json"];Write(root,@"elsewhere.json",@{@"schema":@1,@"source":steam});
        [NSFileManager.defaultManager createSymbolicLinkAtURL:[root URLByAppendingPathComponent:pointer] withDestinationURL:target error:nil];
        Check(!CJGameInputsAvailable(root,info),@"selection symlink rejected");
        printf("PASS_NATIVE_GAME_INPUT_STATE checks=%lu\n",(unsigned long)checks);
    }
    return 0;
}
