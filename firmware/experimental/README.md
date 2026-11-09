# Experimental firmware v2.G1, folder Home revision

[KungFuFlash_v2.G1.upd](KungFuFlash_v2.G1.upd) is a complete 128 KB KFF2 update
with the revised graphical Games, Tools, Utilities and Favourites screen.
It replaces the earlier G1 build with the same filename and version identifier.
Download a fresh copy. This is **not an official release and has not been tested
on physical KFF2 hardware**.

![Folder Home running in VICE](../../preview/integration-home.png)

## Install and recover

Read [RECOVERY.md](RECOVERY.md) before flashing. A working launcher can load an
official update from SD. If the launcher fails, upstream documents USB DFU using
BOOT0/+3.3V on J1, or an ST-Link programmer. Those methods require board access.

Use a FAT32 card with `/Games`, `/Tools`, `/Utilities` and `/Favourites` folders.
Their names match the four buttons. Tools and Utilities are normal directories,
with no content restrictions. Favourites is a folder you organise yourself,
not a shortcut database. Keep multi-disk games together in their own directory.

Missing folders produce a message showing the expected path. OK opens SD root.
B opens the regular SD browser; S opens Settings; F3 opens built-in cart utilities;
Q starts BASIC. F2 in the text browser returns Home. Browse preserves its cached
folder/selection; opening a named collection switches to that folder.

## Changes and checks

The native C64 launcher remains 16 KB with **66 bytes free** in its 14 KB main
ROM allocation. The graphics are stored as a 2,644-byte raw LZ4 block and decoded
into the scratch VIC bank at `$4000-$7fff` while the screen is blank. Its stored
font and graphics pixels are unchanged from the approved design.

The ARM source now includes a small folder-dispatch addition. It validates the
four-entry index, clears search for folder switches, handles missing folders,
and retains the original unsaved EasyFlash CRT prompt before changing folders.
The original disk, USB, cartridge emulation, REU and boot implementations are
retained. Hardware compatibility across them remains unverified.

Verified:

- VICE navigation, all four folder requests and cursor-based selection.
- Original paging and Shift+Return selection flag behaviour.
- Native Settings/utilities routes and interactive keyboard Home/Browse/BASIC routes.
- Decompressed graphics bank matches the generated design byte for byte.
- Host tests of the exact ARM dispatcher: four paths, invalid index,
  missing-folder fallback and preservation of unsaved CRT changes.
- Full update size, version, reset/stack vectors, blank padding, embedded launcher
  hash and SHA-256 checksum.

The harness uses simulated directory data. It does not emulate the STM32 or
verify real SD/CRT loading, bus timing, USB, REU, C128 or a physical joystick.

## Image layout

| Region | File offsets | Size |
| --- | --- | ---: |
| ARM firmware allocation | `$00000-$17FFF` | 96 KB |
| Preserved blank padding | `$18000-$1BFFF` | 16 KB |
| Modified C64 launcher | `$1C000-$1FFFF` | 16 KB |

The `.upd` is exactly 131,072 bytes. See [build-report.json](build-report.json)
and [SHA256SUMS](SHA256SUMS) for the build identity. GCC's warnings about upstream's
ITCM vector table at address zero are preserved, not suppressed.

## Reproduce

Requires Python 3, Pillow, liblz4, cc65, make, patch, host GCC for dispatcher
checks, VICE/C64 ROMs for launcher tests, and GNU Arm Embedded GCC/binutils/newlib.

```sh
python3 tools/design_folder_home.py
python3 tools/pack_folder_home.py
python3 tools/build_integrated_launcher.py --upstream /path/to/KungFuFlash2
python3 tools/test_integrated_launcher.py --vice /path/to/x64sc --rom-dir /path/to/C64
python3 tools/build_firmware.py --upstream /path/to/KungFuFlash2
```

The upstream baseline and compiler versions are recorded in the build report.
Unpacked toolchains can use `--arm-bin`, `--newlib-include` and `--newlib-libdir`.
No files in the upstream checkout are edited. The browser itself still uses its
original text renderer. Physical KFF2 validation is the next step.
