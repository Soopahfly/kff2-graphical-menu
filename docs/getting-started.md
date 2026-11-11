# Getting started with G7.03

G7 is experimental firmware for **Kung Fu Flash 2**. It is based on official
v2.07 plus documentation commit `9c84d99`. It is not firmware for the original KFF.
G7 has passed software checks and has limited positive hardware reports for
PRG/CRT loading, saving preferences and reset with autoboot disabled. Favourites
copying and actual REU operation still need verification. See [test status](testing.md).

G7.03 clears the stale copy-result display so one keypress visibly returns Home. The internal version still
shows `2.G7`, so use `KungFuFlash_v2.G7.03.upd` and verify [SHA256SUMS](../firmware/releases/G7.03/SHA256SUMS).
G7.03 contains the exact G7.0.3 firmware bytes. The owner reports the fix working;
the test environment was not specified. Broader hardware checks remain open.

## Install

1. Back up the SD card, especially `.KFF2.cfg` and `.KFF2-history` if present.
2. Keep your previous working firmware or an official KFF2 update available.
   Read [the recovery methods](../firmware/experimental/RECOVERY.md).
3. Download [KungFuFlash_v2.G7.03.upd](https://github.com/Soopahfly/kff2-graphical-menu/releases/download/G7.03/KungFuFlash_v2.G7.03.upd)
   and copy it to a **FAT32** SD card. exFAT is not supported.
4. Select the update in the working KFF2 file browser and confirm the update.
   Keep power connected until programming finishes.
5. Check that Settings contains **REU size** and **Autoboot last selection**,
   and SD file/folder options contain **Copy to Favourites**.

No separate menu PRG, graphics pack or fonts are required on the SD card.
The `.prg` files in this repository are development previews, not installation files.

## SD folders

Create these ordinary folders at the root of the card:

| Folder | Home shortcut | Contents |
| --- | --- | --- |
| `/Games` | Games | Programs, cartridges and disk/tape images |
| `/Tools` | Tools | Editors, diagnostics and other tools |
| `/Utilities` | Utilities | Your own utility collection |
| `/Favourites` | Favourites | Selected files and game folders |

Names are case-insensitive. Missing folders show a message and fall back to SD
root after OK. G7 can create `/Favourites` when copying your first favourite.
The folders are shortcuts, not restrictions on which file types can run there.

Other folders such as `/Demos`, `/Homebrew` and `/Firmware` are optional and can be
opened using Browse SD. There is no dedicated Homebrew tile. Put homebrew under
`/Games/Homebrew` if you want F4 Random to include it; keep it outside Games if not.
You can keep update files in any folder accessible through Browse SD.

Keep each multi-disk or multi-file game in its own subfolder. Copying one `.d64`
does not gather its other disks. Crunched PRGs unpack themselves on the C64.

## Move around

Use cursor keys and Return, or a joystick in **port 2** and Fire.

| Context | Control | Result |
| --- | --- | --- |
| Home | G / T / U / F | Open the corresponding folder |
| Home | B | Browse SD, retaining the cached browser context when available |
| Home | S | Settings |
| Home | Q | BASIC |
| Browser | DEL / Fire+left | Go up |
| Browser | F2 | Return Home |
| Browser | F5 | Settings |
| Browser | Shift+Return / held Fire | Options for the selected entry |
| Browser | A–Z | Enter search |
| Browser | F1 | Help |
| Home or browser | F3 | Built-in cartridge utilities |
| Home or browser | F4 | Immediately launch a random eligible file from Games |

The **Utilities tile** opens `/Utilities`. **F3** opens built-in functions such as
directory sorting. These are different destinations.

## Favourites

In the SD browser, highlight a game file or its folder. Press **Shift+Return**
(or hold Fire), then select **Copy to Favourites**.

Originals remain in place. Existing destination names are never overwritten.
For a game with companion files or several disks, select its entire folder.
Favourites are copies, not bookmarks, and use additional SD space.
Later changes to the original do not update its Favourite copy. Launch history
also treats their different paths separately.
See [copy limits, duplicate handling and interrupted copies](g7-features.md).

## REU and startup

Open Settings with **S on Home** or **F5 in the browser**.

| Setting | Use |
| --- | --- |
| RAM expansion (REU) | Enable or disable REU emulation |
| REU size | Cycle through 1 MB, 512 KB and 256 KB |
| Autoboot last selection | Choose no to start at Home instead of the saved selection |
| Autostart disk image | Existing behaviour when manually opening a disk image |

Select **Save** to store changes. Cancel leaves the stored values unchanged.
Existing cards default to **1 MB** and **autoboot enabled**; the screenshot in the
README shows example settings, not installation defaults.

REU emulation is available in the existing program/disk/BASIC modes. G7 does not
combine REU with CRT emulation or add `.reu` image loading/saving.

## Sorting and random selection

To sort a folder, open it, press **F3** and choose **Sort directory**. This writes
the current folder's FAT directory order, with directories first and names sorted.
It is not automatic or recursive. Keep power connected while sorting.

F4 scans `/Games` and its subfolders and launches immediately. It avoids the last
ten distinct Games paths when alternatives exist. Different versions, helper PRGs
and secondary disks are separate candidates. There is no preview-before-launch
mode in G7. See [Random rules](random-game.md).

## First hardware checks

Start with [the G7 test checklist](testing.md). A successful update or readable
menu does not prove game loading, REU timing or all cartridge formats work.
Use a small file/folder for the first Favourites copy, then check it on the card.
