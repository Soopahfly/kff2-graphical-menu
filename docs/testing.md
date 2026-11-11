# Current hardware checks, G7

## G7.0.2 hotfix retest

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
The internal label still reads `2.G7`; use the `.0.2.upd` file and its checksum.

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

**Before a first public release:** verify file/folder copies to Favourites, loading
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
| Change REU size, Save and restart | Preference persistence reported working; software detection/use at each capacity remains unverified |
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
