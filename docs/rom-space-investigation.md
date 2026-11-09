# ROM space investigation

The graphical UI fits if it is stored separately and copied into C64 RAM.
The current KFF2 update image contains a deliberately blank 16 KB region that
can hold that payload. This is a proposed firmware change, not an existing
feature or a flashable build.

Measurements below use KFF2 commit `9c84d999f4e2f5b2c7688cbc37a127069f5401b0`,
EF3 bootimage commit `bf89562`, and cc65 V2.19 Git `eebf54a`.

## What the limits actually are

There are three separate things to account for:

1. The 128 KB firmware update stored in the STM32's flash.
2. The 16 KB cartridge ROM window presented to the C64.
3. The C64's own RAM, where a menu can execute and draw graphics.

Unused STM32 flash is not automatically visible through the cartridge window.
Copying code to C64 RAM does not, by itself, create more flash storage either.
Both storage and delivery have to be designed together.

## The blank 16 KB

The ARM linker permits firmware in the first 96 KB. The update Makefile pads
that area, explicitly appends 16,384 bytes of `0xFF`, then appends the 16 KB
launcher. The loader and updater use the launcher/version at the 112 KB offset.

| STM32 flash addresses | Update offset | Size | Current contents |
| --- | --- | ---: | --- |
| `$08000000-$08017FFF` | 0 KB | 96 KB | ARM firmware allocation, including any padding |
| `$08018000-$0801BFFF` | 96 KB | 16 KB | Explicit blank padding |
| `$0801C000-$0801FFFF` | 112 KB | 16 KB | C64 launcher |

No purpose for the gap is documented in the inspected code or relevant commit
messages. The same padding exists in the initial KFF2 commit. Calling it spare
capacity is supported by the build layout; claiming a particular original
reason for reserving it would be speculation.

The updater programs all sixteen 8 KB sectors, including this padding. It is
not an independent configuration partition that the updater preserves.

## Current launcher usage

The resident launcher does not have the entire 16 KB available for ordinary
code and strings. `$8000-$B7FF` is its main 14 KB allocation. The remaining
physical 2 KB contains EasyFlash API data, Ultimax startup code and vectors.
Some of that reserved space is unused, but reclaiming it requires a careful
alias/layout audit and would not provide the same room as the blank flash area.

An important detail: initialized DATA runs at `$C000`, but its initial bytes
are stored in ROM. Counting only the RODATA end overstates the remaining room.

| Link experiment | Result |
| --- | ---: |
| Original launcher main ROM allocation | 14,336 bytes |
| Original launcher used, including padding and DATA initializers | 13,130 bytes |
| Original launcher free | **1,206 bytes** |
| Original launcher plus current UI, all in ROM | 17,563 bytes required |
| Actual excess, including DATA initializers | **3,227 bytes** |
| Original launcher plus UI linked to separate C64 RAM payload | **Links successfully** |
| Separate UI code, text renderer, font and artwork | **4,062 bytes** |
| Payload allocation in the proposed flash/RAM layout | 16,384 bytes |
| Remaining payload capacity before new headers or browser code | **12,322 bytes** |
| Resident ROM remaining in this experiment | **670 bytes** |

The first failing linker diagnostic reports a RODATA overflow of 3,058 bytes.
That excludes the later DATA initializers. A second, explicitly sizing-only
link measures the complete 3,227-byte excess. Its relaxed address layout is
not executable firmware and must not be treated as a fix.

The successful experiment places UI code at `$1000-$17A4` and UI constants at
`$17A5-$1FDD`. It leaves the existing launcher, disk routines and USB loading
support in cartridge ROM. It does not yet transfer the payload or call its UI.

## How EasyFlash 3 manages it

EasyFlash 3 uses bank switching: selecting a flash bank makes a different part
of cartridge storage appear in the same CPU address window. Its system image
places the menu in bank `$08`, EasyProg in other banks, and the directory and
cartridge/KERNAL data elsewhere.

The menu itself still fits into a single 16 KB image. Its linker assigns CODE,
RODATA and DATA a load address in ROM and execution/storage addresses in C64
RAM. Startup copies those segments into RAM. The video setup then copies the
8,000-byte bitmap and 1,000-byte colour matrix into VIC-visible RAM.

A build of the inspected EF3 menu gives:

| Component | EF3 menu | KFF2 baseline launcher |
| --- | ---: | ---: |
| Linked CODE segment | 4,286 bytes | 11,406 bytes |
| Linked RODATA segment | 10,216 bytes | 1,209 bytes |
| Initialized DATA | 983 bytes | 145 bytes |
| Complete cartridge image | 16,384 bytes | 16,384 bytes |

