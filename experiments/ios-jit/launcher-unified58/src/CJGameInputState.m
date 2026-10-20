#import "CJGameInputState.h"

static BOOL CJInputDigest(id value) {
    if (![value isKindOfClass:NSString.class] || [value length] != 64) return NO;
    return [value rangeOfCharacterFromSet:[[NSCharacterSet characterSetWithCharactersInString:@"0123456789abcdef"] invertedSet]].location == NSNotFound;
}
static BOOL CJInputFile(NSURL *url, NSUInteger maximum) {
    NSDictionary *attributes=[NSFileManager.defaultManager attributesOfItemAtPath:url.path error:nil];
    return [attributes[NSFileType] isEqual:NSFileTypeRegular] && [attributes[NSFileSize] unsignedLongLongValue] <= maximum;
}
BOOL CJGameInputsAvailable(NSURL *documents, NSDictionary *buildInfo) {
    NSString *content=buildInfo[@"game_content_aggregate_sha256"];
    if (!CJInputDigest(content)) return NO;
    NSURL *assets=[documents URLByAppendingPathComponent:[NSString stringWithFormat:@"GameLibrary/v1/%@/active.json",content]];
    if (!CJInputFile(assets,4096)) return NO;
    id source=buildInfo[@"game_code_legacy_source_id"];
    NSURL *selection=[documents URLByAppendingPathComponent:@"GameCode/v1/selected-source.json"];
    if ([NSFileManager.defaultManager fileExistsAtPath:selection.path]) {
        if (!CJInputFile(selection,4096)) return NO;
        id pointer=[NSJSONSerialization JSONObjectWithData:[NSData dataWithContentsOfURL:selection] ?: NSData.data options:0 error:nil];
        if (![pointer isKindOfClass:NSDictionary.class] || ![pointer[@"schema"] isEqual:@1]) return NO;
        source=pointer[@"source"];
    }
    if (!CJInputDigest(source)) return NO;
    BOOL supported=NO;
    id inputs=buildInfo[@"game_code_sources"];
    if (![inputs isKindOfClass:NSArray.class]) return NO;
    for (id row in inputs) if ([row isKindOfClass:NSDictionary.class] && [row[@"source_id"] isEqual:source]) supported=YES;
    if (!supported) return NO;
    NSURL *original=[documents URLByAppendingPathComponent:[NSString stringWithFormat:@"GameCode/v1/original/%@/source.json",source]];
    return CJInputFile(original,4096);
}
