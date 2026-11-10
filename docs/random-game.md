# F4: Random game

From the graphical Home screen or file browser, press **F4**. The cart searches `/Games` and its
subdirectories, picks one eligible file and immediately starts it using existing
KFF2 loaders. No PC-generated index is required.

## Eligible files

- CRT cartridges, PRGs and P00 programs.
- Supported disk images recognised by KFF2's `FILE_D64` classification, including
  its supported DXX variants. The random action explicitly autostarts the image.
- T64 images, using the original first-entry loader.

The original file-type and size checks apply. Hidden/system files, directories,
text, firmware updates and raw `.rom` files are not launch candidates. A C128-only
CRT chosen on a C64 produces a message rather than bypassing the compatibility
warning. Unsupported or damaged content can still fail its normal loader checks.

PRGs retain the ordinary filesystem-mounted launch mode for auxiliary loads.
The chosen file's containing directory becomes the working directory.

## History-aware selection

Introduced in G3 and retained in G7, history records explicit launches in `/.KFF2-history`, including whether they came
from F4. Random selection avoids the last 10 distinct Games paths when possible,
falling back to the least recent when the pool is small. See
[launch history and CSV export](launch-history.md).

## What random means

The unit of selection is **a file**. Eligible files outside the recent window get equal selection
weight, irrespective of which subfolder contains them. Multiple versions of a
game, auxiliary PRGs and secondary disk images are separate candidates. This
version does not infer game titles or identify the first disk of a multi-disk set.
A one-file pool, or unavailable history, can still produce repeats.

A one-pass reservoir sampler avoids keeping an entire file list in memory.
The PRNG mixes the STM32's running cycle counter when F4 is pressed. It is
intended for casual game selection, not cryptographic randomness. Sampling uses
rejection before reduction to avoid ordinary modulo bias.

Scanning does not change the current directory or overwrite cartridge buffers.
All opened directory handles are closed, including error exits. The scan is
bounded to 16 nested subdirectory levels and the existing 750-byte directory
path limit. A read failure or excessive path/depth produces an error instead of
silently selecting from an incomplete scan. Large collections can take time to
scan; there is no dedicated scan-cancel key in this version.

Missing `/Games` and an empty eligible collection produce a message without
launching anything. Unsaved EasyFlash CRT changes get the original save prompt
before scanning or changing context; invoke F4 again after resolving that prompt.

## Retained menu corrections

Home's Browse, collection buttons, cart utilities and Random action unwind any
active D64/T64 image context, including an options menu over an image. Image
handles are closed and the automatic-reopen selection is cleared. Browse while
already in the SD browser retains its cached page and selection.

Home's F3 has a separate reply from the original browser's F3. It enters SD
context before calling the original utilities handler, so Settings/options no
longer make it silently do nothing. Normal browser shortcuts are retained.

## Tests and limits

`tools/test_home_features.py --upstream /path/to/KungFuFlash2` compiles the actual
scanner and Home handlers with a simulated filesystem and loader endpoints. It
uses the original hidden-file filtering function and original utilities handler.
It checks 10,000 selection seeds, all eligible launch routes, C128 handling,
empty/missing/error/depth/path cases, cleanup and image/options transitions.
Address and undefined-behaviour checks are enabled for the host test.

The VICE harness checks F4 sends its command and platform flag through the
native launcher. It deliberately stops before loading a game. Neither these
checks nor the firmware build verify physical KFF2 SD access or bus timing.
