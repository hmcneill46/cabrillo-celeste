#import "CJContentImport.h"
#import <CommonCrypto/CommonDigest.h>
#include <stdatomic.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
static _Atomic(int) gCancelled, gFiles;
static _Atomic(int64_t) gDone, gTotal;
void CJContentSetCancelled(BOOL value) { atomic_store(&gCancelled,value); if(!value){atomic_store(&gDone,0);atomic_store(&gTotal,0);atomic_store(&gFiles,0);} }
int CJContentShouldCancel(void) { return atomic_load(&gCancelled); }
void CJContentProgress(int64_t done,int64_t total,int files) { atomic_store(&gDone,done);atomic_store(&gTotal,total);atomic_store(&gFiles,files); }
int64_t CJContentFreeBytes(const char *path) {
    NSString *p=path?[NSString stringWithUTF8String:path]:nil;
    NSDictionary *attributes=p?[NSFileManager.defaultManager attributesOfFileSystemForPath:p error:NULL]:nil;
    return [attributes[NSFileSystemFreeSize] longLongValue];
}
NSDictionary *CJContentSnapshot(void) { return @{@"bytes":@(atomic_load(&gDone)),@"total":@(atomic_load(&gTotal)),@"files":@(atomic_load(&gFiles)),@"cancelled":@(atomic_load(&gCancelled))}; }
static NSError *Failure(NSString *message) { return [NSError errorWithDomain:@"CelesteContentImport" code:1 userInfo:@{NSLocalizedDescriptionKey:message}]; }
void CJStageContentArchive(NSURL *source,NSURL *directory,int64_t contentBytes,void (^log)(NSString *,NSDictionary *),void (^completion)(BOOL,NSError *)) {
    CJContentSetCancelled(NO);
    log(@"content_scope_access_start",@{@"source_url":source.absoluteString ?: @""});
    BOOL scoped=[source startAccessingSecurityScopedResource];
    log(@"content_scope_access_result",@{@"granted":@(scoped)});
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0), ^{
        @autoreleasepool {
            __block NSError *failure=nil;
            __block BOOL saved=NO;
            NSURL *temporary=[directory URLByAppendingPathComponent:@"game-input.zip.partial"];
            NSURL *destination=[directory URLByAppendingPathComponent:@"game-input.zip"];
            NSFileManager *fm=NSFileManager.defaultManager;
            [fm createDirectoryAtURL:directory withIntermediateDirectories:YES attributes:@{NSFileProtectionKey:NSFileProtectionCompleteUntilFirstUserAuthentication} error:&failure];
            if(!failure) {
                NSDictionary *attributes=[fm attributesOfItemAtPath:directory.path error:&failure];
                if(![attributes[NSFileType] isEqualToString:NSFileTypeDirectory])failure=Failure(@"Import storage is not a regular directory.");
            }
            if(!failure) {
                // This exact path is an app-owned interrupted copy, never a user source.
                if([fm fileExistsAtPath:temporary.path]) [fm removeItemAtURL:temporary error:&failure];
            }
            NSFileCoordinator *coordinator=[[NSFileCoordinator alloc] initWithFilePresenter:nil];
            NSError *coordinationError=nil;
            log(@"content_coordinator_start",@{@"directory":directory.path,@"preflight_error":failure.localizedDescription ?: @""});
            if(!failure) [coordinator coordinateReadingItemAtURL:source options:NSFileCoordinatorReadingWithoutChanges error:&coordinationError byAccessor:^(NSURL *url){
                log(@"content_coordinator_accessor",@{@"url":url.absoluteString ?: @""});
                int input=open(url.fileSystemRepresentation,O_RDONLY|O_NOFOLLOW);
                struct stat info;
                if(input<0 || fstat(input,&info) || !S_ISREG(info.st_mode) || info.st_size<22 || info.st_size>2LL*1024*1024*1024) {
                    if(input>=0)close(input);failure=Failure(@"Select a ZIP or IPA no larger than 2 GiB.");return;
                }
                if(CJContentFreeBytes(directory.fileSystemRepresentation)<info.st_size+contentBytes+64LL*1024*1024) {
                    close(input);failure=Failure(@"More free space is needed for the archive and imported game files.");return;
                }
                int output=open(temporary.fileSystemRepresentation,O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW,0600);
                if(output<0){close(input);failure=Failure(@"Could not create the staged archive.");return;}
                unsigned char buffer[128*1024],digest[CC_SHA256_DIGEST_LENGTH];CC_SHA256_CTX hash;CC_SHA256_Init(&hash);
                int64_t copied=0;double last=0;
                while(!CJContentShouldCancel()) {
                    ssize_t count=read(input,buffer,sizeof(buffer));
                    if(count<0 && errno==EINTR)continue;
                    if(count<0){failure=Failure(@"Could not read the selected archive.");break;}
                    if(!count)break;
                    if(copied+count>info.st_size){failure=Failure(@"The selected archive changed during copying.");break;}
                    ssize_t offset=0;
                    while(offset<count) { ssize_t n=write(output,buffer+offset,(size_t)(count-offset));if(n<0&&errno==EINTR)continue;if(n<=0){failure=Failure(@"Could not save the staged archive.");break;}offset+=n; }
                    if(failure)break;
                    CC_SHA256_Update(&hash,buffer,(CC_LONG)count);copied+=count;CJContentProgress(copied,info.st_size,0);
                    double now=NSProcessInfo.processInfo.systemUptime;
                    if(now-last>=2){log(@"content_archive_copy_progress",CJContentSnapshot());last=now;}
                }
                if(CJContentShouldCancel())failure=Failure(@"Import cancelled. Your source file and installed game data were preserved.");
                if(!failure && copied!=info.st_size)failure=Failure(@"The selected archive was truncated.");
                if(!failure && fsync(output))failure=Failure(@"The archive could not be flushed to storage.");
                close(output);close(input);
                if(!failure) {
                    CC_SHA256_Final(digest,&hash);NSMutableString *hex=[NSMutableString string];for(unsigned i=0;i<sizeof(digest);i++)[hex appendFormat:@"%02x",digest[i]];
                    if(rename(temporary.fileSystemRepresentation,destination.fileSystemRepresentation))failure=Failure(@"Could not finish staging the archive.");
                    else {saved=YES;log(@"content_archive_staged",@{@"source_filename":source.lastPathComponent,@"source_sha256":hex,@"bytes":@(copied)});}
                }
            }];
            if(!failure && coordinationError)failure=coordinationError;
            if(!saved && !failure)failure=Failure(@"The file provider did not return an accessible copy. Try the GameImport folder route.");
            if(!saved)[fm removeItemAtURL:temporary error:NULL];
            if(scoped)[source stopAccessingSecurityScopedResource];
            if(failure)log(@"content_archive_copy_stopped",@{@"message":failure.localizedDescription});
            dispatch_async(dispatch_get_main_queue(),^{completion(saved,failure);});
        }
    });
}
