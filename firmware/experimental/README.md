# Experimental firmware G7.0.3, one-key copy-result display fix

[KungFuFlash_v2.G7.0.3.upd](KungFuFlash_v2.G7.0.3.upd) is a complete 128 KB KFF2 update.
It is an altered development build, not an official release. G7 has a positive
hardware report for PRG/CRT loading, saving REU-size/autoboot preferences and
returning to Home after reset with autoboot disabled. Favourites copying and
actual REU operation remain unverified. See [dated hardware results](HARDWARE-TESTS.md)
and the [current test checklist](../../docs/testing.md).

## G7.0.3 hotfix, 11 November 2026

Clears the saved native-terminal view in `browser_leave()`. In G7.0.2 the warning
handshake completed and Home became active, but `waitRelease()` could redraw the
old “Press a key” screen over Home. A second Return then selected Games. G7.0.3
prevents that stale redraw. The copier, configuration and ARM-side `CMD_MENU`
return remain unchanged. There are no G8 features.

VICE reproduces the original G7.0.2 fault and verifies that one Return restores
the exact Home pixels with the correction. B/F2/Q navigation, all eight existing
navigation scenarios, real keyboard navigation, NTSC startup and twelve shared-UI
checkpoints are rerun. [Standalone before-and-after PRGs](../../experiments/copy-return/README.md)
let testers check the C64-side transition without SD access or flashing.
**Physical G7.0.3 retesting remains pending.**

The package is **G7.0.3**; the internal label remains `2.G7`. C64 code grows by
**3 bytes**, leaving **627 bytes** free. The graphics/font bank is unchanged.
The update is still 128 KB with the reserved 16 KB flash gap blank.

G7.0.1 fixed the initial missing sync but could trigger command 9. G7.0.2 fixed
that command return but retained the stale display. Both are superseded; retained
files are for traceability, not current downloads.

The updater accepts the package despite the shared internal version and rewrites
all sixteen 8 KB sectors (128 KB). It does not skip unchanged bytes. Flash duration
has not been measured here; verify the SD file checksum and confirm **Upgrade**.
Leave power connected until the launcher restarts.

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

The C64 launcher remains 16 KB, with **627 bytes spare** in its main allocation.
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
The build report records the current package as `hardware_tested: false`. Earlier
G7 hardware passes and the subsequent failure reports are tracked separately in
[HARDWARE-TESTS.md](HARDWARE-TESTS.md); they are not a hardware pass for G7.0.3.

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
