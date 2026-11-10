# Experimental firmware v2.G2, Random game and menu fixes

[KungFuFlash_v2.G2.upd](KungFuFlash_v2.G2.upd) is a complete 128 KB KFF2 update
with the revised graphical Games, Tools, Utilities and Favourites screen.
Use G2 for new testing. The retained G1 image has known disk-image-exit and
cart-utilities context bugs, fixed in G2. This is **not an official release and has not been tested
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

## Random game

**F4 on Home** scans `/Games` and its subfolders and starts a randomly selected
CRT, PRG, P00, supported disk image or T64. Updates/text/hidden files are excluded.
Disk images autostart. Selection is per file, so duplicates, auxiliary programs
and secondary disks can also be picked. Missing or empty collections show a
message. See [selection rules and limits](../../docs/random-game.md).

G2 closes active disk/tape images when switching Home context and fixes F3 cart
utilities from Settings/options. Its dedicated Home replies leave normal browser
shortcuts intact. It reclaims unneeded RODATA page-alignment padding; CODE's
original page alignment and the image layout below are retained.

## Changes and checks

The native C64 launcher remains 16 KB with **89 bytes free** in its 14 KB main
ROM allocation. The graphics are stored as a 2,688-byte raw LZ4 block and decoded
into the scratch VIC bank at `$4000-$7fff` while the screen is blank. Its stored
font and graphics pixels are unchanged from the approved design.

The ARM source includes Home dispatch and random selection modules. It validates the
four-entry index, clears search for folder switches, handles missing folders,
and retains the original unsaved EasyFlash CRT prompt before changing folders.
The original disk, USB, cartridge emulation, REU and boot implementations are
retained. Hardware compatibility across them remains unverified.

Verified:

- VICE navigation, all four folder requests, cursor-based selection and F4 dispatch.
- Original paging and Shift+Return selection flag behaviour.
- Native Settings/utilities routes and interactive keyboard Home/Browse/BASIC routes.
- Decompressed graphics bank matches the generated design byte for byte.
- Host tests of the exact ARM dispatcher: four paths, invalid index,
  10,000 selection seeds, hidden/non-game filtering, scan-error cleanup, launch
  routes, image/options context transitions and preservation of unsaved CRT changes.
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
