#!/usr/bin/env python3
import os,subprocess
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];O=R/'.build/ios-jit/launcher-compat-native-services-tests';O.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
cmd=['xcrun','clang','-O1','-g','-fobjc-arc','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations','-fsanitize=address,undefined','-I'+str(S/'src'),str(S/'tests/NativeServicesTests.m'),str(S/'src/CJEventStore.m'),str(S/'src/CJFrameMetrics.c'),'-framework','Foundation','-o',str(O/'tests')]
subprocess.run(cmd,env=env,check=True)
subprocess.run([str(O/'tests'),str(O),str(R/'.build/ios-jit/device-evidence/2026-09-12/build-19-results/current-events.json')],env=env,check=True)
