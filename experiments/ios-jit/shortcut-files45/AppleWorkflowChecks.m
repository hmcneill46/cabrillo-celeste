// Host-only Apple condition/completion controls. No radio/URL actions,
// no shortcut library writes, no ActionKit, and no inclusion in the iOS app.
#import <Foundation/Foundation.h>
#import <dlfcn.h>
@protocol AppleWorkflowAPI
+ (id)sharedRegistry;
+ (id)actionsFromSerializedRepresentations:(id)actions actionRegistry:(id)registry;
- (void)fill;
- (id)actions;
- (id)initWithName:(id)name description:(id)description associatedAppBundleIdentifier:(id)bundle actions:(id)actions;
- (void)setWorkflow:(id)workflow;
- (void)setDelegate:(id)delegate;
- (void)setInput:(id)input;
- (void)setDonateInteraction:(BOOL)value;
- (void)setAcquiresAssertionWhileRunning:(BOOL)value;
- (void)addObject:(id)object;
- (void)run;
- (id)output;
- (NSArray *)items;
- (NSString *)string;
- (id)identifier;
- (id)serializedParameters;
- (BOOL)truthWithVariableSource:(id)source;
@end
@interface ConditionObserver : NSObject
@property BOOL done;
@property NSError *error;
@property NSMutableArray *comments;
@property NSMutableArray *truths;
@end
@implementation ConditionObserver
- (void)workflowController:(id)c didFinishRunningWithError:(NSError *)error cancelled:(BOOL)cancelled {
    (void)c;self.error=error ?: (cancelled ? [NSError errorWithDomain:@"Cancelled" code:1 userInfo:nil] : nil);self.done=YES;
}
- (void)workflowController:(id)c didRunAction:(id<AppleWorkflowAPI>)action error:(NSError *)error {
    (void)c;(void)error;
    if([[action identifier] isEqual:@"is.workflow.actions.comment"])
        [self.comments addObject:[action serializedParameters][@"WFCommentActionText"]?:@""];
    if(!error && [[action identifier] isEqual:@"is.workflow.actions.conditional"] && [[action serializedParameters][@"WFControlFlowMode"] integerValue]==0)
        [self.truths addObject:@([action truthWithVariableSource:c])];
}
@end
int main(int argc,char **argv) { @autoreleasepool {
    if(argc!=2)return 2;
    if(!dlopen("/System/Library/PrivateFrameworks/WorkflowKit.framework/WorkflowKit",RTLD_LAZY|RTLD_GLOBAL)){fputs(dlerror(),stderr);return 2;}
    NSArray *cases=[NSArray arrayWithContentsOfFile:@(argv[1])];if(!cases.count)return 2;
    id<AppleWorkflowAPI> registry=[(id<AppleWorkflowAPI>)NSClassFromString(@"WFActionRegistry") sharedRegistry];[registry fill];
    NSDate *fillDeadline=[NSDate dateWithTimeIntervalSinceNow:5];
    while(![[registry actions] count] && fillDeadline.timeIntervalSinceNow>0)
        [NSRunLoop.currentRunLoop runUntilDate:[NSDate dateWithTimeIntervalSinceNow:0.02]];
    NSMutableArray *results=[NSMutableArray array];BOOL all=YES;
    for(NSDictionary *test in cases) {
        NSArray *serialized=test[@"actions"];
        for(NSDictionary *action in serialized)
            if(![@[@"is.workflow.actions.comment",@"is.workflow.actions.conditional",@"is.workflow.actions.nothing"] containsObject:action[@"WFWorkflowActionIdentifier"]])return 2;
        id actions=[(id<AppleWorkflowAPI>)NSClassFromString(@"WFAction") actionsFromSerializedRepresentations:serialized actionRegistry:registry];
        id workflow=[(id<AppleWorkflowAPI>)[NSClassFromString(@"WFWorkflow") alloc] initWithName:@"Cabrillo isolated condition check" description:@"" associatedAppBundleIdentifier:nil actions:actions];
        id<AppleWorkflowAPI> input=[NSClassFromString(@"WFContentCollection") new];[input addObject:test[@"input"]];
        id<AppleWorkflowAPI> controller=[NSClassFromString(@"WFWorkflowController") new];
        ConditionObserver *observer=[ConditionObserver new];observer.comments=[NSMutableArray array];observer.truths=[NSMutableArray array];
        [controller setWorkflow:workflow];[controller setInput:input];[controller setDelegate:observer];
        [controller setDonateInteraction:NO];[controller setAcquiresAssertionWhileRunning:NO];[controller run];
        NSDate *deadline=[NSDate dateWithTimeIntervalSinceNow:5];
        while(!observer.done && deadline.timeIntervalSinceNow>0)
            [NSRunLoop.currentRunLoop runUntilDate:[NSDate dateWithTimeIntervalSinceNow:0.02]];
        NSMutableArray *output=[NSMutableArray array];
        for(id<AppleWorkflowAPI> item in [(id<AppleWorkflowAPI>)[controller output] items]) {
            if(![(id)item isKindOfClass:NSClassFromString(@"WFStringContentItem")])return 2;
            [output addObject:[item string]];
        }
        BOOL expectedError=[test[@"expectMissingParameter"] boolValue];
        BOOL pass=observer.done && (test[@"rejectOutput"] ? !observer.error && ![output isEqual:@[test[@"rejectOutput"]]] :
            test[@"output"] ? !observer.error && [output isEqual:test[@"output"]] :
            expectedError ? [observer.error.domain isEqual:@"ConditionalAction"]&&observer.error.code==1 :
            !observer.error&&[observer.truths isEqual:@[test[@"truth"]]]);
        all=all&&pass;
        [results addObject:@{@"name":test[@"name"],@"pass":@(pass),@"completed":@(observer.done),@"error":observer.error.localizedDescription?:@"",@"comments":observer.comments,@"truths":observer.truths,@"output":output}];
    }
    NSDictionary *result=@{@"status":all?@"PASS_APPLE_WORKFLOW_CONTROLS":@"FAIL_APPLE_WORKFLOW_CONTROLS",@"checks":@(results.count),@"results":results};
    puts([[NSString alloc]initWithData:[NSJSONSerialization dataWithJSONObject:result options:NSJSONWritingPrettyPrinted error:NULL] encoding:NSUTF8StringEncoding].UTF8String);
    return all?0:1;
}}
