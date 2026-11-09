> Current folder Home firmware: 66 bytes free in the native main ROM.
> Earlier measurements below document the previous layouts. See [current build](https://github.com/Soopahfly/kff2-graphical-menu/tree/main/firmware/experimental).

# UI size reduction

The menu looks the same while the linked UI payload is 821 bytes smaller.

| Measurement | Before | After | Saving |
| --- | ---: | ---: | ---: |
| UI code | 1,957 | 1,540 | 417 bytes |
| UI constants, font and artwork | 2,105 | 1,701 | 404 bytes |
| **UI payload** | **4,062** | **3,241** | **821 bytes / 20.2%** |
| Combined resident DATA and BSS | 596 | 452 | 144 bytes |
| Complete standalone preview PRG | 8,565 | 7,576 | 989 bytes |
| Resident launcher ROM free in split-layout experiment | 670 | 926 | 256 more bytes |
| Overflow when everything is linked into the stock ROM allocation | 3,227 | 2,311 | 916 bytes less |

The payload, resident image and standalone PRG are different linked programs.
Their size changes differ because of shared runtime helpers and alignment.
All numbers use cc65 V2.19 Git `eebf54a` and the same upstream KFF2 baseline.

## Changes

- Store the unchanged 704-byte kicking bitmap as a 275-byte count/value stream.
- Precompute the doubled title using the same EF3 glyphs. Its 576 bitmap bytes
  are represented by a 233-byte stream. The shared decoder writes both assets
  directly into VIC bitmap RAM.
- Remove the title's runtime scaling loop and its 144-byte temporary buffer.
- Replace the font's 512-byte pointer table with 256 low-offset bytes and 64
  packed high-offset bytes. Keep all 594 glyph-data bytes and all 256 mappings.
  The complete font data therefore changes from 1,106 to 914 bytes.
- Replace the text renderer's eight repeated pixel blocks with a loop.
- Remove the unused colour-fill helper and its C wrapper.

The artwork generator checks a lossless round trip for both streams. The font
generator checks every decoded offset. This does not remove unfamiliar
characters from the font or restrict it to the labels on the home screen.

## Verification

- Rebuilt the standalone PRG and reran the ROM investigation from fresh inputs.
- Compared before/after PAL home-screen images from VICE: no differing pixels.
- Rendered every non-NUL byte value (1 through 255) using both old and new
  renderers in VICE: no differing pixels across the glyph-grid screenshots.
  Mapping zero is retained and checked by the generator; strings terminate at
  zero, so it is not rendered by the string API.
- Exercised keyboard selection, wraparound, Return, B/S/Q shortcuts, sample
  browser, Utilities/Settings placeholders and exit to BASIC.
- Confirmed NTSC startup and inspected the resulting screenshots.

The compact font lookup and pixel loop execute more instructions per character
than the old table/unrolled loop. The precomputed title avoids its previous
scaling work. No real-hardware rendering-speed benchmark is claimed.
Joystick input and real KFF2 hardware remain untested.

## What this does not solve

The improved UI still does not fit alongside the existing launcher in the
stock ROM allocation. It remains 2,311 bytes over in the inline experiment.
A separate [resident-launcher experiment](../experiments/launcher-size/README.md)
now makes an inline link fit with 249 bytes spare. That optional patch does
not change the UI measurements above. Integration and hardware testing are
still pending, with the flash-to-RAM approach retained as an alternative.

The current [reproduction script](../tools/investigate_rom.py) writes the
updated [measurements](rom-space-measurements.json). Asset sources are
[make_kicker.py](../tools/make_kicker.py),
[make_font.py](../tools/make_font.py) and the retained EF3 `charset.sed`.

The [home integration](../experiments/home-integration/README.md) now adds the
menu dispatch, leaving 217 bytes free. A complete experimental MCU update has
been built; hardware compatibility is not yet verified.
