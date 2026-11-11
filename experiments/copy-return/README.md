# Copy-result return test in VICE

These PRGs run on an ordinary emulated C64. They exercise the project's actual
C64 outer command dispatcher, warning, keyboard wait, Home and file browser.
A small stand-in supplies cartridge replies and sample directory entries.
They do not access an SD card, copy files, flash firmware or emulate the KFF2 ARM.
No C64 ROMs or games are included.

## Try it

1. In VICE x64sc, choose **File > Autostart disk/tape image**, then select a PRG below.
2. The test automatically displays **Added to /Favourites. Original kept.**
3. Press and release **Return once**. Compare what appears.
4. B opens a sample file browser; F2 returns Home. Q ends the fixed test.
   Reset VICE to repeat. Cursor keys and joystick 2 work on Home.

| PRG | Expected after one Return |
| --- | --- |
| [g7.0.2-reproduce.prg](g7.0.2-reproduce.prg) | Old result screen remains over an active Home menu. A second Return selects Games. |
| [g7.0.3-fixed.prg](g7.0.3-fixed.prg) | Home is visibly restored. No second acknowledgement is required. |

The success message is simulated. The PRGs are emulator tests, not cartridge updates.
The older reproduction PRG stops when Q is selected; reset VICE to repeat it.

## Cause and correction

The status renderer kept a `native_view` flag after leaving the warning screen.
Home's existing `waitRelease()` called `browser_capture()`, which used that stale
flag to draw the previous text over the freshly restored Home image. Input was
already being handled by Home. Clearing the status flag in `browser_leave()`
prevents the redraw. Existing message/reader entry points explicitly set it when
needed. The SD copier and ARM-side return-to-Home handshake are unchanged.

## Automated evidence

`tools/test_copy_return.py` runs the real outer dispatcher, injects **one** Return
into the C64 keyboard buffer at the warning prompt, then saves the complete VIC
bank and a screenshot before Home handles another key. It compares that bank with
the original Home assets, then exercises B, F2 and Q. It also checks the two sync
waits, command completion and exact launcher/interactive-PRG hashes.

The original G7.0.2 code reproduced the stale display in VICE. The corrected code
must restore the exact Home pixels after one key and after returning from Browse.
This validates the C64-side display/input transition. Physical SD, flash timing,
bus timing and complete real-hardware copying still require cartridge testing.

After building with `tools/build_integrated_launcher.py`, run:

```sh
python3 tools/test_copy_return.py --vice /path/to/x64sc --rom-dir /path/to/C64
```

For a pre-fix build, use `--expect-stale-screen` to confirm the old fault.
