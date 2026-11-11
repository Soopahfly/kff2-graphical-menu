# Building G7

## Inputs and dependencies

Use a checkout of this repository and upstream Kung Fu Flash 2 pinned to
`9c84d999f4e2f5b2c7688cbc37a127069f5401b0`. This is v2.07 plus one documentation
commit. Build scripts copy and patch upstream files; they do not modify that checkout.

Dependencies:

- Python 3 and Pillow; system liblz4 for graphics-bank fixture packing.
- cc65 tools, GNU make and patch.
- VICE x64sc with your own C64 KERNAL, BASIC and character ROMs.
- Host GCC and address/undefined-behaviour sanitizer support for ARM-side tests.
- GNU Arm Embedded GCC/binutils with newlib headers and libraries for firmware.

The packaged G7 report records cc65 from Debian 2.19-1 and ARM GCC 12.2.1.
Compiler or library changes can change sizes and checksums; rerun the checks.
No C64 ROMs or games are distributed with this project.

## Build and verify

The commands below assume Linux or WSL with the dependencies installed.
Run from this repository's root, replacing the example paths:

```sh
python3 tools/build_integrated_launcher.py --upstream /path/to/KungFuFlash2
python3 tools/test_integrated_launcher.py --vice /path/to/x64sc --rom-dir /path/to/C64
python3 tools/test_uniform_ui.py --vice /path/to/x64sc --rom-dir /path/to/C64
python3 tools/test_copy_return.py --vice /path/to/x64sc --rom-dir /path/to/C64
python3 tools/build_firmware.py --upstream /path/to/KungFuFlash2
```

The ROM directory must contain:

- `kernal-901227-03.bin`
- `basic-901226-01.bin`
- `chargen-901225-01.bin`

For the G7.0.3 hotfix, add `--package-version 2.G7.0.3` to the firmware-builder
command. This changes the download filename and report package version while
preserving the internal `2.G7` identifier. G7.0.3 changes the C64 status-view
cleanup; its new launcher must pass all VICE suites. The
original G7 `.upd` remains alongside the new package.

The default identifier is `2.G7`. The launcher builder also accepts `--version`;
the firmware builder takes its version from the launcher measurements. Version
identifiers must fit the existing 20-byte launcher name field.

For unpacked toolchains, put cc65 executables on `PATH` and use `--cc65-home`
for the directory containing its `cfg`, `include` and `lib` folders. The firmware
builder accepts `--arm-bin`, `--newlib-include` and `--newlib-libdir`.
Use each script's `--help` for the argument names.

## What packaging checks

The firmware builder requires the navigation, shared-UI and one-key copy-return VICE reports to match
the exact native image/preview hashes. It then runs the Home/random, history,
real FatFs, asset-transfer and G7 feature tests before compiling the ARM image.

G7 tests include configuration size/offsets, actual menu Save and boot callbacks,
FAT32 file/folder copying and failures, and actual REU callbacks at all three sizes.
These are software checks, not physical KFF2 emulation.

Layout checks cover the 128 KB update, embedded 16 KB launcher, reset/stack vectors,
ARM allocation and unchanged blank 16 KB region. The packaged G7 launcher has
627 bytes free in its main allocation. Upstream zero-address vector-table compiler
warnings remain visible; they are recorded in the build report.

## Outputs

| Location | Contents |
| --- | --- |
| `launcher/build/integration/` | Patched C64 source, native ROM, measurements, VICE harnesses/screenshots/results |
| `launcher/build/arm-firmware/` | Patched ARM source, host-test log, compiler log and firmware artifacts |
| `firmware/experimental/KungFuFlash_v2.G7.0.3.upd` | Current hotfix update |
| `firmware/experimental/build-report.json` | Current package identity and measurements |
| `firmware/experimental/SHA256SUMS` | Checksums for retained updates |

Generated `launcher/build` contents are ignored by git. Current release snapshots
of the native measurements and VICE results are checked in under
`experiments/home-integration`. Historical prototype measurements are separate.

The checked-in artwork is sufficient for a normal build. To change Home artwork,
regenerate it with `tools/design_folder_home.py` and `tools/pack_folder_home.py`,
then rebuild and repeat the relevant graphics and navigation checks.

For implementation details, see [integration](../experiments/home-integration/README.md),
[browser](browser.md), [shared appearance](uniform-ui.md) and [G7](g7-features.md).
