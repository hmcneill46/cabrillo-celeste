#import <Foundation/Foundation.h>

// Foundation owns the classic app-extension event loop and principal-class
// dispatch. The containing app never loads this executable or StikJIT itself.
extern int NSExtensionMain(int argc, char *argv[]);
int main(int argc, char *argv[]) {
    @autoreleasepool { return NSExtensionMain(argc, argv); }
}
