# Experimental firmware G7.0.2, Favourites acknowledgement fix

[KungFuFlash_v2.G7.0.2.upd](KungFuFlash_v2.G7.0.2.upd) is a complete 128 KB KFF2 update.
It is an altered development build, not an official release. G7 has a positive
hardware report for PRG/CRT loading, saving REU-size/autoboot preferences and
returning to Home after reset with autoboot disabled. Favourites copying and
actual REU operation remain unverified. See [dated hardware results](HARDWARE-TESTS.md)
and the [current test checklist](../../docs/testing.md).

## G7.0.2 hotfix, 11 November 2026

Fixes both stages of the Copy to Favourites return path. G7.0.1 supplied the
missing `CMD_SYNC`, but then sent `CMD_READ_DIR` (9) to the outer C64 dispatcher,
which does not accept directory commands. G7.0.2 restores the previous SD menu
context and returns `CMD_MENU` instead. Dismissing any copy result returns to
**Home**; use Favourites or B/Browse to inspect the copy. The copier, configuration,
C64 launcher and graphics are unchanged. There are no G8 features.

The download version is **G7.0.2**; the internal identifier remains `2.G7` to fit
the existing launcher field. ARM code is 77,620 bytes, with 20,684 bytes available.
RAM/BSS and the exact C64 launcher/graphics hashes are unchanged. Original
[G7](KungFuFlash_v2.G7.upd) and [G7.0.1](KungFuFlash_v2.G7.0.1.upd) remain for
traceability, but their Favourites acknowledgement/return paths are faulty.
**G7.0.1 is superseded.**

Software checks pass. Regression checks derive allowed commands from the actual
C64 outer dispatcher and reject both previous faults. Existing VICE evidence is
reused for the byte-identical launcher; this is not physical ARM/C64 bus emulation.
**G7.0.2 has not yet been retested on hardware.** After updating, copy a file,
dismiss the result, confirm Home appears, then open Favourites and load the copy.
Check the source remains and repeat with a complete game folder.

The updater accepts this package despite the shared internal version, and rewrites
all sixteen 8 KB sectors (128 KB). It does not skip unchanged bytes. We have not
measured a reliable flash duration; a quick return alone cannot prove an update.
Verify the SD file's checksum, select it, then select **Upgrade** on the confirmation
screen and leave power connected until the launcher restarts.

![G7 Settings in VICE, example values](../../preview/g7-settings.png)

G7 adds **Copy to Favourites** in Shift+Return SD file/folder options, plus
**REU size** (256 KB / 512 KB / 1 MB) and **Autoboot last selection** in Settings.
Save commits settings; existing cards retain 1 MB and autoboot enabled. The original
1,024-byte configuration layout is retained. Read [G7 operation and limits](../../docs/g7-features.md).

The base is upstream **v2.07 plus one documentation commit**, `9c84d99`.

G6 introduced the existing patterned border, masthead, font and cyan selection to
Settings/REU, F3 cartridge utilities, file options, Help and search. Cartridge
messages, warnings, progress and the text reader also keep the frame once assets
are available. Early startup diagnostics retain native text. See
[the screen map and implementation limits](../../docs/uniform-ui.md).

The C64 launcher remains 16 KB, with **630 bytes spare** in its main allocation.
The ARM graphics/font bank is unchanged. The complete update remains 131,072 bytes.
The separate reserved 16 KB flash region is still blank.

## Install and recover

Use [Getting started](../../docs/getting-started.md) and the
[current hardware checks](../../docs/testing.md). Read [RECOVERY.md](RECOVERY.md) before flashing. Put the update on a FAT32 SD card
and select it using the working launcher. Keep G6 or an official update available
for rollback. Upstream documents USB DFU and SWD recovery if the launcher fails.

Use `/Games`, `/Tools`, `/Utilities` and `/Favourites` for the four Home cards.
Folder names are case-insensitive. Missing folders warn and fall back to SD root.
Favourites is an ordinary folder, populated on a PC or using G7 Copy to Favourites.
Keep dependent game files and multi-disk sets together.

B opens Browse, S opens Settings, F3 opens built-in cart utilities, Q starts BASIC.
F2 returns Home. Settings contains the existing REU enable/disable control.
The Utilities card opens the SD folder, independently of the F3 functions.

## Existing features

G3 launch history, recent-game avoidance and F4 Random remain. F4 recursively
selects supported files under `/Games`; selection is per file, so auxiliary files,
duplicate releases and secondary disks can also be picked. Manual Games launches
and random launches are logged after loader preparation, before C64 handoff.
History writes are best effort. See [random rules](../../docs/random-game.md) and
[history/export](../../docs/launch-history.md).

G7 retains G6 presentation and text-reader page geometry, adding ARM-side copies
and settings. REU address wrapping changes to match the selected capacity. Existing storage, loader,
cartridge emulation, USB, REU and boot implementations are retained. Compatibility
across those features still needs hardware testing. FAT32 remains required;
exFAT is not enabled.

## Verification

Eight VICE navigation/protocol scenarios, real keyboard-buffer navigation and
NTSC startup capture remain. Twelve further screen checkpoints cover the newly
styled screens, long-menu scrolling, warnings/progress without extra cartridge
requests, reader forward/back pages, wide-character wrapping and startup fallback.
Firmware packaging checks both suites against the exact launcher hash.

G7 additionally checks real FAT32 file/folder copies, collisions, read-only media,
interrupted-copy protection and failures, configuration size/offsets and actual
settings/autoboot callbacks. Actual REU read/write/swap/compare callbacks are
host-tested at all three capacities.

ARM dispatcher, random/history, real FatFs and graphics-transfer host tests run
before packaging. Layout checks cover update size, reset/stack vectors, embedded
launcher and blank reserved space. Current numbers and SHA256 are in
[build-report.json](build-report.json) and [SHA256SUMS](SHA256SUMS).
The build report records the state at packaging time; its `hardware_tested: false`
field predates these user reports. Post-build evidence is tracked separately in
[HARDWARE-TESTS.md](HARDWARE-TESTS.md).

The harness simulates cartridge packets. It does not validate physical bus timing,
SD game loading, USB, REU or CRT readability. Test Settings changes and Save, both autoboot values, REU software at each
capacity, copying a small file and a complete game folder, and game loading on hardware.

## Reproduce

Requires Python 3, Pillow, liblz4, cc65, make, patch, host GCC, VICE with C64 ROMs,
and GNU Arm Embedded GCC/binutils/newlib. Baseline upstream commit:
`9c84d999f4e2f5b2c7688cbc37a127069f5401b0`.

```sh
python3 tools/build_integrated_launcher.py --upstream /path/to/KungFuFlash2
python3 tools/test_integrated_launcher.py --vice /path/to/x64sc --rom-dir /path/to/C64
python3 tools/test_uniform_ui.py --vice /path/to/x64sc --rom-dir /path/to/C64
python3 tools/build_firmware.py --upstream /path/to/KungFuFlash2
```

Unpacked toolchains can use `--cc65-home`, `--arm-bin`, `--newlib-include` and
`--newlib-libdir`. Earlier update files are retained for comparison and rollback.
