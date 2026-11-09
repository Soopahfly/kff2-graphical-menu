# KFF2 graphical menu, first prototype

A real C64 program using a hires bitmap, proportional EasyFlash 3 text and a
larger heading and a cyan high-kick silhouette. This is an interface prototype, not a KFF2 firmware update.

## Try it in VICE

1. Extract the download.
2. Open VICE's C64 emulator (x64sc).
3. Choose File > Autostart disk/tape image and select `kff2-menu-preview.prg`.
4. Use cursor keys and Return, or the B/U/S/Q shortcuts.

With VICE configured for a joystick in port 2, up/down selects and fire opens.
F3 opens Utilities, F5 opens Settings, F7 returns to BASIC. In the sample browser,
F2 or Run/Stop returns home. There are no ROMs or games in this package.

## What works

- The bitmap home screen and proportional text renderer run on the emulated C64.
- Four menu entries, highlight, contextual description and wraparound navigation.
- B opens an illustrative browser. U and S open explicitly labelled placeholders.
- Q exits the program to BASIC, restoring VIC bank and display registers.
- The preview uses the upstream KFF2 keyboard/joystick handling (`base.c`).

The browser list is sample data. It does not access an SD card, load a game,
configure a cartridge or implement favourites. The production KFF2 launcher
and its cartridge protocol are unchanged.

## Build

Install cc65, GNU make and sed. In the KFF2 checkout:

    make -C launcher/preview

Output: `launcher/build/preview/kff2-menu-preview.prg`

The source directories in this package belong under `launcher/` in the KFF2
repository. No ARM compiler is needed for this preview. The full firmware
will need its original ARM toolchain when integration is ready.

## Implementation and memory

- `ui/kicker.h`: 64x88 upright one-bit silhouette, 704 bytes in VIC-II tile order.
- `tools/make_kicker.py`: reproducible code-native icon generator.
- `ui/home.c`: shared home renderer and input loop, no cartridge register access.
- `ui/text_plot*` and `ui/charset.sed`: EF3 proportional font renderer and font.
- `preview/main.c`: mock action dispatch and sample browser for VICE.
- Program entry: BASIC SYS stub at $0801, machine-code startup $080D.
- Program, BSS and C stack are kept below $4000 by the linker.
- VIC bank: $4000. Bitmap matrix: $5C00-$5FE7. Bitmap: $6000-$7F3F.
- Home temporarily disables sprites and Shift+Commodore charset switching.
- Assumes the normal KERNAL raster setup, without an application raster IRQ.
  This is not a display overlay for arbitrary running games.

## Firmware integration still to do

The current launcher links into a $3800-byte ROM area at $8000. Its baseline
RODATA ends at $B2B8, but DATA initializers occupy ROM through $B349.
The actual remaining space is 1,206 bytes. The prototype's renderer, font
and screen logic require more space than that. Integration needs a deliberate
ROM/RAM layout change or a smaller renderer/font. A link-only investigation
has now confirmed a separate 4,062-byte UI payload fits in a proposed layout;
see [the ROM-space investigation](../../docs/rom-space-investigation.md).
The firmware transfer and integrated boot are still pending.

The firmware also sends 23 entries per page. A taller graphical browser header
requires coordinated paging changes, or a C64-side scrolling viewport.

Once the memory layout is settled, the home actions map to existing operations:

| Home result | Existing launcher action |
| --- | --- |
| HOME_BROWSE | Return to the current browser |
| HOME_UTILITIES | REPLY_UTILITIES |
| HOME_SETTINGS | REPLY_SETTINGS |
| HOME_BASIC | REPLY_BASIC |

Favourites and KERNAL replacement are outside this first prototype.

## Verification, 9 November 2026

Built with cc65 Git eebf54a. Ran the compiled PRG in VICE x64sc 3.7.1:

- PAL and NTSC startup, screenshots inspected.
- Down selection, up wraparound and Return selection via C64 keyboard buffer.
- B browser, S settings placeholder and Q exit to BASIC.
- Utilities selected using cursor-down then Return.
- Display restoration inspected after leaving bitmap mode.
- Link map checked for overlap; PRG load address and SYS entry checked.

Joystick support is implemented using upstream code, but physical joystick
input and real C64/KFF2 hardware have not been tested. No flashable firmware
is included. Screenshots are emulator captures, not design mockups.

## Provenance

KFF2 upstream: https://codeberg.org/KimJorgensen/KungFuFlash2
Base commit: 9c84d99 (main, one commit after v2.07).

EF3 menu source: https://github.com/easyflash-mirror/easyflash3-bootimage
Base commit: bf89562. Font and text renderer by Thomas Giesel.
Original notices retained. The new home/preview code is an altered development
version, not an official KFF2 or EasyFlash release. See LICENSE and
`source/launcher/ui/EF3-LICENSE.md` in the download.
