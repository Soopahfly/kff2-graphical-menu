# Community change assessment

Assessed 12 November 2026 against G7.03. These are isolated experiments and candidate patches, not a new firmware release. Main and the published G7.03 image are unchanged.

| Candidate | Recommendation | Evidence |
| --- | --- | --- |
| CRT loader handling of unsupported banks | Take a small fail-fast adaptation into G8 | Reproduced payload/header confusion; 219 parser cases pass; no ARM flash or BSS increase |
| Aligned word-copy optimisation | Retain as a G8 candidate, measure on hardware before enabling | 131,720 correctness cases pass; full ARM image grows 44 bytes; real STM32 speed remains unmeasured |
| PRG autostart preference | Defer | Controls startup policy, not manual load-without-RUN; overlaps our autoboot setting; donor configuration layout is incompatible |

## CRT parser

The current loader continues after an unsupported mapped bank without consuming its payload. The next iteration can read that data as a CHIP header. A crafted test reproduced acceptance of a false header and replacement of an earlier bank.

The donor's payload-skip approach restores alignment. Imported alone into our firmware, however, it can still accept an incomplete cartridge. Our proposed `crt-reject-unsupported.patch` returns failure immediately instead. This does not add support for larger cartridges.

The harness compiles the actual loader functions with test doubles for file access. AddressSanitizer and UndefinedBehaviorSanitizer checks cover all 64 normal EasyFlash banks, ROMH at the last bank, supported Magic Desk raw-bank remapping, 4 KB mirroring, truncated/invalid headers and data, oversized banks and header-shaped payloads. All 219 cases pass with the fail-fast adaptation. This is a focused parser test, not a complete compatibility test of every CRT format.

## Copy optimisation

The donor copies four bytes at a time when both pointers are aligned, then copies residual bytes. Other inputs retain byte copying. Both the exact donor function and our proposed adaptation passed 131,720 cases in total, with sanitizers, lengths 0 to 1,024 at every source/destination offset 0 to 7, larger boundary lengths, guard bytes, return-pointer checks, and inaccessible-page boundaries.

The adaptation uses GCC's `__may_alias__` attribute for word accesses to arbitrary objects. This addresses the compiler's type-aliasing assumptions without changing generated code in this build. No donor miscompilation was observed. Apply either `alias-safe-word-copy.patch` (preferred) or `community-word-copy.patch`, never both.

Host-only timing showed approximately 2.4 to 2.9 times the byte-loop speed for aligned buffers. Unaligned measurements ranged from about 0.89 to 1.02 times the baseline. These short host timings are noisy and are not STM32 timings or game-loading predictions. ARM disassembly confirms word accesses, but SD access, alignment, cache and bus contention can dominate actual loading.

Before enabling this globally, measure aligned and unaligned copy cycles on the STM32 and compare representative PRG/CRT loading and REU operations. Check that the extra branches do not materially penalise frequent small copies. VICE cannot benchmark the cartridge's STM32 implementation.

## Size checks

Complete ARM builds use the existing patched G7.03 source and launcher with GCC 12.2.1, `-Os`, and the original linker allocation. The clean baseline ARM bytes match the published G7.03 image.

| Build | ARM bytes | Change | ARM space remaining | BSS bytes |
| --- | ---: | ---: | ---: | ---: |
| G7.03 baseline | 77,620 | 0 | 20,684 | 25,976 |
| Parser rejection only | 77,620 | 0 | 20,684 | 25,976 |
| Word copy, donor or alias-safe | 77,664 | +44 | 20,640 | 25,976 |
| Parser rejection plus word copy | 77,664 | +44 | 20,640 | 25,976 |

ARM allocation is 98,304 bytes. Standalone copy functions are 18 bytes for the byte loop and 74 bytes for either word-copy version; whole-image growth differs because of compiler/linker effects. The C64 launcher is unchanged, retaining its previously measured 627 bytes free. No C64 ROM space is consumed by these ARM changes.

## PRG startup setting

Correction to the earlier description: the donor's `no_autostart_prg()` hook runs before the initial menu loop. It suppresses automatic startup of remembered PRG/disk selections. It does not let a manually selected PRG load without running. Its narrower per-type policy differs from our general autoboot option, but is not a priority for G8.

The 18 tested flag/type combinations match that behavior. Do not import the donor configuration structure: it retains the same signature while changing size from 1,024 to 1,044 bytes and moving the stored path from byte 18 to 404 and filename from 768 to 916. A future setting should be designed separately with explicit compatibility handling.

## Reproducing the assessment

`tools/assess_upstream.py` extracts real functions from the pinned Git commits. It runs host tests and six full ARM builds in temporary directories, writes JSON/disassembly/candidate patches here, and leaves firmware sources untouched. Build logs are generated locally and ignored by Git. It requires host GCC with sanitizers and a prepared G7.03 ARM source tree, launcher binary and ARM/newlib toolchain. The integration build can prepare the baseline source and launcher first.

Example, with repositories checked out alongside one another and toolchain paths adjusted:

```sh
python3 tools/assess_upstream.py \
  --upstream ../kff2 \
  --baseline-build ../kff2-graphical-menu/launcher/build/arm-firmware/firmware \
  --launcher ../kff2-graphical-menu/launcher/build/integration/native/kff2-integrated-launcher.bin \
  --arm-bin /tmp/kff-arm/usr/bin \
  --newlib-include /tmp/kff-arm/usr/include/newlib \
  --newlib-libdir /tmp/kff-arm/usr/lib/arm-none-eabi/newlib/thumb/v7e-m+dp/hard
```

The upstream checkout must contain the three commits listed in `results.json`. Benchmark timings will vary between runs. Full build hashes describe ARM-only binaries, not flashable update files.

Published G7.03 update SHA-256 remains `2d7456f99b3864578da30b0da6280bd0a9ed26ba9e78034f38bb7841253ee402`.

## Source provenance

- Official v2.07/documentation baseline: `9c84d999f4e2f5b2c7688cbc37a127069f5401b0`.
- [Community runtime and startup policy](https://codeberg.org/r107sl/KungFuFlash2/src/commit/da19c9a892f6e12a40b943a7006e25d413968570/firmware/runtime.c), commit `da19c9a892f6e12a40b943a7006e25d413968570`.
- [Community loader payload skip](https://codeberg.org/lroby74/KungFuFlash2/src/commit/653e03d779220841acd31c22ad46403c2696b402/firmware/loader.c), commit `653e03d779220841acd31c22ad46403c2696b402`.

These community branches contain other substantial changes. This assessment does not recommend merging either branch wholesale. Multi-disk remains the first G8 feature; GMod2 still needs its separate review and hardware gates.
