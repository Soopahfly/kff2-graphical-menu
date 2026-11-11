# G7 hardware results

Candidate: [KungFuFlash_v2.G7.upd](KungFuFlash_v2.G7.upd), based on upstream
v2.07 plus documentation commit `9c84d99`. The original G7 SHA256 is
`c36c30e3ec04bcffdff07dcf03cf9cdafd007b1cbd7eaeffd719696c6d76f552`.
[build-report.json](build-report.json) now describes the G7.0.1 hotfix;
[SHA256SUMS](SHA256SUMS) identifies both downloads.

This log records hardware reports received after packaging. It does not change
the firmware or retrospectively alter the build report's `hardware_tested: false`
snapshot. G7 remains an experimental test candidate, not a public release.

## 11 November 2026, project owner report

Reporter: **Soopahfly**, using a real Kung Fu Flash 2/C64 setup. The reporter
confirmed items 1, 3 and 4 from the requested test list: PRG/CRT loading, saving
REU-size/autoboot settings, and reset with autoboot disabled.

| Check | Result | What this establishes |
| --- | --- | --- |
| Load PRG files | Reported pass | Tested PRGs load; no individual titles specified |
| Load CRT files | Reported pass | Tested CRTs load; cartridge types/titles not specified |
| Save REU size preference | Reported pass | The setting can be saved; capacities exercised not specified |
| Save autoboot preference | Reported pass | The startup preference can be saved |
| Reset with autoboot disabled | Reported pass | Returns to graphical Home instead of replaying the saved selection |

Exact C64 model/board, PAL/NTSC standard and test titles/programs were not
provided with this report. Earlier G5 photographs used an LCD; G7 CRT-display
readability has not been reported. These results do not imply that every loader,
cartridge type, display or hardware configuration has passed.

## 11 November 2026, Favourites result-screen failure

The owner supplied a photograph of the original G7 success message, “Added to
/Favourites. Original kept.”, and reported no response to any key. This confirms
the result screen displayed, but does not independently prove the destination
contents, source retention or successful loading. File/folder and title were not
specified. Treat acknowledgement as a **reported failure**, not a passed copy test.

Source review found that the callback sent directory data while the launcher was
still waiting for `CMD_SYNC` after acknowledging the warning. G7.0.1 adds that
synchronisation. Host regression checks cover success, already present, collision
and failure, and fail when the fix is removed.

**G7.0.1 hardware retest: pending.** Its internal label is still `2.G7`. Download
[KungFuFlash_v2.G7.0.1.upd](KungFuFlash_v2.G7.0.1.upd), SHA256
`d6e6eefdd237a143af32e33a6691f36faa2269aa013f1b9b43b7c0030adb8bcb`.
The earlier PRG/CRT/settings/reset passes apply to original G7, not a claimed
retest of this hotfix.

## Remaining checks before a first public release

- Copy a single file to Favourites and load the copy. Confirm the original remains.
- Copy a complete game folder, including companions/multiple disks, and use it.
- Repeat a file copy and try an existing destination name. Confirm no overwrite.
- Use REU software to detect and exercise **256 KB, 512 KB and 1 MB**. Saving the
  selected size alone does not establish address wrapping or DMA operation.

The public release has not been created. These checks are still pending.

## Additional coverage requested

Autoboot-enabled reset, disk/tape loading (D64/D71/D81/T64), history and random
selection across resets, long-directory navigation, search, Help, file options,
text paging, joystick operation, USB, C128 and additional PAL/NTSC/board setups.
Physical CRT readability remains untested.

See [the current checklist](../../docs/testing.md) for expected outcomes and
the details to include in a report. Successful tests and failures are both useful.
