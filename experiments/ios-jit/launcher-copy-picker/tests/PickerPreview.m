// Simulator-only fixture. No game files, signing keys, or entitlement test seam.
#import <UIKit/UIKit.h>
#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>
#import <CommonCrypto/CommonDigest.h>
#import "CJContentImport.h"
#import "CJDocumentPickerCompatibility.h"

static NSString *Digest(NSURL *url) {
    NSData *data=[NSData dataWithContentsOfURL:url];
    if(!data)return @"missing";
    unsigned char digest[CC_SHA256_DIGEST_LENGTH];CC_SHA256(data.bytes,(CC_LONG)data.length,digest);
    NSMutableString *hex=[NSMutableString string];for(unsigned i=0;i<sizeof(digest);i++)[hex appendFormat:@"%02x",digest[i]];return hex;
}
static NSURL *Documents(void) { return [NSFileManager.defaultManager URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask].firstObject; }
static NSString *CanonicalPath(NSURL *url) { return url.URLByStandardizingPath.URLByResolvingSymlinksInPath.path; }
static BOOL IsWithin(NSString *path,NSString *directory) { return [path hasPrefix:[directory stringByAppendingString:@"/"]]; }

@interface PickerScreen:UIViewController<UIDocumentPickerDelegate>
@property(nonatomic,strong) UILabel *result;
@property(nonatomic,strong) UILabel *pickerMode;
@property(nonatomic,strong) NSMutableDictionary *receipt;
@property(nonatomic,strong) NSURL *source;
@property(nonatomic,copy) NSString *mode;
@property(nonatomic) BOOL importCopy;
@end
@implementation PickerScreen
- (void)viewDidLoad {
    [super viewDidLoad];self.view.backgroundColor=UIColor.systemBackgroundColor;
    self.importCopy=[NSProcessInfo.processInfo.arguments containsObject:@"--copy"];
    self.mode=self.importCopy?@"copy54":@"open-control53";
    self.source=[Documents() URLByAppendingPathComponent:@"synthetic.zip"];
    // This is fixture-owned seed data. Returned picker copies are never removed.
    [NSFileManager.defaultManager removeItemAtURL:self.source error:NULL];
    NSError *error=nil;
    if(![NSFileManager.defaultManager copyItemAtURL:[NSBundle.mainBundle URLForResource:@"synthetic" withExtension:@"zip"] toURL:self.source error:&error]) [NSException raise:@"FixtureError" format:@"%@",error];
    self.receipt=[@{@"mode":self.mode,@"requested_as_copy":@(self.importCopy),@"selections":@0,@"cancellations":@0,@"presentations":@0,@"events":[NSMutableArray array],@"picker_observations":[NSMutableArray array],@"selection_observations":[NSMutableArray array],@"expected_sha256":Digest(self.source),@"entitlement_test_seam":@NO,@"returned_copy_removed":@NO} mutableCopy];
    UIStackView *stack=[UIStackView new];stack.axis=UILayoutConstraintAxisVertical;stack.spacing=18;stack.translatesAutoresizingMaskIntoConstraints=NO;[self.view addSubview:stack];
    UIButton *button=[UIButton buttonWithType:UIButtonTypeSystem];[button setTitle:@"Import game ZIP" forState:UIControlStateNormal];button.accessibilityIdentifier=@"import-zip";[button addTarget:self action:@selector(openPicker) forControlEvents:UIControlEventTouchUpInside];[stack addArrangedSubview:button];
    self.result=[UILabel new];self.result.accessibilityIdentifier=@"result";self.result.text=@"No selection";self.result.numberOfLines=0;[stack addArrangedSubview:self.result];
    self.pickerMode=[UILabel new];self.pickerMode.accessibilityIdentifier=@"picker-mode";self.pickerMode.text=self.mode;self.pickerMode.numberOfLines=0;[stack addArrangedSubview:self.pickerMode];
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
    // This calls the production helper with the real running-process identity.
    self.receipt[@"compatibility_status"]=CJDocumentPickerCompatibilityPrepare();
    UIDocumentPickerViewController *picker=[[UIDocumentPickerViewController alloc] initForOpeningContentTypes:@[UTTypeItem] asCopy:self.importCopy];
    picker.delegate=self;picker.allowsMultipleSelection=NO;
    UIDocumentPickerMode actual=picker.documentPickerMode;
    NSString *actualName=actual==UIDocumentPickerModeImport?@"Import":actual==UIDocumentPickerModeOpen?@"Open":@"unexpected";
    BOOL expected=actual==(self.importCopy?UIDocumentPickerModeImport:UIDocumentPickerModeOpen);
    self.receipt[@"presentations"]=@([self.receipt[@"presentations"] integerValue]+1);
    [self.receipt[@"picker_observations"] addObject:@{@"requested_as_copy":@(self.importCopy),@"controller_mode":actualName,@"controller_mode_value":@(actual),@"mode_matches_request":@(expected),@"allows_multiple_selection":@(picker.allowsMultipleSelection)}];
    self.pickerMode.text=[NSString stringWithFormat:@"%@ mode %@",self.mode,actualName];
    // Begin in the synthetic fixture folder; no private Files contents are read.
    picker.directoryURL=Documents();
    [self writeReceipt];
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
    NSString *selectedPath=CanonicalPath(source),*originalPath=CanonicalPath(self.source);
    BOOL inbox=NO;for(NSString *part in selectedPath.pathComponents)if([part isEqual:@"Inbox"] || [part hasSuffix:@"-Inbox"])inbox=YES;
    NSMutableDictionary *observation=[@{@"selected_url_is_file":@(source.isFileURL),@"selected_url_equals_original_source":@([selectedPath isEqual:originalPath]),@"selected_url_is_in_app_home":@(IsWithin(selectedPath,CanonicalPath([NSURL fileURLWithPath:NSHomeDirectory()]))),@"selected_url_is_within_temp_directory":@(IsWithin(selectedPath,CanonicalPath([NSURL fileURLWithPath:NSTemporaryDirectory()]))),@"selected_path_contains_inbox_component":@(inbox),@"selected_filename_is_synthetic_zip":@([source.lastPathComponent isEqual:@"synthetic.zip"])} mutableCopy];
    [self.receipt[@"selection_observations"] addObject:observation];
    self.result.text=@"Staging selected ZIP";
    CJStageContentArchive(source,stage,0,^(NSString *event,NSDictionary *fields){
        [self.receipt[@"events"] addObject:@{@"event":event,@"fields":fields}];
    },^(BOOL saved,NSError *error){
        NSURL *destination=[stage URLByAppendingPathComponent:@"game-input.zip"];
        NSString *sourceHash=Digest(self.source),*stageHash=Digest(destination);
        BOOL exact=saved && [sourceHash isEqual:self.receipt[@"expected_sha256"]] && [stageHash isEqual:sourceHash];
        observation[@"staged"]=@(saved);observation[@"staged_sha256"]=stageHash;observation[@"source_preserved"]=@([sourceHash isEqual:self.receipt[@"expected_sha256"]]);
        self.receipt[@"staged"]=@(saved);self.receipt[@"staged_sha256"]=stageHash;self.receipt[@"source_preserved"]=observation[@"source_preserved"];
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
    self.window=[[UIWindow alloc] initWithFrame:UIScreen.mainScreen.bounds];self.window.rootViewController=[PickerScreen new];[self.window makeKeyAndVisible];return YES;
}
@end
int main(int argc,char **argv){@autoreleasepool{return UIApplicationMain(argc,argv,nil,NSStringFromClass(PickerAppDelegate.class));}}
