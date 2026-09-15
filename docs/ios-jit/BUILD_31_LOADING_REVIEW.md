# Build31 phone review

15 September2026. **Both build31 phone runs pass game/backend checks. Two loading
presentation issues need refinement.** The owner reports all other visual checks
passed. The single export contains both build31 runs plus two retained build28
sessions; no second export or repetition of the successful browser suite is needed.
Build28 remains the accepted fallback while the loading experience is refined.

The export was copied privately with matching SHA256
`4ac46732645eb7500ecb8ae8152e3e743dad890225766b6d2879d60e5cefe23d`
(5,105,935 bytes). Exact collection, session evidence and timings are in the
[ledger](BUILD_31_LOADING_REVIEW_EVIDENCE.json). Device: iPhone15ProMax, iOS26.5;
exact build31 identity and its expected managed/runtime receipt are recorded.

| Evidence | First run | Second/warm run |
| --- | --- | --- |
| Main-thread startup continuations |160 |160 |
| Longest indivisible step |17.291s, StrawberryJam2021 |4.412s, game content |
| Native cover after first rendered frame |17.733s |17.764s |
| Archive/folder work / successful mod loads |60/60;60 |60/60;60 |
| Catalogue requests before startup |0 |0 |
| Required/selected metadata verified |63; no disabled extras |63; no disabled extras |
| Actual room evidence |SJ `joltik`, a_04 → a_05 |Same SID, a_05 |
| Save and normal Quit |Slot1 readback; eight-stage Stop/detach; delayed foreground heartbeat |Same |
| Game background/resume |12.982s; completed |No gameplay background interval |
| Runtime error counters at Quit |All0 |All0 |

## What the observations mean

Opening, closing and scrolling the details felt choppy because individual
main-thread operations still block UIKit. In the first run the SJ module took
17.29s; in the warm run it took4.04s and game initialization4.41s. This is not a
CPU budget intentionally withheld from the UI. Smooth interaction through those
calls would require further safe splitting of the calls themselves. Moving
arbitrary mod/graphics work to a worker would risk thread-affinity compatibility.

The native cover deliberately waited for `OuiTitleScreen` in build31. Both logs
show a real `Celeste.GameLoader` draw and post-Present GPU readback roughly17.7s
earlier. The game was running its opening/loading sequence behind the cover;
this does not mean all loading had finished. The owner heard audio roughly10s
before the reveal. The log's FMOD-ready marker is not an exact audible-onset
measurement, so those two timings should not be equated.

Build32 removes that title-menu wait and uses the already existing draw/readback
proof before revealing the game. The normal native screen shows useful details
without disclosure/scroll interactions. These native changes reuse build31's
phone-tested managed payload and preserve error Export and save/Quit behavior.
See [build32](FIRST_FRAME_BUILD_32.md) for implementation and the focused phone gate.
