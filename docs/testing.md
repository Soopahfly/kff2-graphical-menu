# G7.03 test status

On 23 November 2026, the project owner confirmed that all G7 features had been tested and no issues had been reported. Individual hardware configurations were not specified.
See [release notes](../firmware/releases/G7.03/RELEASE-NOTES.md).

## G8 development status, 17 November 2026

**G7.03 remains the current stable release.** The separate
[G8-parser-01 test build](https://github.com/Soopahfly/kff2-graphical-menu/blob/g8-development/firmware/development/G8-parser-01/README.md)
adds only the unsupported CRT bank rejection fix. Its update is named
`KungFuFlash_v2.G7.03.1.upd`; it retains the internal `2.G7` label.

The candidate passed 219 parser checks and the existing ARM-side regressions.
ARM flash and BSS sizes are unchanged. Its C64 launcher is byte-identical to
G7.03, with matching earlier VICE reports; VICE was not rerun for this ARM-only
change. Physical cartridge testing of the candidate remains pending.
Multi-disk swapping, GMod2 and optional Random preview are still planned.

The owner reported no new issues raised as of 17 November. This is feedback,
not an additional hardware test pass. Candidate hardware checks are listed in
its linked notes: working CRTs, clean rejection of unsupported images, and
ordinary PRG/D64 and Favourites regressions.

## Historical G7.0.3 display-return retest

The owner reports that the first key flashes and redraws “Press a key”, while the
second opens the file manager. VICE reproduced this in G7.0.2: Home was active,
but its key-release check redrew the stale terminal view. G7.0.3 clears that mode
on leaving the status screen. A single buffered Return now restores the exact
Home bank, and B/F2/Q navigation completes. All navigation/shared-UI VICE suites
are rerun against the new launcher. Physical cartridge confirmation is pending.

Use [the two standalone PRGs](../experiments/copy-return/README.md) to compare old
and corrected C64-side behaviour without flashing. These do not test SD copying.
On hardware, verify a single key visibly returns Home after success, repeat-copy,
collision and failure results; then load the copy and confirm source retention.

## Earlier G7.0.2 return-path fix (superseded)

Original G7 was reported to remain on “Added to /Favourites. Original kept. /
PRESS A KEY” after keypresses. A later report during the G7.0.1 update/test attempt
showed “Communication with cartridge failed. Unexpected command: 9”. The owner
also questioned the short flash duration, so the installed image has not been
independently verified. Source review confirms G7.0.1's directory-return path
is invalid after a warning, whether or not that particular flash completed.

G7.0.2 completes the acknowledgement handshake, restores the SD menu context and
issues the outer dispatcher's `CMD_MENU`. Each copy result now returns to **Home**.
Host checks pass and reject both previous faulty return paths; hardware verification
is pending. Copy contents and source retention still need independent checking.

Retest a new file copy, then an identical repeat and a different file with the
same destination name. Each result should dismiss to Home. Open Favourites,
load the copy and confirm the source remains. Repeat with a complete game folder.
The internal label still reads `2.G7`; use `KungFuFlash_v2.G7.03.upd` and its checksum for G7 retesting.
The separate parser candidate is `KungFuFlash_v2.G7.03.1.upd`.

## Hardware report, 11 November 2026

The project owner (Soopahfly) reports these G7 checks passed on real hardware:

| Check | Result | Scope |
| --- | --- | --- |
| PRG loading | Reported pass | Tested titles not specified |
| CRT loading | Reported pass | Tested titles/cartridge types not specified |
| Saving REU size and autoboot preferences | Reported pass | Persistence only; capacities exercised not specified |
| Reset with autoboot disabled | Reported pass | Returns to Home |

These are user-reported hardware results, separate from the automated tests.
Exact C64 board/model, video standard and REU test programs were not supplied
with this report. See the [release hardware log](../firmware/experimental/HARDWARE-TESTS.md).

**Earlier hardware checklist:** verify file/folder copies to Favourites, loading
the copies and no-overwrite behaviour; verify REU software detects and uses each
selected capacity. Saving a capacity setting alone does not establish REU operation.

## Software checks and earlier evidence

| Area | Evidence |
| --- | --- |
| G5 Home and SD-browser appearance | User photographs from a real KFF2 and C64 on an LCD |
| G7 menu navigation | Eight VICE scenarios, keyboard-buffer navigation and NTSC startup capture |
| Shared UI | Twelve VICE checkpoints, border/font checks and text paging checks |
| Favourites copying | Actual code with upstream FatFs on a RAM-backed FAT32 volume |
| G7 settings/autoboot | Actual callbacks, Save and patched boot function with test doubles |
| REU sizes | Actual read/write/swap/compare callbacks with bus test doubles |
| History, random and assets | ARM-side host tests, real FatFs tests and transfer-buffer checks |
| Update layout and space | Packaging checks and the [G7 build report](../firmware/experimental/build-report.json) |

G7 hardware testing has started with the limited results above. The software
checks do not prove physical bus timing, USB or REU operation. The earlier LCD
photos do not establish CRT readability or compatibility across game loaders.

## Before installing

Back up the card/configuration and retain your previous working firmware or an
official KFF2 update. Read [recovery](../firmware/experimental/RECOVERY.md).
Use [Getting started](getting-started.md) for installation and SD folders.

## Suggested test sequence

| Check | Expected result |
| --- | --- |
| Open Home, Games and a nested folder | Border/title retained; actual SD entries readable |
| Scroll past 12 and 23 entries | Selected entry remains visible; no missing/repeated entries |
| F2, B and the four folder shortcuts | Correct folder and selection restored |
| Settings, Help, search and file options | Shared frame, correct controls and clean return to browser |
| Copy a small PRG to Favourites | Original retained; new copy loads from Favourites |
| Copy a small game folder with companion files | All files/subfolders present and usable |
| Repeat a file copy / try an existing folder name | Already-present message or collision, no overwrite |
| Change REU size, then Cancel | Stored setting remains unchanged |
| Change REU size, Save and restart | Settings persist and REU software can use the selected capacity |
| Set autoboot no, Save, launch a game and reset | Return to Home reported working; repeat on additional setups |
| Set autoboot yes, Save, launch a game and reset | Existing saved-selection behaviour resumes |
| Load PRG and CRT examples | Reported working; additional titles/cartridge types welcome |
| Load D64/D71/D81 and T64 examples | Disk/tape loading remains to be confirmed on hardware |
| Open a longer text file | Pages wrap inside the border; forward/back/first/exit work |
| F4, reset and repeat | Games scan works; history/recent avoidance persists |
| Joystick port 2 | Move, Fire, held-Fire options and Fire+left work |
| USB and C128, if available | Existing functions still work; record exact setup |
| CRT display, if available | Names/selection/footer readable; no edge cropping or unstable fine detail |

REU capability is separate from CRT loading. G7 does not enable simultaneous
CRT+REU, so do not use a CRT-only REU test as evidence for the supported modes.
Do not deliberately interrupt power or remove the card during copying/sorting.

## Report a result

Include the firmware filename/version, C64 model and PAL/NTSC standard, display
and cable, SD format, exact file/action, last key pressed and whether reset/menu
recovers. A photo helps with display faults. For file copying, include the source
folder and whether the destination already existed. For REU, record enable state,
capacity and the program used. Record successful checks as well as failures.

The [G5 checklist](g5-testing.md) is retained as historical context. Use this page
for the current candidate and [G7 feature notes](g7-features.md) for expected limits.
