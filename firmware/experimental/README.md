# Experimental firmware v2.G1

`KungFuFlash_v2.G1.upd` is a complete 128 KB KFF2 update containing the compact
launcher and graphical home-screen integration. It is built and structurally
verified, **not tested on physical KFF2 hardware**. It is not an official release.

## What changed

- Graphical Home opens when the native launcher enters menu mode.
- Browse uses the original text file browser. F2 returns Home.
- Settings, Utilities and BASIC use the existing menu actions.
- Bounded formatting and a fixed directory object make room for the UI.

No cartridge types, SD/disk formats, REU functionality, USB transfer, freezer
support, direct-boot paths or original browser shortcuts were intentionally
removed. The ARM firmware source is unchanged. Actual compatibility across
those features still needs hardware verification.

## Verified structure

| Region | File offsets | Size |
| --- | --- | ---: |
| ARM firmware allocation | `$00000-$17FFF` | 96 KB |
| Preserved blank padding | `$18000-$1BFFF` | 16 KB |
| Modified C64 launcher | `$1C000-$1FFFF` | 16 KB |

The update is exactly 131,072 bytes. Its launcher bytes match the VICE-checked
build byte for byte. The version identifier, initial stack/reset vectors,
blank padding and SHA-256 checksum are checked by the packaging script.
The C64 main ROM allocation has 217 bytes free.

The VICE harness verifies menu routing and selection messages. It does not
execute or validate the STM32 firmware, bus timing or real storage/loading.

## Reproduce

First build and test the integrated launcher as described in
[the integration notes](../../experiments/home-integration/README.md), then:

    python3 tools/build_firmware.py --upstream /path/to/KungFuFlash2

Requires GNU Arm Embedded GCC, binutils and newlib development files, plus
Python 3 and make. Use `--arm-bin /path/to/bin` when the tools are not on PATH.
For manually unpacked packages, `--newlib-include` and `--newlib-libdir` select
headers and the Cortex-M7 hard-float archive directory. Normally a configured
Arm toolchain supplies these paths itself.

The script builds fresh copied ARM sources and passes the exact native launcher
to the upstream Makefile. It checks matching VICE-build hashes before packaging.
No source files in the upstream checkout are edited.

See [build-report.json](build-report.json) for compiler versions and checksums.
GCC reports array-bounds diagnostics for upstream's ITCM vector table at address
zero. Those diagnostics come from unchanged ARM source; they were not suppressed.

The next step is physical validation: menu entry and return, file loading,
reset, disk/USB support, cartridge modes and REU behaviour. The graphical browser
renderer remains a separate development step.
