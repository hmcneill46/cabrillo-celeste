#import <Foundation/Foundation.h>

void CJLoadingBegin(void);
void CJLoadingStage(NSString *phase, NSString *detail);
BOOL CJLoadingAccept(const char *json);
void CJLoadingFail(NSString *detail);
void CJLoadingEnd(void);
NSDictionary *CJLoadingSnapshot(void);
