#pragma once
#import <Foundation/Foundation.h>
void CJContentSetCancelled(BOOL cancelled);
int CJContentShouldCancel(void);
void CJContentProgress(int64_t done, int64_t total, int files);
int64_t CJContentFreeBytes(const char *path);
NSDictionary *CJContentSnapshot(void);
void CJStageContentArchive(NSURL *source, NSURL *directory, int64_t contentBytes,
    void (^log)(NSString *,NSDictionary *), void (^completion)(BOOL,NSError *));
