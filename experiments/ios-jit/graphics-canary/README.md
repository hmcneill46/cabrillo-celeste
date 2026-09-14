# JIT FNA graphics bridge

This bounded G3 preparation follows the accepted build 9 G2 result. It is not
full Celeste/Everest integration. The test combines the actual JIT renderer,
Metal, input, a retained MonoMod render hook and native lifecycle ownership.

The native launcher and request code are an isolated fork of build 9. Shared
G1/G2 protocol, allocator, thread helper, hook bridge and script are read-only
build inputs, recorded by hash. The separate graphics bundle preserves the
accepted Hook Canary. Native libraries are rebuilt in JIT staging and verified
against `native/ios-native-output.lock.json`. Build 11 overlays only FNA3D with
`native/fna3d-callback.patch`, built in `.build/ios-jit/graphics-native-build11`.
The accepted foundation archives stay unchanged; no AOT output is writable.

Build preparation:

```sh
DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  scripts/build-ios-native.sh --build-dir .build/ios-jit/game-native \
  --output-dir .build/ios-jit/game-native-output
DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  python3 scripts/verify-ios-native.py --repo-root . \
  --build-dir .build/ios-jit/game-native --output-dir .build/ios-jit/game-native-output
DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  scripts/prepare-ios-foundation.sh --artifact-dir .build/ios-jit/game-native-output \
  --native-build-dir .build/ios-jit/game-native --stage-dir .build/ios-jit/game-foundation
python3 experiments/ios-jit/graphics-canary/native-build.py
python3 experiments/ios-jit/graphics-canary/managed-build.py
python3 experiments/ios-jit/graphics-canary/build.py
python3 experiments/ios-jit/graphics-canary/managed-build.py --fixture-only
```

The native source root must first be fetched at the exact dependency lock pins.
Existing stages need inspection before replacement. `managed-build.py` uses
the existing isolated SDK 8.0.422 and compiles to net8.0 IL directly, bypassing
the repository's .NET 10 Apple/AOT projects and their shared intermediate paths.
The external fixture is rebuilt after IPA packaging. Delivery receipts prevent
overwriting shipped kits; choose a new version/build for subsequent changes.

One UIKit scene owns a native launcher window and the SDL game window. The
host calls `SDL_SetMainReady` but never `SDL_UIKitRunApp`. A native CADisplayLink
invokes FNA on the main thread. The private FNA copy gains explicit begin/frame/
end methods matching `Game.Run`'s lifecycle, including RegisterGame/BeginRun/
OnExiting/EndRun/UnregisterGame. `RunOneFrame` alone would omit that setup.
SDL's recursive UIKit event pump stays disabled because UIKit owns the loop.

Build 10 failed after LoadContent left a Metal frame/autorelease pool open across
UIKit callbacks. The exact old fixture reproduces a deallocated Metal command
buffer on macOS when the callback pool drains. Build 11 pairs FNA with the private
`FNA3D_CJIT_EndCallback` entry: begin/frame/end use finally blocks to submit any
unfinished GPU work and close its pool without requesting a drawable or adding a
presentation. Normal Present uses the same completion code. Backbuffer reset
realizes pending clears before releasing old attachments; disposal completes and
releases the final command buffer. These are renderer/hosting fixes, not JIT changes.

The fixture now checks a pending-clear reset in LoadContent, startup callback
completion, and GPU readback across one deliberately suppressed Draw at update
120. Keep callback-scoped autorelease pools in the host regression. A single pool
around all frames, as build 10 used, hides the startup failure.

Runtime bootstrap happens on a native worker, which detaches. The main thread
then attaches once, invokes each bounded managed entry inside balanced GC-unsafe
regions, and detaches using the accepted helper after stopping. Native lifecycle
notifications pause frames before inactivity, feed SDL its application events,
then invoke managed resume and reset the game clock. No code arena is initialized
or rewritten over a running runtime. The code budget remains 32 MiB for this
probe; full-game capacity is a separate requirement.

Device native imports use an explicit address table generated from the static
libraries. They do not rely on LiveContainer's global `dlsym` scope or Apple
managed bindings. FNA stock effects/resources and notices are included. The
legacy FNA `FNA_AUDIO_DISABLE_SOUND` environment convention is not used as
audio acceptance: this fixture never creates or plays sound. FMOD and audio
lifecycle remain for the real game stage.

`tests/check_host_graphics.py` runs the actual shared embedding and managed
fixture on the pinned cooperative macOS Mono runtime, the same patched FNA3D
source as the IPA, and a private copy of the supplied desktop SDL library. It runs
540 callbacks (539 draws plus one deliberate skipped draw), reads GPU pixels,
resets, suspends/resumes, removes the hook and detaches the main thread. It
does not synthesize physical touch or claim iOS memory/background acceptance.
The host-only compile symbols must never appear in a device build.

`tests/simulator_smoke.py` checks only native launcher import/export/recovery
and request generation. `tests/check_request_protocol.py` checks the actual
packaged device constants against that native request and the exact packaged
script in a fake debugserver. Physical rendering and input remain separate
acceptance evidence. See [INSTALL.md](INSTALL.md) and the stage report under
`docs/ios-jit/` for the device handoff and known limits.