These are different programs, not equivalent feature sets. EF3 is primarily a
mode/slot chooser; KFF2's C64 launcher includes a directory UI and persistent
disk/USB loading support. EF3 leaves more of its bank for graphics because its
menu code is much smaller. Its copied bitmap accounts for 9,000 bytes of the
RODATA total.

Running from RAM also lets EF3 continue its menu logic while changing flash
banks. KFF2's current launcher read handler simply reads `crt_ptr[addr &
0x3fff]`, so that mode has no equivalent general-purpose menu bank selector.
EasyFlash game emulation and the native launcher are separate modes.

## Recommended approach

Store a UI payload in the existing blank 16 KB region, keeping the launcher at
its existing offset. Deliver the payload through KFF2's existing buffered data
interface and load it into C64 RAM before opening the graphical menu.

The shared data buffer is 64 KB, so the current roughly 4 KB payload fits.
This approach does not require adding work to each timing-sensitive cartridge
ROM read. It also need not change the 128 KB update length or the version
string's offset. It does require matching changes on the ARM and C64 sides.

Implementation still needs:

1. A separately linked UI payload in the update build, with length/version
   validation and a bounded destination range. Any header uses part of the
   same 16 KB capacity.
2. An explicitly numbered command for transferring it before normal menu
   traffic. Existing command numbers must not shift.
3. A small resident receiver and dispatch bridge. The measured 670 bytes
   remaining are before this code is added.
4. Graphics-aware drawing for the file list, search and progress display,
   plus display restoration for existing dialogs, text reader and loaders.
5. Reset/re-entry and hardware tests, including direct PRG/USB boot paths.

The existing disk/USB loading code must remain resident: user programs can
load over the menu's low-RAM area after it exits. Its callbacks must not retain
pointers to temporary UI code or data.

The current ROM launcher also has a small upper-RAM working area. In the
RAM-payload link, DATA plus BSS occupies 596 bytes at `$C000`, leaving about
1.4 KB for heap before the reserved 2 KB C stack. The existing directory
structure already consumes 963 bytes before allocator overhead. New UI buffers
should use explicitly reserved low RAM or reuse the existing directory data,
not add large allocations to that heap.

## Other options

| Option | Trade-off |
| --- | --- |
| Blank flash region plus transfer to RAM | Recommended. Measured capacity, no new dependency on an SD menu file; requires coordinated firmware changes. |
| New bank switching in native launcher mode | Feasible alternative, but requires boot copying/trampolines and an audit of both native and EF3-compatible launch paths. |
| Load UI from the SD card | Can avoid embedded asset storage, but adds an external file dependency and recovery behaviour. |
| Compress the existing single-bank image | Compression does not save ROM unless the output is unpacked somewhere; resident disk callbacks complicate that design. |
| Trim features or shrink font/artwork | May reclaim space, but would trade away functionality or appearance and leaves less room for the browser. |

## Reproduce

With cc65 and make installed, and local checkouts of both upstream projects:

    python3 tools/investigate_rom.py --upstream /path/to/KungFuFlash2 \
        --easyflash-upstream /path/to/easyflash3-bootimage

For an unpacked cc65 source/build tree, also pass `--cc65-home /path/to/cc65`.
The script copies the build inputs into ignored `launcher/build/rom-investigation/`
and does not edit upstream source files. It writes link maps, diagnostics and
`measurements.json`. The checked-in results are in
[rom-space-measurements.json](rom-space-measurements.json).

Verified: fresh baseline build, expected inline overflow, successful split
link, output lengths, payload address bounds, and the EF3 menu build.
Not verified: ARM firmware changes, actual flash-to-RAM transfer, integrated
menu boot in VICE, or operation on real KFF2 hardware. No update is supplied.

## Source locations

- KFF2 `firmware/Makefile` update rule; ARM linker `FLASH` allocation;
  `firmware/cartridges/cartridge.h` launcher address; `firmware/file_types.h`
  update size/version offset; `firmware/loader.c` update programming.
- KFF2 `launcher/ld.crt.cfg`; `launcher/disk.s` and `ef3usb_loader.s`;
  `firmware/commands.c`, `firmware/cartridges/kff.c`, `firmware/memory.h`.
- EF3 `efmenu/src/ld.cfg`, `crt0.s`, `efmenu.c`, `memcfg.h`, and the
  root bootimage `Makefile` bank layout.

Upstream repositories: [KFF2](https://codeberg.org/KimJorgensen/KungFuFlash2)
and [EF3 bootimage](https://github.com/easyflash-mirror/easyflash3-bootimage).
