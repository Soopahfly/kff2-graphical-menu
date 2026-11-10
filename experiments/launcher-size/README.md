> Current G2 firmware: 129 bytes free in the native main ROM.
> Earlier measurements below document the previous layouts. See [current build](https://github.com/Soopahfly/kff2-graphical-menu/tree/main/firmware/experimental).

# Original launcher size experiments

These optional patches are for upstream KFF2 commit
`9c84d999f4e2f5b2c7688cbc37a127069f5401b0`. They are not applied to the standalone
preview or incorporated into a flashable update. All current launcher features
are retained in these link experiments.

| Original launcher variant | ROM bytes used | ROM bytes free | Saving from baseline |
| --- | ---: | ---: | ---: |
| Unmodified | 13,130 | 1,206 | 0 |
| Fixed directory buffer | 12,325 | 2,011 | 805 |
| Bounded formatting helpers | 11,375 | 2,961 | 1,755 |
| Both changes | 10,570 | 3,766 | **2,560** |
| Both changes plus current graphical UI in the same ROM | 14,087 | **249** | UI included |

All figures include alignment and initialized DATA stored in ROM, using cc65
V2.19 Git `eebf54a`. The normal main-ROM allocation is 14,336 bytes. The complete
cartridge image remains 16,384 bytes with EAPI, startup and vectors.

## What changes

`bounded-formatting.patch` replaces general `sprintf`/`cprintf` use with:

- Direct `cputs` calls for constant strings and command names.
- An unpadded one/two-digit hexadecimal printer for byte-sized command values.
- A helper for the three known 40-column header layouts.

The bounded helper is only for these internal layouts: no prefix + 39 columns,
`" Search: "` + 30 columns, or one space + 38 columns, each followed by one
space and a terminator. It is not a general replacement for `sprintf`.

`static-directory.patch` replaces the single `malloc(sizeof(Directory))` with
one static directory object and removes the corresponding `free` and allocation
failure branch. The object is 963 bytes, replacing the existing allocation rather
than duplicating it. The general heap code is no longer linked.

`compact-launcher.patch` combines both changes. Apply one patch from the baseline,
not all three. Original copyright notices are retained; the added helper comment
marks this as an experimental altered version.

## Reproduce the link experiments

The investigation tool applies a patch only to its copied build inputs:

    python3 tools/investigate_rom.py --upstream /path/to/KungFuFlash2 \
        --launcher-patch experiments/launcher-size/compact-launcher.patch

Use either individual patch to reproduce its standalone saving. An unpacked
cc65 build can be selected with `--cc65-home /path/to/cc65`.

The tool now reports successful inline links as well as overflows. Results are
in [variant-measurements.json](variant-measurements.json) and
[combined-ui-measurements.json](combined-ui-measurements.json).

## Verification and limits

- Built the unmodified, each individual, and combined launcher variants.
- Applied the combined patch to fresh copied upstream inputs and linked it with
  the current UI in the original ROM layout. It fits, with 249 bytes spare.
- Confirmed malloc/free and general printf formatting are absent from that map.
- Compared the helper against the standard host formatter for 28,050 bounded
  string cases, including every non-zero byte value and all supported lengths.
- Checked all 256 hexadecimal results against `%x`, then compiled old/new C64
  versions and compared their two output pages in VICE: pixels match.
- Host checks used AddressSanitizer/UndefinedBehaviorSanitizer; leak detection
  was disabled because it cannot run under this environment's process tracing.

In the combined inline link, DATA and BSS occupy `$C000-$C53B`, below the
reserved C stack at `$C800-$CFFF`. This is a link check, not a runtime stack
watermark or real-hardware memory test.

The graphical UI is linked but still not called by the original launcher.
Dispatch, graphical directory rendering and transitions need implementing and
will consume some of the 249-byte margin. The new browser may replace old draw
routines, so some of that work can recover space as well as consume it.

The original main module's `updateScreen`, `showDir`, `updateDir`, `printDirPage`
and `printElement` functions total 413 code bytes in the unmodified build.
That is replacement opportunity, not another saving already achieved.

No firmware flashing, real KFF2 test, complete menu-protocol emulation or
integrated graphical boot is claimed. A one-bank integration now looks worth
trying; the separate payload design remains available if growth requires it.

The later [home integration](../home-integration/README.md) applies these
changes and connects the UI, with 217 bytes free in the main ROM allocation.
The figures in this document remain the earlier size-only experiments.
