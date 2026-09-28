// Host-only ContentKit regression for the actual app43 JIT/return URL builders.
// Constructs URLs and converts content in memory; opens no app and runs no script.
#import <Foundation/Foundation.h>
#import <dlfcn.h>
#import "CJPlatformOptions.h"
#import "CJShortcutPlatform.h"
#import "CJShortcutSession.h"

@protocol ContentAPI
+ (id)itemWithObject:(id)object;
- (void)getObjectRepresentations:(void (^)(NSArray *))handler forClass:(Class)cls;
@end

static NSDictionary *Check(NSString *name, NSURL *url, BOOL typed, BOOL exactExpected) {
    NSString *text=url.absoluteString;
    id<ContentAPI> item=[(id<ContentAPI>)NSClassFromString(@"WFContentItem") itemWithObject:typed?url:text];
    __block NSArray *objects=nil;__block BOOL done=NO;
    [item getObjectRepresentations:^(NSArray *values){objects=values;done=YES;} forClass:NSURL.class];
    NSDate *deadline=[NSDate dateWithTimeIntervalSinceNow:5];
    while(!done && deadline.timeIntervalSinceNow>0)
        [NSRunLoop.currentRunLoop runUntilDate:[NSDate dateWithTimeIntervalSinceNow:0.01]];
    NSURL *received=objects.count==1 && [objects.firstObject isKindOfClass:NSURL.class]?objects.firstObject:nil;
    BOOL exact=[received.absoluteString isEqual:text];
    BOOL missingValue=NO;
    for(NSURLQueryItem *q in [NSURLComponents componentsWithURL:received resolvingAgainstBaseURL:NO].queryItems)
        if([@[@"open-url",@"script-data"] containsObject:q.name] && !q.value)missingValue=YES;
    BOOL pass=done && received && exact==exactExpected;
    if(!exactExpected)pass=pass && missingValue;
    return @{@"name":name,@"typed":@(typed),@"content_class":NSStringFromClass([(id)item class]),
        @"input_length":@(text.length),@"received_length":@(received.absoluteString.length),
        @"exact":@(exact),@"missing_query_value":@(missingValue),@"pass":@(pass)};
}

int main(void) { @autoreleasepool {
    if(!dlopen("/System/Library/PrivateFrameworks/WorkflowKit.framework/WorkflowKit",RTLD_LAZY|RTLD_GLOBAL))return 2;
    NSMutableArray *results=[NSMutableArray array];
    for(NSNumber *size in @[@60,@1024,@8192]) {
        NSString *script=[@"// Harmless URL fixture, never executed. " stringByPaddingToLength:size.integerValue withString:@"example text 12345; " startingAtIndex:0];
        NSURL *direct=CJPlatformJITURL(@"stikdebug",5678,@"example.host",@"fresh-example.js",script);
        NSDictionary *guest=@{@"bundleFolder":@"Stik Debug+example.app",@"containerFolder":@"example-data"};
        NSURL *container=CJShortcutStikGuestURL(guest,direct);
        for(NSString *route in @[@"direct",@"container"]) {
            NSURL *url=[route isEqual:@"direct"]?direct:container;
            for(NSNumber *typed in @[@NO,@YES])
                [results addObject:Check([NSString stringWithFormat:@"%@-%@",route,size],url,typed.boolValue,typed.boolValue || size.integerValue==60)];
        }
    }
    NSURL *run=CJShortcutRunURL(@"jit",@"01234567-89AB-CDEF-0123-456789ABCDEF",@{},@"livecontainer");
    for(NSURLQueryItem *q in [NSURLComponents componentsWithURL:run resolvingAgainstBaseURL:NO].queryItems)
        if([q.name hasPrefix:@"x-"])for(NSNumber *typed in @[@NO,@YES])
            [results addObject:Check(q.name,[NSURL URLWithString:q.value],typed.boolValue,YES)];
    BOOL all=YES;NSUInteger originalFailures=0;
    for(NSDictionary *r in results){all=all&&[r[@"pass"] boolValue];if(![r[@"typed"] boolValue] && ![r[@"exact"] boolValue])originalFailures++;}
    NSDictionary *result=@{@"status":all?@"PASS_APPLE_URL_CONTENT_CONTROLS":@"FAIL_APPLE_URL_CONTENT_CONTROLS",@"checks":@(results.count),@"original_truncation_controls":@(originalFailures),@"results":results};
    puts([[NSString alloc] initWithData:[NSJSONSerialization dataWithJSONObject:result options:NSJSONWritingPrettyPrinted error:NULL] encoding:NSUTF8StringEncoding].UTF8String);
    return all?0:1;
}}
