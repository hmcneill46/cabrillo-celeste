// Simulator-only fixture. No game files, runtime, JIT, or signing keys are used.
#import <UIKit/UIKit.h>
#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>
#import <CommonCrypto/CommonDigest.h>
#import <objc/message.h>
#import "CJContentImport.h"
#import "CJDocumentPickerCompatibility.h"

static NSString *Digest(NSURL *url) {
    NSData *data=[NSData dataWithContentsOfURL:url];
    if(!data)return @"missing";
    unsigned char digest[CC_SHA256_DIGEST_LENGTH];CC_SHA256(data.bytes,(CC_LONG)data.length,digest);
    NSMutableString *hex=[NSMutableString string];for(unsigned i=0;i<sizeof(digest);i++)[hex appendFormat:@"%02x",digest[i]];return hex;
}
static NSURL *Documents(void) { return [NSFileManager.defaultManager URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask].firstObject; }

@interface PickerScreen:UIViewController<UIDocumentPickerDelegate>
@property(nonatomic,strong) UILabel *result;
@property(nonatomic,strong) UILabel *compatibility;
@property(nonatomic,strong) NSMutableDictionary *receipt;
@property(nonatomic,strong) NSURL *source;
@property(nonatomic,copy) NSString *mode;
@property(nonatomic) NSInteger pickerConstructions;
@end
@implementation PickerScreen
- (void)viewDidLoad {
    [super viewDidLoad];self.view.backgroundColor=UIColor.systemBackgroundColor;
    self.mode=[NSProcessInfo.processInfo.arguments containsObject:@"--compatibility"]?@"compatibility":@"original";
    self.source=[Documents() URLByAppendingPathComponent:@"synthetic.zip"];
    [NSFileManager.defaultManager removeItemAtURL:self.source error:NULL];
    NSError *error=nil;
    if(![NSFileManager.defaultManager copyItemAtURL:[NSBundle.mainBundle URLForResource:@"synthetic" withExtension:@"zip"] toURL:self.source error:&error]) [NSException raise:@"FixtureError" format:@"%@",error];
    self.receipt=[@{@"mode":self.mode,@"selections":@0,@"cancellations":@0,@"events":[NSMutableArray array],@"expected_sha256":Digest(self.source)} mutableCopy];
    UIStackView *stack=[UIStackView new];stack.axis=UILayoutConstraintAxisVertical;stack.spacing=18;stack.translatesAutoresizingMaskIntoConstraints=NO;[self.view addSubview:stack];
    UIButton *button=[UIButton buttonWithType:UIButtonTypeSystem];[button setTitle:@"Import game ZIP" forState:UIControlStateNormal];button.accessibilityIdentifier=@"import-zip";[button addTarget:self action:@selector(openPicker) forControlEvents:UIControlEventTouchUpInside];[stack addArrangedSubview:button];
    self.result=[UILabel new];self.result.accessibilityIdentifier=@"result";self.result.text=@"No selection";self.result.numberOfLines=0;[stack addArrangedSubview:self.result];
    self.compatibility=[UILabel new];self.compatibility.accessibilityIdentifier=@"compatibility";self.compatibility.text=self.mode;self.compatibility.numberOfLines=0;[stack addArrangedSubview:self.compatibility];
    [NSLayoutConstraint activateConstraints:@[[stack.centerXAnchor constraintEqualToAnchor:self.view.centerXAnchor],[stack.centerYAnchor constraintEqualToAnchor:self.view.centerYAnchor],[stack.widthAnchor constraintEqualToAnchor:self.view.widthAnchor constant:-48]]];
    [self writeReceipt];
}
- (void)writeReceipt {
    self.receipt[@"source_sha256"]=Digest(self.source);
    NSData *data=[NSJSONSerialization dataWithJSONObject:self.receipt options:NSJSONWritingPrettyPrinted error:NULL];
    [data writeToURL:[Documents() URLByAppendingPathComponent:[@"UIResult-" stringByAppendingFormat:@"%@.json",self.mode]] atomically:YES];
}
- (void)openPicker {
    self.result.text=@"Waiting for ZIP selection";
    if([self.mode isEqual:@"compatibility"]) {
        NSDictionary *status=CJDocumentPickerCompatibilityPrepare();
        if(!self.receipt[@"first_prepare_status"]) {
            self.receipt[@"first_prepare_status"]=status;
            self.receipt[@"picker_constructions_before_first_prepare"]=@(self.pickerConstructions);
        }
#if defined(CJ_DOCUMENT_PICKER_COMPATIBILITY_TESTING)
        Class configuration=NSClassFromString(@"DOCConfiguration");
        id synthetic=[configuration new];
        SEL setter=NSSelectorFromString(@"setHostIdentifier:"),getter=NSSelectorFromString(@"hostIdentifier");
        if([synthetic respondsToSelector:setter] && [synthetic respondsToSelector:getter]) {
            ((void(*)(id,SEL,id))objc_msgSend)(synthetic,setter,@"different.synthetic.bundle");
            NSString *resolved=((id(*)(id,SEL))objc_msgSend)(synthetic,getter);
            self.receipt[@"synthetic_requested_host_rewritten"]=@([resolved isEqual:NSBundle.mainBundle.bundleIdentifier]);
        }
#endif
        self.receipt[@"compatibility_status"]=status;
        self.compatibility.text=[NSString stringWithFormat:@"compatibility: %@",status[@"status"]?:status];
        [self writeReceipt];
    }
    // These are the production build52 picker arguments, unchanged in build53.
    UIDocumentPickerViewController *picker=[[UIDocumentPickerViewController alloc] initForOpeningContentTypes:@[UTTypeItem] asCopy:NO];
    self.pickerConstructions+=1;
    picker.delegate=self;picker.allowsMultipleSelection=NO;
    // Begin in the synthetic fixture folder; no private Files contents are read.
    picker.directoryURL=Documents();
    [self presentViewController:picker animated:YES completion:nil];
}
- (void)documentPickerWasCancelled:(UIDocumentPickerViewController *)controller {
    (void)controller;self.receipt[@"cancellations"]=@([self.receipt[@"cancellations"] integerValue]+1);self.result.text=@"Cancelled; source preserved";[self writeReceipt];
}
- (void)documentPicker:(UIDocumentPickerViewController *)controller didPickDocumentsAtURLs:(NSArray<NSURL *> *)urls {
    (void)controller;
    if(urls.count!=1){self.result.text=@"Unexpected selection count";return;}
    self.receipt[@"selections"]=@([self.receipt[@"selections"] integerValue]+1);
    NSURL *source=urls.firstObject,*stage=[Documents() URLByAppendingPathComponent:@"Staging" isDirectory:YES];
    self.result.text=@"Staging selected ZIP";
    CJStageContentArchive(source,stage,0,^(NSString *event,NSDictionary *fields){
        [self.receipt[@"events"] addObject:@{@"event":event,@"fields":fields}];
    },^(BOOL saved,NSError *error){
        NSURL *destination=[stage URLByAppendingPathComponent:@"game-input.zip"];
        NSString *sourceHash=Digest(self.source),*stageHash=Digest(destination);
        BOOL exact=saved && [sourceHash isEqual:self.receipt[@"expected_sha256"]] && [stageHash isEqual:sourceHash];
        self.receipt[@"staged"]=@(saved);self.receipt[@"staged_sha256"]=stageHash;self.receipt[@"source_preserved"]=@([sourceHash isEqual:self.receipt[@"expected_sha256"]]);
        self.receipt[@"staged_bytes"]=@([[NSFileManager.defaultManager attributesOfItemAtPath:destination.path error:NULL][NSFileSize] longLongValue]);
        self.result.text=exact?[NSString stringWithFormat:@"PASS selection %ld; staged SHA256 %@; source preserved",(long)[self.receipt[@"selections"] integerValue],stageHash]:[NSString stringWithFormat:@"FAIL %@",error.localizedDescription?:@"hash mismatch"];
        [self writeReceipt];
    });
}
@end
@interface PickerAppDelegate:UIResponder<UIApplicationDelegate>
@property(nonatomic,strong) UIWindow *window;
@end
@implementation PickerAppDelegate
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)options {
    (void)application;(void)options;
#if defined(CJ_DOCUMENT_PICKER_COMPATIBILITY_TESTING)
    if([NSProcessInfo.processInfo.arguments containsObject:@"--compatibility"]) {
        // No document picker is created before Prepare. The test seam follows
        // production discovery for Apple's actual DOCConfiguration class. Only
        // the synthetic request maps; the real picker retains its actual host ID.
        CJDocumentPickerCompatibilityTestEnvironment(@"different.synthetic.bundle",[@"SYNTHETIC." stringByAppendingString:NSBundle.mainBundle.bundleIdentifier],@"DOCConfiguration",NO);
    }
#endif
    self.window=[[UIWindow alloc] initWithFrame:UIScreen.mainScreen.bounds];self.window.rootViewController=[PickerScreen new];[self.window makeKeyAndVisible];return YES;
}
@end
int main(int argc,char **argv){@autoreleasepool{return UIApplicationMain(argc,argv,nil,NSStringFromClass(PickerAppDelegate.class));}}
