# Roadmap

Updated 11 November 2026. **G7.03 is the current experimental release package.** This roadmap
sets proposed priorities and acceptance checks, not release dates or a claim that
future features are implemented. G8/G9 are working milestone names.

**Not every feature on this roadmap will necessarily be implemented.** Progress
depends on the coding skills and development time available, the complexity of
each change, and the KFF2/C64's memory, timing and hardware limits. Features may
be simplified, deferred or dropped if they cannot be implemented and tested
reliably. Inclusion here is an idea for consideration, not a promise of delivery.

The project keeps its graphical interface and pinned official v2.07-based source.
Community changes will be reviewed and ported individually, with attribution.

## At a glance

| Order | Milestone | Scope | Status |
| --- | --- | --- | --- |
| 1 | G7.03 experimental release package | Package working copy-screen fix; continue Favourites and REU hardware coverage | Published as an experimental pre-release; remaining hardware checks recorded |
| 2 | G8 everyday-use improvements | D64 disk swapping and optional Random preview | Upstream ideas/code reviewed; not integrated |
| 3 | G9 GMod2 | Native cartridge loading and EEPROM save persistence | Community implementation identified; not integrated |
| 4 | Larger cartridges | Magic Desk 16 images up to 2 MB | Separate banking/timing investigation |
| 5 | REU images | Load/save `.reu` files and optional autoload | Community implementation identified; configuration/memory design needed |
| Backlog | Library and file tools | Recent games, statistics, move/rename, browser sorting preferences | Not scheduled |
| Research | Broader compatibility | exFAT, KERNAL/freezer extensions and selected CRT+REU combinations | Not scheduled; separate feasibility work |

G8's two features should be developed and tested independently. If one is not
ready, it should not delay a usable release of the other or be bundled untested.
Later milestone order can change with tester results, measured space and demand.

## 1. Finish G7 and publish the tested build

**Already user-reported working on real hardware:** PRG/CRT loading, saving
REU-size/autoboot preferences and return to Home after reset with autoboot disabled.
The [hardware log](firmware/experimental/HARDWARE-TESTS.md) records the scope.

### Remaining release checks

- Copy a file to Favourites, load the copy and confirm the original remains.
- Copy a whole game folder and verify companion files/additional disks work.
- Repeat a copy and try an existing destination name; verify no overwrite.
- Use REU software to detect and exercise 256 KB, 512 KB and 1 MB. Saving the
  preference is already reported working, but is not an REU transfer test.

### Release package

Once those pass, prepare a **GitHub experimental/pre-release** tied to the exact
tested source and firmware: `.upd`, SHA-256 checksum, release notes, installation,
rollback/recovery instructions and confirmed hardware results. If fixes change
the candidate, identify the new checksum and repeat affected tests before tagging.

Broader USB, C128, PAL/NTSC/board coverage and CRT readability remain explicit
testing requests. They are not silently promoted to confirmed compatibility.
See [the current checklist](docs/testing.md).

## 2. G8: disk swapping and optional Random preview

See the [G8 scope and implementation plan](docs/g8-scope.md) for proposed controls,
disk-list format, configuration compatibility, work breakdown and release checks.

### D64 disk swapping with the Special button

**Benefit:** change disks in a multi-disk game without returning to the launcher.

Start with explicit disk-set lists and D64 images. Use Special only in the
appropriate disk-emulation context, preserving its existing freezer/cartridge role.
Support for D71/D81 swapping should follow explicit tests, not be assumed from
their normal loading support. The list format and user controls need documenting
before a test build is published.

The community implementation is a starting point, not a drop-in merge. In the
inspected code, the previous image is closed before the replacement is opened;
error handling needs strengthening for missing, unreadable or invalid next images.

**Acceptance checks:**

- Advance through a set, wrap to its first disk, and use the documented reset-to-first action.
- Keep the currently mounted disk usable if the replacement cannot be validated/opened.
- Flush pending disk writes safely before a successful swap; preserve read-only images.
- Debounce presses and handle held buttons without uncontrolled repeated swaps.
- Test real multi-disk games, reset behaviour and Special in non-disk cartridge modes.
- Preserve G7 menus, Favourites, history and REU behaviour.

