# Shared appearance, introduced in G6

Introduced in G6 and retained in G7, this extends Home's existing artwork and font
to the rest of the menu interface.
No additional SD graphics files are needed.

| Screen | Presentation |
| --- | --- |
| Home | Existing four cards and patterned frame |
| SD folders, Games, Tools, Utilities, Favourites | Existing bitmap browser |
| Settings, including REU | Shared frame, cyan selected row |
| F3 cartridge utilities | Shared frame, cyan selected row |
| Shift+Return file options | Shared frame, scrollable twelve-row viewport |
| Help | Shared frame and keyboard/joystick controls |
| Search input and results | Shared frame, blinking bitmap caret |
| Cartridge messages, warnings and progress | Shared frame after graphics are available |
| Text reader | Shared frame, sixteen rows and bounded 32-column wrapping |
| Early startup diagnostics | Original text mode until graphics arrive |

Native options retain their original selection indexes and non-selectable text
rows. The original 23-entry menu protocol is unchanged. Long lists scroll locally
inside the same twelve-row viewport as the file browser. Different footers show
file-browser, menu, Help or reader controls.

Settings, file options and built-in cart utilities are still the original
functions. The Utilities card opens `/Utilities`; F3 opens the built-in functions.
REU configuration remains in Settings.

## Messages and reader

The existing conio terminal is retained for streamed cartridge text, cancellation
prompts and positional progress updates. G6 projects that terminal into the loaded
graphics bank. Projection reads C64 RAM only; it never requests assets, changes the
cartridge read pointer or consumes data from a pending transfer.

The first menu screen obtains the bank through G5's existing asset reply. It stays
available for subsequent messages. Before graphics are available, diagnostics use
native text. The cache is invalidated before the disk loader takes over memory.

The framed reader uses sixteen lines instead of twenty-three. Its stream is wrapped
at 32 characters, so even the widest nine-pixel glyphs fit the 288-pixel text area.
Page boundaries are recorded after wrapping. Forward/back and Home controls remain.
The page-table bound reserves room for the following page pointer.

Native warning colors are retained. Ordinary green terminal text becomes white in
the bitmap presentation. Header, border and chevrons retain Home's artwork.

## Verification

`tools/test_integrated_launcher.py` retains eight navigation/protocol scenarios,
keyboard-buffer input and NTSC startup capture.

`tools/test_uniform_ui.py` exercises the actual patched launcher functions in VICE:
Settings with REU text, utilities, options with non-selectable information, a
23-entry menu scrolled to entry 20, Help, search input, warning, positional progress,
reader first/next/back pages and startup fallback. It checks border pixels/colors,
font-bank integrity, selected rows and asset-request counts. The message and reader
steps must not issue any additional asset request. Reader forward/back banks must
match exactly. A full-width line of wide glyphs checks the wrap boundary.

These fixtures simulate cartridge replies and text bytes. They do not prove SD
loading, physical bus timing, USB or REU operation. The current G7 build needs real KFF2 testing; see [the checklist](testing.md). The
user's earlier G5 tests confirmed Home and folder-browser rendering on hardware.

The native image remains 16 KB, with 630 bytes free in the main allocation. The
update remains 128 KB, and the separate reserved 16 KB flash region stays blank.

Run both VICE checks after building the launcher and before firmware packaging:

```sh
python3 tools/test_integrated_launcher.py --vice /path/to/x64sc --rom-dir /path/to/C64
python3 tools/test_uniform_ui.py --vice /path/to/x64sc --rom-dir /path/to/C64
```

Firmware packaging requires both result files to match the native image hash.
