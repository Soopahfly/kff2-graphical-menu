# Historical Folder Home design preview

> This is the original static prototype. The design is now integrated in G7.
> Use [the current firmware guide](../../firmware/experimental/README.md) for installation.

A proposed replacement for the large high-kick figure and vertical button list.
Four folder panels fill the main area, with the existing system actions below.

The revised design takes cues from EasyFlash 3's colourful framing and shaded
menu panels: a purple geometric surround, cyan selection edges, bevelled black
panels, coloured gamepad/wrench/disk/star icons, and a small spectrum accent.
The paths appear only in the context line. The surround and icons are new
artwork drawn for this project, not EasyFlash's original background bitmap.

![Folder Home, Games selected](../../preview/folder-home-games.png)

This image is a pixel layout render of the exact C64 bitmap and colour matrix
used by the PRG. It is not a VICE screenshot. F4 now selects a random game in the integrated firmware. The revised design is now integrated in the [current G7 firmware](../../firmware/experimental/README.md).

## Intended folder mapping

| Tile | SD card directory | Intended contents |
|---|---|---|
| Games | `/Games/` | PRGs, cartridge images and disk images |
| Tools | `/Tools/` | Editors, diagnostics and other programs |
| Utilities | `/Utilities/` | Your own utility collection |
| Favourites | `/Favourites/` | A collection you organise yourself |

The firmware shortcuts open these ordinary directories. Tools and Utilities are
separate collections for the user to organise, with no file-type restrictions.
In this prototype Favourites means manually placed copies. Current G7 also
offers Copy to Favourites for files and whole game folders; it remains an ordinary
folder, not a shortcut database or automatic list. Keep each multi-disk game together in its own subdirectory.

Built-in cartridge utilities stay separate, labelled **Cart utilities** on F3.
Browse SD (B), Settings (S) and BASIC (Q) remain visible at the bottom.
The firmware shows a missing-folder message and opens the SD root after OK.

## Try the design

Load [kff2-folder-home-preview.prg](../../preview/kff2-folder-home-preview.prg)
in VICE as an ordinary C64 PRG. This is a separately compiled design prototype.
The four folder buttons and system buttons show confirmation screens, without
reading an SD card or loading programs. Q returns to BASIC.

- Cursor left/right switches column; up/down switches row.
- Joystick port 2 uses the same navigation. Return or fire opens the selection.
- G, T, U and F open their corresponding tile confirmation screens.
- B, S and F3 preview the other actions; Q exits.

## Build and verification

Requires cc65, make, Python 3 and Pillow for PNG export:

```sh
python3 tools/design_folder_home.py
make -C experiments/folder-home check
```

The generator reads the existing EF3 proportional font, approved title and
`design.json`. It produces the C64 bitmap streams, matrix, four descriptions
and all four PNG previews. Every RLE stream is checked against its original
bytes. Coordinates are checked against the 320x200 bitmap bounds.

The PRG compiles with cc65 2.19. Its load address, BASIC SYS entry, linked memory
range and decompressed stream lengths are checked. This separate PRG has not been run in VICE. The integrated native-menu harness
has now been tested in VICE, including byte-exact graphics verification. Keyboard and joystick handlers
are included, but their operation is not yet verified in an emulator.

The bitmap lives at `$6000-$7f3f`, its matrix at `$5c00-$5fe7`. Program, assets
and C stack remain below `$4000`. Original video-register values are restored
on leaving the graphical screen.

This prototype uses a complete compressed static bitmap so the PNGs and PRG
share the exact layout. Its asset size is recorded in `measurements.json`.
That is **not a native firmware ROM-fit measurement**. The native launcher uses a separate LZ4-packed version of the same pixels and
had 129 bytes spare at the G3 milestone. Current G7 has 630 bytes spare and uses
an ARM-supplied graphics/font bank. G5 Home/browser display has been checked on
hardware; the current G7 features and other hardware paths remain unverified.

Font: Thomas Giesel / EasyFlash 3. Existing copyright and licence remain in
`launcher/ui/charset.sed` and `launcher/ui/EF3-LICENSE.md`.
