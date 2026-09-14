#import "../src/CJModStore.h"
#import <CommonCrypto/CommonDigest.h>
#include <assert.h>
#include <unistd.h>
static NSString *Hash(NSData *data){unsigned char d[32];CC_SHA256(data.bytes,(CC_LONG)data.length,d);NSMutableString *s=[NSMutableString string];for(int i=0;i<32;i++)[s appendFormat:@"%02x",d[i]];return s;}
int main(int argc,char **argv){@autoreleasepool{
    assert(argc==2);NSURL *root=[NSURL fileURLWithPath:@(argv[1]) isDirectory:YES];NSFileManager *fm=NSFileManager.defaultManager;
    assert([fm createDirectoryAtURL:root withIntermediateDirectories:YES attributes:nil error:NULL]);
    NSMutableData *data=[NSMutableData dataWithLength:131073];for(NSUInteger i=0;i<data.length;i++)((unsigned char *)data.mutableBytes)[i]=(unsigned char)(i*17);
    NSURL *source=[root URLByAppendingPathComponent:@"source.zip"],*mods=[root URLByAppendingPathComponent:@"Mods"];
    assert([data writeToURL:source atomically:YES]);NSDictionary *row=@{@"bytes":@(data.length),@"sha256":Hash(data)};NSDictionary *manifest=@{@"test-v1.0.0.zip":row};NSError *error=nil;
    assert(CJInstallMod(source,mods,@"test-v1.0.0.zip",row,&error));assert(!error && CJVerifiedMods(mods,manifest).count==1);
    NSURL *saved=[mods URLByAppendingPathComponent:@"test-v1.0.0.zip"];NSData *prior=[NSData dataWithContentsOfURL:saved];
    assert(CJInstallMod(source,mods,@"test-v1.0.0.zip",row,&error));
    ((unsigned char *)data.mutableBytes)[400]^=1;assert([data writeToURL:source atomically:YES]);
    assert(!CJInstallMod(source,mods,@"test-v1.0.0.zip",row,&error));assert([[NSData dataWithContentsOfURL:saved] isEqual:prior]);
    assert(!CJInstallMod(source,mods,@"../escape.zip",row,&error));assert(![fm fileExistsAtPath:[root URLByAppendingPathComponent:@"escape.zip"].path]);
    assert(!CJInstallMod(source,mods,@"bad\\path.zip",row,&error));
    assert(!CJInstallMod(source,mods,@"test-v1.0.0.zip",@{@"bytes":@400000001,@"sha256":row[@"sha256"]},&error));
    assert([[data subdataWithRange:NSMakeRange(0,100)] writeToURL:source atomically:YES]);
    assert(!CJInstallMod(source,mods,@"short.zip",row,&error));
    NSURL *link=[root URLByAppendingPathComponent:@"linked.zip"];assert(symlink(saved.fileSystemRepresentation,link.fileSystemRepresentation)==0);
    assert(!CJInstallMod(link,mods,@"link.zip",row,&error));
    assert(!CJInstallMod(mods,mods,@"directory.zip",row,&error));
    assert(CJVerifiedMods(mods,@{@"test-v1.0.0.zip":@{@"bytes":row[@"bytes"],@"sha256":@"wrong"}}).count==0);
    for(NSString *n in [fm contentsOfDirectoryAtPath:mods.path error:NULL])assert(![n hasPrefix:@".install-"]);
    puts("PASS_ATOMIC_IMPORT_HASH_SIZE_PATH_SYMLINK_REIMPORT_AND_RETENTION");
    // Exact tiny real release verifies the actual URLSession redirect/download,
    // delegate-file lifetime and installation path without downloading the pack.
    NSDictionary *tiny=@{@"bytes":@200,@"sha256":@"042dce422374bb2c5d7a9355ac814daa13f582bc4b123a8b239a4e33bfcdad2f",@"url":@"https://gamebanana.com/mmdl/1286483"};
    NSDictionary *remote=@{@"ColoredLights-v1.2.0.zip":tiny};__block BOOL done=NO;__block NSError *failure=nil;
    CJModDownloader *downloader=[[CJModDownloader alloc] initWithDirectory:mods manifest:remote];
    [downloader startWithProgress:^(NSString *name,NSUInteger have,NSUInteger total,int64_t received,int64_t expected){(void)name;(void)have;assert(total==1 && received<=expected && NSThread.isMainThread);} completion:^(NSError *e){failure=e;done=YES;}];
    NSDate *end=[NSDate dateWithTimeIntervalSinceNow:90];while(!done && end.timeIntervalSinceNow>0)[NSRunLoop.currentRunLoop runUntilDate:[NSDate dateWithTimeIntervalSinceNow:0.02]];
    if(!done || failure){fprintf(stderr,"DOWNLOAD TEST: %s\n",failure.description.UTF8String);return 2;}
    assert(CJVerifiedMods(mods,remote).count==1);puts("PASS_REAL_HTTPS_DOWNLOAD_REDIRECT_HASH_INSTALL");
    done=NO;downloader=[[CJModDownloader alloc] initWithDirectory:mods manifest:remote];
    [downloader startWithProgress:^(NSString *n,NSUInteger h,NSUInteger t,int64_t r,int64_t e){(void)n;(void)h;(void)t;(void)r;(void)e;assert(0);} completion:^(NSError *e){assert(!e);done=YES;}];
    end=[NSDate dateWithTimeIntervalSinceNow:10];while(!done && end.timeIntervalSinceNow>0)[NSRunLoop.currentRunLoop runUntilDate:[NSDate dateWithTimeIntervalSinceNow:0.02]];assert(done);puts("PASS_REUSE_WITHOUT_NETWORK");
    done=NO;NSURL *cancel=[root URLByAppendingPathComponent:@"Cancelled"];
    downloader=[[CJModDownloader alloc] initWithDirectory:cancel manifest:remote];[downloader cancel];
    [downloader startWithProgress:^(NSString *n,NSUInteger h,NSUInteger t,int64_t r,int64_t e){(void)n;(void)h;(void)t;(void)r;(void)e;assert(0);} completion:^(NSError *e){assert(e);done=YES;}];
    end=[NSDate dateWithTimeIntervalSinceNow:10];while(!done && end.timeIntervalSinceNow>0)[NSRunLoop.currentRunLoop runUntilDate:[NSDate dateWithTimeIntervalSinceNow:0.02]];assert(done);assert(CJVerifiedMods(cancel,remote).count==0);
    assert([[NSData dataWithContentsOfURL:saved] isEqual:prior]);puts("PASS_CANCEL_PRESERVES_INSTALLED_MODS");
    return 0;
}}
