#pragma once
#import <UIKit/UIKit.h>
#import "CJGraphicsManaged.h"
void CJGraphicsPlatformPrepare(CJGraphicsLog log);
void CJGraphicsPlatformEvent(int state);
UIWindow *CJGraphicsPlatformWindow(void);
NSDictionary *CJGraphicsPlatformSnapshot(void);
void CJGraphicsPlatformForgetWindow(void);
void CJGameQueueTestMap(void);

void CJGameQueueBing(void);
