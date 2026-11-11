# G7.03: KFF2 Graphical Menu

Experimental release package, 11 November 2026. G7.03 replaces G7 as the primary
download. It contains the exact firmware previously packaged as G7.0.3; only the
package name changes. The firmware bytes and SHA256 are identical. No new flash
is needed if you already installed the working G7.0.3 build.

The internal cartridge identifier remains **2.G7** because of its fixed-length
launcher field. Identify this release by **KungFuFlash_v2.G7.03.upd** and SHA256:

`2d7456f99b3864578da30b0da6280bd0a9ed26ba9e78034f38bb7841253ee402`

## Included

- Graphical Home with Games, Tools, Utilities and Favourites folder shortcuts.
- Shared border, font and selection style across browser, settings and messages.
- F4 Random from /Games, persistent launch history and recent-game avoidance.
- Copy files or complete game folders to Favourites, keeping originals and refusing overwrites.
- Selectable 256 KB, 512 KB or 1 MB REU size, and an autoboot preference.
- All three copy-result fixes: acknowledgement sync, valid return-to-Home command,
  and clearing the old status display so one keypress visibly restores Home.

## Installation

For **Kung Fu Flash 2**, not the original Kung Fu Flash. Copy the .upd onto a
FAT32 SD card, select it in the KFF2 file browser, then select Upgrade. Keep power
connected until the launcher restarts. No extra PRG, fonts or graphics are needed.
Home uses /Games, /Tools, /Utilities and /Favourites. Names are case-insensitive.
Keep an official or previous working update available for rollback.

[Installation and controls](https://github.com/Soopahfly/kff2-graphical-menu/blob/main/docs/getting-started.md)
[Recovery guide](https://github.com/Soopahfly/kff2-graphical-menu/blob/main/firmware/experimental/RECOVERY.md)

## Test status and limits

Software checks pass: eight VICE navigation scenarios, real keyboard navigation,
NTSC startup, twelve shared-screen checkpoints, one-key copy-result regression,
and host tests of copying, settings, REU callbacks, history, FatFs and assets.
VICE reproduced the G7.0.2 stale-screen fault and verifies the corrected Home bank.
The owner then reported “that's working”. Whether that confirmation referred to
the VICE test or the physical cartridge was not specified. It is recorded as a
reported fix confirmation, not a blanket hardware pass.

Earlier original-G7 hardware reports cover PRG/CRT loading, preference saving and
reset with autoboot disabled. Broader file/folder copy integrity, loading copied
games, collision handling and actual REU use at all three capacities still need
explicit hardware coverage. USB, C128, further video/board setups, physical CRT
readability and recovery procedures also remain incompletely tested.

[Detailed test status](https://github.com/Soopahfly/kff2-graphical-menu/blob/main/docs/testing.md)
[Runnable VICE tests](https://github.com/Soopahfly/kff2-graphical-menu/tree/main/experiments/copy-return)

FAT32 is required; exFAT is not enabled. No G8 features are included. Random
preview, D64 disk swapping, GMod2 and larger-cartridge work remain outside G7.03.

## Build identity

Based on official v2.07 plus documentation commit 9c84d99. Firmware source:
2a395ca9581cba353b2aca9622c5f09dc071026b. Update: 131,072 bytes. C64 launcher:
16 KB, 627 bytes free. ARM code: 77,620 bytes, 20,684 bytes free in its allocation.
RAM/BSS: 25,976 bytes. The reserved 16 KB flash gap remains blank.
The project is an altered build, not an official upstream release.
