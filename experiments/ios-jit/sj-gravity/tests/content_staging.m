#import <Foundation/Foundation.h>
#import "CJContentImport.h"
#include <assert.h>

static BOOL Stage(NSURL *source,NSURL *destination,BOOL cancel) {
    __block BOOL complete=NO,ok=NO;
    CJStageContentArchive(source,destination,0,^(NSString *event,NSDictionary *fields){
        (void)fields;
        if(cancel && [event isEqualToString:@"content_archive_copy_progress"])CJContentSetCancelled(YES);
    },^(BOOL saved,NSError *error){ok=saved;assert(saved || error);complete=YES;});
    NSDate *deadline=[NSDate dateWithTimeIntervalSinceNow:20];
    while(!complete && deadline.timeIntervalSinceNow>0)[NSRunLoop.currentRunLoop runUntilDate:[NSDate dateWithTimeIntervalSinceNow:0.01]];
    assert(complete);return ok;
}
int main(int argc,const char **argv) {
    @autoreleasepool {
        assert(argc==2);
        NSFileManager *fm=NSFileManager.defaultManager;
        NSURL *root=[NSURL fileURLWithPath:@(argv[1]) isDirectory:YES];
        NSURL *source=[root URLByAppendingPathComponent:@"source.zip"],*dest=[root URLByAppendingPathComponent:@"Staging" isDirectory:YES];
        NSMutableData *data=[NSMutableData dataWithLength:4*1024*1024];memset(data.mutableBytes,0x35,data.length);
        assert([data writeToURL:source atomically:YES]);
        assert(Stage(source,dest,NO));
        NSURL *saved=[dest URLByAppendingPathComponent:@"game-input.zip"];
        assert([[NSData dataWithContentsOfURL:saved] isEqualToData:data]);
        NSDictionary *progress=CJContentSnapshot();assert([progress[@"bytes"] unsignedLongLongValue]==data.length);
        puts("PASS native streaming copy and progress");
        memset(data.mutableBytes,0x71,data.length);assert([data writeToURL:source atomically:YES]);
        NSData *before=[NSData dataWithContentsOfURL:saved];
        assert(!Stage(source,dest,YES));
        assert([[NSData dataWithContentsOfURL:saved] isEqualToData:before] && [[NSData dataWithContentsOfURL:source] isEqualToData:data]);
        assert(![fm fileExistsAtPath:[dest URLByAppendingPathComponent:@"game-input.zip.partial"].path]);
        puts("PASS cancellation preserves prior staged archive and original source");
        assert(!Stage([root URLByAppendingPathComponent:@"missing.zip"],dest,NO));
        assert([[NSData dataWithContentsOfURL:saved] isEqualToData:before]);
        puts("PASS missing input preserves previous archive and reports error");
        NSURL *link=[root URLByAppendingPathComponent:@"linked.zip"];
        assert([fm createSymbolicLinkAtURL:link withDestinationURL:source error:NULL]);
        assert(!Stage(link,dest,NO));
        assert([[NSData dataWithContentsOfURL:source] isEqualToData:data]);
        puts("PASS source symlink rejected");
        puts("PASS_NATIVE_CONTENT_STAGING");
    }
    return 0;
}
