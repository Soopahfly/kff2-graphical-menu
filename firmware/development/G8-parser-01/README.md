# G8-parser-01 development test

Built 17 November 2026. This is G7.03 plus the unsupported CRT bank rejection fix, an isolated first step toward G8. It is not the combined G8 release. Multi-disk swapping, GMod2 and the word-copy optimisation are not included.

## Download and identity

Use `KungFuFlash_v2.G7.03.1.upd` in this directory, or the accompanying ZIP. This development build retains G7's internal `2.G7` identifier and identical C64 launcher. The filename suffix distinguishes the test firmware without rebuilding or changing the menu. Select this exact update file when testing. Do not rely on the on-screen version to distinguish it from G7.03.

Update SHA-256: `fcfbe09127f1531b69f702b1031d435f5011823d19a2954803a96bc17edc2376`.

The existing G7.03 release, main branch and SD configuration layout are unchanged.

## Change

An unsupported mapped CRT bank previously left its data unread. That data could then be mistaken for another cartridge header. The loader now fails immediately, returning through the existing load-error path instead of accepting an incomplete cartridge. This does not add support for larger cartridges.

## Checks completed

- 219 parser cases, compiled from the actual patched loader with address and undefined-behaviour sanitizers. Includes supported bank boundaries, Magic Desk remapping, truncation and crafted header-shaped payloads, with the old loader as a negative control.
- Existing ARM-side Home/random, history, real FAT32, asset-transfer, Favourites, configuration and REU callback regression suites passed.
- Full ARM firmware compiled. ARM flash remains 77,620 / 98,304 bytes; BSS remains 25,976 bytes. C64 ROM space remains 627 bytes free.
- 128 KB update size, stack/reset vectors, blank 16 KB reserve and unchanged embedded launcher verified. Previous VICE results match the exact reused C64 launcher. VICE was not rerun for this ARM-only change and cannot emulate the cartridge's STM32.

No physical cartridge testing of this candidate has been performed.

## Hardware checks requested

1. Load a few known-working CRT games, including EasyFlash and Magic Desk if available. Confirm normal launch and return to the menu.
2. Try an image known to exceed supported banks. Expect the normal load-error path, rather than an incomplete game launching. A deliberately unsupported fixture can be prepared separately; no games are included here.
3. Confirm ordinary PRG/D64 selection and copying to Favourites still behave normally.

Record the exact update checksum and any failing CRT filename/type when reporting results. The published G7.03 update remains available as the comparison firmware.

## Rebuild

Prepare the normal G7.03 launcher and matching VICE reports as described in [building](../../../docs/building.md), then run:

```sh
python3 tools/build_firmware.py --upstream /path/to/KungFuFlash2 \
  --package-version 2.G7.03.1 --crt-parser-fix \
  --output-dir firmware/development/G8-parser-01
```

Add unpacked ARM toolchain options if required. The parser patch is applied after the existing G7 patches, and the regression test runs before compilation. Omitting `--crt-parser-fix` keeps the existing G7 build behavior. Development parser builds require a separate output directory and refuse the release/experimental package directories.