Source candidate: [r107sl enhanced branch](https://codeberg.org/r107sl/KungFuFlash2/src/branch/enhanced).

### Optional Random preview

**Benefit:** see the selected game before committing to launch it.

Add a setting to choose **Launch immediately** or **Preview selection**. Preserve
the current immediate-launch behaviour as the default. In preview mode, F4 selects
and highlights a candidate in its containing folder; Return launches it and F4
picks again. Reuse the existing Games scope and recent-game rules.

**Acceptance checks:**

- Preview never starts a loader or increments launch/history counts.
- The correct folder, page and row are visible, including deep subfolders and long names.
- Missing/moved files and empty collections produce a useful result without an unintended launch.
- Search/image context and unsaved EasyFlash prompts remain correct.
- Existing immediate-launch mode and history behaviour pass their regressions.

Related request: [Random game #44](https://codeberg.org/KimJorgensen/KungFuFlash2/issues/44).

## 3. G9: native GMod2 and EEPROM saves

**Benefit:** support native GMod2 editions of games and their EEPROM save data.
Some games already have usable EasyFlash editions; this expands format support
rather than making every such title newly playable.

Port GMod2 separately from larger-cartridge caching wherever practical. Review
the current source, including EEPROM CHIP packets, rather than copying the first
patch offered in the discussion.

**Acceptance checks:**

- Match cartridge banking and EEPROM protocol behaviour against reference tests/VICE.
- Handle empty/default EEPROM, existing save data and supported image layouts correctly.
- Verify saves across Menu, reset and power cycles, with documented save timing.
- Handle read-only media, full cards and malformed save files without overwriting the CRT.
- Test representative GMod2 releases on hardware and regress existing cartridge modes.

Source discussion: [Magic Desk/GMod2 #54](https://codeberg.org/KimJorgensen/KungFuFlash2/issues/54).

## 4. Larger cartridges: Magic Desk 16 up to 2 MB

**Benefit:** support larger cartridge releases, including suitable AGI-64 images.

KFF2 has a 1 MB cartridge buffer. Supporting a 2 MB image requires bank caching,
packing or another deliberate storage strategy; changing a size check is not enough.
Review the newer DMA handover fixes and the choice between simpler SD caching
and more complex compressed caching. Keep any profile writes optional or justified.

**Acceptance checks:** strict image validation, repeatable bank sweeps, safe
cache misses/DMA release, defined SD-error behaviour, and hardware tests of rapid
bank switching and raster/audio-sensitive cases. Do not assume C128/VIC modes
can service foreground cache misses. Recheck all existing cartridge paths.

The initial target is **2 MB**, not a promise of 4 MB support. This stays a separate
milestone so caching/timing faults can be isolated from GMod2 and menu changes.

Sources: [type-85 proposal #55](https://codeberg.org/KimJorgensen/KungFuFlash2/issues/55)
and [the related implementation discussion #54](https://codeberg.org/KimJorgensen/KungFuFlash2/issues/54).

## 5. REU image loading, saving and optional autoload

**Benefit:** restore prepared REU contents for GEOS and other REU-aware software,
and save a memory image for later use.

Decide image-size rules for G7's three selected capacities, buffer ownership,
when a save is allowed and how the loaded image is shown. Preserve the original
configuration layout or provide an explicit, tested migration/rollback scheme.
The reviewed community branch changes configuration fields and RAM layout, so a
wholesale merge would conflict with our current compatibility guarantees.

**Acceptance checks:** load/save/remount round trips; mismatched/invalid sizes;
read-only/full-card failures; persistence and opt-in autoload; protection against
unintentionally saving over an image; and physical REU software tests at each size.
Do not imply this enables REU alongside an active CRT.

Source discussion: [REU/KERNAL enhancements #47](https://codeberg.org/KimJorgensen/KungFuFlash2/issues/47).

## Backlog: library and file tools

| Feature | Intended behaviour / condition |
| --- | --- |
| Recent games | Use existing launch history, skip missing entries and launch through normal loaders |
| On-cart statistics | Show manual/random counts and recency without interpreting counts as play time |
| Move and rename | Extend file management with collision checks and a clear whole-game-folder workflow |
| Browser sorting preferences | Consider in-memory sorted views; distinguish these from existing F3 FAT-directory sorting |
| Better long-name handling | Preserve CRT readability and selection visibility without shrinking the font |

These need an entry-point/UI design and space measurements before receiving a
release target. Keep the existing four Home tiles and consistent frame unless
a revised design is reviewed separately.

## Research, not committed features

- **exFAT:** audit FatFs configuration, directory sorting and wider file-size types;
  test alongside FAT32. It is not a single-switch change.
- **KERNAL emulation / Magic Formel / diagnostic cartridge extensions:** evaluate
  board, PLA, video-standard and timing differences in separate builds.
- **Selected CRT+REU combinations:** review shared memory and I/O decoding per
  cartridge type. G7's REU selector does not provide this capability.
- **USB-to-REU loading:** consider after image handling and memory ownership are settled.

## Rules for each milestone

1. Keep a tested baseline and change one subsystem at a time. Port reviewed,
   attributable code rather than replacing the entire firmware/menu.
2. Measure C64 ROM, ARM flash, RAM and stack requirements. G7 has **630 C64 ROM
   bytes** and **20,684 bytes in the existing ARM flash allocation** available;
   that is not a guarantee that every proposed feature fits.
3. Reuse ARM-side options/screens where possible. Preserve the update layout and
   blank flash gap unless a separate layout change is designed and checked.
4. Run affected host/FatFs tests and existing VICE regressions. Test compatibility
   with the original configuration, history, Favourites, loaders, USB and REU as relevant.
5. Publish a distinct candidate/checksum and ask for targeted hardware results.
   Record tested setups and remaining limits; simulated tests do not establish bus timing.

After G9, choose identifiers that fit the existing firmware version field, such
as `2.H0`. A label like `2.G10` needs a version-field change and is not assumed here.
