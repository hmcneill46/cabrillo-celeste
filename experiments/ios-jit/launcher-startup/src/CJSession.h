#pragma once
// Versioned, process-local commands. Diagnostic strings never issue commands.
#define CJ_SESSION_ABI 1
int CJSessionOpen(int abi);
int CJSessionRequestQuit(int abi, int origin); // 1: game; 2: regression Finish
int CJSessionQuitOrigin(void);
int CJSessionAdvance(int abi, int stage);
int CJSessionStage(void);
void CJSessionClose(void);
const char *CJSessionStageName(int stage);
