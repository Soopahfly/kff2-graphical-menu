# G7 hardware results

Candidate: [KungFuFlash_v2.G7.upd](KungFuFlash_v2.G7.upd), based on upstream
v2.07 plus documentation commit `9c84d99`. The original G7 SHA256 is
`c36c30e3ec04bcffdff07dcf03cf9cdafd007b1cbd7eaeffd719696c6d76f552`.
[build-report.json](build-report.json) now describes the G7.0.3 hotfix;
[SHA256SUMS](SHA256SUMS) identifies all retained downloads.

This log records hardware reports received after packaging. It does not change
the firmware or retrospectively alter the build report's `hardware_tested: false`
snapshot. G7.03 is the current experimental release package; broad compatibility
and remaining hardware checks are not implied by that release name.

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

## 11 November 2026, command 9 report and G7.0.2

During the subsequent update/test attempt, the owner supplied a photograph showing
“Communication with cartridge failed. Unexpected command: 9”, and questioned the
short flash duration. The actual installed image was not independently verified.
Source review nevertheless establishes a second bug in G7.0.1: a warning exits
the C64 browser loop, so its outer dispatcher rejects the returned `CMD_READ_DIR`
command even after the missing synchronisation has been fixed.

G7.0.2 restores the previous SD context and returns `CMD_MENU` after `CMD_SYNC`.
Dismissing a copy result now returns to Home, not directly to the file list.
Host checks derive valid outer commands from the actual launcher source. Negative
checks reproduce failures with both the missing sync and G7.0.1 directory-return
code. **G7.0.1 is superseded, not a successful hardware fix.**

**G7.0.2 hardware retest: pending.** Its internal label remains `2.G7`. Download
[KungFuFlash_v2.G7.0.2.upd](KungFuFlash_v2.G7.0.2.upd), SHA256
`531ea196a6b762218d07fafe37c29f26c7cf7133e2cec43c5acf6aa63343d558`.
The earlier PRG/CRT/settings/reset passes apply to original G7, not a claimed
retest of either hotfix. Verify the SD file checksum and confirm **Upgrade**.
The unchanged upstream updater rewrites 128 KB without a same-version rejection
or unchanged-sector skipping; flash duration has not been measured here.

## 11 November 2026, two-key display report and G7.0.3

The owner reports that dismissing a copy result requires two keypresses: the
first flashes and redraws the prompt; the second reaches the file manager.
The exact installed package checksum was not supplied. VICE reproduced that
symptom in G7.0.2: Home's `waitRelease()` redrew the old terminal because the saved
status mode was not cleared. Home was already accepting input; the second Return
selected Games. The earlier missing-sync and command-9 faults are separate.

G7.0.3 clears that mode on leaving the status view. Its new VICE regression uses
the actual C64 outer dispatcher, warning/key wait, Home and browser, with a
stand-in supplying ARM replies and sample directory contents. It injects one
Return at the prompt and compares the full Home bank with the original assets.
The old build fails that comparison; the corrected build passes, including B/F2/Q.
No SD copying, flash operation or physical bus is emulated by this check.

**G7.0.3 hardware retest: pending.** Confirm one key visibly returns Home, then
check copied content, source retention and folder copying. Earlier hardware
passes remain associated with original G7. Software evidence and runnable PRGs
are in [copy-return tests](../../experiments/copy-return/README.md).

## 11 November 2026, fix confirmation and G7.03 naming

The owner reported “that's working” after the VICE test pack and G7.0.3 firmware
were supplied, then requested G7.03 as the release version replacing G7. The
confirmation did not specify emulator versus real cartridge, individual copy
checks or REU programs. Record it as a reported copy-screen fix confirmation,
without marking a comprehensive hardware pass.

G7.03 is byte-identical to G7.0.3, SHA256
`2d7456f99b3864578da30b0da6280bd0a9ed26ba9e78034f38bb7841253ee402`.
It requires no reflash when the working G7.0.3 image is already installed.
[Release package and notes](../releases/G7.03/RELEASE-NOTES.md).

## Remaining hardware coverage

- Copy a single file to Favourites and load the copy. Confirm the original remains.
- Copy a complete game folder, including companions/multiple disks, and use it.
- Repeat a file copy and try an existing destination name. Confirm no overwrite.
- Use REU software to detect and exercise **256 KB, 512 KB and 1 MB**. Saving the
  selected size alone does not establish address wrapping or DMA operation.

These checks remain open for the experimental release package. Release naming
does not turn them into passes.

## Additional coverage requested

Autoboot-enabled reset, disk/tape loading (D64/D71/D81/T64), history and random
selection across resets, long-directory navigation, search, Help, file options,
text paging, joystick operation, USB, C128 and additional PAL/NTSC/board setups.
Physical CRT readability remains untested.

See [the current checklist](../../docs/testing.md) for expected outcomes and
the details to include in a report. Successful tests and failures are both useful.
