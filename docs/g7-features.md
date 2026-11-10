# G7 favourites and startup/REU settings

G7 uses upstream **v2.07 plus one documentation commit**,
`9c84d999f4e2f5b2c7688cbc37a127069f5401b0` (the v2.07 tag is
`60b82792bd8275f4ca9e9c43300766e02b05dfcf`). It retains G6's graphical interface.
It does not import a community fork or expand cartridge format support.

## Copy to Favourites

In the SD browser, highlight a file or game folder and use **Shift+Return**
(or hold joystick fire). Choose **Copy to Favourites**.

- A file is copied to `/Favourites/<filename>`.
- A folder is copied to `/Favourites/<foldername>`, including its subfolders,
  companion files, hidden companion files and additional disks.
- `/Favourites` is created if missing. Originals remain untouched.
- An identical file with the same name reports that it is already present.
  A different file or an existing folder with that name is never overwritten.
- Copying a loose disk image does not discover other disks automatically. Select
  the game folder for a set or any game requiring companion files.
- The action is offered for directories and SD CRT, ROM/BIN, PRG, P00, disk and
  T64 files. It is not offered for entries inside an opened disk/tape image.
- Duplicate checking covers the destination name. Differently named copies of
  the same game are not identified by a catalogue or checksum database.

Copies are staged at `/Favourites/.KFF2-copy.tmp` and moved to their final name
only after copying and closing the files. On a normal error, G7 attempts to
remove only staging created by that operation. Power interruption or a failing
card can leave staging behind. A later copy refuses to overwrite it; inspect or
remove that exact temporary path on a PC before retrying. This is not a guarantee
against filesystem damage from interrupted power.

Do not remove the card or interrupt power during copying. G7 shows a waiting
message; copying has no interactive cancel button. Limits: eight nested directory
levels below the selected folder, 4,096 files/directories and 1,023-byte absolute
paths. A failed or oversized copy is not published as a completed favourite.

## Settings

Open **S** from Home or **F5** in the browser. Change a value with Return/fire,
then select **Save**. Cancel leaves the stored settings unchanged.

| Setting | Values | Default for existing G6 cards |
| --- | --- | --- |
| RAM expansion (REU) | Existing yes/no control | Unchanged |
| REU size | 1 MB, 512 KB, 256 KB | 1 MB |
| Autoboot last selection | yes/no | yes |

The REU size applies when REU emulation is enabled. Its address space wraps at the
selected capacity in reads, writes, swaps and comparisons. The underlying physical
buffer remains 1 MB. This does not enable REU together with CRT emulation.

With autoboot set to **no**, power-up/reset enters the menu instead of restarting
the last stored selection. Manually selecting a game still starts it normally.
The cartridge Menu button and its long-press diagnostic route remain available.
This option does not change disk-image autostart after manual selection.

## Configuration compatibility

The original `.KFF2.cfg` remains 1,024 bytes. Its signature, flags, timing offset,
boot data, filename and path offsets are unchanged. G7 uses a tagged value in the
existing reserved word for its three REU-size choices and autoboot bit. Zero or
an unrecognised tag uses the existing 1 MB/autoboot-on defaults.

G6 ignores that word and preserves it when saving its usual configuration.
Downgrading to G6 therefore retains the original fields and G7 preferences, although
G6 itself always uses its previous REU/startup behaviour. This compatibility applies
to our G6/original layout, not arbitrary community forks with different layouts.

## Validation and remaining hardware checks

- Actual copy code runs against upstream FatFs on a RAM-backed FAT32 volume.
  Tests cover files/folders and companions, original preservation, same-name
  duplicates, collisions, interrupted-copy protection, read-only media, depth and
  write failures, cleanup and persistence after remount.
- Compile-time checks fix the original configuration size and path/name offsets.
  Tests exercise actual menu callbacks, Save, the patched autoboot function,
  Menu/diagnostics overrides and the G6 reserved-word round trip.
- The actual patched REU DMA read/write/swap/compare callbacks run with bus test
  doubles at all three sizes, including boundary wrapping and fixed addresses.
- Existing VICE navigation, keyboard/NTSC and twelve shared-screen checks remain.
  Firmware packaging requires the test hashes to match the launcher.

G7 still needs physical KFF2 testing. Check a small PRG copy, a folder containing
companion files, a collision, persistence after restart, both autoboot values and
REU software at the chosen size. Software tests do not prove cartridge bus timing.
Keep a known working G6 or official update available for rollback.
