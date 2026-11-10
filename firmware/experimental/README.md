# Experimental firmware v2.G6, shared appearance

[KungFuFlash_v2.G6.upd](KungFuFlash_v2.G6.upd) is a complete 128 KB KFF2 update.
It is an altered development build, not an official release. G6 has not been
flashed on a physical KFF2. The user previously checked G5 Home and folder-browser
rendering on real hardware.

![Settings in VICE, simulated values](../../preview/g6-settings.png)

G6 extends the existing patterned border, masthead, font and cyan selection to
Settings/REU, F3 cartridge utilities, file options, Help and search. Cartridge
messages, warnings, progress and the text reader also keep the frame once assets
are available. Early startup diagnostics retain native text. See
[the screen map and implementation limits](../../docs/uniform-ui.md).

The C64 launcher remains 16 KB, with **630 bytes spare** in its main allocation.
The ARM graphics/font bank is unchanged. The complete update remains 131,072 bytes.
The separate reserved 16 KB flash region is still blank.

## Install and recover

Read [RECOVERY.md](RECOVERY.md) before flashing. Put the update on a FAT32 SD card
and select it using the working launcher. Keep G5 or an official update available
for rollback. Upstream documents USB DFU and SWD recovery if the launcher fails.

Use `/Games`, `/Tools`, `/Utilities` and `/Favourites` for the four Home cards.
Folder names are case-insensitive. Missing folders warn and fall back to SD root.
Favourites remains a folder you organise yourself. Keep dependent game files
and multi-disk sets together.

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

G6 changes presentation and text-reader page geometry. Existing storage, loader,
cartridge emulation, USB, REU and boot implementations are retained. Compatibility
across those features still needs hardware testing. FAT32 remains required;
exFAT is not enabled.

## Verification

Eight VICE navigation/protocol scenarios, real keyboard-buffer navigation and
NTSC startup capture remain. Twelve further screen checkpoints cover the newly
styled screens, long-menu scrolling, warnings/progress without extra cartridge
requests, reader forward/back pages, wide-character wrapping and startup fallback.
Firmware packaging checks both suites against the exact launcher hash.

ARM dispatcher, random/history, real FatFs and graphics-transfer host tests run
before packaging. Layout checks cover update size, reset/stack vectors, embedded
launcher and blank reserved space. Current numbers and SHA256 are in
[build-report.json](build-report.json) and [SHA256SUMS](SHA256SUMS).

The harness simulates cartridge packets. It does not validate physical bus timing,
SD game loading, USB, REU or CRT readability. Test Settings changes and Save,
file options, Help/search, a warning, long text paging and game loading on hardware.

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
