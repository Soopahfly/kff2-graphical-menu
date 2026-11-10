# KFF2 Graphical Menu

An experimental graphical home screen integrated with Kung Fu Flash 2's native
launcher, inspired by EasyFlash 3. The current firmware candidate is **v2.G2**.
It is built and software-checked, not tested on physical KFF2 hardware.

![Graphical home](preview/integration-home.png)

## Current milestone

**F4: Random game** picks a supported file from `/Games` and its subfolders,
then uses the original loader. See [behaviour and limits](docs/random-game.md).
G2 also fixes leaving disk images and opening cart utilities from Settings.
Do not use the older G1 image for new testing.

**Games / Tools / Utilities / Favourites > original text browser > Home** is
connected. F2 returns Home while preserving the folder and selected entry. B
opens Browse, S opens Settings, F3 opens built-in cart utilities and Q opens BASIC.
The file browser still has its original text appearance.

The native C64 image remains 16 KB, with **129 bytes free** in its main ROM
allocation. The unused 16 KB flash region is not used. The full MCU update is
128 KB. No original cartridge features were intentionally removed, and the ARM
firmware adds folder dispatch and random selection. Full compatibility needs hardware testing.

Existing autoload and direct PRG/USB, cartridge and disk boot paths remain;
the home screen appears when the native launcher enters menu mode.

## Try it in VICE

Autostart [kff2-integration-test.prg](preview/kff2-integration-test.prg) in x64sc.
This runs the patched native menu with a simulated cartridge data source:

- B on Home opens the directory. Cursor keys and Return select.
- F2 returns Home without clearing the folder or selection.
- G/T/U/F open the four simulated collections; S/F3 open Settings/cart utilities.
- F4 records a random-game request in the harness; it does not scan or load SD files.
- Q on Home exits the harness to BASIC.

Directory entries are test data. No SD files or games are loaded. This harness
does not emulate the cartridge's ARM hardware, disk drive, USB or REU.
The earlier [visual-only preview](preview/kff2-menu-preview.prg) remains available.

## Experimental firmware

The complete update, checksum and build report are under
[firmware/experimental](firmware/experimental/README.md). The software checks
verify layout and menu routing; they do not validate physical cartridge timing
or loading. This is an altered development build, not an official release.

## Build and test

Install cc65, GNU make, patch and Python 3. Generating artwork also needs Pillow and liblz4. Obtain the upstream KFF2 source at
commit `9c84d999f4e2f5b2c7688cbc37a127069f5401b0`, then:

    python3 tools/design_folder_home.py
python3 tools/pack_folder_home.py
python3 tools/build_integrated_launcher.py --upstream /path/to/KungFuFlash2

This builds the native launcher and interactive/automated VICE harnesses.
Run the VICE checks with your own C64 ROMs:

    python3 tools/test_integrated_launcher.py --vice /path/to/x64sc \
        --rom-dir /path/to/vice/C64

With a configured GNU Arm Embedded toolchain and newlib development files:

    python3 tools/build_firmware.py --upstream /path/to/KungFuFlash2

The packaging script checks that the software-test hashes match the launcher.
See [integration notes](experiments/home-integration/README.md) and
[firmware notes](firmware/experimental/README.md) for inputs, outputs and limits.

The older standalone UI can be built with `make -C launcher/preview`.
Regenerate the artwork using `python3 tools/make_kicker.py`.

## Size work

- The UI payload was reduced from 4,062 to **3,241 bytes**, with identical pixels
  and all font mappings retained. See [optimisation notes](docs/ui-size-reduction.md).
- Replacing general formatting and a single heap allocation saves **2,560 bytes**
  in the native launcher. See [optional patches](experiments/launcher-size/README.md).
- The initial [ROM investigation](docs/rom-space-investigation.md) also documents
  the separate-payload option if future growth makes it useful.

## Next

Read the [recovery guide](firmware/experimental/RECOVERY.md), test the build on physical KFF2 hardware, then replace the text
browser renderer. Preserve the 23-entry page protocol and selection indexes.
Favourites and further cartridge features are later work.

## Upstream and credits

This repository contains the UI, build tools and patches. Native builds use:

- [Kung Fu Flash 2](https://codeberg.org/KimJorgensen/KungFuFlash2),
  Kim Jørgensen, baseline `9c84d99` (one commit after v2.07).
- [EasyFlash 3 menu](https://github.com/easyflash-mirror/easyflash3-bootimage),
  Thomas Giesel, baseline `bf89562`, providing the proportional font and renderer.

Original notices are retained. See [LICENSE](LICENSE) and
[EF3-LICENSE.md](launcher/ui/EF3-LICENSE.md). No C64 ROMs or games are distributed.
