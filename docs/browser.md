# Patterned bitmap browser, introduced in G5

![Working G5 browser in VICE](../preview/integration-browser.png)

The screenshot entries are simulated; the firmware reads the real SD card.
This is the integrated bitmap renderer, not the earlier static concept PRG.

## Presentation

- Home's exact patterned border, masthead and chevrons.
- Existing licensed EF3 / Home proportional font in native 320x200 hi-res mode.
- White filenames, cyan folders and a full cyan selection bar with black text.
- Twelve visible entries, file icons and right-aligned SD extension labels.
- Selected filename/type in the details band; Help and options hints below.
- Controls remain inside the same frame and bands as Home.

SD entries retain their 33-character bounded name plus type/size packet. Visible
text is clipped by pixel width, so long names can still be truncated. Disk/tape
rows use their entire original 38-character field, preserving flags such as
*PRG<. The example play counts and total-file index in the static concept are
not shown. G3's journal and PC report are unchanged.

The 23-entry transfer-page protocol remains. A twelve-row local viewport shows
all entries as you scroll. Cursor left/right still page; DEL or fire-left goes
up. F2 returns Home, F4 uses the existing /Games random runner. G6 extends this frame to Settings,
options, Help, search input, warnings and the text reader. See
[the shared appearance notes](uniform-ui.md). Early startup diagnostics retain
native text until graphics are available.
No on-disk graphics pack or new configuration file is required.

## Graphics and memory

The new REPLY_HOME_ASSETS ($9c) asks the ARM menu handler to place a 16384-byte
bank in the existing 64 KB KFF transfer buffer, then publish CMD_NONE. The C64
copies it to $4000-$7fff. A non-CMD_NONE response, including USB's CMD_WAIT_SYNC,
is propagated back to the native command loop without reading asset data.

The bank holds the original Home artwork, hints and palettes. Previously unused
space holds the licensed glyph data at $5500, low pointers at $5900, packed high
pointers at $5a00 and widths at $5a40-$5b3f. The screen matrix remains $5c00 and
the bitmap $6000. Navigation redraws rows locally; assets reload when entering
graphics from text mode. Home selection and its artwork are unchanged.

This removes the compressed Home asset payload from the scarce C64 ROM. The
G5 launcher occupied 16 KB, with 1,440 bytes spare in its main allocation.
The current G7 launcher is also 16 KB, with 630 bytes spare. ARM read-only data
grows by 16 KB; upstream mirrors that section
into DTCM RAM as well as storing it in flash. The build report records the final
ARM flash use and BSS end. No REU buffer is repurposed, and the separate spare
16 KB flash region remains blank.

## Verification and limits

VICE PAL scenarios cover folders, options, Home returns, paging beyond both
viewport and packet boundaries, F4, full locked/unclosed disk flags and an
interrupted asset request. Screen-bank checks compare every border cell with
Home, check exact glyph output for type/flag fields and confirm font tables
remain intact. Home's full bank is also compared with the generated asset bank.
Keyboard navigation and NTSC startup are checked separately.

The ARM asset handler is host-tested with upstream buffer-pointer semantics and
sanitizers. Existing loader-route, random, journal and real FatFs tests are run
before firmware packaging. Package checks preserve the 128 KB update layout,
16 KB C64 image, original reserved regions and reset vectors.

G5 Home and SD-browser rendering were confirmed on a physical KFF2 with an LCD.
G7, full loading/bus compatibility and CRT readability remain unverified. The PRG
harness substitutes an ARM response, not the complete
KFF2 hardware. See the [current hardware checks](testing.md) and
[recovery guide](../firmware/experimental/RECOVERY.md).
