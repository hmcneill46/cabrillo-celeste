CELESTE JIT PROBE 0.1.2 — BUILD 3
Build ID: native-probe-20260911-03

This corrects the dSYM signing error from the earlier IPAs. Debug symbols now
stay separately on the Mac for crash analysis, outside the installable app.
The native code and matching StikDebug script are unchanged from build 2,
which passed three native-memory runs on your phone.

Files > iCloud Drive > Celeste JIT Tests > 0.1.2-build-3
Tap a cloud icon if the corresponding file needs downloading.

INSTALLATION CHECK
1. In LiveContainer 1, import CelesteJITProbe-0.1.2-build-3-unsigned.ipa.
   Replace the previous probe while preserving its data container/logs.
2. Confirm the dSYM signing error is gone. If it remains, send the exact path;
   do not delete the data container. No full native retest is required just
   for this packaging fix.

OPTIONAL FRESH JIT RUN
1. Leave Launch with JIT OFF and JIT Launch Script empty for this probe.
2. Have StikDebug ready in LiveContainer 2, with LocalDevVPN on.
3. Start a fresh probe process in slot 1; check the build ID shown above.
4. Tap Enable via LiveContainer 2, let StikDebug complete, then return to the
   same running probe in slot 1.
5. Export diagnostics for either result. If it closes, reopen without JIT and
   export immediately to recover the previous session.

The matching script is embedded and sent automatically. INSTALL.md includes
the session-specific export/import fallback. The TEMPLATE.js in the full Mac
kit is reference material, not an importable prelaunch script.

This app remains a native-memory probe. Managed .NET JIT, Celeste and mods are
the next development stages and are not included in this build.
