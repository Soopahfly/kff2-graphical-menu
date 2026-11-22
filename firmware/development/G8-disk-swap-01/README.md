# G8-disk-swap-01 development firmware

Use `KungFuFlash_v2.G7.03.2.upd` from this folder or the ZIP. The internal
version still reads `2.G7`. This candidate includes D64 disk swapping and the
earlier CRT parser fix. GMod2 and Random preview remain planned.

## Set up a game

On the FAT32 card, put the game's disk images together in one folder. Create
a plain text file named `disks.lst` in that folder and list the actual filenames
in play order, one per line. For example:

```text
My Game Disk 1.d64
My Game Disk 2.d64
My Game Disk 3.d64
```

Open the first disk as an emulated disk from the menu. Opening another listed
disk starts the sequence from that position. When the game asks for a disk,
use the cartridge's **Special** button:

| Action | Result |
| --- | --- |
| Tap and release Special | Mount the next listed disk, wrapping to the first |
| Hold Special for about ¾ second and release | Mount the first listed disk |
| One LED flash | Request succeeded |
| Three LED flashes | Swap failed or the drive was busy. Retry when idle |

Swapping requires idle channels. A game that holds a file or a drive buffer
open can prevent a swap. The firmware syncs the old image and checks the
replacement with its normal disk loader before switching. If the replacement
is missing, unreadable or the wrong image type, the current disk stays mounted
provided the original card and image remain accessible.

The list accepts up to 16 D64 basenames, 255 bytes each, and 8 KiB total.
ASCII filenames are easiest to use. For extended characters the list must
match the firmware's CP437 filename encoding. LF, CRLF, empty lines and an
optional UTF-8 BOM are accepted. Names are case-insensitive. Use actual
filenames and omit comments, directory paths and trailing spaces. A missing
or malformed list, or a disk absent from the list, leaves ordinary loading
available with swapping disabled. Copy the entire game folder to Favourites
to carry its list and disk images together.

## Verification

The real FatFs FAT32 test covered list syntax and limits, case-insensitive
matching, next/wrap/first, dirty writes and sync failures, missing images,
failed header reads, D71 rejection, read-only images, open channels and
button debounce. The graphical build passed the existing ARM regression
suites and included the same C64 launcher and graphics as G7.03. The
standalone patch also compiled with the original v2.07 launcher.

The graphical ARM image uses 78,880 of 98,304 bytes, leaving **19,424 bytes**.
It adds 1,260 bytes of ARM flash and 5,432 bytes of static RAM over the parser
candidate. The C64 launcher has the same 627 bytes free.

Physical testing is pending. Test a real multi-disk game through next, wrap
and first. Save to a disposable copy of a disk image and check that the save
survives swapping away and back. Remove the *next image file* before starting
the test and verify that a failed swap leaves the first disk usable. Check
Special still works in a freezer cartridge and ordinary D64s still mount.

[Standalone patch and tests](../../../experiments/d64-swapping/README.md)

## Rebuild

Prepare the G7 launcher and matching VICE reports using the
[build guide](../../../docs/building.md), then run:

```sh
python3 tools/build_firmware.py --upstream /path/to/KungFuFlash2 \
  --package-version 2.G7.03.2 --crt-parser-fix --disk-swapping \
  --output-dir firmware/development/G8-disk-swap-01
```
