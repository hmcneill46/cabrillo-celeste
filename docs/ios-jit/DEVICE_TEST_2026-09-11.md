# First device result and corrected probe

Received 11 September 2026. Original build `native-probe-20260910-01`, version
0.1.0 (1). Corrected build `native-probe-20260911-02`, version 0.1.1 (2).

**Later follow-up:** the [build 2 retest](NATIVE_EXECUTION_PASS_2026-09-11.md)
confirms three native-memory passes, including background/return. The pending
retest descriptions below preserve the first handoff's chronology. A separate
debug-symbol packaging error is corrected in version 0.1.2 (3).

## Finding

The owner's diagnostic export is sufficient to identify a **probe validation
bug before generated-code execution**. It records a working two-container URL
handoff, an M1 prepared response, and a detached first-container process with
`CS_DEBUGGED` set. The first VM query returns a valid 16 KiB RX entry. The old
checker demands that this one entry cover the entire requested 64 KiB range,
so it stops immediately.

This is positive evidence for the handshake and a reason to fix the checker.
It is not a physical native-JIT PASS: aliases were not created and no generated
code ran. The remainder of each range was not queried by the old build.

| Evidence | Observation |
| --- | --- |
| Phone | iPhone16,2; iOS 26.5, build 23F77; 16 KiB pages |
| Owner-entered versions | LiveContainer 3.8.9; StikDebug 3.1.9 |
| Arrangement | Probe in LiveContainer 1; StikDebug in LiveContainer 2 |
| Script | Embedded M1 template hash matches the delivered build |
| Request | Inline script through `livecontainer2://open-url`; open succeeded |
| Response | Mailbox status 2, script version 1, error 0 |
| Process after response | Actual host `LiveContainer`; traced = false; `CS_DEBUGGED` and get-task-allow flag set |
| Passed checks | `debugger_detached_before_execution`, `mailbox_response_valid` |
| First VM query | Success; current protection 5 (RX), maximum 7; entry length 16,384 bytes |
| Failed check | `prepared_region_is_rx`, because a single entry did not cover 65,536 requested bytes |
| Execution reached | No `about_to_execute` event; no generated-code call |

There are five distinct sessions in the attachment. Two completed attempts hit
the same early validation failure; other sessions end earlier. The current
session also appears in the previous-session list, so it must not be counted
twice. No native crash is established by this report.

Raw owner data is retained only under ignored
`.build/ios-jit/device-evidence/2026-09-11/`. The attachment SHA-256 is
`cd7198ddb02773dc8fb2a0b3c01f80c855b270eaa05606bed6f615435e1297fb`.
Its exported build/source hashes match the original delivery receipt. Do not
track the raw logs or the phone connection/identity records.

## Fix

The range checker now traverses every adjacent VM entry until the requested
end address, rather than equating an allocation with a single map entry. It
records each entry and the covered bytes. It rejects holes, query errors,
malformed/nonadvancing entries, overflow and excessive traversal.

The original protection requirements remain strict. Every entry must have the
same exact current protection: RX for the executable view and RW for its write
alias. A bitwise intersection alone would wrongly accept a mixture of RX and
RWX, so mixed protections are reported explicitly and rejected. Bounds are
checked for the full requested range before execution.

The log exporter now excludes the current session by filename/session identity
rather than URL-object equality. LiveContainer can expose different path
aliases for the same file; the original check allowed the current log into the
historical section. A retest should confirm the correction on that container.

The script and mailbox protocol are unchanged: the app sends its
launch-specific script, the debugger prepares two 64 KiB regions, and the app
requires detach before executing generated instructions. This build still has
no managed runtime, hooks, Celeste or mods.

## Validation and next physical test

The shared C walker and Darwin VM adapter pass 12 host regression cases under
AddressSanitizer and UndefinedBehaviorSanitizer, including the reported four
16 KiB entries/64 KiB range case, holes and mixed RWX permissions. One test
creates an actual fragmented macOS mapping with uniform current permissions
and differing maximum permissions. This tests real VM traversal on the host,
not iOS executable-memory behavior.

The simulator also passes startup, JSON export and previous-session recovery.
Its regression deliberately exposes the current log through a filesystem
alias and confirms that the current session is excluded from the historical
list. Generated-code paths are disabled in that simulator build.

Use the new 0.1.1 (2) IPA and a fresh probe process. Keep Launch with JIT OFF for
this native-bootstrap test. Run the same slot 1 → slot 2 procedure and export
the result. The next report should either identify the remaining VM/alias/
execution issue or demonstrate native execution. After a PASS, repeat the
checks after background/foreground in the same process.

The updated [physical instructions](../../experiments/ios-jit/native-probe/INSTALL.md)
and short phone README accompany the build. The owner authorized an iCloud
Drive handoff for files totaling less than 50 MB. The destination is
**Files → iCloud Drive → Celeste JIT Tests → 0.1.1-build-2**. All four files
(160,333 bytes total) were copied and their hashes verified. Foundation's
iCloud resource metadata confirmed that every file had uploaded successfully
at 00:16:10 UTC on 11 September. Actual phone download remains unobserved.
The [evidence JSON](DEVICE_TEST_2026-09-11_EVIDENCE.json) records transfer and
upload separately from JIT test results.

The local unsigned IPA is
`artifacts/ios-jit/native-probe-20260911-02/CelesteJITProbe-unsigned.ipa`, SHA-256
`3ced8145abe1ed754c1e5186ab37f6ce3692fb6d85529539ee18e3a6c65a823b`.
The full local ZIP, including the dSYM and build evidence, is
`artifacts/ios-jit/CelesteJITProbe-native-probe-20260911-02-test-kit.zip`.
The cloud copy of the IPA has identical bytes and a versioned filename.

Before selecting iCloud, the correct paired iPhone was visible to CoreDevice
and later had a connected wireless tunnel. App listings were empty and the
LocalSend document-container query failed. A Finder Apple-event query timed
out. No direct phone file copy or debugger attachment was completed. These
connection limitations do not block diagnosis of the supplied report.

The owner authorizes relevant log retrieval and debugger use, but an additional
debugger attachment is unnecessary to diagnose this failure. Any later attach
must not compete with StikDebug or be treated as evidence for its JIT path.
