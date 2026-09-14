# JIT26 protocol ABI experiment

This compile-only experiment checks that Xcode 26.6 emits the arm64 register and
breakpoint convention used by the pinned StikDebug universal protocol. It is
independent of all Celeste, Everest, and AOT product projects.

Run from any directory:

```sh
python3 /Users/harrymcneill/Projects/Celeste-Everest-JIT-Apple-Platforms/experiments/ios-jit/protocol-abi/compile.py
```

`DEVELOPER_DIR` defaults to `/Applications/Xcode-26.6.app/Contents/Developer` for
this subprocess only; set it explicitly to test another toolchain. The receipt,
object, and disassembly are written under `.build/ios-jit/audit/protocol-abi/`.

A passing result proves compilation and instruction layout only. It does not
prove executable memory allocation, debugger attachment, iOS 26.5 compatibility,
LiveContainer operation, .NET JIT, or Everest hooks. Neither function is called.
The experiment does not make an app or IPA. These functions would trap and could
terminate a real app if executed without the matching debugger protocol active.

The protocol reference is
[StikJIT universal.js](https://github.com/StikDebug/StikJIT/blob/3623e725876f76aecb0520582ad6194bacb15d39/Resources/universal.js).
The tiny call-site implementation is repository-owned; no MeloNX code or
third-party debugger script is vendored into the product.
