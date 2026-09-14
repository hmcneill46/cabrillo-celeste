#pragma once
#import <Foundation/Foundation.h>
typedef void (^CJManagedLog)(NSString *event, NSDictionary *fields);
BOOL CJManagedRun(NSURL *importedDLL, NSURL *frameworkDirectory, CJManagedLog log);
