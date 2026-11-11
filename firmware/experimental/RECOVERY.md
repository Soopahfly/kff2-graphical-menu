# Installing and recovering KFF2 firmware

This guide is for **Kung Fu Flash 2**, not the original KFF cartridge.
The current **v2.G7** build is experimental, with limited positive hardware
reports for PRG/CRT loading, preference saving and reset with autoboot disabled.
Favourites copies, actual REU operation and broader compatibility still need testing.
See [the hardware log](HARDWARE-TESTS.md). Recovery procedures themselves have not
been tested as part of this project; the methods below are documented upstream.

## Install or roll back using a working launcher

1. Keep a copy of an official KFF2 `.upd` from the upstream releases page on
   your PC, as well as a backup of your SD card configuration.
2. Copy `KungFuFlash_v2.G7.upd` to the FAT32 SD card. The UI is built in; it
   does not need a menu PRG, graphics folder or fonts on the card.
3. Create `/Games`, `/Tools`, `/Utilities` and `/Favourites`, then add your
   normal files. Missing folders show a message; OK opens the SD root.
4. In the existing KFF2 browser select the `.upd` and confirm the firmware
   update. Leave power connected and do not reset during programming.
5. On the new Home screen, B opens Browse SD so another `.upd` can be selected.
   This is also how to restore an official image while the launcher still works.

G7 is the current test candidate. Keep your previous working firmware or an
official image for rollback. Older images are retained as build history.
`SHA256SUMS` identifies each file. Back up `.KFF2-history` with the SD card;
restoring older firmware will not itself erase that file. G7 keeps the original
configuration layout; see [settings and downgrade compatibility](../../docs/g7-features.md).

For SD layout, first-boot checks and controls, use [Getting started](../../docs/getting-started.md).

## USB DFU recovery when the launcher will not run

DFU is the microcontroller's USB firmware-loading mode. It does not require a
working graphical launcher. The upstream KFF2 instructions specify:

1. Power off and remove the cartridge from the C64. Do not perform this with
   the cartridge connected to the C64.
2. With power disconnected, open the case and locate **J1** on the PCB. Verify
   the board labels. Fit a jumper between **BOOT0** and **+3.3V** on J1.
   Do not guess the pins or use a 5V connection.
3. Connect the cartridge to the PC by a USB data cable. With BOOT0 high it
   starts in DFU mode. Install/configure `dfu-util` and the appropriate USB
   driver for your operating system if required.
4. Program a known-good official KFF2 update, substituting its actual filename:

   ```sh
   dfu-util -a 0 -s 0x08000000 -D KungFuFlash_v2.xx.upd
   ```

5. After successful programming, disconnect USB power and remove the BOOT0
   jumper. Reassemble the cartridge, then reconnect it to the C64.

Recovery may require opening the case and access to PCB pads/header pins.
It is not a guaranteed button-only or SD-only recovery procedure.

## SWD alternative

Upstream recommends an ST-Link V2 on J1: **3.3V, GND, SWDIO and SWCLK**, with
BOOT0 connected to 3.3V. Rename the known-good official `.upd` to `.bin` and
program it using STM32CubeProgrammer. Follow the upstream wiring instructions,
keep the cartridge disconnected from the C64, and remove all programming wires
when finished.

## Sources

- [Official KFF2 firmware installation and board connections](https://codeberg.org/KimJorgensen/KungFuFlash2/src/branch/main/firmware/README.md)
- [Official KFF2 releases](https://codeberg.org/KimJorgensen/KungFuFlash2/releases)

The upstream installation methods provide a recovery route for firmware faults.
They do not cover physical damage or incorrect electrical connections.
