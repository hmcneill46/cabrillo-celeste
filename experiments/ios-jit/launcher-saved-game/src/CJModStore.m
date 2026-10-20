#import "CJModStore.h"
#import <CommonCrypto/CommonDigest.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
static NSError *ModError(NSString *text) { return [NSError errorWithDomain:@"CJModStore" code:1 userInfo:@{NSLocalizedDescriptionKey:text}]; }
static BOOL SafeName(NSString *name) { return name.length && [name.lastPathComponent isEqualToString:name] && [name.pathExtension isEqualToString:@"zip"] && [name rangeOfCharacterFromSet:[[NSCharacterSet characterSetWithCharactersInString:@"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"] invertedSet]].location==NSNotFound; }

static NSString *DigestFD(int fd, uint64_t expected) {
    struct stat st; if (fstat(fd,&st) || !S_ISREG(st.st_mode) || st.st_size<0 || (uint64_t)st.st_size!=expected) return nil;
    CC_SHA256_CTX ctx; CC_SHA256_Init(&ctx); unsigned char buffer[65536], digest[CC_SHA256_DIGEST_LENGTH]; uint64_t total=0; ssize_t count;
    while ((count=read(fd,buffer,sizeof(buffer)))>0) { total+=(uint64_t)count; if(total>expected)return nil; CC_SHA256_Update(&ctx,buffer,(CC_LONG)count); }
    if (count<0 || total!=expected) return nil; CC_SHA256_Final(digest,&ctx);
    NSMutableString *hash=[NSMutableString string];for(unsigned i=0;i<sizeof(digest);i++)[hash appendFormat:@"%02x",digest[i]];return hash;
}
static BOOL Verified(NSURL *url, NSDictionary *expected) {
    int fd=open(url.fileSystemRepresentation,O_RDONLY|O_NOFOLLOW);if(fd<0)return NO;
    NSString *hash=DigestFD(fd,[expected[@"bytes"] unsignedLongLongValue]);close(fd);
    return hash && [hash isEqualToString:expected[@"sha256"]];
}
NSArray<NSString *> *CJVerifiedMods(NSURL *directory, NSDictionary *manifest) {
    NSMutableArray *verified=[NSMutableArray array];
    for (NSString *name in [manifest.allKeys sortedArrayUsingSelector:@selector(compare:)])
        if (SafeName(name) && Verified([directory URLByAppendingPathComponent:name],manifest[name])) [verified addObject:name];
    return verified;
}
BOOL CJInstallMod(NSURL *source, NSURL *directory, NSString *name, NSDictionary *expected, NSError **error) {
    if (!SafeName(name) || ![expected[@"bytes"] unsignedLongLongValue] || [expected[@"bytes"] unsignedLongLongValue]>400000000 || [expected[@"sha256"] length]!=64) { if(error)*error=ModError(@"Invalid pinned mod identity.");return NO; }
    NSFileManager *fm=NSFileManager.defaultManager;
    if(![fm createDirectoryAtURL:directory withIntermediateDirectories:YES attributes:@{NSFileProtectionKey:NSFileProtectionCompleteUntilFirstUserAuthentication} error:error])return NO;
    NSURL *destination=[directory URLByAppendingPathComponent:name];
    if(Verified(destination,expected) && Verified(source,expected))return YES;
    int input=open(source.fileSystemRepresentation,O_RDONLY|O_NOFOLLOW);if(input<0){if(error)*error=ModError(@"Could not open the selected mod ZIP.");return NO;}
    struct stat st;uint64_t bytes=[expected[@"bytes"] unsignedLongLongValue];
    if(fstat(input,&st) || !S_ISREG(st.st_mode) || st.st_size<0 || (uint64_t)st.st_size!=bytes){close(input);if(error)*error=ModError(@"Mod size does not match this test version.");return NO;}
    NSURL *temp=[directory URLByAppendingPathComponent:[@".install-" stringByAppendingString:NSUUID.UUID.UUIDString]];
    int output=open(temp.fileSystemRepresentation,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);BOOL ok=output>=0;
    unsigned char buffer[65536];uint64_t total=0;ssize_t count=0;
    while(ok && (count=read(input,buffer,sizeof(buffer)))>0){total+=(uint64_t)count;if(total>bytes){ok=NO;break;}ssize_t offset=0;while(offset<count){ssize_t wrote=write(output,buffer+offset,(size_t)(count-offset));if(wrote<=0){ok=NO;break;}offset+=wrote;}}
    ok=ok && count==0 && total==bytes;if(output>=0){ok=fsync(output)==0 && ok;close(output);}close(input);
    ok=ok && Verified(temp,expected);
    if(ok)ok=rename(temp.fileSystemRepresentation,destination.fileSystemRepresentation)==0;
    [fm removeItemAtURL:temp error:NULL];
    if(!ok && error)*error=ModError(@"The ZIP did not match its pinned checksum, or could not be saved. Existing files were retained.");
    return ok;
}
@interface CJModDownloader ()
@property NSURL *directory;
@property NSDictionary *manifest;
@property NSArray<NSString *> *pending;
@property NSUInteger index;
@property NSUInteger retained;
@property NSURLSession *session;
@property NSURLSessionDownloadTask *task;
@property NSError *installError;
@property BOOL finished;
@property(atomic) BOOL cancelled;
@property(copy) void (^progress)(NSString *,NSUInteger,NSUInteger,int64_t,int64_t);
@property(copy) void (^completion)(NSError *);
@end
@implementation CJModDownloader
- (instancetype)initWithDirectory:(NSURL *)directory manifest:(NSDictionary *)manifest {
    if((self=[super init])){_directory=directory;_manifest=[manifest copy];}return self;
}
- (void)startWithProgress:(void (^)(NSString *,NSUInteger,NSUInteger,int64_t,int64_t))progress completion:(void (^)(NSError *))completion {
    self.progress=progress;self.completion=completion;
    NSOperationQueue *queue=[NSOperationQueue new];queue.maxConcurrentOperationCount=1;
    NSURLSessionConfiguration *config=NSURLSessionConfiguration.ephemeralSessionConfiguration;
    config.allowsCellularAccess=NO;config.timeoutIntervalForRequest=60;config.timeoutIntervalForResource=900;config.HTTPMaximumConnectionsPerHost=1;
    self.session=[NSURLSession sessionWithConfiguration:config delegate:self delegateQueue:queue];
    [queue addOperationWithBlock:^{
        NSArray *verified=CJVerifiedMods(self.directory,self.manifest);self.retained=verified.count;
        NSMutableArray *missing=[[self.manifest.allKeys sortedArrayUsingSelector:@selector(compare:)] mutableCopy];[missing removeObjectsInArray:verified];self.pending=missing;
        [self next];
    }];
}
- (void)report:(NSString *)name received:(int64_t)received expected:(int64_t)expected {
    NSUInteger done=self.retained+self.index,total=self.manifest.count;
    dispatch_async(dispatch_get_main_queue(),^{if(self.progress)self.progress(name,done,total,received,expected);});
}
- (void)finish:(NSError *)error {
    if(self.finished)return;self.finished=YES;[self.session finishTasksAndInvalidate];self.task=nil;
    dispatch_async(dispatch_get_main_queue(),^{if(self.completion)self.completion(error);self.completion=nil;self.progress=nil;});
}
- (void)next {
    if(self.cancelled){[self finish:ModError(@"Download cancelled. Verified ZIPs are kept; tap Download to continue.")];return;}
    if(self.index==self.pending.count){[self finish:nil];return;}
    NSString *name=self.pending[self.index];NSDictionary *row=self.manifest[name];NSURL *url=[NSURL URLWithString:row[@"url"]?:@""];
    if(!SafeName(name) || ![url.scheme isEqualToString:@"https"]){[self finish:ModError(@"Missing pinned HTTPS download URL.")];return;}
    self.installError=nil;[self report:name received:0 expected:[row[@"bytes"] longLongValue]];
    self.task=[self.session downloadTaskWithURL:url];[self.task resume];
}
- (void)cancel { self.cancelled=YES;[self.task cancel]; }
- (void)URLSession:(NSURLSession *)session task:(NSURLSessionTask *)task willPerformHTTPRedirection:(NSHTTPURLResponse *)response newRequest:(NSURLRequest *)request completionHandler:(void (^)(NSURLRequest *))completionHandler {
    (void)session;(void)task;(void)response;completionHandler([request.URL.scheme isEqualToString:@"https"]?request:nil);
}
- (void)URLSession:(NSURLSession *)session downloadTask:(NSURLSessionDownloadTask *)task didWriteData:(int64_t)bytes totalBytesWritten:(int64_t)received totalBytesExpectedToWrite:(int64_t)serverExpected {
    (void)session;(void)bytes;int64_t expected=[self.manifest[self.pending[self.index]][@"bytes"] longLongValue];
    if(received>expected || (serverExpected>0 && serverExpected!=expected)){self.installError=ModError(@"Server response size does not match the pinned release.");[task cancel];return;}
    [self report:self.pending[self.index] received:received expected:expected];
}
- (void)URLSession:(NSURLSession *)session downloadTask:(NSURLSessionDownloadTask *)task didFinishDownloadingToURL:(NSURL *)location {
    (void)session;NSString *name=self.pending[self.index];
    if(self.cancelled)return;
    if(![task.response isKindOfClass:NSHTTPURLResponse.class] || ((NSHTTPURLResponse *)task.response).statusCode!=200){self.installError=ModError(@"The mod download server returned an error.");return;}
    NSError *error=nil;if(!CJInstallMod(location,self.directory,name,self.manifest[name],&error))self.installError=error;
}
- (void)URLSession:(NSURLSession *)session task:(NSURLSessionTask *)task didCompleteWithError:(NSError *)error {
    (void)session;(void)task;
    if(self.cancelled){[self finish:ModError(@"Download cancelled. Verified ZIPs are kept; tap Download to continue.")];return;}
    if(self.installError || error){[self finish:self.installError?:error];return;}
    self.index++;[self next];
}
@end
