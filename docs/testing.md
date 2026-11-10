# Current hardware checks, G7

## What is established

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

G7 has not yet been tested on a physical KFF2. None of the software checks proves
physical bus timing, SD controller behaviour, USB or REU operation. The earlier
LCD photos do not establish CRT readability or compatibility across game loaders.

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
| Change REU size, Save and restart | Selected capacity persists; compatible REU software detects it |
| Set autoboot no, Save, launch a game and reset | Return to Home instead of replaying the saved selection |
| Set autoboot yes, Save, launch a game and reset | Existing saved-selection behaviour resumes |
| Load PRG, CRT and supported disk/tape examples | Existing loader routes/options still work |
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
