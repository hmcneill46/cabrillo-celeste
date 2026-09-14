#pragma once
#import <Foundation/Foundation.h>
typedef void (^CJGraphicsLog)(NSString *event, NSDictionary *fields);
BOOL CJGraphicsPrepare(NSURL *dll, NSURL *frameworks, CJGraphicsLog log);
BOOL CJGraphicsPrepareContent(int *result);
BOOL CJGraphicsCall(const char *method, int *result);
BOOL CJGraphicsDetachMain(void);
NSDictionary *CJGraphicsRuntimeStats(void);
void CJGraphicsMark(const char *name, const char *message);
void CJGraphicsSetWindow(void *window);
void CJGraphicsSample(int frames, int contacts, int presses, int releases, int controllers, int resumes);
void *CJResolveGraphicsNative(const char *library, const char *entry);
