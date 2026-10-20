#import <Foundation/Foundation.h>
#import "CJPlatformOptions.h"
#include <assert.h>

static NSDictionary *Query(NSURL *url) {
    NSMutableDictionary *fields=[NSMutableDictionary dictionary];
    for (NSURLQueryItem *item in [NSURLComponents componentsWithURL:url resolvingAgainstBaseURL:NO].queryItems) fields[item.name]=item.value;
    return fields;
}
int main(void) { @autoreleasepool {
    NSString *suite=[@"CabrilloPlatformTests-" stringByAppendingString:NSUUID.UUID.UUIDString];
    NSUserDefaults *d=[[NSUserDefaults alloc] initWithSuiteName:suite];
    NSDictionary *old=CJPlatformOptions(d,(NSOperatingSystemVersion){15,8,8},NO,60);
    assert(![old[@"scriptRequired"] boolValue] && [old[@"provider"] isEqual:@"manual"]);
    assert([old[@"providers"] containsObject:@"trollstore"] && ![old[@"providers"] containsObject:@"stikdebug"]);
    [d setObject:@"trollstore" forKey:@"platform.jitProvider"];
    assert([CJPlatformOptions(d,(NSOperatingSystemVersion){15,8,8},NO,60)[@"provider"] isEqual:@"trollstore"]);
    assert(![CJPlatformOptions(d,(NSOperatingSystemVersion){15,8,8},YES,60)[@"providers"] containsObject:@"trollstore"]);
    [d removeObjectForKey:@"platform.jitProvider"];
    assert([CJPlatformOptions(d,(NSOperatingSystemVersion){17,3,0},NO,120)[@"provider"] isEqual:@"manual"]);
    assert([CJPlatformOptions(d,(NSOperatingSystemVersion){17,4,0},NO,120)[@"provider"] isEqual:@"stikdebug"]);
    NSDictionary *phone=CJPlatformOptions(d,(NSOperatingSystemVersion){26,5,0},YES,120);
    assert([phone[@"provider"] isEqual:@"livecontainer2"] && [phone[@"scriptRequired"] boolValue] && [phone[@"targetFPS"] intValue]==60);
    [d setBool:YES forKey:@"platform.highRefresh"];
    assert([CJPlatformOptions(d,(NSOperatingSystemVersion){26,5,0},YES,120)[@"targetFPS"] intValue]==120);
    assert([CJPlatformOptions(d,(NSOperatingSystemVersion){15,8,8},NO,60)[@"targetFPS"] intValue]==60);
    [d setObject:@"invalid" forKey:@"platform.jitProvider"];
    assert([CJPlatformOptions(d,(NSOperatingSystemVersion){26,5,0},NO,120)[@"provider"] isEqual:@"stikdebug"]);
    NSString *script=@"const request={pid:42,nonce:'new+/='};\n";
    NSURL *url=CJPlatformJITURL(@"livecontainer2",42,nil,@"fresh.js",script);
    assert([url.scheme isEqual:@"livecontainer2"]);
    NSData *decoded=[[NSData alloc] initWithBase64EncodedString:Query(url)[@"url"] options:0];
    NSURL *inner=[NSURL URLWithString:[[NSString alloc] initWithData:decoded encoding:NSUTF8StringEncoding]];
    NSDictionary *q=Query(inner);
    assert([inner.scheme isEqual:@"stikdebug"] && [q[@"pid"] isEqual:@"42"] && !q[@"bundle-id"] && [q[@"script-name"] isEqual:@"fresh.js"]);
    NSString *encoded=[q[@"script-data"] stringByReplacingOccurrencesOfString:@"-" withString:@"+"];
    encoded=[encoded stringByReplacingOccurrencesOfString:@"_" withString:@"/"];
    while(encoded.length%4) encoded=[encoded stringByAppendingString:@"="];
    assert([[[NSString alloc] initWithData:[[NSData alloc] initWithBase64EncodedString:encoded options:0] encoding:NSUTF8StringEncoding] isEqual:script]);
    q=Query(CJPlatformJITURL(@"stikdebug",42,@"test.bundle",nil,nil));
    assert([q[@"bundle-id"] isEqual:@"test.bundle"] && !q[@"script-name"] && !q[@"script-data"]);
    q=Query(CJPlatformJITURL(@"trollstore",42,@"test.bundle",nil,nil));
    assert([q[@"bundle-id"] isEqual:@"test.bundle"] && q.count==1);
    assert(!CJPlatformJITURL(@"trollstore",42,nil,nil,nil));
    assert(!CJPlatformJITURL(@"manual",42,@"test.bundle",nil,nil));
    assert(!CJPlatformJITURL(@"stikdebug",0,@"test.bundle",nil,nil));
    [d removePersistentDomainForName:suite];
    puts("PASS_PLATFORM_OPTIONS_AND_JIT_URLS");
} return 0; }
