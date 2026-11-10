# G3 launch history and recent-game avoidance

G3 automatically creates `/.KFF2-history` on the SD card. It is separate from
`.KFF2.cfg`, so existing cartridge settings and calibration are retained. The
journal is hidden from the KFF2 browser because its name begins with a dot.
No empty database or additional menu PRG needs to be copied to the card.

## Recorded information

Each verified journal record contains:

- The full file path, with ASCII letter case normalised.
- A global increasing launch number.
- Total launch count for that path.
- Random-runner launch count for that path.
- Whether this particular start came from F4 or manual selection.

Manual launches of supported programs outside `/Games`, such as tools or files
in Favourites, also get counts. Only `/Games` entries influence the random
runner's recent-game window. Copies in different directories and different
formats are separate entries. Moving or renaming a file creates a new identity.
Contents are not hashed to merge game versions or copied favourites. Playing a
copied Favourite does not mark the separate Games copy as recent. Programs inside
a disk/tape image count toward the container image path, not separate entry names.

## What counts as a launch

The journal is updated after a loader has prepared the program/image, immediately
before handing control to the C64. It counts an intended, loader-prepared start.
It cannot prove that the game booted successfully or measure how long it ran.

- Browsing directories, entering disk images and reading text do not count.
- Mounting a disk without autostart does not count.
- Automatic boots/resets do not count again. A new explicit launcher selection does.
- Auxiliary loads performed by a running game do not create extra launches.
- Programs loaded later by BASIC commands are outside the launcher counting path.
- Failed loader preparation is not recorded.

The file is synchronised and closed before starting the game. History does not
write in the background during gameplay or use cartridge/REU image buffers.

## Random selection

F4 still scans `/Games` and its subfolders. It now picks randomly among eligible
files outside the **10 most recently launched distinct Games paths**, including
manual launches. Tool launches do not displace recent games from that window.

If every eligible file is in the recent window, the runner chooses the least
recently launched candidate instead. A one-game library still works. Files never
recorded and files outside the window have the same selection weight.

The window survives power cycles through the journal. Recency is launch order,
not hours or days: this firmware does not maintain a real date/time source.
The fixed timestamp visible on FAT files is not used for selection.

## View the statistics on a PC

Copy `.KFF2-history` from the card, then use Python 3 (no extra packages):

```sh
python tools/history_report.py .KFF2-history
python tools/history_report.py .KFF2-history --csv game-stats.csv
```

The CSV contains `path`, `launches`, `random_launches`, `manual_launches`,
`last_launch` and `last_source`. The reader verifies checksums and reports an
invalid/incomplete tail. It does not modify the journal. There is no on-cart
statistics screen or CSV import in G3.

Back up the journal like any other SD file. To reset the history, delete it with
the cartridge powered off. The next explicit launch creates a new journal.

## Storage and failure behaviour

The journal is append-only in normal use; it does not rewrite a complete CSV
on every launch. Records have a version, bounded length, sequence and CRC32.
A partial/corrupt final record is ignored. On the next append, the unverified tail
is truncated back to the last verified prefix. An unknown record version disables
writing rather than replacing an unrecognised format.

A history read/write failure does not deliberately block a prepared launch.
If history cannot be read, random selection falls back to its ordinary candidate
pool. This cannot compensate for an SD fault that also prevents loading the game.
CRC checks protect journal records, not the FAT filesystem or SD controller from
all consequences of a power interruption.

Only ten full recent paths are kept in a bounded RAM cache. Lifetime counts are
recovered from the journal when appending; logs grow over time, and very large
logs may add loading latency. Automatic compaction is not implemented.

## Verification

The host tests exercise actual journal code and the patched loader cases,
including write ordering, origin/count persistence, recent-window fallback,
failed loaders, automatic boots, mount-only operations, long paths, read/write
failures, torn/checksum-invalid tails and unknown versions.

A separate integration test uses the real upstream FatFs library on a RAM-backed
FAT32 disk. It checks creation, append, sync, unmount/remount, tail truncation and
read-only handling, then decodes the exported journal independently with the PC
tool. Host checks run with address and undefined-behaviour sanitizers.

The VICE harness continues to check the C64 menu and F4 protocol. It does not run
the STM32 or emulate physical SD hardware. **G3 still needs physical KFF2 testing.**
