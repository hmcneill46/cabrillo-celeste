#import "CJShortcutSession.h"

NSURL *CJShortcutGuestURL(NSString *host, NSDictionary<NSString *,NSString *> *query) {
    NSURLComponents *c=[NSURLComponents new]; c.scheme=@"cabrillo"; c.host=host;
    NSMutableArray *items=[NSMutableArray array];
    for(NSString *key in [[query allKeys] sortedArrayUsingSelector:@selector(compare:)])
        [items addObject:[NSURLQueryItem queryItemWithName:key value:query[key]]];
    c.queryItems=items; return c.URL;
}
NSURL *CJShortcutRoute(NSURL *guestURL, NSString *containerScheme) {
    if (!containerScheme.length) return guestURL;
    if (![@[@"livecontainer",@"livecontainer2",@"liveprocess"] containsObject:containerScheme]) return nil;
    NSURLComponents *c=[NSURLComponents new]; c.scheme=containerScheme;c.host=@"open-url";
    c.queryItems=@[[NSURLQueryItem queryItemWithName:@"url" value:[[guestURL.absoluteString dataUsingEncoding:NSUTF8StringEncoding] base64EncodedStringWithOptions:0]]];
    return c.URL;
}
NSURL *CJShortcutRunURL(NSString *stage, NSString *token, NSDictionary *fields, NSString *containerScheme) {
    NSMutableDictionary *input=[fields mutableCopy]; input[@"stage"]=stage;input[@"token"]=token;input[@"schema"]=@1;
    input[@"ack"]=[NSString stringWithFormat:@"cabrillo-39:%@:%@",stage,token];
    NSData *data=[NSJSONSerialization dataWithJSONObject:input options:NSJSONWritingSortedKeys error:NULL];
    if(!data) return nil;
    NSURLComponents *c=[NSURLComponents new];c.scheme=@"shortcuts";c.host=@"x-callback-url";c.path=@"/run-shortcut";
    NSMutableArray *items=[NSMutableArray arrayWithArray:@[[NSURLQueryItem queryItemWithName:@"name" value:@"Cabrillo"],
        [NSURLQueryItem queryItemWithName:@"input" value:@"text"], [NSURLQueryItem queryItemWithName:@"text" value:[[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding]]]];
    for(NSString *outcome in @[@"success",@"cancel",@"error"]) {
        // Put the receipt inside the guest URL. Shortcuts appends its result to
        // the outer LC URL, which LiveContainer does not forward to the guest.
        NSURL *callback=CJShortcutRoute(CJShortcutGuestURL(@"shortcut-callback",@{@"token":token,@"stage":stage,@"outcome":outcome,@"ack":input[@"ack"]}),containerScheme);
        if(!callback) return nil;
        [items addObject:[NSURLQueryItem queryItemWithName:[@"x-" stringByAppendingString:outcome] value:callback.absoluteString]];
    }
    c.queryItems=items;return c.URL;
}

@interface CJShortcutSession ()
@property(nonatomic) NSString *phase;
@property(nonatomic) NSString *token;
@property(nonatomic) NSString *process;
@property(nonatomic) NSString *message;
@property(nonatomic) NSString *failure;
@property(nonatomic) NSURL *journal;
@property(nonatomic) BOOL recoveryRequired;
@property(nonatomic) BOOL travel;
@property(nonatomic) BOOL restoreWiFi;
@property(nonatomic) BOOL restoreCellular;
@property(nonatomic) BOOL jitVerified;
@property(nonatomic) BOOL cancelled;
@property(nonatomic) BOOL handoffReturned;
@property(nonatomic) NSTimeInterval deadline;
@end

@implementation CJShortcutSession
- (instancetype)initWithJournal:(NSURL *)journal process:(NSString *)process {
    if((self=[super init])) {
        _journal=journal;_process=process;_phase=@"idle";_message=@"";_token=NSUUID.UUID.UUIDString;
        _restoreWiFi=YES;_restoreCellular=YES;
        if([NSFileManager.defaultManager fileExistsAtPath:journal.path]) {
            NSData *data=[NSData dataWithContentsOfURL:journal];
            id record=data?[NSJSONSerialization JSONObjectWithData:data options:0 error:NULL]:nil;
            // An unreadable record is still a recovery requirement. Never erase
            // it or silently continue with a new network/JIT transaction.
            if([record isKindOfClass:NSDictionary.class] && [record[@"schema"] isEqual:@1] &&
               [record[@"wifi"] isKindOfClass:NSNumber.class] && [record[@"cellular"] isKindOfClass:NSNumber.class]) {
                _restoreWiFi=[record[@"wifi"] boolValue]; _restoreCellular=[record[@"cellular"] boolValue];
                _message=@"An earlier launch was interrupted. Restore its networking preset before trying again.";
            } else _message=@"The network recovery record is unreadable. Restore uses Wi-Fi and cellular on, Airplane Mode off.";
            _travel=YES;_recoveryRequired=YES;_phase=@"recovery";
        }
    } return self;
}
- (BOOL)active { return [@[@"prepare",@"connect",@"isolate",@"verify-offline",@"jit",@"restore",@"waiting-detach"] containsObject:self.phase]; }
- (NSDictionary *)snapshot {
    return @{@"phase":self.phase,@"message":self.message?:@"",@"active":@(self.active),@"recoveryRequired":@(self.recoveryRequired),
        @"travel":@(self.travel),@"restoreWiFi":@(self.restoreWiFi),@"restoreCellular":@(self.restoreCellular),@"jitVerified":@(self.jitVerified)};
}
- (void)publish { if(self.changed)self.changed(self.snapshot); }
- (void)move:(NSString *)phase message:(NSString *)message now:(NSTimeInterval)now timeout:(NSTimeInterval)timeout {
    self.phase=phase;self.message=message;self.deadline=now+timeout;[self publish];
}
- (BOOL)armRecovery {
    NSError *error=nil;
    [NSFileManager.defaultManager createDirectoryAtURL:self.journal.URLByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:&error];
    NSData *data=[NSJSONSerialization dataWithJSONObject:@{@"schema":@1,@"process":self.process,@"wifi":@(self.restoreWiFi),@"cellular":@(self.restoreCellular)} options:NSJSONWritingSortedKeys error:&error];
    if(!error && [data writeToURL:self.journal options:NSDataWritingAtomic error:&error]) { self.recoveryRequired=YES; return YES; }
    self.phase=@"failed";self.message=@"Could not save network recovery information. No network settings were changed.";[self publish];return NO;
}
- (void)sendStage:(NSString *)stage now:(NSTimeInterval)now {
    NSDictionary *messages=@{@"prepare":@"Making networking available for LocalDevVPN…",@"isolate":@"Switching to the verified local VPN for travel…",
        @"restore":@"Restoring your networking preset…",@"jit":@"Enabling JIT for this running app…"};
    self.token=NSUUID.UUID.UUIDString;
    if([stage isEqual:@"jit"])self.handoffReturned=NO;
    [self move:stage message:messages[stage] now:now timeout:[stage isEqual:@"jit"]?120:35];
    if(self.command)self.command(stage,@{@"token":self.token,@"wifi":self.restoreWiFi?@"on":@"off",@"cellular":self.restoreCellular?@"on":@"off"});
}
- (void)connectAt:(NSTimeInterval)now offline:(BOOL)offline {
    [self move:offline?@"verify-offline":@"connect" message:offline?@"Checking that the local VPN still works in Airplane Mode…":@"Checking LocalDevVPN…" now:now timeout:25];
    if(self.command)self.command(offline?@"probe-offline":@"connect-vpn",@{});
}
- (void)startTravel:(BOOL)travel restoreWiFi:(BOOL)wifi restoreCellular:(BOOL)cellular now:(NSTimeInterval)now {
    if(self.active)return;
    if(self.recoveryRequired){[self recoverAt:now detached:YES];return;}
    self.travel=travel;self.restoreWiFi=wifi;self.restoreCellular=cellular;self.failure=nil;self.cancelled=NO;self.jitVerified=NO;
    if(travel){if([self armRecovery])[self sendStage:@"prepare" now:now];}
    else [self connectAt:now offline:NO];
}
- (void)tunnelReadyAt:(NSTimeInterval)now {
    if([self.phase isEqual:@"connect"]) {
        if(self.travel)[self sendStage:@"isolate" now:now];else [self sendStage:@"jit" now:now];
    } else if([self.phase isEqual:@"verify-offline"]) [self sendStage:@"jit" now:now];
}
- (BOOL)callback:(NSURL *)url now:(NSTimeInterval)now {
    if(![url.scheme isEqual:@"cabrillo"] || ![url.host isEqual:@"shortcut-callback"] || url.absoluteString.length>8192)return NO;
    NSMutableDictionary *q=[NSMutableDictionary dictionary];
    for(NSURLQueryItem *item in [NSURLComponents componentsWithURL:url resolvingAgainstBaseURL:NO].queryItems){
        if(q[item.name] || !item.value)return NO; q[item.name]=item.value;
    }
    BOOL waiting=[self.phase isEqual:@"waiting-detach"] && [q[@"stage"] isEqual:@"jit"];
    if(!self.active || ![q[@"token"] isEqual:self.token] || (![q[@"stage"] isEqual:self.phase] && !waiting))return NO;
    if(![@[@"prepare",@"isolate",@"jit",@"restore"] containsObject:q[@"stage"]])return NO;
    if([@[@"cancel",@"error"] containsObject:q[@"outcome"]]) {
        if([q[@"stage"] isEqual:@"jit"])self.handoffReturned=YES;
        if([self.phase isEqual:@"restore"]){[self move:@"recovery" message:@"Shortcuts did not complete network restoration. Tap Restore networking, or turn Airplane Mode off in Control Center." now:now timeout:0];}
        else [self fail:@"Shortcuts could not complete the launch. Check its permission prompts and keep the shortcut named Cabrillo." now:now];
        return YES;
    }
    NSString *ack=[NSString stringWithFormat:@"cabrillo-39:%@:%@",q[@"stage"],self.token];
    if(![q[@"outcome"] isEqual:@"success"] || ![q[@"ack"] isEqual:ack])return NO;
    if([self.phase isEqual:@"prepare"])[self connectAt:now offline:NO];
    else if([self.phase isEqual:@"isolate"])[self connectAt:now offline:YES];
    else if([self.phase isEqual:@"restore"]) {
        NSError *error=nil;
        if([NSFileManager.defaultManager fileExistsAtPath:self.journal.path] && ![NSFileManager.defaultManager removeItemAtURL:self.journal error:&error]) {
            [self move:@"recovery" message:@"Networking was restored, but its recovery record could not be cleared. Export diagnostics." now:now timeout:0];return YES;
        }
        self.recoveryRequired=NO;
        [self move:self.jitVerified?@"ready":@"failed" message:self.jitVerified?@"JIT is ready. Your networking preset is restored.":(self.failure?:@"Networking restored. Use the Home Screen icon to try a fresh launch.") now:now timeout:0];
    } else if([q[@"stage"] isEqual:@"jit"])self.handoffReturned=YES;
    // The JIT stage acknowledgement only returns the UI. It grants nothing.
    return YES;
}
- (void)fail:(NSString *)reason now:(NSTimeInterval)now {
    self.failure=reason;self.cancelled=YES;
    if([self.phase isEqual:@"restore"]){[self move:@"recovery" message:@"Could not restore networking automatically. Tap Restore networking again, or use Control Center." now:now timeout:0];return;}
    if([self.phase isEqual:@"jit"] || [self.phase isEqual:@"waiting-detach"]) {
        NSTimeInterval remaining=MAX(0,self.deadline-now);
        [self move:@"waiting-detach" message:@"Waiting for StikDebug to finish and detach before restoring networking…" now:now timeout:remaining];
    } else if(self.recoveryRequired)[self sendStage:@"restore" now:now];
    else [self move:@"failed" message:reason now:now timeout:0];
}
- (void)tickAt:(NSTimeInterval)now jitPassed:(BOOL)passed jitFailed:(BOOL)failed detached:(BOOL)detached {
    if([self.phase isEqual:@"jit"]) {
        if(passed && detached && self.handoffReturned) {
            self.jitVerified=YES;
            if(self.recoveryRequired)[self sendStage:@"restore" now:now];
            else [self move:@"ready" message:@"JIT is ready for this running app. Wi-Fi and cellular settings were left unchanged." now:now timeout:0];
        } else if(failed || now>=self.deadline) [self fail:@"JIT was not confirmed. Export diagnostics and check StikDebug before trying a fresh launch." now:now];
    }
    if([self.phase isEqual:@"waiting-detach"] && detached && (self.handoffReturned || now>=self.deadline) && (passed || failed || now>=self.deadline)) {
        if(self.recoveryRequired)[self sendStage:@"restore" now:now];
        else [self move:@"failed" message:self.failure now:now timeout:0];
    } else if([@[@"prepare",@"isolate"] containsObject:self.phase] && now>=self.deadline) {
        // A permission prompt may still be holding that Shortcuts invocation.
        // Don't start another radio-writing stage concurrently with it.
        [self move:@"recovery" message:@"The shortcut did not return. Stop any pending run in Shortcuts, then tap Restore networking." now:now timeout:0];
    } else if([@[@"connect",@"verify-offline"] containsObject:self.phase] && now>=self.deadline) {
        [self fail:@"The local VPN or shortcut did not become ready. Check LocalDevVPN and its default 10.7.0.1 address, then try again." now:now];
    } else if([self.phase isEqual:@"restore"] && now>=self.deadline) {
        [self move:@"recovery" message:@"Networking restoration was not confirmed. Tap Restore networking; Airplane Mode may still be on." now:now timeout:0];
    }
}
- (void)recoverAt:(NSTimeInterval)now detached:(BOOL)detached {
    if(!self.recoveryRequired || [self.phase isEqual:@"restore"])return;
    if([self.phase isEqual:@"jit"] || [self.phase isEqual:@"waiting-detach"]){[self cancelAt:now detached:detached];return;}
    if(!detached){self.failure=@"Network recovery requested.";self.handoffReturned=YES;[self move:@"waiting-detach" message:@"Waiting to verify debugger detach before restoring networking…" now:now timeout:0];return;}
    self.failure=@"Networking restored. Use the Home Screen icon to try a fresh launch.";
    [self sendStage:@"restore" now:now];
}
- (void)cancelAt:(NSTimeInterval)now detached:(BOOL)detached {
    if(!self.active)return;
    if([self.phase isEqual:@"restore"])return;
    [self fail:@"Launch cancelled. Your networking preset has been restored where needed." now:now];
    [self tickAt:now jitPassed:NO jitFailed:NO detached:detached];
}
@end
